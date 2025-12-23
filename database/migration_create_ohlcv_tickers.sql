-- ============================================================================
-- Migracja: Utworzenie tabel ohlcv i tickers
-- ============================================================================
-- Tabele do przechowywania danych OHLCV (świece) i tickers (snapshoty cen)
-- z różnych giełd kryptowalutowych.
-- ============================================================================

-- Tabela: ohlcv - Świece OHLCV (Open, High, Low, Close, Volume)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ohlcv (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    -- Dane OHLCV
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    
    -- Opcjonalne pola
    quote_volume DOUBLE PRECISION,
    trades_count INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint zapobiega duplikatom
    CONSTRAINT uq_ohlcv UNIQUE (timestamp, exchange, symbol, timeframe)
);

-- Indeksy dla szybkiego wyszukiwania
CREATE INDEX IF NOT EXISTS ix_ohlcv_timestamp ON ohlcv (timestamp);
CREATE INDEX IF NOT EXISTS ix_ohlcv_exchange ON ohlcv (exchange);
CREATE INDEX IF NOT EXISTS ix_ohlcv_symbol ON ohlcv (symbol);
CREATE INDEX IF NOT EXISTS ix_ohlcv_timeframe ON ohlcv (timeframe);
CREATE INDEX IF NOT EXISTS ix_ohlcv_lookup ON ohlcv (exchange, symbol, timeframe, timestamp);

COMMENT ON TABLE ohlcv IS 'Tabela świec OHLCV z różnych giełd kryptowalutowych';
COMMENT ON COLUMN ohlcv.timestamp IS 'Czas świecy (UTC)';
COMMENT ON COLUMN ohlcv.exchange IS 'Nazwa giełdy (np. binance, dydx)';
COMMENT ON COLUMN ohlcv.symbol IS 'Symbol pary (np. BTC/USDC, BTC-USD)';
COMMENT ON COLUMN ohlcv.timeframe IS 'Interwał czasowy (1m, 5m, 1h, 1d)';
COMMENT ON COLUMN ohlcv.quote_volume IS 'Wolumen w walucie kwotowanej';
COMMENT ON COLUMN ohlcv.trades_count IS 'Liczba transakcji w świecy';

-- Tabela: tickers - Snapshoty tickerów
-- ============================================================================
CREATE TABLE IF NOT EXISTS tickers (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    
    -- Podstawowe dane cenowe
    price DOUBLE PRECISION NOT NULL,
    bid DOUBLE PRECISION,
    ask DOUBLE PRECISION,
    spread DOUBLE PRECISION,
    
    -- Statystyki 24h
    volume_24h DOUBLE PRECISION,
    change_24h DOUBLE PRECISION,
    high_24h DOUBLE PRECISION,
    low_24h DOUBLE PRECISION,
    
    -- Dla perpetual (dYdX)
    funding_rate DOUBLE PRECISION,
    open_interest DOUBLE PRECISION,
    
    -- Unique constraint zapobiega duplikatom
    CONSTRAINT uq_ticker_unique UNIQUE (timestamp, exchange, symbol)
);

-- Indeksy dla szybkiego wyszukiwania
CREATE INDEX IF NOT EXISTS ix_ticker_timestamp ON tickers (timestamp);
CREATE INDEX IF NOT EXISTS ix_ticker_exchange ON tickers (exchange);
CREATE INDEX IF NOT EXISTS ix_ticker_symbol ON tickers (symbol);
CREATE INDEX IF NOT EXISTS ix_ticker_lookup ON tickers (exchange, symbol, timestamp);

COMMENT ON TABLE tickers IS 'Snapshoty tickerów - aktualne ceny i wolumeny';
COMMENT ON COLUMN tickers.timestamp IS 'Czas snapshotu (UTC)';
COMMENT ON COLUMN tickers.exchange IS 'Nazwa giełdy (np. binance, dydx)';
COMMENT ON COLUMN tickers.symbol IS 'Symbol pary (np. BTC/USDC, BTC-USD)';
COMMENT ON COLUMN tickers.funding_rate IS 'Funding rate dla perpetual (dYdX)';
COMMENT ON COLUMN tickers.open_interest IS 'Open interest dla perpetual (dYdX)';

-- Opcjonalnie: Włącz TimescaleDB jeśli jest dostępne
-- ============================================================================
-- CREATE EXTENSION IF NOT EXISTS timescaledb;
-- SELECT create_hypertable('ohlcv', 'timestamp', if_not_exists => TRUE);
-- SELECT create_hypertable('tickers', 'timestamp', if_not_exists => TRUE);

