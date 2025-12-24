# 🔌 Lista API i Źródeł Danych

## Wprowadzenie

Ten dokument zawiera szczegółowe informacje o wszystkich API i źródłach danych przydatnych dla projektu trends-sniffer.

---

## 🟢 Darmowe API (Tier 1)

### 1. Yahoo Finance (yfinance)

**Typ**: Python library (nieoficjalne API)
**Dane**: Stocks, ETFs, Indices, Currencies, Commodities

```python
import yfinance as yf

# Indeksy
spx = yf.Ticker("^GSPC")  # S&P 500
vix = yf.Ticker("^VIX")   # Volatility Index
dxy = yf.Ticker("DX-Y.NYB")  # Dollar Index
nasdaq = yf.Ticker("^IXIC")  # NASDAQ Composite

# Commodities
gold = yf.Ticker("GC=F")  # Gold Futures
oil = yf.Ticker("CL=F")   # WTI Crude

# Get hourly data
data = spx.history(period="5d", interval="1h")

# Get real-time quote
quote = spx.info
```

| Aspekt | Wartość |
|--------|---------|
| Rate limit | ~2000 req/hour (unofficial) |
| Latency | 500ms - 2s |
| Reliability | ⭐⭐⭐⭐ (może przestać działać) |
| Koszt | **FREE** |

### 2. FRED (Federal Reserve Economic Data)

**Typ**: REST API
**Dane**: Makroekonomiczne US, stopy procentowe, M2

```python
from fredapi import Fred

fred = Fred(api_key='YOUR_API_KEY')

# Stopy procentowe
fed_funds = fred.get_series('FEDFUNDS')
treasury_10y = fred.get_series('DGS10')

# Podaż pieniądza
m2 = fred.get_series('M2SL')

# Inflacja
cpi = fred.get_series('CPIAUCSL')
```

**Rejestracja**: https://fred.stlouisfed.org/docs/api/api_key.html

| Aspekt | Wartość |
|--------|---------|
| Rate limit | 120 req/min |
| Data freshness | Daily/Monthly (zależnie od serii) |
| Koszt | **FREE** (wymaga API key) |

### 3. Alternative.me - Fear & Greed Index

**Typ**: REST API
**Dane**: Crypto Fear & Greed Index

```python
import requests

url = "https://api.alternative.me/fng/"
params = {
    "limit": 30,  # ostatnie 30 dni
    "format": "json"
}

response = requests.get(url, params=params)
data = response.json()

# Przykład odpowiedzi:
# {
#   "data": [
#     {"value": "25", "value_classification": "Extreme Fear", "timestamp": "..."},
#     ...
#   ]
# }
```

| Aspekt | Wartość |
|--------|---------|
| Rate limit | Nieznany (umiarkowany) |
| Update frequency | Raz dziennie |
| Koszt | **FREE** |

### 4. GDELT Project

**Typ**: BigQuery / REST
**Dane**: Globalne newsy, sentiment, events

```python
# BigQuery approach
from google.cloud import bigquery

client = bigquery.Client()

query = """
SELECT DATE, SourceCommonName, Tone, Themes, DocumentIdentifier
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE >= '2024-01-01'
  AND Themes LIKE '%CRYPTOCURRENCY%'
  OR Themes LIKE '%BITCOIN%'
ORDER BY DATE DESC
LIMIT 1000
"""

results = client.query(query).result()
```

| Aspekt | Wartość |
|--------|---------|
| BigQuery cost | First 1TB/month free |
| Update frequency | Every 15 minutes |
| Koszt | **FREE** (do limitu) |

### 5. NOAA Space Weather

**Typ**: REST API
**Dane**: Sunspots, geomagnetic activity

```python
import requests

# Kp Index (planetary magnetic activity)
kp_url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
kp_data = requests.get(kp_url).json()

# Sunspot number
sunspot_url = "https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json"
sunspot_data = requests.get(sunspot_url).json()
```

| Aspekt | Wartość |
|--------|---------|
| Rate limit | Generous |
| Update frequency | Varies (3-hourly Kp) |
| Koszt | **FREE** |

### 6. GitHub API

**Typ**: REST / GraphQL
**Dane**: Repository activity, commits, contributors

```python
import requests

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# Bitcoin Core stats
url = "https://api.github.com/repos/bitcoin/bitcoin/stats/commit_activity"
commits = requests.get(url, headers=headers).json()

# Contributors
url = "https://api.github.com/repos/bitcoin/bitcoin/contributors"
contributors = requests.get(url, headers=headers).json()
```

