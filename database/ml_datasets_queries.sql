-- =============================================================================
-- ML DATASETS QUERIES - Predykcja kierunku ruchu ceny BTC
-- =============================================================================
-- Autor: Claude Opus 4.5 + trends-sniffer
-- Data: 2025-12-24
-- Cel: 5 kwerend generujących datasety do trenowania modeli ML
--      do przewidywania wzrostu/spadku kursu BTC w ciągu następnej godziny
-- =============================================================================

-- =============================================================================
-- KWERENDA 1: ORDER FLOW IMBALANCE DATASET
-- =============================================================================
-- TEORIA: 
-- Order Flow Imbalance (OFI) to jedna z najbardziej predykcyjnych zmiennych
-- w handlu wysokofrequencyjnym. Bazuje na obserwacji, że nierównowaga między 
-- wolumenem BUY i SELL jest wyprzedzającym wskaźnikiem ruchu ceny.
-- 
-- HIPOTEZA TRADINGOWA:
-- Jeśli w ostatnich N minutach/godzinach wolumen zakupów znacząco przewyższa
-- wolumen sprzedaży na rynku perpetual (dYdX), to cena prawdopodobnie wzrośnie
-- w następnej godzinie, ponieważ:
-- 1. Agresywni kupujący (taker) wchodzą na rynek
-- 2. Market makers muszą podnieść ceny, aby zrównoważyć inventory risk
-- 3. Momentum traders podążają za przepływem
--
-- FEATURES:
-- - order_flow_imbalance: (buy_volume - sell_volume) / total_volume
-- - buy_sell_ratio: buy_count / sell_count
-- - large_trade_ratio: wolumen dużych transakcji / total volume
-- - trade_intensity: liczba transakcji / jednostka czasu
-- - volume_weighted_price: średnia cena ważona wolumenem
-- =============================================================================

