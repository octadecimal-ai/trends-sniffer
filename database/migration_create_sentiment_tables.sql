-- ============================================================================
-- Migracja: Tabele do przechowywania wyników monitoringu sentymentu BTC
-- ============================================================================

-- Tabela główna z danymi pomiaru sentymentu
CREATE TABLE IF NOT EXISTS sentiment_measurement (
    id SERIAL PRIMARY KEY,
    phrase_id INTEGER NOT NULL REFERENCES bitcoin_sentiment_phrases(id),
    country_id INTEGER NOT NULL REFERENCES countries(id),
    language_code VARCHAR(10) NOT NULL,
    ip VARCHAR(45),  -- IPv4 lub IPv6
    vpn_country VARCHAR(10),  -- Kod kraju VPN (ISO 2)
    occurrence_count INTEGER DEFAULT 0,  -- Liczba wystąpień (timestampów z wartością > 0)
    stats_count INTEGER DEFAULT 0,  -- Count ze statystyk
    stats_mean DECIMAL(10,4) DEFAULT 0.0,  -- Mean ze statystyk
    stats_std DECIMAL(10,4) DEFAULT 0.0,  -- Std ze statystyk
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Indeksy dla szybkiego wyszukiwania
    CONSTRAINT fk_sentiment_measurement_phrase FOREIGN KEY (phrase_id) REFERENCES bitcoin_sentiment_phrases(id) ON DELETE CASCADE,
    CONSTRAINT fk_sentiment_measurement_country FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE
);

COMMENT ON TABLE sentiment_measurement IS 'Główna tabela z danymi pomiaru sentymentu - zapisuje wszystkie zapytania, nawet bez wystąpień';
COMMENT ON COLUMN sentiment_measurement.phrase_id IS 'ID frazy z bitcoin_sentiment_phrases';
COMMENT ON COLUMN sentiment_measurement.country_id IS 'ID kraju z tabeli countries';
COMMENT ON COLUMN sentiment_measurement.language_code IS 'Kod języka (np. en-CA, pl-PL)';
COMMENT ON COLUMN sentiment_measurement.ip IS 'Adres IP użyty do zapytania';
COMMENT ON COLUMN sentiment_measurement.vpn_country IS 'Kod kraju VPN (ISO 2)';
COMMENT ON COLUMN sentiment_measurement.occurrence_count IS 'Liczba wystąpień (timestampów z wartością > 0)';
COMMENT ON COLUMN sentiment_measurement.stats_count IS 'Liczba pomiarów w statystykach';
COMMENT ON COLUMN sentiment_measurement.stats_mean IS 'Średnia wartość zainteresowania';
COMMENT ON COLUMN sentiment_measurement.stats_std IS 'Odchylenie standardowe';

-- Indeksy
CREATE INDEX idx_sentiment_measurement_phrase_id ON sentiment_measurement(phrase_id);
CREATE INDEX idx_sentiment_measurement_country_id ON sentiment_measurement(country_id);
CREATE INDEX idx_sentiment_measurement_created_at ON sentiment_measurement(created_at);
CREATE INDEX idx_sentiment_measurement_language_code ON sentiment_measurement(language_code);
CREATE INDEX idx_sentiment_measurement_vpn_country ON sentiment_measurement(vpn_country);

-- Tabela z pojedynczymi wystąpieniami sentymentu
CREATE TABLE IF NOT EXISTS sentiments_sniff (
    id SERIAL PRIMARY KEY,
    measurement_id INTEGER NOT NULL REFERENCES sentiment_measurement(id) ON DELETE CASCADE,
    region VARCHAR(200),  -- Nazwa regionu w kraju (np. "Ontario", "British Columbia")
    occurrence_time TIMESTAMPTZ NOT NULL,  -- Dokładny czas wystąpienia zapytania w Google Trends
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_sentiments_sniff_measurement FOREIGN KEY (measurement_id) REFERENCES sentiment_measurement(id) ON DELETE CASCADE
);

COMMENT ON TABLE sentiments_sniff IS 'Pojedyncze wystąpienia sentymentu - jeden rekord na każdy timestamp z wartością > 0';
COMMENT ON COLUMN sentiments_sniff.measurement_id IS 'ID pomiaru z sentiment_measurement';
COMMENT ON COLUMN sentiments_sniff.region IS 'Nazwa regionu w kraju gdzie wystąpiła fraza';
COMMENT ON COLUMN sentiments_sniff.occurrence_time IS 'Dokładny czas wystąpienia zapytania w Google Trends';

-- Indeksy
CREATE INDEX idx_sentiments_sniff_measurement_id ON sentiments_sniff(measurement_id);
CREATE INDEX idx_sentiments_sniff_occurrence_time ON sentiments_sniff(occurrence_time);
CREATE INDEX idx_sentiments_sniff_region ON sentiments_sniff(region);

-- Trigger do automatycznej aktualizacji updated_at
CREATE TRIGGER update_sentiment_measurement_updated_at
BEFORE UPDATE ON sentiment_measurement
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

