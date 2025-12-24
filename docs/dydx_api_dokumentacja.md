# Dokumentacja API dYdX v4 Indexer

## Spis treści
1. [Wprowadzenie](#wprowadzenie)
2. [Endpointy API](#endpointy-api)
3. [Struktura danych](#struktura-danych)
4. [Przykłady użycia](#przykłady-użycia)
5. [Ograniczenia i uwagi](#ograniczenia-i-uwagi)

## Wprowadzenie

dYdX v4 to zdecentralizowana giełda działająca na własnym blockchainie opartym na Cosmos SDK. Moduł **Top Traders Observer** wykorzystuje publiczne API dYdX v4 Indexer do pobierania danych o transakcjach i wynikach traderów.

### Base URL
- **Mainnet**: `https://indexer.dydx.trade/v4`
- **Testnet**: `https://indexer.v4testnet.dydx.exchange/v4`

### Ważne informacje
- API jest **publiczne** - nie wymaga autoryzacji
- Wszystkie endpointy zwracają dane w formacie JSON
- Timestampy są w formacie ISO 8601 (UTC)
- Adresy używane w API to **adresy dYdX Chain** (format: `dydx1...`), nie Ethereum (`0x...`)

---

## Endpointy API

### 1. GET `/fills` - Pobieranie fill'ów (transakcji) dla subkonta

**Opis**: Pobiera zrealizowane transakcje (fills) dla konkretnego adresu i subkonta.

**Endpoint**: `GET https://indexer.dydx.trade/v4/fills`

**Parametry query** (wszystkie wymagane oprócz opcjonalnych):

| Parametr | Typ | Wymagany | Opis |
|----------|-----|----------|------|
| `address` | string | ✅ | Adres dYdX Chain (format: `dydx1...`) |
| `subaccountNumber` | integer | ✅ | Numer subkonta (0-127) |
| `limit` | integer | ❌ | Maksymalna liczba wyników (max 100, domyślnie 100) |
| `ticker` | string | ❌ | Symbol rynku (np. `BTC-USD`, `ETH-USD`) |
| `createdBeforeOrAt` | ISO datetime | ❌ | Filtruj fill'e przed tą datą (UTC) |
| `createdOnOrAfter` | ISO datetime | ❌ | Filtruj fill'e od tej daty (UTC) |
| `page` | integer | ❌ | Numer strony (dla paginacji) |

**Przykładowe zapytanie**:
```bash
curl "https://indexer.dydx.trade/v4/fills?address=dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze&subaccountNumber=0&limit=100"
```

**Odpowiedź**:
```json
{
  "fills": [
    {
      "id": "25c60619-fda0-5b2d-b034-4f2c38c92b81",
      "side": "BUY",
      "liquidity": "TAKER",
      "type": "LIMIT",
      "market": "BTC-USD",
      "marketType": "PERPETUAL",
      "price": "87540",
      "size": "0.1142",
      "fee": "0",
      "affiliateRevShare": "0",
      "createdAt": "2025-12-23T22:23:22.897Z",
      "createdAtHeight": "68663717",
      "orderId": "a2e6f182-cfc7-5718-9991-9f8d314d4eb9",
      "clientMetadata": "3711765758",
      "subaccountNumber": 0,
      "positionSizeBefore": "0.7972",
      "entryPriceBefore": "87561.29066313818780704102",
      "positionSideBefore": "LONG"
    }
  ]
}
```

**Struktura obiektu Fill**:

| Pole | Typ | Opis |
|------|-----|------|
| `id` | string | Unikalny identyfikator fill'a (UUID) |
| `side` | string | Kierunek transakcji: `"BUY"` lub `"SELL"` |
| `liquidity` | string | Typ płynności: `"TAKER"` lub `"MAKER"` |
| `type` | string | Typ zlecenia: `"LIMIT"`, `"MARKET"`, `"LIQUIDATED"` |
| `market` | string | Symbol rynku (np. `"BTC-USD"`, `"ETH-USD"`) |
| `marketType` | string | Typ rynku: `"PERPETUAL"` |
| `price` | string | Cena transakcji (jako string) |
| `size` | string | Rozmiar transakcji (jako string) |
| `fee` | string | Opłata transakcyjna (jako string) |
| `affiliateRevShare` | string | Udział w opłatach dla affiliate (jako string) |
| `createdAt` | ISO datetime | Data utworzenia fill'a (UTC) |
| `createdAtHeight` | string | Wysokość bloku w momencie utworzenia |
| `orderId` | string/null | ID zlecenia (może być null) |
| `clientMetadata` | string/null | Metadane klienta (może być null) |
| `subaccountNumber` | integer | Numer subkonta |
| `positionSizeBefore` | string/null | Rozmiar pozycji przed transakcją (opcjonalnie) |
| `entryPriceBefore` | string/null | Cena wejścia przed transakcją (opcjonalnie) |
| `positionSideBefore` | string/null | Strona pozycji przed transakcją: `"LONG"` lub `"SHORT"` (opcjonalnie) |

**Uwagi**:
- Endpoint wymaga podania konkretnego adresu - nie można pobrać wszystkich fill'ów z rynku
- Maksymalna liczba wyników na stronę: 100
- Wartości numeryczne (`price`, `size`, `fee`) są zwracane jako stringi
- Endpoint używa **parametrów query**, nie ścieżki URL

---

### 2. GET `/historical-pnl` - Pobieranie historycznych PnL dla subkonta

**Opis**: Pobiera historyczne dane o zyskach i stratach (PnL) dla konkretnego adresu i subkonta.

**Endpoint**: `GET https://indexer.dydx.trade/v4/historical-pnl`

**Parametry query**:

| Parametr | Typ | Wymagany | Opis |
|----------|-----|----------|------|
| `address` | string | ✅ | Adres dYdX Chain (format: `dydx1...`) |
| `subaccountNumber` | integer | ✅ | Numer subkonta (0-127) |
| `limit` | integer | ❌ | Maksymalna liczba wyników (max 100) |
| `createdOnOrAfter` | ISO datetime | ❌ | Filtruj PnL od tej daty (UTC) |
| `createdBeforeOrAt` | ISO datetime | ❌ | Filtruj PnL przed tą datą (UTC) |
| `page` | integer | ❌ | Numer strony (dla paginacji) |

**Przykładowe zapytanie**:
```bash
curl "https://indexer.dydx.trade/v4/historical-pnl?address=dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze&subaccountNumber=0&limit=100"
```

**Odpowiedź**:
```json
{
  "historicalPnl": [
    {
      "equity": "5082997.544897",
      "totalPnl": "4794381.149659",
      "netTransfers": "0.000000",
      "createdAt": "2025-12-23T22:00:57.133Z",
      "blockHeight": "68661584",
      "blockTime": "2025-12-23T22:00:55.817Z"
    }
  ]
}
```

**Struktura obiektu Historical PnL**:

| Pole | Typ | Opis |
|------|-----|------|
| `equity` | string | Aktualny kapitał (equity) w USD |
| `totalPnl` | string | Całkowity zysk/strata (PnL) w USD |
| `netTransfers` | string | Netto transferów (depozyty - wypłaty) |
| `createdAt` | ISO datetime | Data utworzenia snapshot'a (UTC) |
| `blockHeight` | string | Wysokość bloku |
| `blockTime` | ISO datetime | Czas bloku (UTC) |

**Uwagi**:
- Endpoint używa **parametrów query**, nie ścieżki URL
- Wartości numeryczne są zwracane jako stringi
- Dane są snapshot'ami stanu konta w określonych momentach czasu

---

### 3. GET `/trades/perpetualMarket/{ticker}` - Transakcje z rynku (bez adresów traderów)

**Opis**: Pobiera ostatnie transakcje dla konkretnego rynku. **UWAGA**: Ten endpoint nie zwraca adresów traderów, tylko podstawowe informacje o transakcjach.

**Endpoint**: `GET https://indexer.dydx.trade/v4/trades/perpetualMarket/{ticker}`

**Parametry query**:

| Parametr | Typ | Wymagany | Opis |
|----------|-----|----------|------|
| `limit` | integer | ❌ | Maksymalna liczba wyników (max 100) |
| `createdBeforeOrAt` | ISO datetime | ❌ | Filtruj przed datą |
| `createdOnOrAfter` | ISO datetime | ❌ | Filtruj od daty |

**Przykładowe zapytanie**:
```bash
curl "https://indexer.dydx.trade/v4/trades/perpetualMarket/BTC-USD?limit=5"
```

**Odpowiedź**:
```json
{
  "trades": [
    {
      "id": "0417acd60000000200000002",
      "side": "BUY",
      "size": "0.0014",
      "price": "87656",
      "type": "LIMIT",
      "createdAt": "2025-12-23T21:48:51.985Z",
      "createdAtHeight": "68660438"
    }
  ]
}
```

**Struktura obiektu Trade**:

| Pole | Typ | Opis |
|------|-----|------|
| `id` | string | Unikalny identyfikator transakcji |
| `side` | string | Kierunek: `"BUY"` lub `"SELL"` |
| `size` | string | Rozmiar transakcji |
| `price` | string | Cena transakcji |
| `type` | string | Typ zlecenia: `"LIMIT"`, `"MARKET"`, etc. |
| `createdAt` | ISO datetime | Data utworzenia (UTC) |
| `createdAtHeight` | string | Wysokość bloku |

**Uwagi**:
- **Ten endpoint NIE zawiera adresów traderów** - nie można użyć go do identyfikacji konkretnych traderów
- Przydatny do analizy aktywności rynku, ale nie do śledzenia konkretnych traderów

---

### 4. GET `/addresses/{address}/parentSubaccountNumber/{parentSubaccountNumber}/fills` - Fill'e dla parent subkonta

**Opis**: Pobiera fill'e dla parent subkonta (agregacja dla rodzica i jego child subaccounts).

**Endpoint**: `GET https://indexer.dydx.trade/v4/addresses/{address}/parentSubaccountNumber/{parentSubaccountNumber}/fills`

**Parametry query**: Analogiczne do `/fills`, ale dla parent subkonta.

**Uwagi**:
- Używany do agregacji danych z wielu subkont pod jednym parent subkonto
- Struktura odpowiedzi identyczna jak `/fills`

---

### 5. GET `/addresses/{address}/parentSubaccountNumber/{parentSubaccountNumber}/historical-pnl` - Historical PnL dla parent subkonta

**Opis**: Pobiera historyczne PnL dla parent subkonta.

**Endpoint**: `GET https://indexer.dydx.trade/v4/addresses/{address}/parentSubaccountNumber/{parentSubaccountNumber}/historical-pnl`

**Parametry query**: Analogiczne do `/historical-pnl`, ale dla parent subkonta.

---

## Struktura danych

### Format adresów

dYdX v4 używa **adresów dYdX Chain** (format Cosmos), nie adresów Ethereum:

- ✅ **Poprawny format**: `dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze`
- ❌ **Niepoprawny format**: `0x1234567890abcdef1234567890abcdef12345678` (Ethereum)

### Format timestampów

Wszystkie timestampy są w formacie **ISO 8601** z timezone UTC:
- Format: `2025-12-23T22:23:22.897Z`
- `Z` oznacza UTC (Zulu time)

### Format wartości numerycznych

Wszystkie wartości numeryczne (ceny, rozmiary, opłaty) są zwracane jako **stringi**, nie liczby:
- `"price": "87540"` (nie `87540`)
- `"size": "0.1142"` (nie `0.1142`)

### Paginacja

Większość endpointów obsługuje paginację:
- Maksymalna liczba wyników na stronę: **100**
- Parametr `page` określa numer strony (zaczyna od 1)
- Odpowiedź zawiera obiekt `pagination` z informacją o `hasMore`

---

## Przykłady użycia

### Przykład 1: Pobranie fill'ów dla tradera

```python
from src.providers.dydx_indexer_provider import DydxIndexerProvider

provider = DydxIndexerProvider()

# Pobierz fill'e dla konkretnego adresu
fills = provider.get_subaccount_fills(
    address="dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze",
    subaccount_number=0,
    limit=100
)

print(f"Znaleziono {len(fills.get('fills', []))} fill'ów")
```

### Przykład 2: Pobranie wszystkich fill'ów z paginacją

```python
from src.providers.dydx_indexer_provider import DydxIndexerProvider
from datetime import datetime, timedelta, timezone

provider = DydxIndexerProvider()

# Pobierz wszystkie fill'e z ostatnich 24 godzin
cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

all_fills = provider.get_all_fills_paginated(
    address="dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze",
    subaccount_number=0,
    created_on_or_after=cutoff
)

print(f"Znaleziono łącznie {len(all_fills)} fill'ów")
```

### Przykład 3: Pobranie historical PnL

```python
from src.providers.dydx_indexer_provider import DydxIndexerProvider
from datetime import datetime, timedelta, timezone

provider = DydxIndexerProvider()

# Pobierz PnL z ostatnich 7 dni
cutoff = datetime.now(timezone.utc) - timedelta(days=7)

pnls = provider.get_all_historical_pnls_paginated(
    address="dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze",
    subaccount_number=0,
    created_on_or_after=cutoff
)

for pnl in pnls:
    print(f"Equity: ${float(pnl['equity']):,.2f}, Total PnL: ${float(pnl['totalPnl']):,.2f}")
```

**Status**: ✅ Endpoint działa, możemy pobrać dane. Tabela `dydx_historical_pnl` istnieje w bazie, ale jeszcze nie zapisujemy danych.

### Przykład 4: Pobranie trades z perpetualMarket

```python
from src.providers.dydx_indexer_provider import DydxIndexerProvider

provider = DydxIndexerProvider()

# Pobierz ostatnie transakcje z rynku BTC-USD
trades = provider.get_trades_for_market(
    ticker="BTC-USD",
    limit=100
)

print(f"Znaleziono {len(trades)} transakcji")
for trade in trades[:5]:
    print(f"{trade['side']} {trade['size']} @ {trade['price']}")
```

**Status**: ✅ Endpoint działa, ale **nie zawiera adresów traderów** - nie można użyć do identyfikacji konkretnych traderów.

### Przykład 5: Użycie bezpośrednio w skrypcie

```bash
# Pobierz fill'e dla tradera
python src/scripts/populate_dydx_fills.py \
    --address dydx1l24wamfqekxkl2650xlhx95e026stpq3ns3xze \
    --limit 100

# Pobierz fill'e dla wszystkich traderów z CSV
python src/scripts/populate_dydx_fills.py \
    --from-csv data/top-trades.csv \
    --limit 100
```

**Uwaga**: Obecnie skrypt pobiera tylko fill'e. Historical PnL można dodać w przyszłości.

---

## Ograniczenia i uwagi

### Rate Limiting
- API może zwracać błąd `429 Too Many Requests` przy zbyt częstych zapytaniach
- Implementacja automatycznie retry'uje z exponential backoff
- Zalecane opóźnienie między zapytaniami: minimum 0.1s

### Ograniczenia endpointów

1. **`/fills` wymaga konkretnego adresu**
   - ❌ Nie można pobrać wszystkich fill'ów z rynku
   - ✅ Musisz znać adres tradera, aby pobrać jego transakcje
   - ✅ Używamy listy adresów z CSV (`top-trades.csv`)

2. **`/trades/perpetualMarket/{ticker}` nie zawiera adresów**
   - ❌ Nie można użyć do identyfikacji konkretnych traderów
   - ✅ Przydatny do analizy aktywności rynku

3. **Maksymalna liczba wyników na stronę: 100**
   - Wszystkie endpointy mają limit 100 wyników na stronę
   - Używamy paginacji do pobrania większej liczby danych

### Obsługa błędów

Implementacja automatycznie obsługuje:
- **429 Rate Limit**: Czeka z exponential backoff
- **404 Not Found**: Może oznaczać, że adres nie ma fill'ów
- **Timeout**: Retry z dłuższym timeout'em
- **Network errors**: Retry z exponential backoff

### Normalizacja danych

Wszystkie timestampy są automatycznie normalizowane do UTC:
- `createdAt` → `datetime` w UTC
- `effectiveAt` → `datetime` w UTC
- `observed_at` → `datetime` w UTC (kiedy pobrano z API)

---

## Mapowanie danych do bazy

### Tabela `dydx_fills`

| Pole API | Pole w bazie | Uwagi |
|----------|--------------|-------|
| `id` | `fill_id` | Unikalny identyfikator |
| `market` | `ticker` | Symbol rynku |
| `side` | `side` | BUY/SELL |
| `price` | `price` | Konwersja string → DECIMAL |
| `size` | `size` | Konwersja string → DECIMAL |
| `fee` | `fee` | Konwersja string → DECIMAL |
| `createdAt` | `effective_at`, `created_at` | Oba ustawione na `createdAt` |
| `createdAt` | `observed_at` | Kiedy pobrano z API |
| `liquidity`, `type`, etc. | `metadata` (JSONB) | Dodatkowe dane w JSON |

### Tabela `dydx_traders`

| Źródło | Pole w bazie | Uwagi |
|--------|--------------|-------|
| CSV (`Rank`) | `rank` | Pozycja w rankingu |
| CSV (`Estimated Rewards`) | `estimated_rewards` | Szacowane nagrody |
| API (`address`) | `address` | Adres dYdX Chain |
| API (`subaccountNumber`) | `subaccount_number` | Numer subkonta |

### Tabela `dydx_historical_pnl` (gotowa, ale jeszcze nie używana)

| Pole API | Pole w bazie | Uwagi |
|----------|--------------|-------|
| `totalPnl` | `net_pnl` | Całkowity PnL (zysk/strata) |
| `equity` | `metadata` (JSONB) | Kapitał - zapisujemy w metadata |
| `netTransfers` | `metadata` (JSONB) | Netto transferów - zapisujemy w metadata |
| `createdAt` | `effective_at`, `created_at` | Oba ustawione na `createdAt` |
| `blockHeight`, `blockTime` | `metadata` (JSONB) | Dodatkowe dane w JSON |
| - | `realized_pnl` | ⚠️ API nie zwraca - może być NULL lub 0 |
| - | `observed_at` | Kiedy pobrano z API |

**Uwaga**: API zwraca `totalPnl` (net PnL), ale nie `realizedPnl`. W tabeli mamy oba pola - `realized_pnl` może pozostać NULL lub 0.

---

## Podsumowanie

### Co pobieramy z API dYdX:

1. **Fill'e (transakcje)** - z endpointu `/fills` ✅ **AKTYWNIE UŻYWANE**
   - Dla każdego tradera z listy (1000 traderów z CSV)
   - Do 100 fill'ów na tradera (można zwiększyć przez paginację)
   - Zapisujemy do tabeli `dydx_fills`
   - **Status**: Działa, zapisujemy do bazy

2. **Historical PnL** - z endpointu `/historical-pnl` ✅ **DZIAŁA, GOTOWE DO UŻYCIA**
   - Dla każdego tradera (opcjonalnie)
   - Zwraca: `equity`, `totalPnl`, `netTransfers`, `createdAt`, `blockHeight`, `blockTime`
   - Możemy zapisać do tabeli `dydx_historical_pnl` (tabela istnieje w bazie)
   - **Status**: Endpoint działa, ale nie jest jeszcze używany w `populate_dydx_fills.py`
   - **Uwaga**: Struktura API (`totalPnl`, `equity`) różni się od struktury tabeli (`realized_pnl`, `net_pnl`)

3. **Trades z perpetualMarket** - z endpointu `/trades/perpetualMarket/{ticker}` ⚠️ **DZIAŁA, ALE BEZ ADRESÓW**
   - Zwraca transakcje z rynku (np. BTC-USD)
   - **Problem**: Nie zawiera adresów traderów - nie można zidentyfikować kto wykonał transakcję
   - **Status**: Endpoint działa, ale nie przydatny do śledzenia konkretnych traderów
   - **Użycie**: Można użyć do analizy aktywności rynku, ale nie do identyfikacji traderów

4. **Ranking i nagrody** - z pliku CSV
   - Rank (pozycja w rankingu)
   - Estimated Rewards (szacowane nagrody)
   - Zapisujemy do tabeli `dydx_traders`

### Główne endpointy używane w projekcie:

| Endpoint | Użycie | Status | Możliwość pobrania |
|----------|--------|--------|-------------------|
| `GET /fills` | ✅ Główny endpoint do pobierania transakcji | Aktywny | ✅ TAK - używamy |
| `GET /historical-pnl` | ⚠️ Do scoringu traderów | Gotowy | ✅ TAK - działa, ale nie używamy jeszcze |
| `GET /trades/perpetualMarket/{ticker}` | ❌ Analiza rynku (bez adresów) | Działa | ✅ TAK - działa, ale bez adresów traderów |

### Dane zapisywane do bazy:

- **`dydx_traders`**: Informacje o traderach (adres, rank, estimated_rewards) ✅
- **`dydx_fills`**: Wszystkie transakcje (fills) od top traderów ✅
- **`dydx_historical_pnl`**: Historyczne PnL (tabela istnieje, ale jeszcze nie zapisujemy) ⚠️
- **`dydx_top_traders_rankings`**: Rankingi top traderów (time-series)

### Możliwość rozszerzenia:

**Historical PnL** - możemy dodać do skryptu `populate_dydx_fills.py`:
- Endpoint działa poprawnie
- Tabela `dydx_historical_pnl` istnieje w bazie
- Wymaga mapowania: `totalPnl` → `net_pnl`, `equity` → metadata
- Może być użyte do lepszego scoringu traderów

**Trades z perpetualMarket** - ograniczone użycie:
- Endpoint działa, ale nie zawiera adresów traderów
- Można użyć do analizy aktywności rynku (ile transakcji, wolumen)
- Nie można użyć do identyfikacji konkretnych traderów

---

## Linki

- [Oficjalna dokumentacja dYdX v4](https://docs.dydx.exchange/)
- [dYdX v4 Indexer API](https://docs.dydx.exchange/v4-teams/reference/indexer)
- [Kod implementacji](../src/providers/dydx_indexer_provider.py)
- [Skrypt pobierania fill'ów](../src/scripts/populate_dydx_fills.py)

