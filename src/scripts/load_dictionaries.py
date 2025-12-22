#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wczytania danych z dictionaries.sql do bazy danych.
Dostosowuje region_code i country codes do struktury naszej bazy danych.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

CONFIG_VERBOSE = True                           # Czy wyświetlać szczegółowe informacje
CONFIG_DRY_RUN = False                          # Tryb testowy (nie zapisuje do bazy)
CONFIG_SQL_FILE = 'data/dictionaries.sql'       # Ścieżka do pliku SQL

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import re
from typing import Dict, Optional
from dotenv import load_dotenv
import psycopg2

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.models.regions import PyTrendsRegions

# Załaduj zmienne środowiskowe
load_dotenv()


def get_database_connection():
    """Tworzy połączenie z bazą danych."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL nie jest ustawiony w pliku .env")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Błąd połączenia z bazą danych: {e}")


def get_region_code_mapping() -> Dict[str, str]:
    """
    Mapuje kody krajów ISO 2 na kody regionów z naszej bazy.
    
    Returns:
        Słownik: kod_kraju -> kod_regionu
    """
    mapping = {}
    
    # Dla każdego kraju znajdź jego region
    for country_code in PyTrendsRegions.REGIONS.keys():
        countries = PyTrendsRegions.get_region_countries(country_code)
        for country in countries:
            iso2 = country.get('code')
            if iso2:
                # Użyj pierwszego regionu (priorytetowy)
                if iso2 not in mapping:
                    mapping[iso2] = country_code
    
    # Dodatkowe mapowania dla krajów które mogą nie być w regionach
    additional_mappings = {
        'CN': 'china',
        'HK': 'china',
        'MO': 'china',
        'TW': 'china',
        'US': 'north_america',
        'CA': 'north_america',
        'DE': 'europe',
        'GB': 'europe',
        'FR': 'europe',
        'PL': 'europe',
        'JP': 'asia_pacific',
        'KR': 'asia_pacific',
        'SG': 'asia_pacific',
        'IN': 'asia_pacific',
        'AU': 'asia_pacific',
        'AE': 'middle_east',
        'SA': 'middle_east',
        'BR': 'emerging_markets',
        'AR': 'emerging_markets',
        'TR': 'emerging_markets',
        'NG': 'emerging_markets',
        'RU': 'emerging_markets',
    }
    
    mapping.update(additional_mappings)
    return mapping


def map_country_code_to_region_code(country_code: str) -> Optional[str]:
    """
    Mapuje kod kraju ISO 2 na kod regionu z naszej bazy.
    
    Args:
        country_code: Kod kraju ISO 2
    
    Returns:
        Kod regionu lub None
    """
    mapping = get_region_code_mapping()
    return mapping.get(country_code.upper())


def get_region_id_from_code(conn, region_code: str) -> Optional[int]:
    """Pobiera ID regionu z bazy na podstawie kodu."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM regions WHERE code = %s;", (region_code,))
        result = cur.fetchone()
        return result[0] if result else None