WITH hourly_trades AS (
    SELECT 
        date_trunc('hour', effective_at) AS hour_start,
        date_trunc('hour', effective_at) + INTERVAL '1 hour' AS hour_end,
        
        -- Wolumeny
        SUM(CASE WHEN side = 'BUY' THEN size::float ELSE 0 END) AS buy_volume,
        SUM(CASE WHEN side = 'SELL' THEN size::float ELSE 0 END) AS sell_volume,
        SUM(size::float) AS total_volume,
        
        -- Liczby transakcji
        SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) AS buy_count,
        SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
        COUNT(*) AS total_trades,
        
        -- Duże transakcje (>0.5 BTC)
        SUM(CASE WHEN size::float > 0.5 THEN size::float ELSE 0 END) AS large_trade_volume,
        SUM(CASE WHEN size::float > 0.5 THEN 1 ELSE 0 END) AS large_trade_count,
        
        -- Whale trades (>5 BTC)
        SUM(CASE WHEN size::float > 5 THEN size::float ELSE 0 END) AS whale_volume,
        SUM(CASE WHEN size::float > 5 THEN 1 ELSE 0 END) AS whale_count,
        
        -- Ceny
        AVG(price::float) AS avg_price,
        MIN(price::float) AS min_price,
        MAX(price::float) AS max_price,
        SUM(size::float * price::float) / NULLIF(SUM(size::float), 0) AS vwap
        
    FROM dydx_perpetual_market_trades
    WHERE ticker = 'BTC-USD'
    GROUP BY date_trunc('hour', effective_at)
),
ohlcv_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        FIRST_VALUE(open) OVER (PARTITION BY date_trunc('hour', timestamp) ORDER BY timestamp) AS hour_open,
        MAX(high) AS hour_high,
        MIN(low) AS hour_low,
        LAST_VALUE(close) OVER (PARTITION BY date_trunc('hour', timestamp) ORDER BY timestamp 
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS hour_close,
        SUM(volume) AS hour_volume
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp), timestamp, open, close
),
ohlcv_agg AS (
    SELECT 
        hour_start,
        AVG(hour_open) AS open_price,
        MAX(hour_high) AS high_price,
        MIN(hour_low) AS low_price,
        AVG(hour_close) AS close_price,
        SUM(hour_volume) AS volume
    FROM ohlcv_hourly
    GROUP BY hour_start
),
target_labels AS (
    SELECT 
        hour_start,
        close_price,
        LEAD(close_price, 1) OVER (ORDER BY hour_start) AS next_hour_close,
        LEAD(high_price, 1) OVER (ORDER BY hour_start) AS next_hour_high,
        LEAD(low_price, 1) OVER (ORDER BY hour_start) AS next_hour_low
    FROM ohlcv_agg
)
SELECT 
    t.hour_start AS timestamp,
    
    -- === FEATURES: Order Flow ===
    t.buy_volume,
    t.sell_volume,
    t.total_volume,
    (t.buy_volume - t.sell_volume) / NULLIF(t.total_volume, 0) AS order_flow_imbalance,
    t.buy_count::float / NULLIF(t.sell_count, 0) AS buy_sell_ratio,
    t.total_trades AS trade_count,
    
    -- === FEATURES: Large Trades ===
    t.large_trade_volume / NULLIF(t.total_volume, 0) AS large_trade_ratio,
    t.large_trade_count,
    t.whale_volume / NULLIF(t.total_volume, 0) AS whale_trade_ratio,
    t.whale_count,
    
    -- === FEATURES: Price ===
    t.vwap,
    t.avg_price,
    o.close_price,
    (t.vwap - o.close_price) / NULLIF(o.close_price, 0) * 100 AS vwap_deviation_pct,
    (o.high_price - o.low_price) / NULLIF(o.close_price, 0) * 100 AS price_range_pct,
    
    -- === FEATURES: Volume ===
    o.volume AS binance_volume,
    t.total_volume / NULLIF(o.volume, 0) AS dydx_binance_volume_ratio,
    
    -- === TARGET: Następna godzina ===
    l.next_hour_close,
    (l.next_hour_close - l.close_price) / NULLIF(l.close_price, 0) * 100 AS next_hour_return_pct,
    CASE 
        WHEN l.next_hour_close > l.close_price THEN 1  -- wzrost
        WHEN l.next_hour_close < l.close_price THEN 0  -- spadek
        ELSE NULL  -- bez zmiany (odfiltruj)
    END AS target_direction,
    -- Siła ruchu (do regresji)
    (l.next_hour_high - l.close_price) / NULLIF(l.close_price, 0) * 100 AS max_upside_pct,
    (l.close_price - l.next_hour_low) / NULLIF(l.close_price, 0) * 100 AS max_downside_pct
    
FROM hourly_trades t
JOIN ohlcv_agg o ON t.hour_start = o.hour_start
JOIN target_labels l ON t.hour_start = l.hour_start
WHERE t.total_volume > 0
    AND l.next_hour_close IS NOT NULL
ORDER BY t.hour_start;


-- =============================================================================
-- KWERENDA 2: SENTIMENT MOMENTUM DATASET
-- =============================================================================
-- TEORIA:
-- Sentyment medialny ma istotny wpływ na rynek kryptowalut, szczególnie BTC.
-- GDELT (Global Database of Events, Language and Tone) zbiera dane z mediów
-- z całego świata i oblicza "tone" - wskaźnik nastrojów w artykułach.
--
-- HIPOTEZA TRADINGOWA:
-- 1. Gwałtowna zmiana sentymentu (momentum) wyprzedza ruch ceny
-- 2. Ekstremalnie negatywny sentyment często oznacza bottoms (contrarian)
-- 3. Nagły wzrost wolumenu artykułów o BTC sugeruje zwiększoną zmienność
-- 4. Rozbieżność między sentymentem a ceną może sygnalizować reversal
--
-- FEATURES:
-- - tone_ma: średnia krocząca sentymentu
-- - tone_momentum: zmiana sentymentu vs poprzedni okres
-- - tone_volatility: zmienność sentymentu
-- - volume_spike: czy wolumen artykułów jest znacząco wyższy niż zwykle
-- - sentiment_price_divergence: czy cena i sentyment idą w przeciwnych kierunkach
-- =============================================================================

