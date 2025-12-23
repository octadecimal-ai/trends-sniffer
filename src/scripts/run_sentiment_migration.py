#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wykonania migracji tabel sentiment_measurement i sentiments_sniff.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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
    
    # Usuń komentarze (linie zaczynające się od --)
    lines = []
    for line in sql_content.split('\n'):
        # Usuń komentarze z końca linii
        if '--' in line:
            comment_pos = line.find('--')
            # Sprawdź czy to nie jest część stringa
            if comment_pos > 0:
                line = line[:comment_pos].rstrip()
        lines.append(line)
    
    sql_content = '\n'.join(lines)
    
    # Wykonaj cały plik SQL jako jeden blok
    # psycopg2 automatycznie obsługuje wieloliniowe komendy
    with conn.cursor() as cur:
        try:
            cur.execute(sql_content)
            conn.commit()
            print("✓ Migracja wykonana pomyślnie")
        except Exception as e:
            conn.rollback()
            print(f"✗ Błąd podczas wykonywania migracji: {e}")
            raise


def check_tables_exist(conn) -> dict:
    """Sprawdza czy tabele już istnieją."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('sentiment_measurement', 'sentiments_sniff')
        """)
        existing = [row[0] for row in cur.fetchall()]
    
    return {
        'sentiment_measurement': 'sentiment_measurement' in existing,
        'sentiments_sniff': 'sentiments_sniff' in existing
    }


def main():
    """Główna funkcja programu."""
    print("="*70)
    print("MIGRACJA: Tabele sentiment_measurement i sentiments_sniff")
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
        # Sprawdź czy tabele już istnieją
        print("\nSprawdzanie istniejących tabel...")
        existing = check_tables_exist(conn)
        
        if existing['sentiment_measurement']:
            print("⚠ Tabela 'sentiment_measurement' już istnieje")
        if existing['sentiments_sniff']:
            print("⚠ Tabela 'sentiments_sniff' już istnieje")
        
        if existing['sentiment_measurement'] and existing['sentiments_sniff']:
            print("\n✓ Obie tabele już istnieją - migracja nie jest potrzebna")
            return 0
        
        # Wykonaj migrację tabel
        migration_file = os.path.join(
            os.path.dirname(__file__),
            '../../database/migration_create_sentiment_tables.sql'
        )
        
        print(f"\nWykonywanie migracji z pliku: {migration_file}")
        execute_sql_file(conn, migration_file)
        
        # Wykonaj migrację dodającą kolumnę error
        error_migration_file = os.path.join(
            os.path.dirname(__file__),
            '../../database/migration_add_error_column.sql'
        )
        
        if os.path.exists(error_migration_file):
            print(f"\nWykonywanie migracji z pliku: {error_migration_file}")
            execute_sql_file(conn, error_migration_file)
        
        # Sprawdź ponownie
        print("\nWeryfikacja utworzonych tabel...")
        existing_after = check_tables_exist(conn)
        
        if existing_after['sentiment_measurement'] and existing_after['sentiments_sniff']:
            print("✓ Obie tabele zostały utworzone pomyślnie")
        else:
            print("⚠ Niektóre tabele nie zostały utworzone:")
            if not existing_after['sentiment_measurement']:
                print("  - sentiment_measurement")
            if not existing_after['sentiments_sniff']:
                print("  - sentiments_sniff")
            return 1
        
        # Sprawdź liczbę rekordów
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sentiment_measurement")
            count_measurement = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM sentiments_sniff")
            count_sniff = cur.fetchone()[0]
        
        print(f"\nStatystyki:")
        print(f"  sentiment_measurement: {count_measurement} rekordów")
        print(f"  sentiments_sniff: {count_sniff} rekordów")
        
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

