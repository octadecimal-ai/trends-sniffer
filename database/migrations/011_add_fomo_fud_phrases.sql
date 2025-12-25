-- Migration: 011_add_fomo_fud_phrases
-- Opis: Dodanie fraz FOMO/FUD do bitcoin_sentiment_phrases dla głównych krajów anglojęzycznych
-- Data: 2025-12-25
-- Autor: trends-sniffer

-- =============================================================================
-- DODANIE FRAZ FOMO/FUD
-- =============================================================================

-- FOMO (Fear Of Missing Out) - pozytywne frazy wskazujące na chęć kupna
-- FUD (Fear, Uncertainty, Doubt) - negatywne frazy wskazujące na strach i chęć sprzedaży

-- Kraje anglojęzyczne: US, GB, CA, AU, NZ, IE, ZA
-- Języki: en-US, en-GB, en-CA, en-AU, en-NZ, en-IE, en-ZA

-- Funkcja pomocnicza do dodawania fraz (UPSERT)
DO $$
DECLARE
    country_record RECORD;
    lang_code VARCHAR(10);
    phrase_text TEXT;
    phrase_multiplier NUMERIC(5,4);
BEGIN
    -- Dla każdego kraju anglojęzycznego
    FOR country_record IN 
        SELECT id, iso2_code 
        FROM countries 
        WHERE iso2_code IN ('US', 'GB', 'CA', 'AU', 'NZ', 'IE', 'ZA')
        ORDER BY iso2_code
    LOOP
        -- Określ kod języka na podstawie kraju
        CASE country_record.iso2_code
            WHEN 'US' THEN lang_code := 'en-US';
            WHEN 'GB' THEN lang_code := 'en-GB';
            WHEN 'CA' THEN lang_code := 'en-CA';
            WHEN 'AU' THEN lang_code := 'en-AU';
            WHEN 'NZ' THEN lang_code := 'en-NZ';
            WHEN 'IE' THEN lang_code := 'en-IE';
            WHEN 'ZA' THEN lang_code := 'en-ZA';
            ELSE lang_code := 'en';
        END CASE;
        
        -- FOMO frazy (pozytywne, multiplier 0.5-0.8)
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('bitcoin fomo', 0.7::NUMERIC(5,4)),
                ('crypto fomo', 0.6::NUMERIC(5,4)),
                ('bitcoin pump', 0.8::NUMERIC(5,4)),
                ('bitcoin moon', 0.7::NUMERIC(5,4)),
                ('bitcoin bull', 0.6::NUMERIC(5,4)),
                ('buy bitcoin now', 0.7::NUMERIC(5,4)),
                ('bitcoin rally', 0.6::NUMERIC(5,4)),
                ('bitcoin surge', 0.6::NUMERIC(5,4)),
                ('bitcoin breakout', 0.5::NUMERIC(5,4)),
                ('bitcoin gains', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (
                country_id,
                language_code,
                phrase,
                multiplier,
                is_active
            )
            VALUES (
                country_record.id,
                lang_code,
                phrase_text,
                phrase_multiplier,
                TRUE
            )
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET
                multiplier = EXCLUDED.multiplier,
                is_active = EXCLUDED.is_active,
                updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy (negatywne, multiplier -0.5 do -1.0)
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('bitcoin fud', -0.8::NUMERIC(5,4)),
                ('crypto fud', -0.7::NUMERIC(5,4)),
                ('bitcoin crash', -1.0::NUMERIC(5,4)),
                ('bitcoin dump', -0.9::NUMERIC(5,4)),
                ('bitcoin bear', -0.7::NUMERIC(5,4)),
                ('bitcoin sell', -0.6::NUMERIC(5,4)),
                ('bitcoin drop', -0.7::NUMERIC(5,4)),
                ('bitcoin decline', -0.6::NUMERIC(5,4)),
                ('bitcoin correction', -0.5::NUMERIC(5,4)),
                ('bitcoin bubble', -0.8::NUMERIC(5,4)),
                ('bitcoin scam', -1.0::NUMERIC(5,4)),
                ('bitcoin hack', -0.9::NUMERIC(5,4)),
                ('bitcoin ban', -1.0::NUMERIC(5,4)),
                ('bitcoin regulation', -0.4::NUMERIC(5,4))  -- Regulacje mogą być negatywne, ale nie zawsze
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (
                country_id,
                language_code,
                phrase,
                multiplier,
                is_active
            )
            VALUES (
                country_record.id,
                lang_code,
                phrase_text,
                phrase_multiplier,
                TRUE
            )
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET
                multiplier = EXCLUDED.multiplier,
                is_active = EXCLUDED.is_active,
                updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END LOOP;
END $$;

-- Statystyki
SELECT 
    'FOMO/FUD frazy dodane' AS status,
    COUNT(*) AS total_phrases,
    COUNT(DISTINCT country_id) AS countries,
    COUNT(DISTINCT language_code) AS languages,
    SUM(CASE WHEN multiplier > 0 THEN 1 ELSE 0 END) AS fomo_phrases,
    SUM(CASE WHEN multiplier < 0 THEN 1 ELSE 0 END) AS fud_phrases
FROM bitcoin_sentiment_phrases
WHERE phrase IN (
    'bitcoin fomo', 'crypto fomo', 'bitcoin pump', 'bitcoin moon', 'bitcoin bull',
    'buy bitcoin now', 'bitcoin rally', 'bitcoin surge', 'bitcoin breakout', 'bitcoin gains',
    'bitcoin fud', 'crypto fud', 'bitcoin crash', 'bitcoin dump', 'bitcoin bear',
    'bitcoin sell', 'bitcoin drop', 'bitcoin decline', 'bitcoin correction', 'bitcoin bubble',
    'bitcoin scam', 'bitcoin hack', 'bitcoin ban', 'bitcoin regulation'
);

-- Komentarz
COMMENT ON TABLE bitcoin_sentiment_phrases IS 'Frazy sentymentu BTC per kraj i język. Zawiera teraz również frazy FOMO/FUD dla głównych krajów anglojęzycznych.';

