"""
Market Data Provider
====================
Provider dla danych z tradycyjnych rynków finansowych.

Źródła:
- Yahoo Finance (yfinance) - indeksy, akcje, commodities
- Alternative.me - Fear & Greed Index

Używane do analizy korelacji BTC z tradycyjnymi rynkami.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """
    Provider danych rynkowych z Yahoo Finance i innych źródeł.
    
    Dostępne indeksy:
    - SPX (^GSPC) - S&P 500
    - VIX (^VIX) - Volatility Index
    - DXY (DX-Y.NYB) - Dollar Index
    - NASDAQ (^IXIC) - NASDAQ Composite
    - GOLD (GC=F) - Gold Futures
    - TNX (^TNX) - 10-Year Treasury Yield
    """
    
    # Mapowanie przyjaznych nazw na symbole Yahoo Finance
    SYMBOLS = {
        'SPX': '^GSPC',      # S&P 500
        'VIX': '^VIX',       # Volatility Index
        'DXY': 'DX-Y.NYB',   # Dollar Index
        'NASDAQ': '^IXIC',   # NASDAQ Composite
        'GOLD': 'GC=F',      # Gold Futures
        'TNX': '^TNX',       # 10-Year Treasury Yield
        'OIL': 'CL=F',       # WTI Crude Oil
        'BTC': 'BTC-USD',    # Bitcoin (dla porównania)
    }
    
    def __init__(self):
        """Inicjalizacja providera."""
        self._yf_available = self._check_yfinance()
        
    def _check_yfinance(self) -> bool:
        """Sprawdź czy yfinance jest dostępny."""
        try:
            import yfinance as yf
            return True
        except ImportError:
            logger.warning("yfinance nie jest zainstalowany. Użyj: pip install yfinance")
            return False
    
    def get_index(self, name: str, period: str = "1d", interval: str = "1h") -> Optional[Dict[str, Any]]:
        """
        Pobierz dane dla pojedynczego indeksu.
        
        Args:
            name: Nazwa indeksu (SPX, VIX, DXY, NASDAQ, GOLD, TNX)
            period: Okres danych (1d, 5d, 1mo, etc.)
            interval: Interwał (1m, 5m, 1h, 1d)
            
        Returns:
            Dict z danymi lub None jeśli błąd
        """
        if not self._yf_available:
            return None
            
        import yfinance as yf
        
        symbol = self.SYMBOLS.get(name.upper())
        if not symbol:
            logger.error(f"Nieznany indeks: {name}. Dostępne: {list(self.SYMBOLS.keys())}")
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"Brak danych dla {name} ({symbol})")
                return None
            
            # Ostatni punkt danych
            latest = data.iloc[-1]
            
            # Oblicz zmiany jeśli mamy wystarczająco danych
            change_1h = None
            change_24h = None
            
            if len(data) > 1:
                change_1h = ((latest['Close'] - data.iloc[-2]['Close']) / data.iloc[-2]['Close']) * 100
            if len(data) > 24:
                change_24h = ((latest['Close'] - data.iloc[-24]['Close']) / data.iloc[-24]['Close']) * 100
            
            # Konwersja numpy -> Python (dla kompatybilności z PostgreSQL)
            def to_float(val):
                if val is None or (hasattr(val, '__len__') and len(val) == 0):
                    return None
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return None
            
            return {
                'symbol': symbol,
                'name': name.upper(),
                'timestamp': data.index[-1].to_pydatetime().replace(tzinfo=timezone.utc),
                'value': to_float(latest['Close']),
                'open': to_float(latest['Open']),
                'high': to_float(latest['High']),
                'low': to_float(latest['Low']),
                'close': to_float(latest['Close']),
                'volume': int(latest['Volume']) if latest['Volume'] > 0 else None,
                'change_1h': round(float(change_1h), 4) if change_1h is not None else None,
                'change_24h': round(float(change_24h), 4) if change_24h is not None else None,
                'source': 'yfinance',
            }
            
        except Exception as e:
            logger.error(f"Błąd pobierania {name}: {e}")
            return None
    
    def get_all_indices(self, period: str = "1d", interval: str = "1h") -> List[Dict[str, Any]]:
        """
        Pobierz dane dla wszystkich dostępnych indeksów.
        
        Args:
            period: Okres danych
            interval: Interwał
            
        Returns:
            Lista słowników z danymi
        """
        results = []
        
        # Główne indeksy do śledzenia
        priority_indices = ['SPX', 'VIX', 'DXY', 'NASDAQ', 'GOLD', 'TNX']
        
        for name in priority_indices:
            data = self.get_index(name, period=period, interval=interval)
            if data:
                results.append(data)
                logger.debug(f"✓ {name}: {data['value']:.2f}")
            else:
                logger.warning(f"✗ {name}: brak danych")
        
        return results
    
    def get_historical(self, name: str, start: datetime, end: datetime = None, 
                       interval: str = "1h") -> List[Dict[str, Any]]:
        """
        Pobierz dane historyczne dla indeksu.
        
        Args:
            name: Nazwa indeksu
            start: Data początkowa
            end: Data końcowa (domyślnie teraz)
            interval: Interwał
            
        Returns:
            Lista słowników z danymi historycznymi
        """
        if not self._yf_available:
            return []
            
        import yfinance as yf
        
        symbol = self.SYMBOLS.get(name.upper())
        if not symbol:
            return []
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start, end=end, interval=interval)
            
            # Konwersja numpy -> Python
            def to_float(val):
                if val is None:
                    return None
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return None
            
            results = []
            for idx, row in data.iterrows():
                results.append({
                    'symbol': symbol,
                    'name': name.upper(),
                    'timestamp': idx.to_pydatetime().replace(tzinfo=timezone.utc),
                    'value': to_float(row['Close']),
                    'open': to_float(row['Open']),
                    'high': to_float(row['High']),
                    'low': to_float(row['Low']),
                    'close': to_float(row['Close']),
                    'volume': int(row['Volume']) if row['Volume'] > 0 else None,
                    'source': 'yfinance',
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Błąd pobierania historii {name}: {e}")
            return []


class FearGreedProvider:
    """
    Provider dla Crypto Fear & Greed Index z alternative.me.
    
    API: https://api.alternative.me/fng/
    
    Zwraca wartość 0-100:
    - 0-24: Extreme Fear
    - 25-44: Fear  
    - 45-55: Neutral
    - 56-75: Greed
    - 76-100: Extreme Greed
    """
    
    API_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        """Inicjalizacja providera."""
        pass
    
    def get_current(self) -> Optional[Dict[str, Any]]:
        """
        Pobierz aktualną wartość Fear & Greed Index.
        
        Returns:
            Dict z danymi lub None jeśli błąd
        """
        try:
            response = requests.get(self.API_URL, params={"limit": 1}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or len(data['data']) == 0:
                logger.error("Brak danych w odpowiedzi API")
                return None
            
            entry = data['data'][0]
            
            # Konwertuj timestamp
            timestamp = datetime.fromtimestamp(int(entry['timestamp']), tz=timezone.utc)
            
            return {
                'timestamp': timestamp,
                'value': int(entry['value']),
                'classification': entry['value_classification'],
                'time_until_update': entry.get('time_until_update'),
                'source': 'alternative.me',
            }
            
        except requests.RequestException as e:
            logger.error(f"Błąd HTTP przy pobieraniu Fear & Greed: {e}")
            return None
        except Exception as e:
            logger.error(f"Błąd parsowania Fear & Greed: {e}")
            return None
    
    def get_historical(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Pobierz historyczne wartości Fear & Greed Index.
        
        Args:
            limit: Liczba dni wstecz (max ~365)
            
        Returns:
            Lista słowników z danymi historycznymi
        """
        try:
            response = requests.get(self.API_URL, params={"limit": limit}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data:
                return []
            
            results = []
            for entry in data['data']:
                timestamp = datetime.fromtimestamp(int(entry['timestamp']), tz=timezone.utc)
                results.append({
                    'timestamp': timestamp,
                    'value': int(entry['value']),
                    'classification': entry['value_classification'],
                    'source': 'alternative.me',
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Błąd pobierania historii Fear & Greed: {e}")
            return []
    
    def get_with_context(self) -> Optional[Dict[str, Any]]:
        """
        Pobierz Fear & Greed z kontekstem (wczoraj, tydzień temu).
        
        Returns:
            Dict z aktualną wartością i zmianami
        """
        history = self.get_historical(limit=8)
        
        if not history:
            return None
        
        current = history[0]
        
        # Znajdź wczorajszą wartość
        yesterday = history[1] if len(history) > 1 else None
        week_ago = history[7] if len(history) > 7 else None
        
        return {
            **current,
            'value_change_24h': current['value'] - yesterday['value'] if yesterday else None,
            'value_change_7d': current['value'] - week_ago['value'] if week_ago else None,
            'yesterday_value': yesterday['value'] if yesterday else None,
            'yesterday_classification': yesterday['classification'] if yesterday else None,
            'week_ago_value': week_ago['value'] if week_ago else None,
            'week_ago_classification': week_ago['classification'] if week_ago else None,
        }


# === Convenience functions ===

def get_market_snapshot() -> Dict[str, Any]:
    """
    Pobierz snapshot wszystkich danych rynkowych.
    
    Returns:
        Dict z indeksami i Fear & Greed
    """
    market_provider = MarketDataProvider()
    fg_provider = FearGreedProvider()
    
    indices = market_provider.get_all_indices()
    fear_greed = fg_provider.get_with_context()
    
    return {
        'timestamp': datetime.now(timezone.utc),
        'indices': {idx['name']: idx for idx in indices},
        'fear_greed': fear_greed,
    }


# === Test ===

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=" * 60)
    print("🏦 Market Data Provider Test")
    print("=" * 60)
    
    # Test Market Indices
    print("\n📊 Market Indices:")
    market = MarketDataProvider()
    indices = market.get_all_indices()
    for idx in indices:
        print(f"  {idx['name']}: {idx['value']:.2f} ({idx['change_1h']:+.2f}% 1h)" if idx['change_1h'] else f"  {idx['name']}: {idx['value']:.2f}")
    
    # Test Fear & Greed
    print("\n😱 Fear & Greed Index:")
    fg = FearGreedProvider()
    current = fg.get_with_context()
    if current:
        print(f"  Value: {current['value']} ({current['classification']})")
        if current['value_change_24h']:
            print(f"  Change 24h: {current['value_change_24h']:+d}")
        if current['value_change_7d']:
            print(f"  Change 7d: {current['value_change_7d']:+d}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed")

