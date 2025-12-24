#!/usr/bin/env python3
"""
Export ML Datasets
==================
Skrypt do eksportowania datasetów dla modeli ML przewidujących kierunek ruchu BTC.

Autor: Claude Opus 4.5 + trends-sniffer
Data: 2025-12-24

Użycie:
    python scripts/export_ml_datasets.py --dataset all --output ./data/ml/
    python scripts/export_ml_datasets.py --dataset order_flow --format parquet
    python scripts/export_ml_datasets.py --dataset combined --start-date 2025-12-01

Dostępne datasety:
    1. order_flow      - Order Flow Imbalance Dataset
    2. sentiment       - Sentiment Momentum Dataset
    3. funding         - Funding Rate & Derivatives Dataset
    4. price_action    - Multi-Timeframe Price Action Dataset
    5. combined        - Combined Multi-Source Dataset (Master Query)
    all                - Eksportuj wszystkie datasety
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


# Załaduj zmienne środowiskowe
load_dotenv()


# ============================================================================
# KWERENDY SQL
# ============================================================================

QUERY_ORDER_FLOW = """
-- ORDER FLOW IMBALANCE DATASET
WITH hourly_trades AS (
    SELECT 
        date_trunc('hour', effective_at) AS hour_start,
        SUM(CASE WHEN side = 'BUY' THEN size::float ELSE 0 END) AS buy_volume,
        SUM(CASE WHEN side = 'SELL' THEN size::float ELSE 0 END) AS sell_volume,
        SUM(size::float) AS total_volume,
        SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) AS buy_count,
        SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
        COUNT(*) AS total_trades,
        SUM(CASE WHEN size::float > 0.5 THEN size::float ELSE 0 END) AS large_trade_volume,
        SUM(CASE WHEN size::float > 0.5 THEN 1 ELSE 0 END) AS large_trade_count,
        SUM(CASE WHEN size::float > 5 THEN size::float ELSE 0 END) AS whale_volume,
        SUM(CASE WHEN size::float > 5 THEN 1 ELSE 0 END) AS whale_count,
        AVG(price::float) AS avg_price,
        SUM(size::float * price::float) / NULLIF(SUM(size::float), 0) AS vwap
    FROM dydx_perpetual_market_trades
    WHERE ticker = 'BTC-USD'
    GROUP BY date_trunc('hour', effective_at)
),
ohlcv_agg AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(close) AS close_price,
        MAX(high) AS high_price,
        MIN(low) AS low_price,
        SUM(volume) AS volume
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp)
),
target_labels AS (
    SELECT 
        hour_start,
        close_price,
        LEAD(close_price, 1) OVER (ORDER BY hour_start) AS next_hour_close
    FROM ohlcv_agg
)
SELECT 
    t.hour_start AS timestamp,
    t.buy_volume,
    t.sell_volume,
    t.total_volume,
    (t.buy_volume - t.sell_volume) / NULLIF(t.total_volume, 0) AS order_flow_imbalance,
    t.buy_count::float / NULLIF(t.sell_count, 0) AS buy_sell_ratio,
    t.total_trades AS trade_count,
    t.large_trade_volume / NULLIF(t.total_volume, 0) AS large_trade_ratio,
    t.large_trade_count,
    t.whale_volume / NULLIF(t.total_volume, 0) AS whale_trade_ratio,
    t.whale_count,
    t.vwap,
    o.close_price,
    (t.vwap - o.close_price) / NULLIF(o.close_price, 0) * 100 AS vwap_deviation_pct,
    (o.high_price - o.low_price) / NULLIF(o.close_price, 0) * 100 AS price_range_pct,
    o.volume AS binance_volume,
    (l.next_hour_close - l.close_price) / NULLIF(l.close_price, 0) * 100 AS next_hour_return_pct,
    CASE 
        WHEN l.next_hour_close > l.close_price THEN 1
        WHEN l.next_hour_close < l.close_price THEN 0
        ELSE NULL
    END AS target_direction
FROM hourly_trades t
JOIN ohlcv_agg o ON t.hour_start = o.hour_start
JOIN target_labels l ON t.hour_start = l.hour_start
WHERE t.total_volume > 0
    AND l.next_hour_close IS NOT NULL
