-- ============================================================================
-- WIDOK: Statystyki tabel - liczba rekordów i daty zakresu danych
-- ============================================================================
-- Widok zwracający liczbę rekordów oraz daty pierwszego i ostatniego rekordu
-- dla wybranych tabel
-- ============================================================================

-- Usuń widok jeśli istnieje (wymagane przy zmianie liczby kolumn)
DROP VIEW IF EXISTS v_table_stats;

CREATE VIEW v_table_stats AS
SELECT 
    'sentiments_sniff' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(occurrence_time) AS data_pierwszego_rekordu,
    MAX(occurrence_time) AS data_ostatniego_rekordu
FROM public.sentiments_sniff

UNION ALL

SELECT 
    'ohlcv' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(timestamp) AS data_pierwszego_rekordu,
    MAX(timestamp) AS data_ostatniego_rekordu
FROM public.ohlcv

UNION ALL

SELECT 
    'gdelt_sentiment' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(timestamp) AS data_pierwszego_rekordu,
    MAX(timestamp) AS data_ostatniego_rekordu
FROM public.gdelt_sentiment

UNION ALL

SELECT 
    'dydx_traders' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(last_seen_at) AS data_pierwszego_rekordu,
    MAX(last_seen_at) AS data_ostatniego_rekordu
FROM public.dydx_traders

UNION ALL

SELECT 
    'dydx_perpetual_market_trades' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(observed_at) AS data_pierwszego_rekordu,
    MAX(observed_at) AS data_ostatniego_rekordu
FROM public.dydx_perpetual_market_trades

UNION ALL

SELECT 
    'tickers' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(timestamp) AS data_pierwszego_rekordu,
    MAX(timestamp) AS data_ostatniego_rekordu
FROM public.tickers

UNION ALL

SELECT 
    'market_indices' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(timestamp) AS data_pierwszego_rekordu,
    MAX(timestamp) AS data_ostatniego_rekordu
FROM public.market_indices

UNION ALL

SELECT 
    'fear_greed_index' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(timestamp) AS data_pierwszego_rekordu,
    MAX(timestamp) AS data_ostatniego_rekordu
FROM public.fear_greed_index

UNION ALL

SELECT 
    'economic_calendar' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MIN(event_date) AS data_pierwszego_rekordu,
    MAX(event_date) AS data_ostatniego_rekordu
FROM public.economic_calendar;

-- Komentarz do widoku
COMMENT ON VIEW v_table_stats IS 'Statystyki tabel: liczba rekordów i zakres dat (pierwszy/ostatni rekord) dla głównych tabel systemu';

-- Przykład użycia:
-- SELECT * FROM v_table_stats ORDER BY tabela;

