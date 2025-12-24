#!/usr/bin/env python3
"""
Skrypt do pobierania transakcji z perpetualMarket z dYdX API i zapisywania do tabeli dydx_perpetual_market_trades.

Endpoint: GET https://indexer.dydx.trade/v4/trades/perpetualMarket/{ticker}
Parametry query:
  - limit: max liczba wyników (max 100)
  - createdBeforeOrAt: (opcjonalnie) ISO timestamp
  - createdOnOrAfter: (opcjonalnie) ISO timestamp

Uwaga: Ten endpoint NIE zawiera adresów traderów - służy do analizy aktywności rynku.

Użycie:
  python src/scripts/populate_dydx_perpetual_market_trades.py --ticker BTC-USD [--days N] [--limit N]
  python src/scripts/populate_dydx_perpetual_market_trades.py --all-markets [--days N] [--limit N]
"""

import os
import sys
import argparse
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import json

# Dodaj ścieżkę projektu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from loguru import logger
from src.providers.dydx_indexer_provider import DydxIndexerProvider

# Konfiguracja loggera
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")

# Stałe
DYDX_API_URL = "https://indexer.dydx.trade/v4"

# Konfiguracja retry
MAX_RETRIES_PER_BATCH = 5  # Maksymalna liczba prób dla jednego batcha
RETRY_DELAY_BASE = 10  # Bazowe opóźnienie w sekundach (dłuższe, bo VPN może się przełączać)
RETRY_DELAY_MAX = 300  # Maksymalne opóźnienie (5 minut)
MAX_CONSECUTIVE_FAILURES = 5  # Po tylu kolejnych błędach zwiększ opóźnienie (VPN przełącza się w tle)


def get_db_connection():
    """Tworzy połączenie z bazą danych."""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("Brak DATABASE_URL w .env")
    
    return psycopg2.connect(database_url)


def wait_after_max_retries(attempt: int, max_retries: int):
    """
    Czeka po przekroczeniu maksymalnej liczby prób.
    Czas oczekiwania rośnie wykładniczo.
    """
    if attempt >= max_retries:
        wait_time = min(RETRY_DELAY_BASE * (2 ** (attempt - max_retries)), RETRY_DELAY_MAX)
        logger.info(f"⏳ Przekroczono limit prób ({max_retries}). Czekam {wait_time}s przed kolejną próbą...")
        time.sleep(wait_time)
        return True
    return False


def get_trades_with_retry(
    provider: DydxIndexerProvider,
    ticker: str,
    created_before_or_at: Optional[datetime],
    created_on_or_after: Optional[datetime],
    consecutive_failures: int = 0
) -> Optional[List[Dict[str, Any]]]:
    """
    Pobiera transakcje z retry logic i obsługą VPN.
    
    Returns:
        Lista transakcji lub None w przypadku błędu
    """
    last_exception = None
    
    for attempt in range(MAX_RETRIES_PER_BATCH):
        try:
            trades = provider.get_trades_for_market(
                ticker=ticker,
                limit=100,
                created_before_or_at=created_before_or_at,
                created_on_or_after=created_on_or_after
            )
            
            # Sukces - resetuj licznik błędów
            if consecutive_failures > 0:
                logger.info(f"✓ Połączenie przywrócone po {consecutive_failures} błędach")
            
            return trades
            
        except Exception as e:
            last_exception = e
            consecutive_failures += 1
            
            # Sprawdź typ błędu
            error_str = str(e).lower()
            is_network_error = any(keyword in error_str for keyword in [
                'timeout', 'connection', 'network', 'dns', 'nodename', 'servname'
            ])
            
            if is_network_error:
                logger.warning(f"⚠️ Błąd sieci (próba {attempt + 1}/{MAX_RETRIES_PER_BATCH}): {e}")
                
                # Po kilku kolejnych błędach sieciowych, zwiększ opóźnienie
                # (VPN może się przełączać w tle przez trends_sniffer_service.sh)
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.info(f"⏳ {consecutive_failures} kolejnych błędów sieciowych - VPN może się przełączać, czekam dłużej...")
                    # Nie resetujemy consecutive_failures - pozwalamy VPN się przełączyć w tle
                
                # Czekaj przed kolejną próbą (dłuższe opóźnienia dla VPN)
                wait_time = min(RETRY_DELAY_BASE * (2 ** attempt) * (1 + consecutive_failures), RETRY_DELAY_MAX)
                if attempt < MAX_RETRIES_PER_BATCH - 1:
                    logger.info(f"⏳ Czekam {wait_time}s przed kolejną próbą (VPN może się przełączać)...")
                    time.sleep(wait_time)
            else:
                # Inny błąd (nie sieciowy) - nie retry
                logger.error(f"❌ Błąd nie-sieciowy: {e}")
                break
    
    # Wszystkie próby wyczerpane
    wait_after_max_retries(MAX_RETRIES_PER_BATCH, MAX_RETRIES_PER_BATCH)
    logger.error(f"❌ Nie udało się pobrać danych po {MAX_RETRIES_PER_BATCH} próbach: {last_exception}")
    return None


