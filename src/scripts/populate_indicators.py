#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do uzupełniania wskaźników ekonomicznych, krypto i hashrate w bazie danych.
Pobiera dane z:
- World Bank API (wskaźniki ekonomiczne)
- IMF SDMX API (premia BTC)
- CSV files (hashrate)
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

# --- Parametry przetwarzania ---
CONFIG_COUNTRY_CODES = None                     # Lista kodów krajów do przetworzenia (None = wszystkie)
CONFIG_VERBOSE = True                           # Czy wyświetlać szczegółowe informacje
CONFIG_DRY_RUN = False                          # Tryb testowy (nie zapisuje do bazy)
CONFIG_UPDATE_EXISTING = True                   # Czy aktualizować istniejące dane

# --- Parametry World Bank ---
CONFIG_WB_START_YEAR = 2020                     # Rok początkowy dla danych World Bank
CONFIG_WB_END_YEAR = 2024                       # Rok końcowy dla danych World Bank
CONFIG_WB_INDICATORS = {
    'NY.GDP.PCAP.CD': 'gdp_per_capita',         # GDP per capita (current USD)
    'FP.CPI.TOTL.ZG': 'inflation_rate',         # Inflation (CPI %)
    'IT.NET.USER.ZS': 'internet_users_percent', # Internet Users (% of population)
    'SL.UEM.TOTL.ZS': 'unemployment_rate'       # Unemployment Rate (%)
}

# --- Ścieżki do plików CSV ---
CONFIG_HASHRATE_CSV = 'data/hashrate-by-country.csv'
CONFIG_IMF_CSV = 'data/dataset_2025-12-22T12_40_16.754606401Z_DEFAULT_INTEGRATION_IMF.STA_WPCPER_6.0.0.csv'

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import csv
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.services.world_bank_service import WorldBankService
from src.models.countries import PyTrendsCountries

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


def get_country_id(conn, iso2_code: str) -> Optional[int]:
    """Pobiera ID kraju z bazy na podstawie kodu ISO 2."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM countries WHERE iso2_code = %s;", (iso2_code,))
        result = cur.fetchone()
        return result[0] if result else None


def get_indicator_id(conn, indicator_code: str) -> Optional[int]:
    """Pobiera ID wskaźnika z bazy na podstawie kodu."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM indicators WHERE code = %s;", (indicator_code,))
        result = cur.fetchone()
        return result[0] if result else None


def convert_iso2_to_iso3(iso2_code: str) -> Optional[str]:
    """Konwertuje kod ISO 2 na ISO 3."""
    mapping = {
        'PL': 'POL', 'US': 'USA', 'GB': 'GBR', 'DE': 'DEU', 'FR': 'FRA',
        'IT': 'ITA', 'ES': 'ESP', 'NL': 'NLD', 'BE': 'BEL', 'CH': 'CHE',
        'AT': 'AUT', 'SE': 'SWE', 'NO': 'NOR', 'DK': 'DNK', 'FI': 'FIN',
        'CZ': 'CZE', 'SK': 'SVK', 'HU': 'HUN', 'RO': 'ROU', 'BG': 'BGR',
        'GR': 'GRC', 'PT': 'PRT', 'IE': 'IRL', 'LU': 'LUX', 'EE': 'EST',
        'LV': 'LVA', 'LT': 'LTU', 'SI': 'SVN', 'HR': 'HRV', 'MT': 'MLT',
        'CY': 'CYP', 'JP': 'JPN', 'CN': 'CHN', 'IN': 'IND', 'BR': 'BRA',
        'RU': 'RUS', 'CA': 'CAN', 'AU': 'AUS', 'KR': 'KOR', 'MX': 'MEX',
        'AR': 'ARG', 'ZA': 'ZAF', 'TR': 'TUR', 'ID': 'IDN', 'TH': 'THA',
        'VN': 'VNM', 'PH': 'PHL', 'MY': 'MYS', 'SG': 'SGP', 'NZ': 'NZL',
        'NG': 'NGA', 'PK': 'PAK', 'BD': 'BGD', 'EG': 'EGY', 'SA': 'SAU',
        'AE': 'ARE', 'IL': 'ISR', 'HK': 'HKG', 'TW': 'TWN', 'KZ': 'KAZ',
        'UA': 'UKR', 'CL': 'CHL', 'CO': 'COL', 'PE': 'PER', 'VE': 'VEN',
        'UY': 'URY', 'PY': 'PRY', 'BO': 'BOL', 'EC': 'ECU', 'CR': 'CRI',
        'PA': 'PAN', 'GT': 'GTM', 'HN': 'HND', 'NI': 'NIC', 'SV': 'SLV',
        'DO': 'DOM', 'CU': 'CUB', 'JM': 'JAM', 'HT': 'HTI', 'TT': 'TTO',
        'BS': 'BHS', 'BB': 'BRB', 'GD': 'GRD', 'LC': 'LCA', 'VC': 'VCT',
        'AG': 'ATG', 'KN': 'KNA', 'DM': 'DMA', 'SR': 'SUR', 'GY': 'GUY',
        'GF': 'GUF', 'FK': 'FLK', 'GS': 'SGS', 'BV': 'BVT', 'AQ': 'ATA',
        'TF': 'ATF', 'HM': 'HMD', 'CC': 'CCK', 'CX': 'CXR', 'NF': 'NFK',
        'NC': 'NCL', 'PF': 'PYF', 'WS': 'WSM', 'TO': 'TON', 'FJ': 'FJI',
        'VU': 'VUT', 'SB': 'SLB', 'PG': 'PNG', 'FM': 'FSM', 'MH': 'MHL',
        'PW': 'PLW', 'KI': 'KIR', 'TV': 'TUV', 'NR': 'NRU', 'NU': 'NIU',
        'CK': 'COK', 'PN': 'PCN', 'TK': 'TKL', 'AS': 'ASM', 'GU': 'GUM',
        'MP': 'MNP', 'VI': 'VIR', 'PR': 'PRI', 'VG': 'VGB', 'AI': 'AIA',
        'MS': 'MSR', 'TC': 'TCA', 'KY': 'CYM', 'BM': 'BMU', 'AW': 'ABW',
        'CW': 'CUW', 'SX': 'SXM', 'BQ': 'BES', 'BL': 'BLM', 'MF': 'MAF',
        'GP': 'GLP', 'MQ': 'MTQ', 'RE': 'REU', 'YT': 'MYT', 'PM': 'SPM',
        'WF': 'WLF'
    }
    return mapping.get(iso2_code.upper())


