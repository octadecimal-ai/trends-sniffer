# dYdX Top Traders Observer - Dokumentacja

## Architektura modułu

Moduł składa się z 4 głównych komponentów:

1. **DydxIndexerProvider** (`src/providers/dydx_indexer_provider.py`)
   - Niskopoziomowy klient API
   - Obsługa paginacji, retry, normalizacja timestampów
   - Metody: `get_subaccount_fills()`, `get_subaccount_historical_pnls()`, etc.

2. **CandidateDiscoveryService**
   - Zbiera kandydatów z ostatnich fill'ów
   - Agreguje metryki (fill count, volume)
   - Filtruje według progów (min fills, min volume)

3. **PnlScoringService**
   - Pobiera historical PnL dla kandydatów
   - Oblicza scoring na podstawie metryk
   - Ranking: realized PnL, net PnL, fill count, turnover

4. **TopTradersRepository**
   - Persistencja listy top traderów
   - Idempotencja (deduplikacja)
   - Cache w pamięci (opcjonalnie: DB)

5. **TraderActivityWatcher**
   - Śledzi nowe fill'e dla top traderów
   - Deduplikacja fill'ów (po fill_id)
   - Emituje FillEvent do reszty systemu

## Przykłady użycia

### Podstawowe użycie

```python
from src.services.dydx_top_traders_service import DydxTopTradersService

# Inicjalizacja
service = DydxTopTradersService(testnet=False)

# Aktualizuj ranking top 50 traderów
top_traders = service.update_top_traders(
    tickers=['BTC-USD', 'ETH-USD'],
    top_n=50,
    lookback_hours=24,
    window_hours=24,
    min_fills=5,
    min_volume=1000.0
)

# Obserwuj aktywność top traderów
def on_fill_event(event):
    print(f"Nowy fill: {event.ticker} {event.side} @ {event.price}")

events = service.watch_top_traders(
    top_n=50,
    event_callback=on_fill_event
)
```

### Przykładowe requesty HTTP (curl)

```bash
# Get Fills dla subkonta
curl "https://indexer.dydx.trade/v4/addresses/0x123.../subaccountNumber/0/fills?limit=100&ticker=BTC-USD"

# Get Historical PnL
curl "https://indexer.dydx.trade/v4/addresses/0x123.../subaccountNumber/0/historical-pnl?limit=100&createdOnOrAfter=2024-01-01T00:00:00Z"

# Get Parent Fills (agregacja)
curl "https://indexer.dydx.trade/v4/addresses/0x123.../parentSubaccountNumber/0/fills?limit=100"
```

## Struktury danych (DTO)

### Fill (z API)
```python
{
    "id": "0x...",
    "side": "BUY" | "SELL",
    "ticker": "BTC-USD",
    "price": "50000.0",
    "size": "0.1",
    "fee": "5.0",
    "realizedPnl": "100.0",
    "createdAt": "2024-01-01T12:00:00Z",
    "effectiveAt": "2024-01-01T12:00:00Z"
}
```

### Historical PnL (z API)
```python
{
    "realizedPnl": "1000.0",
    "netPnl": "950.0",
    "createdAt": "2024-01-01T12:00:00Z",
    "effectiveAt": "2024-01-01T12:00:00Z"
}
```

### TraderScore (wewnętrzny)
```python
@dataclass
class TraderScore:
    address: str
    subaccount_number: int
    realized_pnl: float
    net_pnl: float
    fill_count: int
    turnover: float
    score: float  # Znormalizowany wynik
    window_start: datetime
    window_end: datetime
```

## Algorytm rankingu

### Okno czasowe
- Rolling window: 24h lub 7d
- `window_start = now - window_hours`
- `window_end = now`

### Metryki
1. **Realized PnL**: Suma zrealizowanego PnL w oknie
2. **Net PnL**: Suma netto PnL (realized + unrealized)
3. **Fill Count**: Liczba transakcji w oknie
4. **Turnover**: Całkowity wolumen (size * price)

### Scoring
```python
score = (
    weight_realized_pnl * realized_pnl +
    weight_net_pnl * net_pnl +
    weight_fill_count * fill_count +
    weight_turnover * (turnover / 1_000_000)  # Normalizacja
)
```

Domyślne wagi:
- `realized_pnl`: 0.4
- `net_pnl`: 0.3
- `fill_count`: 0.1
- `turnover`: 0.2

### Filtr anty-szum
- Min liczba fill'ów: 5 (domyślnie)
- Min wolumen: $1000 (domyślnie)
- Filtruje przed scoringiem

## Pseudokod procedur

### discoverCandidates()
```
1. Dla każdego ticker'a:
   a. Pobierz ostatnie fill'e (lookback_hours)
   b. Wyciągnij unikalne (address, subaccount_number)
   c. Agreguj: fill_count, total_volume, first_seen, last_seen

2. Filtruj:
   - fill_count >= min_fills
   - total_volume >= min_volume

3. Zwróć listę TraderCandidate
```

