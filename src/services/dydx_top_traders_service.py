"""
dYdX Top Traders Observer Service
==================================
Serwis wysokopoziomowy do obserwacji i rankingu najlepszych traderów na dYdX v4.

Architektura modułu:
- CandidateDiscoveryService: Zbiera kandydatów z fill'ów
- PnlScoringService: Pobiera PnL i oblicza scoring
- TopTradersRepository: Persistencja listy top traderów
- TraderActivityWatcher: Śledzi aktywność top traderów i emituje eventy
"""

from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

from src.providers.dydx_indexer_provider import DydxIndexerProvider


@dataclass
class TraderCandidate:
    """Kandydat do rankingu top traderów."""
    address: str
    subaccount_number: int
    fill_count: int = 0
    total_volume: float = 0.0
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


@dataclass
class TraderScore:
    """Wynik tradera w rankingu."""
    address: str
    subaccount_number: int
    realized_pnl: float = 0.0
    net_pnl: float = 0.0
    fill_count: int = 0
    turnover: float = 0.0
    score: float = 0.0  # Znormalizowany wynik rankingowy
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    window_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TopTrader:
    """Top trader zapisany w repozytorium."""
    address: str
    subaccount_number: int
    rank: int
    score: float
    realized_pnl: float
    net_pnl: float
    fill_count: int
    turnover: float
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    effective_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    window_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FillEvent:
    """Event nowego fill'a od top tradera."""
    fill_id: str
    address: str
    subaccount_number: int
    ticker: str
    side: str  # BUY, SELL
    price: float
    size: float
    fee: float
    realized_pnl: Optional[float]
    effective_at: datetime
    created_at: datetime
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CandidateDiscoveryService:
    """
    Zbiera kandydatów do rankingu z ostatnich fill'ów.
    
    Algorytm:
    1. Pobiera ostatnie fill'e dla rynku/rynków
    2. Wyciąga unikalne pary (address, subaccount_number)
    3. Agreguje metryki: liczba fill'ów, wolumen, zakres czasowy
    4. Filtruje według minimalnych progów (min fill'ów, min wolumen)
    
    UWAGA: dYdX Indexer API nie ma endpointu "wszystkie fill'e dla rynku".
    Używamy własnego adresu z .env jako punktu startowego lub budujemy bazę stopniowo.
    """
    
    def __init__(self, provider: DydxIndexerProvider):
        self.provider = provider
        # Załaduj adresy z .env (zarówno Ethereum jak i dYdX)
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.known_addresses = []
        
        # Adres z DYDYX_ADDRESS (powinien być dYdX Chain address)
        own_addr = provider.address
        if own_addr:
            if own_addr.startswith('dydx1'):
                self.known_addresses.append((own_addr, 0))  # Domyślnie subaccount 0
                logger.debug(f"Dodano adres dYdX Chain z DYDYX_ADDRESS: {own_addr}")
            elif own_addr.startswith('0x'):
                logger.warning(
                    f"DYDYX_ADDRESS to adres Ethereum ({own_addr}), ale endpoint /fills wymaga adresu dYdX Chain (dydx1...). "
                    f"Pomijam. Użyj adresu dYdX Chain zamiast Ethereum."
                )
        
        # Adresy od Piotra (powinny być dYdX Chain addresses)
        addr1 = os.getenv('WALLET_ADDRESS_FROM_PIOTREK_1')
        addr2 = os.getenv('WALLET_ADDRESS_FROM_PIOTREK_2')
        
        for addr, name in [(addr1, 'WALLET_ADDRESS_FROM_PIOTREK_1'), 
                          (addr2, 'WALLET_ADDRESS_FROM_PIOTREK_2')]:
            if addr:
                if addr.startswith('dydx1'):
                    self.known_addresses.append((addr, 0))
                    logger.debug(f"Dodano adres dYdX Chain z {name}: {addr}")
                elif addr.startswith('0x'):
                    logger.warning(
                        f"{name} to adres Ethereum ({addr}), ale endpoint /fills wymaga adresu dYdX Chain (dydx1...). "
                        f"Pomijam. Użyj adresu dYdX Chain zamiast Ethereum."
                    )
        
        if self.known_addresses:
            logger.info(f"Załadowano {len(self.known_addresses)} adresów jako punkty startowe")
    
    def discover_from_fills(
        self,
        tickers: List[str],
        lookback_hours: int = 24,
        min_fills: int = 5,
        min_volume: float = 1000.0,
        known_addresses: Optional[List[Tuple[str, int]]] = None
    ) -> List[TraderCandidate]:
        """
        Odkrywa kandydatów z ostatnich fill'ów.
        
        Args:
            tickers: Lista symboli rynków do analizy
            lookback_hours: Okno czasowe wstecz (godziny)
            min_fills: Minimalna liczba fill'ów aby być kandydatem
            min_volume: Minimalny wolumen (USD) aby być kandydatem
            known_addresses: Lista znanych adresów do sprawdzenia (opcjonalnie)
            
        Returns:
            Lista kandydatów spełniających progi
        """
        logger.info(f"Odkrywanie kandydatów z {len(tickers)} rynków (okno: {lookback_hours}h)")
        
        candidates: Dict[Tuple[str, int], TraderCandidate] = {}
        # Użyj cutoff_time tylko jeśli lookback_hours > 0, w przeciwnym razie pobierz wszystkie fill'e
        cutoff_time = None if lookback_hours <= 0 else datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        
        # Lista adresów do sprawdzenia
        addresses_to_check = known_addresses or []
        
        # Dodaj znane adresy z inicjalizacji (adresy od Piotra, etc.)
        if self.known_addresses:
            addresses_to_check.extend(self.known_addresses)
        
        if not addresses_to_check:
            logger.warning(
                "Brak adresów do sprawdzenia. "
                "Podaj known_addresses lub ustaw DYDYX_ADDRESS w .env"
            )
            return []
        
        # Dla każdego adresu pobierz fill'e
        for address, subaccount_number in addresses_to_check:
            # dYdX Indexer API endpoint /fills wymaga adresu dYdX Chain (dydx1...), nie Ethereum (0x...)
            if address.startswith('0x'):
                logger.warning(
                    f"Adres Ethereum ({address}) nie jest obsługiwany przez endpoint /fills. "
                    f"Endpoint wymaga adresu dYdX Chain (dydx1...). Pomijam."
                )
                continue
            
            # Spróbuj najpierw bez filtra tickera (wszystkie rynki)
            try:
                logger.debug(
                    f"Pobieranie fill'ów dla {address}:{subaccount_number} "
                    f"(wszystkie rynki, bez filtra daty: {cutoff_time is None})..."
                )
                
                fills = self.provider.get_all_fills_paginated(
                    address=address,
                    subaccount_number=subaccount_number,
                    ticker=None,  # Bez filtra tickera - sprawdź wszystkie rynki
                    created_on_or_after=cutoff_time,  # None = wszystkie historyczne
                    max_results=1000  # Limit dla wydajności
                )
                
                if fills:
                    logger.info(f"Znaleziono {len(fills)} fill'ów dla {address}:{subaccount_number} (wszystkie rynki)")
                else:
                    logger.debug(f"Brak fill'ów dla {address}:{subaccount_number} (wszystkie rynki)")
                    
            except Exception as exc:
                logger.warning(
                    f"Błąd podczas pobierania fill'ów dla {address}:{subaccount_number}: {exc}"
                )
                import traceback
                logger.debug(traceback.format_exc())
                continue
            
            # Jeśli nie znaleziono fill'ów bez filtra tickera, spróbuj dla każdego tickera osobno
            if not fills:
                for ticker in tickers:
                    try:
                        logger.debug(
                            f"Pobieranie fill'ów dla {address}:{subaccount_number} "
                            f"na rynku {ticker}..."
                        )
                        
                        ticker_fills = self.provider.get_all_fills_paginated(
                            address=address,
                            subaccount_number=subaccount_number,
                            ticker=ticker,
                            created_on_or_after=cutoff_time,
                            max_results=1000
                        )
                        
                        if ticker_fills:
                            logger.info(f"Znaleziono {len(ticker_fills)} fill'ów dla {address}:{subaccount_number} na {ticker}")
                            fills.extend(ticker_fills)  # Dodaj do listy fill'ów
                            
                    except Exception as exc:
                        logger.debug(f"Błąd dla {ticker}: {exc}")
                        continue
            
            # Agreguj metryki (jeśli znaleziono jakiekolwiek fill'e)
            if fills:
                key = (address, subaccount_number)
                if key not in candidates:
                    candidates[key] = TraderCandidate(
                        address=address,
                        subaccount_number=subaccount_number,
                        first_seen_at=cutoff_time,
                        last_seen_at=cutoff_time
                    )
                
                candidate = candidates[key]
                
                for fill in fills:
                    candidate.fill_count += 1
                    price = float(fill.get('price', 0))
                    size = float(fill.get('size', 0))
                    candidate.total_volume += price * size
                    
                    # Aktualizuj zakres czasowy
                    fill_time = fill.get('effectiveAt') or fill.get('createdAt')
                    if fill_time:
                        if isinstance(fill_time, str):
                            fill_time = datetime.fromisoformat(
                                fill_time.replace('Z', '+00:00')
                            )
                        if fill_time.tzinfo is None:
                            fill_time = fill_time.replace(tzinfo=timezone.utc)
                        
                        if candidate.first_seen_at is None or fill_time < candidate.first_seen_at:
                            candidate.first_seen_at = fill_time
                        if candidate.last_seen_at is None or fill_time > candidate.last_seen_at:
                            candidate.last_seen_at = fill_time
                
                logger.debug(
                    f"Agregowano {len(fills)} fill'ów dla {address}:{subaccount_number}"
                )
        
        # Filtruj według progów
        filtered = [
            c for c in candidates.values()
            if c.fill_count >= min_fills and c.total_volume >= min_volume
        ]
        
        logger.info(f"Znaleziono {len(filtered)} kandydatów spełniających progi")
        return filtered


