#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wczytania struktury bazy danych i przykładowych danych z pliku SQL.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

CONFIG_SCHEMA_FILE = "database/schema.sql"      # Ścieżka do pliku schema.sql
CONFIG_VERBOSE = True                            # Czy wyświetlać szczegółowe informacje
CONFIG_FORCE_RECREATE = False                   # Czy wymusić odtworzenie struktury (UWAGA: usuwa dane!)

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql

# Załaduj zmienne środowiskowe
load_dotenv()


def get_database_connection():
    """
    Tworzy połączenie z bazą danych na podstawie DATABASE_URL.
    
    Returns:
        psycopg2.connection: Połączenie z bazą danych
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL nie jest ustawiony w pliku .env")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Błąd połączenia z bazą danych: {e}")


def check_table_exists(conn, table_name):
    """
    Sprawdza czy tabela istnieje w bazie danych.
    
    Args:
        conn: Połączenie z bazą danych
        table_name: Nazwa tabeli
    
    Returns:
        bool: True jeśli tabela istnieje
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        return cur.fetchone()[0]


def check_tables_exist(conn):
    """
    Sprawdza czy główne tabele istnieją w bazie danych.
    
    Args:
        conn: Połączenie z bazą danych
    
    Returns:
        dict: Słownik z informacją o istnieniu tabel
    """
    main_tables = [
        'continents', 'regions', 'income_levels', 'indicator_types',
        'countries', 'indicators', 'keywords',
        'country_indicators', 'hashrate_data', 'btc_premium_data',
        'trend_snapshots', 'trend_keyword_results',
        'sentiment_scores', 'sentiment_alerts',
        'config', 'data_refresh_log'
    ]
    
    result = {}
    for table in main_tables:
        result[table] = check_table_exists(conn, table)
    
    return result


