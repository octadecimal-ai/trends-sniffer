-- Migration: 008_rename_more_tables_with_prefixes
-- ==================================================
-- Zmiana nazw tabel aby miały prefix wskazujący źródło danych.
-- 
-- Zmiany:
-- - sentiment_measurement → google_trends_sentiment_measurement (Google Trends)
-- - sentiments_sniff → google_trends_sentiments_sniff (Google Trends)
-- - sentiment_scores → aggregated_sentiment_scores (agregowana z różnych źródeł)
-- - fear_greed_index → alternative_me_fear_greed_index (alternative.me)
-- - economic_calendar → manual_economic_calendar (manual/static)
-- - btc_premium_data → imf_btc_premium_data (IMF)

-- ============================================================================
-- RENAME: sentiment_measurement → google_trends_sentiment_measurement
-- ============================================================================

ALTER TABLE IF EXISTS sentiment_measurement 
    RENAME TO google_trends_sentiment_measurement;

-- Zmień nazwy indeksów
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiment_measurement_phrase_id') THEN
        ALTER INDEX idx_sentiment_measurement_phrase_id 
            RENAME TO idx_google_trends_sentiment_measurement_phrase_id;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiment_measurement_country_id') THEN
        ALTER INDEX idx_sentiment_measurement_country_id 
            RENAME TO idx_google_trends_sentiment_measurement_country_id;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiment_measurement_created_at') THEN
        ALTER INDEX idx_sentiment_measurement_created_at 
            RENAME TO idx_google_trends_sentiment_measurement_created_at;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiment_measurement_language_code') THEN
        ALTER INDEX idx_sentiment_measurement_language_code 
            RENAME TO idx_google_trends_sentiment_measurement_language_code;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiment_measurement_vpn_country') THEN
        ALTER INDEX idx_sentiment_measurement_vpn_country 
            RENAME TO idx_google_trends_sentiment_measurement_vpn_country;
    END IF;
END $$;

-- Zmień nazwy foreign key constraints
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sentiment_measurement_phrase') THEN
        ALTER TABLE google_trends_sentiment_measurement
            RENAME CONSTRAINT fk_sentiment_measurement_phrase 
            TO fk_google_trends_sentiment_measurement_phrase;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sentiment_measurement_country') THEN
        ALTER TABLE google_trends_sentiment_measurement
            RENAME CONSTRAINT fk_sentiment_measurement_country 
            TO fk_google_trends_sentiment_measurement_country;
    END IF;
END $$;

COMMENT ON TABLE google_trends_sentiment_measurement IS 
    'Główna tabela z danymi pomiaru sentymentu Google Trends - zapisuje wszystkie zapytania, nawet bez wystąpień';

-- ============================================================================
-- RENAME: sentiments_sniff → google_trends_sentiments_sniff
-- ============================================================================

ALTER TABLE IF EXISTS sentiments_sniff 
    RENAME TO google_trends_sentiments_sniff;

-- Zmień nazwy indeksów
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiments_sniff_measurement_id') THEN
        ALTER INDEX idx_sentiments_sniff_measurement_id 
            RENAME TO idx_google_trends_sentiments_sniff_measurement_id;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiments_sniff_occurrence_time') THEN
        ALTER INDEX idx_sentiments_sniff_occurrence_time 
            RENAME TO idx_google_trends_sentiments_sniff_occurrence_time;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_sentiments_sniff_region') THEN
        ALTER INDEX idx_sentiments_sniff_region 
            RENAME TO idx_google_trends_sentiments_sniff_region;
    END IF;
END $$;

-- Zmień nazwy foreign key constraints
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sentiments_sniff_measurement') THEN
        ALTER TABLE google_trends_sentiments_sniff
            RENAME CONSTRAINT fk_sentiments_sniff_measurement 
            TO fk_google_trends_sentiments_sniff_measurement;
    END IF;
END $$;

-- Aktualizuj foreign key w sentiments_sniff, który teraz wskazuje na google_trends_sentiment_measurement
-- (PostgreSQL automatycznie zaktualizuje referencje, ale musimy zaktualizować constraint name)
DO $$
BEGIN
    -- Sprawdź czy istnieje constraint z referencją do sentiment_measurement
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conrelid = 'google_trends_sentiments_sniff'::regclass 
        AND confrelid = 'google_trends_sentiment_measurement'::regclass
    ) THEN
        -- Constraint zostanie automatycznie zaktualizowany przez PostgreSQL
        -- gdy zmienimy nazwę tabeli referencyjnej
        NULL;
    END IF;
