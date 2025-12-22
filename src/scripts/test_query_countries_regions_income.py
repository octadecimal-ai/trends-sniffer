#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test zapytania: Lista krajów z region_id i income_level_id
"""

import sys
import os
from dotenv import load_dotenv
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

query = """
SELECT 
    c.id AS country_id,
    c.iso2_code,
    c.name_en AS country_name,
    r.id AS region_id,
    r.code AS region_code,
    r.name_en AS region_name,
    il.id AS income_level_id,
    il.code AS income_level_code,
    il.name_en AS income_level_name
FROM 
    countries c
    INNER JOIN regions r ON c.region_id = r.id
    INNER JOIN income_levels il ON c.income_level_id = il.id
WHERE 
    c.region_id IS NOT NULL 
    AND c.income_level_id IS NOT NULL
ORDER BY 
    r.id ASC,
    c.name_en ASC
LIMIT 15;
"""

cur.execute(query)
rows = cur.fetchall()
print("Przykładowe wyniki (pierwsze 15):")
print("=" * 100)
for row in rows:
    print(f"Region ID: {row[3]}, Region: {row[5]} ({row[4]}) | Country: {row[2]} ({row[1]}) | Income: {row[8]} ({row[7]})")

cur.execute("SELECT COUNT(*) FROM countries c WHERE c.region_id IS NOT NULL AND c.income_level_id IS NOT NULL;")
total = cur.fetchone()[0]
print(f"\nŁączna liczba krajów: {total}")

conn.close()