def adapt_sql_for_our_database(sql_content: str, conn) -> str:
    """
    Dostosowuje SQL do naszej struktury bazy danych.
    - Mapuje region_code z kodów krajów na kody regionów
    - Usuwa OWNER TO piotradamczyk
    - Dostosowuje ON CONFLICT jeśli potrzeba
    """
    # Mapowanie kodów krajów na regiony
    country_to_region = get_region_code_mapping()
    
    # Mapowanie specjalnych kodów (zostają bez zmian)
    special_mappings = {
        'GLOBAL': 'GLOBAL',
        'ALGO': 'ALGO',
        'OPTIONS': 'OPTIONS',
        'SOCIAL': 'SOCIAL',
        'EVENT': 'EVENT',
        'MACRO': 'MACRO',
    }
    
    # Usuń OWNER TO
    sql_content = re.sub(r"ALTER TABLE.*OWNER TO.*?;", "", sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r"ALTER SEQUENCE.*OWNER TO.*?;", "", sql_content, flags=re.MULTILINE)
    
    # Mapuj region_code w VALUES - musimy znaleźć pozycję region_code w kolumnach
    # i zamienić odpowiednią wartość w VALUES
    lines = sql_content.split('\n')
    result_lines = []
    
    for line in lines:
        # Sprawdź czy to INSERT statement
        if 'INSERT INTO' in line.upper() and 'VALUES' in line.upper():
            # Znajdź pozycję region_code w kolumnach
            col_match = re.search(r'\(([^)]+)\)', line)
            if col_match:
                columns = [c.strip() for c in col_match.group(1).split(',')]
                try:
                    region_code_idx = columns.index('region_code')
                except ValueError:
                    # region_code nie jest w tej tabeli
                    result_lines.append(line)
                    continue
                
                # Znajdź VALUES i zamień odpowiednią wartość
                values_match = re.search(r'VALUES\s*\(([^)]+)\)', line, re.IGNORECASE)
                if values_match:
                    values = []
                    current_value = ''
                    in_quotes = False
                    quote_char = None
                    
                    # Parsuj wartości ręcznie (aby obsłużyć zagnieżdżone nawiasy i cudzysłowy)
                    values_str = values_match.group(1)
                    i = 0
                    while i < len(values_str):
                        char = values_str[i]
                        
                        if char in ("'", '"') and (i == 0 or values_str[i-1] != '\\'):
                            if not in_quotes:
                                in_quotes = True
                                quote_char = char
                            elif char == quote_char:
                                in_quotes = False
                                quote_char = None
                            current_value += char
                        elif char == ',' and not in_quotes:
                            values.append(current_value.strip())
                            current_value = ''
                        else:
                            current_value += char
                        i += 1
                    
                    if current_value:
                        values.append(current_value.strip())
                    
                    # Zamień wartość na pozycji region_code_idx
                    if region_code_idx < len(values):
                        old_value = values[region_code_idx].strip()
                        # Usuń cudzysłowy jeśli są
                        if old_value.startswith("'") and old_value.endswith("'"):
                            country_code = old_value[1:-1]
                            
                            # Sprawdź czy to specjalny kod
                            if country_code not in special_mappings:
                                # Mapuj kod kraju na region
                                mapped_region = map_country_code_to_region_code(country_code)
                                if mapped_region:
                                    values[region_code_idx] = f"'{mapped_region}'"
                    
                    # Zbuduj nową linię
                    new_values = ', '.join(values)
                    new_line = re.sub(r'VALUES\s*\([^)]+\)', f'VALUES ({new_values})', line, flags=re.IGNORECASE)
                    result_lines.append(new_line)
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)
    
    sql_content = '\n'.join(result_lines)
    
    return sql_content