def map_country_name_to_iso2(country_name: str) -> Optional[str]:
    """Mapuje nazwę kraju na kod ISO 2."""
    # Mapowanie najpopularniejszych nazw
    mapping = {
        'United States': 'US', 'USA': 'US',
        'China': 'CN', 'People\'s Republic of China': 'CN',
        'Kazakhstan': 'KZ',
        'Canada': 'CA',
        'Russia': 'RU', 'Russian Federation': 'RU',
        'Germany': 'DE',
        'Malaysia': 'MY',
        'Ireland': 'IE',
        'Thailand': 'TH',
        'Sweden': 'SE',
        'Norway': 'NO',
        'Australia': 'AU',
        'Indonesia': 'ID',
        'Brazil': 'BR',
        'Japan': 'JP',
        'United Kingdom': 'GB', 'UK': 'GB',
        'Georgia': 'GE',
        'France': 'FR',
        'Netherlands': 'NL',
        'Ukraine': 'UA',
        'Paraguay': 'PY',
        'Libya': 'LY',
        'Iran': 'IR',
        'Mexico': 'MX',
        'Italy': 'IT',
        'Romania': 'RO',
        'South Korea': 'KR', 'Korea, Rep.': 'KR',
        'Argentina': 'AR',
        'Uzbekistan': 'UZ',
        'Greece': 'GR',
        'Vietnam': 'VN',
        'Turkey': 'TR', 'Turkiye': 'TR',
        'Mongolia': 'MN',
        'India': 'IN',
        'Hungary': 'HU',
        'Switzerland': 'CH',
        'Poland': 'PL',
        'Finland': 'FI',
        'South Africa': 'ZA',
        'Colombia': 'CO',
        'Saudi Arabia': 'SA',
        'Portugal': 'PT',
        'Belgium': 'BE',
        'United Arab Emirates': 'AE',
        'Austria': 'AT',
        'Bulgaria': 'BG',
        'Oman': 'OM',
        'Croatia': 'HR',
        'Uruguay': 'UY',
        'Armenia': 'AM'
    }
    
    # Najpierw sprawdź dokładne dopasowanie
    if country_name in mapping:
        return mapping[country_name]
    
    # Spróbuj znaleźć w PyTrendsCountries
    for code, info in PyTrendsCountries.COUNTRIES.items():
        if code and (info.get('en', '').lower() == country_name.lower() or 
                     info.get('pl', '').lower() == country_name.lower()):
            return code
    
    return None


