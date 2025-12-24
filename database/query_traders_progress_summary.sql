-- ============================================================================
-- PODSUMOWANIE POSTĘPU IMPORTU
-- ============================================================================
-- Szybkie podsumowanie: ile traderów przetworzono, ile ma fill'ów, etc.
-- ============================================================================

SELECT 
    COUNT(*) AS total_traders_with_rank,
    COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) AS traders_with_fills,
    COUNT(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) AS traders_without_fills,
    ROUND(100.0 * COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) / NULLIF(COUNT(*), 0), 2) AS progress_percent,
    SUM((SELECT COUNT(*) FROM dydx_fills WHERE trader_id = t.id)) AS total_fills,
    MAX(t.updated_at) AS last_update_time,
    MIN(t.rank) AS min_rank,
    MAX(t.rank) AS max_rank
FROM dydx_traders t
WHERE t.rank IS NOT NULL;