def create_dictionary_tables(conn):
    """Tworzy tabele dictionary_* jeśli nie istnieją."""
    tables_sql = """
    -- Tabela: dictionary_algo_events
    CREATE TABLE IF NOT EXISTS dictionary_algo_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(10),
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20) DEFAULT 'ALGO',
        news_sensitivity VARCHAR(20),
        category VARCHAR(20) DEFAULT 'ALGO',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabela: dictionary_global_events
    CREATE TABLE IF NOT EXISTS dictionary_global_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(10) DEFAULT 'GLOBAL',
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20),
        news_sensitivity VARCHAR(20),
        category VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabela: dictionary_macro_events
    CREATE TABLE IF NOT EXISTS dictionary_macro_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(10),
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20),
        news_sensitivity VARCHAR(20),
        category VARCHAR(20) DEFAULT 'MACRO',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabela: dictionary_options_events
    CREATE TABLE IF NOT EXISTS dictionary_options_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(10),
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20),
        news_sensitivity VARCHAR(20),
        category VARCHAR(20) DEFAULT 'EVENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabela: dictionary_region_events
    CREATE TABLE IF NOT EXISTS dictionary_region_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(20) NOT NULL,
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20),
        news_sensitivity VARCHAR(20),
        category VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabela: dictionary_social_events
    CREATE TABLE IF NOT EXISTS dictionary_social_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(10),
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20) DEFAULT 'RETAIL',
        news_sensitivity VARCHAR(20) DEFAULT 'HIGH',
        category VARCHAR(20) DEFAULT 'SESSION',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabela: dictionary_special_events
    CREATE TABLE IF NOT EXISTS dictionary_special_events (
        id SERIAL PRIMARY KEY,
        phase_code VARCHAR(100) NOT NULL,
        region_code VARCHAR(10),
        label VARCHAR(200) NOT NULL,
        description TEXT,
        utc_start TIME NOT NULL,
        utc_end TIME NOT NULL,
        wraps_midnight BOOLEAN DEFAULT FALSE NOT NULL,
        priority INTEGER DEFAULT 10 NOT NULL,
        volatility_level VARCHAR(20),
        volume_impact VARCHAR(20),
        typical_duration_min INTEGER,
        trading_pattern VARCHAR(20),
        dominant_actors VARCHAR(20),
        news_sensitivity VARCHAR(20),
        category VARCHAR(20) DEFAULT 'EVENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(tables_sql)
            conn.commit()
            if CONFIG_VERBOSE:
                print("✓ Tabele dictionary_* zostały utworzone")
    except psycopg2.Error as e:
        conn.rollback()
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd tworzenia tabel (mogą już istnieć): {e}")


def load_dictionaries_from_sql(conn):
    """Wczytuje dane z dictionaries.sql do bazy."""
    if not os.path.exists(CONFIG_SQL_FILE):
        print(f"✗ Plik {CONFIG_SQL_FILE} nie istnieje")
        return
    
    print(f"\nWczytywanie danych z {CONFIG_SQL_FILE}...")
    
    with open(CONFIG_SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Dostosuj SQL do naszej bazy
    if CONFIG_VERBOSE:
        print("  Dostosowywanie SQL do struktury naszej bazy...")
    
    adapted_sql = adapt_sql_for_our_database(sql_content, conn)
    
    # Podziel na pojedyncze komendy
    # Usuń komentarze i puste linie
    commands = []
    current_command = []
    
    for line in adapted_sql.split('\n'):
        # Usuń komentarze z końca linii
        if '--' in line:
            line = line.split('--')[0]
        
        line = line.strip()
        
        # Pomiń puste linie i linie zaczynające się od komentarza
        if not line or line.startswith('--') or line.startswith('TOC'):
            continue
        
        # Jeśli linia kończy się średnikiem, to koniec komendy
        if line.endswith(';'):
            current_command.append(line)
            if current_command:
                commands.append(' '.join(current_command))
                current_command = []
        else:
            current_command.append(line)
    
    if CONFIG_DRY_RUN:
        print(f"  DRY RUN: Znaleziono {len(commands)} komend SQL")
        return
    
    # Wykonaj komendy
    stats = {'processed': 0, 'success': 0, 'errors': 0}
    
    for cmd in commands:
        if not cmd.strip():
            continue
        
        stats['processed'] += 1
        
        try:
            with conn.cursor() as cur:
                cur.execute(cmd)
                conn.commit()
                stats['success'] += 1
        except psycopg2.Error as e:
            conn.rollback()
            # Ignoruj błędy "already exists" i "duplicate"
            error_msg = str(e)
            if 'already exists' not in error_msg.lower() and 'duplicate' not in error_msg.lower():
                stats['errors'] += 1
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Błąd wykonania komendy: {error_msg[:100]}")
            else:
                stats['success'] += 1  # Traktuj jako sukces (już istnieje)
    
    print(f"\n✓ Zakończono: przetworzono {stats['processed']}, sukces: {stats['success']}, błędy: {stats['errors']}")


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("WCZYTYWANIE DANYCH Z DICTIONARIES.SQL")
    print("="*80)
    
    if CONFIG_DRY_RUN:
        print("\n⚠ TRYB TESTOWY (DRY RUN) - dane nie będą zapisane do bazy")
    
    # Połącz z bazą danych
    try:
        print("\nŁączenie z bazą danych...")
        conn = get_database_connection()
        print("✓ Połączono z bazą danych")
    except Exception as e:
        print(f"\n✗ Błąd połączenia: {e}")
        return 1
    
    try:
        # Utwórz tabele jeśli nie istnieją
        print("\nTworzenie tabel dictionary_*...")
        create_dictionary_tables(conn)
        
        # Wczytaj dane
        load_dictionaries_from_sql(conn)
        
        # Podsumowanie
        print("\n" + "="*80)
        print("PODSUMOWANIE")
        print("="*80)
        
        tables = [
            'dictionary_algo_events',
            'dictionary_global_events',
            'dictionary_macro_events',
            'dictionary_options_events',
            'dictionary_region_events',
            'dictionary_social_events',
            'dictionary_special_events'
        ]
        
        with conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cur.fetchone()[0]
                    print(f"{table}: {count} rekordów")
                except:
                    print(f"{table}: tabela nie istnieje")
        
        print("\n✓ Zakończono pomyślnie!")
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