ORDER BY t.hour_start
"""

QUERY_SENTIMENT = """
-- SENTIMENT MOMENTUM DATASET
WITH gdelt_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(tone) AS avg_tone,
        STDDEV(tone) AS tone_std,
        COUNT(*) AS article_count
    FROM gdelt_sentiment
    WHERE region = 'US'
    GROUP BY date_trunc('hour', timestamp)
),
gdelt_features AS (
    SELECT 
        hour_start,
        avg_tone,
        tone_std,
        article_count,
        AVG(avg_tone) OVER (ORDER BY hour_start ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS tone_ma_6h,
        AVG(avg_tone) OVER (ORDER BY hour_start ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS tone_ma_24h,
        avg_tone - LAG(avg_tone, 1) OVER (ORDER BY hour_start) AS tone_change_1h,
        avg_tone - LAG(avg_tone, 6) OVER (ORDER BY hour_start) AS tone_change_6h,
        (article_count - AVG(article_count) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW)) 
        / NULLIF(STDDEV(article_count) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW), 0) AS volume_zscore,
        AVG(avg_tone) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW) AS tone_weekly_avg,
        STDDEV(avg_tone) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW) AS tone_weekly_std
    FROM gdelt_hourly
),
ohlcv_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(close) AS close_price,
        MAX(high) AS high_price,
        MIN(low) AS low_price,
        SUM(volume) AS volume
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp)
),
price_features AS (
    SELECT 
        hour_start,
        close_price,
        (close_price - LAG(close_price, 1) OVER (ORDER BY hour_start)) 
            / NULLIF(LAG(close_price, 1) OVER (ORDER BY hour_start), 0) * 100 AS return_1h_pct,
        LEAD(close_price, 1) OVER (ORDER BY hour_start) AS next_hour_close
    FROM ohlcv_hourly
)
SELECT 
    g.hour_start AS timestamp,
    g.avg_tone,
    g.tone_std AS tone_volatility,
    g.tone_ma_6h,
    g.tone_ma_24h,
    g.tone_change_1h AS sentiment_momentum_1h,
    g.tone_change_6h AS sentiment_momentum_6h,
    (g.avg_tone - g.tone_weekly_avg) / NULLIF(g.tone_weekly_std, 0) AS sentiment_zscore,
    g.article_count,
    g.volume_zscore AS article_volume_zscore,
    p.close_price,
    p.return_1h_pct,
    (p.next_hour_close - p.close_price) / NULLIF(p.close_price, 0) * 100 AS next_hour_return_pct,
    CASE 
        WHEN p.next_hour_close > p.close_price THEN 1
        WHEN p.next_hour_close < p.close_price THEN 0
        ELSE NULL
    END AS target_direction
FROM gdelt_features g
JOIN price_features p ON g.hour_start = p.hour_start
WHERE g.avg_tone IS NOT NULL
    AND p.next_hour_close IS NOT NULL
ORDER BY g.hour_start
"""

QUERY_FUNDING = """
-- FUNDING RATE & DERIVATIVES DATASET
WITH funding_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(funding_rate) AS avg_funding,
        AVG(open_interest) AS avg_oi,
        AVG(price) AS avg_price
    FROM tickers
    WHERE symbol = 'BTC/USDC' AND funding_rate IS NOT NULL
    GROUP BY date_trunc('hour', timestamp)
),
funding_features AS (
    SELECT 
        hour_start,
        avg_funding,
        avg_oi,
        avg_price,
        AVG(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS funding_ma_8h,
        AVG(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS funding_ma_24h,
        avg_funding - LAG(avg_funding, 1) OVER (ORDER BY hour_start) AS funding_change_1h,
        avg_funding - LAG(avg_funding, 8) OVER (ORDER BY hour_start) AS funding_change_8h,
        AVG(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW) AS funding_weekly_avg,
        STDDEV(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW) AS funding_weekly_std,
        avg_oi - LAG(avg_oi, 1) OVER (ORDER BY hour_start) AS oi_change_1h
    FROM funding_hourly
),
ohlcv_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(close) AS close_price,
        MAX(high) - MIN(low) AS price_range,
        SUM(volume) AS volume,
        LEAD(AVG(close), 1) OVER (ORDER BY date_trunc('hour', timestamp)) AS next_hour_close
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp)
)
SELECT 
    f.hour_start AS timestamp,
    f.avg_funding * 10000 AS funding_rate_bps,
    f.funding_ma_8h * 10000 AS funding_ma_8h_bps,
    f.funding_ma_24h * 10000 AS funding_ma_24h_bps,
    f.funding_change_1h * 10000 AS funding_momentum_1h_bps,
    f.funding_change_8h * 10000 AS funding_momentum_8h_bps,
    (f.avg_funding - f.funding_weekly_avg) / NULLIF(f.funding_weekly_std, 0) AS funding_zscore,
    f.avg_oi,
    f.oi_change_1h,
    o.close_price,
    o.price_range / NULLIF(o.close_price, 0) * 100 AS volatility_pct,
    o.volume,
    (o.next_hour_close - o.close_price) / NULLIF(o.close_price, 0) * 100 AS next_hour_return_pct,
    CASE 
        WHEN o.next_hour_close > o.close_price THEN 1
        WHEN o.next_hour_close < o.close_price THEN 0
        ELSE NULL
    END AS target_direction
