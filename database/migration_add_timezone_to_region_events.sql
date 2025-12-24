-- ============================================================================
-- MIGRACJA: Dodanie kolumny timezone_id do dictionary_region_events
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Dodanie kolumny timezone_id
-- ----------------------------------------------------------------------------
ALTER TABLE dictionary_region_events 
ADD COLUMN IF NOT EXISTS timezone_id INTEGER REFERENCES timezones(id);

COMMENT ON COLUMN dictionary_region_events.timezone_id IS 'ID strefy czasowej z tabeli timezones - wskazuje na strefę czasową dla wydarzenia (zwykle stolica kraju/miasta z description)';

CREATE INDEX IF NOT EXISTS idx_dictionary_region_events_timezone ON dictionary_region_events(timezone_id);

-- ----------------------------------------------------------------------------
-- Funkcja pomocnicza do dopasowania strefy czasowej na podstawie label
-- Porównuje timezones.name z dictionary_region_events.label
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_timezone_from_label(label_text TEXT)
RETURNS INTEGER AS $$
DECLARE
    matched_timezone_id INTEGER;
BEGIN
    -- Jeśli label jest puste, zwróć NULL
    IF label_text IS NULL OR TRIM(label_text) = '' THEN
        RETURN NULL;
    END IF;
    
    -- Porównaj timezones.name z label_text
    -- label_text powinien zawierać timezones.name (bez względu na wielkość znaków)
    SELECT t.id INTO matched_timezone_id
    FROM timezones t
    WHERE label_text ILIKE '%' || t.name || '%'
    ORDER BY 
        -- Priorytet: dłuższe nazwy (bardziej specyficzne)
        LENGTH(t.name) DESC,
        -- Drugi priorytet: nazwy które są na początku label
        CASE WHEN label_text ILIKE t.name || '%' THEN 1 ELSE 2 END
    LIMIT 1;
    
    RETURN matched_timezone_id;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- Wypełnienie timezone_id dla istniejących rekordów
-- ----------------------------------------------------------------------------
UPDATE dictionary_region_events
SET timezone_id = match_timezone_from_label(label)
WHERE timezone_id IS NULL;

-- ----------------------------------------------------------------------------
-- Usunięcie funkcji pomocniczej (opcjonalne - można zostawić do późniejszego użycia)
-- ----------------------------------------------------------------------------
-- DROP FUNCTION IF EXISTS match_timezone_from_description(TEXT);

