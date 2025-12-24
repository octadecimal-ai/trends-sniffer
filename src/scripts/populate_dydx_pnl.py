#!/usr/bin/env python3
"""
Skrypt do pobierania Historical PnL z dYdX API i zapisywania do tabeli dydx_historical_pnl.

Endpoint: GET https://indexer.dydx.trade/v4/historical-pnl
Parametry query:
  - address: adres dYdX Chain (dydx1...)
  - subaccountNumber: numer subkonta (0-127)  
  - limit: max liczba wyników (max 100)
  - createdBeforeOrAt: (opcjonalnie) ISO timestamp
  - createdOnOrAfter: (opcjonalnie) ISO timestamp

Użycie:
  python src/scripts/populate_dydx_pnl.py [--address ADDR] [--from-csv CSV_FILE] [--days N]
"""

import os
import sys
import argparse
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


def get_db_connection():
    """Tworzy połączenie z bazą danych."""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("Brak DATABASE_URL w .env")
    
    return psycopg2.connect(database_url)


def ensure_trader_exists(conn, address: str, subaccount_number: int) -> int:
    """
    Upewnia się, że trader istnieje w dydx_traders. Zwraca trader_id.
    """
    with conn.cursor() as cur:
        # Sprawdź czy istnieje
        cur.execute("""
            SELECT id FROM dydx_traders 
            WHERE address = %s AND subaccount_number = %s
        """, (address, subaccount_number))
        
        row = cur.fetchone()
        if row:
            return row[0]
        
        # Utwórz nowego tradera
        cur.execute("""
            INSERT INTO dydx_traders (address, subaccount_number, first_seen_at, last_seen_at, is_active)
            VALUES (%s, %s, NOW(), NOW(), TRUE)
            RETURNING id
        """, (address, subaccount_number))
        
        trader_id = cur.fetchone()[0]
        conn.commit()
        
        logger.info(f"Utworzono nowego tradera: {address}:{subaccount_number} (ID: {trader_id})")
        return trader_id


