-- ============================================================================
-- MIGRACJA: Tabele dla modułu dYdX Top Traders Observer
-- ============================================================================
-- Moduł do obserwacji i rankingu najlepszych traderów na dYdX v4
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: dydx_traders - Podstawowe informacje o traderach
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_traders (
    id BIGSERIAL PRIMARY KEY,
    address VARCHAR(42) NOT NULL,                    -- Adres Ethereum (0x...)
    subaccount_number INTEGER NOT NULL,              -- Numer subkonta (0-127)
    parent_subaccount_number INTEGER,                -- Numer parent subkonta (jeśli istnieje)
    
    -- Metadane
    first_seen_at TIMESTAMPTZ NOT NULL,              -- Kiedy pierwszy raz zaobserwowany
    last_seen_at TIMESTAMPTZ NOT NULL,               -- Ostatnia obserwacja
    is_active BOOLEAN DEFAULT TRUE,                  -- Czy trader jest aktywny
    
    -- Agregowane statystyki (ostatnie 30 dni)
    total_fills_count INTEGER DEFAULT 0,             -- Całkowita liczba fill'ów
    total_volume_usd DECIMAL(30,6) DEFAULT 0,        -- Całkowity wolumen (USD)
    total_realized_pnl DECIMAL(30,6) DEFAULT 0,     -- Całkowity realized PnL
    total_net_pnl DECIMAL(30,6) DEFAULT 0,          -- Całkowity net PnL
    
    -- Metadane dodatkowe
    metadata JSONB,                                   -- Dodatkowe dane (opcjonalnie)
    notes TEXT,                                       -- Notatki (opcjonalnie)
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(address, subaccount_number)
);

COMMENT ON TABLE dydx_traders IS 'Podstawowe informacje o traderach na dYdX v4';
COMMENT ON COLUMN dydx_traders.address IS 'Adres Ethereum subkonta (0x...)';
COMMENT ON COLUMN dydx_traders.subaccount_number IS 'Numer subkonta (0-127)';
COMMENT ON COLUMN dydx_traders.parent_subaccount_number IS 'Numer parent subkonta (dla agregacji)';
COMMENT ON COLUMN dydx_traders.metadata IS 'Dodatkowe metadane w formacie JSON';