WITH gdelt_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(tone) AS avg_tone,
        STDDEV(tone) AS tone_std,
        COUNT(*) AS article_count
    FROM gdelt_sentiment
    WHERE region = 'US'  -- główny rynek
    GROUP BY date_trunc('hour', timestamp)
),
gdelt_features AS (
    SELECT 
        hour_start,
        avg_tone,
        tone_std,
        article_count,
        
        -- Moving averages
        AVG(avg_tone) OVER (ORDER BY hour_start ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS tone_ma_6h,
        AVG(avg_tone) OVER (ORDER BY hour_start ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS tone_ma_24h,
        
        -- Momentum
        avg_tone - LAG(avg_tone, 1) OVER (ORDER BY hour_start) AS tone_change_1h,
        avg_tone - LAG(avg_tone, 6) OVER (ORDER BY hour_start) AS tone_change_6h,
        avg_tone - LAG(avg_tone, 24) OVER (ORDER BY hour_start) AS tone_change_24h,
        
        -- Volume z-score
        (article_count - AVG(article_count) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW)) 
        / NULLIF(STDDEV(article_count) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW), 0) AS volume_zscore,
        
        -- Ekstremalne wartości
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
        high_price,
        low_price,
        volume,
        
        -- Price momentum
        close_price - LAG(close_price, 1) OVER (ORDER BY hour_start) AS price_change_1h,
        (close_price - LAG(close_price, 1) OVER (ORDER BY hour_start)) 
            / NULLIF(LAG(close_price, 1) OVER (ORDER BY hour_start), 0) * 100 AS return_1h_pct,
        
        -- Target: następna godzina
        LEAD(close_price, 1) OVER (ORDER BY hour_start) AS next_hour_close
        
    FROM ohlcv_hourly
)
SELECT 
    g.hour_start AS timestamp,
    
    -- === FEATURES: Sentyment ===
    g.avg_tone,
    g.tone_std AS tone_volatility,
    g.tone_ma_6h,
    g.tone_ma_24h,
    g.tone_change_1h AS sentiment_momentum_1h,
    g.tone_change_6h AS sentiment_momentum_6h,
    g.tone_change_24h AS sentiment_momentum_24h,
    
    -- === FEATURES: Sentiment Extremes ===
    (g.avg_tone - g.tone_weekly_avg) / NULLIF(g.tone_weekly_std, 0) AS sentiment_zscore,
    CASE WHEN g.avg_tone < g.tone_weekly_avg - 2 * g.tone_weekly_std THEN 1 ELSE 0 END AS extreme_negative,
    CASE WHEN g.avg_tone > g.tone_weekly_avg + 2 * g.tone_weekly_std THEN 1 ELSE 0 END AS extreme_positive,
    
    -- === FEATURES: Volume anomalies ===
    g.article_count,
    g.volume_zscore AS article_volume_zscore,
    CASE WHEN g.volume_zscore > 2 THEN 1 ELSE 0 END AS volume_spike,
    
    -- === FEATURES: Price context ===
    p.close_price,
    p.return_1h_pct,
    (p.high_price - p.low_price) / NULLIF(p.close_price, 0) * 100 AS hourly_range_pct,
    
    -- === FEATURES: Divergence ===
    -- Dywergencja = sentyment i cena idą w przeciwnych kierunkach
    CASE 
        WHEN g.tone_change_6h > 0 AND p.return_1h_pct < 0 THEN 1  -- bullish divergence
        WHEN g.tone_change_6h < 0 AND p.return_1h_pct > 0 THEN -1 -- bearish divergence
        ELSE 0
    END AS sentiment_price_divergence,
    
    -- === TARGET ===
    p.next_hour_close,
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
ORDER BY g.hour_start;