def insert_pnl_snapshots(conn, trader_id: int, address: str, subaccount_number: int, pnls: List[Dict[str, Any]]) -> int:
    """
    Wstawia historical PnL do tabeli dydx_historical_pnl.
    Zwraca liczbę wstawionych rekordów.
    """
    if not pnls:
        return 0
    
    observed_at = datetime.now(timezone.utc)
    
    # Deduplikacja - usuń duplikaty po (address, subaccount_number, effective_at)
    seen = set()
    unique_pnls = []
    for pnl in pnls:
        created_at_raw = pnl.get('createdAt', '')
        if isinstance(created_at_raw, datetime):
            created_at = created_at_raw
        elif isinstance(created_at_raw, str):
            try:
                created_at = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
            except:
                continue
        else:
            continue
        
        key = (address, subaccount_number, created_at)
        if key not in seen:
            seen.add(key)
            unique_pnls.append(pnl)
    
    if not unique_pnls:
        return 0
    
    logger.debug(f"Po deduplikacji: {len(unique_pnls)} unikalnych rekordów PnL (z {len(pnls)} pobranych)")
    
    # Przygotuj dane do wstawienia
    rows = []
    for pnl in unique_pnls:
        # Parsuj timestamp (może być już datetime object lub string)
        created_at_raw = pnl.get('createdAt', '')
        if isinstance(created_at_raw, datetime):
            created_at = created_at_raw
        elif isinstance(created_at_raw, str):
            try:
                created_at = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
            except:
                created_at = observed_at
        else:
            created_at = observed_at
        
        # Mapowanie pól API -> tabela
        # API zwraca: equity, totalPnl, netTransfers, createdAt, blockHeight, blockTime
        # Tabela ma: realized_pnl, net_pnl, effective_at, created_at, observed_at, metadata
        
        row = (
            trader_id,
            address,
            subaccount_number,
            None,  # realized_pnl - API nie zwraca, zostawiamy NULL
            float(pnl.get('totalPnl', 0)),  # net_pnl (API zwraca totalPnl)
            created_at,  # effective_at
            created_at,  # created_at
            observed_at,  # observed_at
            json.dumps({  # metadata - dodatkowe dane z API
                'equity': pnl.get('equity'),
                'netTransfers': pnl.get('netTransfers'),
                'blockHeight': pnl.get('blockHeight'),
                'blockTime': pnl.get('blockTime')
            })
        )
        rows.append(row)
    
    # Wstaw z ON CONFLICT (deduplikacja)
    insert_sql = """
        INSERT INTO dydx_historical_pnl (
            trader_id, address, subaccount_number, realized_pnl, net_pnl,
            effective_at, created_at, observed_at, metadata
        ) VALUES %s
        ON CONFLICT (address, subaccount_number, effective_at) DO UPDATE SET
            net_pnl = EXCLUDED.net_pnl,
            metadata = EXCLUDED.metadata,
            observed_at = EXCLUDED.observed_at
    """
    
    with conn.cursor() as cur:
        # Sprawdź ile rekordów już istnieje
        if rows:
            first_created_at = rows[0][5]  # effective_at
            last_created_at = rows[-1][5]
            cur.execute("""
                SELECT COUNT(*) FROM dydx_historical_pnl
                WHERE address = %s AND subaccount_number = %s
                AND effective_at >= %s AND effective_at <= %s
            """, (address, subaccount_number, first_created_at, last_created_at))
            existing_count = cur.fetchone()[0]
            logger.debug(f"Rekordów w zakresie dat: {existing_count} istniejących, {len(rows)} do wstawienia")
        
        execute_values(cur, insert_sql, rows)
        # rowcount może być 0 jeśli wszystkie już istnieją (ON CONFLICT UPDATE)
        # Sprawdź faktyczną liczbę wstawionych/zmienionych
        inserted = cur.rowcount if cur.rowcount > 0 else len(rows)
    
    conn.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description='Pobierz Historical PnL z dYdX i zapisz do bazy')
    parser.add_argument('--address', type=str, help='Adres dYdX Chain (dydx1...)')
    parser.add_argument('--subaccount', type=int, default=0, help='Numer subkonta (domyślnie 0)')
    parser.add_argument('--days', type=int, default=30, help='Liczba dni wstecz (domyślnie 30)')
    parser.add_argument('--from-csv', type=str, help='Wczytaj adresy z pliku CSV (format: Rank;Trader;Estimated Rewards)')
    parser.add_argument('--limit', type=int, help='Limit rekordów na tradera (None = wszystkie)')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    # Zbierz adresy do sprawdzenia
    addresses = []
    
    if args.from_csv:
        # Wczytaj z pliku CSV
        csv_path = args.from_csv
        if not os.path.exists(csv_path):
            logger.error(f"Plik CSV nie istnieje: {csv_path}")
            sys.exit(1)
        
        logger.info(f"Wczytywanie adresów z pliku CSV: {csv_path}")
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Pomiń nagłówki (linie 1-2)
        for line_num, line in enumerate(lines[2:], start=3):
            line = line.strip()
            if not line:
                continue
            
            try:
                parts = line.split(';')
                if len(parts) >= 2:
                    address = parts[1].strip()
                    if address.startswith('dydx1'):
                        addresses.append((address, 0))
            except (ValueError, IndexError) as e:
                logger.warning(f"Błąd parsowania linii {line_num}: {line} - {e}")
                continue
        
        logger.info(f"Wczytano {len(addresses)} adresów z CSV")
    elif args.address:
        addresses.append((args.address, args.subaccount))
    else:
        logger.error("Brak adresów do sprawdzenia. Użyj --address lub --from-csv")
        sys.exit(1)
    
    if not addresses:
        logger.error("Brak adresów do sprawdzenia")
        sys.exit(1)
    
    logger.info(f"Adresy do sprawdzenia: {len(addresses)}")
    for addr, sub in addresses[:5]:  # Pokaż pierwsze 5
        logger.info(f"  - {addr}:{sub}")
    if len(addresses) > 5:
        logger.info(f"  ... i {len(addresses) - 5} więcej")
    
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
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    
    total_inserted = 0
    
    try:
        for address, subaccount_number in addresses:
            logger.info(f"\n{'='*60}")
            logger.info(f"Przetwarzanie: {address}:{subaccount_number}")
            logger.info(f"{'='*60}")
            
            # Zapewnij istnienie tradera
            trader_id = ensure_trader_exists(conn, address, subaccount_number)
            
            # Pobierz Historical PnL z API
            try:
                pnls = provider.get_all_historical_pnls_paginated(
                    address=address,
                    subaccount_number=subaccount_number,
                    created_on_or_after=cutoff,
                    max_results=args.limit
                )
            except Exception as e:
                logger.warning(f"Błąd API: {e}")
                continue
            
            if not pnls:
                logger.info("Brak PnL do zapisania")
                continue
            
            # Pokaż przykładowe PnL
            logger.info(f"\nPrzykładowe PnL ({min(3, len(pnls))} z {len(pnls)}):")
            for pnl in pnls[:3]:
                equity = float(pnl.get('equity', 0))
                total_pnl = float(pnl.get('totalPnl', 0))
                logger.info(f"  - Equity: ${equity:,.2f}, Total PnL: ${total_pnl:,.2f} ({pnl.get('createdAt')})")
            
            # Zapisz do bazy
            inserted = insert_pnl_snapshots(conn, trader_id, address, subaccount_number, pnls)
            
            logger.success(f"Zapisano {inserted} rekordów PnL do bazy (trader_id: {trader_id})")
            total_inserted += inserted
    
    finally:
        conn.close()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"PODSUMOWANIE: Zapisano łącznie {total_inserted} rekordów PnL")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()

