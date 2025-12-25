-- Migration: 007_rename_tables_with_prefixes
-- ==================================================
-- Zmiana nazw tabel aby miały prefix wskazujący źródło danych.
-- 
-- Zmiany:
-- - top_trader_alerts → dydx_top_trader_alerts (dYdX)
-- - sentiment_propagation → google_trends_sentiment_propagation (Google Trends)

-- ============================================================================
-- RENAME: top_trader_alerts → dydx_top_trader_alerts
-- ============================================================================

-- Zmień nazwę tabeli
ALTER TABLE IF EXISTS top_trader_alerts 
    RENAME TO dydx_top_trader_alerts;

-- Zmień nazwy indeksów
DO $$
BEGIN
    -- Indeksy timestamp
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_top_trader_alerts_timestamp') THEN
        ALTER INDEX ix_top_trader_alerts_timestamp 
            RENAME TO ix_dydx_top_trader_alerts_timestamp;
    END IF;
    
    -- Indeks trader
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_top_trader_alerts_trader') THEN
        ALTER INDEX ix_top_trader_alerts_trader 
            RENAME TO ix_dydx_top_trader_alerts_trader;
    END IF;
    
    -- Indeks type
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_top_trader_alerts_type') THEN
        ALTER INDEX ix_top_trader_alerts_type 
            RENAME TO ix_dydx_top_trader_alerts_type;
    END IF;
    
    -- Indeks unread
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_top_trader_alerts_unread') THEN
        ALTER INDEX ix_top_trader_alerts_unread 
            RENAME TO ix_dydx_top_trader_alerts_unread;
    END IF;
    
    -- Indeks ticker
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_top_trader_alerts_ticker') THEN
        ALTER INDEX ix_top_trader_alerts_ticker 
            RENAME TO ix_dydx_top_trader_alerts_ticker;
    END IF;
END $$;

-- Zmień nazwę view
DROP VIEW IF EXISTS top_trader_alerts_summary;
CREATE OR REPLACE VIEW dydx_top_trader_alerts_summary AS
SELECT 
    DATE_TRUNC('hour', alert_timestamp) AS hour,
    alert_type,
    alert_severity,
    COUNT(*) AS alert_count,
    COUNT(DISTINCT trader_address || ':' || subaccount_number) AS unique_traders,
    SUM(volume_usd) AS total_volume_usd,
    AVG(volume_usd) AS avg_volume_usd,
    MAX(volume_usd) AS max_volume_usd
FROM dydx_top_trader_alerts
GROUP BY 
    DATE_TRUNC('hour', alert_timestamp),
    alert_type,
    alert_severity
ORDER BY hour DESC, alert_severity DESC, alert_count DESC;

COMMENT ON VIEW dydx_top_trader_alerts_summary IS 
    'Agregowany widok alertów top traderów dYdX pogrupowany po godzinie, typie i ważności';

-- Aktualizuj komentarze
COMMENT ON TABLE dydx_top_trader_alerts IS 
    'Alerty dotyczące aktywności top traderów na dYdX';

-- ============================================================================
-- RENAME: sentiment_propagation → google_trends_sentiment_propagation
-- ============================================================================

-- Zmień nazwę tabeli
ALTER TABLE IF EXISTS sentiment_propagation 
    RENAME TO google_trends_sentiment_propagation;

-- Zmień nazwy indeksów
DO $$
BEGIN
    -- Indeks timestamp
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_sentiment_propagation_timestamp') THEN
        ALTER INDEX ix_sentiment_propagation_timestamp 
            RENAME TO ix_google_trends_sentiment_propagation_timestamp;
    END IF;
    
    -- Indeks leading_region
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_sentiment_propagation_leading_region') THEN
        ALTER INDEX ix_sentiment_propagation_leading_region 
            RENAME TO ix_google_trends_sentiment_propagation_leading_region;
    END IF;
    
    -- Unique constraint
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'sentiment_propagation_timestamp_key') THEN
        ALTER TABLE google_trends_sentiment_propagation
            RENAME CONSTRAINT sentiment_propagation_timestamp_key 
            TO google_trends_sentiment_propagation_timestamp_key;
    END IF;
END $$;

-- Aktualizuj komentarze
COMMENT ON TABLE google_trends_sentiment_propagation IS 
    'Metryki propagacji sentymentu Google Trends między regionami (APAC, EU, US) w czasie';

