-- ============================================================================
-- MIGRACJA: Tabela dla transakcji z perpetualMarket (dYdX v4)
-- ============================================================================
-- Tabela do przechowywania transakcji z rynku perpetual (bez adresów traderów)
-- Endpoint: GET /trades/perpetualMarket/{ticker}
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: dydx_perpetual_market_trades - Transakcje z rynku perpetual
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_perpetual_market_trades (
    id BIGSERIAL PRIMARY KEY,
    
    -- Identyfikacja rynku
    ticker VARCHAR(20) NOT NULL,                       -- Symbol rynku (np. BTC-USD, ETH-USD)
    
    -- Dane transakcji (z API)
    trade_id VARCHAR(100) NOT NULL,                     -- Unikalny ID transakcji z API
    side VARCHAR(10) NOT NULL,                          -- BUY lub SELL
    size DECIMAL(30,18) NOT NULL,                       -- Rozmiar transakcji
    price DECIMAL(30,8) NOT NULL,                       -- Cena transakcji
    trade_type VARCHAR(20),                              -- Typ zlecenia: LIMIT, MARKET, etc.
    
    -- Timestampy
    effective_at TIMESTAMPTZ NOT NULL,                   -- Data utworzenia transakcji (UTC)
    created_at_height BIGINT,                           -- Wysokość bloku (createdAtHeight)
    observed_at TIMESTAMPTZ NOT NULL,                   -- Kiedy pobrano z API (UTC)
    
    -- Metadane
    metadata JSONB,                                     -- Dodatkowe dane z API (opcjonalnie)
    
    created_at_db TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(trade_id, ticker)                           -- Deduplikacja po trade_id i ticker
);

COMMENT ON TABLE dydx_perpetual_market_trades IS 'Transakcje z rynku perpetual (bez adresów traderów)';
COMMENT ON COLUMN dydx_perpetual_market_trades.ticker IS 'Symbol rynku (np. BTC-USD, ETH-USD)';
COMMENT ON COLUMN dydx_perpetual_market_trades.trade_id IS 'Unikalny ID transakcji z API dYdX';
COMMENT ON COLUMN dydx_perpetual_market_trades.effective_at IS 'Data utworzenia transakcji (UTC)';
COMMENT ON COLUMN dydx_perpetual_market_trades.observed_at IS 'Kiedy pobrano transakcję z API (UTC)';
COMMENT ON COLUMN dydx_perpetual_market_trades.metadata IS 'Dodatkowe dane z API w formacie JSON';

-- Indeksy dla szybkiego wyszukiwania
CREATE INDEX idx_dydx_market_trades_ticker ON dydx_perpetual_market_trades(ticker);
CREATE INDEX idx_dydx_market_trades_effective_at ON dydx_perpetual_market_trades(effective_at);
CREATE INDEX idx_dydx_market_trades_observed_at ON dydx_perpetual_market_trades(observed_at);
CREATE INDEX idx_dydx_market_trades_side ON dydx_perpetual_market_trades(side);
CREATE INDEX idx_dydx_market_trades_lookup ON dydx_perpetual_market_trades(ticker, effective_at DESC);
CREATE INDEX idx_dydx_market_trades_unique ON dydx_perpetual_market_trades(trade_id, ticker);

-- Indeks dla analizy wolumenu
CREATE INDEX idx_dydx_market_trades_volume ON dydx_perpetual_market_trades(ticker, effective_at DESC) 
    WHERE size > 0;

