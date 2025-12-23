"""
API Endpoint dla dictionary_region_events
=========================================
Endpoint zwracający wydarzenia regionalne z danymi OHLCV i GDELT sentiment.
"""

import os
from datetime import datetime, timedelta, timezone, time as dt_time
from typing import Optional, List, Tuple
from pathlib import Path
from decimal import Decimal

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from loguru import logger
from dotenv import load_dotenv

from ..database.manager import DatabaseManager

# Załaduj zmienne środowiskowe
load_dotenv()

# Inicjalizuj DatabaseManager
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL nie jest ustawiony w pliku .env")

db_manager = DatabaseManager(database_url=database_url)

# Wczytaj zapytanie SQL
QUERY_FILE = Path(__file__).parent.parent.parent / "database" / "query_dictionary_region_events.sql"
with open(QUERY_FILE, 'r', encoding='utf-8') as f:
    BASE_QUERY = f.read()


def build_query(
    time_from: Optional[datetime] = None,
    time_to: Optional[datetime] = None,
    region: Optional[str] = None,
    country: Optional[List[str]] = None
) -> Tuple[str, dict]:
    """
    Buduje zapytanie SQL z filtrami używając parametrów SQLAlchemy.
    
    Args:
        time_from: Czas początkowy (UTC) - domyślnie now()
        time_to: Czas końcowy (UTC) - domyślnie 1h wstecz
        region: Kod regionu (opcjonalnie)
        country: Lista kodów krajów (domyślnie ['PL'])
    
    Returns:
        Tuple (zapytanie SQL jako string, parametry jako dict)
    """
    # Domyślne wartości
    if time_from is None:
        time_from = datetime.now(timezone.utc)
    if time_to is None:
        time_to = time_from - timedelta(hours=1)
    if country is None:
        country = ['PL']
    
    # Buduj zapytanie z filtrami
    query = BASE_QUERY
    
    # Dodaj filtry WHERE (zapytanie już ma WHERE bsp.multiplier <> 0)
    where_conditions = []
    params = {}
    
    # Filtr po czasie - filtrujemy po occurrence_time z sentiments_sniff
    if time_from:
        where_conditions.append("ss.occurrence_time >= :time_from")
        params['time_from'] = time_from
    
    if time_to:
        where_conditions.append("ss.occurrence_time <= :time_to")
        params['time_to'] = time_to
    
    # Filtr po regionie
    if region:
        where_conditions.append("r.code = :region")
        params['region'] = region
    
    # Filtr po krajach
    if country:
        # Użyj parametru dla każdego kraju lub IN z parametrem
        placeholders = ', '.join([f':country_{i}' for i in range(len(country))])
        where_conditions.append(f"c.iso2_code IN ({placeholders})")
        for i, c in enumerate(country):
            params[f'country_{i}'] = c.upper()
    
    # Dodaj warunki do istniejącego WHERE
    if where_conditions:
        additional_conditions = ' AND ' + ' AND '.join(where_conditions)
        
        # Znajdź miejsce przed ORDER BY
        order_by_pos = query.rfind('ORDER BY')
        if order_by_pos != -1:
            # Dodaj przed ORDER BY
            query = query[:order_by_pos] + additional_conditions + '\n    ' + query[order_by_pos:]
        else:
            # Jeśli nie ma ORDER BY, dodaj na końcu
            query = query.rstrip() + additional_conditions
    
    return query, params


async def get_events(
    time_from: Optional[datetime] = Query(None, description="Czas początkowy (UTC) - domyślnie now()"),
    time_to: Optional[datetime] = Query(None, description="Czas końcowy (UTC) - domyślnie 1h wstecz od time_from"),
    region: Optional[str] = Query(None, description="Kod regionu (np. 'north_america', 'europe')"),
    country: Optional[List[str]] = Query(['PL'], description="Lista kodów krajów (np. ['PL', 'US'])")
) -> JSONResponse:
    """
    Zwraca wydarzenia regionalne z danymi OHLCV i GDELT sentiment.
    
    Parametry:
    - time_from: Czas początkowy (UTC) - domyślnie now()
    - time_to: Czas końcowy (UTC) - domyślnie 1h wstecz od time_from
    - region: Kod regionu (opcjonalnie)
    - country: Lista kodów krajów (domyślnie ['PL'])
    
    Zwraca wszystkie kolumny z zapytania SQL.
    """
    try:
        # Ustaw domyślne wartości
        if time_from is None:
            time_from = datetime.now(timezone.utc)
        if time_to is None:
            time_to = time_from - timedelta(hours=1)
        
        # Buduj zapytanie z parametrami
        query, params = build_query(
            time_from=time_from,
            time_to=time_to,
            region=region,
            country=country
        )
        
        logger.info(f"Wykonuję zapytanie z parametrami: time_from={time_from}, time_to={time_to}, region={region}, country={country}")
        
        # Wykonaj zapytanie z parametrami
        with db_manager.get_session() as session:
            result = session.execute(text(query), params)
            rows = result.fetchall()
            
            # Konwertuj wyniki na listę słowników
            columns = result.keys()
            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    # Konwertuj None
                    if val is None:
                        row_dict[col] = None
                    # Konwertuj datetime na string ISO format
                    elif isinstance(val, datetime):
                        row_dict[col] = val.isoformat()
                    # Konwertuj time na string
                    elif isinstance(val, dt_time):
                        row_dict[col] = val.isoformat()
                    # Konwertuj Decimal na float
                    elif isinstance(val, Decimal):
                        row_dict[col] = float(val)
                    # Konwertuj inne typy na JSON-serializable
                    elif hasattr(val, '__dict__'):
                        row_dict[col] = str(val)
                    else:
                        row_dict[col] = val
                data.append(row_dict)
        
        logger.info(f"Zwracam {len(data)} wyników")
        
        return JSONResponse(content={
            "count": len(data),
            "data": data,
            "parameters": {
                "time_from": time_from.isoformat(),
                "time_to": time_to.isoformat(),
                "region": region,
                "country": country
            }
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas wykonywania zapytania: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")

