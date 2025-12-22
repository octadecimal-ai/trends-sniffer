#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do uzupełniania tabeli timezones danymi o strefach czasowych.
Pobiera wszystkie strefy czasowe używane przez kraje i zapisuje je do bazy.
Dla każdego kraju określa wszystkie strefy czasowe które w nim obowiązują.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

# --- Parametry przetwarzania ---
CONFIG_VERBOSE = True                           # Czy wyświetlać szczegółowe informacje
CONFIG_DRY_RUN = False                          # Tryb testowy (nie zapisuje do bazy)
CONFIG_UPDATE_EXISTING = True                   # Czy aktualizować istniejące strefy czasowe
CONFIG_BATCH_SIZE = 20                          # Liczba krajów przetwarzanych na raz

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import json
import pytz
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.providers.geonames_provider import GeonamesProvider
from src.models.countries import PyTrendsCountries

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


def get_timezone_info(timezone_id: str) -> Dict:
    """
    Pobiera informacje o strefie czasowej z biblioteki pytz.
    
    Args:
        timezone_id: IANA timezone ID (np. 'Europe/Warsaw')
    
    Returns:
        Słownik z informacjami o strefie czasowej
    """
    try:
        tz = pytz.timezone(timezone_id)
        
        # Pobierz standardowy offset (bez DST) - użyj stycznia (zima, bez DST)
        jan_dt = tz.localize(datetime(2024, 1, 15, 12, 0, 0))
        standard_offset = jan_dt.utcoffset()
        
        # Sprawdź czy używa DST - porównaj styczeń z lipcem
        jul_dt = tz.localize(datetime(2024, 7, 15, 12, 0, 0))
        jul_offset = jul_dt.utcoffset()
        
        uses_dst = (standard_offset != jul_offset)
        
        # Pobierz offset DST jeśli istnieje
        dst_offset = None
        if uses_dst:
            dst_offset = int((jul_offset - standard_offset).total_seconds() / 60)
        
        # Pobierz skrót strefy czasowej
        abbreviation = jan_dt.strftime('%Z')
        
        # Nazwa strefy (bez prefiksu kontynentu)
        name_parts = timezone_id.split('/')
        if len(name_parts) > 1:
            name = name_parts[-1].replace('_', ' ')
        else:
            name = timezone_id
        
        return {
            'timezone_id': timezone_id,
            'name': name,
            'abbreviation': abbreviation if abbreviation else None,
            'utc_offset_minutes': int(standard_offset.total_seconds() / 60),
            'dst_offset_minutes': dst_offset,
            'uses_dst': uses_dst,
            'dst_start_rule': None,  # Można dodać później z zewnętrznego źródła
            'dst_end_rule': None,     # Można dodać później z zewnętrznego źródła
            'description': f"Timezone: {timezone_id}"
        }
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd pobierania informacji o strefie {timezone_id}: {e}")
        return None


def get_country_timezones_from_pytz(country_code: str) -> List[str]:
    """
    Pobiera listę stref czasowych dla kraju z biblioteki pytz.
    Używa wbudowanego mapowania country_timezones.
    
    Args:
        country_code: Kod kraju ISO 2
    
    Returns:
        Lista IANA timezone IDs
    """
    try:
        # pytz.country_timezones mapuje kody krajów ISO 2 na listy stref czasowych
        timezones = pytz.country_timezones.get(country_code.upper(), [])
        return sorted(timezones) if timezones else []
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd pobierania stref czasowych z pytz dla {country_code}: {e}")
        return []


