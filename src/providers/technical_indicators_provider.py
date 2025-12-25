"""
Technical Indicators Provider
=============================
Provider do obliczania wskaźników technicznych z danych OHLCV.

Obsługiwane wskaźniki:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- ATR (Average True Range)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicatorsProvider:
    """
    Provider do obliczania wskaźników technicznych.
    """
    
    def __init__(self):
        """Inicjalizacja providera."""
        logger.info("📊 Technical Indicators Provider initialized")
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Oblicza RSI (Relative Strength Index).
        
        Args:
            prices: Seria cen (zwykle close)
            period: Okres RSI (domyślnie 14)
        
        Returns:
            Seria z wartościami RSI (0-100)
        """
        if len(prices) < period + 1:
            return pd.Series(index=prices.index, dtype=float)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(
        self, 
        prices: pd.Series, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Oblicza MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Seria cen (zwykle close)
            fast_period: Okres szybkiej EMA (domyślnie 12)
            slow_period: Okres wolnej EMA (domyślnie 26)
            signal_period: Okres sygnału EMA (domyślnie 9)
        
        Returns:
            Słownik z kluczami: 'macd', 'signal', 'histogram'
        """
        if len(prices) < slow_period + signal_period:
            empty = pd.Series(index=prices.index, dtype=float)
            return {'macd': empty, 'signal': empty, 'histogram': empty}
        
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return {
            'macd': macd,
            'signal': signal,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(
        self, 
        prices: pd.Series, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Oblicza Bollinger Bands.
        
        Args:
            prices: Seria cen (zwykle close)
            period: Okres SMA (domyślnie 20)
            std_dev: Liczba odchyleń standardowych (domyślnie 2.0)
        
        Returns:
            Słownik z kluczami: 'upper', 'middle', 'lower'
        """
        if len(prices) < period:
            empty = pd.Series(index=prices.index, dtype=float)
            return {'upper': empty, 'middle': empty, 'lower': empty}
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower
        }
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Oblicza SMA (Simple Moving Average).
        
        Args:
            prices: Seria cen
            period: Okres średniej
        
        Returns:
            Seria z wartościami SMA
        """
        if len(prices) < period:
            return pd.Series(index=prices.index, dtype=float)
        
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Oblicza EMA (Exponential Moving Average).
        
        Args:
            prices: Seria cen
            period: Okres średniej
        
        Returns:
            Seria z wartościami EMA
        """
        if len(prices) < period:
            return pd.Series(index=prices.index, dtype=float)
        
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_atr(
        self, 
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 14
    ) -> pd.Series:
        """
        Oblicza ATR (Average True Range).
        
        Args:
            high: Seria najwyższych cen
            low: Seria najniższych cen
            close: Seria cen zamknięcia
            period: Okres ATR (domyślnie 14)
        
        Returns:
            Seria z wartościami ATR
        """
        if len(high) < period + 1:
            return pd.Series(index=high.index, dtype=float)
        
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def calculate_all_indicators(
        self, 
        df: pd.DataFrame,
        close_col: str = 'close',
        high_col: str = 'high',
        low_col: str = 'low'
    ) -> pd.DataFrame:
        """
        Oblicza wszystkie wskaźniki techniczne dla danego DataFrame.
        
        Args:
            df: DataFrame z danymi OHLCV (musi mieć kolumny: timestamp, close, high, low)
            close_col: Nazwa kolumny z ceną zamknięcia
            high_col: Nazwa kolumny z najwyższą ceną
            low_col: Nazwa kolumny z najniższą ceną
        
        Returns:
            DataFrame z dodanymi kolumnami wskaźników
        """
        if df.empty or len(df) < 200:
            logger.warning(f"Za mało danych do obliczenia wskaźników: {len(df)} rekordów")
            return df
        
        result_df = df.copy()
        prices = result_df[close_col]
        
        # RSI
        result_df['rsi'] = self.calculate_rsi(prices, period=14)
        
        # MACD
        macd_data = self.calculate_macd(prices)
        result_df['macd'] = macd_data['macd']
        result_df['macd_signal'] = macd_data['signal']
        result_df['macd_histogram'] = macd_data['histogram']
        
        # Bollinger Bands
        bb_data = self.calculate_bollinger_bands(prices, period=20, std_dev=2.0)
        result_df['bb_upper'] = bb_data['upper']
        result_df['bb_middle'] = bb_data['middle']
        result_df['bb_lower'] = bb_data['lower']
        
        # SMA
        result_df['sma_20'] = self.calculate_sma(prices, period=20)
        result_df['sma_50'] = self.calculate_sma(prices, period=50)
        result_df['sma_200'] = self.calculate_sma(prices, period=200)
        
        # EMA
        result_df['ema_9'] = self.calculate_ema(prices, period=9)
        result_df['ema_21'] = self.calculate_ema(prices, period=21)
        
        # ATR
        result_df['atr'] = self.calculate_atr(
            result_df[high_col],
            result_df[low_col],
            prices,
            period=14
        )
        
        return result_df
    
    def get_latest_indicators_for_symbol(
        self,
        df: pd.DataFrame,
        exchange: str,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """
        Pobiera najnowsze wskaźniki dla danego symbolu.
        
        Args:
            df: DataFrame z obliczonymi wskaźnikami
            exchange: Nazwa giełdy
            symbol: Symbol pary
            timeframe: Interwał czasowy
        
        Returns:
            Słownik z wartościami wskaźników dla ostatniego rekordu
        """
        if df.empty:
            return None
        
        latest = df.iloc[-1]
        
        return {
            'timestamp': latest.get('timestamp'),
            'exchange': exchange,
            'symbol': symbol,
            'timeframe': timeframe,
            'rsi': latest.get('rsi'),
            'macd': latest.get('macd'),
            'macd_signal': latest.get('macd_signal'),
            'macd_histogram': latest.get('macd_histogram'),
            'bb_upper': latest.get('bb_upper'),
            'bb_middle': latest.get('bb_middle'),
            'bb_lower': latest.get('bb_lower'),
            'sma_20': latest.get('sma_20'),
            'sma_50': latest.get('sma_50'),
            'sma_200': latest.get('sma_200'),
            'ema_9': latest.get('ema_9'),
            'ema_21': latest.get('ema_21'),
            'atr': latest.get('atr'),
        }

