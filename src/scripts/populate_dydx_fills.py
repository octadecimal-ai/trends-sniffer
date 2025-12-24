#!/usr/bin/env python3
"""
Skrypt do pobierania fill'ów z dYdX API i zapisywania do tabeli dydx_fills.

Endpoint: GET https://indexer.dydx.trade/v4/fills
Parametry query:
  - address: adres dYdX Chain (dydx1...)
  - subaccountNumber: numer subkonta (0-127)  
  - limit: max liczba wyników (max 100)
  - ticker: (opcjonalnie) symbol rynku np. BTC-USD
  - createdBeforeOrAt: (opcjonalnie) ISO timestamp
  - createdOnOrAfter: (opcjonalnie) ISO timestamp

Użycie:
  python src/scripts/populate_dydx_fills.py [--address ADDR] [--limit N]
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json

# Dodaj ścieżkę projektu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
import requests
import psycopg2
from psycopg2.extras import execute_values
from loguru import logger

# Konfiguracja loggera
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")

# Stałe
DYDX_API_URL = "https://indexer.dydx.trade/v4"


def get_fills_from_api(
    address: str,
    subaccount_number: int = 0,
    limit: int = 100,
    ticker: Optional[str] = None,
    created_on_or_after: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Pobiera fill'e z dYdX API.
    
    Zapytanie:
      GET /fills?address={addr}&subaccountNumber={num}&limit={limit}
    
    Odpowiedź:
      {
        "fills": [
          {
            "id": "uuid",
            "side": "SELL",
            "liquidity": "TAKER",
            "type": "LIQUIDATED",
            "market": "OP-USD",
            "marketType": "PERPETUAL",
            "price": "0.51",
            "size": "303",
            "fee": "2.31795",
            "affiliateRevShare": "0",
            "createdAt": "2025-06-21T21:25:36.417Z",
            "createdAtHeight": "48103678",
            "orderId": null,
            "clientMetadata": null,
            "subaccountNumber": 0
          },
          ...
        ]
      }
    """
    url = f"{DYDX_API_URL}/fills"
    params = {
        'address': address,
        'subaccountNumber': subaccount_number,
        'limit': min(limit, 100)
    }
    
    if ticker:
        params['ticker'] = ticker
    if created_on_or_after:
        params['createdOnOrAfter'] = created_on_or_after.isoformat().replace('+00:00', 'Z')
    
    logger.info(f"Wysyłam zapytanie: GET {url}")
    logger.info(f"Parametry: {json.dumps(params, indent=2)}")
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    fills = data.get('fills', [])
    
    logger.info(f"Otrzymano {len(fills)} fill'ów")
    return fills


def get_db_connection():
    """Tworzy połączenie z bazą danych."""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("Brak DATABASE_URL w .env")
    
    return psycopg2.connect(database_url)


def ensure_trader_exists(
    conn, 
    address: str, 
    subaccount_number: int,
    rank: Optional[int] = None,
    estimated_rewards: Optional[float] = None
) -> int:
    """
    Upewnia się, że trader istnieje w dydx_traders. Zwraca trader_id.
    Jeśli trader istnieje i podano rank/estimated_rewards, aktualizuje je.
    """
    with conn.cursor() as cur:
        # Sprawdź czy istnieje
        cur.execute("""
            SELECT id FROM dydx_traders 
            WHERE address = %s AND subaccount_number = %s
        """, (address, subaccount_number))
        
        row = cur.fetchone()
        if row:
            trader_id = row[0]
            # Aktualizuj rank i estimated_rewards jeśli podano
            if rank is not None or estimated_rewards is not None:
                updates = []
                params = []
                if rank is not None:
                    updates.append("rank = %s")
                    params.append(rank)
                if estimated_rewards is not None:
                    updates.append("estimated_rewards = %s")
                    params.append(estimated_rewards)
                updates.append("updated_at = NOW()")
                params.append(trader_id)
                
                cur.execute(f"""
                    UPDATE dydx_traders 
                    SET {', '.join(updates)}
                    WHERE id = %s
                """, params)
                conn.commit()
                logger.debug(f"Zaktualizowano tradera {address}:{subaccount_number} (rank={rank}, rewards={estimated_rewards})")
            return trader_id
        
        # Utwórz nowego tradera
        cur.execute("""
            INSERT INTO dydx_traders (
                address, subaccount_number, first_seen_at, last_seen_at, is_active,
                rank, estimated_rewards
            )
            VALUES (%s, %s, NOW(), NOW(), TRUE, %s, %s)
            RETURNING id
        """, (address, subaccount_number, rank, estimated_rewards))
        
        trader_id = cur.fetchone()[0]
        conn.commit()
        
        logger.info(f"Utworzono nowego tradera: {address}:{subaccount_number} (ID: {trader_id}, rank={rank}, rewards={estimated_rewards})")
        return trader_id


