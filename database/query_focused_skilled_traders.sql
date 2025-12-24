-- ============================================================================
-- ZAPYTANIE: Traderzy inwestujący w mało aktywów, ale umiejętnie
-- ============================================================================
-- Znajduje traderów, którzy:
-- 1. Inwestują w małą liczbę unikalnych aktywów (niskie zróżnicowanie)
-- 2. Mają dobre wyniki (wysoki ranking, aktywność, wolumen)
-- ============================================================================
-- 
-- UWAGA: Kolumna realized_pnl w dydx_fills jest pusta (NULL), więc używamy
-- alternatywnych metryk do oceny "umiejętności":
-- 
-- Metryki "umiejętności":
-- - Wysoki ranking (estimated_rewards - proxy dla umiejętności)
-- - Wysoka aktywność (dużo transakcji)
-- - Wysoki wolumen (duże zaangażowanie kapitałowe)
-- - Różnorodność strategii (balance buy/sell)
-- - Efektywność (wolumen per transakcja)
-- - Możliwe użycie net_pnl z dydx_historical_pnl (jeśli dostępne)
--
-- Metryki "mało aktywów":
-- - Niska liczba unikalnych tickerów (np. <= 5)
-- ============================================================================

WITH trader_stats AS (
    SELECT 
        t.id AS trader_id,
        t.address,
        t.subaccount_number,
        t.rank,
        t.estimated_rewards,
        
        -- Liczba unikalnych aktywów (główna metryka "mało aktywów")
        COUNT(DISTINCT f.ticker) AS unique_tickers_count,
        
        -- Statystyki transakcji
        COUNT(f.id) AS total_fills_count,
        COALESCE(SUM(f.price::numeric * f.size::numeric), 0) AS total_volume_usd,
        COALESCE(SUM(f.fee::numeric), 0) AS total_fees_usd,
        
        -- Efektywność (umiejętność) - średni rozmiar transakcji
        CASE 
            WHEN COUNT(f.id) > 0 
            THEN COALESCE(SUM(f.price::numeric * f.size::numeric), 0) / COUNT(f.id)::numeric
            ELSE 0 
        END AS avg_fill_size_usd,
        
        -- Różnorodność strategii (umiejętność) - balance buy/sell
        COUNT(*) FILTER (WHERE f.side = 'BUY') AS buy_count,
        COUNT(*) FILTER (WHERE f.side = 'SELL') AS sell_count,
        CASE 
            WHEN COUNT(f.id) > 0 
            THEN ROUND(
                ABS(
                    (COUNT(*) FILTER (WHERE f.side = 'BUY')::numeric / COUNT(f.id)::numeric) - 0.5
                ) * 200, 
                2
            )
            ELSE 100 
        END AS buy_sell_imbalance_percent,  -- 0% = idealny balance, 100% = tylko buy lub tylko sell
        
        -- Lista aktywów
        STRING_AGG(DISTINCT f.ticker, ', ' ORDER BY f.ticker) FILTER (WHERE f.ticker IS NOT NULL) AS traded_tickers,
        
        -- Zakres czasowy aktywności
        MIN(f.effective_at) AS first_fill_at,
        MAX(f.effective_at) AS last_fill_at,
        CASE 
            WHEN MIN(f.effective_at) IS NOT NULL AND MAX(f.effective_at) IS NOT NULL
            THEN EXTRACT(EPOCH FROM (MAX(f.effective_at) - MIN(f.effective_at))) / 86400.0  -- dni aktywności
            ELSE 0
        END AS trading_days,
        
        -- Częstotliwość transakcji (umiejętność)
        CASE 
            WHEN MIN(f.effective_at) IS NOT NULL AND MAX(f.effective_at) IS NOT NULL
                AND EXTRACT(EPOCH FROM (MAX(f.effective_at) - MIN(f.effective_at))) > 0
            THEN COUNT(f.id)::numeric / GREATEST(EXTRACT(EPOCH FROM (MAX(f.effective_at) - MIN(f.effective_at))) / 86400.0, 1.0)
            ELSE COUNT(f.id)::numeric
        END AS fills_per_day,
        
        -- PnL z dydx_historical_pnl (jeśli dostępne)
        (SELECT COALESCE(SUM(net_pnl), 0) 
         FROM dydx_historical_pnl pnl 
         WHERE pnl.trader_id = t.id) AS total_net_pnl_from_pnl_table
        
    FROM dydx_traders t
    LEFT JOIN dydx_fills f ON t.id = f.trader_id
    WHERE t.is_active = TRUE
    GROUP BY t.id, t.address, t.subaccount_number, t.rank, t.estimated_rewards
    HAVING COUNT(f.id) > 0  -- Tylko traderzy z przynajmniej jedną transakcją
)
SELECT 
    trader_id,
    address,
    subaccount_number,
    rank,
    estimated_rewards,
    
    -- Metryki "mało aktywów"
    unique_tickers_count,
    traded_tickers,
    
    -- Metryki "umiejętności"
    total_fills_count,
    total_volume_usd,
    avg_fill_size_usd,
    buy_count,
    sell_count,
    buy_sell_imbalance_percent,
    fills_per_day,
    trading_days,
    total_net_pnl_from_pnl_table,
    first_fill_at,
    last_fill_at,
    
    -- Kompozytowy score "umiejętności" (można dostosować wagi)
    (
        -- Waga 30%: Ranking (estimated_rewards - znormalizowany, max 500000)
        LEAST(COALESCE(estimated_rewards, 0) / 500000.0, 1.0) * 0.3 +
        -- Waga 25%: Aktywność (fills_per_day - znormalizowany, max 50)
        LEAST(fills_per_day / 50.0, 1.0) * 0.25 +
        -- Waga 20%: Wolumen (total_volume_usd - znormalizowany, max 10M)
        LEAST(total_volume_usd / 10000000.0, 1.0) * 0.2 +
        -- Waga 15%: Różnorodność strategii (im bliżej 0% imbalance, tym lepiej)
        (1.0 - LEAST(buy_sell_imbalance_percent / 100.0, 1.0)) * 0.15 +
        -- Waga 10%: Net PnL z historical_pnl (jeśli dostępne, znormalizowany max 100000)
        LEAST(COALESCE(total_net_pnl_from_pnl_table, 0) / 100000.0, 1.0) * 0.1
    ) * 100 AS skill_score
    
