-- ============================================================================
-- MIGRACJA: Tabela dla postępu daemona dydx_perpetual_market_trades
-- ============================================================================
-- Tabela do przechowywania postępu daemona pobierającego transakcje z perpetualMarket
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: dydx_perpetual_market_trades_progress - Postęp daemona
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_perpetual_market_trades_progress (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identyfikacja
    ticker VARCHAR(20) NOT NULL,                       -- Symbol rynku (np. BTC-USD, ETH-USD)
    
    -- Postęp
    processing_date TIMESTAMPTZ NOT NULL,               -- Aktualna data przetwarzania (UTC)
    total_trades INTEGER DEFAULT 0,                    -- Łączna liczba zapisanych transakcji
    last_update TIMESTAMPTZ NOT NULL,                  -- Ostatnia aktualizacja (UTC)
    
    -- Szczegóły prób
    attempts JSONB,                                    -- Lista prób z batchami (JSON)
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ticker)                                     -- Jeden rekord postępu na ticker
);

COMMENT ON TABLE dydx_perpetual_market_trades_progress IS 'Postęp daemona pobierającego transakcje z perpetualMarket';
COMMENT ON COLUMN dydx_perpetual_market_trades_progress.ticker IS 'Symbol rynku (np. BTC-USD, ETH-USD)';
COMMENT ON COLUMN dydx_perpetual_market_trades_progress.processing_date IS 'Aktualna data przetwarzania (UTC)';
COMMENT ON COLUMN dydx_perpetual_market_trades_progress.total_trades IS 'Łączna liczba zapisanych transakcji';
COMMENT ON COLUMN dydx_perpetual_market_trades_progress.attempts IS 'Lista prób z batchami w formacie JSON';

-- Indeksy
CREATE INDEX idx_dydx_progress_ticker ON dydx_perpetual_market_trades_progress(ticker);
CREATE INDEX idx_dydx_progress_processing_date ON dydx_perpetual_market_trades_progress(processing_date);
CREATE INDEX idx_dydx_progress_last_update ON dydx_perpetual_market_trades_progress(last_update);

-- Trigger do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_dydx_progress_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_dydx_progress_updated_at_trigger
    BEFORE UPDATE ON dydx_perpetual_market_trades_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_dydx_progress_updated_at();

