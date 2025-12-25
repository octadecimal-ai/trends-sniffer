-- Migration: 012_add_fomo_fud_phrases_other_languages
-- Opis: Dodanie tłumaczeń fraz FOMO/FUD dla głównych języków (chiński, japoński, koreański, rosyjski, niemiecki, francuski, hiszpański, włoski, polski, portugalski, turecki)
-- Data: 2025-12-25
-- Autor: trends-sniffer

-- =============================================================================
-- DODANIE FRAZ FOMO/FUD W INNYCH JĘZYKACH
-- =============================================================================

-- Funkcja pomocnicza do dodawania fraz (UPSERT)
DO $$
DECLARE
    country_id_var INTEGER;
    lang_code VARCHAR(10);
    phrase_text TEXT;
    phrase_multiplier NUMERIC(5,4);
BEGIN
    -- =====================================================================
    -- CHINY (zh-CN)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'CN' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'zh-CN';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('比特币FOMO', 0.7::NUMERIC(5,4)),
                ('加密货币FOMO', 0.6::NUMERIC(5,4)),
                ('比特币暴涨', 0.8::NUMERIC(5,4)),
                ('比特币月亮', 0.7::NUMERIC(5,4)),
                ('比特币牛市', 0.6::NUMERIC(5,4)),
                ('现在买比特币', 0.7::NUMERIC(5,4)),
                ('比特币反弹', 0.6::NUMERIC(5,4)),
                ('比特币飙升', 0.6::NUMERIC(5,4)),
                ('比特币突破', 0.5::NUMERIC(5,4)),
                ('比特币收益', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('比特币FUD', -0.8::NUMERIC(5,4)),
                ('加密货币FUD', -0.7::NUMERIC(5,4)),
                ('比特币崩盘', -1.0::NUMERIC(5,4)),
                ('比特币暴跌', -0.9::NUMERIC(5,4)),
                ('比特币熊市', -0.7::NUMERIC(5,4)),
                ('卖比特币', -0.6::NUMERIC(5,4)),
                ('比特币下跌', -0.7::NUMERIC(5,4)),
                ('比特币下降', -0.6::NUMERIC(5,4)),
                ('比特币回调', -0.5::NUMERIC(5,4)),
                ('比特币泡沫', -0.8::NUMERIC(5,4)),
                ('比特币骗局', -1.0::NUMERIC(5,4)),
                ('比特币黑客', -0.9::NUMERIC(5,4)),
                ('比特币禁令', -1.0::NUMERIC(5,4)),
                ('比特币监管', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- JAPONIA (ja)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'JP' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'ja';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('ビットコインFOMO', 0.7::NUMERIC(5,4)),
                ('暗号通貨FOMO', 0.6::NUMERIC(5,4)),
                ('ビットコインパンプ', 0.8::NUMERIC(5,4)),
                ('ビットコインムーン', 0.7::NUMERIC(5,4)),
                ('ビットコインブル', 0.6::NUMERIC(5,4)),
                ('今ビットコインを買う', 0.7::NUMERIC(5,4)),
                ('ビットコインラリー', 0.6::NUMERIC(5,4)),
                ('ビットコイン急騰', 0.6::NUMERIC(5,4)),
                ('ビットコインブレイクアウト', 0.5::NUMERIC(5,4)),
                ('ビットコイン利益', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('ビットコインFUD', -0.8::NUMERIC(5,4)),
                ('暗号通貨FUD', -0.7::NUMERIC(5,4)),
                ('ビットコインクラッシュ', -1.0::NUMERIC(5,4)),
                ('ビットコインダンプ', -0.9::NUMERIC(5,4)),
                ('ビットコインベア', -0.7::NUMERIC(5,4)),
                ('ビットコイン売る', -0.6::NUMERIC(5,4)),
                ('ビットコイン下落', -0.7::NUMERIC(5,4)),
                ('ビットコイン減少', -0.6::NUMERIC(5,4)),
                ('ビットコイン調整', -0.5::NUMERIC(5,4)),
                ('ビットコインバブル', -0.8::NUMERIC(5,4)),
                ('ビットコイン詐欺', -1.0::NUMERIC(5,4)),
                ('ビットコインハック', -0.9::NUMERIC(5,4)),
                ('ビットコイン禁止', -1.0::NUMERIC(5,4)),
                ('ビットコイン規制', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- KOREA POŁUDNIOWA (ko-KR)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'KR' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'ko-KR';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('비트코인 FOMO', 0.7::NUMERIC(5,4)),
                ('암호화폐 FOMO', 0.6::NUMERIC(5,4)),
                ('비트코인 펌프', 0.8::NUMERIC(5,4)),
                ('비트코인 문', 0.7::NUMERIC(5,4)),
                ('비트코인 황소', 0.6::NUMERIC(5,4)),
                ('지금 비트코인 사기', 0.7::NUMERIC(5,4)),
                ('비트코인 랠리', 0.6::NUMERIC(5,4)),
                ('비트코인 급등', 0.6::NUMERIC(5,4)),
                ('비트코인 돌파', 0.5::NUMERIC(5,4)),
                ('비트코인 수익', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('비트코인 FUD', -0.8::NUMERIC(5,4)),
                ('암호화폐 FUD', -0.7::NUMERIC(5,4)),
                ('비트코인 크래시', -1.0::NUMERIC(5,4)),
                ('비트코인 덤프', -0.9::NUMERIC(5,4)),
                ('비트코인 곰', -0.7::NUMERIC(5,4)),
                ('비트코인 판매', -0.6::NUMERIC(5,4)),
                ('비트코인 하락', -0.7::NUMERIC(5,4)),
                ('비트코인 감소', -0.6::NUMERIC(5,4)),
                ('비트코인 조정', -0.5::NUMERIC(5,4)),
                ('비트코인 버블', -0.8::NUMERIC(5,4)),
                ('비트코인 사기', -1.0::NUMERIC(5,4)),
                ('비트코인 해킹', -0.9::NUMERIC(5,4)),
                ('비트코인 금지', -1.0::NUMERIC(5,4)),
                ('비트코인 규제', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- ROSJA (ru)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'RU' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'ru';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('биткоин FOMO', 0.7::NUMERIC(5,4)),
                ('криптовалюта FOMO', 0.6::NUMERIC(5,4)),
                ('биткоин памп', 0.8::NUMERIC(5,4)),
                ('биткоин луна', 0.7::NUMERIC(5,4)),
                ('биткоин бык', 0.6::NUMERIC(5,4)),
                ('купить биткоин сейчас', 0.7::NUMERIC(5,4)),
                ('биткоин ралли', 0.6::NUMERIC(5,4)),
                ('биткоин всплеск', 0.6::NUMERIC(5,4)),
                ('биткоин прорыв', 0.5::NUMERIC(5,4)),
                ('биткоин прибыль', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('биткоин FUD', -0.8::NUMERIC(5,4)),
                ('криптовалюта FUD', -0.7::NUMERIC(5,4)),
                ('биткоин крах', -1.0::NUMERIC(5,4)),
                ('биткоин дамп', -0.9::NUMERIC(5,4)),
                ('биткоин медведь', -0.7::NUMERIC(5,4)),
                ('продать биткоин', -0.6::NUMERIC(5,4)),
                ('биткоин падение', -0.7::NUMERIC(5,4)),
                ('биткоин снижение', -0.6::NUMERIC(5,4)),
                ('биткоин коррекция', -0.5::NUMERIC(5,4)),
                ('биткоин пузырь', -0.8::NUMERIC(5,4)),
                ('биткоин скам', -1.0::NUMERIC(5,4)),
                ('биткоин хак', -0.9::NUMERIC(5,4)),
                ('запрет биткоина', -1.0::NUMERIC(5,4)),
                ('регулирование биткоина', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- NIEMCY (de)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'DE' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'de';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Krypto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Mond', 0.7::NUMERIC(5,4)),
                ('Bitcoin Bulle', 0.6::NUMERIC(5,4)),
                ('Bitcoin jetzt kaufen', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rallye', 0.6::NUMERIC(5,4)),
                ('Bitcoin Anstieg', 0.6::NUMERIC(5,4)),
                ('Bitcoin Ausbruch', 0.5::NUMERIC(5,4)),
                ('Bitcoin Gewinne', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Krypto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Crash', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Bär', -0.7::NUMERIC(5,4)),
                ('Bitcoin verkaufen', -0.6::NUMERIC(5,4)),
                ('Bitcoin Fall', -0.7::NUMERIC(5,4)),
                ('Bitcoin Rückgang', -0.6::NUMERIC(5,4)),
                ('Bitcoin Korrektur', -0.5::NUMERIC(5,4)),
                ('Bitcoin Blase', -0.8::NUMERIC(5,4)),
                ('Bitcoin Betrug', -1.0::NUMERIC(5,4)),
                ('Bitcoin Hack', -0.9::NUMERIC(5,4)),
                ('Bitcoin Verbot', -1.0::NUMERIC(5,4)),
                ('Bitcoin Regulierung', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- FRANCJA (fr-FR)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'FR' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'fr-FR';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Crypto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Lune', 0.7::NUMERIC(5,4)),
                ('Bitcoin Taureau', 0.6::NUMERIC(5,4)),
                ('Acheter Bitcoin maintenant', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rallye', 0.6::NUMERIC(5,4)),
                ('Bitcoin Hausse', 0.6::NUMERIC(5,4)),
                ('Bitcoin Rupture', 0.5::NUMERIC(5,4)),
                ('Bitcoin Gains', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Crypto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Crash', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Ours', -0.7::NUMERIC(5,4)),
                ('Vendre Bitcoin', -0.6::NUMERIC(5,4)),
                ('Bitcoin Chute', -0.7::NUMERIC(5,4)),
                ('Bitcoin Baisse', -0.6::NUMERIC(5,4)),
                ('Bitcoin Correction', -0.5::NUMERIC(5,4)),
                ('Bitcoin Bulle', -0.8::NUMERIC(5,4)),
                ('Bitcoin Arnaque', -1.0::NUMERIC(5,4)),
                ('Bitcoin Piratage', -0.9::NUMERIC(5,4)),
                ('Bitcoin Interdiction', -1.0::NUMERIC(5,4)),
                ('Bitcoin Régulation', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- HISZPANIA (es-ES)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'ES' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'es-ES';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Crypto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Luna', 0.7::NUMERIC(5,4)),
                ('Bitcoin Toro', 0.6::NUMERIC(5,4)),
                ('Comprar Bitcoin ahora', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rally', 0.6::NUMERIC(5,4)),
                ('Bitcoin Subida', 0.6::NUMERIC(5,4)),
                ('Bitcoin Ruptura', 0.5::NUMERIC(5,4)),
                ('Bitcoin Ganancias', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Crypto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Crash', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Oso', -0.7::NUMERIC(5,4)),
                ('Vender Bitcoin', -0.6::NUMERIC(5,4)),
                ('Bitcoin Caída', -0.7::NUMERIC(5,4)),
                ('Bitcoin Declive', -0.6::NUMERIC(5,4)),
                ('Bitcoin Corrección', -0.5::NUMERIC(5,4)),
                ('Bitcoin Burbuja', -0.8::NUMERIC(5,4)),
                ('Bitcoin Estafa', -1.0::NUMERIC(5,4)),
                ('Bitcoin Hack', -0.9::NUMERIC(5,4)),
                ('Bitcoin Prohibición', -1.0::NUMERIC(5,4)),
                ('Bitcoin Regulación', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- WŁOCHY (it-IT)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'IT' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'it-IT';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Crypto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Luna', 0.7::NUMERIC(5,4)),
                ('Bitcoin Toro', 0.6::NUMERIC(5,4)),
                ('Comprare Bitcoin ora', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rally', 0.6::NUMERIC(5,4)),
                ('Bitcoin Impennata', 0.6::NUMERIC(5,4)),
                ('Bitcoin Rottura', 0.5::NUMERIC(5,4)),
                ('Bitcoin Guadagni', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Crypto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Crash', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Orso', -0.7::NUMERIC(5,4)),
                ('Vendere Bitcoin', -0.6::NUMERIC(5,4)),
                ('Bitcoin Caduta', -0.7::NUMERIC(5,4)),
                ('Bitcoin Declino', -0.6::NUMERIC(5,4)),
                ('Bitcoin Correzione', -0.5::NUMERIC(5,4)),
                ('Bitcoin Bolla', -0.8::NUMERIC(5,4)),
                ('Bitcoin Truffa', -1.0::NUMERIC(5,4)),
                ('Bitcoin Hackeraggio', -0.9::NUMERIC(5,4)),
                ('Bitcoin Divieto', -1.0::NUMERIC(5,4)),
                ('Bitcoin Regolamentazione', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- POLSKA (pl)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'PL' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'pl';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Krypto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Księżyc', 0.7::NUMERIC(5,4)),
                ('Bitcoin Byk', 0.6::NUMERIC(5,4)),
                ('Kup Bitcoin teraz', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rally', 0.6::NUMERIC(5,4)),
                ('Bitcoin Wzrost', 0.6::NUMERIC(5,4)),
                ('Bitcoin Przełamanie', 0.5::NUMERIC(5,4)),
                ('Bitcoin Zyski', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Krypto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Krach', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Niedźwiedź', -0.7::NUMERIC(5,4)),
                ('Sprzedaj Bitcoin', -0.6::NUMERIC(5,4)),
                ('Bitcoin Spadek', -0.7::NUMERIC(5,4)),
                ('Bitcoin Spadki', -0.6::NUMERIC(5,4)),
                ('Bitcoin Korekta', -0.5::NUMERIC(5,4)),
                ('Bitcoin Bańka', -0.8::NUMERIC(5,4)),
                ('Bitcoin Scam', -1.0::NUMERIC(5,4)),
                ('Bitcoin Hack', -0.9::NUMERIC(5,4)),
                ('Bitcoin Zakaz', -1.0::NUMERIC(5,4)),
                ('Bitcoin Regulacja', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- BRAZYLIA (pt-BR)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'BR' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'pt-BR';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Crypto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Lua', 0.7::NUMERIC(5,4)),
                ('Bitcoin Touro', 0.6::NUMERIC(5,4)),
                ('Comprar Bitcoin agora', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rally', 0.6::NUMERIC(5,4)),
                ('Bitcoin Alta', 0.6::NUMERIC(5,4)),
                ('Bitcoin Ruptura', 0.5::NUMERIC(5,4)),
                ('Bitcoin Ganhos', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Crypto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Crash', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Urso', -0.7::NUMERIC(5,4)),
                ('Vender Bitcoin', -0.6::NUMERIC(5,4)),
                ('Bitcoin Queda', -0.7::NUMERIC(5,4)),
                ('Bitcoin Declínio', -0.6::NUMERIC(5,4)),
                ('Bitcoin Correção', -0.5::NUMERIC(5,4)),
                ('Bitcoin Bolha', -0.8::NUMERIC(5,4)),
                ('Bitcoin Golpe', -1.0::NUMERIC(5,4)),
                ('Bitcoin Hack', -0.9::NUMERIC(5,4)),
                ('Bitcoin Proibição', -1.0::NUMERIC(5,4)),
                ('Bitcoin Regulamentação', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
    -- =====================================================================
    -- TURCJA (tr-TR)
    -- =====================================================================
    SELECT id INTO country_id_var FROM countries WHERE iso2_code = 'TR' LIMIT 1;
    IF country_id_var IS NOT NULL THEN
        lang_code := 'tr-TR';
        
        -- FOMO frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FOMO', 0.7::NUMERIC(5,4)),
                ('Kripto FOMO', 0.6::NUMERIC(5,4)),
                ('Bitcoin Pump', 0.8::NUMERIC(5,4)),
                ('Bitcoin Ay', 0.7::NUMERIC(5,4)),
                ('Bitcoin Boğa', 0.6::NUMERIC(5,4)),
                ('Bitcoin şimdi al', 0.7::NUMERIC(5,4)),
                ('Bitcoin Rally', 0.6::NUMERIC(5,4)),
                ('Bitcoin Yükseliş', 0.6::NUMERIC(5,4)),
                ('Bitcoin Kırılım', 0.5::NUMERIC(5,4)),
                ('Bitcoin Kazanç', 0.5::NUMERIC(5,4))
            ) AS fomo_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
        
        -- FUD frazy
        FOR phrase_text, phrase_multiplier IN 
            SELECT * FROM (VALUES
                ('Bitcoin FUD', -0.8::NUMERIC(5,4)),
                ('Kripto FUD', -0.7::NUMERIC(5,4)),
                ('Bitcoin Çöküş', -1.0::NUMERIC(5,4)),
                ('Bitcoin Dump', -0.9::NUMERIC(5,4)),
                ('Bitcoin Ayı', -0.7::NUMERIC(5,4)),
                ('Bitcoin sat', -0.6::NUMERIC(5,4)),
                ('Bitcoin Düşüş', -0.7::NUMERIC(5,4)),
                ('Bitcoin Düzeltme', -0.5::NUMERIC(5,4)),
                ('Bitcoin Balon', -0.8::NUMERIC(5,4)),
                ('Bitcoin Dolandırıcılık', -1.0::NUMERIC(5,4)),
                ('Bitcoin Hack', -0.9::NUMERIC(5,4)),
                ('Bitcoin Yasak', -1.0::NUMERIC(5,4)),
                ('Bitcoin Düzenleme', -0.4::NUMERIC(5,4))
            ) AS fud_phrases(phrase, multiplier)
        LOOP
            INSERT INTO bitcoin_sentiment_phrases (country_id, language_code, phrase, multiplier, is_active)
            VALUES (country_id_var, lang_code, phrase_text, phrase_multiplier, TRUE)
            ON CONFLICT (country_id, language_code, phrase) 
            DO UPDATE SET multiplier = EXCLUDED.multiplier, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
        END LOOP;
    END IF;
    
END $$;

-- Statystyki
SELECT 
    'FOMO/FUD frazy w innych językach' AS status,
    COUNT(*) AS total_phrases,
    COUNT(DISTINCT country_id) AS countries,
    COUNT(DISTINCT language_code) AS languages,
    SUM(CASE WHEN multiplier > 0 THEN 1 ELSE 0 END) AS fomo_phrases,
    SUM(CASE WHEN multiplier < 0 THEN 1 ELSE 0 END) AS fud_phrases
FROM bitcoin_sentiment_phrases
WHERE (phrase LIKE '%FOMO%' OR phrase LIKE '%FUD%' OR phrase LIKE '%pump%' OR phrase LIKE '%crash%'
   OR phrase LIKE '%パンプ%' OR phrase LIKE '%クラッシュ%' OR phrase LIKE '%펌프%' OR phrase LIKE '%크래시%'
   OR phrase LIKE '%暴涨%' OR phrase LIKE '%崩盘%' OR phrase LIKE '%памп%' OR phrase LIKE '%крах%'
   OR phrase LIKE '%Pump%' OR phrase LIKE '%Crash%' OR phrase LIKE '%Księżyc%' OR phrase LIKE '%Krach%')
   AND is_active = TRUE;

