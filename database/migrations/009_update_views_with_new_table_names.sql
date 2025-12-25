-- Migration: 009_update_views_with_new_table_names
-- ==================================================
-- Aktualizacja widoków aby używały nowych nazw tabel z prefiksami.
-- 
-- Widoki do aktualizacji:
-- - v_current_fear_greed (już zaktualizowany w migracji 008)
-- - v_upcoming_economic_events (wymaga aktualizacji)
-- - v_btc_premium_ranking (już zaktualizowany w migracji 008)
-- - Inne widoki w plikach SQL

-- ============================================================================
-- UPDATE: v_upcoming_economic_events
-- ============================================================================

CREATE OR REPLACE VIEW v_upcoming_economic_events AS
SELECT 
    event_date,
    event_name,
    event_type,
    country,
    importance,
    forecast,
    previous
FROM manual_economic_calendar
WHERE event_date >= NOW()
ORDER BY event_date
LIMIT 20;

COMMENT ON VIEW v_upcoming_economic_events IS 
    'Nadchodzące wydarzenia ekonomiczne z kalendarza (FOMC, CPI, NFP, GDP)';

-- ============================================================================
-- UPDATE: v_current_fear_greed (ponownie dla pewności)
-- ============================================================================

CREATE OR REPLACE VIEW v_current_fear_greed AS
SELECT 
    value,
    classification,
    value_change_24h,
    value_change_7d,
    timestamp
FROM alternative_me_fear_greed_index
ORDER BY timestamp DESC
LIMIT 1;

COMMENT ON VIEW v_current_fear_greed IS 
    'Aktualny stan Crypto Fear & Greed Index z alternative.me';

-- ============================================================================
-- UPDATE: v_current_market_indices (sprawdzenie czy nie wymaga zmian)
-- ============================================================================
-- Ten widok używa market_indices, które nie zostało przemianowane (OK)

-- ============================================================================
-- UPDATE: v_btc_premium_ranking (ponownie dla pewności)
-- ============================================================================

CREATE OR REPLACE VIEW v_btc_premium_ranking AS
SELECT 
    c.iso2_code,
    c.name_en AS country_name,
    bp.premium_percent,
    bp.parallel_rate,
    bp.period_date
FROM imf_btc_premium_data bp
JOIN countries c ON bp.country_id = c.id
WHERE bp.period_date = (
    SELECT MAX(period_date)
    FROM imf_btc_premium_data
)
ORDER BY bp.premium_percent DESC NULLS LAST;

COMMENT ON VIEW v_btc_premium_ranking IS 
    'Ranking krajów według premii BTC (IMF WPCPER) - najnowsze dane';

