#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wykonania migracji tabel dla modułu dYdX Top Traders Observer.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Załaduj zmienne środowiskowe
load_dotenv()

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def get_database_connection():
    """Nawiązuje połączenie z bazą danych."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("Brak zmiennej środowiskowej DATABASE_URL")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        raise Exception(f"Błąd połączenia z bazą danych: {e}")


def execute_sql_file(conn, filepath: str):
    """Wykonuje plik SQL."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Plik nie istnieje: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Wykonaj cały plik SQL jako jeden blok
    with conn.cursor() as cur:
        try:
            cur.execute(sql_content)
            conn.commit()
            print("✓ Migracja wykonana pomyślnie")
            return True
        except Exception as e:
            conn.rollback()
            print(f"✗ Błąd podczas wykonywania migracji: {e}")
            raise


def check_table_exists(conn, table_name: str) -> bool:
    """Sprawdza czy tabela już istnieje."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        """, (table_name,))
        return cur.fetchone() is not None


def main():
    """Główna funkcja programu."""
    print("="*70)
    print("MIGRACJA: Tabele dla modułu dYdX Top Traders Observer")
    print("="*70)
    
    # Połącz z bazą danych
    try:
        print("\nŁączenie z bazą danych...")
        conn = get_database_connection()
        print("✓ Połączono z bazą danych")
    except Exception as e:
        print(f"\n✗ Błąd połączenia: {e}")
        return 1
    
    try:
        # Sprawdź czy główna tabela już istnieje
        print("\nSprawdzanie istniejących tabel...")
        table_exists = check_table_exists(conn, 'dydx_traders')
        
        if table_exists:
            print("⚠ Tabela 'dydx_traders' już istnieje")
            response = input("Czy chcesz kontynuować? (t/n): ")
            if response.lower() != 't':
                print("Anulowano migrację")
                return 0
        else:
            print("✓ Tabele nie istnieją - będą utworzone")
        
        # Wykonaj migrację
        migration_file = os.path.join(
            os.path.dirname(__file__),
            '../../database/migration_create_dydx_top_traders_tables.sql'
        )
        
        print(f"\nWykonywanie migracji z pliku: {migration_file}")
        execute_sql_file(conn, migration_file)
        
        # Sprawdź statystyki tabel
        tables_to_check = [
            'dydx_traders',
            'dydx_top_traders_rankings',
            'dydx_fills',
            'dydx_historical_pnl',
            'dydx_trader_metrics',
            'dydx_fill_events',
            'dydx_observer_log'
        ]
        
        print(f"\nStatystyki utworzonych tabel:")
        with conn.cursor() as cur:
            for table in tables_to_check:
                if check_table_exists(conn, table):
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"  {table}: {count} rekordów")
                else:
                    print(f"  {table}: NIE ISTNIEJE")
        
        print("\n" + "="*70)
        print("Migracja zakończona pomyślnie!")
        print("="*70)
        
        return 0
    
    except Exception as e:
        print(f"\n✗ Błąd podczas migracji: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

