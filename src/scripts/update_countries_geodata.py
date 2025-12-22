#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do uzupełniania brakujących danych geograficznych w tabeli countries.
Pobiera: latitude, longitude, timezone, utc_offset z Geonames.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

# --- Parametry przetwarzania ---
CONFIG_COUNTRY_CODES = None                     # Lista kodów krajów do przetworzenia (None = wszystkie z brakującymi danymi)
CONFIG_BATCH_SIZE = 10                          # Liczba krajów przetwarzanych na raz
CONFIG_VERBOSE = True                           # Czy wyświetlać szczegółowe informacje
CONFIG_DRY_RUN = False                          # Tryb testowy (nie zapisuje do bazy)
CONFIG_UPDATE_ONLY_MISSING = True               # Czy aktualizować tylko kraje z brakującymi danymi

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg2

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.providers.geonames_provider import GeonamesProvider

# Załaduj zmienne środowiskowe
load_dotenv()


def get_database_connection():
    """
    Tworzy połączenie z bazą danych.
    
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


def get_countries_with_missing_geodata(conn) -> List[Tuple[str, str]]:
    """
    Pobiera listę krajów z brakującymi danymi geograficznymi.
    
    Args:
        conn: Połączenie z bazą danych
    
    Returns:
        Lista tupli (iso2_code, name_en) krajów z brakującymi danymi
    """
    with conn.cursor() as cur:
        query = """
            SELECT iso2_code, name_en 
            FROM countries 
            WHERE (latitude IS NULL OR longitude IS NULL OR timezone IS NULL OR utc_offset IS NULL)
            AND is_active = TRUE
            ORDER BY iso2_code;
        """
        cur.execute(query)
        return cur.fetchall()


def get_country_geodata_from_geonames(
    geonames_provider: GeonamesProvider,
    country_code: str,
    lang: str = 'pl'
) -> Optional[Dict]:
    """
    Pobiera dane geograficzne o kraju z Geonames.
    
    Args:
        geonames_provider: Instancja GeonamesProvider
        country_code: Kod kraju ISO 2
        lang: Język odpowiedzi
    
    Returns:
        Słownik z danymi geograficznymi lub None
    """
    try:
        country_info = geonames_provider.get_country_info(country_code, lang=lang)
        if not country_info:
            return None
        
        # Pobierz współrzędne
        lat = None
        lng = None
        try:
            lat_str = country_info.get('lat', '')
            lng_str = country_info.get('lng', '')
            if lat_str:
                lat = float(lat_str)
            if lng_str:
                lng = float(lng_str)
        except:
            pass
        
        # Jeśli nie ma współrzędnych w country_info, spróbuj pobrać stolicę
        if not lat or not lng:
            capital_name = country_info.get('capital', '')
            if capital_name:
                try:
                    capital_info = geonames_provider.get_capital(country_code, lang=lang)
                    if capital_info:
                        try:
                            lat_str = capital_info.get('lat', '')
                            lng_str = capital_info.get('lng', '')
                            if lat_str:
                                lat = float(lat_str)
                            if lng_str:
                                lng = float(lng_str)
                        except:
                            pass
                except:
                    pass
        
        # Pobierz strefę czasową jeśli mamy współrzędne
        timezone_id = None
        utc_offset = None
        
        if lat and lng:
            try:
                timezone_info = geonames_provider.get_timezone(lat, lng)
                if timezone_info:
                    timezone_id = timezone_info.get('timezoneId', '')
                    try:
                        gmt_offset = timezone_info.get('gmtOffset')
                        if gmt_offset is not None:
                            utc_offset = int(gmt_offset) * 60  # Konwersja godzin na minuty
                    except:
                        pass
            except Exception as e:
                if CONFIG_VERBOSE:
                    print(f"    ⚠ Błąd pobierania strefy czasowej: {e}")
        
        return {
            'latitude': lat,
            'longitude': lng,
            'timezone': timezone_id,
            'utc_offset': utc_offset
        }
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd Geonames dla {country_code}: {e}")
        return None


def update_country_geodata(
    conn,
    country_code: str,
    geodata: Dict
) -> Tuple[bool, str]:
    """
    Aktualizuje dane geograficzne kraju w bazie danych.
    
    Args:
        conn: Połączenie z bazą danych
        country_code: Kod kraju ISO 2
        geodata: Słownik z danymi geograficznymi
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if CONFIG_DRY_RUN:
        return True, "DRY RUN - nie zaktualizowano"
    
    try:
        with conn.cursor() as cur:
            # Przygotuj pola do aktualizacji
            update_fields = []
            update_values = []
            
            if geodata.get('latitude') is not None:
                update_fields.append("latitude = %s")
                update_values.append(geodata['latitude'])
            
            if geodata.get('longitude') is not None:
                update_fields.append("longitude = %s")
                update_values.append(geodata['longitude'])
            
            if geodata.get('timezone') is not None:
                update_fields.append("timezone = %s")
                update_values.append(geodata['timezone'])
            
            if geodata.get('utc_offset') is not None:
                update_fields.append("utc_offset = %s")
                update_values.append(geodata['utc_offset'])
            
            if not update_fields:
                return True, "Brak danych do aktualizacji"
            
            # Dodaj updated_at i country_code
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(country_code)
            
            query = f"""
                UPDATE countries 
                SET {', '.join(update_fields)}
                WHERE iso2_code = %s
                RETURNING id;
            """
            
            cur.execute(query, update_values)
            result = cur.fetchone()
            
            if result:
                conn.commit()
                updated_fields = [f for f in ['latitude', 'longitude', 'timezone', 'utc_offset'] 
                                if geodata.get(f) is not None]
                return True, f"Zaktualizowano: {', '.join(updated_fields)}"
            else:
                return False, "Kraj nie został znaleziony"
    
    except psycopg2.Error as e:
        conn.rollback()
        return False, f"Błąd SQL: {e}"


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("UZUPEŁNIANIE DANYCH GEOGRAFICZNYCH W TABELI COUNTRIES")
    print("="*80)
    
    if CONFIG_DRY_RUN:
        print("\n⚠ TRYB TESTOWY (DRY RUN) - dane nie będą zapisane do bazy")
    
    # Inicjalizacja providera
    print("\nInicjalizacja GeonamesProvider...")
    
    try:
        geonames_provider = GeonamesProvider()
        if CONFIG_VERBOSE:
            print("✓ GeonamesProvider zainicjalizowany")
    except Exception as e:
        print(f"\n✗ Błąd inicjalizacji GeonamesProvider: {e}")
        print("  Upewnij się, że zmienna GEONAMES_LOGIN jest ustawiona w pliku .env")
        return 1
    
    # Połącz z bazą danych
    try:
        print("\nŁączenie z bazą danych...")
        conn = get_database_connection()
        print("✓ Połączono z bazą danych")
    except Exception as e:
        print(f"\n✗ Błąd połączenia: {e}")
        return 1
    
    try:
        # Pobierz listę krajów do przetworzenia
        if CONFIG_COUNTRY_CODES:
            country_codes = [code.upper() for code in CONFIG_COUNTRY_CODES]
            print(f"\nPrzetwarzanie wybranych krajów: {len(country_codes)}")
        elif CONFIG_UPDATE_ONLY_MISSING:
            countries_list = get_countries_with_missing_geodata(conn)
            country_codes = [row[0] for row in countries_list]
            print(f"\nZnaleziono {len(country_codes)} krajów z brakującymi danymi geograficznymi")
        else:
            # Wszystkie kraje
            with conn.cursor() as cur:
                cur.execute("SELECT iso2_code FROM countries WHERE is_active = TRUE ORDER BY iso2_code;")
                country_codes = [row[0] for row in cur.fetchall()]
            print(f"\nPrzetwarzanie wszystkich krajów: {len(country_codes)}")
        
        if not country_codes:
            print("\n✓ Nie znaleziono krajów do przetworzenia")
            return 0
        
        # Statystyki
        stats = {
            'processed': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Przetwarzaj w batchach
        for i in range(0, len(country_codes), CONFIG_BATCH_SIZE):
            batch = country_codes[i:i+CONFIG_BATCH_SIZE]
            batch_num = (i // CONFIG_BATCH_SIZE) + 1
            total_batches = (len(country_codes) + CONFIG_BATCH_SIZE - 1) // CONFIG_BATCH_SIZE
            
            print(f"\n{'='*80}")
            print(f"BATCH {batch_num}/{total_batches} - Przetwarzanie {len(batch)} krajów")
            print(f"{'='*80}")
            
            for country_code in batch:
                stats['processed'] += 1
                
                if CONFIG_VERBOSE:
                    # Pobierz nazwę kraju
                    with conn.cursor() as cur:
                        cur.execute("SELECT name_en FROM countries WHERE iso2_code = %s;", (country_code,))
                        result = cur.fetchone()
                        country_name = result[0] if result else country_code
                    
                    print(f"\n[{stats['processed']}/{len(country_codes)}] {country_code}: {country_name}")
                
                # Pobierz dane geograficzne z Geonames
                if CONFIG_VERBOSE:
                    print("  Pobieranie danych geograficznych z Geonames...")
                
                geodata = get_country_geodata_from_geonames(geonames_provider, country_code)
                
                if not geodata:
                    stats['errors'] += 1
                    if CONFIG_VERBOSE:
                        print("  ✗ Nie udało się pobrać danych geograficznych")
                    continue
                
                # Sprawdź czy są jakieś dane do aktualizacji
                has_data = any(geodata.get(key) is not None 
                             for key in ['latitude', 'longitude', 'timezone', 'utc_offset'])
                
                if not has_data:
                    stats['skipped'] += 1
                    if CONFIG_VERBOSE:
                        print("  ⚠ Brak danych geograficznych w Geonames")
                    continue
                
                # Wyświetl co zostało znalezione
                if CONFIG_VERBOSE:
                    found = []
                    if geodata.get('latitude') is not None:
                        found.append(f"lat={geodata['latitude']}")
                    if geodata.get('longitude') is not None:
                        found.append(f"lng={geodata['longitude']}")
                    if geodata.get('timezone'):
                        found.append(f"tz={geodata['timezone']}")
                    if geodata.get('utc_offset') is not None:
                        found.append(f"offset={geodata['utc_offset']}min")
                    if found:
                        print(f"  ✓ Znaleziono: {', '.join(found)}")
                
                # Aktualizuj w bazie
                success, message = update_country_geodata(conn, country_code, geodata)
                
                if success:
                    if 'Zaktualizowano' in message:
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                    
                    if CONFIG_VERBOSE:
                        print(f"  ✓ {message}")
                else:
                    stats['errors'] += 1
                    if CONFIG_VERBOSE:
                        print(f"  ✗ {message}")
            
            # Krótka przerwa między batchami
            if i + CONFIG_BATCH_SIZE < len(country_codes):
                import time
                time.sleep(1)
        
        # Podsumowanie
        print("\n" + "="*80)
        print("PODSUMOWANIE")
        print("="*80)
        print(f"Przetworzono:     {stats['processed']} krajów")
        print(f"Zaktualizowano:  {stats['updated']} krajów")
        print(f"Pominięto:       {stats['skipped']} krajów")
        print(f"Błędy:           {stats['errors']} krajów")
        print("="*80)
        
        # Sprawdź ile krajów ma kompletne dane geograficzne
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM countries 
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL 
                AND timezone IS NOT NULL 
                AND utc_offset IS NOT NULL
                AND is_active = TRUE;
            """)
            complete_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT COUNT(*) 
                FROM countries 
                WHERE is_active = TRUE;
            """)
            total_count = cur.fetchone()[0]
            
            print(f"\nKraje z kompletnymi danymi geograficznymi: {complete_count}/{total_count}")
        
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

