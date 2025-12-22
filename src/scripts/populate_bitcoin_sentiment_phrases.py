#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do wczytania fraz sentymentu BTC z pliku phrases.csv do tabeli bitcoin_sentiment_phrases.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

CONFIG_CSV_FILE = 'data/phrases.csv'                # Ścieżka do pliku CSV
CONFIG_VERBOSE = True                               # Czy wyświetlać szczegółowe informacje
CONFIG_DRY_RUN = False                              # Tryb testowy (nie zapisuje do bazy)

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import csv
from typing import Dict, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

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


def get_country_id_mapping(conn) -> Dict[str, int]:
    """
    Tworzy mapowanie country_code -> country_id.
    
    Returns:
        Słownik: kod_kraju -> id_kraju
    """
    mapping = {}
    with conn.cursor() as cur:
        cur.execute("SELECT id, iso2_code FROM countries;")
        for row in cur.fetchall():
            country_id, iso2_code = row
            if iso2_code:
                mapping[iso2_code.upper()] = country_id
    
    return mapping


def read_phrases_csv(csv_file: str) -> list:
    """
    Czyta dane z pliku CSV.
    
    Args:
        csv_file: Ścieżka do pliku CSV
    
    Returns:
        Lista słowników z danymi
    """
    phrases = []
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Plik {csv_file} nie istnieje")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            phrases.append({
                'country_code': row['country_code'].strip().upper(),
                'language_code': row['language_code'].strip(),
                'phrase': row['phrase'].strip(),
                'multiplier': float(row['multiplier'])
            })
    
    return phrases


def populate_phrases(conn, phrases: list, country_mapping: Dict[str, int]):
    """
    Wczytuje frazy do bazy danych.
    
    Args:
        conn: Połączenie z bazą danych
        phrases: Lista fraz z CSV
        country_mapping: Mapowanie country_code -> country_id
    """
    stats = {
        'processed': 0,
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    if CONFIG_DRY_RUN:
        print(f"  DRY RUN: Znaleziono {len(phrases)} fraz do wczytania")
        return stats
    
    with conn.cursor() as cur:
        for phrase_data in phrases:
            stats['processed'] += 1
            
            country_code = phrase_data['country_code']
            country_id = country_mapping.get(country_code)
            
            if not country_id:
                stats['skipped'] += 1
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Pominięto: brak kraju {country_code} w bazie")
                continue
            
            try:
                # Sprawdź czy fraza już istnieje
                cur.execute("""
                    SELECT id FROM bitcoin_sentiment_phrases
                    WHERE country_id = %s AND language_code = %s AND phrase = %s;
                """, (country_id, phrase_data['language_code'], phrase_data['phrase']))
                
                existing = cur.fetchone()
                
                if existing:
                    # Aktualizuj istniejący rekord
                    cur.execute("""
                        UPDATE bitcoin_sentiment_phrases
                        SET multiplier = %s, is_active = TRUE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s;
                    """, (phrase_data['multiplier'], existing[0]))
                    stats['updated'] += 1
                else:
                    # Wstaw nowy rekord
                    cur.execute("""
                        INSERT INTO bitcoin_sentiment_phrases 
                        (country_id, language_code, phrase, multiplier, is_active)
                        VALUES (%s, %s, %s, %s, TRUE);
                    """, (
                        country_id,
                        phrase_data['language_code'],
                        phrase_data['phrase'],
                        phrase_data['multiplier']
                    ))
                    stats['inserted'] += 1
                
                conn.commit()
                
            except psycopg2.Error as e:
                conn.rollback()
                stats['errors'] += 1
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Błąd dla {country_code}/{phrase_data['language_code']}/{phrase_data['phrase']}: {e}")
    
    return stats


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("WCZYTYWANIE FRAZ SENTYMENTU BTC Z PHRASES.CSV")
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
        # Utwórz mapowanie krajów
        print("\nTworzenie mapowania krajów...")
        country_mapping = get_country_id_mapping(conn)
        print(f"✓ Znaleziono {len(country_mapping)} krajów w bazie")
        
        # Wczytaj dane z CSV
        print(f"\nWczytywanie danych z {CONFIG_CSV_FILE}...")
        phrases = read_phrases_csv(CONFIG_CSV_FILE)
        print(f"✓ Wczytano {len(phrases)} fraz z CSV")
        
        # Sprawdź ile fraz można zmapować
        mappable = sum(1 for p in phrases if p['country_code'] in country_mapping)
        print(f"✓ {mappable} fraz można zmapować do krajów w bazie")
        
        # Wczytaj frazy do bazy
        print("\nWczytywanie fraz do bazy danych...")
        stats = populate_phrases(conn, phrases, country_mapping)
        
        # Podsumowanie
        print("\n" + "="*80)
        print("PODSUMOWANIE")
        print("="*80)
        print(f"Przetworzono: {stats['processed']}")
        print(f"Wstawiono: {stats['inserted']}")
        print(f"Zaktualizowano: {stats['updated']}")
        print(f"Pominięto: {stats['skipped']}")
        print(f"Błędy: {stats['errors']}")
        
        # Sprawdź łączną liczbę rekordów
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM bitcoin_sentiment_phrases;")
            total = cur.fetchone()[0]
            print(f"\nŁączna liczba rekordów w bitcoin_sentiment_phrases: {total}")
            
            cur.execute("SELECT COUNT(*) FROM bitcoin_sentiment_phrases WHERE is_active = TRUE;")
            active = cur.fetchone()[0]
            print(f"Liczba aktywnych rekordów: {active}")
        
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