FROM funding_features f
JOIN ohlcv_hourly o ON f.hour_start = o.hour_start
WHERE f.avg_funding IS NOT NULL
    AND o.next_hour_close IS NOT NULL
ORDER BY f.hour_start
"""

QUERY_PRICE_ACTION = """
-- MULTI-TIMEFRAME PRICE ACTION DATASET
WITH base_ohlcv AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour,
        AVG(open) AS open,
        MAX(high) AS high,
        MIN(low) AS low,
        AVG(close) AS close,
        SUM(volume) AS volume
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp)
),
price_features AS (
    SELECT 
        hour,
        open, high, low, close, volume,
        (close - LAG(close, 1) OVER w) / NULLIF(LAG(close, 1) OVER w, 0) * 100 AS return_1h,
        (close - LAG(close, 4) OVER w) / NULLIF(LAG(close, 4) OVER w, 0) * 100 AS return_4h,
        (close - LAG(close, 12) OVER w) / NULLIF(LAG(close, 12) OVER w, 0) * 100 AS return_12h,
        (close - LAG(close, 24) OVER w) / NULLIF(LAG(close, 24) OVER w, 0) * 100 AS return_24h,
        (close - LAG(close, 6) OVER w) / NULLIF(LAG(close, 6) OVER w, 0) * 100 AS roc_6h,
        (high - low) / NULLIF(close, 0) * 100 AS hourly_volatility,
        AVG((high - low) / NULLIF(close, 0) * 100) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS volatility_24h_avg,
        volume / NULLIF(AVG(volume) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW), 0) AS volume_ratio,
        (close - MIN(low) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW)) 
        / NULLIF(MAX(high) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) 
        - MIN(low) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW), 0) * 100 AS price_position_24h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS ma_8h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS ma_24h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 72 PRECEDING AND CURRENT ROW) AS ma_72h,
        LEAD(close, 1) OVER w AS next_hour_close
    FROM base_ohlcv
    WINDOW w AS (ORDER BY hour)
)
SELECT 
    hour AS timestamp,
    return_1h, return_4h, return_12h, return_24h,
    roc_6h AS momentum_6h,
    close,
    CASE WHEN close > ma_8h THEN 1 ELSE 0 END AS above_ma_8h,
    CASE WHEN close > ma_24h THEN 1 ELSE 0 END AS above_ma_24h,
    CASE WHEN close > ma_72h THEN 1 ELSE 0 END AS above_ma_72h,
    (CASE WHEN close > ma_8h THEN 1 ELSE 0 END +
     CASE WHEN close > ma_24h THEN 1 ELSE 0 END +
     CASE WHEN close > ma_72h THEN 1 ELSE 0 END) AS trend_alignment_score,
    (ma_8h - ma_24h) / NULLIF(ma_24h, 0) * 100 AS ma_spread_8_24,
    (ma_24h - ma_72h) / NULLIF(ma_72h, 0) * 100 AS ma_spread_24_72,
    hourly_volatility, volatility_24h_avg,
    hourly_volatility / NULLIF(volatility_24h_avg, 0) AS volatility_ratio,
    volume, volume_ratio,
    price_position_24h,
    (next_hour_close - close) / NULLIF(close, 0) * 100 AS next_hour_return_pct,
    CASE WHEN next_hour_close > close THEN 1 ELSE 0 END AS target_direction