def insert_fills(conn, trader_id: int, address: str, subaccount_number: int, fills: List[Dict[str, Any]]) -> int:
    """
    Wstawia fill'e do tabeli dydx_fills.
    Zwraca liczbę wstawionych rekordów.
    """
    if not fills:
        return 0
    
    observed_at = datetime.now(timezone.utc)
    
    # Przygotuj dane do wstawienia
    rows = []
    for fill in fills:
        # Parsuj timestamp
        created_at_str = fill.get('createdAt', '')
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        except:
            created_at = observed_at
        
        # Mapowanie pól API -> tabela
        row = (
            trader_id,
            address,
            subaccount_number,
            fill.get('id', ''),                    # fill_id
            fill.get('market', 'UNKNOWN'),         # ticker (API używa 'market')
            fill.get('side', 'UNKNOWN'),           # side
            float(fill.get('price', 0)),           # price
            float(fill.get('size', 0)),            # size
            float(fill.get('fee', 0)),             # fee
            None,                                   # realized_pnl (API nie zwraca)
            created_at,                            # effective_at (używamy createdAt)
            created_at,                            # created_at
            observed_at,                           # observed_at
            json.dumps({                           # metadata - dodatkowe pola z API
                'liquidity': fill.get('liquidity'),
                'type': fill.get('type'),
                'marketType': fill.get('marketType'),
                'affiliateRevShare': fill.get('affiliateRevShare'),
                'createdAtHeight': fill.get('createdAtHeight'),
                'orderId': fill.get('orderId'),
                'clientMetadata': fill.get('clientMetadata'),
                # Dodatkowe pola o pozycji przed transakcją
                'positionSizeBefore': fill.get('positionSizeBefore'),
                'entryPriceBefore': fill.get('entryPriceBefore'),
                'positionSideBefore': fill.get('positionSideBefore')
            })
        )
        rows.append(row)
    
    # Wstaw z ON CONFLICT (deduplikacja)
    insert_sql = """
        INSERT INTO dydx_fills (
            trader_id, address, subaccount_number, fill_id, ticker, side,
            price, size, fee, realized_pnl, effective_at, created_at, 
            observed_at, metadata
        ) VALUES %s
        ON CONFLICT (fill_id, address, subaccount_number) DO UPDATE SET
            observed_at = EXCLUDED.observed_at,
            metadata = EXCLUDED.metadata
    """
    
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, rows)
        inserted = cur.rowcount
    
    conn.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description='Pobierz fill\'e z dYdX i zapisz do bazy')
    parser.add_argument('--address', type=str, help='Adres dYdX Chain (dydx1...)')
    parser.add_argument('--subaccount', type=int, default=0, help='Numer subkonta (domyślnie 0)')
    parser.add_argument('--limit', type=int, default=100, help='Limit fill\'ów (max 100)')
    parser.add_argument('--ticker', type=str, help='Filtruj po tickerze (np. BTC-USD)')
    parser.add_argument('--use-env', action='store_true', help='Użyj adresów z .env (WALLET_ADDRESS_FROM_PIOTREK_*)')
    parser.add_argument('--use-top-traders', action='store_true', help='Użyj adresów TOP_TRADER_* z .env (linie 53-58)')
    parser.add_argument('--from-csv', type=str, help='Wczytaj adresy z pliku CSV (format: Rank;Trader;Estimated Rewards)')
    
    args = parser.parse_args()
    
    load_dotenv()
    
    # Zbierz adresy do sprawdzenia
    # Format: (address, subaccount_number, rank, estimated_rewards)
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
                if len(parts) >= 3:
                    rank = int(parts[0])
                    address = parts[1].strip()
                    estimated_rewards = float(parts[2])
                    
                    if address.startswith('dydx1'):
                        addresses.append((address, 0, rank, estimated_rewards))
            except (ValueError, IndexError) as e:
                logger.warning(f"Błąd parsowania linii {line_num}: {line} - {e}")
                continue
        
        logger.info(f"Wczytano {len(addresses)} adresów z CSV")
    elif args.address:
        addresses.append((args.address, args.subaccount, None, None))
    elif args.use_top_traders:
        # Adresy TOP_TRADER_* z .env (linie 53-58)
        for i in range(1, 7):
            addr = os.getenv(f'TOP_TRADER_{i}')
            if addr and addr.startswith('dydx1'):
                addresses.append((addr, 0, None, None))
        logger.info(f"Załadowano {len(addresses)} adresów TOP_TRADER_* z .env")
    elif args.use_env:
        # Adresy z .env
        addr1 = os.getenv('WALLET_ADDRESS_FROM_PIOTREK_1')
        addr2 = os.getenv('WALLET_ADDRESS_FROM_PIOTREK_2')
        dydx_addr = os.getenv('DYDYX_ADDRESS')
        
        for addr in [addr1, addr2, dydx_addr]:
            if addr and addr.startswith('dydx1'):
                addresses.append((addr, 0, None, None))
    else:
        # Domyślny adres testowy
        addresses.append(('dydx1gqc3l5nqrajex67al34p5p47s5pcvguv4u2j49', 0, None, None))
    
    if not addresses:
        logger.error("Brak adresów do sprawdzenia. Użyj --address lub --use-env")
        sys.exit(1)
    
    logger.info(f"Adresy do sprawdzenia: {len(addresses)}")
    for item in addresses[:10]:  # Pokaż tylko pierwsze 10
        if len(item) == 4:
            addr, sub, rank, rewards = item
            if rank is not None:
                logger.info(f"  - {addr}:{sub} (rank={rank}, rewards={rewards:.2f})")
            else:
                logger.info(f"  - {addr}:{sub}")
        else:
            addr, sub = item[:2]
            logger.info(f"  - {addr}:{sub}")
    if len(addresses) > 10:
        logger.info(f"  ... i {len(addresses) - 10} więcej")
    
    # Połącz z bazą
    try:
        conn = get_db_connection()
        logger.info("Połączono z bazą danych")
    except Exception as e:
        logger.error(f"Błąd połączenia z bazą: {e}")
        sys.exit(1)
    
    total_inserted = 0
    
    try:
        for item in addresses:
            # Rozpakuj adres, subaccount, rank, estimated_rewards
            if len(item) == 4:
                address, subaccount_number, rank, estimated_rewards = item
            else:
                address, subaccount_number = item[:2]
                rank, estimated_rewards = None, None
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Przetwarzanie: {address}:{subaccount_number}")
            if rank is not None:
                logger.info(f"Rank: {rank}, Estimated Rewards: {estimated_rewards:.2f}")
            logger.info(f"{'='*60}")
            
            # Zapewnij istnienie tradera i zaktualizuj rank/rewards
            trader_id = ensure_trader_exists(
                conn, 
                address, 
                subaccount_number,
                rank=rank,
                estimated_rewards=estimated_rewards
            )
            
            # Pobierz fill'e z API
            try:
                fills = get_fills_from_api(
                    address=address,
                    subaccount_number=subaccount_number,
                    limit=args.limit,
                    ticker=args.ticker
                )
            except requests.exceptions.HTTPError as e:
                logger.warning(f"Błąd API: {e}")
                continue
            except Exception as e:
                logger.error(f"Nieoczekiwany błąd: {e}")
                continue
            
            if not fills:
                logger.info("Brak fill'ów do zapisania")
                continue
            
            # Pokaż przykładowe fill'e
            logger.info(f"\nPrzykładowe fill'e ({min(3, len(fills))} z {len(fills)}):")
            for fill in fills[:3]:
                logger.info(f"  - {fill.get('market')} {fill.get('side')} {fill.get('size')} @ {fill.get('price')} ({fill.get('type')})")
            
            # Zapisz fill'e do bazy
            inserted = insert_fills(conn, trader_id, address, subaccount_number, fills)
            
            logger.success(f"Zapisano {inserted} fill'ów do bazy (trader_id: {trader_id})")
            total_inserted += inserted
    
    finally:
        conn.close()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"PODSUMOWANIE: Zapisano łącznie {total_inserted} fill'ów")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()

