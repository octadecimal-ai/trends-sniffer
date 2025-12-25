-- Migration: 005_sentiment_propagation
-- ==================================================
-- Tabela do przechowywania metryk propagacji sentymentu między regionami.
-- 
-- UWAGA: Tabela została przemianowana na google_trends_sentiment_propagation w migracji 007.
-- Ta migracja jest zachowana dla historii, ale użyj migracji 007 do aktualizacji.
-- 
-- Analizuje jak sentyment propaguje się przez strefy czasowe:
-- - APAC (Asia-Pacific): UTC+8 to UTC+12
-- - EU (Europe): UTC+0 to UTC+3
-- - US (Americas): UTC-8 to UTC-3
--
-- Metryki:
-- - Korelacje z opóźnieniem czasowym (lagged correlations)
-- - Prędkość propagacji (propagation speed)
-- - Amplifikacja/tłumienie sentymentu
-- - Leading region (region wiodący)
-- - Global Activity Index (GAI)

-- ============================================================================
-- TABELA: sentiment_propagation
-- ============================================================================

CREATE TABLE IF NOT EXISTS sentiment_propagation (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Korelacje z opóźnieniem czasowym (lagged correlations)
    -- Wartości: -1.0 do 1.0
    asia_to_eu_corr DECIMAL(5, 4),      -- Korelacja: Asia → EU (z lag 4h)
    eu_to_us_corr DECIMAL(5, 4),        -- Korelacja: EU → US (z lag 4h)
    us_to_asia_corr DECIMAL(5, 4),     -- Korelacja: US → Asia (overnight, lag 12h)
    
    -- Prędkość propagacji (godziny)
    -- Jak szybko sentyment propaguje się między regionami
    propagation_speed_hours DECIMAL(4, 2),  -- Średnia prędkość propagacji
    
    -- Amplifikacja lub tłumienie
    -- Wartość > 1.0 = amplifikacja, < 1.0 = tłumienie
    asia_to_eu_amplification DECIMAL(5, 4),  -- EU_sentiment / Asia_sentiment
    eu_to_us_amplification DECIMAL(5, 4),    -- US_sentiment / EU_sentiment
    us_to_asia_amplification DECIMAL(5, 4),   -- Asia_sentiment / US_sentiment (overnight)
    
    -- Leading region (region wiodący w danym momencie)
    -- Wartości: 'APAC', 'EU', 'US', 'MIXED', 'NONE'
    leading_region VARCHAR(10),
    
    -- Global Activity Index (GAI)
    -- Agregowany wskaźnik aktywności we wszystkich regionach
    gai_score DECIMAL(10, 4),
    
    -- Sentyment per region (surowy)
    asia_sentiment DECIMAL(10, 4),      -- Średni sentyment APAC
    eu_sentiment DECIMAL(10, 4),        -- Średni sentyment EU
    us_sentiment DECIMAL(10, 4),        -- Średni sentyment US
    
    -- Liczba pomiarów per region
    asia_measurements_count INTEGER DEFAULT 0,
    eu_measurements_count INTEGER DEFAULT 0,
    us_measurements_count INTEGER DEFAULT 0,
    
    -- Metadane
    calculation_window_hours INTEGER DEFAULT 24,  -- Okno czasowe użyte do obliczeń
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Unikalny constraint na timestamp
ALTER TABLE sentiment_propagation 
    ADD CONSTRAINT sentiment_propagation_timestamp_key UNIQUE (timestamp);

-- Indeksy
CREATE INDEX IF NOT EXISTS ix_sentiment_propagation_timestamp 
    ON sentiment_propagation (timestamp);

CREATE INDEX IF NOT EXISTS ix_sentiment_propagation_leading_region 
    ON sentiment_propagation (leading_region, timestamp);

-- TimescaleDB hypertable (jeśli dostępne)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('sentiment_propagation', 'timestamp', 
                                  chunk_time_interval => INTERVAL '1 day',
                                  if_not_exists => TRUE);
    END IF;
END $$;

-- Komentarze
COMMENT ON TABLE sentiment_propagation IS 
    'Metryki propagacji sentymentu między regionami (APAC, EU, US) w czasie';

COMMENT ON COLUMN sentiment_propagation.timestamp IS 
    'Timestamp dla którego obliczono metryki propagacji';

COMMENT ON COLUMN sentiment_propagation.asia_to_eu_corr IS 
    'Korelacja sentymentu Asia → EU z opóźnieniem 4h (wartość: -1.0 do 1.0)';

COMMENT ON COLUMN sentiment_propagation.eu_to_us_corr IS 
    'Korelacja sentymentu EU → US z opóźnieniem 4h (wartość: -1.0 do 1.0)';

COMMENT ON COLUMN sentiment_propagation.us_to_asia_corr IS 
    'Korelacja sentymentu US → Asia (overnight) z opóźnieniem 12h (wartość: -1.0 do 1.0)';

COMMENT ON COLUMN sentiment_propagation.propagation_speed_hours IS 
    'Średnia prędkość propagacji sentymentu między regionami (w godzinach)';

COMMENT ON COLUMN sentiment_propagation.leading_region IS 
    'Region wiodący w danym momencie (APAC, EU, US, MIXED, NONE)';

COMMENT ON COLUMN sentiment_propagation.gai_score IS 
    'Global Activity Index - agregowany wskaźnik aktywności we wszystkich regionach';

-- ============================================================================
-- FUNKCJA POMOCNICZA: map_country_to_propagation_region
-- ============================================================================
-- Mapuje kod kraju na region propagacji (APAC, EU, US) na podstawie UTC offset

CREATE OR REPLACE FUNCTION map_country_to_propagation_region(
    utc_offset_minutes INTEGER
) RETURNS VARCHAR(10) AS $$
BEGIN
    -- APAC: UTC+8 to UTC+12 (480 do 720 minut)
    IF utc_offset_minutes >= 480 AND utc_offset_minutes <= 720 THEN
        RETURN 'APAC';
    END IF;
    
    -- EU: UTC+0 to UTC+3 (0 do 180 minut)
    IF utc_offset_minutes >= 0 AND utc_offset_minutes <= 180 THEN
        RETURN 'EU';
    END IF;
    
    -- US: UTC-8 to UTC-3 (-480 do -180 minut)
    IF utc_offset_minutes >= -480 AND utc_offset_minutes <= -180 THEN
        RETURN 'US';
    END IF;
    
    -- Dla innych offsetów zwróć NULL (nie mapujemy)
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION map_country_to_propagation_region IS 
    'Mapuje UTC offset kraju na region propagacji (APAC, EU, US)';