class PnlScoringService:
    """
    Pobiera PnL dla kandydatów i oblicza scoring.
    
    Algorytm rankingu:
    - Okno czasu: rolling 24h/7d
    - Metryki: realized PnL, net PnL, liczba transakcji, turnover
    - Filtr anty-szum: min liczba fill'ów, min wolumen
    - Score = weighted sum metryk
    """
    
    def __init__(self, provider: DydxIndexerProvider):
        self.provider = provider
    
    def score_candidates(
        self,
        candidates: List[TraderCandidate],
        window_hours: int = 24,
        weights: Optional[Dict[str, float]] = None
    ) -> List[TraderScore]:
        """
        Oblicza scoring dla kandydatów.
        
        Args:
            candidates: Lista kandydatów
            window_hours: Okno czasowe dla PnL (godziny)
            weights: Wagi dla metryk (realized_pnl, net_pnl, fill_count, turnover)
            
        Returns:
            Lista wyników posortowana malejąco po score
        """
        if weights is None:
            weights = {
                'realized_pnl': 0.4,
                'net_pnl': 0.3,
                'fill_count': 0.1,
                'turnover': 0.2
            }
        
        logger.info(f"Obliczanie scoringu dla {len(candidates)} kandydatów (okno: {window_hours}h)")
        
        window_end = datetime.now(timezone.utc)
        window_start = window_end - timedelta(hours=window_hours)
        
        scores = []
        
        for candidate in candidates:
            try:
                # Pobierz historical PnL
                pnls = self.provider.get_all_historical_pnls_paginated(
                    address=candidate.address,
                    subaccount_number=candidate.subaccount_number,
                    created_on_or_after=window_start,
                    created_before_or_at=window_end
                )
                
                # Pobierz fill'e dla obliczenia turnover
                fills = self.provider.get_all_fills_paginated(
                    address=candidate.address,
                    subaccount_number=candidate.subaccount_number,
                    created_on_or_after=window_start,
                    created_before_or_at=window_end
                )
                
                # Agreguj metryki
                realized_pnl = sum(float(pnl.get('realizedPnl', 0)) for pnl in pnls)
                net_pnl = sum(float(pnl.get('netPnl', 0)) for pnl in pnls)
                fill_count = len(fills)
                turnover = sum(
                    float(fill.get('size', 0)) * float(fill.get('price', 0))
                    for fill in fills
                )
                
                # Oblicz znormalizowany score
                # Normalizacja: dziel przez max wartości (lub użyj percentyli)
                score = (
                    weights['realized_pnl'] * realized_pnl +
                    weights['net_pnl'] * net_pnl +
                    weights['fill_count'] * fill_count +
                    weights['turnover'] * (turnover / 1000000.0)  # Normalizuj do milionów
                )
                
                scores.append(TraderScore(
                    address=candidate.address,
                    subaccount_number=candidate.subaccount_number,
                    realized_pnl=realized_pnl,
                    net_pnl=net_pnl,
                    fill_count=fill_count,
                    turnover=turnover,
                    score=score,
                    window_start=window_start,
                    window_end=window_end
                ))
                
            except Exception as e:
                logger.warning(f"Błąd podczas scoringu dla {candidate.address}:{candidate.subaccount_number}: {e}")
                continue
        
        # Sortuj malejąco po score
        scores.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Obliczono scoring dla {len(scores)} traderów")
        return scores


