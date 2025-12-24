-- Migration: 004_gdelt_sentiment_unique_constraint
-- Opis: Dodanie unique constraint dla gdelt_sentiment (timestamp, region, query, resolution)
-- Data: 2024-12-24
-- Autor: trends-sniffer

-- =============================================================================
-- DODANIE UNIQUE CONSTRAINT
-- =============================================================================

-- Usuń duplikaty przed dodaniem constraint (jeśli istnieją)
-- Znajdź duplikaty i zostaw tylko najnowszy rekord
DELETE FROM gdelt_sentiment
WHERE id NOT IN (
    SELECT DISTINCT ON (timestamp, region, query, resolution) id
    FROM gdelt_sentiment
    ORDER BY timestamp, region, query, resolution, created_at DESC
);

-- Dodaj unique constraint
ALTER TABLE gdelt_sentiment 
    ADD CONSTRAINT uq_gdelt_sentiment 
    UNIQUE (timestamp, region, query, resolution);

-- Komentarz
COMMENT ON CONSTRAINT uq_gdelt_sentiment ON gdelt_sentiment IS 
    'Unique constraint: jeden rekord na kombinację (timestamp, region, query, resolution)';

