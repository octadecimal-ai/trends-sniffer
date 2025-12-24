#!/usr/bin/env python3
"""Test zapytania SQL dla traderów"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Podsumowanie
cur.execute("""
    SELECT 
        COUNT(*) AS total_traders_with_rank,
        COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) AS traders_with_fills,
        COUNT(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) AS traders_without_fills,
        ROUND(100.0 * COUNT(*) FILTER (WHERE EXISTS (SELECT 1 FROM dydx_fills WHERE trader_id = t.id)) / NULLIF(COUNT(*), 0), 2) AS progress_percent,
        SUM((SELECT COUNT(*) FROM dydx_fills WHERE trader_id = t.id)) AS total_fills
    FROM dydx_traders t
    WHERE t.rank IS NOT NULL
""")

row = cur.fetchone()
print('=== PODSUMOWANIE POSTĘPU ===\n')
print(f'Traderów z rankiem: {row[0]}')
print(f'Traderów z fill\'ami: {row[1]}')
print(f'Traderów bez fill\'ów: {row[2]}')
print(f'Postęp: {row[3]}%')
print(f'Całkowita liczba fill\'ów: {row[4]:,}')

conn.close()

