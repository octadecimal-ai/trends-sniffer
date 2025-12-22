-- ============================================================================
-- Zapytanie: Lista krajów z region_id i income_level_id
-- ============================================================================
-- Wyświetla kraje, które mają wpisany region_id i income_level_id,
-- wraz z nazwami regionów (i ich id) oraz poziomami dochodów,
-- posortowane ASC po region_id
-- ============================================================================

SELECT 
    c.id AS country_id,
    c.iso2_code,
    c.iso3_code,
    c.name_en AS country_name,
    c.name_pl AS country_name_pl,
    r.id AS region_id,
    r.code AS region_code,
    r.name_en AS region_name,
    r.name_pl AS region_name_pl,
    il.id AS income_level_id,
    il.code AS income_level_code,
    il.name_en AS income_level_name,
    il.name_pl AS income_level_name_pl
FROM 
    countries c
    INNER JOIN regions r ON c.region_id = r.id
    INNER JOIN income_levels il ON c.income_level_id = il.id
WHERE 
    c.region_id IS NOT NULL 
    AND c.income_level_id IS NOT NULL
ORDER BY 
    r.id ASC,
    c.name_en ASC;