FROM price_features
WHERE return_24h IS NOT NULL AND next_hour_close IS NOT NULL
ORDER BY hour
"""

QUERY_COMBINED = """
-- COMBINED MULTI-SOURCE DATASET
WITH ohlcv_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour,
        AVG(open) AS open,
        MAX(high) AS high,
        MIN(low) AS low,
        AVG(close) AS close,
        SUM(volume) AS volume
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp)
),
price_features AS (
    SELECT 
        hour, close, volume,
        (high - low) / NULLIF(close, 0) * 100 AS volatility,
        (close - LAG(close, 1) OVER w) / NULLIF(LAG(close, 1) OVER w, 0) * 100 AS return_1h,
        (close - LAG(close, 4) OVER w) / NULLIF(LAG(close, 4) OVER w, 0) * 100 AS return_4h,
        (close - LAG(close, 24) OVER w) / NULLIF(LAG(close, 24) OVER w, 0) * 100 AS return_24h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS ma_8h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS ma_24h,
        volume / NULLIF(AVG(volume) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW), 0) AS volume_ratio,
        LEAD(close, 1) OVER w AS next_hour_close
    FROM ohlcv_hourly
    WINDOW w AS (ORDER BY hour)
),
dydx_hourly AS (
    SELECT 
        date_trunc('hour', effective_at) AS hour,
        SUM(CASE WHEN side = 'BUY' THEN size::float ELSE 0 END) AS buy_volume,
        SUM(CASE WHEN side = 'SELL' THEN size::float ELSE 0 END) AS sell_volume,
        COUNT(*) AS trade_count,
        SUM(CASE WHEN size::float > 0.5 THEN size::float ELSE 0 END) AS large_trade_volume
    FROM dydx_perpetual_market_trades
    WHERE ticker = 'BTC-USD'
    GROUP BY date_trunc('hour', effective_at)
),
gdelt_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour,
        AVG(tone) AS avg_tone,
        COUNT(*) AS article_count
    FROM gdelt_sentiment WHERE region = 'US'
    GROUP BY date_trunc('hour', timestamp)
),
funding_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour,
        AVG(funding_rate) AS avg_funding,
        AVG(open_interest) AS avg_oi
    FROM tickers
    WHERE symbol = 'BTC/USDC' AND funding_rate IS NOT NULL
    GROUP BY date_trunc('hour', timestamp)
)
SELECT 
    p.hour AS timestamp,
    EXTRACT(HOUR FROM p.hour) AS hour_of_day,
    EXTRACT(DOW FROM p.hour) AS day_of_week,
    CASE WHEN EXTRACT(DOW FROM p.hour) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,
    p.close AS price, p.return_1h, p.return_4h, p.return_24h,
    p.volatility, p.volume AS binance_volume, p.volume_ratio,
    (p.close - p.ma_8h) / NULLIF(p.ma_8h, 0) * 100 AS price_ma_8h_deviation,
    (p.close - p.ma_24h) / NULLIF(p.ma_24h, 0) * 100 AS price_ma_24h_deviation,
    d.buy_volume, d.sell_volume,
    (d.buy_volume - d.sell_volume) / NULLIF(d.buy_volume + d.sell_volume, 0) AS order_flow_imbalance,
    d.buy_volume / NULLIF(d.sell_volume, 0) AS buy_sell_ratio,
    d.trade_count AS dydx_trades,
    d.large_trade_volume / NULLIF(d.buy_volume + d.sell_volume, 0) AS large_trade_ratio,
    g.avg_tone AS sentiment_tone, g.article_count,
    g.avg_tone - LAG(g.avg_tone, 1) OVER (ORDER BY p.hour) AS sentiment_momentum,
    f.avg_funding * 10000 AS funding_rate_bps, f.avg_oi AS open_interest,
    (CASE WHEN (d.buy_volume - d.sell_volume) / NULLIF(d.buy_volume + d.sell_volume, 0) > 0.1 THEN 1 ELSE 0 END +
     CASE WHEN g.avg_tone > 0 THEN 1 ELSE 0 END +
     CASE WHEN p.close > p.ma_8h THEN 1 ELSE 0 END) AS bullish_confluence_score,
    (CASE WHEN (d.buy_volume - d.sell_volume) / NULLIF(d.buy_volume + d.sell_volume, 0) < -0.1 THEN 1 ELSE 0 END +
     CASE WHEN g.avg_tone < 0 THEN 1 ELSE 0 END +
     CASE WHEN p.close < p.ma_8h THEN 1 ELSE 0 END) AS bearish_confluence_score,
    (p.next_hour_close - p.close) / NULLIF(p.close, 0) * 100 AS next_hour_return_pct,
    CASE WHEN p.next_hour_close > p.close THEN 1 ELSE 0 END AS target_direction