def load_world_bank_indicators(conn, worldbank_service: WorldBankService) -> Dict[str, int]:
    """Ładuje wskaźniki World Bank do bazy i zwraca mapowanie kod->id."""
    indicator_ids = {}
    
    for wb_code, _ in CONFIG_WB_INDICATORS.items():
        indicator_id = get_indicator_id(conn, wb_code)
        if not indicator_id:
            if CONFIG_VERBOSE:
                print(f"  ⚠ Wskaźnik {wb_code} nie istnieje w bazie - pomijam")
            continue
        indicator_ids[wb_code] = indicator_id
    
    return indicator_ids


def insert_country_indicator(
    conn,
    country_id: int,
    indicator_id: int,
    period_date: date,
    value: float,
    period_type: str = 'yearly'
) -> Tuple[bool, str]:
    """Wstawia lub aktualizuje wskaźnik kraju."""
    if CONFIG_DRY_RUN:
        return True, "DRY RUN - nie zapisano"
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO country_indicators 
                (country_id, indicator_id, period_date, period_type, value, source)
                VALUES (%s, %s, %s, %s, %s, 'world_bank')
                ON CONFLICT (country_id, indicator_id, period_date, period_type)
                DO UPDATE SET value = EXCLUDED.value, source = EXCLUDED.source
                RETURNING id;
            """, (country_id, indicator_id, period_date, period_type, value))
            
            result = cur.fetchone()
            if result:
                conn.commit()
                return True, f"Zapisano (ID: {result[0]})"
            return False, "Błąd zapisu"
    
    except psycopg2.Error as e:
        conn.rollback()
        return False, f"Błąd SQL: {e}"


def load_world_bank_data(conn, worldbank_service: WorldBankService):
    """Ładuje dane World Bank do bazy."""
    print("\n" + "="*80)
    print("ŁADOWANIE DANYCH WORLD BANK")
    print("="*80)
    
    indicator_ids = load_world_bank_indicators(conn, worldbank_service)
    
    if not indicator_ids:
        print("  ⚠ Brak wskaźników do załadowania")
        return
    
    # Pobierz listę krajów
    if CONFIG_COUNTRY_CODES:
        country_codes = [code.upper() for code in CONFIG_COUNTRY_CODES]
    else:
        with conn.cursor() as cur:
            cur.execute("SELECT iso2_code FROM countries WHERE is_active = TRUE ORDER BY iso2_code;")
            country_codes = [row[0] for row in cur.fetchall()]
    
    print(f"Przetwarzanie {len(country_codes)} krajów dla {len(indicator_ids)} wskaźników")
    
    stats = {'processed': 0, 'inserted': 0, 'errors': 0}
    
    for country_code in country_codes:
        stats['processed'] += 1
        country_id = get_country_id(conn, country_code)
        
        if not country_id:
            if CONFIG_VERBOSE:
                print(f"[{stats['processed']}/{len(country_codes)}] {country_code}: Kraj nie znaleziony w bazie")
            continue
        
        iso3_code = convert_iso2_to_iso3(country_code)
        if not iso3_code:
            if CONFIG_VERBOSE:
                print(f"[{stats['processed']}/{len(country_codes)}] {country_code}: Brak kodu ISO 3")
            continue
        
        if CONFIG_VERBOSE:
            country_name = PyTrendsCountries.get_country_name(country_code, 'pl')
            print(f"\n[{stats['processed']}/{len(country_codes)}] {country_code}: {country_name}")
        
        for wb_code, indicator_id in indicator_ids.items():
            try:
                # Pobierz dane z World Bank
                try:
                    data = worldbank_service.get_data_for_indicator(
                        wb_code,
                        country_codes=iso3_code,
                        start_year=CONFIG_WB_START_YEAR,
                        end_year=CONFIG_WB_END_YEAR
                    )
                    
                    if not data or not isinstance(data, list):
                        continue
                except Exception as e:
                    if CONFIG_VERBOSE:
                        print(f"    ⚠ Błąd pobierania {wb_code}: {e}")
                    continue
                
                # Zapisz najnowsze dane
                for record in data:
                    year = record.get('date')
                    value = record.get('value')
                    
                    if year and value is not None:
                        try:
                            period_date = date(int(year), 12, 31)  # Koniec roku
                            success, message = insert_country_indicator(
                                conn, country_id, indicator_id, period_date, float(value)
                            )
                            if success:
                                stats['inserted'] += 1
                        except Exception as e:
                            if CONFIG_VERBOSE:
                                print(f"    ⚠ Błąd dla {wb_code} {year}: {e}")
                            stats['errors'] += 1
                
            except Exception as e:
                if CONFIG_VERBOSE:
                    print(f"    ⚠ Błąd pobierania {wb_code}: {e}")
                stats['errors'] += 1
        
        # Przerwa między krajami
        import time
        time.sleep(0.5)
    
    print(f"\n✓ Zakończono: przetworzono {stats['processed']}, wstawiono {stats['inserted']}, błędy {stats['errors']}")


def load_hashrate_data(conn):
    """Ładuje dane hashrate z CSV do bazy."""
    print("\n" + "="*80)
    print("ŁADOWANIE DANYCH HASHRATE Z CSV")
    print("="*80)
    
    if not os.path.exists(CONFIG_HASHRATE_CSV):
        print(f"  ⚠ Plik {CONFIG_HASHRATE_CSV} nie istnieje")
        return
    
    # Pobierz ID wskaźnika hashrate
    hashrate_indicator_id = get_indicator_id(conn, 'HASHRATE_SHARE')
    if not hashrate_indicator_id:
        print("  ⚠ Wskaźnik HASHRATE_SHARE nie istnieje w bazie")
        return
    
    stats = {'processed': 0, 'inserted': 0, 'errors': 0}
    recorded_at = datetime.now()
    
    with open(CONFIG_HASHRATE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            stats['processed'] += 1
            country_name = row.get('Country', '').strip()
            hashrate_share = row.get('Hashrate_Share_Percent', '').strip()
            
            if not country_name or not hashrate_share:
                continue
            
            # Mapuj nazwę kraju na kod ISO 2
            iso2_code = map_country_name_to_iso2(country_name)
            if not iso2_code:
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Nie znaleziono kodu dla: {country_name}")
                stats['errors'] += 1
                continue
            
            country_id = get_country_id(conn, iso2_code)
            if not country_id:
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Kraj {iso2_code} nie znaleziony w bazie")
                stats['errors'] += 1
                continue
            
            try:
                hashrate_value = float(hashrate_share)
                
                # Zapisz do hashrate_data
                if not CONFIG_DRY_RUN:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO hashrate_data 
                            (country_id, recorded_at, hashrate_share_percent, source)
                            VALUES (%s, %s, %s, 'cbeci')
                            ON CONFLICT (country_id, recorded_at, source)
                            DO UPDATE SET hashrate_share_percent = EXCLUDED.hashrate_share_percent
                            RETURNING id;
                        """, (country_id, recorded_at, hashrate_value))
                        
                        result = cur.fetchone()
                        if result:
                            conn.commit()
                            stats['inserted'] += 1
                            if CONFIG_VERBOSE:
                                print(f"  ✓ {country_name} ({iso2_code}): {hashrate_value}%")
                
            except ValueError:
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Nieprawidłowa wartość hashrate dla {country_name}: {hashrate_share}")
                stats['errors'] += 1
    
    print(f"\n✓ Zakończono: przetworzono {stats['processed']}, wstawiono {stats['inserted']}, błędy {stats['errors']}")


