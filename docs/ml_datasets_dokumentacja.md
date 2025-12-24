# ML Datasets dla Predykcji Kierunku BTC

## Przegląd

Ten dokument opisuje 5 zaawansowanych kwerend SQL zaprojektowanych do generowania datasetów dla modeli Machine Learning przewidujących kierunek ruchu ceny Bitcoin w ciągu następnej godziny.

**Autor:** Claude Opus 4.5 + trends-sniffer  
**Data utworzenia:** 2025-12-24  
**Baza danych:** trends_sniffer (PostgreSQL)

---

## Podsumowanie Struktury Bazy Danych

### Główne Źródła Danych

| Tabela | Rekordów | Zakres dat | Opis |
|--------|----------|------------|------|
| `ohlcv` | 3,560,449 | 2018-12 — 2025-12 | Świece OHLCV (głównie BTC/USDC 1m z Binance) |
| `dydx_perpetual_market_trades` | 468,350 | 2025-12-17 — 2025-12-24 | Transakcje perpetual z dYdX |
| `gdelt_sentiment` | 175,809 | 2025-12-17 — 2025-12-22 | Sentyment z mediów (GDELT) |
| `tickers` | 57,678 | 2020-01 — 2025-12 | Funding rate, open interest |
| `sentiment_measurement` | 13,764 | 2025-12 | Pomiary sentymentu Google Trends |

### Kluczowe Relacje

```
ohlcv ←→ tickers (timestamp, symbol)
dydx_perpetual_market_trades → standalone (transakcje rynkowe)
gdelt_sentiment → standalone (sentyment mediów, region = US/KR/DE/GB/CN)
dydx_traders → dydx_fills → dydx_fill_events (traderzy i ich transakcje)
countries → regions → sentiment_measurement (geograficzne dane sentymentu)
```

---

## Kwerenda 1: Order Flow Imbalance Dataset

### Teoria i Hipoteza Tradingowa

**Order Flow Imbalance (OFI)** to jedna z najbardziej predykcyjnych zmiennych w handlu wysokofrequencyjnym. Bazuje na fundamentalnej obserwacji, że nierównowaga między wolumenem BUY i SELL jest wyprzedzającym wskaźnikiem ruchu ceny.

#### Mechanizm Działania

1. **Agresywni kupujący (market takers)** wchodzą na rynek gdy spodziewają się wzrostu ceny
2. **Market makers** muszą podnieść ceny, aby zrównoważyć **inventory risk** (zbyt dużo shortów)
3. **Momentum traders** podążają za przepływem zleceń, wzmacniając ruch

#### Kluczowe Obserwacje z Danych

Z analizy danych dYdX (468K transakcji BTC-USD z 7 dni):
- Średni wolumen BUY: ~55% całkowitego wolumenu
- Średni wolumen SELL: ~45% całkowitego wolumenu
- Rozkład wielkości transakcji:
  - Micro (<0.01 BTC): 49% transakcji
  - Small (0.01-0.1 BTC): 40% transakcji
  - Medium (0.1-1 BTC): 10.6% transakcji
  - Large (1-10 BTC): 0.15% transakcji
  - Whale (>10 BTC): 0.0004% transakcji

### Features

| Feature | Opis | Wartości typowe |
|---------|------|-----------------|
| `order_flow_imbalance` | (buy_vol - sell_vol) / total_vol | -0.3 do +0.3 |
| `buy_sell_ratio` | buy_count / sell_count | 0.7 do 1.5 |
| `large_trade_ratio` | wolumen dużych transakcji / total | 0.1 do 0.5 |
| `whale_trade_ratio` | wolumen whale / total | 0 do 0.1 |
| `vwap_deviation_pct` | różnica VWAP vs close | -0.5% do +0.5% |
| `trade_count` | liczba transakcji w godzinie | 1000 do 10000 |

### Target

- `target_direction`: 1 = cena wzrośnie w następnej godzinie, 0 = spadnie
- `next_hour_return_pct`: procentowy zwrot (do regresji)

### Strategia ML

**Rekomendowane podejście:**
- Model: XGBoost / LightGBM (gradient boosting)
- Ważne features: `order_flow_imbalance`, `large_trade_ratio`, `whale_trade_ratio`
- Uwaga: Dataset wymaga wspólnego zakresu czasowego OHLCV + dYdX (od 2025-12-17)

---

## Kwerenda 2: Sentiment Momentum Dataset

### Teoria i Hipoteza Tradingowa

Sentyment medialny ma szczególny wpływ na rynek kryptowalut ze względu na:
1. **Dominację inwestorów detalicznych** wrażliwych na nastroje
2. **24/7 cykl informacyjny** bez przerw weekendowych
3. **Globalny charakter rynku** z różnymi strefami czasowymi

#### Kluczowe Hipotezy

1. **Momentum sentymentu** - gwałtowna zmiana nastrojów wyprzedza ruch ceny
2. **Contrarian signal** - ekstremalnie negatywny sentyment często oznacza lokalne dno
3. **Volume spike** - nagły wzrost liczby artykułów = zwiększona zmienność
4. **Divergence** - gdy sentyment i cena idą w przeciwnych kierunkach = potencjalny reversal