| Aspekt | Wartość |
|--------|---------|
| Rate limit | 5000 req/hour (authenticated) |
| Koszt | **FREE** |

### 7. Reddit API (PRAW)

**Typ**: Python library (official API)
**Dane**: Posts, comments, sentiment

```python
import praw

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="trends-sniffer/1.0"
)

# Get hot posts
subreddit = reddit.subreddit("Bitcoin")
for post in subreddit.hot(limit=100):
    print(post.title, post.score)
```

| Aspekt | Wartość |
|--------|---------|
| Rate limit | 60 req/min |
| Koszt | **FREE** (basic tier) |

### 8. CoinGecko API

**Typ**: REST API
**Dane**: Crypto prices, market cap, volume

```python
import requests

# Bitcoin data
url = "https://api.coingecko.com/api/v3/coins/bitcoin"
params = {
    "localization": "false",
    "tickers": "false",
    "community_data": "true",
    "developer_data": "true"
}

response = requests.get(url, params=params).json()
```

| Aspekt | Wartość |
|--------|---------|
| Rate limit | 10-50 req/min (free tier) |
| Koszt | **FREE** (z limitami) |

---

## 🟡 Płatne API (Tier 2)

### 9. Glassnode

**Typ**: REST API
**Dane**: On-chain metrics (MVRV, NUPL, Exchange Flows, etc.)

```python
import requests

API_KEY = "your_api_key"
base_url = "https://api.glassnode.com/v1/metrics"

# MVRV Ratio
url = f"{base_url}/market/mvrv"
params = {
    "a": "BTC",
    "api_key": API_KEY,
    "i": "24h"  # interval: 1h, 24h, 1w
}

response = requests.get(url, params=params).json()
```

| Plan | Cena/mies | Limit |
|------|-----------|-------|
| Standard | $49 | 10K req |
| Professional | $149 | 50K req |
| Advanced | $299 | 200K req |
| Institutional | $799 | Unlimited |

### 10. CryptoQuant

**Typ**: REST API
**Dane**: Exchange flows, whale movements

```python
import requests

API_KEY = "your_api_key"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Exchange netflow
url = "https://api.cryptoquant.com/v1/btc/exchange-flows/netflow"
params = {
    "exchange": "all",
    "window": "hour"
}

response = requests.get(url, headers=headers, params=params).json()
```

| Plan | Cena/mies |
|------|-----------|
| Basic | $29 |
| Professional | $99 |

### 11. Santiment

**Typ**: GraphQL API
**Dane**: Social + On-chain combined

```python
import san

# Wymaga API key
san.ApiConfig.api_key = 'your_api_key'

# Social volume
social = san.get(
    "social_volume/bitcoin",
    from_date="2024-01-01",
    to_date="2024-12-31",
    interval="1d"
)

# Development activity
dev = san.get(
    "dev_activity/bitcoin",
    from_date="2024-01-01",
    to_date="2024-12-31",
    interval="1d"
)
```

| Plan | Cena/mies |
|------|-----------|
| Free | $0 (limited) |
| Pro | $49 |
| Pro+ | $149 |
| Business | $349 |

### 12. Twitter/X API

**Typ**: REST / Streaming API
**Dane**: Tweets, sentiment, influencers

```python
import tweepy

client = tweepy.Client(bearer_token="YOUR_BEARER_TOKEN")

# Search tweets
tweets = client.search_recent_tweets(
    query="bitcoin -is:retweet lang:en",
    max_results=100,
    tweet_fields=["created_at", "public_metrics"]
)
```

| Plan | Cena/mies | Limit |
|------|-----------|-------|
| Free | $0 | 1.5K tweets/month |
| Basic | $100 | 10K tweets/month |
| Pro | $5000 | 1M tweets/month |
| Enterprise | Custom | Unlimited |

**⚠️ Uwaga**: Od 2023 Twitter API jest bardzo drogi!

### 13. Deribit API

**Typ**: REST / WebSocket
**Dane**: Options, futures, derivatives

```python
import requests

# Public endpoint (no auth needed)
url = "https://www.deribit.com/api/v2/public/get_index_price"
params = {"index_name": "btc_usd"}

response = requests.get(url, params=params).json()

# Options open interest
url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
params = {"currency": "BTC", "kind": "option"}

response = requests.get(url, params=params).json()
```

| Aspekt | Wartość |
|--------|---------|
| Public API | **FREE** |
| Private API | Requires account |

---

## 🔴 Premium/Enterprise API (Tier 3)

### 14. Bloomberg Terminal

**Dane**: Everything financial
**Koszt**: ~$20,000-$25,000/rok
**Uwagi**: Institutional standard, nie dla małych projektów