def get_country_timezones_from_geonames(
    geonames_provider: GeonamesProvider,
    country_code: str
) -> List[str]:
    """
    Pobiera listę stref czasowych dla kraju.
    Najpierw próbuje z pytz.country_timezones, potem z Geonames jako fallback.
    
    Args:
        geonames_provider: Instancja GeonamesProvider
        country_code: Kod kraju ISO 2
    
    Returns:
        Lista IANA timezone IDs
    """
    # Najpierw spróbuj z pytz (najbardziej niezawodne)
    timezones = get_country_timezones_from_pytz(country_code)
    
    if timezones:
        return timezones
    
    # Fallback: spróbuj z Geonames (dla krajów które nie są w pytz)
    timezones_set = set()
    
    try:
        # Pobierz informacje o kraju
        country_info = geonames_provider.get_country_info(country_code)
        if not country_info:
            return []
        
        # Pobierz strefę czasową ze stolicy
        capital = country_info.get('capital', '')
        if capital:
            try:
                capital_info = geonames_provider.get_capital(country_code)
                if capital_info:
                    lat = capital_info.get('lat')
                    lng = capital_info.get('lng')
                    if lat and lng:
                        tz_info = geonames_provider.get_timezone(float(lat), float(lng))
                        if tz_info and tz_info.get('timezoneId'):
                            timezones_set.add(tz_info['timezoneId'])
            except Exception as e:
                if CONFIG_VERBOSE:
                    print(f"      ⚠ Błąd pobierania stolicy: {e}")
        
        # Spróbuj użyć bounding box
        bbox_north = country_info.get('north')
        bbox_south = country_info.get('south')
        bbox_east = country_info.get('east')
        bbox_west = country_info.get('west')
        
        if all([bbox_north, bbox_south, bbox_east, bbox_west]):
            # Pobierz kilka punktów w bounding box
            lat_step = (float(bbox_north) - float(bbox_south)) / 3
            lng_step = (float(bbox_east) - float(bbox_west)) / 3
            
            for i in range(4):
                for j in range(4):
                    lat = float(bbox_south) + i * lat_step
                    lng = float(bbox_west) + j * lng_step
                    lat = round(lat, 2)
                    lng = round(lng, 2)
                    
                    try:
                        tz_info = geonames_provider.get_timezone(lat, lng)
                        if tz_info and tz_info.get('timezoneId'):
                            timezones_set.add(tz_info['timezoneId'])
                    except:
                        continue
        
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd pobierania stref czasowych z Geonames dla {country_code}: {e}")
    
    return sorted(list(timezones_set))


def get_all_iana_timezones() -> List[str]:
    """
    Pobiera listę wszystkich IANA timezone IDs z biblioteki pytz.
    
    Returns:
        Lista wszystkich IANA timezone IDs
    """
    return sorted(pytz.all_timezones)


def insert_or_update_timezone(conn, timezone_data: Dict) -> Tuple[bool, int, str]:
    """
    Wstawia lub aktualizuje strefę czasową w bazie danych.
    
    Args:
        conn: Połączenie z bazą danych
        timezone_data: Słownik z danymi strefy czasowej
    
    Returns:
        tuple: (success: bool, timezone_id: int, message: str)
    """
    if CONFIG_DRY_RUN:
        return True, 0, "DRY RUN - nie zapisano"
    
    try:
        with conn.cursor() as cur:
            # Sprawdź czy strefa już istnieje
            cur.execute("SELECT id FROM timezones WHERE timezone_id = %s;", (timezone_data['timezone_id'],))
            existing = cur.fetchone()
            
            if existing:
                if not CONFIG_UPDATE_EXISTING:
                    return True, existing[0], "Pominięto (już istnieje)"
                
                # Aktualizuj
                timezone_db_id = existing[0]
                update_fields = []
                update_values = []
                
                for key in ['name', 'abbreviation', 'utc_offset_minutes', 'dst_offset_minutes', 
                           'uses_dst', 'dst_start_rule', 'dst_end_rule', 'description']:
                    if key in timezone_data and timezone_data[key] is not None:
                        update_fields.append(f"{key} = %s")
                        update_values.append(timezone_data[key])
                
                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    update_values.append(timezone_data['timezone_id'])
                    
                    query = f"""
                        UPDATE timezones 
                        SET {', '.join(update_fields)}
                        WHERE timezone_id = %s;
                    """
                    cur.execute(query, update_values)
                    conn.commit()
                    return True, timezone_db_id, f"Aktualizowano (ID: {timezone_db_id})"
                else:
                    return True, timezone_db_id, "Brak zmian"
            else:
                # Wstaw nową
                fields = ['timezone_id', 'name', 'abbreviation', 'utc_offset_minutes', 
                         'dst_offset_minutes', 'uses_dst', 'dst_start_rule', 'dst_end_rule', 
                         'description']
                placeholders = ['%s'] * len(fields)
                values = [timezone_data.get(f) for f in fields]
                
                query = f"""
                    INSERT INTO timezones ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING id;
                """
                cur.execute(query, values)
                timezone_db_id = cur.fetchone()[0]
                conn.commit()
                return True, timezone_db_id, f"Wstawiono (ID: {timezone_db_id})"
    
    except psycopg2.Error as e:
        conn.rollback()
        return False, 0, f"Błąd SQL: {e}"


