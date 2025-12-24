-- ============================================================================
-- WIDOK: Statystyki tabel - liczba rekordów i ostatnia data aktualizacji
-- ============================================================================
-- Widok zwracający liczbę rekordów oraz ostatnią datę aktualizacji dla wybranych tabel
-- ============================================================================

CREATE OR REPLACE VIEW v_table_stats AS
SELECT 
    'sentiments_sniff' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MAX(created_at) AS ostatnia_aktualizacja,
    MAX(occurrence_time) AS ostatnie_wystapienie
FROM public.sentiments_sniff

UNION ALL

SELECT 
    'ohlcv' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MAX(created_at) AS ostatnia_aktualizacja,
    MAX(timestamp) AS ostatnie_wystapienie
FROM public.ohlcv

UNION ALL

SELECT 
    'gdelt_sentiment' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MAX(created_at) AS ostatnia_aktualizacja,
    MAX(timestamp) AS ostatnie_wystapienie
FROM public.gdelt_sentiment

UNION ALL

SELECT 
    'dydx_traders' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MAX(updated_at) AS ostatnia_aktualizacja,
    MAX(last_seen_at) AS ostatnie_wystapienie
FROM public.dydx_traders

UNION ALL

SELECT 
    'dydx_perpetual_market_trades' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MAX(created_at_db) AS ostatnia_aktualizacja,
    MAX(observed_at) AS ostatnie_wystapienie
FROM public.dydx_perpetual_market_trades

UNION ALL

SELECT 
    'tickers' AS tabela,
    COUNT(*) AS liczba_rekordow,
    MAX(timestamp) AS ostatnia_aktualizacja,
    MAX(timestamp) AS ostatnie_wystapienie
FROM public.tickers;

-- Komentarz do widoku
COMMENT ON VIEW v_table_stats IS 'Statystyki tabel: liczba rekordów i ostatnia data aktualizacji dla głównych tabel systemu';

-- Przykład użycia:
-- SELECT * FROM v_table_stats ORDER BY tabela;

