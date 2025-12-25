-- Migration: 010_order_flow_imbalance
-- ==================================================
-- Tabela do przechowywania metryk Order Flow Imbalance z dYdX.
-- 
-- Order Flow Imbalance (OFI) to jedna z najbardziej predykcyjnych zmiennych
-- w handlu wysokofrequencyjnym. Bazuje na obserwacji, że nierównowaga między
-- wolumenem BUY i SELL jest wyprzedzającym wskaźnikiem ruchu ceny.
-- 
-- Metryki obliczane co godzinę dla każdego tickera.

CREATE TABLE IF NOT EXISTS dydx_order_flow_imbalance (
    timestamp TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    
    -- === Wolumeny ===
    buy_volume DECIMAL(30, 8) NOT NULL DEFAULT 0,
    sell_volume DECIMAL(30, 8) NOT NULL DEFAULT 0,
    total_volume DECIMAL(30, 8) NOT NULL DEFAULT 0,
    
    -- === Order Flow Imbalance ===
    order_flow_imbalance DECIMAL(10, 6) NOT NULL,  -- (buy_volume - sell_volume) / total_volume [-1, 1]
    buy_sell_ratio DECIMAL(10, 4),                  -- buy_count / sell_count
    
    -- === Liczby transakcji ===
    buy_count INTEGER NOT NULL DEFAULT 0,
    sell_count INTEGER NOT NULL DEFAULT 0,
    total_trades INTEGER NOT NULL DEFAULT 0,
    
    -- === Duże transakcje ===
    large_trade_threshold DECIMAL(30, 8),           -- Próg dla dużych transakcji (domyślnie 0.5 BTC)
    large_trade_volume DECIMAL(30, 8) DEFAULT 0,
    large_trade_count INTEGER DEFAULT 0,
    large_trade_ratio DECIMAL(10, 6),               -- large_trade_volume / total_volume
    
    -- === Whale transakcje ===
    whale_threshold DECIMAL(30, 8),                 -- Próg dla whale (domyślnie 5 BTC)
    whale_volume DECIMAL(30, 8) DEFAULT 0,
    whale_count INTEGER DEFAULT 0,
    whale_ratio DECIMAL(10, 6),                     -- whale_volume / total_volume
    
    -- === Ceny ===
    vwap DECIMAL(30, 8),                            -- Volume Weighted Average Price
    avg_price DECIMAL(30, 8),                       -- Średnia cena
    min_price DECIMAL(30, 8),                       -- Najniższa cena w oknie
    max_price DECIMAL(30, 8),                       -- Najwyższa cena w oknie
    price_range DECIMAL(30, 8),                     -- max_price - min_price
    price_range_pct DECIMAL(10, 6),                 -- (max_price - min_price) / avg_price * 100
    
    -- === Intensywność ===
    trades_per_minute DECIMAL(10, 4),               -- Średnia liczba transakcji na minutę
    volume_per_minute DECIMAL(30, 8),               -- Średni wolumen na minutę
    
    -- === Momentum ===
    imbalance_change_1h DECIMAL(10, 6),             -- Zmiana imbalance vs poprzednia godzina
    volume_change_1h DECIMAL(10, 6),                -- Zmiana wolumenu vs poprzednia godzina (%)
    price_change_1h DECIMAL(10, 6),                  -- Zmiana ceny vs poprzednia godzina (%)
    
    -- === Korelacja z OHLCV ===
    ohlcv_close_price DECIMAL(30, 8),               -- Cena zamknięcia z OHLCV (opcjonalne)
    vwap_deviation_pct DECIMAL(10, 6),               -- (vwap - ohlcv_close) / ohlcv_close * 100
    
    -- === Metadane ===
    calculation_window_minutes INTEGER DEFAULT 60,  -- Okno obliczeń (domyślnie 60 min)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (timestamp, ticker)
);

COMMENT ON TABLE dydx_order_flow_imbalance IS 
    'Metryki Order Flow Imbalance z dYdX - agregowane co godzinę dla każdego tickera';
COMMENT ON COLUMN dydx_order_flow_imbalance.timestamp IS 
    'Timestamp początku okna godzinowego (UTC)';
COMMENT ON COLUMN dydx_order_flow_imbalance.ticker IS 
    'Symbol rynku (np. BTC-USD, ETH-USD)';
COMMENT ON COLUMN dydx_order_flow_imbalance.order_flow_imbalance IS 
    'Główna metryka imbalance: (buy_volume - sell_volume) / total_volume, zakres [-1, 1]';
COMMENT ON COLUMN dydx_order_flow_imbalance.large_trade_threshold IS 
    'Próg dla dużych transakcji (domyślnie 0.5 BTC)';
COMMENT ON COLUMN dydx_order_flow_imbalance.whale_threshold IS 
    'Próg dla whale transakcji (domyślnie 5 BTC)';
COMMENT ON COLUMN dydx_order_flow_imbalance.vwap IS 
    'Volume Weighted Average Price - średnia cena ważona wolumenem';
COMMENT ON COLUMN dydx_order_flow_imbalance.vwap_deviation_pct IS 
    'Odchylenie VWAP od ceny zamknięcia OHLCV w procentach';

-- Indeksy
CREATE INDEX IF NOT EXISTS ix_dydx_order_flow_imbalance_timestamp 
    ON dydx_order_flow_imbalance (timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_dydx_order_flow_imbalance_ticker 
    ON dydx_order_flow_imbalance (ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_dydx_order_flow_imbalance_imbalance 
    ON dydx_order_flow_imbalance (order_flow_imbalance, timestamp DESC);

-- TimescaleDB hypertable (jeśli dostępne)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('dydx_order_flow_imbalance', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE, chunk_time_interval => INTERVAL '1 day');
    END IF;
END $$;