def update_country_timezones(conn, country_code: str, timezone_ids: List[int]) -> Tuple[bool, str]:
    """
    Aktualizuje tablicę timezone_ids dla kraju.
    
    Args:
        conn: Połączenie z bazą danych
        country_code: Kod kraju ISO 2
        timezone_ids: Lista ID stref czasowych z tabeli timezones
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if CONFIG_DRY_RUN:
        return True, "DRY RUN - nie zaktualizowano"
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE countries 
                SET timezone_ids = %s, updated_at = CURRENT_TIMESTAMP
                WHERE iso2_code = %s
                RETURNING id;
            """, (timezone_ids, country_code))
            
            result = cur.fetchone()
            if result:
                conn.commit()
                return True, f"Zaktualizowano {len(timezone_ids)} stref czasowych"
            else:
                return False, "Kraj nie został znaleziony"
    
    except psycopg2.Error as e:
        conn.rollback()
        return False, f"Błąd SQL: {e}"


def get_timezone_id_from_db(conn, timezone_iana_id: str) -> Optional[int]:
    """
    Pobiera ID strefy czasowej z bazy na podstawie IANA timezone ID.
    
    Args:
        conn: Połączenie z bazą danych
        timezone_iana_id: IANA timezone ID
    
    Returns:
        ID strefy czasowej z bazy lub None
    """
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM timezones WHERE timezone_id = %s;", (timezone_iana_id,))
        result = cur.fetchone()
        return result[0] if result else None


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("UZUPEŁNIANIE TABELI TIMEZONES I MAPOWANIE STREF CZASOWYCH DO KRAJÓW")
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
        # KROK 1: Pobierz wszystkie IANA timezones i zapisz do bazy
        print("\n" + "="*80)
        print("KROK 1: Ładowanie wszystkich IANA timezones do bazy")
        print("="*80)
        
        all_timezones = get_all_iana_timezones()
        print(f"Znaleziono {len(all_timezones)} stref czasowych IANA")
        
        stats_timezones = {
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for tz_id in all_timezones:
            stats_timezones['processed'] += 1
            
            if CONFIG_VERBOSE and stats_timezones['processed'] % 100 == 0:
                print(f"  Przetworzono {stats_timezones['processed']}/{len(all_timezones)} stref...")
            
            tz_info = get_timezone_info(tz_id)
            if not tz_info:
                stats_timezones['errors'] += 1
                continue
            
            success, db_id, message = insert_or_update_timezone(conn, tz_info)
            
            if success:
                if 'Wstawiono' in message:
                    stats_timezones['inserted'] += 1
                elif 'Aktualizowano' in message:
                    stats_timezones['updated'] += 1
                else:
                    stats_timezones['skipped'] += 1
            else:
                stats_timezones['errors'] += 1
        
        print(f"\n✓ Zakończono ładowanie stref czasowych:")
        print(f"  Przetworzono: {stats_timezones['processed']}")
        print(f"  Wstawiono: {stats_timezones['inserted']}")
        print(f"  Zaktualizowano: {stats_timezones['updated']}")
        print(f"  Pominięto: {stats_timezones['skipped']}")
        print(f"  Błędy: {stats_timezones['errors']}")
        
        # KROK 2: Dla każdego kraju pobierz jego strefy czasowe i zmapuj
        print("\n" + "="*80)
        print("KROK 2: Mapowanie stref czasowych do krajów")
        print("="*80)
        
        # Pobierz wszystkie kraje z bazy
        with conn.cursor() as cur:
            cur.execute("SELECT iso2_code, name_en FROM countries WHERE is_active = TRUE ORDER BY iso2_code;")
            countries = cur.fetchall()
        
        print(f"Znaleziono {len(countries)} krajów do przetworzenia")
        
        stats_countries = {
            'processed': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Przetwarzaj w batchach
        for i in range(0, len(countries), CONFIG_BATCH_SIZE):
            batch = countries[i:i+CONFIG_BATCH_SIZE]
            batch_num = (i // CONFIG_BATCH_SIZE) + 1
            total_batches = (len(countries) + CONFIG_BATCH_SIZE - 1) // CONFIG_BATCH_SIZE
            
            print(f"\n{'='*80}")
            print(f"BATCH {batch_num}/{total_batches} - Przetwarzanie {len(batch)} krajów")
            print(f"{'='*80}")
            
            for country_code, country_name in batch:
                stats_countries['processed'] += 1
                
                if CONFIG_VERBOSE:
                    print(f"\n[{stats_countries['processed']}/{len(countries)}] {country_code}: {country_name}")
                
                # Pobierz strefy czasowe dla kraju
                if CONFIG_VERBOSE:
                    print("  Pobieranie stref czasowych z Geonames...")
                
                timezone_iana_ids = get_country_timezones_from_geonames(geonames_provider, country_code)
                
                if not timezone_iana_ids:
                    stats_countries['skipped'] += 1
                    if CONFIG_VERBOSE:
                        print("  ⚠ Nie znaleziono stref czasowych")
                    continue
                
                if CONFIG_VERBOSE:
                    print(f"  ✓ Znaleziono {len(timezone_iana_ids)} stref: {', '.join(timezone_iana_ids)}")
                
                # Pobierz ID stref z bazy
                timezone_db_ids = []
                for tz_iana_id in timezone_iana_ids:
                    tz_db_id = get_timezone_id_from_db(conn, tz_iana_id)
                    if tz_db_id:
                        timezone_db_ids.append(tz_db_id)
                    else:
                        if CONFIG_VERBOSE:
                            print(f"    ⚠ Strefa {tz_iana_id} nie została znaleziona w bazie")
                
                if not timezone_db_ids:
                    stats_countries['skipped'] += 1
                    if CONFIG_VERBOSE:
                        print("  ⚠ Brak ID stref w bazie")
                    continue
                
                # Aktualizuj kraj
                success, message = update_country_timezones(conn, country_code, timezone_db_ids)
                
                if success:
                    stats_countries['updated'] += 1
                    if CONFIG_VERBOSE:
                        print(f"  ✓ {message}")
                else:
                    stats_countries['errors'] += 1
                    if CONFIG_VERBOSE:
                        print(f"  ✗ {message}")
            
            # Krótka przerwa między batchami
            if i + CONFIG_BATCH_SIZE < len(countries):
                import time
                time.sleep(2)
        
        # Podsumowanie
        print("\n" + "="*80)
        print("PODSUMOWANIE")
        print("="*80)
        print(f"Kraje przetworzone:  {stats_countries['processed']}")
        print(f"Kraje zaktualizowane: {stats_countries['updated']}")
        print(f"Kraje pominięte:     {stats_countries['skipped']}")
        print(f"Błędy:               {stats_countries['errors']}")
        print("="*80)
        
        # Sprawdź ile krajów ma przypisane strefy czasowe
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM countries 
                WHERE timezone_ids IS NOT NULL 
                AND array_length(timezone_ids, 1) > 0
                AND is_active = TRUE;
            """)
            countries_with_tz = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM countries WHERE is_active = TRUE;")
            total_countries = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM timezones;")
            total_timezones = cur.fetchone()[0]
            
            print(f"\nKraje z przypisanymi strefami czasowymi: {countries_with_tz}/{total_countries}")
            print(f"Łączna liczba stref czasowych w bazie: {total_timezones}")
        
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

