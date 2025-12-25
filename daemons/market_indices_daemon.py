#!/usr/bin/env python3
"""
Market Indices Daemon
=====================
Daemon do pobierania danych z tradycyjnych rynków finansowych.

Źródła:
- Yahoo Finance: S&P 500, NASDAQ, VIX, DXY, Gold, Treasury Yields
- Alternative.me: Fear & Greed Index

Interwały:
- Market Indices: co godzinę (podczas sesji US 14:30-21:00 UTC)
- Fear & Greed: raz dziennie (aktualizacja ~00:00 UTC)

Użycie:
    python daemons/market_indices_daemon.py [--once] [--historical-days N]
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

from providers.market_data_provider import MarketDataProvider, FearGreedProvider
from database.models import MarketIndex, FearGreedIndex, Base

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class MarketIndicesDaemon:
    """
    Daemon do zbierania danych rynkowych.
    
    Obsługuje:
    - Market Indices z Yahoo Finance
    - Fear & Greed Index z alternative.me
    """
    
    # Interwały w sekundach
    INDICES_INTERVAL = 3600  # 1 godzina
    FEAR_GREED_INTERVAL = 86400  # 24 godziny
    
    def __init__(self, database_url: str):
        """
        Inicjalizacja daemona.
        
        Args:
            database_url: URL do bazy PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Providery
        self.market_provider = MarketDataProvider()
        self.fg_provider = FearGreedProvider()
        
        # Stan
        self.running = True
        self.last_indices_fetch = None
        self.last_fg_fetch = None
        
        # Obsługa sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🏦 Market Indices Daemon initialized")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów zatrzymania."""
        logger.info(f"Otrzymano sygnał {signum}, zatrzymuję daemon...")
        self.running = False
    
    def ensure_tables(self):
        """Upewnij się, że tabele istnieją."""
        # Utwórz tabele jeśli nie istnieją
        Base.metadata.create_all(self.engine, tables=[
            MarketIndex.__table__,
            FearGreedIndex.__table__,
        ])
        logger.info("✓ Tabele market_indices i alternative_me_fear_greed_index gotowe")
    
    def _save_market_index(self, session, data: dict) -> bool:
        """
        Zapisz pojedynczy indeks rynkowy.
        
        Używa UPSERT dla PostgreSQL.
        """
        try:
            stmt = pg_insert(MarketIndex).values(
                timestamp=data['timestamp'],
                symbol=data['symbol'],
                name=data['name'],
                value=data['value'],
                open=data.get('open'),
                high=data.get('high'),
                low=data.get('low'),
                close=data.get('close'),
                volume=data.get('volume'),
                change_1h=data.get('change_1h'),
                change_24h=data.get('change_24h'),
                source=data.get('source', 'yfinance'),
            ).on_conflict_do_update(
                constraint='uq_market_index',
                set_={
                    'value': data['value'],
                    'open': data.get('open'),
                    'high': data.get('high'),
                    'low': data.get('low'),
                    'close': data.get('close'),
                    'volume': data.get('volume'),
                    'change_1h': data.get('change_1h'),
                    'change_24h': data.get('change_24h'),
                }
            )
            session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Błąd zapisu indeksu {data.get('name')}: {e}")
            return False
    
    def _save_fear_greed(self, session, data: dict) -> bool:
        """
        Zapisz Fear & Greed Index.
        
        Używa UPSERT dla PostgreSQL.
        """
        try:
            stmt = pg_insert(FearGreedIndex).values(
                timestamp=data['timestamp'],
                value=data['value'],
                classification=data['classification'],
                value_change_24h=data.get('value_change_24h'),
                value_change_7d=data.get('value_change_7d'),
                time_until_update=data.get('time_until_update'),
                source=data.get('source', 'alternative.me'),
            ).on_conflict_do_update(
                constraint='uq_fear_greed',
                set_={
                    'value': data['value'],
                    'classification': data['classification'],
                    'value_change_24h': data.get('value_change_24h'),
                    'value_change_7d': data.get('value_change_7d'),
                }
            )
            session.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Błąd zapisu Fear & Greed: {e}")
            return False
    
    def fetch_indices(self) -> int:
        """
        Pobierz i zapisz aktualne indeksy rynkowe.
        
        Returns:
            Liczba zapisanych indeksów
        """
        logger.info("📊 Pobieram indeksy rynkowe...")
        
        indices = self.market_provider.get_all_indices()
        if not indices:
            logger.warning("Brak danych z Yahoo Finance")
            return 0
        
        saved = 0
        session = self.Session()
        try:
            for data in indices:
                if self._save_market_index(session, data):
                    saved += 1
                    logger.debug(f"  ✓ {data['name']}: {data['value']:.2f}")
            
            session.commit()
            self.last_indices_fetch = datetime.now(timezone.utc)
            logger.info(f"✅ Zapisano {saved}/{len(indices)} indeksów")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Błąd zapisu indeksów: {e}")
        finally:
            session.close()
        
        return saved
    
    def fetch_fear_greed(self) -> bool:
        """
        Pobierz i zapisz Fear & Greed Index.
        
        Returns:
            True jeśli sukces
        """
        logger.info("😱 Pobieram Fear & Greed Index...")
        
        data = self.fg_provider.get_with_context()
        if not data:
            logger.warning("Brak danych z alternative.me")
            return False
        
        session = self.Session()
        try:
            success = self._save_fear_greed(session, data)
            session.commit()
            
            if success:
                self.last_fg_fetch = datetime.now(timezone.utc)
                logger.info(f"✅ Fear & Greed: {data['value']} ({data['classification']})")
                if data.get('value_change_24h'):
                    logger.info(f"   Zmiana 24h: {data['value_change_24h']:+d}")
            
            return success
            
        except Exception as e:
            session.rollback()
            logger.error(f"Błąd zapisu Fear & Greed: {e}")
            return False
        finally:
            session.close()
    
    def fetch_historical(self, days: int = 30):
        """
        Pobierz dane historyczne.
        
        Args:
            days: Liczba dni wstecz
        """
        logger.info(f"📚 Pobieram dane historyczne ({days} dni)...")
        
        # Fear & Greed - historyczne
        fg_history = self.fg_provider.get_historical(limit=days)
        if fg_history:
            session = self.Session()
            try:
                saved = 0
                for data in fg_history:
                    if self._save_fear_greed(session, data):
                        saved += 1
                session.commit()
                logger.info(f"✅ Fear & Greed historyczne: {saved}/{len(fg_history)}")
            except Exception as e:
                session.rollback()
                logger.error(f"Błąd zapisu historii Fear & Greed: {e}")
            finally:
                session.close()
        
        # Market Indices - historyczne
        indices_names = ['SPX', 'VIX', 'DXY', 'NASDAQ', 'GOLD', 'TNX']
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        session = self.Session()
        try:
            total_saved = 0
            for name in indices_names:
                history = self.market_provider.get_historical(name, start=start_date)
                for data in history:
                    if self._save_market_index(session, data):
                        total_saved += 1
                logger.debug(f"  ✓ {name}: {len(history)} rekordów")
            
            session.commit()
            logger.info(f"✅ Market Indices historyczne: {total_saved} rekordów")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Błąd zapisu historii indeksów: {e}")
        finally:
            session.close()
    
    def _should_fetch_indices(self) -> bool:
        """Sprawdź czy pora na pobranie indeksów."""
        if self.last_indices_fetch is None:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_indices_fetch).total_seconds()
        return elapsed >= self.INDICES_INTERVAL
    
    def _should_fetch_fear_greed(self) -> bool:
        """Sprawdź czy pora na pobranie Fear & Greed."""
        if self.last_fg_fetch is None:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_fg_fetch).total_seconds()
        return elapsed >= self.FEAR_GREED_INTERVAL
    
    def run_once(self):
        """Wykonaj pojedynczy cykl pobierania."""
        logger.info("=" * 60)
        logger.info("🔄 Wykonuję pojedynczy cykl...")
        
        self.fetch_indices()
        self.fetch_fear_greed()
        
        logger.info("=" * 60)
    
    def run(self):
        """
        Główna pętla daemona.
        
        Pobiera dane w odpowiednich interwałach.
        """
        logger.info("=" * 60)
        logger.info("🚀 Market Indices Daemon - START")
        logger.info(f"   Indices interval: {self.INDICES_INTERVAL}s")
        logger.info(f"   Fear & Greed interval: {self.FEAR_GREED_INTERVAL}s")
        logger.info("=" * 60)
        
        # Pierwsze pobranie od razu
        self.fetch_indices()
        self.fetch_fear_greed()
        
        while self.running:
            try:
                # Sprawdź czy pora na pobranie
                if self._should_fetch_indices():
                    self.fetch_indices()
                
                if self._should_fetch_fear_greed():
                    self.fetch_fear_greed()
                
                # Czekaj 60 sekund przed następnym sprawdzeniem
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Błąd w głównej pętli: {e}")
                time.sleep(60)
        
        logger.info("🛑 Market Indices Daemon - STOP")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Market Indices Daemon")
    parser.add_argument('--once', action='store_true', help='Wykonaj jeden cykl i zakończ')
    parser.add_argument('--historical-days', type=int, default=0,
                        help='Pobierz dane historyczne (liczba dni)')
    args = parser.parse_args()
    
    # Pobierz DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("Ustaw zmienną środowiskową DATABASE_URL")
        sys.exit(1)
    
    # Utwórz daemon
    daemon = MarketIndicesDaemon(database_url)
    daemon.ensure_tables()
    
    # Tryb działania
    if args.historical_days > 0:
        daemon.fetch_historical(days=args.historical_days)
    elif args.once:
        daemon.run_once()
    else:
        daemon.run()


if __name__ == "__main__":
    main()

