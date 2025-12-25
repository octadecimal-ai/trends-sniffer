-- Migration: 003_market_indices
-- Opis: Tabele dla danych z tradycyjnych rynków finansowych
-- Data: 2024-12-24
-- Autor: trends-sniffer

-- =============================================================================
-- TABELA: market_indices
-- Dane indeksów rynkowych z Yahoo Finance
-- =============================================================================

CREATE TABLE IF NOT EXISTS market_indices (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(50) NOT NULL,
    
    -- Dane cenowe
    value FLOAT NOT NULL,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    
    -- Zmiany procentowe
    change_1h FLOAT,
    change_24h FLOAT,
    change_7d FLOAT,
    
    -- Metadane
    source VARCHAR(50) DEFAULT 'yfinance',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint (wymagany przed hypertable)
ALTER TABLE market_indices 
    ADD CONSTRAINT uq_market_index UNIQUE (timestamp, symbol);

-- Indeksy
CREATE INDEX IF NOT EXISTS ix_market_indices_lookup 
    ON market_indices (symbol, timestamp);
CREATE INDEX IF NOT EXISTS ix_market_indices_name 
    ON market_indices (name);

-- Hypertable (TimescaleDB)
SELECT create_hypertable('market_indices', 'timestamp', 
    if_not_exists => TRUE, 
    migrate_data => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);

-- =============================================================================
-- TABELA: fear_greed_index
-- Crypto Fear & Greed Index z alternative.me
-- =============================================================================

CREATE TABLE IF NOT EXISTS fear_greed_index (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Wartość indeksu
    value INTEGER NOT NULL CHECK (value >= 0 AND value <= 100),
    classification VARCHAR(20) NOT NULL,
    
    -- Kontekst
    btc_price_at_reading FLOAT,
    
    -- Zmiany
    value_change_24h INTEGER,
    value_change_7d INTEGER,
    
    -- Metadane
    time_until_update VARCHAR(50),
    source VARCHAR(50) DEFAULT 'alternative.me',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint
ALTER TABLE fear_greed_index 
    ADD CONSTRAINT uq_fear_greed UNIQUE (timestamp);

-- Indeksy
CREATE INDEX IF NOT EXISTS ix_fear_greed_timestamp 
    ON fear_greed_index (timestamp);
CREATE INDEX IF NOT EXISTS ix_fear_greed_value 
    ON fear_greed_index (value);

-- Hypertable (TimescaleDB)
SELECT create_hypertable('fear_greed_index', 'timestamp', 
    if_not_exists => TRUE, 
    migrate_data => TRUE,
    chunk_time_interval => INTERVAL '30 days'
);

-- =============================================================================
-- TABELA: economic_calendar
-- Kalendarz wydarzeń ekonomicznych
-- =============================================================================

CREATE TABLE IF NOT EXISTS economic_calendar (
    id SERIAL PRIMARY KEY,
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Opis wydarzenia
    event_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    country VARCHAR(10) NOT NULL DEFAULT 'US',
    
    -- Ważność
    importance VARCHAR(10) NOT NULL DEFAULT 'medium',
    
    -- Dane (wypełniane po publikacji)
    actual FLOAT,
    forecast FLOAT,
    previous FLOAT,
    
    -- Wpływ na rynek
    btc_price_before FLOAT,
    btc_price_after_1h FLOAT,
    btc_price_after_24h FLOAT,
    
    -- Metadane
    notes TEXT,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint
ALTER TABLE economic_calendar 
    ADD CONSTRAINT uq_economic_event UNIQUE (event_date, event_name);

-- Indeksy
CREATE INDEX IF NOT EXISTS ix_economic_calendar_lookup 
    ON economic_calendar (event_type, event_date);
CREATE INDEX IF NOT EXISTS ix_economic_calendar_country 
    ON economic_calendar (country, event_date);
CREATE INDEX IF NOT EXISTS ix_economic_calendar_importance 
    ON economic_calendar (importance, event_date);

-- =============================================================================
-- WIDOKI POMOCNICZE
-- =============================================================================

-- Widok: Aktualny stan indeksów
CREATE OR REPLACE VIEW v_current_market_indices AS
SELECT DISTINCT ON (symbol)
    symbol,
    name,
    value,
    change_1h,
    change_24h,
    timestamp
FROM market_indices
ORDER BY symbol, timestamp DESC;

-- Widok: Aktualny Fear & Greed
CREATE OR REPLACE VIEW v_current_fear_greed AS
SELECT 
    value,
    classification,
    value_change_24h,
    value_change_7d,
    timestamp
FROM alternative_me_fear_greed_index
ORDER BY timestamp DESC
LIMIT 1;

-- Widok: Nadchodzące wydarzenia ekonomiczne
CREATE OR REPLACE VIEW v_upcoming_economic_events AS
SELECT 
    event_date,
    event_name,
    event_type,
    country,
    importance,
    forecast,
    previous
FROM manual_economic_calendar
WHERE event_date >= NOW()
ORDER BY event_date
LIMIT 20;

-- =============================================================================
-- KOMENTARZE
-- =============================================================================

COMMENT ON TABLE market_indices IS 
    'Indeksy rynkowe z tradycyjnych rynków (Yahoo Finance): SPX, VIX, DXY, NASDAQ, GOLD, TNX';

COMMENT ON TABLE fear_greed_index IS 
    'Crypto Fear & Greed Index (alternative.me): 0-100, aktualizowany raz dziennie';

COMMENT ON TABLE economic_calendar IS 
    'Kalendarz wydarzeń makroekonomicznych: FOMC, CPI, NFP, GDP';

COMMENT ON COLUMN market_indices.symbol IS 
    'Symbol Yahoo Finance: ^GSPC (SPX), ^VIX (VIX), DX-Y.NYB (DXY), ^IXIC (NASDAQ)';

COMMENT ON COLUMN fear_greed_index.classification IS 
    'Extreme Fear (0-24), Fear (25-44), Neutral (45-55), Greed (56-75), Extreme Greed (76-100)';