FROM trader_stats
WHERE 
    -- Filtrujemy traderów z małą liczbą aktywów (można dostosować próg)
    unique_tickers_count <= 5
    -- I dobrymi wynikami (można dostosować próg)
    AND total_fills_count >= 10  -- Minimum transakcji dla wiarygodności statystyk
    AND total_volume_usd > 0     -- Musi mieć jakiś wolumen
ORDER BY 
    -- Sortujemy po kompozytowym score umiejętności (malejąco)
    skill_score DESC,
    -- Potem po liczbie aktywów (rosnąco - mniej aktywów = lepiej)
    unique_tickers_count ASC,
    -- Potem po estimated_rewards (malejąco)
    estimated_rewards DESC NULLS LAST,
    -- Potem po total volume (malejąco)
    total_volume_usd DESC
LIMIT 20;  -- Top 20 traderów spełniających kryteria

-- ============================================================================
-- UWAGI:
-- ============================================================================
-- 1. Próg "mało aktywów" (unique_tickers_count <= 5) można dostosować
-- 2. Próg "umiejętności" (total_fills_count >= 10, total_volume_usd > 0) można dostosować
-- 3. Kompozytowy skill_score można dostosować wagami i metrykami:
--    - 30% ranking (estimated_rewards)
--    - 25% aktywność (fills_per_day)
--    - 20% wolumen (total_volume_usd)
--    - 15% różnorodność strategii (buy/sell balance)
--    - 10% net PnL z dydx_historical_pnl (jeśli dostępne)
-- 4. Można dodać filtry czasowe (np. ostatnie 30 dni) używając WHERE f.effective_at >= ...
-- 5. UWAGA: realized_pnl w dydx_fills jest puste, więc używamy alternatywnych metryk
-- 6. Można dodać filtry na minimum estimated_rewards dla wyższej jakości traderów
-- ============================================================================

