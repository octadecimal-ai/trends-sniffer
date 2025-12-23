"""
API Endpoint dla dictionary_region_events
=========================================
Endpoint zwracający wydarzenia regionalne z danymi OHLCV i GDELT sentiment.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from pathlib import Path

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
) -> str:
    """
    Buduje zapytanie SQL z filtrami.
    
    Args:
        time_from: Czas początkowy (UTC) - domyślnie now()
        time_to: Czas końcowy (UTC) - domyślnie 1h wstecz
        region: Kod regionu (opcjonalnie)
        country: Lista kodów krajów (domyślnie ['PL'])
    
    Returns:
        Zapytanie SQL jako string
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
    
    # Filtr po czasie - filtrujemy po occurrence_time z sentiments_sniff
    if time_from:
        time_from_str = time_from.isoformat()
        where_conditions.append(f"ss.occurrence_time >= '{time_from_str}'")
    
    if time_to:
        time_to_str = time_to.isoformat()
        where_conditions.append(f"ss.occurrence_time <= '{time_to_str}'")
    
    # Filtr po regionie
    if region:
        # Escapuj pojedyncze cudzysłowy (na wypadek)
        region_escaped = region.replace("'", "''")
        where_conditions.append(f"r.code = '{region_escaped}'")
    
    # Filtr po krajach
    if country:
        # Escapuj pojedyncze cudzysłowy w kodach krajów
        country_escaped = [c.replace("'", "''") for c in country]
        country_list = "', '".join(country_escaped)
        where_conditions.append(f"c.iso2_code IN ('{country_list}')")
    
    # Dodaj warunki do istniejącego WHERE
    if where_conditions:
        additional_conditions = ' AND ' + ' AND '.join(where_conditions)
        
        # Znajdź miejsce przed ORDER BY
        order_by_pos = query.rfind('ORDER BY')
        if order_by_pos != -1:
            # Znajdź linię z komentarzem o opcjonalnych filtrach (jeśli istnieje)
            comment_pos = query.rfind('-- Opcjonalne filtry', 0, order_by_pos)
            if comment_pos != -1:
                # Zastąp komentarz warunkami
                # Znajdź koniec linii z komentarzem
                comment_end = query.find('\n', comment_pos)
                if comment_end != -1:
                    query = query[:comment_pos] + additional_conditions + '\n' + query[comment_end:]
                else:
                    query = query[:comment_pos] + additional_conditions + '\n' + query[order_by_pos:]
            else:
                # Jeśli nie ma komentarza, dodaj przed ORDER BY
                query = query[:order_by_pos] + additional_conditions + '\n' + query[order_by_pos:]
        else:
            # Jeśli nie ma ORDER BY, dodaj na końcu
            query = query.rstrip() + additional_conditions
    
    return query


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
        
        # Buduj zapytanie
        query = build_query(
            time_from=time_from,
            time_to=time_to,
            region=region,
            country=country
        )
        
        logger.info(f"Wykonuję zapytanie z parametrami: time_from={time_from}, time_to={time_to}, region={region}, country={country}")
        
        # Wykonaj zapytanie
        with db_manager.get_session() as session:
            result = session.execute(text(query))
            rows = result.fetchall()
            
            # Konwertuj wyniki na listę słowników
            columns = result.keys()
            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    # Konwertuj datetime na string ISO format
                    if isinstance(val, datetime):
                        row_dict[col] = val.isoformat()
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

