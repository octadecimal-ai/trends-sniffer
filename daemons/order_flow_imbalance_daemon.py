#!/usr/bin/env python3
"""
Order Flow Imbalance Daemon
===========================
Daemon do obliczania i zapisywania metryk Order Flow Imbalance z dYdX.

Order Flow Imbalance (OFI) to jedna z najbardziej predykcyjnych zmiennych
w handlu wysokofrequencyjnym. Bazuje na obserwacji, że nierównowaga między
wolumenem BUY i SELL jest wyprzedzającym wskaźnikiem ruchu ceny.

Użycie:
    python daemons/order_flow_imbalance_daemon.py [--once] [--ticker TICKER] [--backfill]
"""

import os
import sys
import signal
import argparse
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pathlib import Path

# Dodaj ścieżkę projektu do PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.database.manager import DatabaseManager
from src.database.models import OrderFlowImbalance, Base
from src.analyzers.order_flow_imbalance_analyzer import OrderFlowImbalanceAnalyzer
from sqlalchemy import text

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(PROJECT_ROOT, '.dev/logs/order_flow_imbalance_daemon.log'))
    ]
)
logger = logging.getLogger(__name__)


class OrderFlowImbalanceDaemon:
    """
    Daemon do obliczania i zapisywania metryk Order Flow Imbalance.
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        cycle_interval: int = 3600,  # 1 godzina
        tickers: Optional[List[str]] = None,
        backfill: bool = False
    ):
        """
        Inicjalizacja daemona.
        
        Args:
            database_url: URL bazy danych (domyślnie z DATABASE_URL)
            cycle_interval: Interwał cyklu w sekundach (domyślnie 3600)
            tickers: Lista tickerów do przetworzenia (domyślnie ['BTC-USD'])
            backfill: Czy wykonać backfill dla ostatnich godzin
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL nie jest ustawiony")
        
        self.db_manager = DatabaseManager(self.database_url)
        self.analyzer = OrderFlowImbalanceAnalyzer(self.database_url)
        self.cycle_interval = cycle_interval
        self.tickers = tickers or ['BTC-USD']
        self.backfill = backfill
        self.running = False
        
        # Obsługa sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("📊 Order Flow Imbalance Daemon initialized")
        logger.info(f"   Tickers: {self.tickers}")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów do zatrzymania daemona."""
        logger.info(f"Otrzymano sygnał {signum}, zatrzymywanie daemona...")
        self.running = False
    
    def ensure_tables(self):
        """Upewnij się, że tabele istnieją."""
        try:
            if not self.db_manager.check_if_table_exists(OrderFlowImbalance.__tablename__):
                Base.metadata.create_all(
                    self.db_manager.engine,
                    tables=[OrderFlowImbalance.__table__]
                )
                logger.info(f"✓ Tabela {OrderFlowImbalance.__tablename__} utworzona")
            else:
                logger.info(f"✓ Tabela {OrderFlowImbalance.__tablename__} gotowa (istnieje)")
        except Exception as e:
            logger.debug(f"Tabela {OrderFlowImbalance.__tablename__}: {e}")
            logger.info(f"✓ Tabela {OrderFlowImbalance.__tablename__} gotowa (istnieje)")
    
    def _get_available_tickers(self) -> List[str]:
        """
        Pobiera dostępne tickery z bazy danych.
        
        Returns:
            Lista tickerów
        """
        query = """
            SELECT DISTINCT ticker
            FROM dydx_perpetual_market_trades
            WHERE effective_at >= NOW() - INTERVAL '7 days'
            ORDER BY ticker
            LIMIT 20
        """
        
        with self.db_manager.get_session() as session:
            result = session.execute(query)
            rows = result.fetchall()
        
        return [row[0] for row in rows] if rows else ['BTC-USD']
    
    def run_once(self, timestamp: Optional[datetime] = None):
        """
        Wykonuje jeden cykl obliczeń.
        
        Args:
            timestamp: Timestamp do obliczenia (domyślnie ostatnia pełna godzina)
        """
        if timestamp is None:
            # Domyślnie ostatnia pełna godzina
            now = datetime.now(timezone.utc)
            timestamp = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        
        logger.info(f"📊 Obliczam metryki imbalance dla {timestamp.strftime('%Y-%m-%d %H:%M:%S')}...")
        
        # Użyj dostępnych tickerów jeśli nie podano
        tickers_to_process = self.tickers if self.tickers else self._get_available_tickers()
        
        saved_count = 0
        for ticker in tickers_to_process:
            if self.analyzer.calculate_and_save(ticker, timestamp):
                saved_count += 1
                logger.debug(f"✓ Zapisano metryki dla {ticker}")
            else:
                logger.warning(f"⚠ Nie udało się zapisać metryk dla {ticker}")
        
        if saved_count > 0:
            logger.info(f"✅ Zapisano metryki imbalance dla {saved_count}/{len(tickers_to_process)} tickerów")
        else:
            logger.warning("⚠ Nie zapisano żadnych metryk imbalance")
    
    def run_backfill(self, hours: int = 24):
        """
        Wykonuje backfill dla ostatnich N godzin.
        
        Args:
            hours: Liczba godzin do przetworzenia
        """
        now = datetime.now(timezone.utc)
        start_timestamp = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours)
        
        logger.info(f"📊 Backfill: obliczam metryki dla ostatnich {hours} godzin...")
        
        current = start_timestamp
        while current < now.replace(minute=0, second=0, microsecond=0):
            self.run_once(current)
            current += timedelta(hours=1)
        
        logger.info("✅ Backfill zakończony")
    
    def run(self):
        """Główna pętla daemona."""
        self.ensure_tables()
        
        if self.backfill:
            self.run_backfill(hours=24)
        
        self.running = True
        
        logger.info("🚀 Order Flow Imbalance Daemon uruchomiony")
        logger.info(f"   Cykl co {self.cycle_interval} sekund")
        
        try:
            while self.running:
                self.run_once()
                
                if self.running:
                    import time
                    time.sleep(self.cycle_interval)
        
        except KeyboardInterrupt:
            logger.info("Zatrzymywanie daemona (KeyboardInterrupt)...")
        except Exception as e:
            logger.error(f"Błąd w głównej pętli daemona: {e}", exc_info=True)
        finally:
            logger.info("Order Flow Imbalance Daemon zatrzymany")


def main():
    """Główna funkcja."""
    parser = argparse.ArgumentParser(description='Order Flow Imbalance Daemon')
    parser.add_argument('--once', action='store_true', help='Wykonaj jeden cykl i zakończ')
    parser.add_argument('--ticker', type=str, help='Ticker do przetworzenia (np. BTC-USD)')
    parser.add_argument('--backfill', action='store_true', help='Wykonaj backfill dla ostatnich 24h')
    parser.add_argument('--interval', type=int, default=3600, help='Interwał cyklu w sekundach')
    
    args = parser.parse_args()
    
    tickers = [args.ticker] if args.ticker else None
    
    database_url = os.getenv('DATABASE_URL')
    daemon = OrderFlowImbalanceDaemon(
        database_url=database_url,
        cycle_interval=args.interval,
        tickers=tickers,
        backfill=args.backfill
    )
    
    if args.once:
        daemon.run_once()
    else:
        daemon.run()


if __name__ == '__main__':
    main()