### Dane GDELT

GDELT (Global Database of Events, Language and Tone) zbiera dane z:
- Ponad 100,000 źródeł medialnych
- 65+ języków
- Real-time monitoring

**Metryki z bazy:**
- Region US dominuje (175,766 rekordów)
- Średni tone: -0.88 (lekko negatywny)
- Zakres tone: -10 do +10

### Features

| Feature | Opis | Interpretacja |
|---------|------|---------------|
| `avg_tone` | średni ton artykułów | < 0 = negatywny, > 0 = pozytywny |
| `tone_ma_6h` / `tone_ma_24h` | średnie kroczące | wygładzony trend |
| `sentiment_momentum_1h` | zmiana tone vs 1h wcześniej | acceleration |
| `sentiment_zscore` | jak daleko od normy | extremity indicator |
| `article_count` | liczba artykułów | attention proxy |
| `article_volume_zscore` | czy volume jest anomalią | spike detection |

### Strategia ML

**Rekomendowane podejście:**
- Model: LSTM / GRU (dla sekwencyjności sentymentu)
- Alternatywnie: Random Forest z rolling window features
- Key insight: sentyment działa lepiej jako **leading indicator** niż coincident

---

## Kwerenda 3: Funding Rate & Derivatives Dataset

### Teoria i Hipoteza Tradingowa

**Funding rate** na rynkach perpetual jest kluczowym wskaźnikiem pozycjonowania uczestników:
- **Positive funding** = więcej long pozycji = kupujący płacą sprzedającym
- **Negative funding** = więcej short pozycji = sprzedający płacą kupującym

#### Mechanizm Predykcyjny

1. **Ekstremalnie wysoki funding** (> 0.03% / 8h):
   - Rynek overleveraged w longach
   - Potencjalny short squeeze lub korekta
   - Smart money często fade'uje takie poziomy

2. **Ekstremalnie ujemny funding** (< -0.03% / 8h):
   - Rynek overleveraged w shortach
   - Potencjalny long squeeze lub odbicie
   - Contrarian opportunity

3. **Funding-Price Divergence**:
   - Funding rośnie + cena spada = buildup longów, potencjalne odbicie
   - Funding spada + cena rośnie = buildup shortów, potencjalna korekta

### Dane z Bazy

Z analizy tickers BTC/USDC (51,298 rekordów):
- Średni funding rate: 0.000122 (12.2 bps / 8h)
- Zakres: -0.0003 do +0.0005
- Open interest: średnio 88,166 BTC

### Features

| Feature | Opis | Wartości |
|---------|------|----------|
| `funding_rate_bps` | funding rate w basis points | -30 do +50 bps |
| `funding_ma_8h_bps` | 8h MA fundingu | wygładzony trend |
| `funding_zscore` | jak daleko od normy | extremity |
| `funding_extremity_level` | kategoryczny | -2 do +2 |
| `avg_oi` | open interest | exposure indicator |
| `oi_change_1h` | zmiana OI | new positions |
| `funding_price_divergence` | dywergencja | -1, 0, +1 |

### Strategia ML

**Rekomendowane podejście:**
- Model: Gradient Boosting z custom loss function
- Feature engineering: rolling extremity indicators
- Key insight: funding działa najlepiej jako **reversal signal** przy ekstremach

---

## Kwerenda 4: Multi-Timeframe Price Action Dataset

### Teoria i Hipoteza Tradingowa

**Price Action Analysis** to fundamentalna technika analizy technicznej bazująca na:
1. **Multi-timeframe confluence** - trend wyższego TF dominuje
2. **Mean reversion** - ceny wracają do średnich
3. **Volatility clustering** - wysoka zmienność rodzi wysoką zmienność
4. **Volume confirmation** - ruchy z wolumenem są bardziej wiarygodne

#### Hierarchia Timeframe'ów

```
24h trend > 12h trend > 4h trend > 1h trend
```

Gdy wszystkie timeframe'y są w zgodzie (trend alignment), prawdopodobieństwo kontynuacji jest wyższe.

### Features

| Feature | Opis | Zastosowanie |
|---------|------|--------------|
| `return_1h` / `return_4h` / `return_12h` / `return_24h` | zwroty różnych TF | momentum |
| `trend_alignment_score` | 0-3 (ile MA powyżej/poniżej) | confluence |
| `ma_spread_8_24` | spread między MA | trend strength |
| `hourly_volatility` | range / close | ATR proxy |
| `volatility_ratio` | bieżąca / średnia | volatility regime |
| `volume_ratio` | volume vs 24h średnia | volume anomaly |
| `price_position_24h` | pozycja w 24h range | overbought/oversold |

### Mean Reversion Signals

- `overbought_24h`: gdy price_position > 90%
- `oversold_24h`: gdy price_position < 10%

### Strategia ML

**Rekomendowane podejście:**
- Model: Ensemble (XGBoost + LSTM)
- Feature selection: użyj `trend_alignment_score` jako głównej zmiennej
- Uwaga: volatility clustering wymaga GARCH-like preprocessing

---

