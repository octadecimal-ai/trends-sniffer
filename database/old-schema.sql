-- ============================================================================
-- TRENDS SNIFFER - Struktura Bazy Danych
-- ============================================================================
-- Baza danych do przechowywania danych o sentymencie BTC na świecie
-- Wersja: 1.0.0
-- Data utworzenia: 2024-12-22
-- ============================================================================

-- Rozszerzenia
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- SCHEMAT: Tabele słownikowe (справочники)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: continents - Kontynenty
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS continents (
    id SERIAL PRIMARY KEY,
    code VARCHAR(2) NOT NULL UNIQUE,           -- AF, AS, EU, NA, SA, OC, AN
    name_en VARCHAR(50) NOT NULL,
    name_pl VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE continents IS 'Słownik kontynentów';

-- ----------------------------------------------------------------------------
-- Tabela: regions - Regiony strategiczne dla analizy BTC
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,           -- north_america, europe, asia_pacific, etc.
    name_en VARCHAR(100) NOT NULL,
    name_pl VARCHAR(100),
    description_en TEXT,
    description_pl TEXT,
    priority_tier SMALLINT DEFAULT 3,           -- 1=najwyższy, 4=najniższy
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE regions IS 'Regiony strategiczne dla analizy trendów BTC';

-- ----------------------------------------------------------------------------
-- Tabela: income_levels - Poziomy dochodów (World Bank classification)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS income_levels (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,           -- HIC, UMC, LMC, LIC
    name_en VARCHAR(100) NOT NULL,
    name_pl VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE income_levels IS 'Poziomy dochodów wg klasyfikacji World Bank';

-- ----------------------------------------------------------------------------
-- Tabela: indicator_types - Typy wskaźników
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicator_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,           -- economic, social, crypto, geographic
    name_en VARCHAR(100) NOT NULL,
    name_pl VARCHAR(100),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE indicator_types IS 'Typy wskaźników (ekonomiczne, społeczne, krypto, geograficzne)';

-- ============================================================================
-- SCHEMAT: Tabele główne
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: countries - Kraje
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    iso2_code VARCHAR(2) NOT NULL UNIQUE,       -- PL, US, DE
    iso3_code VARCHAR(3) UNIQUE,                -- POL, USA, DEU
    name_en VARCHAR(100) NOT NULL,
    name_pl VARCHAR(100),
    continent_id INTEGER REFERENCES continents(id),
    region_id INTEGER REFERENCES regions(id),
    income_level_id INTEGER REFERENCES income_levels(id),
    capital VARCHAR(100),
    currency_code VARCHAR(3),
    currency_name VARCHAR(50),
    languages TEXT,                              -- Kody języków oddzielone przecinkami
    population BIGINT,
    area_km2 DECIMAL(15,2),
    population_density DECIMAL(10,2),            -- Obliczane: population / area_km2
    
    -- Dane geograficzne
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    timezone VARCHAR(50),
    utc_offset INTEGER,                          -- Offset w minutach
    bbox_north DECIMAL(10,6),
    bbox_south DECIMAL(10,6),
    bbox_east DECIMAL(10,6),
    bbox_west DECIMAL(10,6),
    
    -- Priorytet monitoringu
    monitoring_priority SMALLINT DEFAULT 3,      -- 1=najwyższy (Tier 1), 4=najniższy
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadane
    geonames_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE countries IS 'Kraje z danymi geograficznymi i klasyfikacją';

CREATE INDEX idx_countries_iso2 ON countries(iso2_code);
CREATE INDEX idx_countries_iso3 ON countries(iso3_code);
CREATE INDEX idx_countries_priority ON countries(monitoring_priority);
CREATE INDEX idx_countries_region ON countries(region_id);

-- ----------------------------------------------------------------------------
-- Tabela: indicators - Definicje wskaźników
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicators (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,            -- SP.POP.TOTL, BIT_SHD_PT, etc.
    name_en VARCHAR(200) NOT NULL,
    name_pl VARCHAR(200),
    description TEXT,
    indicator_type_id INTEGER REFERENCES indicator_types(id),
    source VARCHAR(50),                          -- world_bank, imf, geonames, google_trends
    unit VARCHAR(50),                            -- %, USD, LCU/USD, etc.
    frequency VARCHAR(20),                       -- hourly, daily, monthly, yearly
    is_higher_better BOOLEAN,                    -- NULL = neutral, TRUE = wyższa wartość lepsza
    sentiment_weight DECIMAL(5,4),               -- Waga w modelu sentymentu (0.0000-1.0000)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE indicators IS 'Definicje wszystkich wskaźników używanych w analizie';

CREATE INDEX idx_indicators_code ON indicators(code);
CREATE INDEX idx_indicators_source ON indicators(source);
CREATE INDEX idx_indicators_type ON indicators(indicator_type_id);

-- ----------------------------------------------------------------------------
-- Tabela: keywords - Słowa kluczowe do monitoringu Google Trends
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    language_code VARCHAR(5) DEFAULT 'en',       -- en, pl, jp, kr, ru, etc.
    sentiment_type VARCHAR(20) NOT NULL,         -- positive, negative, neutral
    category VARCHAR(50),                        -- buy, sell, fomo, fud, price, etc.
    weight DECIMAL(5,4) DEFAULT 1.0000,          -- Waga słowa w obliczeniach
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(keyword, language_code)
);

COMMENT ON TABLE keywords IS 'Słowa kluczowe do monitoringu trendów Google';

CREATE INDEX idx_keywords_language ON keywords(language_code);
CREATE INDEX idx_keywords_sentiment ON keywords(sentiment_type);
CREATE INDEX idx_keywords_category ON keywords(category);

-- ============================================================================
-- SCHEMAT: Tabele danych czasowych (time-series)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: country_indicators - Wskaźniki krajów (dane statyczne/miesięczne)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS country_indicators (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    indicator_id INTEGER NOT NULL REFERENCES indicators(id),
    period_date DATE NOT NULL,                   -- Data okresu (YYYY-MM-DD)
    period_type VARCHAR(10) DEFAULT 'monthly',   -- daily, monthly, yearly
    value DECIMAL(20,6),
    value_text VARCHAR(100),                     -- Dla wartości tekstowych
    source VARCHAR(50),                          -- world_bank, imf, manual
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(country_id, indicator_id, period_date, period_type)
);

COMMENT ON TABLE country_indicators IS 'Wartości wskaźników dla krajów (dane statyczne/miesięczne)';

CREATE INDEX idx_country_indicators_country ON country_indicators(country_id);
CREATE INDEX idx_country_indicators_indicator ON country_indicators(indicator_id);
CREATE INDEX idx_country_indicators_date ON country_indicators(period_date);
CREATE INDEX idx_country_indicators_lookup ON country_indicators(country_id, indicator_id, period_date);

-- ----------------------------------------------------------------------------
-- Tabela: hashrate_data - Dane o hashrate BTC per kraj
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hashrate_data (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    recorded_at TIMESTAMPTZ NOT NULL,
    hashrate_share_percent DECIMAL(10,6),        -- Udział w globalnym hashrate (%)
    hashrate_absolute DECIMAL(20,2),             -- Absolutny hashrate (TH/s)
    source VARCHAR(50) DEFAULT 'cbeci',          -- cbeci, manual, etc.
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(country_id, recorded_at, source)
);

COMMENT ON TABLE hashrate_data IS 'Dane o udziale krajów w globalnym hashrate BTC';

CREATE INDEX idx_hashrate_country ON hashrate_data(country_id);
CREATE INDEX idx_hashrate_date ON hashrate_data(recorded_at);

-- ----------------------------------------------------------------------------
-- Tabela: btc_premium_data - Premia BTC (IMF WPCPER)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS btc_premium_data (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    period_date DATE NOT NULL,                   -- Data okresu
    premium_percent DECIMAL(10,6),               -- Premia BTC (%)
    parallel_rate DECIMAL(20,6),                 -- Kurs równoległy (LCU/USD)
    source VARCHAR(50) DEFAULT 'imf',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(country_id, period_date, source)
);

COMMENT ON TABLE btc_premium_data IS 'Premia kursu BTC na lokalnych rynkach (IMF WPCPER)';

CREATE INDEX idx_btc_premium_country ON btc_premium_data(country_id);
CREATE INDEX idx_btc_premium_date ON btc_premium_data(period_date);

-- ----------------------------------------------------------------------------
-- Tabela: trend_snapshots - Snapshoty trendów Google (co 1h)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trend_snapshots (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    snapshot_at TIMESTAMPTZ NOT NULL,            -- Czas snapshotu
    timeframe VARCHAR(20) DEFAULT 'now 1-H',     -- Zakres czasowy Google Trends
    
    -- Wyniki zagregowane
    total_interest DECIMAL(10,4),                -- Suma zainteresowania wszystkimi słowami
    positive_score DECIMAL(10,4),                -- Wynik dla słów pozytywnych
    negative_score DECIMAL(10,4),                -- Wynik dla słów negatywnych
    neutral_score DECIMAL(10,4),                 -- Wynik dla słów neutralnych
    sentiment_ratio DECIMAL(10,6),               -- positive / (positive + negative)
    
    -- Metadane
    keywords_count INTEGER,                      -- Liczba przeszukanych słów
    api_success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE trend_snapshots IS 'Snapshoty trendów Google Trends (co 1h)';

CREATE INDEX idx_trend_snapshots_country ON trend_snapshots(country_id);
CREATE INDEX idx_trend_snapshots_time ON trend_snapshots(snapshot_at);
CREATE INDEX idx_trend_snapshots_lookup ON trend_snapshots(country_id, snapshot_at);

-- ----------------------------------------------------------------------------
-- Tabela: trend_keyword_results - Wyniki dla poszczególnych słów kluczowych
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trend_keyword_results (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES trend_snapshots(id) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id),
    interest_value INTEGER,                      -- Wartość zainteresowania (0-100)
    is_partial BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE trend_keyword_results IS 'Wyniki dla poszczególnych słów kluczowych w snapshocie';

CREATE INDEX idx_trend_keyword_snapshot ON trend_keyword_results(snapshot_id);
CREATE INDEX idx_trend_keyword_keyword ON trend_keyword_results(keyword_id);

-- ============================================================================
-- SCHEMAT: Tabele sentymentu (wyniki analizy)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: sentiment_scores - Obliczony sentyment dla kraju
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    calculated_at TIMESTAMPTZ NOT NULL,
    
    -- Składowe sentymentu (wagi z dokumentu analizy)
    google_trends_score DECIMAL(10,6),           -- Waga: 0.35
    btc_premium_score DECIMAL(10,6),             -- Waga: 0.20
    economic_stability_score DECIMAL(10,6),      -- Waga: 0.15
    hashrate_score DECIMAL(10,6),                -- Waga: 0.10
    internet_access_score DECIMAL(10,6),         -- Waga: 0.10
    inflation_score DECIMAL(10,6),               -- Waga: 0.10
    
    -- Wynik końcowy
    total_score DECIMAL(10,6),                   -- Suma ważona (-100 do +100)
    sentiment_label VARCHAR(20),                 -- bullish, bearish, neutral
    confidence DECIMAL(5,4),                     -- Pewność wyniku (0-1)
    
    -- Źródła danych użyte do obliczeń
    trend_snapshot_id BIGINT REFERENCES trend_snapshots(id),
    btc_premium_id BIGINT REFERENCES btc_premium_data(id),
    hashrate_id BIGINT REFERENCES hashrate_data(id),
    
    -- Metadane
    model_version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(country_id, calculated_at, model_version)
);

COMMENT ON TABLE sentiment_scores IS 'Obliczony sentyment dla krajów';

CREATE INDEX idx_sentiment_country ON sentiment_scores(country_id);
CREATE INDEX idx_sentiment_time ON sentiment_scores(calculated_at);
CREATE INDEX idx_sentiment_label ON sentiment_scores(sentiment_label);
CREATE INDEX idx_sentiment_lookup ON sentiment_scores(country_id, calculated_at);

-- ----------------------------------------------------------------------------
-- Tabela: sentiment_alerts - Alerty o znaczących zmianach sentymentu
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_alerts (
    id BIGSERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    alert_type VARCHAR(50) NOT NULL,             -- spike, drop, threshold_breach, etc.
    severity VARCHAR(20) DEFAULT 'medium',       -- low, medium, high, critical
    
    -- Szczegóły alertu
    current_score DECIMAL(10,6),
    previous_score DECIMAL(10,6),
    change_percent DECIMAL(10,4),
    threshold_value DECIMAL(10,6),
    message TEXT,
    
    -- Status
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(100),
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sentiment_alerts IS 'Alerty o znaczących zmianach sentymentu';

CREATE INDEX idx_alerts_country ON sentiment_alerts(country_id);
CREATE INDEX idx_alerts_type ON sentiment_alerts(alert_type);
CREATE INDEX idx_alerts_severity ON sentiment_alerts(severity);
CREATE INDEX idx_alerts_unacknowledged ON sentiment_alerts(is_acknowledged) WHERE is_acknowledged = FALSE;

-- ============================================================================
-- SCHEMAT: Tabele konfiguracyjne
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: config - Konfiguracja systemu
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',     -- string, integer, decimal, boolean, json
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE config IS 'Konfiguracja systemu';

-- ----------------------------------------------------------------------------
-- Tabela: data_refresh_log - Log odświeżania danych
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_refresh_log (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,                 -- google_trends, world_bank, imf, geonames
    operation VARCHAR(50) NOT NULL,              -- full_refresh, incremental, single_country
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'running',        -- running, success, failed, partial
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    details JSONB
);

COMMENT ON TABLE data_refresh_log IS 'Log operacji odświeżania danych';

CREATE INDEX idx_refresh_log_source ON data_refresh_log(source);
CREATE INDEX idx_refresh_log_status ON data_refresh_log(status);
CREATE INDEX idx_refresh_log_time ON data_refresh_log(started_at);

-- ============================================================================
-- FUNKCJE I TRIGGERY
-- ============================================================================

-- Funkcja do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggery dla updated_at
CREATE TRIGGER update_countries_updated_at
    BEFORE UPDATE ON countries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_indicators_updated_at
    BEFORE UPDATE ON indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_keywords_updated_at
    BEFORE UPDATE ON keywords
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_regions_updated_at
    BEFORE UPDATE ON regions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at
    BEFORE UPDATE ON config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Funkcja do obliczania gęstości zaludnienia
CREATE OR REPLACE FUNCTION calculate_population_density()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.population IS NOT NULL AND NEW.area_km2 IS NOT NULL AND NEW.area_km2 > 0 THEN
        NEW.population_density = NEW.population / NEW.area_km2;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_countries_density
    BEFORE INSERT OR UPDATE ON countries
    FOR EACH ROW EXECUTE FUNCTION calculate_population_density();

-- ============================================================================
-- WIDOKI
-- ============================================================================

-- Widok: Aktualny sentyment dla wszystkich krajów
CREATE OR REPLACE VIEW v_current_sentiment AS
SELECT 
    c.iso2_code,
    c.name_en AS country_name,
    r.name_en AS region_name,
    c.monitoring_priority,
    ss.total_score,
    ss.sentiment_label,
    ss.google_trends_score,
    ss.btc_premium_score,
    ss.calculated_at,
    ss.confidence
FROM countries c
LEFT JOIN regions r ON c.region_id = r.id
LEFT JOIN LATERAL (
    SELECT * FROM aggregated_sentiment_scores 
    WHERE country_id = c.id 
    ORDER BY calculated_at DESC 
    LIMIT 1
) ss ON TRUE
WHERE c.is_active = TRUE
ORDER BY c.monitoring_priority, ss.total_score DESC NULLS LAST;

-- Widok: Kraje z najwyższą premią BTC
CREATE OR REPLACE VIEW v_btc_premium_ranking AS
SELECT 
    c.iso2_code,
    c.name_en AS country_name,
    bp.premium_percent,
    bp.parallel_rate,
    bp.period_date
FROM imf_btc_premium_data bp
JOIN countries c ON bp.country_id = c.id
WHERE bp.period_date = (SELECT MAX(period_date) FROM imf_btc_premium_data)
ORDER BY bp.premium_percent DESC NULLS LAST;

-- Widok: Kraje z najwyższym hashrate
CREATE OR REPLACE VIEW v_hashrate_ranking AS
SELECT 
    c.iso2_code,
    c.name_en AS country_name,
    hd.hashrate_share_percent,
    hd.recorded_at
FROM hashrate_data hd
JOIN countries c ON hd.country_id = c.id
WHERE hd.recorded_at = (SELECT MAX(recorded_at) FROM hashrate_data)
ORDER BY hd.hashrate_share_percent DESC NULLS LAST;

-- ============================================================================
-- DANE POCZĄTKOWE
-- ============================================================================

-- Kontynenty
INSERT INTO continents (code, name_en, name_pl) VALUES
    ('AF', 'Africa', 'Afryka'),
    ('AN', 'Antarctica', 'Antarktyda'),
    ('AS', 'Asia', 'Azja'),
    ('EU', 'Europe', 'Europa'),
    ('NA', 'North America', 'Ameryka Północna'),
    ('OC', 'Oceania', 'Oceania'),
    ('SA', 'South America', 'Ameryka Południowa')
ON CONFLICT (code) DO NOTHING;

-- Poziomy dochodów
INSERT INTO income_levels (code, name_en, name_pl, description) VALUES
    ('HIC', 'High Income Countries', 'Kraje o wysokich dochodach', 'GNI per capita > $13,845'),
    ('UMC', 'Upper Middle Income', 'Kraje o średnio-wysokich dochodach', 'GNI per capita $4,466 - $13,845'),
    ('LMC', 'Lower Middle Income', 'Kraje o średnio-niskich dochodach', 'GNI per capita $1,136 - $4,465'),
    ('LIC', 'Low Income Countries', 'Kraje o niskich dochodach', 'GNI per capita < $1,136')
ON CONFLICT (code) DO NOTHING;

-- Typy wskaźników
INSERT INTO indicator_types (code, name_en, name_pl, description) VALUES
    ('economic', 'Economic Indicators', 'Wskaźniki ekonomiczne', 'PKB, inflacja, bezrobocie, itp.'),
    ('social', 'Social Indicators', 'Wskaźniki społeczne', 'Populacja, urbanizacja, edukacja, itp.'),
    ('technological', 'Technological Indicators', 'Wskaźniki technologiczne', 'Dostęp do internetu, telefonia, itp.'),
    ('crypto', 'Cryptocurrency Indicators', 'Wskaźniki kryptowalutowe', 'Premia BTC, hashrate, itp.'),
    ('geographic', 'Geographic Data', 'Dane geograficzne', 'Położenie, strefa czasowa, itp.'),
    ('sentiment', 'Sentiment Indicators', 'Wskaźniki sentymentu', 'Trendy wyszukiwań, itp.')
ON CONFLICT (code) DO NOTHING;

-- Regiony strategiczne
INSERT INTO regions (code, name_en, name_pl, description_en, priority_tier) VALUES
    ('north_america', 'North America', 'Ameryka Północna', 'Main price discovery point, largest USD liquidity', 1),
    ('asia_pacific', 'Asia-Pacific', 'Azja-Pacyfik', 'Largest user base, high adoption', 1),
    ('europe', 'Europe', 'Europa', 'Capital, regulations, financial infrastructure', 2),
    ('china', 'China', 'Chiny', 'Policy influence, mining infrastructure', 2),
    ('middle_east', 'Middle East', 'Bliski Wschód', 'Growing capital hub, financial centers', 3),
    ('emerging_markets', 'Emerging Crypto Markets', 'Rynki wschodzące', 'High adoption, inflation hedge', 2),
    ('offshore_hubs', 'Offshore Exchange Hubs', 'Huby giełd offshore', 'Exchange jurisdictions', 4)
ON CONFLICT (code) DO NOTHING;

-- Podstawowe wskaźniki
INSERT INTO indicators (code, name_en, name_pl, source, unit, frequency, sentiment_weight, indicator_type_id) VALUES
    ('SP.POP.TOTL', 'Total Population', 'Populacja całkowita', 'world_bank', 'persons', 'yearly', 0.05, (SELECT id FROM indicator_types WHERE code = 'social')),
    ('NY.GDP.MKTP.CD', 'GDP (current USD)', 'PKB (bieżące USD)', 'world_bank', 'USD', 'yearly', 0.05, (SELECT id FROM indicator_types WHERE code = 'economic')),
    ('NY.GDP.PCAP.CD', 'GDP per capita (current USD)', 'PKB per capita (bieżące USD)', 'world_bank', 'USD', 'yearly', 0.05, (SELECT id FROM indicator_types WHERE code = 'economic')),
    ('FP.CPI.TOTL.ZG', 'Inflation (CPI)', 'Inflacja (CPI)', 'world_bank', '%', 'yearly', 0.10, (SELECT id FROM indicator_types WHERE code = 'economic')),
    ('IT.NET.USER.ZS', 'Internet Users (% of population)', 'Użytkownicy Internetu (% populacji)', 'world_bank', '%', 'yearly', 0.10, (SELECT id FROM indicator_types WHERE code = 'technological')),
    ('SL.UEM.TOTL.ZS', 'Unemployment Rate', 'Stopa bezrobocia', 'world_bank', '%', 'yearly', 0.05, (SELECT id FROM indicator_types WHERE code = 'economic')),
    ('BIT_SHD_PT', 'BTC Premium (%)', 'Premia BTC (%)', 'imf', '%', 'monthly', 0.20, (SELECT id FROM indicator_types WHERE code = 'crypto')),
    ('BIT_SHD_RT', 'BTC Parallel Rate', 'Kurs równoległy BTC', 'imf', 'LCU/USD', 'monthly', 0.05, (SELECT id FROM indicator_types WHERE code = 'crypto')),
    ('HASHRATE_SHARE', 'Hashrate Share', 'Udział w hashrate', 'cbeci', '%', 'monthly', 0.10, (SELECT id FROM indicator_types WHERE code = 'crypto')),
    ('GOOGLE_TRENDS', 'Google Trends Score', 'Wynik Google Trends', 'google_trends', 'score', 'hourly', 0.35, (SELECT id FROM indicator_types WHERE code = 'sentiment'))
ON CONFLICT (code) DO NOTHING;

-- Podstawowe słowa kluczowe (angielskie)
INSERT INTO keywords (keyword, language_code, sentiment_type, category, weight) VALUES
    -- Pozytywne
    ('buy bitcoin', 'en', 'positive', 'buy', 1.0),
    ('bitcoin investment', 'en', 'positive', 'invest', 0.9),
    ('bitcoin bull', 'en', 'positive', 'bullish', 1.0),
    ('btc moon', 'en', 'positive', 'fomo', 0.8),
    ('bitcoin etf', 'en', 'positive', 'adoption', 0.9),
    ('bitcoin rally', 'en', 'positive', 'bullish', 1.0),
    ('bitcoin all time high', 'en', 'positive', 'fomo', 1.0),
    
    -- Negatywne
    ('sell bitcoin', 'en', 'negative', 'sell', 1.0),
    ('bitcoin crash', 'en', 'negative', 'fear', 1.0),
    ('btc bear', 'en', 'negative', 'bearish', 1.0),
    ('bitcoin dead', 'en', 'negative', 'fud', 0.8),
    ('bitcoin ban', 'en', 'negative', 'regulation', 0.9),
    ('bitcoin scam', 'en', 'negative', 'fud', 0.8),
    ('bitcoin bubble', 'en', 'negative', 'fud', 0.7),
    
    -- Neutralne
    ('bitcoin price', 'en', 'neutral', 'price', 1.0),
    ('btc usd', 'en', 'neutral', 'price', 1.0),
    ('bitcoin news', 'en', 'neutral', 'info', 0.8),
    ('what is bitcoin', 'en', 'neutral', 'education', 0.5),
    ('bitcoin halving', 'en', 'neutral', 'technical', 0.7)
ON CONFLICT (keyword, language_code) DO NOTHING;

-- Słowa kluczowe polskie
INSERT INTO keywords (keyword, language_code, sentiment_type, category, weight) VALUES
    ('kup bitcoin', 'pl', 'positive', 'buy', 1.0),
    ('inwestycja bitcoin', 'pl', 'positive', 'invest', 0.9),
    ('bitcoin hossa', 'pl', 'positive', 'bullish', 1.0),
    ('sprzedaj bitcoin', 'pl', 'negative', 'sell', 1.0),
    ('bitcoin krach', 'pl', 'negative', 'fear', 1.0),
    ('cena bitcoin', 'pl', 'neutral', 'price', 1.0),
    ('kurs btc', 'pl', 'neutral', 'price', 1.0)
ON CONFLICT (keyword, language_code) DO NOTHING;

-- Konfiguracja domyślna
INSERT INTO config (key, value, value_type, description) VALUES
    ('sentiment.weight.google_trends', '0.35', 'decimal', 'Waga Google Trends w modelu sentymentu'),
    ('sentiment.weight.btc_premium', '0.20', 'decimal', 'Waga premii BTC w modelu sentymentu'),
    ('sentiment.weight.economic_stability', '0.15', 'decimal', 'Waga stabilności ekonomicznej'),
    ('sentiment.weight.hashrate', '0.10', 'decimal', 'Waga hashrate w modelu sentymentu'),
    ('sentiment.weight.internet_access', '0.10', 'decimal', 'Waga dostępu do internetu'),
    ('sentiment.weight.inflation', '0.10', 'decimal', 'Waga inflacji w modelu sentymentu'),
    ('trends.timeframe', 'now 1-H', 'string', 'Domyślny zakres czasowy dla Google Trends'),
    ('trends.refresh_interval_minutes', '60', 'integer', 'Interwał odświeżania trendów (minuty)'),
    ('alert.premium_threshold', '10.0', 'decimal', 'Próg alertu dla zmiany premii BTC (%)'),
    ('alert.sentiment_threshold', '15.0', 'decimal', 'Próg alertu dla zmiany sentymentu (%)')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- KONIEC SCHEMATU
-- ============================================================================