-- =============================================================================
-- KWERENDA 3: FUNDING RATE & DERIVATIVES DATASET
-- =============================================================================
-- TEORIA:
-- Funding rate na rynkach perpetual jest kluczowym wskaźnikiem pozycjonowania
-- uczestników rynku. Positive funding = więcej long pozycji, negative = więcej short.
--
-- HIPOTEZA TRADINGOWA:
-- 1. Ekstremalnie wysoki funding rate często poprzedza short squeeze lub korektę
--    (too many longs = market is overleveraged)
-- 2. Ekstremalnie ujemny funding często poprzedza long squeeze lub odbicie
-- 3. Nagła zmiana funding rate sygnalizuje zmianę pozycjonowania smart money
-- 4. Funding rate vs cena: dywergencja może wskazywać na potencjalny reversal
--
-- FEATURES:
-- - funding_rate: bieżący funding rate
-- - funding_ma: średnia krocząca funding rate
-- - funding_momentum: zmiana funding rate
-- - funding_extremity: jak daleko od normy jest funding
-- - oi_change: zmiana open interest (jeśli dostępne)
-- =============================================================================

WITH funding_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(funding_rate) AS avg_funding,
        AVG(open_interest) AS avg_oi,
        AVG(price) AS avg_price
    FROM tickers
    WHERE symbol = 'BTC/USDC' 
        AND funding_rate IS NOT NULL
    GROUP BY date_trunc('hour', timestamp)
),
funding_features AS (
    SELECT 
        hour_start,
        avg_funding,
        avg_oi,
        avg_price,
        
        -- Moving averages
        AVG(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS funding_ma_8h,
        AVG(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS funding_ma_24h,
        
        -- Momentum
        avg_funding - LAG(avg_funding, 1) OVER (ORDER BY hour_start) AS funding_change_1h,
        avg_funding - LAG(avg_funding, 8) OVER (ORDER BY hour_start) AS funding_change_8h,
        
        -- Z-score (extremity)
        AVG(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW) AS funding_weekly_avg,
        STDDEV(avg_funding) OVER (ORDER BY hour_start ROWS BETWEEN 168 PRECEDING AND CURRENT ROW) AS funding_weekly_std,
        
        -- Open Interest changes
        avg_oi - LAG(avg_oi, 1) OVER (ORDER BY hour_start) AS oi_change_1h,
        (avg_oi - LAG(avg_oi, 24) OVER (ORDER BY hour_start)) / NULLIF(LAG(avg_oi, 24) OVER (ORDER BY hour_start), 0) * 100 AS oi_change_24h_pct
        
    FROM funding_hourly
),
ohlcv_hourly AS (
    SELECT 
        date_trunc('hour', timestamp) AS hour_start,
        AVG(close) AS close_price,
        MAX(high) - MIN(low) AS price_range,
        SUM(volume) AS volume,
        (AVG(close) - LAG(AVG(close), 1) OVER (ORDER BY date_trunc('hour', timestamp))) 
            / NULLIF(LAG(AVG(close), 1) OVER (ORDER BY date_trunc('hour', timestamp)), 0) * 100 AS return_1h,
        LEAD(AVG(close), 1) OVER (ORDER BY date_trunc('hour', timestamp)) AS next_hour_close
    FROM ohlcv
    WHERE symbol = 'BTC/USDC' AND timeframe = '1m'
    GROUP BY date_trunc('hour', timestamp)
)
SELECT 
    f.hour_start AS timestamp,
    
    -- === FEATURES: Funding Rate ===
    f.avg_funding * 10000 AS funding_rate_bps,  -- konwersja na basis points
    f.funding_ma_8h * 10000 AS funding_ma_8h_bps,
    f.funding_ma_24h * 10000 AS funding_ma_24h_bps,
    f.funding_change_1h * 10000 AS funding_momentum_1h_bps,
    f.funding_change_8h * 10000 AS funding_momentum_8h_bps,
    
    -- === FEATURES: Funding Extremity ===
    (f.avg_funding - f.funding_weekly_avg) / NULLIF(f.funding_weekly_std, 0) AS funding_zscore,
    CASE 
        WHEN f.avg_funding > 0.0003 THEN 2  -- bardzo wysoki (overleveraged longs)
        WHEN f.avg_funding > 0.0001 THEN 1  -- wysoki
        WHEN f.avg_funding < -0.0003 THEN -2  -- bardzo niski (overleveraged shorts)
        WHEN f.avg_funding < -0.0001 THEN -1  -- niski
        ELSE 0
    END AS funding_extremity_level,
    
    -- === FEATURES: Open Interest ===
    f.avg_oi,
    f.oi_change_1h,
    f.oi_change_24h_pct,
    
    -- === FEATURES: Price context ===
    o.close_price,
    o.return_1h AS price_return_1h_pct,
    o.price_range / NULLIF(o.close_price, 0) * 100 AS volatility_pct,
    o.volume,
    
    -- === FEATURES: Funding-Price Divergence ===
    -- Dywergencja = funding rośnie ale cena spada (lub odwrotnie)
    CASE 
        WHEN f.funding_change_8h > 0 AND o.return_1h < 0 THEN 1  -- longs building, price falling
        WHEN f.funding_change_8h < 0 AND o.return_1h > 0 THEN -1 -- shorts building, price rising
        ELSE 0
    END AS funding_price_divergence,
    
    -- === TARGET ===
    o.next_hour_close,
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
ORDER BY f.hour_start;


-- =============================================================================
-- KWERENDA 4: MULTI-TIMEFRAME PRICE ACTION DATASET
-- =============================================================================
-- TEORIA:
-- Price action analysis wykorzystuje historyczne ruchy cen do przewidywania
-- przyszłych ruchów. Kluczowe jest połączenie różnych perspektyw czasowych.
--
-- HIPOTEZA TRADINGOWA:
-- 1. Trend wyższego timeframe'u dominuje (np. 4h trend > 1h trend > 15m trend)
-- 2. Divergences między timeframe'ami sygnalizują potencjalne reversal points
-- 3. Volatility clustering - wysoka zmienność ma tendencję do kontynuacji
-- 4. Volume confirmation - ruchy cen z wysokim wolumenem są bardziej wiarygodne
-- 5. Mean reversion po ekstremalnych ruchach (especially in ranging markets)
--
-- FEATURES:
-- - returns różnych timeframe'ów (1h, 4h, 12h, 24h)
-- - volatility measures
-- - momentum indicators (ROC, momentum)
-- - volume profile
-- - trend alignment score
-- =============================================================================

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
        open,
        high,
        low,
        close,
        volume,
        
        -- Returns różnych timeframe'ów
        (close - LAG(close, 1) OVER w) / NULLIF(LAG(close, 1) OVER w, 0) * 100 AS return_1h,
        (close - LAG(close, 4) OVER w) / NULLIF(LAG(close, 4) OVER w, 0) * 100 AS return_4h,
        (close - LAG(close, 12) OVER w) / NULLIF(LAG(close, 12) OVER w, 0) * 100 AS return_12h,
        (close - LAG(close, 24) OVER w) / NULLIF(LAG(close, 24) OVER w, 0) * 100 AS return_24h,
        
        -- Momentum (Rate of Change)
        (close - LAG(close, 6) OVER w) / NULLIF(LAG(close, 6) OVER w, 0) * 100 AS roc_6h,
        
        -- Volatility (ATR proxy - range / close)
        (high - low) / NULLIF(close, 0) * 100 AS hourly_volatility,
        AVG((high - low) / NULLIF(close, 0) * 100) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS volatility_24h_avg,
        
        -- Volume analysis
        volume / NULLIF(AVG(volume) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW), 0) AS volume_ratio,
        
        -- Price position w range
        (close - MIN(low) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW)) 
        / NULLIF(MAX(high) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) 
        - MIN(low) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW), 0) * 100 AS price_position_24h,
        
        -- Moving averages
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS ma_8h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) AS ma_24h,
        AVG(close) OVER (ORDER BY hour ROWS BETWEEN 72 PRECEDING AND CURRENT ROW) AS ma_72h,
        
        -- Higher highs / lower lows (trend structure)
        high - LAG(high, 1) OVER w AS hh_change,
        low - LAG(low, 1) OVER w AS ll_change,
        
        -- Target
        LEAD(close, 1) OVER w AS next_hour_close
        
    FROM base_ohlcv
    WINDOW w AS (ORDER BY hour)
)
SELECT 
    hour AS timestamp,
    
    -- === FEATURES: Multi-timeframe returns ===
    return_1h,
    return_4h,
    return_12h,
    return_24h,
    roc_6h AS momentum_6h,
    
    -- === FEATURES: Trend alignment ===
    close,
    CASE WHEN close > ma_8h THEN 1 ELSE 0 END AS above_ma_8h,
    CASE WHEN close > ma_24h THEN 1 ELSE 0 END AS above_ma_24h,
    CASE WHEN close > ma_72h THEN 1 ELSE 0 END AS above_ma_72h,
    -- Trend alignment score: suma pozycji powyżej MA
    (CASE WHEN close > ma_8h THEN 1 ELSE 0 END +
     CASE WHEN close > ma_24h THEN 1 ELSE 0 END +
     CASE WHEN close > ma_72h THEN 1 ELSE 0 END) AS trend_alignment_score,
    
    -- === FEATURES: MA crossovers ===
    (ma_8h - ma_24h) / NULLIF(ma_24h, 0) * 100 AS ma_spread_8_24,
    (ma_24h - ma_72h) / NULLIF(ma_72h, 0) * 100 AS ma_spread_24_72,
    
    -- === FEATURES: Volatility ===
    hourly_volatility,
    volatility_24h_avg,
    hourly_volatility / NULLIF(volatility_24h_avg, 0) AS volatility_ratio,
    
    -- === FEATURES: Volume ===
    volume,
    volume_ratio,
    CASE WHEN volume_ratio > 1.5 THEN 1 ELSE 0 END AS high_volume_flag,
    
    -- === FEATURES: Price structure ===
    price_position_24h,
    CASE WHEN hh_change > 0 THEN 1 ELSE 0 END AS higher_high,
    CASE WHEN ll_change > 0 THEN 1 ELSE 0 END AS higher_low,
    
    -- === FEATURES: Mean reversion signals ===
    CASE WHEN price_position_24h > 90 THEN 1 ELSE 0 END AS overbought_24h,
    CASE WHEN price_position_24h < 10 THEN 1 ELSE 0 END AS oversold_24h,
    
    -- === TARGET ===
    next_hour_close,
    (next_hour_close - close) / NULLIF(close, 0) * 100 AS next_hour_return_pct,
    CASE 
        WHEN next_hour_close > close THEN 1
        WHEN next_hour_close < close THEN 0
        ELSE NULL
    END AS target_direction