END $$;

COMMENT ON TABLE google_trends_sentiments_sniff IS 
    'Pojedyncze wystąpienia sentymentu Google Trends - jeden rekord na każdy timestamp z wartością > 0';

-- ============================================================================
-- RENAME: sentiment_scores → aggregated_sentiment_scores
-- ============================================================================

ALTER TABLE IF EXISTS sentiment_scores 
    RENAME TO aggregated_sentiment_scores;

-- Zmień nazwy indeksów
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_sentiment_lookup') THEN
        ALTER INDEX ix_sentiment_lookup 
            RENAME TO ix_aggregated_sentiment_scores_lookup;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_sentiment_scores_timestamp') THEN
        ALTER INDEX ix_sentiment_scores_timestamp 
            RENAME TO ix_aggregated_sentiment_scores_timestamp;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_sentiment_scores_symbol') THEN
        ALTER INDEX ix_sentiment_scores_symbol 
            RENAME TO ix_aggregated_sentiment_scores_symbol;
    END IF;
END $$;

COMMENT ON TABLE aggregated_sentiment_scores IS 
    'Agregowane wyniki analizy sentymentu z różnych źródeł (twitter, reddit, news, llm)';

-- ============================================================================
-- RENAME: fear_greed_index → alternative_me_fear_greed_index
-- ============================================================================

ALTER TABLE IF EXISTS fear_greed_index 
    RENAME TO alternative_me_fear_greed_index;

-- Zmień nazwy indeksów
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_fear_greed_timestamp') THEN
        ALTER INDEX ix_fear_greed_timestamp 
            RENAME TO ix_alternative_me_fear_greed_index_timestamp;
    END IF;
END $$;

-- Zmień nazwy unique constraints
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_fear_greed') THEN
        ALTER TABLE alternative_me_fear_greed_index
            RENAME CONSTRAINT uq_fear_greed 
            TO uq_alternative_me_fear_greed_index;
    END IF;
END $$;

COMMENT ON TABLE alternative_me_fear_greed_index IS 
    'Crypto Fear & Greed Index z alternative.me (0-100, aktualizowany raz dziennie)';

-- ============================================================================
-- RENAME: economic_calendar → manual_economic_calendar
-- ============================================================================

ALTER TABLE IF EXISTS economic_calendar 
    RENAME TO manual_economic_calendar;

-- Zmień nazwy indeksów
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_economic_calendar_event_date') THEN
        ALTER INDEX ix_economic_calendar_event_date 
            RENAME TO ix_manual_economic_calendar_event_date;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_economic_calendar_event_type') THEN
        ALTER INDEX ix_economic_calendar_event_type 
            RENAME TO ix_manual_economic_calendar_event_type;
    END IF;
END $$;

-- Zmień nazwy unique constraints
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_economic_event') THEN
        ALTER TABLE manual_economic_calendar
            RENAME CONSTRAINT uq_economic_event 
            TO uq_manual_economic_calendar_event;
    END IF;
END $$;

COMMENT ON TABLE manual_economic_calendar IS 
    'Kalendarz wydarzeń ekonomicznych (FOMC, CPI, NFP, GDP) - dane manual/static';

-- ============================================================================
-- RENAME: btc_premium_data → imf_btc_premium_data
-- ============================================================================

ALTER TABLE IF EXISTS btc_premium_data 
    RENAME TO imf_btc_premium_data;

-- Zmień nazwy indeksów
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_btc_premium_country') THEN
        ALTER INDEX idx_btc_premium_country 
            RENAME TO idx_imf_btc_premium_data_country;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_btc_premium_date') THEN
        ALTER INDEX idx_btc_premium_date 
            RENAME TO idx_imf_btc_premium_data_date;
    END IF;
END $$;

COMMENT ON TABLE imf_btc_premium_data IS 
    'Premia kursu BTC na lokalnych rynkach (IMF WPCPER)';

