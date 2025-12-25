"""
Order Flow Imbalance Analyzer
==============================
Analyzer do obliczania metryk Order Flow Imbalance z danych dYdX.

Order Flow Imbalance (OFI) to jedna z najbardziej predykcyjnych zmiennych
w handlu wysokofrequencyjnym. Bazuje na obserwacji, że nierównowaga między
wolumenem BUY i SELL jest wyprzedzającym wskaźnikiem ruchu ceny.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text, Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
import logging

logger = logging.getLogger(__name__)


class OrderFlowImbalanceAnalyzer:
    """
    Analyzer do obliczania metryk Order Flow Imbalance.
    """
    
    def __init__(self, database_url: str):
        """
        Inicjalizacja analyzer'a.
        
        Args:
            database_url: URL do bazy PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Progi dla dużych transakcji
        self.large_trade_threshold = 0.5  # BTC
        self.whale_threshold = 5.0  # BTC
        
        logger.info("📊 Order Flow Imbalance Analyzer initialized")
    
    def _fetch_trades(
        self,
        ticker: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """
        Pobiera transakcje z bazy danych.
        
        Args:
            ticker: Symbol rynku (np. BTC-USD)
            start_time: Początek okna czasowego
            end_time: Koniec okna czasowego
        
        Returns:
            DataFrame z transakcjami
        """
        query = text("""
            SELECT 
                effective_at,
                side,
                size,
                price,
                trade_type
            FROM dydx_perpetual_market_trades
            WHERE ticker = :ticker
              AND effective_at >= :start_time
              AND effective_at < :end_time
            ORDER BY effective_at
        """)
        
        with self.Session() as session:
            result = session.execute(
                query,
                {
                    'ticker': ticker,
                    'start_time': start_time,
                    'end_time': end_time
                }
            )
            rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['effective_at', 'side', 'size', 'price', 'trade_type'])
        df['effective_at'] = pd.to_datetime(df['effective_at'])
        df['size'] = pd.to_numeric(df['size'], errors='coerce')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        return df
    
    def _fetch_ohlcv_price(
        self,
        symbol: str,
        timestamp: datetime
    ) -> Optional[float]:
        """
        Pobiera cenę zamknięcia z OHLCV dla danego timestamp.
        
        Args:
            symbol: Symbol pary (np. BTC/USDC)
            timestamp: Timestamp
        
        Returns:
            Cena zamknięcia lub None
        """
        query = text("""
            SELECT close
            FROM ohlcv
            WHERE symbol = :symbol
              AND timeframe = '1m'
              AND timestamp <= :timestamp
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        with self.Session() as session:
            result = session.execute(
                query,
                {
                    'symbol': symbol,
                    'timestamp': timestamp
                }
            )
            row = result.fetchone()
        
        return float(row[0]) if row else None
    
    def _get_previous_imbalance(
        self,
        ticker: str,
        current_timestamp: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Pobiera metryki imbalance z poprzedniej godziny.
        
        Args:
            ticker: Symbol rynku
            current_timestamp: Aktualny timestamp
        
        Returns:
            Słownik z metrykami poprzedniej godziny lub None
        """
        prev_timestamp = current_timestamp - timedelta(hours=1)
        
        query = text("""
            SELECT 
                order_flow_imbalance,
                total_volume,
                vwap
            FROM dydx_order_flow_imbalance
            WHERE ticker = :ticker
              AND timestamp = :timestamp
        """)
        
        with self.Session() as session:
            result = session.execute(
                query,
                {
                    'ticker': ticker,
                    'timestamp': prev_timestamp
                }
            )
            row = result.fetchone()
        
        if row:
            return {
                'order_flow_imbalance': float(row[0]),
                'total_volume': float(row[1]),
                'vwap': float(row[2]) if row[2] else None
            }
        
        return None
    
    def calculate_imbalance_metrics(
        self,
        ticker: str,
        timestamp: datetime,
        window_minutes: int = 60
    ) -> Optional[Dict[str, Any]]:
        """
        Oblicza metryki Order Flow Imbalance dla danego okna czasowego.
        
        Args:
            ticker: Symbol rynku (np. BTC-USD)
            timestamp: Początek okna czasowego
            window_minutes: Długość okna w minutach (domyślnie 60)
        
        Returns:
            Słownik z metrykami imbalance lub None jeśli brak danych
        """
        start_time = timestamp
        end_time = timestamp + timedelta(minutes=window_minutes)
        
        # Pobierz transakcje
        df = self._fetch_trades(ticker, start_time, end_time)
        
        if df.empty:
            logger.debug(f"Brak transakcji dla {ticker} w oknie {start_time} - {end_time}")
            return None
        
        if len(df) < 10:
            logger.debug(f"Za mało transakcji dla {ticker} w oknie {start_time} - {end_time} ({len(df)})")
            return None
        
        # Oblicz podstawowe metryki
        buy_trades = df[df['side'] == 'BUY']
        sell_trades = df[df['side'] == 'SELL']
        
        buy_volume = float(buy_trades['size'].sum())
        sell_volume = float(sell_trades['size'].sum())
        total_volume = buy_volume + sell_volume
        
        buy_count = len(buy_trades)
        sell_count = len(sell_trades)
        total_trades = len(df)
        
        # Order Flow Imbalance
        order_flow_imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0.0
        buy_sell_ratio = buy_count / sell_count if sell_count > 0 else None
        
        # Duże transakcje
        large_trades = df[df['size'] >= self.large_trade_threshold]
        large_trade_volume = float(large_trades['size'].sum())
        large_trade_count = len(large_trades)
        large_trade_ratio = large_trade_volume / total_volume if total_volume > 0 else 0.0
        
        # Whale transakcje
        whale_trades = df[df['size'] >= self.whale_threshold]
        whale_volume = float(whale_trades['size'].sum())
        whale_count = len(whale_trades)
        whale_ratio = whale_volume / total_volume if total_volume > 0 else 0.0
        
        # Ceny
        vwap = float((df['size'] * df['price']).sum() / df['size'].sum()) if df['size'].sum() > 0 else None
        avg_price = float(df['price'].mean())
        min_price = float(df['price'].min())
        max_price = float(df['price'].max())
        price_range = max_price - min_price
        price_range_pct = (price_range / avg_price * 100) if avg_price > 0 else 0.0
        
        # Intensywność
        window_duration_minutes = (end_time - start_time).total_seconds() / 60
        trades_per_minute = total_trades / window_duration_minutes if window_duration_minutes > 0 else 0.0
        volume_per_minute = total_volume / window_duration_minutes if window_duration_minutes > 0 else 0.0
        
        # Momentum (zmiany vs poprzednia godzina)
        prev_metrics = self._get_previous_imbalance(ticker, timestamp)
        imbalance_change_1h = None
        volume_change_1h = None
        price_change_1h = None
        
        if prev_metrics:
            imbalance_change_1h = order_flow_imbalance - prev_metrics['order_flow_imbalance']
            if prev_metrics['total_volume'] > 0:
                volume_change_1h = ((total_volume - prev_metrics['total_volume']) / prev_metrics['total_volume']) * 100
            if prev_metrics['vwap'] and vwap:
                price_change_1h = ((vwap - prev_metrics['vwap']) / prev_metrics['vwap']) * 100
        
        # Korelacja z OHLCV
        # Mapuj ticker dYdX na symbol Binance
        ohlcv_symbol = ticker.replace('-USD', '/USDC') if '-USD' in ticker else ticker
        ohlcv_close_price = self._fetch_ohlcv_price(ohlcv_symbol, end_time)
        vwap_deviation_pct = None
        
        if ohlcv_close_price and vwap:
            vwap_deviation_pct = ((vwap - ohlcv_close_price) / ohlcv_close_price) * 100
        
        return {
            'timestamp': timestamp,
            'ticker': ticker,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'total_volume': total_volume,
            'order_flow_imbalance': order_flow_imbalance,
            'buy_sell_ratio': buy_sell_ratio,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_trades': total_trades,
            'large_trade_threshold': self.large_trade_threshold,
            'large_trade_volume': large_trade_volume,
            'large_trade_count': large_trade_count,
            'large_trade_ratio': large_trade_ratio,
            'whale_threshold': self.whale_threshold,
            'whale_volume': whale_volume,
            'whale_count': whale_count,
            'whale_ratio': whale_ratio,
            'vwap': vwap,
            'avg_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_range': price_range,
            'price_range_pct': price_range_pct,
            'trades_per_minute': trades_per_minute,
            'volume_per_minute': volume_per_minute,
            'imbalance_change_1h': imbalance_change_1h,
            'volume_change_1h': volume_change_1h,
            'price_change_1h': price_change_1h,
            'ohlcv_close_price': ohlcv_close_price,
            'vwap_deviation_pct': vwap_deviation_pct,
            'calculation_window_minutes': window_minutes,
        }
    
    def save_imbalance_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Zapisuje metryki imbalance do bazy danych.
        
        Args:
            metrics: Słownik z metrykami
        
        Returns:
            True jeśli zapisano pomyślnie
        """
        if not metrics:
            return False
        
        # Użyj Table reflection dla pg_insert
        metadata = MetaData()
        table = Table('dydx_order_flow_imbalance', metadata, autoload_with=self.engine)
        
        with self.Session() as session:
            try:
                insert_stmt = pg_insert(table).values(
                    timestamp=metrics['timestamp'],
                    ticker=metrics['ticker'],
                    buy_volume=metrics['buy_volume'],
                    sell_volume=metrics['sell_volume'],
                    total_volume=metrics['total_volume'],
                    order_flow_imbalance=metrics['order_flow_imbalance'],
                    buy_sell_ratio=metrics.get('buy_sell_ratio'),
                    buy_count=metrics['buy_count'],
                    sell_count=metrics['sell_count'],
                    total_trades=metrics['total_trades'],
                    large_trade_threshold=metrics['large_trade_threshold'],
                    large_trade_volume=metrics['large_trade_volume'],
                    large_trade_count=metrics['large_trade_count'],
                    large_trade_ratio=metrics['large_trade_ratio'],
                    whale_threshold=metrics['whale_threshold'],
                    whale_volume=metrics['whale_volume'],
                    whale_count=metrics['whale_count'],
                    whale_ratio=metrics['whale_ratio'],
                    vwap=metrics.get('vwap'),
                    avg_price=metrics['avg_price'],
                    min_price=metrics['min_price'],
                    max_price=metrics['max_price'],
                    price_range=metrics['price_range'],
                    price_range_pct=metrics['price_range_pct'],
                    trades_per_minute=metrics['trades_per_minute'],
                    volume_per_minute=metrics['volume_per_minute'],
                    imbalance_change_1h=metrics.get('imbalance_change_1h'),
                    volume_change_1h=metrics.get('volume_change_1h'),
                    price_change_1h=metrics.get('price_change_1h'),
                    ohlcv_close_price=metrics.get('ohlcv_close_price'),
                    vwap_deviation_pct=metrics.get('vwap_deviation_pct'),
                    calculation_window_minutes=metrics['calculation_window_minutes'],
                )
                
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['timestamp', 'ticker'],
                    set_={
                        'buy_volume': insert_stmt.excluded.buy_volume,
                        'sell_volume': insert_stmt.excluded.sell_volume,
                        'total_volume': insert_stmt.excluded.total_volume,
                        'order_flow_imbalance': insert_stmt.excluded.order_flow_imbalance,
                        'buy_sell_ratio': insert_stmt.excluded.buy_sell_ratio,
                        'buy_count': insert_stmt.excluded.buy_count,
                        'sell_count': insert_stmt.excluded.sell_count,
                        'total_trades': insert_stmt.excluded.total_trades,
                        'large_trade_volume': insert_stmt.excluded.large_trade_volume,
                        'large_trade_count': insert_stmt.excluded.large_trade_count,
                        'large_trade_ratio': insert_stmt.excluded.large_trade_ratio,
                        'whale_volume': insert_stmt.excluded.whale_volume,
                        'whale_count': insert_stmt.excluded.whale_count,
                        'whale_ratio': insert_stmt.excluded.whale_ratio,
                        'vwap': insert_stmt.excluded.vwap,
                        'avg_price': insert_stmt.excluded.avg_price,
                        'min_price': insert_stmt.excluded.min_price,
                        'max_price': insert_stmt.excluded.max_price,
                        'price_range': insert_stmt.excluded.price_range,
                        'price_range_pct': insert_stmt.excluded.price_range_pct,
                        'trades_per_minute': insert_stmt.excluded.trades_per_minute,
                        'volume_per_minute': insert_stmt.excluded.volume_per_minute,
                        'imbalance_change_1h': insert_stmt.excluded.imbalance_change_1h,
                        'volume_change_1h': insert_stmt.excluded.volume_change_1h,
                        'price_change_1h': insert_stmt.excluded.price_change_1h,
                        'ohlcv_close_price': insert_stmt.excluded.ohlcv_close_price,
                        'vwap_deviation_pct': insert_stmt.excluded.vwap_deviation_pct,
                    }
                )
                
                session.execute(on_conflict_stmt)
                session.commit()
                return True
            
            except Exception as e:
                session.rollback()
                logger.error(f"Błąd zapisu metryk imbalance: {e}")
                return False
    
    def calculate_and_save(
        self,
        ticker: str,
        timestamp: Optional[datetime] = None,
        window_minutes: int = 60
    ) -> bool:
        """
        Oblicza i zapisuje metryki imbalance dla danego tickera i timestamp.
        
        Args:
            ticker: Symbol rynku
            timestamp: Timestamp początku okna (domyślnie ostatnia pełna godzina)
            window_minutes: Długość okna w minutach
        
        Returns:
            True jeśli zapisano pomyślnie
        """
        if timestamp is None:
            # Domyślnie ostatnia pełna godzina
            now = datetime.now(timezone.utc)
            timestamp = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        
        metrics = self.calculate_imbalance_metrics(ticker, timestamp, window_minutes)
        
        if not metrics:
            return False
        
        return self.save_imbalance_metrics(metrics)

