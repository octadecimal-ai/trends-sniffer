#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wykonania migracji dodającej kolumnę timezone_id do dictionary_region_events.
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


def check_column_exists(conn) -> bool:
    """Sprawdza czy kolumna timezone_id już istnieje."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'dictionary_region_events'
            AND column_name = 'timezone_id'
        """)
        return cur.fetchone() is not None


def main():
    """Główna funkcja programu."""
    print("="*70)
    print("MIGRACJA: Dodanie kolumny timezone_id do dictionary_region_events")
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
        # Sprawdź czy kolumna już istnieje
        print("\nSprawdzanie istniejącej kolumny...")
        column_exists = check_column_exists(conn)
        
        if column_exists:
            print("⚠ Kolumna 'timezone_id' już istnieje")
        else:
            print("✓ Kolumna 'timezone_id' nie istnieje - będzie utworzona")
        
        # Wykonaj migrację
        migration_file = os.path.join(
            os.path.dirname(__file__),
            '../../database/migration_add_timezone_to_region_events.sql'
        )
        
        print(f"\nWykonywanie migracji z pliku: {migration_file}")
        execute_sql_file(conn, migration_file)
        
        # Sprawdź liczbę zaktualizowanych rekordów
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(timezone_id) as with_timezone,
                    COUNT(*) - COUNT(timezone_id) as without_timezone
                FROM dictionary_region_events
            """)
            stats = cur.fetchone()
            total, with_timezone, without_timezone = stats
        
        print(f"\nStatystyki:")
        print(f"  Wszystkie rekordy: {total}")
        print(f"  Z timezone_id: {with_timezone}")
        print(f"  Bez timezone_id: {without_timezone}")
        
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

