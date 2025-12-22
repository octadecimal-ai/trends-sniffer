-- ============================================================================
-- Migracja: Utworzenie tabeli bitcoin_sentiment_phrases
-- ============================================================================
-- Tabela do przechowywania fraz sentymentu BTC z pliku phrases.csv
-- ============================================================================

CREATE TABLE IF NOT EXISTS bitcoin_sentiment_phrases (
    id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    language_code VARCHAR(10) NOT NULL,              -- en-CA, en-US, zh-CN, etc.
    phrase VARCHAR(200) NOT NULL,                    -- Fraza do monitoringu
    multiplier DECIMAL(5,4) NOT NULL DEFAULT 0.0000, -- Waga sentymentu (-1.0 do 1.0)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(country_id, language_code, phrase)
);

COMMENT ON TABLE bitcoin_sentiment_phrases IS 'Frazy sentymentu BTC per kraj i język';

CREATE INDEX idx_bitcoin_sentiment_phrases_country ON bitcoin_sentiment_phrases(country_id);
CREATE INDEX idx_bitcoin_sentiment_phrases_language ON bitcoin_sentiment_phrases(language_code);
CREATE INDEX idx_bitcoin_sentiment_phrases_active ON bitcoin_sentiment_phrases(is_active);
CREATE INDEX idx_bitcoin_sentiment_phrases_lookup ON bitcoin_sentiment_phrases(country_id, language_code, is_active);

-- Trigger do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_bitcoin_sentiment_phrases_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_bitcoin_sentiment_phrases_updated_at
    BEFORE UPDATE ON bitcoin_sentiment_phrases
    FOR EACH ROW
    EXECUTE FUNCTION update_bitcoin_sentiment_phrases_updated_at();