def parse_imf_date(date_str: str) -> Optional[date]:
    """Parsuje datę z formatu IMF (YYYY-M##)."""
    try:
        match = re.match(r'(\d{4})-M(\d{2})', date_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            # Ostatni dzień miesiąca
            if month == 12:
                return date(year, 12, 31)
            else:
                next_month = date(year, month + 1, 1)
                from datetime import timedelta
                return next_month - timedelta(days=1)
    except:
        pass
    return None


def load_imf_btc_data(conn):
    """Ładuje dane BTC premium z CSV IMF do bazy."""
    print("\n" + "="*80)
    print("ŁADOWANIE DANYCH BTC PREMIUM Z CSV IMF")
    print("="*80)
    
    if not os.path.exists(CONFIG_IMF_CSV):
        print(f"  ⚠ Plik {CONFIG_IMF_CSV} nie istnieje")
        return
    
    stats = {'processed': 0, 'inserted': 0, 'errors': 0}
    
    with open(CONFIG_IMF_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            stats['processed'] += 1
            
            country_name = row.get('COUNTRY', '').strip()
            series_code = row.get('SERIES_CODE', '').strip()
            currency = row.get('CURRENCY', '').strip()
            
            if not country_name:
                continue
            
            # Mapuj nazwę kraju na kod ISO 2
            iso2_code = map_country_name_to_iso2(country_name)
            if not iso2_code:
                if CONFIG_VERBOSE and stats['processed'] <= 10:
                    print(f"  ⚠ Nie znaleziono kodu dla: {country_name}")
                continue
            
            country_id = get_country_id(conn, iso2_code)
            if not country_id:
                continue
            
            # Sprawdź typ wskaźnika (premium czy rate)
            is_premium = 'BIT_SHD_PT' in series_code or 'Premium' in row.get('INDICATOR', '')
            is_rate = 'BIT_SHD_RT' in series_code or 'Rate' in row.get('INDICATOR', '')
            
            # Przetwórz wszystkie kolumny z datami
            for key, value in row.items():
                if re.match(r'\d{4}-M\d{2}', key) and value and value.strip():
                    try:
                        period_date = parse_imf_date(key)
                        if not period_date:
                            continue
                        
                        num_value = float(value.strip())
                        
                        if is_premium:
                            # Zapisz do btc_premium_data jako premium_percent
                            if not CONFIG_DRY_RUN:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        INSERT INTO btc_premium_data 
                                        (country_id, period_date, premium_percent, source)
                                        VALUES (%s, %s, %s, 'imf')
                                        ON CONFLICT (country_id, period_date, source)
                                        DO UPDATE SET premium_percent = EXCLUDED.premium_percent
                                        RETURNING id;
                                    """, (country_id, period_date, num_value))
                                    
                                    if cur.fetchone():
                                        conn.commit()
                                        stats['inserted'] += 1
                        
                        elif is_rate:
                            # Zapisz do btc_premium_data jako parallel_rate
                            if not CONFIG_DRY_RUN:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        INSERT INTO btc_premium_data 
                                        (country_id, period_date, parallel_rate, source)
                                        VALUES (%s, %s, %s, 'imf')
                                        ON CONFLICT (country_id, period_date, source)
                                        DO UPDATE SET parallel_rate = EXCLUDED.parallel_rate
                                        RETURNING id;
                                    """, (country_id, period_date, num_value))
                                    
                                    if cur.fetchone():
                                        conn.commit()
                                        stats['inserted'] += 1
                    
                    except (ValueError, TypeError):
                        continue
            
            if CONFIG_VERBOSE and stats['processed'] % 100 == 0:
                print(f"  Przetworzono {stats['processed']} rekordów...")
    
    print(f"\n✓ Zakończono: przetworzono {stats['processed']}, wstawiono {stats['inserted']}, błędy {stats['errors']}")


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("UZUPEŁNIANIE WSKAŹNIKÓW W BAZIE DANYCH")
    print("="*80)
    
    if CONFIG_DRY_RUN:
        print("\n⚠ TRYB TESTOWY (DRY RUN) - dane nie będą zapisane do bazy")
    
    # Inicjalizacja serwisów
    print("\nInicjalizacja serwisów...")
    
    try:
        worldbank_service = WorldBankService(verbose=False)
        if CONFIG_VERBOSE:
            print("✓ WorldBankService zainicjalizowany")
    except Exception as e:
        print(f"✗ Błąd inicjalizacji WorldBankService: {e}")
        worldbank_service = None
    
    # Połącz z bazą danych
    try:
        print("\nŁączenie z bazą danych...")
        conn = get_database_connection()
        print("✓ Połączono z bazą danych")
    except Exception as e:
        print(f"\n✗ Błąd połączenia: {e}")
        return 1
    
    try:
        # 1. Ładuj dane World Bank
        if worldbank_service:
            load_world_bank_data(conn, worldbank_service)
        
        # 2. Ładuj dane hashrate z CSV
        load_hashrate_data(conn)
        
        # 3. Ładuj dane BTC premium z CSV IMF
        load_imf_btc_data(conn)
        
        # Podsumowanie
        print("\n" + "="*80)
        print("PODSUMOWANIE")
        print("="*80)
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM country_indicators;")
            indicators_count = cur.fetchone()[0]
            print(f"Łączna liczba rekordów w country_indicators: {indicators_count}")
            
            cur.execute("SELECT COUNT(*) FROM hashrate_data;")
            hashrate_count = cur.fetchone()[0]
            print(f"Łączna liczba rekordów w hashrate_data: {hashrate_count}")
            
            cur.execute("SELECT COUNT(*) FROM btc_premium_data;")
            btc_premium_count = cur.fetchone()[0]
            print(f"Łączna liczba rekordów w btc_premium_data: {btc_premium_count}")
        
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

