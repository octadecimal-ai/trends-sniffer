SELECT 
   (ss.created_at AT TIME ZONE 'UTC -1')::TIME as created_at_warsaw_time,
   (ss.occurrence_time AT TIME ZONE 'UTC -2')::TIME as occurrence_warsaw_time,
    ss.occurrence_time,
	ss.occurrence_time - (c.utc_offset || ' minutes + 1 hour')::interval as occurrence_local_time,
    sm.language_code,
	bsp.phrase,
    bsp.multiplier,
    sm.vpn_country,
    c.name_en AS country_name_en,
    c.population,
    c.population_density,
    c.area_km2,
    c.utc_offset AS country_utc_offset_minutes,
    r.code AS region_code,
	r.description_en,
    r.priority_tier AS region_priority_tier,
    il.name_pl AS income_level_name_pl,
    hd.hashrate_share_percent,
    dre.phase_code,
    dre.region_code AS event_region_code,
    dre.label AS event_label,
    dre.description AS event_description,
    -- Wskaźniki jako oddzielne kolumny
    (SELECT sentiment_weight FROM indicators WHERE code = 'GOOGLE_TRENDS' AND is_active = TRUE) AS indicator_google_trends_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'BIT_SHD_PT' AND is_active = TRUE) AS indicator_bitcoin_premium_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'FP.CPI.TOTL.ZG' AND is_active = TRUE) AS indicator_inflation_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'HASHRATE_SHARE' AND is_active = TRUE) AS indicator_hashrate_share_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'IT.NET.USER.ZS' AND is_active = TRUE) AS indicator_internet_access_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'NY.GDP.MKTP.CD' AND is_active = TRUE) AS indicator_gdp_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'NY.GDP.PCAP.CD' AND is_active = TRUE) AS indicator_gdp_per_capita_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'SP.POP.TOTL' AND is_active = TRUE) AS indicator_population_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'SL.UEM.TOTL.ZS' AND is_active = TRUE) AS indicator_unemployment_weight,
    (SELECT sentiment_weight FROM indicators WHERE code = 'BIT_SHD_RT' AND is_active = TRUE) AS indicator_bitcoin_parallel_rate_weight,
	ohlcv.open AS ohlcv_open,
    ohlcv.close AS ohlcv_close,
    ohlcv.volume AS ohlcv_volume,
    ohlcv.timestamp AS ohlcv_timestamp,
    gdelt.tone AS gdelt_tone    
FROM 
    google_trends_sentiments_sniff ss
    JOIN google_trends_sentiment_measurement sm ON ss.measurement_id = sm.id
    JOIN bitcoin_sentiment_phrases bsp ON bsp.id = sm.phrase_id
    JOIN countries c ON c.id = sm.country_id
    JOIN regions r ON r.id = c.region_id
    INNER JOIN income_levels il ON c.income_level_id = il.id
    LEFT JOIN LATERAL (
        SELECT 
            hd.id,
            hd.hashrate_share_percent
        FROM hashrate_data hd
        WHERE hd.country_id = c.id
        ORDER BY hd.recorded_at DESC
        LIMIT 1
    ) hd ON TRUE
    LEFT JOIN LATERAL (
        SELECT 
            dre.phase_code,
            dre.region_code,
            dre.label,
            dre.description,
            dre.utc_start,
            dre.utc_end,
            dre.wraps_midnight,
            dre.priority,
            dre.volatility_level,
            dre.volume_impact,
            dre.typical_duration_min,
            dre.trading_pattern,
            dre.dominant_actors,
            dre.news_sensitivity,
            dre.category
        FROM dictionary_region_events dre
        WHERE dre.region_code = r.code
          AND (
              (ss.occurrence_time AT TIME ZONE 'UTC')::TIME >= dre.utc_start - (c.utc_offset || ' minutes')::interval
              AND (ss.occurrence_time AT TIME ZONE 'UTC')::TIME <= dre.utc_end - (c.utc_offset || ' minutes')::interval
              OR
              (dre.wraps_midnight AND (
                  (ss.occurrence_time AT TIME ZONE 'UTC')::TIME >= dre.utc_start - (c.utc_offset || ' minutes')::interval
                  OR (ss.occurrence_time AT TIME ZONE 'UTC')::TIME <= dre.utc_start - (c.utc_offset || ' minutes')::interval
              ))
          )
        ORDER BY dre.priority ASC
        LIMIT 1
    ) dre ON TRUE
    LEFT JOIN LATERAL (
        SELECT 
            o.open,
            o.close,
            o.volume,
            o.timestamp
        FROM ohlcv o
        WHERE o.exchange = 'binance'
          AND o.symbol = 'BTC/USDC'
          AND o.timeframe = '1m'
          AND DATE_TRUNC('minute', o.timestamp AT TIME ZONE 'UTC')::TIME = 
              DATE_TRUNC('minute', (ss.occurrence_time AT TIME ZONE 'UTC')::TIME)
          AND o.timestamp >= (SELECT MIN(occurrence_time) - INTERVAL '1 hour' FROM google_trends_sentiments_sniff)
          AND o.timestamp <= (SELECT MAX(occurrence_time) + INTERVAL '1 hour' FROM google_trends_sentiments_sniff)
        ORDER BY o.timestamp DESC
        LIMIT 1
    ) ohlcv ON TRUE
    LEFT JOIN LATERAL (
        SELECT 
            g.tone,
            g.tone_std,
            g.volume,
            g.positive_count,
            g.negative_count,
            g.neutral_count,
            g.timestamp
        FROM gdelt_sentiment g
        WHERE g.region = c.iso2_code
          AND g.timestamp <= ss.occurrence_time
          AND g.timestamp >= (SELECT MIN(occurrence_time) - INTERVAL '1 hour' FROM sentiments_sniff)
          AND g.timestamp <= (SELECT MAX(occurrence_time) + INTERVAL '1 hour' FROM sentiments_sniff)
        ORDER BY g.timestamp DESC
        LIMIT 1
    ) gdelt ON TRUE

WHERE 
    bsp.multiplier <> 0

ORDER BY 
    ss.occurrence_time DESC;
