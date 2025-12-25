-- Migration: 006_top_trader_alerts
-- ==================================================
-- Tabela do przechowywania alertów dotyczących aktywności top traderów.
-- 
-- UWAGA: Tabela została przemianowana na dydx_top_trader_alerts w migracji 007.
-- Ta migracja jest zachowana dla historii, ale użyj migracji 007 do aktualizacji.
-- 
-- Alerty są generowane gdy:
-- - Top trader wykonuje dużą transakcję (przekracza threshold)
-- - Top trader zmienia znacząco pozycję (net position change)
-- - Top trader osiąga określony wolumen w oknie czasowym
-- - Top trader ma nietypową aktywność (anomalia)

-- ============================================================================
-- TABELA: top_trader_alerts
-- ============================================================================

CREATE TABLE IF NOT EXISTS top_trader_alerts (
    id SERIAL PRIMARY KEY,
    alert_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Trader info
    trader_address VARCHAR(42) NOT NULL,
    subaccount_number INTEGER NOT NULL,
    trader_rank INTEGER,  -- Pozycja w rankingu w momencie alertu
    
    -- Fill info (jeśli alert dotyczy konkretnego fill'a)
    fill_id VARCHAR(255),
    ticker VARCHAR(20),
    side VARCHAR(10),  -- BUY, SELL
    price DECIMAL(20, 8),
    size DECIMAL(20, 8),
    volume_usd DECIMAL(20, 2),  -- size * price
    
    -- Alert type
    alert_type VARCHAR(50) NOT NULL,  -- LARGE_TRADE, POSITION_CHANGE, VOLUME_SPIKE, ANOMALY
    alert_severity VARCHAR(20) NOT NULL DEFAULT 'medium',  -- low, medium, high, critical
    alert_message TEXT,
    
    -- Metrics
    threshold_value DECIMAL(20, 2),  -- Wartość progu który został przekroczony
    actual_value DECIMAL(20, 2),  -- Rzeczywista wartość
    net_position_before DECIMAL(20, 8),  -- Net position przed transakcją
    net_position_after DECIMAL(20, 8),  -- Net position po transakcji
    
    -- Context
    window_hours INTEGER,  -- Okno czasowe dla metryk
    lookback_hours INTEGER,  -- Lookback dla porównań
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB,  -- Dodatkowe dane (np. historical context)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indeksy
CREATE INDEX IF NOT EXISTS ix_top_trader_alerts_timestamp 
    ON top_trader_alerts (alert_timestamp DESC);

CREATE INDEX IF NOT EXISTS ix_top_trader_alerts_trader 
    ON top_trader_alerts (trader_address, subaccount_number, alert_timestamp DESC);

CREATE INDEX IF NOT EXISTS ix_top_trader_alerts_type 
    ON top_trader_alerts (alert_type, alert_severity, alert_timestamp DESC);

CREATE INDEX IF NOT EXISTS ix_top_trader_alerts_unread 
    ON top_trader_alerts (is_read, alert_timestamp DESC) 
    WHERE is_read = FALSE;

CREATE INDEX IF NOT EXISTS ix_top_trader_alerts_ticker 
    ON top_trader_alerts (ticker, alert_timestamp DESC);

-- TimescaleDB hypertable (jeśli dostępne)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('top_trader_alerts', 'alert_timestamp', 
                                  chunk_time_interval => INTERVAL '1 day',
                                  if_not_exists => TRUE);
    END IF;
END $$;

-- Komentarze
COMMENT ON TABLE top_trader_alerts IS 
    'Alerty dotyczące aktywności top traderów na dYdX';

COMMENT ON COLUMN top_trader_alerts.alert_type IS 
    'Typ alertu: LARGE_TRADE, POSITION_CHANGE, VOLUME_SPIKE, ANOMALY';

COMMENT ON COLUMN top_trader_alerts.alert_severity IS 
    'Poziom ważności: low, medium, high, critical';

COMMENT ON COLUMN top_trader_alerts.volume_usd IS 
    'Wartość transakcji w USD (size * price)';

COMMENT ON COLUMN top_trader_alerts.metadata IS 
    'Dodatkowe dane w formacie JSON (np. historical averages, context)';

-- ============================================================================
-- VIEW: top_trader_alerts_summary
-- ============================================================================
-- Widok agregujący alerty dla łatwego monitorowania

CREATE OR REPLACE VIEW top_trader_alerts_summary AS
SELECT 
    DATE_TRUNC('hour', alert_timestamp) AS hour,
    alert_type,
    alert_severity,
    COUNT(*) AS alert_count,
    COUNT(DISTINCT trader_address || ':' || subaccount_number) AS unique_traders,
    SUM(volume_usd) AS total_volume_usd,
    AVG(volume_usd) AS avg_volume_usd,
    MAX(volume_usd) AS max_volume_usd
FROM top_trader_alerts
GROUP BY 
    DATE_TRUNC('hour', alert_timestamp),
    alert_type,
    alert_severity
ORDER BY hour DESC, alert_severity DESC, alert_count DESC;

COMMENT ON VIEW top_trader_alerts_summary IS 
    'Agregowany widok alertów top traderów pogrupowany po godzinie, typie i ważności';