### 15. Refinitiv (ex-Reuters)

**Dane**: News, financial data
**Koszt**: Custom pricing ($$$$)
**Uwagi**: Enterprise grade

### 16. Quandl (Nasdaq)

**Dane**: Alternative data, financial
**Koszt**: $0 - $$$$ (zależnie od dataset)

```python
import quandl

quandl.ApiConfig.api_key = "YOUR_API_KEY"

# Free dataset
data = quandl.get("FRED/GDP")

# Premium datasets require subscription
```

---

## 📋 Quick Reference Table

| API | Kategoria | Koszt | Rate Limit | Priorytet |
|-----|-----------|-------|------------|-----------|
| yfinance | Market Data | FREE | ~2000/h | 🥇 |
| Alternative.me | Sentiment | FREE | Moderate | 🥇 |
| FRED | Macro | FREE | 120/min | 🥈 |
| GDELT | News | FREE* | N/A | 🥈 |
| NOAA | Alternative | FREE | Generous | 🥉 |
| GitHub | Dev Activity | FREE | 5000/h | 🥉 |
| Reddit | Social | FREE | 60/min | 🥉 |
| CoinGecko | Crypto | FREE* | 10-50/min | 🥉 |
| Glassnode | On-chain | $49+ | Varies | 💰 |
| CryptoQuant | On-chain | $29+ | Varies | 💰 |
| Santiment | Multi | $49+ | Varies | 💰 |
| Twitter/X | Social | $100+ | Varies | ⚠️ |
| Deribit | Derivatives | FREE | Generous | 💰 |

---

## 🛠️ Przykładowy Multi-API Client

```python
"""
multi_api_client.py - Unified interface for all data sources
"""

import yfinance as yf
import requests
from fredapi import Fred
from typing import Dict, Any
from datetime import datetime

class MultiAPIClient:
    def __init__(self, config: Dict[str, str]):
        self.fred = Fred(api_key=config.get('fred_api_key'))
        self.fear_greed_url = "https://api.alternative.me/fng/"
        
    def get_market_indices(self) -> Dict[str, float]:
        """Pobierz aktualne wartości indeksów rynkowych."""
        tickers = {
            'SPX': '^GSPC',
            'VIX': '^VIX',
            'DXY': 'DX-Y.NYB',
            'NASDAQ': '^IXIC',
            'GOLD': 'GC=F',
        }
        
        results = {}
        for name, symbol in tickers.items():
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='1d', interval='1h')
                if not data.empty:
                    results[name] = data['Close'].iloc[-1]
            except Exception as e:
                print(f"Error fetching {name}: {e}")
        
        return results
    
    def get_fear_greed(self) -> Dict[str, Any]:
        """Pobierz Fear & Greed Index."""
        try:
            response = requests.get(self.fear_greed_url)
            data = response.json()
            latest = data['data'][0]
            return {
                'value': int(latest['value']),
                'classification': latest['value_classification'],
                'timestamp': latest['timestamp']
            }
        except Exception as e:
            print(f"Error fetching Fear & Greed: {e}")
            return None
    
    def get_treasury_yields(self) -> Dict[str, float]:
        """Pobierz rentowności obligacji z FRED."""
        series = {
            '2Y': 'DGS2',
            '10Y': 'DGS10',
            '30Y': 'DGS30',
        }
        
        results = {}
        for name, code in series.items():
            try:
                data = self.fred.get_series(code)
                results[name] = data.iloc[-1]
            except Exception as e:
                print(f"Error fetching {name}: {e}")
        
        return results


# Użycie
if __name__ == "__main__":
    config = {
        'fred_api_key': 'YOUR_FRED_API_KEY',
    }
    
    client = MultiAPIClient(config)
    
    print("Market Indices:", client.get_market_indices())
    print("Fear & Greed:", client.get_fear_greed())
    print("Treasury Yields:", client.get_treasury_yields())
```

---

## 📝 Checklist Implementacji

### Faza 1 (Darmowe)
- [ ] yfinance: SPX, VIX, DXY, NASDAQ
- [ ] Alternative.me: Fear & Greed
- [ ] FRED API key registration
- [ ] Dodać do database schema

### Faza 2 (Opcjonalne darmowe)
- [ ] GitHub API: Bitcoin repos monitoring
- [ ] Reddit PRAW setup
- [ ] CoinGecko: dodatkowe metryki

### Faza 3 (Płatne)
- [ ] CryptoQuant trial
- [ ] Glassnode trial
- [ ] Deribit options data

---

*Dokument stworzony: 2025-12-24 | Autor: Claude Opus 4.5*