class TopTradersRepository:
    """
    Repozytorium do przechowywania listy top traderów.
    
    Persistencja:
    - Lista top N traderów
    - Metryki (PnL, fill count, turnover)
    - Timestampy (observed_at, effective_at, window_start, window_end)
    - Idempotencja: deduplikacja po (address, subaccount_number, window_end)
    """
    
    def __init__(self, db_manager=None):
        """
        Inicjalizacja repozytorium.
        
        Args:
            db_manager: DatabaseManager (opcjonalnie, jeśli chcemy persistować do DB)
        """
        self.db_manager = db_manager
        # W pamięci cache (w produkcji: DB)
        self._top_traders: List[TopTrader] = []
        self._last_update: Optional[datetime] = None
    
    def save_top_traders(
        self,
        scores: List[TraderScore],
        top_n: int = 50
    ) -> List[TopTrader]:
        """
        Zapisuje top N traderów.
        
        Args:
            scores: Lista wyników posortowana
            top_n: Liczba top traderów do zapisania
            
        Returns:
            Lista zapisanych top traderów
        """
        observed_at = datetime.now(timezone.utc)
        
        top_traders = []
        for rank, score in enumerate(scores[:top_n], start=1):
            trader = TopTrader(
                address=score.address,
                subaccount_number=score.subaccount_number,
                rank=rank,
                score=score.score,
                realized_pnl=score.realized_pnl,
                net_pnl=score.net_pnl,
                fill_count=score.fill_count,
                turnover=score.turnover,
                observed_at=observed_at,
                effective_at=score.window_end,
                window_start=score.window_start,
                window_end=score.window_end
            )
            top_traders.append(trader)
        
        # Deduplikacja: usuń stare wpisy dla tych samych (address, subaccount_number)
        # i tego samego okna czasowego
        self._top_traders = [
            t for t in self._top_traders
            if not any(
                t.address == new.address and
                t.subaccount_number == new.subaccount_number and
                t.window_end == new.window_end
                for new in top_traders
            )
        ]
        
        self._top_traders.extend(top_traders)
        self._last_update = observed_at
        
        logger.info(f"Zapisano {len(top_traders)} top traderów (rank 1-{top_n})")
        
        # TODO: Jeśli db_manager, zapisz do bazy danych
        if self.db_manager:
            pass  # TODO: Implementacja zapisu do DB
    
    def get_top_traders(self, top_n: Optional[int] = None) -> List[TopTrader]:
        """
        Pobiera listę top traderów.
        
        Args:
            top_n: Liczba traderów do zwrócenia (None = wszyscy)
            
        Returns:
            Lista top traderów posortowana po rank
        """
        traders = sorted(self._top_traders, key=lambda x: x.rank if x.rank else 999999)
        if top_n:
            traders = traders[:top_n]
        return traders
    
    def get_known_addresses(self, limit: int = 100) -> List[Tuple[str, int]]:
        """
        Pobiera listę znanych adresów z bazy danych lub cache.
        
        Args:
            limit: Maksymalna liczba adresów do zwrócenia
            
        Returns:
            Lista tupli (address, subaccount_number)
        """
        addresses = []
        
        # Z cache (top traderzy)
        for trader in self._top_traders[:limit]:
            addresses.append((trader.address, trader.subaccount_number))
        
        # Z bazy danych (jeśli dostępna)
        if self.db_manager:
            try:
                from sqlalchemy import text
                with self.db_manager.get_session() as session:
                    # Pobierz adresy z tabeli dydx_traders
                    result = session.execute(text("""
                        SELECT address, subaccount_number
                        FROM dydx_traders
                        WHERE is_active = TRUE
                        ORDER BY last_seen_at DESC
                        LIMIT :limit
                    """), {'limit': limit})
                    
                    for row in result:
                        addresses.append((row.address, row.subaccount_number))
            except Exception as e:
                logger.debug(f"Błąd podczas pobierania adresów z DB: {e}")
        
        # Usuń duplikaty zachowując kolejność
        seen = set()
        unique_addresses = []
        for addr in addresses:
            if addr not in seen:
                seen.add(addr)
                unique_addresses.append(addr)
        
        return unique_addresses[:limit]
    
    def _persist_to_db(self, traders: List[TopTrader]):
        """Zapisuje do bazy danych (TODO: implementacja)."""
        # TODO: Implementacja zapisu do DB
        pass


