-- ============================================================================
-- MIGRACJA: Dodanie tabeli timezones i zmiana kolumny timezone w countries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tabela: timezones - Strefy czasowe
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS timezones (
    id SERIAL PRIMARY KEY,
    timezone_id VARCHAR(100) NOT NULL UNIQUE,     -- IANA timezone ID (np. 'Europe/Warsaw', 'America/New_York')
    name VARCHAR(100) NOT NULL,                   -- Nazwa strefy (np. 'Central European Time')
    abbreviation VARCHAR(10),                     -- Skrót (np. 'CET', 'EST')
    utc_offset_minutes INTEGER NOT NULL,           -- Offset UTC w minutach (standardowy, bez DST)
    dst_offset_minutes INTEGER,                   -- Dodatkowy offset podczas DST (zwykle 60 minut)
    uses_dst BOOLEAN DEFAULT FALSE,               -- Czy używa czasu letniego (DST)
    dst_start_rule VARCHAR(50),                   -- Reguła rozpoczęcia DST (np. '2nd Sunday in March')
    dst_end_rule VARCHAR(50),                     -- Reguła zakończenia DST (np. '1st Sunday in November')
    country_codes TEXT,                           -- Kody krajów ISO 2 oddzielone przecinkami (np. 'PL,DE,FR')
    description TEXT,                              -- Opis strefy czasowej
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE timezones IS 'Strefy czasowe IANA z parametrami UTC offset i DST';
COMMENT ON COLUMN timezones.timezone_id IS 'IANA timezone identifier (np. Europe/Warsaw)';
COMMENT ON COLUMN timezones.utc_offset_minutes IS 'Standardowy offset UTC w minutach (bez DST)';
COMMENT ON COLUMN timezones.dst_offset_minutes IS 'Dodatkowy offset podczas DST (zwykle 60 minut)';
COMMENT ON COLUMN timezones.country_codes IS 'Kody krajów ISO 2 używające tej strefy, oddzielone przecinkami';

CREATE INDEX idx_timezones_timezone_id ON timezones(timezone_id);
CREATE INDEX idx_timezones_country_codes ON timezones USING gin(to_tsvector('simple', country_codes));

-- ----------------------------------------------------------------------------
-- Zmiana kolumny timezone w tabeli countries na tablicę ID
-- ----------------------------------------------------------------------------

-- Najpierw usuń starą kolumnę timezone (jeśli istnieje)
ALTER TABLE countries DROP COLUMN IF EXISTS timezone;

-- Dodaj nową kolumnę jako tablicę integer (ID stref czasowych)
ALTER TABLE countries ADD COLUMN timezone_ids INTEGER[];

COMMENT ON COLUMN countries.timezone_ids IS 'Tablica ID stref czasowych z tabeli timezones';

CREATE INDEX idx_countries_timezone_ids ON countries USING gin(timezone_ids);

-- ----------------------------------------------------------------------------
-- Funkcja do aktualizacji updated_at
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_timezones_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_timezones_updated_at
    BEFORE UPDATE ON timezones
    FOR EACH ROW
    EXECUTE FUNCTION update_timezones_updated_at_column();

