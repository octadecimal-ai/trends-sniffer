#!/usr/bin/env python3
"""
Sentiment Propagation Daemon
=============================
Daemon do obliczania i zapisywania metryk propagacji sentymentu między regionami.

Analizuje jak sentyment propaguje się przez strefy czasowe:
- APAC → EU (lag ~4h)
- EU → US (lag ~4h)
- US → APAC (overnight, lag ~12h)

Interwał:
- Co godzinę (3600 sekund)

Użycie:
    python daemons/sentiment_propagation_daemon.py [--once] [--backfill]
"""

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

# Dodaj src do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

from analyzers.sentiment_propagation_analyzer import SentimentPropagationAnalyzer
from database.models import SentimentPropagation, Base

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SentimentPropagationDaemon:
    """
    Daemon do obliczania i zapisywania metryk propagacji sentymentu.
    
    Oblicza metryki propagacji co godzinę i zapisuje je do bazy.
    """
    
    # Interwał w sekundach (1 godzina)
    UPDATE_INTERVAL = 3600  # 1 godzina
    
    def __init__(self, database_url: str):
        """
        Inicjalizacja daemona.
        
        Args:
            database_url: URL do bazy PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Analizator
        self.analyzer = SentimentPropagationAnalyzer(database_url)
        
        # Stan
        self.running = True
        self.last_update = None
        
        # Obsługa sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🌍 Sentiment Propagation Daemon initialized")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów zatrzymania."""
        logger.info(f"Otrzymano sygnał {signum}, zatrzymuję daemon...")
        self.running = False
    
    def ensure_tables(self):
        """Upewnij się, że tabele istnieją."""
        try:
            Base.metadata.create_all(self.engine, tables=[SentimentPropagation.__table__], checkfirst=True)
            logger.info("✓ Tabela google_trends_sentiment_propagation gotowa")
        except Exception as e:
            # Tabela może już istnieć z migracji
            logger.debug(f"Tabela google_trends_sentiment_propagation: {e}")
            logger.info("✓ Tabela google_trends_sentiment_propagation gotowa (istnieje)")
    
    def _save_propagation_metrics(self, metrics: dict) -> bool:
        """
        Zapisz metryki propagacji do bazy danych.
        
        Używa UPSERT dla PostgreSQL.
        """
        session = self.Session()
        try:
            insert_stmt = pg_insert(SentimentPropagation).values(
                timestamp=metrics['timestamp'],
                asia_to_eu_corr=metrics.get('asia_to_eu_corr'),
                eu_to_us_corr=metrics.get('eu_to_us_corr'),
                us_to_asia_corr=metrics.get('us_to_asia_corr'),
                propagation_speed_hours=metrics.get('propagation_speed_hours'),
                asia_to_eu_amplification=metrics.get('asia_to_eu_amplification'),
                eu_to_us_amplification=metrics.get('eu_to_us_amplification'),
                us_to_asia_amplification=metrics.get('us_to_asia_amplification'),
                leading_region=metrics.get('leading_region'),
                gai_score=metrics.get('gai_score'),
                asia_sentiment=metrics.get('asia_sentiment'),
                eu_sentiment=metrics.get('eu_sentiment'),
                us_sentiment=metrics.get('us_sentiment'),
                asia_measurements_count=metrics.get('asia_measurements_count', 0),
                eu_measurements_count=metrics.get('eu_measurements_count', 0),
                us_measurements_count=metrics.get('us_measurements_count', 0),
                calculation_window_hours=metrics.get('calculation_window_hours', 24),
            )
            stmt = insert_stmt.on_conflict_do_update(
                constraint='google_trends_sentiment_propagation_timestamp_key',
                set_={
                    'asia_to_eu_corr': insert_stmt.excluded.asia_to_eu_corr,
                    'eu_to_us_corr': insert_stmt.excluded.eu_to_us_corr,
                    'us_to_asia_corr': insert_stmt.excluded.us_to_asia_corr,
                    'propagation_speed_hours': insert_stmt.excluded.propagation_speed_hours,
                    'asia_to_eu_amplification': insert_stmt.excluded.asia_to_eu_amplification,
                    'eu_to_us_amplification': insert_stmt.excluded.eu_to_us_amplification,
                    'us_to_asia_amplification': insert_stmt.excluded.us_to_asia_amplification,
                    'leading_region': insert_stmt.excluded.leading_region,
                    'gai_score': insert_stmt.excluded.gai_score,
                    'asia_sentiment': insert_stmt.excluded.asia_sentiment,
                    'eu_sentiment': insert_stmt.excluded.eu_sentiment,
                    'us_sentiment': insert_stmt.excluded.us_sentiment,
                    'asia_measurements_count': insert_stmt.excluded.asia_measurements_count,
                    'eu_measurements_count': insert_stmt.excluded.eu_measurements_count,
                    'us_measurements_count': insert_stmt.excluded.us_measurements_count,
                }
            )
            session.execute(stmt)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Błąd zapisu metryk propagacji: {e}")
            return False
        finally:
            session.close()
    
    def calculate_and_save(self, timestamp: Optional[datetime] = None) -> bool:
        """
        Oblicz i zapisz metryki propagacji dla danego timestampu.
        
        Args:
            timestamp: Timestamp do analizy (domyślnie teraz)
            
        Returns:
            True jeśli sukces
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        logger.info(f"📊 Obliczam metryki propagacji dla {timestamp.strftime('%Y-%m-%d %H:%M:%S')}...")
        
        # Oblicz metryki
        metrics = self.analyzer.analyze_propagation(timestamp, window_hours=24)
        
        if not metrics:
            logger.warning("Nie udało się obliczyć metryk propagacji")
            return False
        
        # Zapisz do bazy
        if self._save_propagation_metrics(metrics):
            logger.info(
                f"✅ Zapisano metryki: leading={metrics.get('leading_region')}, "
                f"GAI={metrics.get('gai_score', 0):.2f}, "
                f"speed={metrics.get('propagation_speed_hours', 0):.1f}h"
            )
            return True
        else:
            logger.error("Nie udało się zapisać metryk propagacji")
            return False
    
    def backfill(self, days_back: int = 7, hours_step: int = 1):
        """
        Wypełnij historyczne metryki propagacji.
        
        Args:
            days_back: Liczba dni wstecz
            hours_step: Krok w godzinach (domyślnie 1h)
        """
        logger.info(f"📥 Wypełniam historyczne metryki propagacji ({days_back} dni wstecz, krok {hours_step}h)...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        current_time = start_time
        saved = 0
        failed = 0
        
        while current_time <= end_time:
            if self.calculate_and_save(current_time):
                saved += 1
            else:
                failed += 1
            
            current_time += timedelta(hours=hours_step)
        
        logger.info(f"✅ Wypełniono: {saved} sukcesów, {failed} błędów")
    
    def _should_update(self) -> bool:
        """Sprawdź czy pora na aktualizację."""
        if self.last_update is None:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_update).total_seconds()
        return elapsed >= self.UPDATE_INTERVAL
    
    def run_once(self):
        """Wykonaj pojedynczy cykl obliczeń."""
        logger.info("=" * 60)
        logger.info("🔄 Wykonuję pojedynczy cykl...")
        
        self.calculate_and_save()
        
        logger.info("=" * 60)
    
    def run(self):
        """
        Główna pętla daemona.
        
        Oblicza metryki propagacji co godzinę.
        """
        logger.info("=" * 60)
        logger.info("🚀 Sentiment Propagation Daemon - START")
        logger.info(f"   Update interval: {self.UPDATE_INTERVAL}s (1h)")
        logger.info("=" * 60)
        
        # Pierwsza aktualizacja od razu
        self.calculate_and_save()
        
        while self.running:
            try:
                # Sprawdź czy pora na aktualizację
                if self._should_update():
                    self.calculate_and_save()
                    self.last_update = datetime.now(timezone.utc)
                
                # Czekaj 5 minut przed następnym sprawdzeniem
                for _ in range(300):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Błąd w głównej pętli: {e}")
                time.sleep(300)
        
        logger.info("🛑 Sentiment Propagation Daemon - STOP")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Sentiment Propagation Daemon")
    parser.add_argument('--once', action='store_true', help='Wykonaj jeden cykl i zakończ')
    parser.add_argument('--backfill', type=int, metavar='DAYS', help='Wypełnij historyczne dane (liczba dni wstecz)')
    args = parser.parse_args()
    
    # Pobierz DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Ustaw zmienną środowiskową DATABASE_URL")
        sys.exit(1)
    
    # Utwórz daemon
    daemon = SentimentPropagationDaemon(database_url)
    daemon.ensure_tables()
    
    # Tryb działania
    if args.backfill:
        daemon.backfill(days_back=args.backfill, hours_step=1)
    elif args.once:
        daemon.run_once()
    else:
        daemon.run()


if __name__ == "__main__":
    main()