class TraderActivityWatcher:
    """
    Śledzi aktywność top traderów i emituje eventy.
    
    Dla każdego top tradera:
    1. Pobiera nowe fill'e (od ostatniego sprawdzenia)
    2. Deduplikuje (po fill_id)
    3. Emituje FillEvent do reszty systemu
    """
    
    def __init__(self, provider: DydxIndexerProvider, repository: TopTradersRepository):
        self.provider = provider
        self.repository = repository
        self._last_check: Dict[Tuple[str, int], datetime] = {}
        self._seen_fill_ids: Set[str] = set()
    
    def watch_top_traders(
        self,
        top_n: int = 50,
        event_callback: Optional[callable] = None
    ) -> List[FillEvent]:
        """
        Sprawdza nowe fill'e dla top traderów.
        
        Args:
            top_n: Liczba top traderów do obserwacji
            event_callback: Funkcja callback do emisji eventów (opcjonalnie)
            
        Returns:
            Lista nowych fill eventów
        """
        top_traders = self.repository.get_top_traders(top_n)
        logger.info(f"Sprawdzanie aktywności dla {len(top_traders)} top traderów")
        
        new_events = []
        now = datetime.now(timezone.utc)
        
        for trader in top_traders:
            key = (trader.address, trader.subaccount_number)
            last_check = self._last_check.get(key, trader.observed_at)
            
            try:
                # Pobierz fill'e od ostatniego sprawdzenia
                fills = self.provider.get_all_fills_paginated(
                    address=trader.address,
                    subaccount_number=trader.subaccount_number,
                    created_on_or_after=last_check
                )
                
                for fill in fills:
                    fill_id = fill.get('id') or f"{fill.get('createdAt')}-{fill.get('ticker')}"
                    
                    # Deduplikacja
                    if fill_id in self._seen_fill_ids:
                        continue
                    
                    self._seen_fill_ids.add(fill_id)
                    
                    event = FillEvent(
                        fill_id=fill_id,
                        address=trader.address,
                        subaccount_number=trader.subaccount_number,
                        ticker=fill.get('ticker', ''),
                        side=fill.get('side', ''),
                        price=float(fill.get('price', 0)),
                        size=float(fill.get('size', 0)),
                        fee=float(fill.get('fee', 0)),
                        realized_pnl=fill.get('realizedPnl'),
                        effective_at=fill.get('effectiveAt', fill.get('createdAt')),
                        created_at=fill.get('createdAt')
                    )
                    
                    new_events.append(event)
                    
                    # Emituj event
                    if event_callback:
                        event_callback(event)
                
                self._last_check[key] = now
                
            except Exception as e:
                logger.warning(f"Błąd podczas obserwacji {trader.address}:{trader.subaccount_number}: {e}")
                continue
        
        logger.info(f"Znaleziono {len(new_events)} nowych fill eventów")
        return new_events


