-- ============================================================================
-- Migracja: Dodanie kolumny error do tabeli sentiment_measurement
-- ============================================================================

ALTER TABLE sentiment_measurement 
ADD COLUMN IF NOT EXISTS error TEXT;

COMMENT ON COLUMN sentiment_measurement.error IS 'Komunikat błędu w przypadku wystąpienia błędu podczas zapytania';

