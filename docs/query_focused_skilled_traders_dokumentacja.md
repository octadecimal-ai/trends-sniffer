# Dokumentacja: Query Focused Skilled Traders

## Przegląd

Zapytanie `query_focused_skilled_traders.sql` znajduje traderów, którzy:
1. **Inwestują w mało aktywów** - maksymalnie 5 unikalnych tickerów
2. **Mają dobre wyniki** - wysoki ranking, aktywność i wolumen

## Cel zapytania

Identyfikacja traderów, którzy koncentrują się na małej liczbie aktywów (specjalizacja), ale osiągają dobre wyniki dzięki umiejętnościom tradingowym.

---

## Opis kolumn wynikowych

Zapytanie zwraca **19 kolumn** pogrupowanych w kategorie:

### 1. Identyfikacja Tradera

#### `trader_id` (BIGINT)
- **Opis**: Unikalny identyfikator tradera w bazie danych (klucz główny z tabeli `dydx_traders`)
- **Typ**: BIGINT
- **Przykład**: `1`, `42`, `176`
- **Użycie**: Do łączenia z innymi tabelami, referencji wewnętrznych

#### `address` (VARCHAR(42))
- **Opis**: Adres dYdX Chain tradera (format: `dydx1...`)
- **Typ**: VARCHAR(42)
- **Przykład**: `dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze`
- **Użycie**: Główny identyfikator tradera w systemie dYdX

#### `subaccount_number` (INTEGER)
- **Opis**: Numer subkonta tradera (0-127)
- **Typ**: INTEGER
- **Przykład**: `0`, `1`, `127`
- **Użycie**: Jeden trader może mieć wiele subkont, to określa które subkonto jest analizowane

---

### 2. Ranking i Nagrody

#### `rank` (INTEGER)
- **Opis**: Pozycja tradera w rankingu dYdX (1 = najlepszy)
- **Typ**: INTEGER
- **Przykład**: `1`, `5`, `23`, `100`
- **Użycie**: Wskaźnik ogólnej pozycji tradera w rankingu
- **Uwaga**: Może być NULL jeśli trader nie jest w rankingu

#### `estimated_rewards` (DECIMAL(30,6))
- **Opis**: Szacowane nagrody tradera w USD (z rankingu dYdX)
- **Typ**: DECIMAL(30,6)
- **Przykład**: `438180.74`, `58791.55`, `10564.24`
- **Użycie**: Proxy dla umiejętności tradera - wyższe nagrody = lepsze wyniki
- **Uwaga**: Może być NULL
- **Waga w skill_score**: 30%

---

### 3. Metryki "Mało Aktywów"

#### `unique_tickers_count` (INTEGER)
- **Opis**: Liczba unikalnych aktywów (tickerów), w które trader inwestuje
- **Typ**: INTEGER
- **Przykład**: `1`, `3`, `4`, `5`
- **Obliczanie**: `COUNT(DISTINCT f.ticker)`
- **Użycie**: Główna metryka "fokusa" - im mniej, tym bardziej skoncentrowany trader
- **Filtr**: `<= 5` (można dostosować)
- **Interpretacja**: 
  - `1` = bardzo skoncentrowany (jeden asset)
  - `2-3` = umiarkowanie skoncentrowany
  - `4-5` = lekko zdywersyfikowany

#### `traded_tickers` (TEXT)
- **Opis**: Lista wszystkich tickerów, w które trader inwestuje (oddzielone przecinkami)
- **Typ**: TEXT (STRING_AGG)
- **Przykład**: `BTC-USD, ETH-USD, SOL-USD`, `ETH-USD`, `BTC-USD, ETH-USD`
- **Obliczanie**: `STRING_AGG(DISTINCT f.ticker, ', ' ORDER BY f.ticker)`
- **Użycie**: Szybki przegląd, w które aktywa trader inwestuje
- **Format**: Posortowane alfabetycznie, oddzielone przecinkami i spacją

