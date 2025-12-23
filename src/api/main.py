"""
FastAPI Application
===================
Główny plik aplikacji FastAPI dla trends-sniffer API.
"""

from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .events import get_events

# Utwórz aplikację FastAPI
app = FastAPI(
    title="Trends Sniffer API",
    description="API do pobierania wydarzeń regionalnych z danymi OHLCV i GDELT sentiment",
    version="1.0.0"
)

# Dodaj CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji ustaw konkretne domeny
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint główny."""
    return {
        "message": "Trends Sniffer API",
        "version": "1.0.0",
        "endpoints": {
            "/events": "GET - Pobierz wydarzenia regionalne z danymi OHLCV i GDELT",
            "/docs": "Swagger UI dokumentacja",
            "/redoc": "ReDoc dokumentacja"
        }
    }


@app.get("/events")
async def events_endpoint(
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None
):
    """
    Endpoint do pobierania wydarzeń regionalnych.
    
    Parametry query string:
    - time_from: Czas początkowy w formacie ISO (UTC) - domyślnie now()
    - time_to: Czas końcowy w formacie ISO (UTC) - domyślnie 1h wstecz
    - region: Kod regionu (np. 'north_america', 'europe')
    - country: Kody krajów oddzielone przecinkami (np. 'PL,US,DE') - domyślnie 'PL'
    
    Przykłady:
    - /events?country=PL,US
    - /events?region=north_america&time_from=2025-12-22T10:00:00Z&time_to=2025-12-22T12:00:00Z
    """
    from datetime import datetime, timezone
    from .events import get_events
    
    # Parsuj parametry
    time_from_dt = None
    time_to_dt = None
    country_list = None
    
    if time_from:
        try:
            # Obsługa różnych formatów daty
            time_str = time_from.replace('Z', '+00:00')
            if 'T' not in time_str:
                time_str = time_str + 'T00:00:00+00:00'
            time_from_dt = datetime.fromisoformat(time_str)
            if time_from_dt.tzinfo is None:
                time_from_dt = time_from_dt.replace(tzinfo=timezone.utc)
        except ValueError as e:
            logger.warning(f"Nieprawidłowy format time_from: {time_from}, błąd: {e}")
            raise HTTPException(status_code=400, detail=f"Nieprawidłowy format time_from: {time_from}")
    
    if time_to:
        try:
            # Obsługa różnych formatów daty
            time_str = time_to.replace('Z', '+00:00')
            if 'T' not in time_str:
                time_str = time_str + 'T00:00:00+00:00'
            time_to_dt = datetime.fromisoformat(time_str)
            if time_to_dt.tzinfo is None:
                time_to_dt = time_to_dt.replace(tzinfo=timezone.utc)
        except ValueError as e:
            logger.warning(f"Nieprawidłowy format time_to: {time_to}, błąd: {e}")
            raise HTTPException(status_code=400, detail=f"Nieprawidłowy format time_to: {time_to}")
    
    if country:
        country_list = [c.strip().upper() for c in country.split(',') if c.strip()]
    
    return await get_events(
        time_from=time_from_dt,
        time_to=time_to_dt,
        region=region,
        country=country_list
    )


@app.on_event("startup")
async def startup_event():
    """Event uruchamiany przy starcie aplikacji."""
    logger.info("Trends Sniffer API uruchomione")


@app.on_event("shutdown")
async def shutdown_event():
    """Event uruchamiany przy zamykaniu aplikacji."""
    logger.info("Trends Sniffer API zamykane")

