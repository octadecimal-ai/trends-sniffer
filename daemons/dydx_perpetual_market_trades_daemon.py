#!/usr/bin/env python3
"""
Daemon do pobierania transakcji z perpetualMarket z dYdX API dzień po dniu.

Skrypt przetwarza dane w porcjach po 1 dniu wstecz. Przechodzi do kolejnego dnia
tylko gdy bezbłędnie zakończy przetwarzanie aktualnego dnia.

Logi:
  - Główne logi: .dev/logs/dydx_perpetual_market_trades_service.log
  - Logi dni: .dev/logs/dydx_perpetual_market_trades_days.log (tylko dni i liczba rekordów)
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Dodaj ścieżkę projektu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from loguru import logger
from src.providers.dydx_indexer_provider import DydxIndexerProvider
from src.scripts.populate_dydx_perpetual_market_trades import (
    get_db_connection,
    insert_market_trades,
    get_trades_with_retry,
    MAX_RETRIES_PER_BATCH,
    RETRY_DELAY_BASE,
    RETRY_DELAY_MAX,
    MAX_CONSECUTIVE_FAILURES
)

# Konfiguracja loggera
logger.remove()

# Główny logger (do pliku usługi)
service_log_file = os.path.join(
    os.path.dirname(__file__), '..', '..', '.dev', 'logs',
    'dydx_perpetual_market_trades_service.log'
)
os.makedirs(os.path.dirname(service_log_file), exist_ok=True)
logger.add(service_log_file, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {message}")

# Plik logów dla dni (tylko dni i liczba rekordów)
days_log_file = os.path.join(
    os.path.dirname(__file__), '..', '..', '.dev', 'logs',
    'dydx_perpetual_market_trades_days.log'
)

# NIE dodajemy loggera do stderr - tylko do pliku (daemon działa w tle)


def get_progress_file(ticker: str) -> str:
    """Zwraca ścieżkę do pliku postępu dla danego tickera."""
    return os.path.join(
        os.path.dirname(__file__), '..', '..', '.dev', 'logs',
        f'dydx_perpetual_market_trades_progress_{ticker}.json'
    )


def load_progress(conn, ticker: str) -> Optional[Dict]:
    """Wczytuje postęp z bazy danych."""
    try:
        with conn.cursor() as cur:
            select_sql = """
                SELECT ticker, processing_date, total_trades, last_update, attempts
                FROM dydx_perpetual_market_trades_progress
                WHERE ticker = %s
            """
            cur.execute(select_sql, (ticker,))
            row = cur.fetchone()
            
            if row:
                return {
                    'ticker': row[0],
                    'current_date': row[1].isoformat() if row[1] else None,
                    'total_trades': row[2] or 0,
                    'last_update': row[3].isoformat() if row[3] else None,
                    'attempts': row[4] if row[4] else []
                }
    except Exception as e:
        logger.warning(f"Błąd wczytywania postępu z bazy: {e}")
    return None


def save_progress(conn, ticker: str, current_date: datetime, total_trades: int, attempts: List[Dict]):
    """Zapisuje postęp do bazy danych."""
    try:
        with conn.cursor() as cur:
            # Przygotuj dane
            last_update = datetime.now(timezone.utc)
            attempts_json = json.dumps(attempts) if attempts else json.dumps([])
            
            # INSERT ... ON CONFLICT UPDATE (upsert)
            insert_sql = """
                INSERT INTO dydx_perpetual_market_trades_progress (
                    ticker, processing_date, total_trades, last_update, attempts
                ) VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (ticker) DO UPDATE SET
                    processing_date = EXCLUDED.processing_date,
                    total_trades = EXCLUDED.total_trades,
                    last_update = EXCLUDED.last_update,
                    attempts = EXCLUDED.attempts,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            cur.execute(
                insert_sql,
                (
                    ticker,
                    current_date,
                    total_trades,
                    last_update,
                    attempts_json
                )
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Błąd zapisywania postępu do bazy: {e}")
        conn.rollback()


def process_single_day(
    provider: DydxIndexerProvider,
    conn,
    ticker: str,
    target_date: datetime
) -> tuple[bool, int, List[Dict]]:
    """
    Przetwarza transakcje dla jednego dnia.
    
    Returns:
        (success, total_trades, attempts) gdzie:
        - success: True jeśli dzień został bezbłędnie przetworzony
        - total_trades: Łączna liczba zapisanych transakcji
        - attempts: Lista prób z liczbą rekordów
    """
    # Oblicz zakres dat dla dnia (00:00:00 - 23:59:59 UTC)
    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
    
    logger.info(f"📅 Przetwarzanie dnia: {day_start.date()} ({day_start} - {day_end})")
    
    all_trades = []  # Używane tylko do zliczania i końcowego zapisu pozostałych
    attempts = []
    current_end = day_end
    batch_count = 0
    consecutive_failures = 0
    last_successful_batch_time = datetime.now(timezone.utc)
    max_batches = 10000  # Zabezpieczenie
    total_inserted = 0  # Łączna liczba zapisanych transakcji
    
    logger.info(f"🔄 Rozpoczynam pobieranie dla dnia {day_start.date()} (od {day_end} do {day_start})")
    
    while current_end >= day_start and batch_count < max_batches:
        # Sprawdź czy nie ma zbyt długiej przerwy bez sukcesu
        time_since_last_success = (datetime.now(timezone.utc) - last_successful_batch_time).total_seconds()
        if time_since_last_success > 1800:  # 30 minut bez sukcesu
            logger.warning(f"⚠️ Brak sukcesu przez {time_since_last_success/60:.1f} minut - VPN może się przełączać, czekam dłużej...")
            wait_time = min(RETRY_DELAY_MAX, time_since_last_success / 10)
            logger.info(f"⏳ Czekam {wait_time:.0f}s przed kolejną próbą...")
            time.sleep(wait_time)
            last_successful_batch_time = datetime.now(timezone.utc)
        
        # Pobierz transakcje z retry
        attempt_start = datetime.now(timezone.utc)
        logger.debug(f"Próba pobrania batch {batch_count + 1} dla dnia {day_start.date()} (od {current_end} do {day_start})")
        
        trades = get_trades_with_retry(
            provider=provider,
            ticker=ticker,
            created_before_or_at=current_end,
            created_on_or_after=day_start,
            consecutive_failures=consecutive_failures
        )
        attempt_end = datetime.now(timezone.utc)
        attempt_duration = (attempt_end - attempt_start).total_seconds()
        
        if trades is None:
            consecutive_failures += 1
            logger.warning(f"⚠️ Nie udało się pobrać batch {batch_count + 1}. Błędy z rzędu: {consecutive_failures}")
            
            attempts.append({
                'batch': batch_count + 1,
                'success': False,
                'trades_count': 0,
                'duration_seconds': attempt_duration,
                'timestamp': attempt_start.isoformat()
            })
            
            # Po zbyt wielu błędach, zwiększ opóźnienie
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.info(f"⏳ {consecutive_failures} kolejnych błędów - VPN może się przełączać, czekam dłużej...")
            
            wait_time = min(RETRY_DELAY_BASE * (2 ** consecutive_failures) * (1 + consecutive_failures / 2), RETRY_DELAY_MAX)
            logger.info(f"⏳ Czekam {wait_time:.0f}s przed ponowną próbą (VPN może się przełączać)...")
            time.sleep(wait_time)
            continue
        
        if not trades:
            logger.debug(f"Brak więcej transakcji dla dnia {day_start.date()} (batch {batch_count + 1})")
            attempts.append({
                'batch': batch_count + 1,
                'success': True,
                'trades_count': 0,
                'duration_seconds': attempt_duration,
                'timestamp': attempt_start.isoformat(),
                'note': 'Brak transakcji'
            })
            break
        
        # Sukces - resetuj liczniki
        consecutive_failures = 0
        last_successful_batch_time = datetime.now(timezone.utc)
        
        batch_count += 1
        
        logger.info(f"✓ Batch {batch_count}: pobrano {len(trades)} transakcji (czas: {attempt_duration:.1f}s)")
        
        # Zapisz batch od razu do bazy
        inserted = 0
        try:
            inserted = insert_market_trades(conn, ticker, trades)
            total_inserted += inserted
            logger.info(f"💾 Zapisano {inserted} transakcji z batcha {batch_count} do bazy")
        except Exception as e:
            logger.error(f"❌ Błąd zapisywania batcha {batch_count}: {e}")
            # Nie przerywamy - kontynuujemy, ale zapisujemy do listy na później
            all_trades.extend(trades)
        
        attempts.append({
            'batch': batch_count,
            'success': True,
            'trades_count': len(trades),
            'inserted_count': inserted,
            'duration_seconds': attempt_duration,
            'timestamp': attempt_start.isoformat()
        })
        
        # Znajdź najstarszą transakcję z tego batcha
        oldest_trade = min(trades, key=lambda t: t.get('createdAt', current_end))
        oldest_date = oldest_trade.get('createdAt')
        
        if isinstance(oldest_date, datetime):
            current_end = oldest_date
        elif isinstance(oldest_date, str):
            try:
                current_end = datetime.fromisoformat(oldest_date.replace('Z', '+00:00'))
            except:
                logger.error(f"Błąd parsowania daty: {oldest_date}")
                return False, total_inserted, attempts
        else:
            logger.error(f"Nieprawidłowy format daty: {oldest_date}")
            return False, total_inserted, attempts
        
        # Logowanie postępu co 10 batchy
        if batch_count % 10 == 0:
            logger.info(f"📊 Postęp: {batch_count} batchy, {total_inserted} transakcji zapisanych, current_end: {current_end}, day_start: {day_start}")
        
        # Jeśli najstarsza transakcja jest przed początkiem dnia, zakończ
        if current_end < day_start:
            logger.info(f"✓ Osiągnięto początek dnia ({day_start}). Kończę pobieranie.")
            break
        
        # Jeśli pobraliśmy mniej niż limit, to znaczy że to koniec
        if len(trades) < 100:
            logger.info(f"✓ Otrzymano mniej niż 100 transakcji ({len(trades)}). Kończę pobieranie.")
            break
        
        logger.debug(f"Batch {batch_count}: pobrano {len(trades)} transakcji, kontynuuję od {current_end}")
    
    # Zapisz pozostałe transakcje do bazy (jeśli są - tylko te, które nie zostały zapisane z powodu błędu)
    logger.info(f"📝 Zakończono pobieranie dla dnia {day_start.date()}. Łącznie zapisano {total_inserted} transakcji w {batch_count} batchach.")
    
    if all_trades:
        try:
            logger.info(f"💾 Zapisuję {len(all_trades)} pozostałych transakcji do bazy (z błędów)...")
            inserted = insert_market_trades(conn, ticker, all_trades)
            total_inserted += inserted
            logger.info(f"✓ Zapisano dodatkowo {inserted} transakcji do bazy dla dnia {day_start.date()}")
        except Exception as e:
            logger.error(f"❌ Błąd zapisywania pozostałych transakcji dla dnia {day_start.date()}: {e}")
    
    # Log do pliku dni
    total_attempts = len(attempts)
    successful_attempts = sum(1 for a in attempts if a['success'] and a['trades_count'] > 0)
    total_trades_from_attempts = sum(a['trades_count'] for a in attempts)
    
    # Log do pliku dni - tylko informacje o dniu i liczbie rekordów
    if total_inserted > 0:
        days_log_msg = f"✓ {day_start.date()} | {total_inserted} rekordów | {successful_attempts}/{total_attempts} prób udanych | {total_trades_from_attempts} transakcji pobranych"
    else:
        days_log_msg = f"ℹ️ {day_start.date()} | 0 rekordów | Brak transakcji"
    
    # Użyj bezpośredniego zapisu do pliku, bo logger może nie działać poprawnie z filtrem
    with open(days_log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} | {days_log_msg}\n")
    
    return True, total_inserted, attempts


def main():
    parser = argparse.ArgumentParser(description='Daemon do pobierania transakcji z perpetualMarket dzień po dniu')
    parser.add_argument('--ticker', type=str, default='BTC-USD', help='Symbol rynku (domyślnie: BTC-USD)')
    parser.add_argument('--days-back-start', type=int, default=1, help='Od ilu dni wstecz zacząć (domyślnie: 1)')
    parser.add_argument('--max-days', type=int, help='Maksymalna liczba dni do przetworzenia (None = bez limitu)')
    parser.add_argument('--delay-between-days', type=int, default=5, help='Opóźnienie między dniami w sekundach (domyślnie: 5)')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    logger.info("="*70)
    logger.info(f"Uruchamianie daemona dla {args.ticker}")
    logger.info(f"Start od {args.days_back_start} dni wstecz")
    logger.info("="*70)
    
    # Połącz z bazą
    try:
        conn = get_db_connection()
        logger.info("✓ Połączono z bazą danych")
    except Exception as e:
        logger.error(f"❌ Błąd połączenia z bazą: {e}")
        sys.exit(1)
    
    # Wczytaj postęp jeśli istnieje
    progress = load_progress(conn, args.ticker)
    if progress:
        try:
            resume_date = datetime.fromisoformat(progress['current_date'].replace('Z', '+00:00'))
            logger.info(f"📌 Wznawianie od daty: {resume_date.date()}")
            current_date = resume_date
        except:
            current_date = datetime.now(timezone.utc) - timedelta(days=args.days_back_start)
            logger.info(f"⚠️ Błąd wczytywania postępu, zaczynam od {current_date.date()}")
    else:
        current_date = datetime.now(timezone.utc) - timedelta(days=args.days_back_start)
        logger.info(f"📅 Zaczynam od daty: {current_date.date()}")
    
    # Inicjalizuj provider
    provider = DydxIndexerProvider()
    
    days_processed = 0
    days_successful = 0
    days_failed = 0
    total_trades = 0
    
    try:
        while True:
            # Przetwórz jeden dzień
            success, trades_count, attempts = process_single_day(
                provider=provider,
                conn=conn,
                ticker=args.ticker,
                target_date=current_date
            )
            
            days_processed += 1
            
            if success:
                days_successful += 1
                total_trades += trades_count
                
                # Zapisz postęp
                save_progress(conn, args.ticker, current_date, total_trades, attempts)
                
                completed_date = current_date
                
                # Przejdź do poprzedniego dnia
                current_date = current_date - timedelta(days=1)
                
                logger.info(f"✓ Dzień {completed_date.date()} zakończony pomyślnie ({trades_count} transakcji). Przechodzę do {current_date.date()}")
                
                # Sprawdź limit dni
                if args.max_days and days_processed >= args.max_days:
                    logger.info(f"✓ Osiągnięto limit {args.max_days} dni. Zatrzymywanie...")
                    break
                
                # Opóźnienie między dniami
                if args.delay_between_days > 0:
                    time.sleep(args.delay_between_days)
            else:
                days_failed += 1
                logger.error(f"❌ Błąd przetwarzania dnia {current_date.date()}. Błędy z rzędu: {days_failed}. Ponawiam...")
                
                # Nie przechodzimy do następnego dnia - ponawiamy ten sam dzień
                # Zwiększ opóźnienie przed ponowną próbą
                wait_time = min(RETRY_DELAY_BASE * (2 ** min(days_failed, 5)), RETRY_DELAY_MAX)
                logger.info(f"⏳ Czekam {wait_time:.0f}s przed ponowną próbą dnia {current_date.date()}...")
                time.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.warning("⚠️ Przerwano przez użytkownika")
        try:
            save_progress(conn, args.ticker, current_date, total_trades, [])
        except:
            pass  # Ignoruj błędy przy zapisie postępu przy przerwaniu
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            save_progress(conn, args.ticker, current_date, total_trades, [])
        except:
            pass  # Ignoruj błędy przy zapisie postępu przy błędzie
    finally:
        if 'conn' in locals():
            conn.close()
        logger.info("="*70)
        logger.info("PODSUMOWANIE:")
        logger.info(f"  Dni przetworzone: {days_processed}")
        logger.info(f"  Dni zakończone sukcesem: {days_successful}")
        logger.info(f"  Dni z błędami: {days_failed}")
        logger.info(f"  Łącznie transakcji: {total_trades}")
        logger.info("="*70)


if __name__ == '__main__':
    main()