class DydxTopTradersService:
    """
    Główny serwis łączący wszystkie komponenty.
    
    Użycie:
    ```python
    service = DydxTopTradersService()
    service.update_top_traders(tickers=['BTC-USD'], top_n=50)
    events = service.watch_top_traders(top_n=50)
    ```
    """
    
    def __init__(
        self, 
        testnet: bool = False, 
        db_manager=None,
        wallet_address: Optional[str] = None,
        private_key: Optional[str] = None,
        address: Optional[str] = None
    ):
        """
        Inicjalizacja serwisu.
        
        Args:
            testnet: Czy używać testnet API
            db_manager: Manager bazy danych
            wallet_address: Adres portfela dYdX (opcjonalnie, domyślnie z .env)
            private_key: Klucz prywatny (opcjonalnie, domyślnie z .env)
            address: Adres Ethereum (opcjonalnie, domyślnie z .env)
        """
        self.provider = DydxIndexerProvider(
            testnet=testnet,
            wallet_address=wallet_address,
            private_key=private_key,
            address=address
        )
        self.discovery = CandidateDiscoveryService(self.provider)
        self.scoring = PnlScoringService(self.provider)
        self.repository = TopTradersRepository(db_manager)
        self.watcher = TraderActivityWatcher(self.provider, self.repository)
    
    def update_top_traders(
        self,
        tickers: List[str],
        top_n: int = 50,
        lookback_hours: int = 24,
        window_hours: int = 24,
        min_fills: int = 5,
        min_volume: float = 1000.0,
        known_addresses: Optional[List[Tuple[str, int]]] = None
    ) -> List[TopTrader]:
        """
        Aktualizuje ranking top traderów.
        
        Args:
            tickers: Lista rynków do analizy
            top_n: Liczba top traderów do zapisania
            lookback_hours: Okno dla odkrywania kandydatów
            window_hours: Okno dla scoringu PnL
            min_fills: Minimalna liczba fill'ów
            min_volume: Minimalny wolumen
            known_addresses: Lista znanych adresów do sprawdzenia (opcjonalnie)
            
        Returns:
            Lista top traderów
        """
        # 1. Odkryj kandydatów
        candidates = self.discovery.discover_from_fills(
            tickers=tickers,
            lookback_hours=lookback_hours,
            min_fills=min_fills,
            min_volume=min_volume,
            known_addresses=known_addresses
        )
        
        # 2. Oblicz scoring
        scores = self.scoring.score_candidates(
            candidates=candidates,
            window_hours=window_hours
        )
        
        # 3. Zapisz top N
        top_traders = self.repository.save_top_traders(scores, top_n)
        
        return top_traders
    
    def watch_top_traders(
        self,
        top_n: int = 50,
        event_callback: Optional[callable] = None
    ) -> List[FillEvent]:
        """
        Sprawdza nowe fill'e dla top traderów.
        
        Args:
            top_n: Liczba top traderów do obserwacji
            event_callback: Callback dla eventów
            
        Returns:
            Lista nowych fill eventów
        """
        return self.watcher.watch_top_traders(top_n, event_callback)

