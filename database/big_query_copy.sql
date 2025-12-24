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
    dre.utc_start AS event_utc_start,
    dre.utc_end AS event_utc_end,
    -- Czasy lokalne dla utc_start i utc_end względem strefy czasowej wydarzenia
    CASE 
        WHEN dre_tz.timezone_id IS NOT NULL THEN
            ((date_trunc('day', ss.occurrence_time AT TIME ZONE 'UTC') + dre.utc_start) 
             AT TIME ZONE 'UTC' 
             AT TIME ZONE dre_tz.timezone_id)::TIME
        ELSE NULL
    END AS event_local_start,
    CASE 
        WHEN dre_tz.timezone_id IS NOT NULL THEN
            ((date_trunc('day', ss.occurrence_time AT TIME ZONE 'UTC') + dre.utc_end) 
             AT TIME ZONE 'UTC' 
             AT TIME ZONE dre_tz.timezone_id)::TIME
        ELSE NULL
    END AS event_local_end,
    -- Wskaźniki jako oddzielne kolumny (wartości z country_indicators dla najnowszego period_date)
    ci_google_trends.value AS indicator_google_trends_value,
    ci_bitcoin_premium.value AS indicator_bitcoin_premium_value,
    ci_inflation.value AS indicator_inflation_value,
    ci_hashrate_share.value AS indicator_hashrate_share_value,
    ci_internet_access.value AS indicator_internet_access_value,
    ci_gdp.value AS indicator_gdp_value,
    ci_gdp_per_capita.value AS indicator_gdp_per_capita_value,
    ci_population.value AS indicator_population_value,
    ci_unemployment.value AS indicator_unemployment_value,
    ci_bitcoin_parallel_rate.value AS indicator_bitcoin_parallel_rate_value,
	ohlcv.open AS ohlcv_open,
    ohlcv.close AS ohlcv_close,
    ohlcv.volume AS ohlcv_volume,
    ohlcv.timestamp AS ohlcv_timestamp,
    gdelt.tone AS gdelt_tone    
FROM 
    sentiments_sniff ss
    JOIN sentiment_measurement sm ON ss.measurement_id = sm.id
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
            dre.category,
            dre.timezone_id
        FROM dictionary_region_events dre
        WHERE dre.region_code = r.code
        AND (
            (
                -- zakres NIE przechodzi przez północ
                NOT dre.wraps_midnight
                AND
                (ss.occurrence_time AT TIME ZONE 'UTC')
                    BETWEEN
                    (
                        date_trunc('day', ss.occurrence_time AT TIME ZONE 'UTC')
                        + dre.utc_start
                    )
                    AND
                    (
                        date_trunc('day', ss.occurrence_time AT TIME ZONE 'UTC')
                        + dre.utc_end
                    )
            )
            OR
            (
                -- zakres PRZECHODZI przez północ
                dre.wraps_midnight
                AND
                (
                    -- część przed północą
                    (ss.occurrence_time AT TIME ZONE 'UTC') >=
                    (
                        date_trunc('day', ss.occurrence_time AT TIME ZONE 'UTC')
                        + dre.utc_start
                    )
                    OR
                    -- część po północy
                    (ss.occurrence_time AT TIME ZONE 'UTC') <
                    (
                        date_trunc('day', ss.occurrence_time AT TIME ZONE 'UTC')
                        + dre.utc_end
                    )
                )
            )
        )
        ORDER BY dre.priority ASC
        LIMIT 1
    ) dre ON TRUE
    LEFT JOIN timezones dre_tz ON dre_tz.id = dre.timezone_id
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
          AND o.timestamp >= (SELECT MIN(occurrence_time) - INTERVAL '1 hour' FROM sentiments_sniff)
          AND o.timestamp <= (SELECT MAX(occurrence_time) + INTERVAL '1 hour' FROM sentiments_sniff)
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
    -- Wskaźniki z country_indicators dla najnowszego period_date
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'GOOGLE_TRENDS'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_google_trends ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'BIT_SHD_PT'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_bitcoin_premium ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'FP.CPI.TOTL.ZG'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_inflation ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'HASHRATE_SHARE'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_hashrate_share ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'IT.NET.USER.ZS'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_internet_access ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'NY.GDP.MKTP.CD'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_gdp ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'NY.GDP.PCAP.CD'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_gdp_per_capita ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'SP.POP.TOTL'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_population ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'SL.UEM.TOTL.ZS'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_unemployment ON TRUE
    LEFT JOIN LATERAL (
        SELECT ci.value
        FROM country_indicators ci
        JOIN indicators i ON ci.indicator_id = i.id
        WHERE ci.country_id = c.id
          AND i.code = 'BIT_SHD_RT'
          AND i.is_active = TRUE
        ORDER BY ci.period_date DESC
        LIMIT 1
    ) ci_bitcoin_parallel_rate ON TRUE

WHERE 
    bsp.multiplier <> 0
    -- Opcjonalne filtry czasowe (będą dodawane przez API):
    -- AND ss.occurrence_time >= :time_from
    -- AND ss.occurrence_time <= :time_to

ORDER BY 
    ss.occurrence_time DESC;
