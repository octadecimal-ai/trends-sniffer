"""
dYdX v4 Indexer API Provider
=============================
Niskopoziomowy klient do komunikacji z dYdX v4 Indexer HTTP API.
Obsługuje paginację, retry logic i normalizację timestampów do UTC.

API Documentation: https://docs.dydx.exchange/
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from loguru import logger
import time
import os
from dotenv import load_dotenv


class DydxIndexerProvider:
    """
    Provider do komunikacji z dYdX v4 Indexer API.
    
    Obsługuje:
    - Get Fills (subaccount i parent)
    - Get Historical PnL (subaccount i parent)
    - Paginację i retry logic
    - Normalizację timestampów do UTC
    """
    
    BASE_URL = "https://indexer.dydx.trade/v4"
    BASE_URL_TESTNET = "https://indexer.v4testnet.dydx.exchange/v4"
    
    def __init__(
        self, 
        testnet: bool = False, 
        max_retries: int = 3, 
        retry_delay: float = 1.0,
        wallet_address: Optional[str] = None,
        private_key: Optional[str] = None,
        address: Optional[str] = None
    ):
        """
        Inicjalizacja providera.
        
        Args:
            testnet: Czy używać testnet API
            max_retries: Maksymalna liczba prób przy błędzie
            retry_delay: Opóźnienie między próbami (sekundy)
            wallet_address: Adres portfela dYdX (z .env: DYDYX_API_WALLET_ADDRESS)
            private_key: Klucz prywatny (z .env: DYDYX_PRIVATE_KEY)
            address: Adres Ethereum (z .env: DYDYX_ADDRESS)
        """
        # Załaduj zmienne środowiskowe jeśli nie podano
        load_dotenv()
        
        self.wallet_address = wallet_address or os.getenv('DYDYX_API_WALLET_ADDRESS')
        self.private_key = private_key or os.getenv('DYDYX_PRIVATE_KEY')
        self.address = address or os.getenv('DYDYX_ADDRESS')
        
        self.base_url = self.BASE_URL_TESTNET if testnet else self.BASE_URL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Jeśli mamy dane dostępowe, możemy dodać autentykację
        # (obecnie Indexer API jest publiczne, ale mogą być potrzebne do innych operacji)
        if self.wallet_address or self.private_key or self.address:
            logger.debug("Dane dostępowe dYdX wykryte (dostępne do użycia w przyszłości)")
        
        mode = "TESTNET" if testnet else "MAINNET"
        logger.debug(f"dYdX Indexer Provider uruchomiony ({mode})")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Wykonuje request do API z retry logic.
        
        Args:
            endpoint: Endpoint API (zaczyna się od /)
            params: Parametry zapytania
            page: Numer strony (dodaje do params jeśli podany)
            
        Returns:
            Odpowiedź JSON jako dict
            
        Raises:
            requests.RequestException: W przypadku błędu po wszystkich próbach
        """
        if params is None:
            params = {}
        
        if page is not None:
            params['page'] = page
        
        url = f"{self.base_url}{endpoint}"
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=60)  # Zwiększony timeout dla VPN
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit osiągnięty, czekam {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                last_exception = e
            except requests.exceptions.RequestException as e:
                last_exception = e
            
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)
                if last_exception:
                    logger.warning(f"Błąd API (próba {attempt + 1}/{self.max_retries}): {last_exception}. Ponawiam za {wait_time:.1f}s...")
                else:
                    logger.warning(f"Błąd API (próba {attempt + 1}/{self.max_retries}). Ponawiam za {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        logger.error(f"Błąd API po {self.max_retries} próbach: {last_exception}")
        raise last_exception
    
    def _normalize_timestamp(self, ts: str) -> datetime:
        """Normalizuje timestamp z API do UTC datetime."""
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
        
        # API zwraca ISO 8601 string
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc)
    
    def get_subaccount_fills(
        self,
        address: str,
        subaccount_number: int,
        ticker: Optional[str] = None,
        limit: int = 100,
        created_before_or_at: Optional[datetime] = None,
        created_on_or_after: Optional[datetime] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pobiera fill'e (transakcje) dla subkonta.
        
        Args:
            address: Adres dYdX Chain (dydx1...) - wallet address on dYdX Chain
            subaccount_number: Numer subkonta (0-127)
            ticker: Symbol rynku (opcjonalnie, np. "BTC-USD")
            limit: Maksymalna liczba wyników (max 100)
            created_before_or_at: Filtruj fill'e przed tą datą (UTC)
            created_on_or_after: Filtruj fill'e od tej daty (UTC)
            page: Numer strony (dla paginacji)
            
        Returns:
            Dict z kluczami: fills (lista), pagination (info o paginacji)
        """
        # Endpoint /fills używa parametrów query, nie ścieżki URL!
        endpoint = "/fills"
        
        params = {
            'address': address,
            'subaccountNumber': subaccount_number,
            'limit': min(limit, 100)
        }
        
        if ticker:
            params['ticker'] = ticker
        if created_before_or_at:
            params['createdBeforeOrAt'] = created_before_or_at.isoformat().replace('+00:00', 'Z')
        if created_on_or_after:
            params['createdOnOrAfter'] = created_on_or_after.isoformat().replace('+00:00', 'Z')
        
        data = self._make_request(endpoint, params, page)
        
        # Normalizuj timestampy w fill'ach
        if 'fills' in data:
            for fill in data['fills']:
                if 'createdAt' in fill:
                    fill['createdAt'] = self._normalize_timestamp(fill['createdAt'])
                if 'effectiveAt' in fill:
                    fill['effectiveAt'] = self._normalize_timestamp(fill['effectiveAt'])
        
        return data
    
    def get_subaccount_historical_pnls(
        self,
        address: str,
        subaccount_number: int,
        created_on_or_after: Optional[datetime] = None,
        created_before_or_at: Optional[datetime] = None,
        limit: int = 100,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pobiera historyczne PnL dla subkonta.
        
        Args:
            address: Adres Ethereum subkonta
            subaccount_number: Numer subkonta (0-127)
            created_on_or_after: Filtruj PnL od tej daty (UTC)
            created_before_or_at: Filtruj PnL przed tą datą (UTC)
            limit: Maksymalna liczba wyników (max 100)
            page: Numer strony (dla paginacji)
            
        Returns:
            Dict z kluczami: historicalPnl (lista), pagination (info o paginacji)
        """
        # Endpoint /historical-pnl używa parametrów query, nie ścieżki URL!
        endpoint = "/historical-pnl"
        
        params = {
            'address': address,
            'subaccountNumber': subaccount_number,
            'limit': min(limit, 100)
        }
        
        if created_on_or_after:
            params['createdOnOrAfter'] = created_on_or_after.isoformat().replace('+00:00', 'Z')
        if created_before_or_at:
            params['createdBeforeOrAt'] = created_before_or_at.isoformat().replace('+00:00', 'Z')
        
        data = self._make_request(endpoint, params, page)
        
        # Normalizuj timestampy
        if 'historicalPnl' in data:
            for pnl in data['historicalPnl']:
                if 'createdAt' in pnl:
                    pnl['createdAt'] = self._normalize_timestamp(pnl['createdAt'])
                if 'effectiveAt' in pnl:
                    pnl['effectiveAt'] = self._normalize_timestamp(pnl['effectiveAt'])
        
        return data
    
    def get_parent_subaccount_fills(
        self,
        address: str,
        parent_subaccount_number: int,
        ticker: Optional[str] = None,
        limit: int = 100,
        created_before_or_at: Optional[datetime] = None,
        created_on_or_after: Optional[datetime] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pobiera fill'e dla parent subkonta (agregacja dla rodzica i jego child subaccounts).
        
        Args:
            address: Adres Ethereum
            parent_subaccount_number: Numer parent subkonta
            ticker: Symbol rynku (opcjonalnie)
            limit: Maksymalna liczba wyników
            created_before_or_at: Filtruj przed datą
            created_on_or_after: Filtruj od daty
            page: Numer strony
            
        Returns:
            Dict z fill'ami i paginacją
        """
        endpoint = f"/addresses/{address}/parentSubaccountNumber/{parent_subaccount_number}/fills"
        
        params = {
            'limit': min(limit, 100)
        }
        
        if ticker:
            params['ticker'] = ticker
        if created_before_or_at:
            params['createdBeforeOrAt'] = created_before_or_at.isoformat().replace('+00:00', 'Z')
        if created_on_or_after:
            params['createdOnOrAfter'] = created_on_or_after.isoformat().replace('+00:00', 'Z')
        
        data = self._make_request(endpoint, params, page)
        
        # Normalizuj timestampy
        if 'fills' in data:
            for fill in data['fills']:
                if 'createdAt' in fill:
                    fill['createdAt'] = self._normalize_timestamp(fill['createdAt'])
                if 'effectiveAt' in fill:
                    fill['effectiveAt'] = self._normalize_timestamp(fill['effectiveAt'])
        
        return data
    
    def get_parent_subaccount_historical_pnls(
        self,
        address: str,
        parent_subaccount_number: int,
        created_on_or_after: Optional[datetime] = None,
        created_before_or_at: Optional[datetime] = None,
        limit: int = 100,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Pobiera historyczne PnL dla parent subkonta.
        
        Args:
            address: Adres Ethereum
            parent_subaccount_number: Numer parent subkonta
            created_on_or_after: Filtruj od daty
            created_before_or_at: Filtruj przed datą
            limit: Maksymalna liczba wyników
            page: Numer strony
            
        Returns:
            Dict z historicalPnl i paginacją
        """
        endpoint = f"/addresses/{address}/parentSubaccountNumber/{parent_subaccount_number}/historical-pnl"
        
        params = {
            'limit': min(limit, 100)
        }
        
        if created_on_or_after:
            params['createdOnOrAfter'] = created_on_or_after.isoformat().replace('+00:00', 'Z')
        if created_before_or_at:
            params['createdBeforeOrAt'] = created_before_or_at.isoformat().replace('+00:00', 'Z')
        
        data = self._make_request(endpoint, params, page)
        
        # Normalizuj timestampy
        if 'historicalPnl' in data:
            for pnl in data['historicalPnl']:
                if 'createdAt' in pnl:
                    pnl['createdAt'] = self._normalize_timestamp(pnl['createdAt'])
                if 'effectiveAt' in pnl:
                    pnl['effectiveAt'] = self._normalize_timestamp(pnl['effectiveAt'])
        
        return data
    
    def get_all_fills_paginated(
        self,
        address: str,
        subaccount_number: int,
        ticker: Optional[str] = None,
        created_on_or_after: Optional[datetime] = None,
        created_before_or_at: Optional[datetime] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Pobiera wszystkie fill'e z paginacją.
        
        Args:
            address: Adres subkonta
            subaccount_number: Numer subkonta
            ticker: Symbol rynku (opcjonalnie)
            created_on_or_after: Filtruj od daty
            created_before_or_at: Filtruj przed datą
            max_results: Maksymalna liczba wyników (None = wszystkie)
            
        Returns:
            Lista wszystkich fill'ów
        """
        all_fills = []
        page = 1
        
        while True:
            data = self.get_subaccount_fills(
                address=address,
                subaccount_number=subaccount_number,
                ticker=ticker,
                limit=100,
                created_on_or_after=created_on_or_after,
                created_before_or_at=created_before_or_at,
                page=page
            )
            
            fills = data.get('fills', [])
            if not fills:
                break
            
            all_fills.extend(fills)
            
            # Sprawdź paginację
            pagination = data.get('pagination', {})
            if not pagination.get('hasMore', False):
                break
            
            if max_results and len(all_fills) >= max_results:
                all_fills = all_fills[:max_results]
                break
            
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        return all_fills
    
    def get_all_historical_pnls_paginated(
        self,
        address: str,
        subaccount_number: int,
        created_on_or_after: Optional[datetime] = None,
        created_before_or_at: Optional[datetime] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Pobiera wszystkie historyczne PnL z paginacją.
        
        Args:
            address: Adres subkonta
            subaccount_number: Numer subkonta
            created_on_or_after: Filtruj od daty
            created_before_or_at: Filtruj przed datą
            max_results: Maksymalna liczba wyników (None = wszystkie)
            
        Returns:
            Lista wszystkich PnL
        """
        all_pnls = []
        page = 1
        
        while True:
            data = self.get_subaccount_historical_pnls(
                address=address,
                subaccount_number=subaccount_number,
                created_on_or_after=created_on_or_after,
                created_before_or_at=created_before_or_at,
                limit=100,
                page=page
            )
            
            pnls = data.get('historicalPnl', [])
            if not pnls:
                break
            
            all_pnls.extend(pnls)
            
            # Sprawdź paginację
            pagination = data.get('pagination', {})
            if not pagination.get('hasMore', False):
                break
            
            if max_results and len(all_pnls) >= max_results:
                all_pnls = all_pnls[:max_results]
                break
            
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        return all_pnls
    
    def get_trades_for_market(
        self,
        ticker: str,
        limit: int = 100,
        created_before_or_at: Optional[datetime] = None,
        created_on_or_after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Pobiera ostatnie transakcje dla rynku.
        
        UWAGA: Ten endpoint zwraca tylko podstawowe informacje o transakcjach,
        bez adresów traderów. Może być użyty do analizy aktywności rynku.
        
        Args:
            ticker: Symbol rynku (np. "BTC-USD")
            limit: Maksymalna liczba wyników (max 100)
            created_before_or_at: Filtruj przed datą
            created_on_or_after: Filtruj od daty
            
        Returns:
            Lista transakcji
        """
        endpoint = f"/trades/perpetualMarket/{ticker}"
        
        params = {
            'limit': min(limit, 100)
        }
        
        if created_before_or_at:
            params['createdBeforeOrAt'] = created_before_or_at.isoformat().replace('+00:00', 'Z')
        if created_on_or_after:
            params['createdOnOrAfter'] = created_on_or_after.isoformat().replace('+00:00', 'Z')
        
        data = self._make_request(endpoint, params)
        
        trades = data.get('trades', [])
        
        # Normalizuj timestampy
        for trade in trades:
            if 'createdAt' in trade:
                trade['createdAt'] = self._normalize_timestamp(trade['createdAt'])
        
        return trades