## Kwerenda 5: Combined Multi-Source Dataset (Master Query)

### Teoria i Hipoteza Tradingowa

**Signal Confluence** - gdy wiele niezależnych źródeł wskazuje ten sam kierunek, prawdopodobieństwo sukcesu jest znacząco wyższe.

#### Filozofia Multi-Source

Każde źródło danych wnosi unikalne informacje:

| Źródło | Informacja | Opóźnienie |
|--------|------------|------------|
| OHLCV (Binance) | Price action, technical | Real-time |
| Order Flow (dYdX) | Microstructure | Real-time |
| Sentiment (GDELT) | Behavioral | ~1-4h opóźnienia |
| Funding Rate | Derivatives positioning | 8h intervals |

### Composite Features

| Feature | Opis | Wartości |
|---------|------|----------|
| `bullish_confluence_score` | suma bullish signals | 0 do 3 |
| `bearish_confluence_score` | suma bearish signals | 0 do 3 |
| `hour_of_day` | godzina UTC | 0-23 |
| `day_of_week` | dzień tygodnia | 0-6 |
| `is_weekend` | czy weekend | 0/1 |

### Logika Confluence Score

**Bullish Confluence = 3** gdy:
1. Order flow imbalance > 10% (więcej kupujących)
2. Sentiment tone > 0 (pozytywny)
3. Price > MA8h (uptrend)

**Bearish Confluence = 3** gdy:
1. Order flow imbalance < -10% (więcej sprzedających)
2. Sentiment tone < 0 (negatywny)
3. Price < MA8h (downtrend)

### Strategia ML

**Rekomendowane podejście:**
1. **Feature Engineering:**
   - Confluence scores jako główne features
   - Interaction terms między źródłami
   - Time-of-day embeddings

2. **Model Architecture:**
   - Primary: XGBoost / LightGBM
   - Secondary: TabNet dla attention na features
   - Ensemble: stacking z logistic regression

3. **Validation Strategy:**
   - Walk-forward validation (nie random split!)
   - Purged cross-validation
   - Out-of-sample testing na nowych danych

---

## Użycie

### Eksport Datasetów

```bash
# Eksport wszystkich datasetów do CSV
python scripts/export_ml_datasets.py --dataset all --output ./data/ml

# Eksport konkretnego datasetu do Parquet
python scripts/export_ml_datasets.py --dataset combined --format parquet

# Eksport order flow
python scripts/export_ml_datasets.py --dataset order_flow
```

### Bezpośrednie Zapytania SQL

```bash
# Uruchom pełną kwerendę z pliku
psql "$DATABASE_URL" -f database/ml_datasets_queries.sql

# Lub pojedyncze zapytanie
psql "$DATABASE_URL" -c "SELECT * FROM (...kwerenda...) LIMIT 100"
```

### Przykład w Pythonie

```python
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))

# Wczytaj combined dataset
df = pd.read_sql("""
    WITH ohlcv_hourly AS (...) -- pełna kwerenda
    SELECT * FROM combined_features
""", conn)

# Przygotuj do ML
X = df.drop(['target_direction', 'next_hour_return_pct', 'timestamp'], axis=1)
y = df['target_direction']

# Train/test split (temporal!)
train_size = int(len(df) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]
```

---

## Ważne Uwagi

### Zakres Czasowy Danych

| Dataset | Wymaga danych z: | Min. wspólny zakres |
|---------|------------------|---------------------|
| Order Flow | dYdX + OHLCV | 2025-12-17 — 2025-12-24 |
| Sentiment | GDELT + OHLCV | 2025-12-17 — 2025-12-22 |
| Funding | Tickers + OHLCV | 2020-01 — 2025-12 (długi) |
| Price Action | OHLCV tylko | 2018-12 — 2025-12 (bardzo długi) |
| Combined | Wszystkie źródła | 2025-12-17 — 2025-12-22 (najkrótszy) |

### Potencjalne Problemy

1. **Look-ahead bias** - upewnij się, że target jest obliczany z przyszłych danych
2. **Survivorship bias** - nie dotyczy (mamy tylko BTC)
3. **Regime change** - model trenowany na bull market może nie działać w bear market
4. **Data leakage** - nie używaj przyszłych danych w features

### Rekomendacje Dalszych Kroków

1. **Rozszerzenie danych:**
   - Więcej historii dYdX (obecnie tylko 7 dni)
   - Inne regiony GDELT (nie tylko US)
   - Dodatkowe pary (ETH, SOL)

2. **Feature Engineering:**
   - Lagged features (1h, 2h, 4h wstecz)
   - Rolling statistics (volatility, correlation)
   - Cross-asset signals (BTC dominance, ETH ratio)

3. **Model Enhancement:**
   - Hyperparameter tuning
   - Ensemble methods
   - Interpretability (SHAP values)

---

## Pliki

- **SQL Queries:** `database/ml_datasets_queries.sql`
- **Export Script:** `scripts/export_ml_datasets.py`
- **Dokumentacja:** `docs/ml_datasets_dokumentacja.md`

---

*Dokument wygenerowany automatycznie przez Claude Opus 4.5 dla projektu trends-sniffer*