---

### 4. Metryki Aktywności

#### `total_fills_count` (INTEGER)
- **Opis**: Całkowita liczba transakcji (fill'ów) wykonanych przez tradera
- **Typ**: INTEGER
- **Przykład**: `100`, `189`, `253`
- **Obliczanie**: `COUNT(f.id)`
- **Użycie**: Wskaźnik aktywności tradera
- **Filtr**: `>= 10` (minimum dla wiarygodności statystyk)
- **Interpretacja**: Więcej transakcji = większa aktywność

#### `total_volume_usd` (DECIMAL(30,6))
- **Opis**: Całkowity wolumen transakcji w USD (suma price × size dla wszystkich fill'ów)
- **Typ**: DECIMAL(30,6)
- **Przykład**: `886692.90`, `9855593.71`, `368955.00`
- **Obliczanie**: `SUM(f.price::numeric * f.size::numeric)`
- **Użycie**: Wskaźnik zaangażowania kapitałowego
- **Filtr**: `> 0` (musi mieć jakiś wolumen)
- **Waga w skill_score**: 20% (znormalizowany do max 10M USD)
- **Interpretacja**: Wyższy wolumen = większe zaangażowanie

#### `avg_fill_size_usd` (DECIMAL(30,6))
- **Opis**: Średni rozmiar transakcji w USD
- **Typ**: DECIMAL(30,6)
- **Przykład**: `3504.72`, `98555.94`, `1952.14`
- **Obliczanie**: `total_volume_usd / total_fills_count`
- **Użycie**: Wskaźnik efektywności - średni rozmiar pojedynczej transakcji
- **Interpretacja**: 
  - Wysokie wartości = większe transakcje (może oznaczać większy kapitał)
  - Niskie wartości = mniejsze transakcje (może oznaczać częstsze, mniejsze pozycje)

#### `fills_per_day` (DECIMAL)
- **Opis**: Średnia liczba transakcji na dzień
- **Typ**: DECIMAL
- **Przykład**: `253.00`, `100.00`, `189.00`
- **Obliczanie**: `total_fills_count / GREATEST(trading_days, 1.0)`
- **Użycie**: Wskaźnik częstotliwości tradingu
- **Waga w skill_score**: 25% (znormalizowany do max 50 fills/day)
- **Interpretacja**: 
  - Wysokie wartości = bardzo aktywny trader
  - Niskie wartości = mniej aktywny trader
- **Uwaga**: Jeśli wszystkie transakcje są w tym samym dniu, `trading_days = 1.0`

#### `trading_days` (DECIMAL)
- **Opis**: Liczba dni aktywności tradingowej (różnica między pierwszą a ostatnią transakcją)
- **Typ**: DECIMAL
- **Przykład**: `0.0`, `0.6`, `1.7`, `30.5`
- **Obliczanie**: `EXTRACT(EPOCH FROM (MAX(effective_at) - MIN(effective_at))) / 86400.0`
- **Użycie**: Okres aktywności tradera
- **Interpretacja**: 
  - `0.0` = wszystkie transakcje w tym samym dniu
  - `> 1` = trader aktywny przez wiele dni
- **Uwaga**: Używane do obliczania `fills_per_day`

---

### 5. Metryki Strategii (Buy/Sell)

#### `buy_count` (INTEGER)
- **Opis**: Liczba transakcji typu BUY (zakup)
- **Typ**: INTEGER
- **Przykład**: `113`, `28`, `91`
- **Obliczanie**: `COUNT(*) FILTER (WHERE f.side = 'BUY')`
- **Użycie**: Analiza strategii tradera
- **Interpretacja**: Więcej buy = trader częściej otwiera długie pozycje

#### `sell_count` (INTEGER)
- **Opis**: Liczba transakcji typu SELL (sprzedaż)
- **Typ**: INTEGER
- **Przykład**: `140`, `72`, `98`
- **Obliczanie**: `COUNT(*) FILTER (WHERE f.side = 'SELL')`
- **Użycie**: Analiza strategii tradera
- **Interpretacja**: Więcej sell = trader częściej otwiera krótkie pozycje

#### `buy_sell_imbalance_percent` (DECIMAL)
- **Opis**: Wskaźnik niezbalansowania strategii buy/sell (0% = idealny balance, 100% = tylko buy lub tylko sell)
- **Typ**: DECIMAL
- **Przykład**: `10.7`, `44.0`, `0.0`, `3.7`
- **Obliczanie**: `ABS((buy_count / total_fills_count) - 0.5) * 200`
- **Użycie**: Wskaźnik różnorodności strategii
- **Waga w skill_score**: 15% (im bliżej 0%, tym lepiej)
- **Interpretacja**: 
  - `0%` = idealny balance (50% buy, 50% sell)
  - `10%` = lekko niezbalansowany (np. 55% buy, 45% sell)
  - `50%+` = bardzo niezbalansowany (np. 75% buy, 25% sell)
  - `100%` = tylko buy lub tylko sell

---

### 6. Metryki Czasowe

#### `first_fill_at` (TIMESTAMPTZ)
- **Opis**: Data i czas pierwszej transakcji tradera (UTC)
- **Typ**: TIMESTAMPTZ
- **Przykład**: `2025-12-09 18:00:00+00`, `2025-12-10 10:30:00+00`
- **Obliczanie**: `MIN(f.effective_at)`
- **Użycie**: Określenie początku aktywności tradera
- **Format**: ISO 8601 z timezone

#### `last_fill_at` (TIMESTAMPTZ)
- **Opis**: Data i czas ostatniej transakcji tradera (UTC)
- **Typ**: TIMESTAMPTZ
- **Przykład**: `2025-12-09 22:08:00+00`, `2025-12-10 15:45:00+00`
- **Obliczanie**: `MAX(f.effective_at)`
- **Użycie**: Określenie końca aktywności tradera
- **Format**: ISO 8601 z timezone

---

### 7. Metryki PnL (jeśli dostępne)

#### `total_net_pnl_from_pnl_table` (DECIMAL(30,6))
- **Opis**: Całkowity net PnL z tabeli `dydx_historical_pnl` (jeśli dostępne)
- **Typ**: DECIMAL(30,6)
- **Przykład**: `15000.50`, `-5000.25`, `NULL`
- **Obliczanie**: `SUM(net_pnl) FROM dydx_historical_pnl WHERE trader_id = t.id`
- **Użycie**: Rzeczywisty zysk/strata tradera (jeśli dane są dostępne)
- **Waga w skill_score**: 10% (znormalizowany do max 100k USD)
- **Uwaga**: 
  - Może być NULL jeśli trader nie ma danych w `dydx_historical_pnl`
  - Większość traderów może mieć NULL (tylko 24 rekordy w bazie)
- **Interpretacja**: 
  - Pozytywne = zysk
  - Negatywne = strata
  - NULL = brak danych

---

### 8. Kompozytowy Score Umiejętności

#### `skill_score` (DECIMAL)
- **Opis**: Kompozytowy wskaźnik umiejętności tradera (0-100)
- **Typ**: DECIMAL
- **Przykład**: `66.46`, `56.64`, `41.96`
- **Obliczanie**: Ważona suma znormalizowanych metryk:
  ```
  skill_score = 
    (estimated_rewards / 500000) * 0.30 +           # 30% - Ranking
    (fills_per_day / 50) * 0.25 +                    # 25% - Aktywność
    (total_volume_usd / 10000000) * 0.20 +           # 20% - Wolumen
    (1 - buy_sell_imbalance_percent / 100) * 0.15 +  # 15% - Różnorodność strategii
    (total_net_pnl_from_pnl_table / 100000) * 0.10   # 10% - Net PnL
  ```
- **Użycie**: Główna metryka do sortowania i porównywania traderów
- **Sortowanie**: Malejąco (wyższy = lepszy)
- **Interpretacja**: 
  - `80-100` = bardzo umiejętny trader
  - `60-80` = umiejętny trader
  - `40-60` = przeciętny trader
  - `0-40` = początkujący trader
- **Normalizacja**: Wszystkie komponenty są znormalizowane do zakresu 0-1 przed ważeniem

---

## Filtry zapytania

Zapytanie filtruje traderów według następujących kryteriów:

1. **`unique_tickers_count <= 5`**
   - Tylko traderzy inwestujący w maksymalnie 5 aktywów
   - Można dostosować (np. `<= 3` dla bardziej restrykcyjnego)

2. **`total_fills_count >= 10`**
   - Minimum 10 transakcji dla wiarygodności statystyk
   - Można dostosować (np. `>= 50` dla bardziej aktywnych)

3. **`total_volume_usd > 0`**
   - Musi mieć jakiś wolumen (wyklucza puste rekordy)

4. **`t.is_active = TRUE`**
   - Tylko aktywni traderzy

---

## Sortowanie wyników

Wyniki są sortowane w następującej kolejności:

1. **`skill_score DESC`** - Najpierw po kompozytowym score umiejętności (wyższy = lepszy)
2. **`unique_tickers_count ASC`** - Potem po liczbie aktywów (mniej = lepiej)
3. **`estimated_rewards DESC NULLS LAST`** - Potem po estimated rewards (wyższe = lepsze)
4. **`total_volume_usd DESC`** - Na końcu po wolumenie (wyższy = lepszy)

**Limit**: Top 20 traderów spełniających kryteria

---

## Uwagi techniczne

### Brak danych realized_pnl

⚠️ **Ważne**: Kolumna `realized_pnl` w tabeli `dydx_fills` jest pusta (wszystkie wartości NULL). 

Z tego powodu zapytanie używa **alternatywnych metryk** do oceny umiejętności:
- Ranking (`estimated_rewards`) - proxy dla umiejętności
- Aktywność (`fills_per_day`)
- Wolumen (`total_volume_usd`)
- Różnorodność strategii (`buy_sell_imbalance_percent`)
- Net PnL z `dydx_historical_pnl` (jeśli dostępne)

### Dostosowanie wag skill_score

Wagi w `skill_score` można dostosować w zapytaniu (linie 117-128):

```sql
-- Przykład: zwiększenie wagi dla ranking
LEAST(COALESCE(estimated_rewards, 0) / 500000.0, 1.0) * 0.40 +  -- było 0.30
```

### Filtry czasowe

Można dodać filtry czasowe, np. tylko ostatnie 30 dni:

```sql
WHERE 
    unique_tickers_count <= 5
    AND total_fills_count >= 10
    AND total_volume_usd > 0
    AND f.effective_at >= NOW() - INTERVAL '30 days'  -- Dodaj to
```

### Progi normalizacji

Progi normalizacji w `skill_score` można dostosować:
- `estimated_rewards`: max 500000 USD
- `fills_per_day`: max 50 fills/day
- `total_volume_usd`: max 10M USD
- `total_net_pnl_from_pnl_table`: max 100k USD

---

## Przykładowe użycie

```sql
-- Uruchomienie zapytania
\i database/query_focused_skilled_traders.sql

-- Lub w Pythonie:
import psycopg2
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
with open('database/query_focused_skilled_traders.sql', 'r') as f:
    cur.execute(f.read())
results = cur.fetchall()
```

---

## Historia zmian

- **2025-12-24**: Utworzenie zapytania i dokumentacji
- **2025-12-24**: Aktualizacja - użycie alternatywnych metryk zamiast realized_pnl (które jest puste)

---

## Autor

Dokumentacja utworzona: 2025-12-24  
Zapytanie: `database/query_focused_skilled_traders.sql`