def get_available_markets(provider: DydxIndexerProvider) -> List[str]:
    """
    Pobiera listę dostępnych rynków perpetual z dYdX.
    Zwraca listę tickerów (np. ['BTC-USD', 'ETH-USD', ...]).
    """
    try:
        # Użyj endpointu /perpetualMarkets
        import requests
        response = requests.get(f"{DYDX_API_URL}/perpetualMarkets", timeout=30)
        response.raise_for_status()
        data = response.json()
        
        markets = []
        if 'markets' in data:
            for ticker, info in data['markets'].items():
                # Tylko aktywne rynki
                if info.get('status') == 'ACTIVE':
                    markets.append(ticker)
        
        logger.info(f"Znaleziono {len(markets)} aktywnych rynków perpetual")
        return sorted(markets)
    
    except Exception as e:
        logger.warning(f"Błąd pobierania listy rynków: {e}. Używam domyślnych.")
        # Domyślne rynki
        return ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'MATIC-USD']


def insert_market_trades(conn, ticker: str, trades: List[Dict[str, Any]]) -> int:
    """
    Wstawia transakcje z perpetualMarket do tabeli dydx_perpetual_market_trades.
    Zwraca liczbę wstawionych rekordów.
    """
    if not trades:
        return 0
    
    observed_at = datetime.now(timezone.utc)
    
    # Deduplikacja - usuń duplikaty po (trade_id, ticker)
    seen = set()
    unique_trades = []
    for trade in trades:
        trade_id = trade.get('id', '')
        if not trade_id:
            continue
        
        key = (trade_id, ticker)
        if key not in seen:
            seen.add(key)
            unique_trades.append(trade)
    
    if not unique_trades:
        return 0
    
    logger.debug(f"Po deduplikacji: {len(unique_trades)} unikalnych transakcji (z {len(trades)} pobranych)")
    
    # Przygotuj dane do wstawienia
    rows = []
    for trade in unique_trades:
        # Parsuj timestamp
        created_at_raw = trade.get('createdAt', '')
        if isinstance(created_at_raw, datetime):
            created_at = created_at_raw
        elif isinstance(created_at_raw, str):
            try:
                created_at = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
            except:
                created_at = observed_at
        else:
            created_at = observed_at
        
        # Parsuj createdAtHeight
        created_at_height = None
        try:
            height_str = trade.get('createdAtHeight', '')
            if height_str:
                created_at_height = int(height_str)
        except (ValueError, TypeError):
            pass
        
        # Mapowanie pól API -> tabela
        row = (
            ticker,
            trade.get('id', ''),  # trade_id
            trade.get('side', 'UNKNOWN'),  # side
            float(trade.get('size', 0)),  # size
            float(trade.get('price', 0)),  # price
            trade.get('type'),  # trade_type
            created_at,  # effective_at
            created_at_height,  # created_at_height
            observed_at,  # observed_at
            json.dumps({  # metadata - dodatkowe dane z API
                'original_data': {
                    'id': trade.get('id'),
                    'side': trade.get('side'),
                    'size': trade.get('size'),
                    'price': trade.get('price'),
                    'type': trade.get('type'),
                    'createdAt': trade.get('createdAt').isoformat() if isinstance(trade.get('createdAt'), datetime) else str(trade.get('createdAt', '')),
                    'createdAtHeight': trade.get('createdAtHeight')
                }
            })
        )
        rows.append(row)
    
    # Wstaw z ON CONFLICT (deduplikacja)
    insert_sql = """
        INSERT INTO dydx_perpetual_market_trades (
            ticker, trade_id, side, size, price, trade_type,
            effective_at, created_at_height, observed_at, metadata
        ) VALUES %s
        ON CONFLICT (trade_id, ticker) DO UPDATE SET
            observed_at = EXCLUDED.observed_at,
            metadata = EXCLUDED.metadata
    """
    
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, rows)
        # rowcount może być 0 jeśli wszystkie już istnieją (ON CONFLICT UPDATE)
        inserted = cur.rowcount if cur.rowcount > 0 else len(rows)
    
    conn.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description='Pobierz transakcje z perpetualMarket i zapisz do bazy')
    parser.add_argument('--ticker', type=str, help='Symbol rynku (np. BTC-USD, ETH-USD)')
    parser.add_argument('--all-markets', action='store_true', help='Pobierz dla wszystkich dostępnych rynków')
    parser.add_argument('--days', type=int, default=1, help='Liczba dni wstecz (domyślnie 1)')
    parser.add_argument('--limit', type=int, help='Limit rekordów na rynek (None = wszystkie, max 100 na batch)')
    parser.add_argument('--resume-from', type=str, help='Wznów od daty (ISO format, np. 2025-12-23T00:00:00Z)')
    parser.add_argument('--save-progress', action='store_true', default=True, help='Zapisuj postęp do pliku (domyślnie True)')
    parser.add_argument('--no-save-progress', dest='save_progress', action='store_false', help='Nie zapisuj postępu')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    # Zbierz tickery do sprawdzenia
    tickers = []
    
    if args.all_markets:
        # Pobierz listę wszystkich rynków
        provider = DydxIndexerProvider()
        tickers = get_available_markets(provider)
        logger.info(f"Pobieranie dla {len(tickers)} rynków")
    elif args.ticker:
        tickers = [args.ticker]
    else:
        logger.error("Brak tickerów do sprawdzenia. Użyj --ticker lub --all-markets")
        sys.exit(1)
    
    if not tickers:
        logger.error("Brak tickerów do sprawdzenia")
        sys.exit(1)
    
    logger.info(f"Tickery do sprawdzenia: {len(tickers)}")
    for ticker in tickers[:10]:  # Pokaż pierwsze 10
        logger.info(f"  - {ticker}")
    if len(tickers) > 10:
        logger.info(f"  ... i {len(tickers) - 10} więcej")
    
    # Połącz z bazą
    try:
        conn = get_db_connection()
        logger.info("Połączono z bazą danych")
    except Exception as e:
        logger.error(f"Błąd połączenia z bazą: {e}")
        sys.exit(1)
    
    # Inicjalizuj provider
    provider = DydxIndexerProvider()
    
    # Oblicz datę początkową
    if args.resume_from:
        try:
            cutoff = datetime.fromisoformat(args.resume_from.replace('Z', '+00:00'))
            logger.info(f"📌 Wznawianie od daty: {cutoff}")
        except:
            logger.warning(f"⚠️ Nieprawidłowy format daty --resume-from, używam --days")
            cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    
    # Plik do zapisywania postępu
    progress_file = None
    if args.save_progress or args.save_progress is None:  # Domyślnie True
        progress_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '.dev', 'logs',
            f'dydx_perpetual_market_trades_progress_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        os.makedirs(os.path.dirname(progress_file), exist_ok=True)
    
    total_inserted = 0
    
    try:
        for ticker in tickers:
            logger.info(f"\n{'='*60}")
            logger.info(f"Przetwarzanie: {ticker}")
            logger.info(f"{'='*60}")
            
            # Pobierz transakcje z API - iteruj po datach (endpoint nie obsługuje paginacji)
            all_trades = []
            current_end = datetime.now(timezone.utc)
            batch_count = 0
            max_batches = 1000  # Zabezpieczenie przed nieskończoną pętlą
            
            logger.info(f"Pobieranie transakcji od {cutoff} do {current_end}")
            
            consecutive_failures = 0
            last_successful_batch_time = datetime.now(timezone.utc)
            
            while current_end > cutoff and batch_count < max_batches:
                # Sprawdź czy nie ma zbyt długiej przerwy bez sukcesu
                time_since_last_success = (datetime.now(timezone.utc) - last_successful_batch_time).total_seconds()
                if time_since_last_success > 1800:  # 30 minut bez sukcesu
                    logger.warning(f"⚠️ Brak sukcesu przez {time_since_last_success/60:.1f} minut - VPN może się przełączać, czekam dłużej...")
                    # Nie przełączamy VPN - trends_sniffer_service.sh robi to w tle
                    # Zwiększamy opóźnienie i czekamy
                    wait_time = min(RETRY_DELAY_MAX, time_since_last_success / 10)
                    logger.info(f"⏳ Czekam {wait_time:.0f}s przed kolejną próbą...")
                    time.sleep(wait_time)
                    last_successful_batch_time = datetime.now(timezone.utc)
                
                # Pobierz transakcje z retry
                trades = get_trades_with_retry(
                    provider=provider,
                    ticker=ticker,
                    created_before_or_at=current_end,
                    created_on_or_after=cutoff,
                    consecutive_failures=consecutive_failures
                )
                
                if trades is None:
                    consecutive_failures += 1
                    logger.warning(f"⚠️ Nie udało się pobrać batch {batch_count + 1}. Błędy z rzędu: {consecutive_failures}")
                    
                    # Po zbyt wielu błędach, zwiększ opóźnienie (VPN przełącza się w tle)
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        logger.info(f"⏳ {consecutive_failures} kolejnych błędów - VPN może się przełączać, czekam dłużej...")
                        # Nie resetujemy consecutive_failures - pozwalamy VPN się przełączyć w tle
                    
                    # Poczekaj i spróbuj ponownie (dłuższe opóźnienia dla VPN)
                    wait_time = min(RETRY_DELAY_BASE * (2 ** consecutive_failures) * (1 + consecutive_failures / 2), RETRY_DELAY_MAX)
                    logger.info(f"⏳ Czekam {wait_time:.0f}s przed ponowną próbą (VPN może się przełączać)...")
                    time.sleep(wait_time)
                    # Kontynuuj pętlę - nie przerywaj
                    continue
                
                if not trades:
                    logger.debug(f"Brak więcej transakcji (batch {batch_count + 1})")
                    break
                
                # Sukces - resetuj liczniki
                consecutive_failures = 0
                last_successful_batch_time = datetime.now(timezone.utc)
                
                # Dodaj do listy (deduplikacja będzie w insert_market_trades)
                all_trades.extend(trades)
                batch_count += 1
                
                # Znajdź najstarszą transakcję z tego batcha
                oldest_trade = min(trades, key=lambda t: t.get('createdAt', current_end))
                oldest_date = oldest_trade.get('createdAt')
                
                if isinstance(oldest_date, datetime):
                    current_end = oldest_date
                elif isinstance(oldest_date, str):
                    try:
                        current_end = datetime.fromisoformat(oldest_date.replace('Z', '+00:00'))
                    except:
                        break
                else:
                    break
                
                # Jeśli najstarsza transakcja jest przed cutoff, zakończ
                if current_end <= cutoff:
                    break
                
                # Jeśli pobraliśmy mniej niż limit, to znaczy że to koniec
                if len(trades) < 100:
                    break
                
                logger.debug(f"Batch {batch_count}: pobrano {len(trades)} transakcji, kontynuuję od {current_end}")
                
                # Zapisz postęp
                if progress_file:
                    try:
                        progress_data = {
                            'ticker': ticker,
                            'cutoff': cutoff.isoformat(),
                            'current_end': current_end.isoformat(),
                            'batch_count': batch_count,
                            'total_trades': len(all_trades),
                            'last_update': datetime.now(timezone.utc).isoformat()
                        }
                        with open(progress_file, 'w') as f:
                            json.dump(progress_data, f, indent=2)
                    except Exception as e:
                        logger.debug(f"Nie udało się zapisać postępu: {e}")
            
            if not all_trades:
                logger.info("Brak transakcji do zapisania")
                continue
            
            # Pokaż przykładowe transakcje
            logger.info(f"\nPobrano łącznie {len(all_trades)} transakcji w {batch_count} batchach")
            logger.info(f"Przykładowe transakcje (3 z {len(all_trades)}):")
            for trade in all_trades[:3]:
                side = trade.get('side', 'UNKNOWN')
                size = float(trade.get('size', 0))
                price = float(trade.get('price', 0))
                logger.info(f"  - {side:4} {size:>10.6f} @ ${price:>10,.2f} ({trade.get('createdAt')})")
            
            # Zapisz do bazy
            inserted = insert_market_trades(conn, ticker, all_trades)
            
            logger.success(f"Zapisano {inserted} transakcji do bazy dla {ticker}")
            total_inserted += inserted
    
    finally:
        conn.close()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"PODSUMOWANIE: Zapisano łącznie {total_inserted} transakcji")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()

