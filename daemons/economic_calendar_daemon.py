#!/usr/bin/env python3
"""
Economic Calendar Daemon
========================
Daemon do zarządzania kalendarzem wydarzeń ekonomicznych.

Źródła:
- FOMC meetings (Federal Reserve)
- CPI releases (Bureau of Labor Statistics)
- NFP releases (Bureau of Labor Statistics)
- GDP releases (Bureau of Economic Analysis)

Interwał:
- Codziennie o 00:00 UTC (sprawdza i dodaje nowe wydarzenia)

Użycie:
    python daemons/economic_calendar_daemon.py [--once] [--update-all]
"""

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Dodaj src do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

from providers.economic_calendar_provider import EconomicCalendarProvider
from database.models import EconomicCalendar, Base

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class EconomicCalendarDaemon:
    """
    Daemon do zarządzania kalendarzem wydarzeń ekonomicznych.
    
    Codziennie sprawdza i dodaje nowe wydarzenia do bazy.
    """
    
    # Interwał w sekundach (24 godziny)
    UPDATE_INTERVAL = 86400  # 24 godziny
    
    def __init__(self, database_url: str):
        """
        Inicjalizacja daemona.
        
        Args:
            database_url: URL do bazy PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Provider
        self.provider = EconomicCalendarProvider()
        
        # Stan
        self.running = True
        self.last_update = None
        
        # Obsługa sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("📅 Economic Calendar Daemon initialized")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów zatrzymania."""
        logger.info(f"Otrzymano sygnał {signum}, zatrzymuję daemon...")
        self.running = False
    
    def ensure_tables(self):
        """Upewnij się, że tabele istnieją."""
        Base.metadata.create_all(self.engine, tables=[EconomicCalendar.__table__])
        logger.info("✓ Tabela manual_economic_calendar gotowa")
    
    def _save_event(self, session, event: dict) -> bool:
        """
        Zapisz pojedyncze wydarzenie ekonomiczne.
        
        Używa UPSERT dla PostgreSQL.
        """
        try:
            stmt = pg_insert(EconomicCalendar).values(
                event_date=event['event_date'],
                event_name=event['event_name'],
                event_type=event['event_type'],
                country=event.get('country', 'US'),
                importance=event.get('importance', 'high'),
                notes=event.get('notes'),
                source='economic_calendar_provider',
            ).on_conflict_do_update(
                constraint='uq_economic_event',
                set_={
                    'event_name': event['event_name'],
                    'event_type': event['event_type'],
                    'importance': event.get('importance', 'high'),
                    'notes': event.get('notes'),
                    'updated_at': datetime.now(timezone.utc),
                }
            )
            session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Błąd zapisu wydarzenia {event.get('event_name')}: {e}")
            return False
    
    def update_calendar(self, days_ahead: int = 365) -> int:
        """
        Zaktualizuj kalendarz wydarzeń ekonomicznych.
        
        Args:
            days_ahead: Liczba dni do przodu do pobrania
            
        Returns:
            Liczba zapisanych/aktualizowanych wydarzeń
        """
        logger.info(f"📅 Aktualizuję kalendarz wydarzeń ekonomicznych ({days_ahead} dni do przodu)...")
        
        # Pobierz wszystkie wydarzenia
        events = self.provider.get_all_events(
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=days_ahead)
        )
        
        if not events:
            logger.warning("Brak wydarzeń do zapisania")
            return 0
        
        saved = 0
        session = self.Session()
        try:
            for event in events:
                if self._save_event(session, event):
                    saved += 1
                    logger.debug(f"  ✓ {event['event_date'].strftime('%Y-%m-%d')} | {event['event_type']:4s} | {event['event_name']}")
            
            session.commit()
            self.last_update = datetime.now(timezone.utc)
            logger.info(f"✅ Zapisano/aktualizowano {saved}/{len(events)} wydarzeń")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Błąd zapisu kalendarza: {e}")
        finally:
            session.close()
        
        return saved
    
    def get_upcoming_events(self, days: int = 7) -> int:
        """
        Pobierz nadchodzące wydarzenia z bazy.
        
        Args:
            days: Liczba dni do przodu
            
        Returns:
            Liczba nadchodzących wydarzeń
        """
        session = self.Session()
        try:
            now = datetime.now(timezone.utc)
            end_date = now + timedelta(days=days)
            
            result = session.execute(
                text("""
                    SELECT event_date, event_name, event_type, importance
                    FROM manual_economic_calendar
                    WHERE event_date >= :now AND event_date <= :end_date
                    ORDER BY event_date
                """),
                {"now": now, "end_date": end_date}
            )
            
            events = result.fetchall()
            
            if events:
                logger.info(f"\n📊 Nadchodzące wydarzenia (następne {days} dni):")
                for event in events:
                    logger.info(f"  {event[0].strftime('%Y-%m-%d %H:%M')} | {event[2]:4s} | {event[1]} ({event[3]})")
            else:
                logger.info(f"Brak nadchodzących wydarzeń w ciągu {days} dni")
            
            return len(events)
            
        except Exception as e:
            logger.error(f"Błąd pobierania wydarzeń: {e}")
            return 0
        finally:
            session.close()
    
    def _should_update(self) -> bool:
        """Sprawdź czy pora na aktualizację."""
        if self.last_update is None:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_update).total_seconds()
        return elapsed >= self.UPDATE_INTERVAL
    
    def run_once(self):
        """Wykonaj pojedynczy cykl aktualizacji."""
        logger.info("=" * 60)
        logger.info("🔄 Wykonuję pojedynczy cykl...")
        
        self.update_calendar(days_ahead=365)
        self.get_upcoming_events(days=30)
        
        logger.info("=" * 60)
    
    def run(self):
        """
        Główna pętla daemona.
        
        Aktualizuje kalendarz codziennie o 00:00 UTC.
        """
        logger.info("=" * 60)
        logger.info("🚀 Economic Calendar Daemon - START")
        logger.info(f"   Update interval: {self.UPDATE_INTERVAL}s (24h)")
        logger.info("=" * 60)
        
        # Pierwsza aktualizacja od razu
        self.update_calendar(days_ahead=365)
        self.get_upcoming_events(days=7)
        
        while self.running:
            try:
                # Sprawdź czy pora na aktualizację
                if self._should_update():
                    self.update_calendar(days_ahead=365)
                    self.get_upcoming_events(days=7)
                
                # Czekaj 1 godzinę przed następnym sprawdzeniem
                for _ in range(3600):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Błąd w głównej pętli: {e}")
                time.sleep(3600)
        
        logger.info("🛑 Economic Calendar Daemon - STOP")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Economic Calendar Daemon")
    parser.add_argument('--once', action='store_true', help='Wykonaj jeden cykl i zakończ')
    parser.add_argument('--update-all', action='store_true', help='Zaktualizuj wszystkie wydarzenia')
    args = parser.parse_args()
    
    # Pobierz DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Ustaw zmienną środowiskową DATABASE_URL")
        sys.exit(1)
    
    # Utwórz daemon
    daemon = EconomicCalendarDaemon(database_url)
    daemon.ensure_tables()
    
    # Tryb działania
    if args.once:
        daemon.run_once()
    elif args.update_all:
        daemon.update_calendar(days_ahead=730)  # 2 lata
    else:
        daemon.run()


if __name__ == "__main__":
    main()