### scoreCandidates()
```
1. Dla każdego kandydata:
   a. Pobierz historical PnL (window_hours)
   b. Pobierz fill'e (window_hours)
   c. Agreguj metryki:
      - realized_pnl = sum(historicalPnl.realizedPnl)
      - net_pnl = sum(historicalPnl.netPnl)
      - fill_count = len(fills)
      - turnover = sum(fill.size * fill.price)
   d. Oblicz score (weighted sum)
   e. Utwórz TraderScore

2. Sortuj malejąco po score
3. Zwróć listę TraderScore
```

### updateTopTraders()
```
1. candidates = discoverCandidates()
2. scores = scoreCandidates(candidates)
3. top_traders = save_top_traders(scores[:top_n])
4. Zwróć top_traders
```

### watchTopTraders()
```
1. top_traders = repository.get_top_traders(top_n)
2. Dla każdego tradera:
   a. last_check = get_last_check_time(trader)
   b. fills = get_fills_since(last_check)
   c. Dla każdego fill'a:
      - Sprawdź deduplikację (fill_id)
      - Utwórz FillEvent
      - Emituj event (callback)
   d. Zaktualizuj last_check_time

3. Zwróć listę nowych FillEvent
```

## Optymalizacja kosztów (rate limiting)

### Cache
- Cache wyników scoringu (TTL: 5-10 min)
- Cache historical PnL (TTL: 1 min)
- Cache listy top traderów (TTL: 15 min)

### Sampling
- Nie sprawdzaj wszystkich kandydatów - tylko top 100-200
- Użyj parent subaccount jeśli dostępne (mniej requestów)

### Batchowanie
- Grupuj requesty dla wielu subkont w batch
- Użyj `createdOnOrAfter` do ograniczenia zakresu

### Wykrywanie zmian bez polling
- WebSocket dla real-time fills (jeśli dostępne)
- Event-driven: sprawdzaj tylko gdy są nowe fill'e
- Exponential backoff przy rate limit

## Gotchas (ważne szczegóły)

### 1. Paginacja
- API zwraca max 100 wyników na stronę
- Sprawdzaj `pagination.hasMore`
- Używaj `page` parametru
- Rate limiting między stronami (0.1s delay)

### 2. Rate Limit
- API ma rate limits (sprawdź dokumentację)
- 429 status = rate limit
- Exponential backoff: `delay * (2 ** attempt)`
- Cache agresywnie

### 3. Time Window
- Wszystkie timestampy normalizuj do UTC
- `createdAt` vs `effectiveAt`: używaj `effectiveAt` dla PnL
- Rolling window: `window_end = now`, `window_start = now - window_hours`
- Uwaga na timezone: API zwraca UTC, ale bez 'Z' suffix

### 4. Parent Subaccount
- Parent agreguje child subaccounts
- Mniej requestów = użyj parent jeśli możesz
- `parentSubaccountNumber` zamiast `subaccountNumber`

### 5. Idempotencja
- Deduplikacja fill'ów: użyj `fill.id` lub `createdAt + ticker`
- Deduplikacja top traderów: `(address, subaccount_number, window_end)`
- `observed_at` vs `effective_at`: różne znaczenie

### 6. Brakujące dane
- Niektóre fill'e mogą nie mieć `realizedPnl` (None)
- Historical PnL może być opóźnione (nie "natychmiast")
- Obsłuż `None` wartości gracefully

### 7. Adresy jako pseudonimy
- Nie próbuj deanonymizacji
- Traktuj adresy jako unikalne identyfikatory
- Nie zakładaj dostępu do danych prywatnych

## Integracja z resztą systemu

### Event callback
```python
def on_fill_event(event: FillEvent):
    # Publikuj do message queue (RabbitMQ, Redis, etc.)
    # Lub zapisz do bazy danych
    # Lub wyślij webhook
    pass

service.watch_top_traders(event_callback=on_fill_event)
```

### Database integration
```python
from src.database.manager import DatabaseManager

db = DatabaseManager()
service = DydxTopTradersService(db_manager=db)
# Repository automatycznie zapisze do DB
```

### Scheduler integration
```python
# Uruchom update co godzinę
scheduler.add_job(
    service.update_top_traders,
    'interval',
    hours=1,
    args=[['BTC-USD', 'ETH-USD']],
    kwargs={'top_n': 50}
)

# Uruchom watch co 5 minut
scheduler.add_job(
    service.watch_top_traders,
    'interval',
    minutes=5,
    kwargs={'top_n': 50}
)
```

## Przykładowe metryki do monitorowania

- Liczba requestów API / minuta
- Cache hit rate
- Liczba nowych fill eventów / minuta
- Czas wykonania `update_top_traders()`
- Liczba kandydatów vs liczba top traderów
- Średni score top traderów

