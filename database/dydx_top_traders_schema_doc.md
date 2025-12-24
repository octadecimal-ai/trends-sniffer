# dYdX Top Traders Observer - Struktura Tabel

## Przegląd architektury

Moduł składa się z 7 głównych tabel:

1. **dydx_traders** - Podstawowe informacje o traderach
2. **dydx_top_traders_rankings** - Rankingi top traderów (time-series)
3. **dydx_fills** - Fill'e (transakcje) od top traderów
4. **dydx_historical_pnl** - Historical PnL (cache z API)
5. **dydx_trader_metrics** - Agregowane metryki traderów (okresowe snapshoty)
6. **dydx_fill_events** - Eventy fill'ów do publikacji
7. **dydx_observer_log** - Log operacji observera

## Szczegółowy opis tabel

### 1. dydx_traders

**Cel**: Przechowuje podstawowe informacje o traderach (adres, subaccount) i agregowane statystyki.

**Kluczowe kolumny**:
- `address` + `subaccount_number` - Unikalny identyfikator tradera
- `parent_subaccount_number` - Dla agregacji parent-child
- `first_seen_at` / `last_seen_at` - Zakres obserwacji
- `total_fills_count`, `total_volume_usd`, `total_realized_pnl`, `total_net_pnl` - Agregowane statystyki (30 dni)

**Indeksy**:
- `(address, subaccount_number)` - UNIQUE
- `address`, `(address, subaccount_number)`, `(address, parent_subaccount_number)`
- `is_active`, `last_seen_at`

**Użycie**: 
- Lookup tradera po adresie
- Sprawdzanie czy trader jest aktywny
- Agregowane statystyki dla szybkiego dostępu

### 2. dydx_top_traders_rankings

**Cel**: Przechowuje rankingi top traderów w czasie (time-series).

**Kluczowe kolumny**:
- `trader_id` - FK do dydx_traders
- `rank` - Pozycja w rankingu (1 = najlepszy)
- `score` - Znormalizowany wynik rankingowy
- `window_start` / `window_end` / `window_hours` - Okno czasowe rankingu
- `realized_pnl`, `net_pnl`, `fill_count`, `turnover_usd` - Metryki w oknie
- `observed_at` - Kiedy pobrano dane z API (UTC)
- `effective_at` - Efektywna data rankingu (UTC)

**Indeksy**:
- `(trader_id, window_end, window_hours)` - UNIQUE
- `trader_id`, `(address, subaccount_number)`, `(window_start, window_end)`
- `effective_at`, `observed_at`, `(rank, effective_at)`
- `(effective_at, window_hours, rank)` - Dla szybkiego lookup rankingu

**Użycie**:
- Historia rankingu w czasie
- Porównanie pozycji tradera między okresami
- Analiza trendów (awans/spadek w rankingu)

### 3. dydx_fills

**Cel**: Przechowuje wszystkie fill'e (transakcje) od top traderów.

**Kluczowe kolumny**:
- `trader_id` - FK do dydx_traders
- `fill_id` - Unikalny ID fill'a (z API lub generated)
- `ticker`, `side`, `price`, `size`, `fee` - Dane transakcji
- `realized_pnl` - Realized PnL (może być NULL)
- `effective_at` - Efektywna data fill'a (UTC)
- `created_at` - Data utworzenia fill'a (UTC)
- `observed_at` - Kiedy pobrano z API (UTC)

**Indeksy**:
- `(fill_id, address, subaccount_number)` - UNIQUE (deduplikacja)
- `trader_id`, `(address, subaccount_number)`, `ticker`
- `effective_at`, `created_at`, `observed_at`
- `(address, subaccount_number, effective_at)` - Dla szybkiego lookup fill'ów tradera

**Użycie**:
- Historia transakcji top traderów
- Analiza aktywności (kiedy, co, ile)
- Wykrywanie wzorców tradingowych

### 4. dydx_historical_pnl

**Cel**: Cache historical PnL z API (optymalizacja - unikamy wielokrotnych requestów).

**Kluczowe kolumny**:
- `trader_id` - FK do dydx_traders
- `realized_pnl`, `net_pnl` - PnL
- `effective_at` - Efektywna data PnL (UTC)
- `observed_at` - Kiedy pobrano z API (UTC)

**Indeksy**:
- `(address, subaccount_number, effective_at)` - UNIQUE
- `trader_id`, `(address, subaccount_number)`, `effective_at`, `observed_at`
- `(address, subaccount_number, effective_at)` - Dla szybkiego lookup

**Użycie**:
- Cache PnL (TTL: 1-5 min)
- Unikanie wielokrotnych requestów do API
- Szybki dostęp do PnL dla scoringu

### 5. dydx_trader_metrics

**Cel**: Agregowane metryki traderów w okresach czasowych (hourly, daily, weekly).

**Kluczowe kolumny**:
- `trader_id` - FK do dydx_traders
- `period_start` / `period_end` / `period_type` - Okres metryk
- `fills_count`, `unique_tickers_count` - Metryki aktywności
- `total_volume_usd`, `avg_fill_size_usd`, `max_fill_size_usd` - Metryki wolumenu
- `total_realized_pnl`, `total_net_pnl`, `avg_realized_pnl`, `win_rate` - Metryki PnL
- `total_fees_usd` - Metryki opłat
- `calculated_at` - Kiedy obliczono metryki (UTC)

