#!/usr/bin/env python3
"""
Technical Indicators Daemon
===========================
Daemon do obliczania i zapisywania wskaźników technicznych z danych OHLCV.

Oblicza:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- SMA (20, 50, 200)
- EMA (9, 21)
- ATR (Average True Range)

Użycie:
    python daemons/technical_indicators_daemon.py [--once] [--symbol SYMBOL] [--timeframe TIMEFRAME]
"""

import os
import sys
import signal
import argparse
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Dodaj ścieżkę projektu do PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.database.manager import DatabaseManager
from src.database.models import TechnicalIndicator, Base
from src.providers.technical_indicators_provider import TechnicalIndicatorsProvider

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(PROJECT_ROOT, '.dev/logs/technical_indicators_daemon.log'))
    ]
)
logger = logging.getLogger(__name__)


class TechnicalIndicatorsDaemon:
    """
    Daemon do obliczania i zapisywania wskaźników technicznych.
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        cycle_interval: int = 300,  # 5 minut
        symbols: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None
    ):
        """
        Inicjalizacja daemona.
        
        Args:
            database_url: URL bazy danych (domyślnie z DATABASE_URL)
            cycle_interval: Interwał cyklu w sekundach (domyślnie 300)
            symbols: Lista symboli do przetworzenia (domyślnie ['BTC/USDC', 'BTC-USD'])
            timeframes: Lista interwałów czasowych (domyślnie ['1h', '4h', '1d'])
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL nie jest ustawiony")
        
        self.db_manager = DatabaseManager(self.database_url)
        self.provider = TechnicalIndicatorsProvider()
        self.cycle_interval = cycle_interval
        self.running = False
        
        # Domyślne symbole i timeframes
        # Sprawdzamy jakie symbole są dostępne w bazie
        self.symbols = symbols or self._get_available_symbols()
        # Sprawdzamy jakie timeframes są dostępne w bazie
        self.timeframes = timeframes or self._get_available_timeframes()
        
        # Obsługa sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("📊 Technical Indicators Daemon initialized")
        logger.info(f"   Symbols: {self.symbols}")
        logger.info(f"   Timeframes: {self.timeframes}")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów do zatrzymania daemona."""
        logger.info(f"Otrzymano sygnał {signum}, zatrzymywanie daemona...")
        self.running = False
    
    def _get_available_symbols(self) -> List[tuple]:
        """
        Pobiera dostępne symbole z bazy danych.
        
        Returns:
            Lista tupli (exchange, symbol)
        """
        query = text("""
            SELECT DISTINCT exchange, symbol
            FROM ohlcv
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            ORDER BY exchange, symbol
            LIMIT 20
        """)
        
        with self.db_manager.get_session() as session:
            result = session.execute(query)
            rows = result.fetchall()
        
        # Zwróć jako listę tupli (exchange, symbol)
        return [(row[0], row[1]) for row in rows] if rows else [('binance', 'BTC/USDT')]
    
    def _get_available_timeframes(self) -> List[str]:
        """
        Pobiera dostępne timeframes z bazy danych.
        
        Returns:
            Lista timeframes
        """
        query = text("""
            SELECT DISTINCT timeframe
            FROM ohlcv
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            ORDER BY timeframe
        """)
        
        with self.db_manager.get_session() as session:
            result = session.execute(query)
            rows = result.fetchall()
        
        # Zwróć listę timeframes
        timeframes = [row[0] for row in rows] if rows else ['1m']
        
        # Preferuj większe timeframes jeśli są dostępne
        preferred = ['1h', '4h', '1d', '1m']
        ordered = [tf for tf in preferred if tf in timeframes]
        return ordered if ordered else timeframes
    
    def ensure_tables(self):
        """Upewnij się, że tabele istnieją."""
        try:
            Base.metadata.create_all(
                self.db_manager.engine,
                tables=[TechnicalIndicator.__table__],
                checkfirst=True
            )
            logger.info("✓ Tabela technical_indicators gotowa")
        except Exception as e:
            logger.debug(f"Tabela technical_indicators: {e}")
            logger.info("✓ Tabela technical_indicators gotowa (istnieje)")
    
    def _fetch_ohlcv_data(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Pobiera dane OHLCV z bazy danych.
        
        Args:
            exchange: Nazwa giełdy
            symbol: Symbol pary
            timeframe: Interwał czasowy
            limit: Maksymalna liczba rekordów
        
        Returns:
            DataFrame z danymi OHLCV
        """
        query = text("""
            SELECT 
                timestamp,
                exchange,
                symbol,
                timeframe,
                open,
                high,
                low,
                close,
                volume
            FROM ohlcv
            WHERE exchange = :exchange
              AND symbol = :symbol
              AND timeframe = :timeframe
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        with self.db_manager.get_session() as session:
            result = session.execute(
                query,
                {
                    'exchange': exchange,
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'limit': limit
                }
            )
            rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=[
            'timestamp', 'exchange', 'symbol', 'timeframe',
            'open', 'high', 'low', 'close', 'volume'
        ])
        
        # Sortuj rosnąco po czasie (dla obliczeń)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def _convert_to_float(self, value):
        """Konwertuje wartość numpy na float."""
        if value is None:
            return None
        if hasattr(value, 'item'):
            return float(value.item())
        return float(value)
    
    def _save_indicators(self, indicators: List[Dict[str, Any]]) -> int:
        """
        Zapisuje wskaźniki techniczne do bazy danych.
        
        Args:
            indicators: Lista słowników z wartościami wskaźników
        
        Returns:
            Liczba zapisanych rekordów
        """
        if not indicators:
            return 0
        
        with self.db_manager.get_session() as session:
            for indicator_data in indicators:
                # Przygotuj dane do wstawienia (konwertuj numpy na float)
                insert_stmt = pg_insert(TechnicalIndicator).values(
                    timestamp=indicator_data['timestamp'],
                    exchange=indicator_data['exchange'],
                    symbol=indicator_data['symbol'],
                    timeframe=indicator_data['timeframe'],
                    sma_20=self._convert_to_float(indicator_data.get('sma_20')),
                    sma_50=self._convert_to_float(indicator_data.get('sma_50')),
                    sma_200=self._convert_to_float(indicator_data.get('sma_200')),
                    ema_9=self._convert_to_float(indicator_data.get('ema_9')),
                    ema_21=self._convert_to_float(indicator_data.get('ema_21')),
                    rsi=self._convert_to_float(indicator_data.get('rsi')),
                    macd=self._convert_to_float(indicator_data.get('macd')),
                    macd_signal=self._convert_to_float(indicator_data.get('macd_signal')),
                    macd_histogram=self._convert_to_float(indicator_data.get('macd_histogram')),
                    bb_upper=self._convert_to_float(indicator_data.get('bb_upper')),
                    bb_middle=self._convert_to_float(indicator_data.get('bb_middle')),
                    bb_lower=self._convert_to_float(indicator_data.get('bb_lower')),
                    atr=self._convert_to_float(indicator_data.get('atr')),
                )
                
                # UPSERT - aktualizuj jeśli istnieje
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    constraint='uq_indicators',
                    set_={
                        'sma_20': insert_stmt.excluded.sma_20,
                        'sma_50': insert_stmt.excluded.sma_50,
                        'sma_200': insert_stmt.excluded.sma_200,
                        'ema_9': insert_stmt.excluded.ema_9,
                        'ema_21': insert_stmt.excluded.ema_21,
                        'rsi': insert_stmt.excluded.rsi,
                        'macd': insert_stmt.excluded.macd,
                        'macd_signal': insert_stmt.excluded.macd_signal,
                        'macd_histogram': insert_stmt.excluded.macd_histogram,
                        'bb_upper': insert_stmt.excluded.bb_upper,
                        'bb_middle': insert_stmt.excluded.bb_middle,
                        'bb_lower': insert_stmt.excluded.bb_lower,
                        'atr': insert_stmt.excluded.atr,
                    }
                )
                
                session.execute(on_conflict_stmt)
            
            session.commit()
        
        return len(indicators)
    
    def _process_symbol_timeframe(
        self,
        exchange: str,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """
        Przetwarza jeden symbol i timeframe.
        
        Args:
            exchange: Nazwa giełdy
            symbol: Symbol pary
            timeframe: Interwał czasowy
        
        Returns:
            Słownik z wartościami wskaźników lub None jeśli brak danych
        """
        # Pobierz dane OHLCV
        df = self._fetch_ohlcv_data(exchange, symbol, timeframe, limit=500)
        
        if df.empty:
            logger.debug(f"Brak danych OHLCV dla {exchange}:{symbol}:{timeframe}")
            return None
        
        if len(df) < 200:
            logger.warning(
                f"Za mało danych dla {exchange}:{symbol}:{timeframe} "
                f"(mamy {len(df)}, potrzeba min. 200)"
            )
            return None
        
        # Oblicz wskaźniki
        try:
            df_with_indicators = self.provider.calculate_all_indicators(df)
            
            # Pobierz najnowsze wartości
            latest_indicators = self.provider.get_latest_indicators_for_symbol(
                df_with_indicators,
                exchange,
                symbol,
                timeframe
            )
            
            return latest_indicators
        
        except Exception as e:
            logger.error(f"Błąd obliczania wskaźników dla {exchange}:{symbol}:{timeframe}: {e}")
            return None
    
    def run_once(self):
        """Wykonuje jeden cykl obliczeń."""
        now = datetime.now(timezone.utc)
        logger.info(f"📊 Obliczam wskaźniki techniczne dla {now.strftime('%Y-%m-%d %H:%M:%S')}...")
        
        all_indicators = []
        
        # Dla każdego symbolu i timeframe
        for symbol_config in self.symbols:
            # symbol_config może być stringiem lub tuplą (exchange, symbol)
            if isinstance(symbol_config, tuple):
                exchange, symbol = symbol_config
            else:
                symbol = symbol_config
                # Określ exchange na podstawie symbolu
                if 'BTC-USD' in symbol:
                    exchange = 'dydx'
                elif 'BTC/USDC' in symbol or 'BTC/USDT' in symbol:
                    exchange = 'binance'
                else:
                    exchange = 'binance'  # domyślnie
            
            for timeframe in self.timeframes:
                indicators = self._process_symbol_timeframe(exchange, symbol, timeframe)
                if indicators:
                    all_indicators.append(indicators)
                    logger.debug(
                        f"✓ {exchange}:{symbol}:{timeframe} - "
                        f"RSI={indicators.get('rsi', 'N/A'):.2f}, "
                        f"MACD={indicators.get('macd', 'N/A'):.4f}"
                    )
        
        # Zapisz wszystkie wskaźniki
        if all_indicators:
            saved_count = self._save_indicators(all_indicators)
            logger.info(f"✅ Zapisano {saved_count} rekordów wskaźników technicznych")
        else:
            logger.warning("⚠ Nie zapisano żadnych wskaźników (brak danych lub błędy)")
    
    def run(self):
        """Główna pętla daemona."""
        self.ensure_tables()
        self.running = True
        
        logger.info("🚀 Technical Indicators Daemon uruchomiony")
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
            logger.info("Technical Indicators Daemon zatrzymany")


def main():
    """Główna funkcja."""
    parser = argparse.ArgumentParser(description='Technical Indicators Daemon')
    parser.add_argument('--once', action='store_true', help='Wykonaj jeden cykl i zakończ')
    parser.add_argument('--symbol', type=str, help='Symbol do przetworzenia (np. BTC/USDC)')
    parser.add_argument('--timeframe', type=str, help='Timeframe do przetworzenia (np. 1h)')
    parser.add_argument('--interval', type=int, default=300, help='Interwał cyklu w sekundach')
    
    args = parser.parse_args()
    
    # Konfiguracja symboli i timeframes
    symbols = [args.symbol] if args.symbol else None
    timeframes = [args.timeframe] if args.timeframe else None
    
    database_url = os.getenv('DATABASE_URL')
    daemon = TechnicalIndicatorsDaemon(
        database_url=database_url,
        cycle_interval=args.interval,
        symbols=symbols,
        timeframes=timeframes
    )
    
    if args.once:
        daemon.run_once()
    else:
        daemon.run()


if __name__ == '__main__':
    main()

