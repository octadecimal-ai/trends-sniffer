#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dYdX Top Traders Observer - Daemon
====================================
Skrypt działający w tle, który:
1. Aktualizuje ranking top traderów (co określony interwał)
2. Obserwuje aktywność top traderów (sprawdza nowe fill'e)
3. Publikuje eventy do reszty systemu
"""

import os
import sys
import time
import signal
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List
from loguru import logger

# Dodaj ścieżkę projektu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.services.dydx_top_traders_service import (
    DydxTopTradersService,
    FillEvent
)
from src.database.manager import DatabaseManager


class DydxTopTradersObserver:
    """
    Daemon do obserwacji top traderów na dYdX v4.
    
    Działa w pętli:
    - Co update_interval: aktualizuje ranking top traderów
    - Co watch_interval: sprawdza nowe fill'e dla top traderów
    - Publikuje eventy przez callback
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        testnet: bool = False,
        update_interval: int = 3600,  # 1 godzina
        watch_interval: int = 300,    # 5 minut
        top_n: int = 50,
        tickers: Optional[List[str]] = None,
        window_hours: int = 24,
        wallet_address: Optional[str] = None,
        private_key: Optional[str] = None,
        address: Optional[str] = None
    ):
        """
        Inicjalizacja observera.
        
        Args:
            database_url: URL bazy danych
            testnet: Czy używać testnet
            update_interval: Interwał aktualizacji rankingu (sekundy)
            watch_interval: Interwał sprawdzania fill'ów (sekundy)
            top_n: Liczba top traderów do obserwacji
            tickers: Lista rynków do analizy (domyślnie: BTC-USD, ETH-USD)
            window_hours: Okno czasowe dla rankingu (godziny)
            wallet_address: Adres portfela dYdX (opcjonalnie, domyślnie z .env)
            private_key: Klucz prywatny (opcjonalnie, domyślnie z .env)
            address: Adres Ethereum (opcjonalnie, domyślnie z .env)
        """
        self.update_interval = update_interval
        self.watch_interval = watch_interval
        self.top_n = top_n
        self.tickers = tickers or ['BTC-USD', 'ETH-USD']
        self.window_hours = window_hours
        
        # Inicjalizacja serwisu
        db_manager = DatabaseManager(database_url) if database_url else None
        self.service = DydxTopTradersService(
            testnet=testnet, 
            db_manager=db_manager,
            wallet_address=wallet_address,
            private_key=private_key,
            address=address
        )
        
        # Stan
        self.running = False
        self.last_update = None
        self.last_watch = None
        
        # Obsługa sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"dYdX Top Traders Observer zainicjalizowany")
        logger.info(f"  Update interval: {update_interval}s ({update_interval/60:.1f} min)")
        logger.info(f"  Watch interval: {watch_interval}s ({watch_interval/60:.1f} min)")
        logger.info(f"  Top N: {top_n}")
        logger.info(f"  Tickers: {', '.join(self.tickers)}")
        logger.info(f"  Window: {window_hours}h")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów do graceful shutdown."""
        logger.info(f"Otrzymano sygnał {signum}, zatrzymuję observer...")
        self.running = False
    
    def _on_fill_event(self, event: FillEvent):
        """
        Callback dla fill eventów.
        
        Tutaj można:
        - Publikować do message queue (RabbitMQ, Redis, etc.)
        - Wysyłać webhook
        - Zapisować do bazy danych
        - Wysyłać notyfikacje
        """
        logger.info(
            f"Fill event: {event.ticker} {event.side} @ {event.price} "
            f"(size: {event.size}, PnL: {event.realized_pnl}) "
            f"from {event.address}:{event.subaccount_number}"
        )
        
        # TODO: Implementacja publikacji eventu
        # Przykład:
        # - publish_to_queue(event)
        # - send_webhook(event)
        # - save_to_db(event)
    
    def update_ranking(self) -> bool:
        """
        Aktualizuje ranking top traderów.
        
        Returns:
            True jeśli sukces, False w przeciwnym razie
        """
        try:
            logger.info(f"Aktualizowanie rankingu top {self.top_n} traderów...")
            
            # Pobierz znane adresy z bazy danych (jeśli istnieją)
            known_addresses = self.service.repository.get_known_addresses(limit=100)
            
            top_traders = self.service.update_top_traders(
                tickers=self.tickers,
                top_n=self.top_n,
                lookback_hours=self.window_hours,
                window_hours=self.window_hours,
                min_fills=5,
                min_volume=1000.0,
                known_addresses=known_addresses
            )
            
            if top_traders is None:
                top_traders = []
            
            logger.success(
                f"Ranking zaktualizowany: {len(top_traders)} top traderów "
                f"(okno: {self.window_hours}h)"
            )
            
            # Log szczegółów
            if top_traders:
                logger.info(f"Top 5 traderów:")
                for trader in top_traders[:5]:
                    logger.info(
                        f"  #{trader.rank}: {trader.address}:{trader.subaccount_number} "
                        f"(score: {trader.score:.2f}, PnL: {trader.realized_pnl:.2f} USD)"
                    )
            
            self.last_update = datetime.now(timezone.utc)
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji rankingu: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def watch_traders(self) -> int:
        """
        Sprawdza nowe fill'e dla top traderów.
        
        Returns:
            Liczba znalezionych nowych fill eventów
        """
        try:
            logger.debug(f"Sprawdzanie aktywności top {self.top_n} traderów...")
            
            events = self.service.watch_top_traders(
                top_n=self.top_n,
                event_callback=self._on_fill_event
            )
            
            if events:
                logger.info(f"Znaleziono {len(events)} nowych fill eventów")
            else:
                logger.debug("Brak nowych fill eventów")
            
            self.last_watch = datetime.now(timezone.utc)
            return len(events)
            
        except Exception as e:
            logger.error(f"Błąd podczas obserwacji traderów: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return 0
    
    def run_once(self):
        """Wykonuje jedną iterację (update + watch)."""
        now = datetime.now(timezone.utc)
        
        # Sprawdź czy czas na update rankingu
        should_update = (
            self.last_update is None or
            (now - self.last_update).total_seconds() >= self.update_interval
        )
        
        if should_update:
            self.update_ranking()
        
        # Zawsze sprawdź nowe fill'e
        self.watch_traders()
    
    def run(self):
        """Główna pętla daemon."""
        logger.info("Uruchamianie dYdX Top Traders Observer...")
        self.running = True
        
        # Pierwszy update od razu
        self.update_ranking()
        self.watch_traders()
        
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                
                # Sprawdź czy czas na update rankingu
                should_update = (
                    self.last_update is None or
                    (now - self.last_update).total_seconds() >= self.update_interval
                )
                
                if should_update:
                    self.update_ranking()
                
                # Sprawdź czy czas na watch
                should_watch = (
                    self.last_watch is None or
                    (now - self.last_watch).total_seconds() >= self.watch_interval
                )
                
                if should_watch:
                    self.watch_traders()
                
                # Sleep na 1 minutę (sprawdzamy co minutę)
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Przerwano przez użytkownika")
                break
            except Exception as e:
                logger.error(f"Błąd w głównej pętli: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                time.sleep(60)  # Poczekaj przed ponowną próbą
        
        logger.info("dYdX Top Traders Observer zatrzymany")


def main():
    """Główna funkcja programu."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='dYdX Top Traders Observer - Daemon do obserwacji top traderów'
    )
    parser.add_argument(
        '--update-interval',
        type=int,
        default=3600,
        help='Interwał aktualizacji rankingu w sekundach (domyślnie: 3600 = 1h)'
    )
    parser.add_argument(
        '--watch-interval',
        type=int,
        default=300,
        help='Interwał sprawdzania fill\'ów w sekundach (domyślnie: 300 = 5min)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=50,
        help='Liczba top traderów do obserwacji (domyślnie: 50)'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        default=['BTC-USD', 'ETH-USD'],
        help='Lista rynków do analizy (domyślnie: BTC-USD ETH-USD)'
    )
    parser.add_argument(
        '--window-hours',
        type=int,
        default=24,
        help='Okno czasowe dla rankingu w godzinach (domyślnie: 24)'
    )
    parser.add_argument(
        '--testnet',
        action='store_true',
        help='Użyj testnet API'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Wykonaj jedną iterację i zakończ'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Szczegółowe logi'
    )
    
    args = parser.parse_args()
    
    # Konfiguracja logowania
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")
    
    # Załaduj .env
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    # Pobierz zmienne środowiskowe
    database_url = os.getenv('DATABASE_URL')
    wallet_address = os.getenv('DYDYX_API_WALLET_ADDRESS')
    private_key = os.getenv('DYDYX_PRIVATE_KEY')
    address = os.getenv('DYDYX_ADDRESS')
    
    # Inicjalizacja observera
    observer = DydxTopTradersObserver(
        database_url=database_url,
        testnet=args.testnet,
        update_interval=args.update_interval,
        watch_interval=args.watch_interval,
        top_n=args.top_n,
        tickers=args.tickers,
        window_hours=args.window_hours,
        wallet_address=wallet_address,
        private_key=private_key,
        address=address
    )
    
    # Uruchom
    if args.once:
        observer.run_once()
    else:
        observer.run()


if __name__ == "__main__":
    main()