**Indeksy**:
- `(trader_id, period_start, period_end, period_type)` - UNIQUE
- `trader_id`, `(address, subaccount_number)`, `(period_start, period_end)`
- `period_type`, `calculated_at`
- `(trader_id, period_type, period_start)` - Dla szybkiego lookup metryk

**Użycie**:
- Agregowane metryki dla analizy
- Porównanie traderów między okresami
- Wykrywanie trendów (wzrost/spadek aktywności)

### 6. dydx_fill_events

**Cel**: Eventy fill'ów do publikacji do reszty systemu (message queue, webhook, etc.).

**Kluczowe kolumny**:
- `fill_id` - FK do dydx_fills
- `trader_id` - FK do dydx_traders
- `event_type` - Typ eventu (fill, large_fill, pnl_event, etc.)
- `event_status` - Status (pending, published, failed)
- `event_occurred_at` - Kiedy zdarzenie wystąpiło (effective_at)
- `event_created_at` - Kiedy event został utworzony
- `event_published_at` - Kiedy event został opublikowany
- `published_to` - Gdzie opublikowano (queue name, webhook URL)
- `publish_attempts`, `publish_error` - Retry logic
- `event_data` - Dane eventu (JSONB, serialized FillEvent)

**Indeksy**:
- `fill_id`, `trader_id`, `event_status`
- `event_occurred_at`
- `(event_status, event_occurred_at) WHERE event_status = 'pending'` - Dla pending events

**Użycie**:
- Kolejka eventów do publikacji
- Retry logic dla failed events
- Audit trail publikacji

### 7. dydx_observer_log

**Cel**: Log operacji observera (update_ranking, watch_traders, etc.).

**Kluczowe kolumny**:
- `operation_type` - Typ operacji (update_ranking, watch_traders, discover_candidates)
- `operation_status` - Status (running, success, failed, partial)
- `started_at` / `completed_at` - Timestampy operacji
- `candidates_discovered`, `traders_scored`, `top_traders_saved`, `fills_processed`, `events_created` - Statystyki
- `errors_count`, `error_message` - Błędy
- `config`, `details` - JSONB z konfiguracją i szczegółami

**Indeksy**:
- `operation_type`, `operation_status`, `started_at`
- `(operation_type, started_at)` - Dla szybkiego lookup logów

**Użycie**:
- Monitoring operacji
- Debugging błędów
- Analiza wydajności

## Relacje między tabelami

```
dydx_traders (1) ──< (N) dydx_top_traders_rankings
dydx_traders (1) ──< (N) dydx_fills
dydx_traders (1) ──< (N) dydx_historical_pnl
dydx_traders (1) ──< (N) dydx_trader_metrics
dydx_fills (1) ──< (N) dydx_fill_events
```

## Najlepsze praktyki zastosowane

1. **Normalizacja timestampów**: Wszystkie timestampy w UTC (TIMESTAMPTZ)
2. **Deduplikacja**: UNIQUE constraints na kluczowych kombinacjach
3. **Indeksy**: Indeksy na wszystkich kolumnach używanych w WHERE/JOIN
4. **Foreign keys**: CASCADE delete dla zależności
5. **Denormalizacja**: `address` i `subaccount_number` w tabelach potomnych (szybszy lookup)
6. **JSONB**: Dla metadanych i opcjonalnych danych (elastyczność)
7. **Triggers**: Automatyczna aktualizacja `updated_at` i `last_seen_at`
8. **Komentarze**: Dokumentacja tabel i kolumn w bazie

## Przykładowe zapytania

### Top 10 traderów (ostatni ranking)
```sql
SELECT 
    t.address,
    t.subaccount_number,
    r.rank,
    r.score,
    r.realized_pnl,
    r.fill_count
FROM dydx_top_traders_rankings r
JOIN dydx_traders t ON r.trader_id = t.id
WHERE r.effective_at = (
    SELECT MAX(effective_at) 
    FROM dydx_top_traders_rankings
)
ORDER BY r.rank
LIMIT 10;
```

### Fill'e top tradera (ostatnie 24h)
```sql
SELECT 
    f.ticker,
    f.side,
    f.price,
    f.size,
    f.realized_pnl,
    f.effective_at
FROM dydx_fills f
JOIN dydx_traders t ON f.trader_id = t.id
WHERE t.address = '0x...'
  AND f.effective_at >= NOW() - INTERVAL '24 hours'
ORDER BY f.effective_at DESC;
```

### Historia rankingu tradera
```sql
SELECT 
    r.effective_at,
    r.rank,
    r.score,
    r.realized_pnl,
    r.fill_count
FROM dydx_top_traders_rankings r
JOIN dydx_traders t ON r.trader_id = t.id
WHERE t.address = '0x...'
ORDER BY r.effective_at DESC;
```

### Pending events do publikacji
```sql
SELECT 
    e.id,
    e.event_type,
    e.event_occurred_at,
    f.ticker,
    f.side,
    f.price
FROM dydx_fill_events e
JOIN dydx_fills f ON e.fill_id = f.id
WHERE e.event_status = 'pending'
ORDER BY e.event_occurred_at ASC;
```