def execute_sql_file(conn, file_path):
    """
    Wykonuje plik SQL na bazie danych.
    
    Args:
        conn: Połączenie z bazą danych
        file_path: Ścieżka do pliku SQL
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not os.path.exists(file_path):
        return False, f"Plik nie istnieje: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Podziel na pojedyncze komendy (oddzielone średnikami)
        # Uwaga: to jest uproszczone - w rzeczywistości może być bardziej skomplikowane
        commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        with conn.cursor() as cur:
            for i, command in enumerate(commands):
                if command:
                    try:
                        cur.execute(command)
                        if CONFIG_VERBOSE and i % 10 == 0:
                            print(f"  Wykonano komendę {i+1}/{len(commands)}...")
                    except psycopg2.Error as e:
                        # Niektóre komendy mogą się nie powieść (np. CREATE TABLE IF NOT EXISTS gdy już istnieje)
                        if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                            print(f"  Ostrzeżenie przy komendzie {i+1}: {e}")
        
        conn.commit()
        return True, "Plik SQL wykonany pomyślnie"
    
    except Exception as e:
        conn.rollback()
        return False, f"Błąd podczas wykonywania pliku SQL: {e}"


def count_records(conn, table_name):
    """
    Liczy rekordy w tabeli.
    
    Args:
        conn: Połączenie z bazą danych
        table_name: Nazwa tabeli
    
    Returns:
        int: Liczba rekordów
    """
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cur.fetchone()[0]
    except psycopg2.Error:
        return 0


def display_data_summary(conn):
    """
    Wyświetla podsumowanie załadowanych danych.
    
    Args:
        conn: Połączenie z bazą danych
    """
    print("\n" + "="*80)
    print("PODSUMOWANIE ZAŁADOWANYCH DANYCH")
    print("="*80)
    
    tables_to_check = {
        'continents': 'Kontynenty',
        'regions': 'Regiony',
        'income_levels': 'Poziomy dochodów',
        'indicator_types': 'Typy wskaźników',
        'indicators': 'Wskaźniki',
        'keywords': 'Słowa kluczowe',
        'config': 'Konfiguracja',
        'countries': 'Kraje'
    }
    
    for table, description in tables_to_check.items():
        count = count_records(conn, table)
        print(f"{description:30} {table:25} {count:>5} rekordów")
    
    print("="*80)


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("WCZYTYWANIE STRUKTURY BAZY DANYCH I DANYCH POCZĄTKOWYCH")
    print("="*80)
    
    # Sprawdź czy plik schema.sql istnieje
    schema_path = Path(CONFIG_SCHEMA_FILE)
    if not schema_path.exists():
        print(f"\n✗ Plik schema.sql nie istnieje: {CONFIG_SCHEMA_FILE}")
        print(f"  Bieżący katalog: {os.getcwd()}")
        return 1
    
    print(f"\n✓ Znaleziono plik: {CONFIG_SCHEMA_FILE}")
    
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
        tables_status = check_tables_exist(conn)
        
        existing_tables = [t for t, exists in tables_status.items() if exists]
        missing_tables = [t for t, exists in tables_status.items() if not exists]
        
        if existing_tables:
            print(f"✓ Znaleziono {len(existing_tables)} istniejących tabel")
            if CONFIG_VERBOSE:
                print(f"  Tabele: {', '.join(existing_tables[:5])}{'...' if len(existing_tables) > 5 else ''}")
        
        if missing_tables:
            print(f"⚠ Brakuje {len(missing_tables)} tabel")
            if CONFIG_VERBOSE:
                print(f"  Brakujące: {', '.join(missing_tables)}")
        
        # Jeśli brakuje tabel lub wymuszono odtworzenie
        if missing_tables or CONFIG_FORCE_RECREATE:
            if CONFIG_FORCE_RECREATE:
                print("\n⚠ UWAGA: Wymuszono odtworzenie struktury (CONFIG_FORCE_RECREATE=True)")
                print("  To może usunąć istniejące dane!")
            
            print(f"\nWykonywanie pliku SQL: {CONFIG_SCHEMA_FILE}...")
            success, message = execute_sql_file(conn, schema_path)
            
            if success:
                print(f"✓ {message}")
            else:
                print(f"✗ {message}")
                return 1
        else:
            print("\n✓ Wszystkie tabele już istnieją - pomijam tworzenie struktury")
            print("  Wczytuję tylko dane początkowe (INSERT statements)...")
            
            # Wykonaj tylko INSERT statements
            # Wczytaj plik i wyciągnij tylko INSERT statements
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Znajdź sekcję z INSERT statements
            insert_section_start = sql_content.find('-- DANE POCZĄTKOWE')
            if insert_section_start != -1:
                insert_sql = sql_content[insert_section_start:]
                # Usuń komentarze końcowe
                insert_sql = insert_sql.split('-- KONIEC SCHEMATU')[0]
                
                # Wykonaj INSERT statements
                with conn.cursor() as cur:
                    # Podziel na komendy - szukaj INSERT nawet jeśli jest w wielu liniach
                    # Usuń komentarze jednoliniowe
                    lines = insert_sql.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        # Usuń komentarze jednoliniowe
                        if '--' in line:
                            line = line[:line.index('--')]
                        cleaned_lines.append(line)
                    
                    cleaned_sql = '\n'.join(cleaned_lines)
                    
                    # Podziel na komendy po średnikach
                    commands = []
                    current_command = []
                    for line in cleaned_sql.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        current_command.append(line)
                        if line.endswith(';'):
                            command = ' '.join(current_command)
                            if 'INSERT' in command.upper():
                                commands.append(command)
                            current_command = []
                    
                    # Jeśli zostało coś w current_command
                    if current_command:
                        command = ' '.join(current_command)
                        if 'INSERT' in command.upper():
                            commands.append(command)
                    
                    executed = 0
                    for i, command in enumerate(commands):
                        if command:
                            try:
                                cur.execute(command)
                                executed += 1
                                if CONFIG_VERBOSE:
                                    print(f"  Wykonano INSERT {executed}/{len(commands)}...")
                            except psycopg2.Error as e:
                                # ON CONFLICT DO NOTHING może zwracać błędy, które ignorujemy
                                error_str = str(e).lower()
                                if "duplicate key" not in error_str and "already exists" not in error_str:
                                    print(f"  Ostrzeżenie przy INSERT {i+1}: {e}")
                    
                    conn.commit()
                    print(f"✓ Wykonano {executed} INSERT statements")
        
        # Wyświetl podsumowanie
        display_data_summary(conn)
        
        # Sprawdź widoki
        print("\nSprawdzanie widoków...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            views = [row[0] for row in cur.fetchall()]
            if views:
                print(f"✓ Znaleziono {len(views)} widoków:")
                for view in views:
                    print(f"  - {view}")
            else:
                print("⚠ Nie znaleziono widoków")
        
        # Sprawdź funkcje
        print("\nSprawdzanie funkcji...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_type = 'FUNCTION'
                ORDER BY routine_name;
            """)
            functions = [row[0] for row in cur.fetchall()]
            if functions:
                print(f"✓ Znaleziono {len(functions)} funkcji:")
                for func in functions:
                    print(f"  - {func}")
            else:
                print("⚠ Nie znaleziono funkcji")
        
        print("\n" + "="*80)
        print("✓ Zakończono pomyślnie!")
        print("="*80)
        
        return 0
    
    except Exception as e:
        print(f"\n✗ Błąd: {e}")
        import traceback
        if CONFIG_VERBOSE:
            traceback.print_exc()
        return 1
    
    finally:
        conn.close()
        print("\n✓ Połączenie z bazą danych zamknięte")


if __name__ == "__main__":
    sys.exit(main())

