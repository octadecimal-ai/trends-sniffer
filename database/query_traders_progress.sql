-- ============================================================================
-- ZAPYTANIE: Pełne dane o traderach + śledzenie postępu zapisu
-- ============================================================================
-- Zwraca wszystkie dane o traderach (oprócz id) oraz statystyki z fill'ów
-- Pozwala śledzić postęp importu z CSV (1000 traderów)
-- ============================================================================

SELECT 
    -- Podstawowe dane tradera
    t.address,
    t.subaccount_number,
    t.parent_subaccount_number,
    
    -- Ranking i nagrody
    t.rank,
    t.estimated_rewards,
    
    -- Status
    t.is_active,
    t.first_seen_at,
    t.last_seen_at,
    t.created_at,
    t.updated_at,
    
    -- Statystyki z tabeli traders (jeśli są aktualizowane)
    t.total_fills_count AS trader_total_fills,
    t.total_volume_usd AS trader_total_volume,
    t.total_realized_pnl AS trader_realized_pnl,
    t.total_net_pnl AS trader_net_pnl,
    
    -- Statystyki z fill'ów (rzeczywiste dane)
    COUNT(f.id) AS actual_fills_count,
    COALESCE(SUM(f.price::numeric * f.size::numeric), 0) AS actual_total_volume_usd,
    COALESCE(SUM(f.fee::numeric), 0) AS total_fees_usd,
    COUNT(DISTINCT f.ticker) AS unique_tickers_count,
    
    -- Ostatnia aktywność
    MAX(f.observed_at) AS last_fill_observed_at,
    MAX(f.created_at) AS last_fill_created_at,
    MIN(f.created_at) AS first_fill_created_at,
    
    -- Najpopularniejsze tickery
    STRING_AGG(DISTINCT f.ticker, ', ' ORDER BY f.ticker) FILTER (WHERE f.ticker IS NOT NULL) AS traded_tickers,
    
    -- Statystyki BUY vs SELL
    COUNT(*) FILTER (WHERE f.side = 'BUY') AS buy_count,
    COUNT(*) FILTER (WHERE f.side = 'SELL') AS sell_count,
    COALESCE(SUM(f.price::numeric * f.size::numeric) FILTER (WHERE f.side = 'BUY'), 0) AS buy_volume_usd,
    COALESCE(SUM(f.price::numeric * f.size::numeric) FILTER (WHERE f.side = 'SELL'), 0) AS sell_volume_usd,
    
    -- Postęp importu
    CASE 
        WHEN t.rank IS NOT NULL THEN '✅ Z CSV'
        ELSE '❌ Brak ranku'
    END AS import_status,
    CASE 
        WHEN COUNT(f.id) > 0 THEN '✅ Ma fill''e'
        ELSE '⏳ Brak fill''ów'
    END AS fills_status,
    
    -- Metadane
    t.metadata,
    t.notes

FROM dydx_traders t
LEFT JOIN dydx_fills f ON f.trader_id = t.id

WHERE t.rank IS NOT NULL  -- Tylko traderzy z CSV

GROUP BY 
    t.address,
    t.subaccount_number,
    t.parent_subaccount_number,
    t.rank,
    t.estimated_rewards,
    t.is_active,
    t.first_seen_at,
    t.last_seen_at,
    t.created_at,
    t.updated_at,
    t.total_fills_count,
    t.total_volume_usd,
    t.total_realized_pnl,
    t.total_net_pnl,
    t.metadata,
    t.notes

ORDER BY 
    t.rank ASC NULLS LAST,  -- Najpierw według ranku z CSV
    actual_fills_count DESC,  -- Potem według liczby fill'ów
    t.last_seen_at DESC;

-- ============================================================================
-- PODSUMOWANIE POSTĘPU (osobne zapytanie)
-- ============================================================================

-- SELECT 
--     COUNT(*) AS total_traders_with_rank,
--     COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) AS traders_with_fills,
--     COUNT(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) AS traders_without_fills,
--     ROUND(100.0 * COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) / COUNT(*), 2) AS progress_percent,
--     SUM((SELECT COUNT(*) FROM dydx_fills WHERE trader_id = t.id)) AS total_fills,
--     MAX(t.updated_at) AS last_update_time
-- FROM dydx_traders t
-- WHERE t.rank IS NOT NULL;