FROM price_features
WHERE return_24h IS NOT NULL
    AND next_hour_close IS NOT NULL
ORDER BY hour;


-- =============================================================================
-- KWERENDA 5: COMBINED MULTI-SOURCE DATASET (MASTER QUERY)
-- =============================================================================
-- TEORIA:
-- Najlepsze modele ML wykorzystują dane z wielu źródeł jednocześnie.
-- Ta kwerenda łączy wszystkie dostępne sygnały w jeden kompleksowy dataset.
--
-- HIPOTEZA TRADINGOWA:
-- 1. Confluence of signals - gdy wiele wskaźników wskazuje ten sam kierunek,
--    prawdopodobieństwo sukcesu jest wyższe
-- 2. Każde źródło danych wnosi unikalne informacje:
--    - OHLCV: technical/price action
--    - Order flow: market microstructure
--    - Sentiment: behavioral/psychological
--    - Funding: derivatives positioning
-- 3. Feature importance może być różna w różnych warunkach rynkowych
--
-- FEATURES:
-- - Wszystkie najważniejsze features z poprzednich kwerend
-- - Syntetyczne features łączące wiele źródeł
-- - Time-based features (godzina, dzień tygodnia)
-- =============================================================================

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
        hour,
        close,
        volume,
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
    FROM gdelt_sentiment
    WHERE region = 'US'
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
    
    -- === TIME FEATURES ===
    EXTRACT(HOUR FROM p.hour) AS hour_of_day,
    EXTRACT(DOW FROM p.hour) AS day_of_week,
    CASE WHEN EXTRACT(DOW FROM p.hour) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,
    
    -- === PRICE FEATURES ===
    p.close AS price,
    p.return_1h,
    p.return_4h,
    p.return_24h,
    p.volatility,
    p.volume AS binance_volume,
    p.volume_ratio,
    (p.close - p.ma_8h) / NULLIF(p.ma_8h, 0) * 100 AS price_ma_8h_deviation,
    (p.close - p.ma_24h) / NULLIF(p.ma_24h, 0) * 100 AS price_ma_24h_deviation,
    CASE WHEN p.close > p.ma_8h AND p.ma_8h > p.ma_24h THEN 1
         WHEN p.close < p.ma_8h AND p.ma_8h < p.ma_24h THEN -1
         ELSE 0 END AS trend_direction,
    
    -- === ORDER FLOW FEATURES ===
    d.buy_volume,
    d.sell_volume,
    (d.buy_volume - d.sell_volume) / NULLIF(d.buy_volume + d.sell_volume, 0) AS order_flow_imbalance,
    d.buy_volume / NULLIF(d.sell_volume, 0) AS buy_sell_ratio,
    d.trade_count AS dydx_trades,
    d.large_trade_volume / NULLIF(d.buy_volume + d.sell_volume, 0) AS large_trade_ratio,
    
    -- === SENTIMENT FEATURES ===
    g.avg_tone AS sentiment_tone,
    g.article_count,
    LAG(g.avg_tone, 1) OVER (ORDER BY p.hour) AS sentiment_tone_lag1h,
    g.avg_tone - LAG(g.avg_tone, 1) OVER (ORDER BY p.hour) AS sentiment_momentum,
    
    -- === FUNDING FEATURES ===
    f.avg_funding * 10000 AS funding_rate_bps,
    f.avg_oi AS open_interest,
    f.avg_funding - LAG(f.avg_funding, 1) OVER (ORDER BY p.hour) AS funding_change,
    
    -- === COMPOSITE FEATURES ===
    -- Bullish confluence: order flow + sentiment + trend
    (CASE WHEN (d.buy_volume - d.sell_volume) / NULLIF(d.buy_volume + d.sell_volume, 0) > 0.1 THEN 1 ELSE 0 END +
     CASE WHEN g.avg_tone > 0 THEN 1 ELSE 0 END +
     CASE WHEN p.close > p.ma_8h THEN 1 ELSE 0 END) AS bullish_confluence_score,
    
    -- Bearish confluence
    (CASE WHEN (d.buy_volume - d.sell_volume) / NULLIF(d.buy_volume + d.sell_volume, 0) < -0.1 THEN 1 ELSE 0 END +
     CASE WHEN g.avg_tone < 0 THEN 1 ELSE 0 END +
     CASE WHEN p.close < p.ma_8h THEN 1 ELSE 0 END) AS bearish_confluence_score,
    
    -- === TARGET ===
    p.next_hour_close,
    (p.next_hour_close - p.close) / NULLIF(p.close, 0) * 100 AS next_hour_return_pct,
    CASE 
        WHEN p.next_hour_close > p.close THEN 1
        WHEN p.next_hour_close < p.close THEN 0
        ELSE NULL
    END AS target_direction

FROM price_features p
LEFT JOIN dydx_hourly d ON p.hour = d.hour
LEFT JOIN gdelt_hourly g ON p.hour = g.hour
LEFT JOIN funding_hourly f ON p.hour = f.hour
WHERE p.return_24h IS NOT NULL
    AND p.next_hour_close IS NOT NULL
ORDER BY p.hour;