FROM price_features p
LEFT JOIN dydx_hourly d ON p.hour = d.hour
LEFT JOIN gdelt_hourly g ON p.hour = g.hour
LEFT JOIN funding_hourly f ON p.hour = f.hour
WHERE p.return_24h IS NOT NULL AND p.next_hour_close IS NOT NULL
ORDER BY p.hour
"""


# ============================================================================
# GŁÓWNA LOGIKA
# ============================================================================

DATASETS = {
    'order_flow': ('Order Flow Imbalance Dataset', QUERY_ORDER_FLOW),
    'sentiment': ('Sentiment Momentum Dataset', QUERY_SENTIMENT),
    'funding': ('Funding Rate & Derivatives Dataset', QUERY_FUNDING),
    'price_action': ('Multi-Timeframe Price Action Dataset', QUERY_PRICE_ACTION),
    'combined': ('Combined Multi-Source Dataset', QUERY_COMBINED),
}


def get_db_connection():
    """Pobiera połączenie z bazą danych."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("Brak DATABASE_URL w .env")
    return psycopg2.connect(database_url)


def export_dataset(name: str, output_dir: Path, format: str = 'csv') -> Path:
    """Eksportuje pojedynczy dataset."""
    if name not in DATASETS:
        raise ValueError(f"Nieznany dataset: {name}. Dostępne: {list(DATASETS.keys())}")
    
    title, query = DATASETS[name]
    print(f"\n📊 Eksportuję: {title}")
    
    conn = get_db_connection()
    try:
        df = pd.read_sql(query, conn)
        print(f"   Pobrano {len(df)} rekordów")
        
        if df.empty:
            print(f"   ⚠️  Brak danych do eksportu!")
            return None
        
        # Statystyki
        if 'target_direction' in df.columns:
            target_dist = df['target_direction'].value_counts(normalize=True)
            print(f"   Rozkład target: UP={target_dist.get(1, 0):.2%}, DOWN={target_dist.get(0, 0):.2%}")
        
        # Zapisz do pliku
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'parquet':
            output_path = output_dir / f"ml_dataset_{name}_{timestamp}.parquet"
            df.to_parquet(output_path, index=False)
        else:
            output_path = output_dir / f"ml_dataset_{name}_{timestamp}.csv"
            df.to_csv(output_path, index=False)
        
        print(f"   ✅ Zapisano: {output_path}")
        return output_path
        
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Eksport datasetów ML dla predykcji kierunku BTC'
    )
    parser.add_argument(
        '--dataset', '-d',
        choices=list(DATASETS.keys()) + ['all'],
        default='all',
        help='Dataset do eksportu (domyślnie: all)'
    )
    parser.add_argument(
        '--output', '-o',
        default='./data/ml',
        help='Katalog wyjściowy (domyślnie: ./data/ml)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['csv', 'parquet'],
        default='csv',
        help='Format pliku (domyślnie: csv)'
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    
    print("=" * 60)
    print("🤖 ML DATASETS EXPORT - trends-sniffer")
    print("=" * 60)
    
    if args.dataset == 'all':
        datasets_to_export = list(DATASETS.keys())
    else:
        datasets_to_export = [args.dataset]
    
    exported_files = []
    for name in datasets_to_export:
        try:
            path = export_dataset(name, output_dir, args.format)
            if path:
                exported_files.append(path)
        except Exception as e:
            print(f"   ❌ Błąd: {e}")
    
    print("\n" + "=" * 60)
    print(f"📁 Wyeksportowano {len(exported_files)} datasetów do {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()