CREATE INDEX idx_dydx_traders_address ON dydx_traders(address);
CREATE INDEX idx_dydx_traders_subaccount ON dydx_traders(address, subaccount_number);
CREATE INDEX idx_dydx_traders_parent ON dydx_traders(address, parent_subaccount_number) WHERE parent_subaccount_number IS NOT NULL;
CREATE INDEX idx_dydx_traders_active ON dydx_traders(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_dydx_traders_last_seen ON dydx_traders(last_seen_at);

-- ----------------------------------------------------------------------------
-- Tabela: dydx_top_traders_rankings - Rankingi top traderów (time-series)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_top_traders_rankings (
    id BIGSERIAL PRIMARY KEY,
    trader_id BIGINT NOT NULL REFERENCES dydx_traders(id) ON DELETE CASCADE,
    address VARCHAR(42) NOT NULL,                    -- Denormalizacja dla szybkiego dostępu
    subaccount_number INTEGER NOT NULL,
    
    -- Ranking
    rank INTEGER NOT NULL,                            -- Pozycja w rankingu (1 = najlepszy)
    score DECIMAL(20,6) NOT NULL,                     -- Znormalizowany wynik rankingowy
    
    -- Metryki w oknie czasowym
    window_start TIMESTAMPTZ NOT NULL,               -- Początek okna czasowego
    window_end TIMESTAMPTZ NOT NULL,                 -- Koniec okna czasowego
    window_hours INTEGER NOT NULL,                    -- Długość okna (24, 168, etc.)
    
    -- Metryki PnL
    realized_pnl DECIMAL(30,6) NOT NULL DEFAULT 0,   -- Realized PnL w oknie
    net_pnl DECIMAL(30,6) NOT NULL DEFAULT 0,       -- Net PnL w oknie
    
    -- Metryki aktywności
    fill_count INTEGER NOT NULL DEFAULT 0,            -- Liczba fill'ów w oknie
    turnover_usd DECIMAL(30,6) NOT NULL DEFAULT 0,   -- Turnover (USD) w oknie
    
    -- Timestampy
    observed_at TIMESTAMPTZ NOT NULL,                -- Kiedy pobrano dane (UTC)
    effective_at TIMESTAMPTZ NOT NULL,                -- Efektywna data rankingu (UTC)
    
    -- Metadane
    weights JSONB,                                    -- Wagi użyte do scoringu (opcjonalnie)
    metadata JSONB,                                   -- Dodatkowe metadane
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(trader_id, window_end, window_hours)      -- Jeden ranking per trader per okno
);

COMMENT ON TABLE dydx_top_traders_rankings IS 'Rankingi top traderów w czasie (time-series)';
COMMENT ON COLUMN dydx_top_traders_rankings.rank IS 'Pozycja w rankingu (1 = najlepszy)';
COMMENT ON COLUMN dydx_top_traders_rankings.score IS 'Znormalizowany wynik rankingowy';
COMMENT ON COLUMN dydx_top_traders_rankings.observed_at IS 'Kiedy pobrano dane z API (UTC)';
COMMENT ON COLUMN dydx_top_traders_rankings.effective_at IS 'Efektywna data rankingu (UTC)';

CREATE INDEX idx_dydx_rankings_trader ON dydx_top_traders_rankings(trader_id);
CREATE INDEX idx_dydx_rankings_address ON dydx_top_traders_rankings(address, subaccount_number);
CREATE INDEX idx_dydx_rankings_window ON dydx_top_traders_rankings(window_start, window_end);
CREATE INDEX idx_dydx_rankings_effective_at ON dydx_top_traders_rankings(effective_at);
CREATE INDEX idx_dydx_rankings_observed_at ON dydx_top_traders_rankings(observed_at);
CREATE INDEX idx_dydx_rankings_rank ON dydx_top_traders_rankings(rank, effective_at);
CREATE INDEX idx_dydx_rankings_lookup ON dydx_top_traders_rankings(effective_at, window_hours, rank);

-- ----------------------------------------------------------------------------
-- Tabela: dydx_fills - Fill'e (transakcje) od top traderów
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_fills (
    id BIGSERIAL PRIMARY KEY,
    trader_id BIGINT NOT NULL REFERENCES dydx_traders(id) ON DELETE CASCADE,
    address VARCHAR(42) NOT NULL,                    -- Denormalizacja
    subaccount_number INTEGER NOT NULL,
    
    -- Identyfikacja fill'a
    fill_id VARCHAR(255) NOT NULL,                   -- ID fill'a z API (lub generated)
    
    -- Dane transakcji
    ticker VARCHAR(20) NOT NULL,                     -- Symbol rynku (np. BTC-USD)
    side VARCHAR(10) NOT NULL,                        -- BUY, SELL
    price DECIMAL(30,8) NOT NULL,                     -- Cena
    size DECIMAL(30,8) NOT NULL,                     -- Rozmiar
    fee DECIMAL(30,8) NOT NULL DEFAULT 0,            -- Opłata
    
    -- PnL
    realized_pnl DECIMAL(30,6),                       -- Realized PnL (może być NULL)
    
    -- Timestampy
    effective_at TIMESTAMPTZ NOT NULL,                -- Efektywna data fill'a (UTC)
    created_at TIMESTAMPTZ NOT NULL,                 -- Data utworzenia fill'a (UTC)
    observed_at TIMESTAMPTZ NOT NULL,                 -- Kiedy pobrano z API (UTC)
    
    -- Metadane
    metadata JSONB,                                   -- Dodatkowe dane z API
    
    created_at_db TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(fill_id, address, subaccount_number)      -- Deduplikacja
);

COMMENT ON TABLE dydx_fills IS 'Fille (transakcje) od top traderów na dYdX v4';
COMMENT ON COLUMN dydx_fills.fill_id IS 'Unikalny ID filla (z API lub generated)';
COMMENT ON COLUMN dydx_fills.effective_at IS 'Efektywna data filla z API (UTC)';
COMMENT ON COLUMN dydx_fills.created_at IS 'Data utworzenia filla z API (UTC)';
COMMENT ON COLUMN dydx_fills.observed_at IS 'Kiedy pobrano filla z API (UTC)';

CREATE INDEX idx_dydx_fills_trader ON dydx_fills(trader_id);
CREATE INDEX idx_dydx_fills_address ON dydx_fills(address, subaccount_number);
CREATE INDEX idx_dydx_fills_ticker ON dydx_fills(ticker);
CREATE INDEX idx_dydx_fills_effective_at ON dydx_fills(effective_at);
CREATE INDEX idx_dydx_fills_created_at ON dydx_fills(created_at);
CREATE INDEX idx_dydx_fills_observed_at ON dydx_fills(observed_at);
CREATE INDEX idx_dydx_fills_lookup ON dydx_fills(address, subaccount_number, effective_at);

-- ----------------------------------------------------------------------------
-- Tabela: dydx_historical_pnl - Historical PnL (cache)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_historical_pnl (
    id BIGSERIAL PRIMARY KEY,
    trader_id BIGINT NOT NULL REFERENCES dydx_traders(id) ON DELETE CASCADE,
    address VARCHAR(42) NOT NULL,                    -- Denormalizacja
    subaccount_number INTEGER NOT NULL,
    
    -- PnL
    realized_pnl DECIMAL(30,6) NOT NULL,             -- Realized PnL
    net_pnl DECIMAL(30,6) NOT NULL,                  -- Net PnL
    
    -- Timestampy
    effective_at TIMESTAMPTZ NOT NULL,                -- Efektywna data PnL (UTC)
    created_at TIMESTAMPTZ NOT NULL,                  -- Data utworzenia PnL (UTC)
    observed_at TIMESTAMPTZ NOT NULL,                  -- Kiedy pobrano z API (UTC)
    
    -- Metadane
    metadata JSONB,                                    -- Dodatkowe dane z API
    
    created_at_db TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(address, subaccount_number, effective_at)  -- Deduplikacja
);

COMMENT ON TABLE dydx_historical_pnl IS 'Historical PnL dla traderów (cache z API)';
COMMENT ON COLUMN dydx_historical_pnl.effective_at IS 'Efektywna data PnL (UTC)';
COMMENT ON COLUMN dydx_historical_pnl.observed_at IS 'Kiedy pobrano PnL z API (UTC)';

CREATE INDEX idx_dydx_pnl_trader ON dydx_historical_pnl(trader_id);
CREATE INDEX idx_dydx_pnl_address ON dydx_historical_pnl(address, subaccount_number);
CREATE INDEX idx_dydx_pnl_effective_at ON dydx_historical_pnl(effective_at);
CREATE INDEX idx_dydx_pnl_observed_at ON dydx_historical_pnl(observed_at);
CREATE INDEX idx_dydx_pnl_lookup ON dydx_historical_pnl(address, subaccount_number, effective_at);

-- ----------------------------------------------------------------------------
-- Tabela: dydx_trader_metrics - Agregowane metryki traderów (okresowe snapshoty)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_trader_metrics (
    id BIGSERIAL PRIMARY KEY,
    trader_id BIGINT NOT NULL REFERENCES dydx_traders(id) ON DELETE CASCADE,
    address VARCHAR(42) NOT NULL,
    subaccount_number INTEGER NOT NULL,
    
    -- Okres metryk
    period_start TIMESTAMPTZ NOT NULL,               -- Początek okresu
    period_end TIMESTAMPTZ NOT NULL,                  -- Koniec okresu
    period_type VARCHAR(20) NOT NULL,                 -- hourly, daily, weekly
    
    -- Metryki aktywności
    fills_count INTEGER NOT NULL DEFAULT 0,           -- Liczba fill'ów
    unique_tickers_count INTEGER NOT NULL DEFAULT 0,  -- Liczba unikalnych tickerów
    
    -- Metryki wolumenu
    total_volume_usd DECIMAL(30,6) NOT NULL DEFAULT 0, -- Całkowity wolumen (USD)
    avg_fill_size_usd DECIMAL(30,6),                  -- Średni rozmiar fill'a (USD)
    max_fill_size_usd DECIMAL(30,6),                  -- Maksymalny rozmiar fill'a (USD)
    
    -- Metryki PnL
    total_realized_pnl DECIMAL(30,6) NOT NULL DEFAULT 0, -- Całkowity realized PnL
    total_net_pnl DECIMAL(30,6) NOT NULL DEFAULT 0,      -- Całkowity net PnL
    avg_realized_pnl DECIMAL(30,6),                      -- Średni realized PnL per fill
    win_rate DECIMAL(5,4),                                -- Wskaźnik wygranych (0-1)
    
    -- Metryki opłat
    total_fees_usd DECIMAL(30,6) NOT NULL DEFAULT 0,     -- Całkowite opłaty (USD)
    
    -- Timestampy
    calculated_at TIMESTAMPTZ NOT NULL,                   -- Kiedy obliczono metryki (UTC)
    
    -- Metadane
    metadata JSONB,                                       -- Dodatkowe metadane
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(trader_id, period_start, period_end, period_type)
);

COMMENT ON TABLE dydx_trader_metrics IS 'Agregowane metryki traderów w okresach czasowych';
COMMENT ON COLUMN dydx_trader_metrics.period_type IS 'Typ okresu: hourly, daily, weekly';
COMMENT ON COLUMN dydx_trader_metrics.win_rate IS 'Wskaźnik wygranych transakcji (0-1)';

CREATE INDEX idx_dydx_metrics_trader ON dydx_trader_metrics(trader_id);
CREATE INDEX idx_dydx_metrics_address ON dydx_trader_metrics(address, subaccount_number);
CREATE INDEX idx_dydx_metrics_period ON dydx_trader_metrics(period_start, period_end);
CREATE INDEX idx_dydx_metrics_type ON dydx_trader_metrics(period_type);
CREATE INDEX idx_dydx_metrics_calculated_at ON dydx_trader_metrics(calculated_at);
CREATE INDEX idx_dydx_metrics_lookup ON dydx_trader_metrics(trader_id, period_type, period_start);

-- ----------------------------------------------------------------------------
-- Tabela: dydx_fill_events - Eventy fill'ów do publikacji
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_fill_events (
    id BIGSERIAL PRIMARY KEY,
    fill_id BIGINT NOT NULL REFERENCES dydx_fills(id) ON DELETE CASCADE,
    trader_id BIGINT NOT NULL REFERENCES dydx_traders(id) ON DELETE CASCADE,
    
    -- Event metadata
    event_type VARCHAR(50) NOT NULL DEFAULT 'fill',  -- fill, large_fill, pnl_event, etc.
    event_status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, published, failed
    
    -- Timestampy
    event_occurred_at TIMESTAMPTZ NOT NULL,          -- Kiedy zdarzenie wystąpiło (effective_at)
    event_created_at TIMESTAMPTZ NOT NULL,           -- Kiedy event został utworzony
    event_published_at TIMESTAMPTZ,                   -- Kiedy event został opublikowany
    
    -- Publikacja
    published_to TEXT,                                -- Gdzie opublikowano (queue name, webhook URL, etc.)
    publish_attempts INTEGER DEFAULT 0,               -- Liczba prób publikacji
    publish_error TEXT,                               -- Ostatni błąd publikacji
    
    -- Metadane
    event_data JSONB,                                  -- Dane eventu (serialized FillEvent)
    metadata JSONB,                                    -- Dodatkowe metadane
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dydx_fill_events IS 'Eventy fillów do publikacji do reszty systemu';
COMMENT ON COLUMN dydx_fill_events.event_type IS 'Typ eventu: fill, large_fill, pnl_event, etc.';
COMMENT ON COLUMN dydx_fill_events.event_status IS 'Status: pending, published, failed';
COMMENT ON COLUMN dydx_fill_events.published_to IS 'Gdzie opublikowano (queue name, webhook, etc.)';

CREATE INDEX idx_dydx_events_fill ON dydx_fill_events(fill_id);
CREATE INDEX idx_dydx_events_trader ON dydx_fill_events(trader_id);
CREATE INDEX idx_dydx_events_status ON dydx_fill_events(event_status);
CREATE INDEX idx_dydx_events_occurred_at ON dydx_fill_events(event_occurred_at);
CREATE INDEX idx_dydx_events_pending ON dydx_fill_events(event_status, event_occurred_at) WHERE event_status = 'pending';

-- ----------------------------------------------------------------------------
-- Tabela: dydx_observer_log - Log operacji observera
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dydx_observer_log (
    id BIGSERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,             -- update_ranking, watch_traders, discover_candidates, etc.
    operation_status VARCHAR(20) NOT NULL,           -- running, success, failed, partial
    
    -- Timestampy
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    
    -- Statystyki
    candidates_discovered INTEGER DEFAULT 0,         -- Liczba odkrytych kandydatów
    traders_scored INTEGER DEFAULT 0,                -- Liczba traderów ze scoringiem
    top_traders_saved INTEGER DEFAULT 0,            -- Liczba zapisanych top traderów
    fills_processed INTEGER DEFAULT 0,               -- Liczba przetworzonych fill'ów
    events_created INTEGER DEFAULT 0,                 -- Liczba utworzonych eventów
    
    -- Błędy
    errors_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Metadane
    config JSONB,                                     -- Konfiguracja użyta w operacji
    details JSONB,                                    -- Szczegóły operacji
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dydx_observer_log IS 'Log operacji modułu Top Traders Observer';
COMMENT ON COLUMN dydx_observer_log.operation_type IS 'Typ operacji: update_ranking, watch_traders, etc.';
COMMENT ON COLUMN dydx_observer_log.operation_status IS 'Status: running, success, failed, partial';

CREATE INDEX idx_dydx_log_operation ON dydx_observer_log(operation_type);
CREATE INDEX idx_dydx_log_status ON dydx_observer_log(operation_status);
CREATE INDEX idx_dydx_log_started_at ON dydx_observer_log(started_at);
CREATE INDEX idx_dydx_log_lookup ON dydx_observer_log(operation_type, started_at);

-- ----------------------------------------------------------------------------
-- Funkcje pomocnicze
-- ----------------------------------------------------------------------------

-- Trigger do aktualizacji updated_at
CREATE TRIGGER update_dydx_traders_updated_at
    BEFORE UPDATE ON dydx_traders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dydx_fill_events_updated_at
    BEFORE UPDATE ON dydx_fill_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Funkcja do aktualizacji last_seen_at w dydx_traders
CREATE OR REPLACE FUNCTION update_trader_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE dydx_traders
    SET last_seen_at = NEW.observed_at,
        total_fills_count = total_fills_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.trader_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_trader_on_fill
    AFTER INSERT ON dydx_fills
    FOR EACH ROW
    EXECUTE FUNCTION update_trader_last_seen();

