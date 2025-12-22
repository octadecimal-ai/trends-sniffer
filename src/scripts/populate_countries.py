#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do uzupełniania tabeli countries danymi z serwisów Geonames i World Bank.
Wykorzystuje klasy PyTrendsCountries i PyTrendsRegions do mapowania danych.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

# --- Parametry przetwarzania ---
CONFIG_COUNTRY_CODES = None                     # Lista kodów krajów do przetworzenia (None = wszystkie)
CONFIG_BATCH_SIZE = 5                           # Liczba krajów przetwarzanych na raz (mniejszy batch = mniej obciążenia API)
CONFIG_VERBOSE = True                           # Czy wyświetlać szczegółowe informacje
CONFIG_DRY_RUN = False                          # Tryb testowy (nie zapisuje do bazy)
CONFIG_SKIP_EXISTING = True                     # Czy pomijać kraje które już istnieją w bazie
CONFIG_UPDATE_EXISTING = True                   # Czy aktualizować istniejące kraje

# --- Parametry priorytetów ---
CONFIG_PRIORITY_TIER_1 = ['US', 'CN', 'JP', 'KR']  # Tier 1 - najwyższy priorytet
CONFIG_PRIORITY_TIER_2 = ['AR', 'NG', 'TR', 'KZ', 'DE', 'CA', 'AU', 'GB']  # Tier 2
CONFIG_PRIORITY_TIER_3 = ['PL', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO']  # Tier 3
CONFIG_PRIORITY_TIER_4 = []                     # Tier 4 - pozostałe (domyślnie)

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.models.countries import PyTrendsCountries
from src.models.regions import PyTrendsRegions
from src.providers.geonames_provider import GeonamesProvider
from src.services.world_bank_service import WorldBankService

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


def get_continent_id(conn, continent_code: str) -> Optional[int]:
    """
    Pobiera ID kontynentu na podstawie kodu.
    
    Args:
        conn: Połączenie z bazą danych
        continent_code: Kod kontynentu (AF, AS, EU, NA, SA, OC, AN)
    
    Returns:
        ID kontynentu lub None
    """
    if not continent_code:
        return None
    
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM continents WHERE code = %s;", (continent_code,))
        result = cur.fetchone()
        return result[0] if result else None


def get_region_id(conn, region_code: str) -> Optional[int]:
    """
    Pobiera ID regionu na podstawie kodu.
    
    Args:
        conn: Połączenie z bazą danych
        region_code: Kod regionu (north_america, europe, etc.)
    
    Returns:
        ID regionu lub None
    """
    if not region_code:
        return None
    
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM regions WHERE code = %s;", (region_code,))
        result = cur.fetchone()
        return result[0] if result else None


def get_income_level_id(conn, income_level_code: str) -> Optional[int]:
    """
    Pobiera ID poziomu dochodów na podstawie kodu.
    
    Args:
        conn: Połączenie z bazą danych
        income_level_code: Kod poziomu dochodów (HIC, UMC, LMC, LIC)
    
    Returns:
        ID poziomu dochodów lub None
    """
    if not income_level_code:
        return None
    
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM income_levels WHERE code = %s;", (income_level_code,))
        result = cur.fetchone()
        return result[0] if result else None


def map_continent_code(continent_name: str) -> Optional[str]:
    """
    Mapuje nazwę kontynentu na kod.
    
    Args:
        continent_name: Nazwa kontynentu
    
    Returns:
        Kod kontynentu lub None
    """
    mapping = {
        'Africa': 'AF',
        'Antarctica': 'AN',
        'Asia': 'AS',
        'Europe': 'EU',
        'North America': 'NA',
        'Oceania': 'OC',
        'South America': 'SA',
        'Afryka': 'AF',
        'Antarktyda': 'AN',
        'Azja': 'AS',
        'Europa': 'EU',
        'Ameryka Północna': 'NA',
        'Oceania': 'OC',
        'Ameryka Południowa': 'SA'
    }
    return mapping.get(continent_name)


def convert_iso2_to_iso3(iso2_code: str) -> Optional[str]:
    """
    Konwertuje kod ISO 2 na ISO 3.
    
    Args:
        iso2_code: Kod ISO 2
    
    Returns:
        Kod ISO 3 lub None
    """
    # Mapowanie kodów ISO 2 -> ISO 3 (najpopularniejsze + wszystkie z PyTrendsCountries)
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
        'WF': 'WLF', 'AD': 'AND', 'AE': 'ARE', 'AF': 'AFG', 'AG': 'ATG',
        'AI': 'AIA', 'AL': 'ALB', 'AM': 'ARM', 'AO': 'AGO', 'AQ': 'ATA',
        'AR': 'ARG', 'AS': 'ASM', 'AT': 'AUT', 'AU': 'AUS', 'AW': 'ABW',
        'AX': 'ALA', 'AZ': 'AZE', 'BA': 'BIH', 'BB': 'BRB', 'BD': 'BGD',
        'BE': 'BEL', 'BF': 'BFA', 'BG': 'BGR', 'BH': 'BHR', 'BI': 'BDI',
        'BJ': 'BEN', 'BL': 'BLM', 'BM': 'BMU', 'BN': 'BRN', 'BO': 'BOL',
        'BQ': 'BES', 'BR': 'BRA', 'BS': 'BHS', 'BT': 'BTN', 'BV': 'BVT',
        'BW': 'BWA', 'BY': 'BLR', 'BZ': 'BLZ', 'CA': 'CAN', 'CC': 'CCK',
        'CD': 'COD', 'CF': 'CAF', 'CG': 'COG', 'CH': 'CHE', 'CI': 'CIV',
        'CK': 'COK', 'CL': 'CHL', 'CM': 'CMR', 'CN': 'CHN', 'CO': 'COL',
        'CR': 'CRI', 'CU': 'CUB', 'CV': 'CPV', 'CW': 'CUW', 'CX': 'CXR',
        'CY': 'CYP', 'CZ': 'CZE', 'DE': 'DEU', 'DJ': 'DJI', 'DK': 'DNK',
        'DM': 'DMA', 'DO': 'DOM', 'DZ': 'DZA', 'EC': 'ECU', 'EE': 'EST',
        'EG': 'EGY', 'EH': 'ESH', 'ER': 'ERI', 'ES': 'ESP', 'ET': 'ETH',
        'FI': 'FIN', 'FJ': 'FJI', 'FK': 'FLK', 'FM': 'FSM', 'FO': 'FRO',
        'FR': 'FRA', 'GA': 'GAB', 'GB': 'GBR', 'GD': 'GRD', 'GE': 'GEO',
        'GF': 'GUF', 'GG': 'GGY', 'GH': 'GHA', 'GI': 'GIB', 'GL': 'GRL',
        'GM': 'GMB', 'GN': 'GIN', 'GP': 'GLP', 'GQ': 'GNQ', 'GR': 'GRC',
        'GS': 'SGS', 'GT': 'GTM', 'GU': 'GUM', 'GW': 'GNB', 'GY': 'GUY',
        'HK': 'HKG', 'HM': 'HMD', 'HN': 'HND', 'HR': 'HRV', 'HT': 'HTI',
        'HU': 'HUN', 'ID': 'IDN', 'IE': 'IRL', 'IL': 'ISR', 'IM': 'IMN',
        'IN': 'IND', 'IO': 'IOT', 'IQ': 'IRQ', 'IR': 'IRN', 'IS': 'ISL',
        'IT': 'ITA', 'JE': 'JEY', 'JM': 'JAM', 'JO': 'JOR', 'JP': 'JPN',
        'KE': 'KEN', 'KG': 'KGZ', 'KH': 'KHM', 'KI': 'KIR', 'KM': 'COM',
        'KN': 'KNA', 'KP': 'PRK', 'KR': 'KOR', 'KW': 'KWT', 'KY': 'CYM',
        'KZ': 'KAZ', 'LA': 'LAO', 'LB': 'LBN', 'LC': 'LCA', 'LI': 'LIE',
        'LK': 'LKA', 'LR': 'LBR', 'LS': 'LSO', 'LT': 'LTU', 'LU': 'LUX',
        'LV': 'LVA', 'LY': 'LBY', 'MA': 'MAR', 'MC': 'MCO', 'MD': 'MDA',
        'ME': 'MNE', 'MF': 'MAF', 'MG': 'MDG', 'MH': 'MHL', 'MK': 'MKD',
        'ML': 'MLI', 'MM': 'MMR', 'MN': 'MNG', 'MO': 'MAC', 'MP': 'MNP',
        'MQ': 'MTQ', 'MR': 'MRT', 'MS': 'MSR', 'MT': 'MLT', 'MU': 'MUS',
        'MV': 'MDV', 'MW': 'MWI', 'MX': 'MEX', 'MY': 'MYS', 'MZ': 'MOZ',
        'NA': 'NAM', 'NC': 'NCL', 'NE': 'NER', 'NF': 'NFK', 'NG': 'NGA',
        'NI': 'NIC', 'NL': 'NLD', 'NO': 'NOR', 'NP': 'NPL', 'NR': 'NRU',
        'NU': 'NIU', 'NZ': 'NZL', 'OM': 'OMN', 'PA': 'PAN', 'PE': 'PER',
        'PF': 'PYF', 'PG': 'PNG', 'PH': 'PHL', 'PK': 'PAK', 'PL': 'POL',
        'PM': 'SPM', 'PN': 'PCN', 'PR': 'PRI', 'PS': 'PSE', 'PT': 'PRT',
        'PW': 'PLW', 'PY': 'PRY', 'QA': 'QAT', 'RE': 'REU', 'RO': 'ROU',
        'RS': 'SRB', 'RU': 'RUS', 'RW': 'RWA', 'SA': 'SAU', 'SB': 'SLB',
        'SC': 'SYC', 'SD': 'SDN', 'SE': 'SWE', 'SG': 'SGP', 'SH': 'SHN',
        'SI': 'SVN', 'SJ': 'SJM', 'SK': 'SVK', 'SL': 'SLE', 'SM': 'SMR',
        'SN': 'SEN', 'SO': 'SOM', 'SR': 'SUR', 'SS': 'SSD', 'ST': 'STP',
        'SV': 'SLV', 'SX': 'SXM', 'SY': 'SYR', 'SZ': 'SWZ', 'TC': 'TCA',
        'TD': 'TCD', 'TF': 'ATF', 'TG': 'TGO', 'TH': 'THA', 'TJ': 'TJK',
        'TK': 'TKL', 'TL': 'TLS', 'TM': 'TKM', 'TN': 'TUN', 'TO': 'TON',
        'TR': 'TUR', 'TT': 'TTO', 'TV': 'TUV', 'TW': 'TWN', 'TZ': 'TZA',
        'UA': 'UKR', 'UG': 'UGA', 'UM': 'UMI', 'US': 'USA', 'UY': 'URY',
        'UZ': 'UZB', 'VA': 'VAT', 'VC': 'VCT', 'VE': 'VEN', 'VG': 'VGB',
        'VI': 'VIR', 'VN': 'VNM', 'VU': 'VUT', 'WF': 'WLF', 'WS': 'WSM',
        'XK': 'XKX', 'YE': 'YEM', 'YT': 'MYT', 'ZA': 'ZAF', 'ZM': 'ZMB',
        'ZW': 'ZWE'
    }
    return mapping.get(iso2_code.upper())


def get_priority_tier(country_code: str) -> int:
    """
    Określa priorytet monitoringu dla kraju.
    
    Args:
        country_code: Kod kraju ISO 2
    
    Returns:
        Priorytet (1-4)
    """
    if country_code in CONFIG_PRIORITY_TIER_1:
        return 1
    elif country_code in CONFIG_PRIORITY_TIER_2:
        return 2
    elif country_code in CONFIG_PRIORITY_TIER_3:
        return 3
    else:
        return 4


def get_region_code_for_country(country_code: str) -> Optional[str]:
    """
    Określa kod regionu dla kraju na podstawie PyTrendsRegions.
    
    Args:
        country_code: Kod kraju ISO 2
    
    Returns:
        Kod regionu lub None
    """
    regions = PyTrendsRegions.get_country_region(country_code)
    if regions:
        # Zwróć pierwszy region (kraj może być w wielu regionach)
        # Priorytetyzacja: north_america > asia_pacific > europe > china > middle_east > emerging_markets > offshore_hubs
        priority_order = [
            'north_america', 'asia_pacific', 'europe', 'china',
            'middle_east', 'high_adoption', 'offshore_hubs'
        ]
        
        for priority_region in priority_order:
            if priority_region in regions:
                return priority_region
        
        return regions[0]
    return None


def get_country_data_from_geonames(
    geonames_provider: GeonamesProvider,
    country_code: str,
    lang: str = 'pl'
) -> Optional[Dict]:
    """
    Pobiera dane o kraju z Geonames.
    
    Args:
        geonames_provider: Instancja GeonamesProvider
        country_code: Kod kraju ISO 2
        lang: Język odpowiedzi
    
    Returns:
        Słownik z danymi o kraju lub None
    """
    try:
        country_info = geonames_provider.get_country_info(country_code, lang=lang)
        if not country_info:
            return None
        
        # Pobierz strefę czasową jeśli mamy współrzędne
        timezone_info = None
        if country_info.get('lat') and country_info.get('lng'):
            try:
                lat = float(country_info.get('lat', 0))
                lng = float(country_info.get('lng', 0))
                if lat and lng:
                    timezone_info = geonames_provider.get_timezone(lat, lng)
            except:
                pass
        
        return {
            'geonames': country_info,
            'timezone': timezone_info
        }
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd Geonames dla {country_code}: {e}")
        return None


def get_country_data_from_worldbank(
    worldbank_service: WorldBankService,
    iso3_code: str
) -> Optional[Dict]:
    """
    Pobiera dane o kraju z World Bank.
    
    Args:
        worldbank_service: Instancja WorldBankService
        iso3_code: Kod kraju ISO 3
    
    Returns:
        Słownik z danymi o kraju lub None
    """
    try:
        country_info = worldbank_service.get_country_details(iso3_code)
        return country_info
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd World Bank dla {iso3_code}: {e}")
        return None


def prepare_country_data(
    country_code: str,
    geonames_data: Optional[Dict],
    worldbank_data: Optional[Dict],
    conn
) -> Optional[Dict]:
    """
    Przygotowuje dane kraju do wstawienia do bazy danych.
    
    Args:
        country_code: Kod kraju ISO 2
        geonames_data: Dane z Geonames
        worldbank_data: Dane z World Bank
        conn: Połączenie z bazą danych
    
    Returns:
        Słownik z danymi gotowymi do wstawienia
    """
    # Podstawowe dane z PyTrendsCountries
    country_info = PyTrendsCountries.COUNTRIES.get(country_code)
    if not country_info:
        return None
    
    # ISO 3
    iso3_code = convert_iso2_to_iso3(country_code)
    
    # Dane z Geonames
    geonames_info = geonames_data.get('geonames') if geonames_data else None
    timezone_info = geonames_data.get('timezone') if geonames_data else None
    
    # Dane z World Bank
    wb_country = worldbank_data
    
    # Kontynent
    continent_id = None
    if geonames_info:
        continent_name = geonames_info.get('continentName', '')
        continent_code = map_continent_code(continent_name)
        if continent_code:
            continent_id = get_continent_id(conn, continent_code)
    
    # Region
    region_code = get_region_code_for_country(country_code)
    region_id = get_region_id(conn, region_code) if region_code else None
    
    # Poziom dochodów
    income_level_id = None
    if wb_country:
        income_level = wb_country.get('incomeLevel', {})
        income_level_code = income_level.get('id') if isinstance(income_level, dict) else None
        if income_level_code:
            income_level_id = get_income_level_id(conn, income_level_code)
    
    # Priorytet
    monitoring_priority = get_priority_tier(country_code)
    
    # Przygotuj dane
    data = {
        'iso2_code': country_code,
        'iso3_code': iso3_code,
        'name_en': country_info.get('en', ''),
        'name_pl': country_info.get('pl', ''),
        'continent_id': continent_id,
        'region_id': region_id,
        'income_level_id': income_level_id,
        'monitoring_priority': monitoring_priority,
    }
    
    # Dane z Geonames
    if geonames_info:
        data['capital'] = geonames_info.get('capital', '')
        data['currency_code'] = geonames_info.get('currencyCode', '')
        data['languages'] = geonames_info.get('languages', '')
        
        # Populacja i powierzchnia
        try:
            population = geonames_info.get('population')
            if population:
                data['population'] = int(population)
        except:
            pass
        
        try:
            area = geonames_info.get('areaInSqKm')
            if area:
                data['area_km2'] = float(area)
        except:
            pass
        
        # Współrzędne
        try:
            lat = geonames_info.get('lat')
            lng = geonames_info.get('lng')
            if lat:
                data['latitude'] = float(lat)
            if lng:
                data['longitude'] = float(lng)
        except:
            pass
        
        # Bounding box
        try:
            if geonames_info.get('north'):
                data['bbox_north'] = float(geonames_info.get('north'))
            if geonames_info.get('south'):
                data['bbox_south'] = float(geonames_info.get('south'))
            if geonames_info.get('east'):
                data['bbox_east'] = float(geonames_info.get('east'))
            if geonames_info.get('west'):
                data['bbox_west'] = float(geonames_info.get('west'))
        except:
            pass
        
        # Geonames ID
        try:
            geoname_id = geonames_info.get('geonameId')
            if geoname_id:
                data['geonames_id'] = int(geoname_id)
        except:
            pass
    
    # Strefa czasowa
    if timezone_info:
        data['timezone'] = timezone_info.get('timezoneId', '')
        try:
            gmt_offset = timezone_info.get('gmtOffset')
            if gmt_offset is not None:
                data['utc_offset'] = int(gmt_offset) * 60  # Konwersja godzin na minuty
        except:
            pass
    
    # Waluta z World Bank
    if wb_country and not data.get('currency_code'):
        # World Bank może mieć informacje o walucie w innych polach
        pass
    
    return data


def insert_or_update_country(conn, country_data: Dict) -> Tuple[bool, str]:
    """
    Wstawia lub aktualizuje kraj w bazie danych.
    
    Args:
        conn: Połączenie z bazą danych
        country_data: Dane kraju
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if CONFIG_DRY_RUN:
        return True, "DRY RUN - nie zapisano"
    
    try:
        with conn.cursor() as cur:
            # Sprawdź czy kraj już istnieje
            cur.execute("SELECT id FROM countries WHERE iso2_code = %s;", (country_data['iso2_code'],))
            existing = cur.fetchone()
            
            if existing:
                if not CONFIG_UPDATE_EXISTING:
                    return True, "Pominięto (już istnieje)"
                
                # Aktualizuj
                country_id = existing[0]
                update_fields = []
                update_values = []
                
                for key, value in country_data.items():
                    if key != 'iso2_code' and value is not None:
                        update_fields.append(f"{key} = %s")
                        update_values.append(value)
                
                if update_fields:
                    update_values.append(country_data['iso2_code'])
                    query = f"""
                        UPDATE countries 
                        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE iso2_code = %s;
                    """
                    cur.execute(query, update_values)
                    return True, f"Aktualizowano (ID: {country_id})"
            else:
                # Wstaw nowy
                fields = list(country_data.keys())
                placeholders = ['%s'] * len(fields)
                values = [country_data[f] for f in fields]
                
                query = f"""
                    INSERT INTO countries ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING id;
                """
                cur.execute(query, values)
                country_id = cur.fetchone()[0]
                conn.commit()
                return True, f"Wstawiono (ID: {country_id})"
    
    except psycopg2.Error as e:
        conn.rollback()
        return False, f"Błąd SQL: {e}"


def check_country_exists(conn, country_code: str) -> bool:
    """
    Sprawdza czy kraj już istnieje w bazie.
    
    Args:
        conn: Połączenie z bazą danych
        country_code: Kod kraju ISO 2
    
    Returns:
        bool: True jeśli kraj istnieje
    """
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS(SELECT 1 FROM countries WHERE iso2_code = %s);", (country_code,))
        return cur.fetchone()[0]


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("UZUPEŁNIANIE TABELI COUNTRIES")
    print("="*80)
    
    if CONFIG_DRY_RUN:
        print("\n⚠ TRYB TESTOWY (DRY RUN) - dane nie będą zapisane do bazy")
    
    # Inicjalizacja providerów
    print("\nInicjalizacja providerów...")
    
    try:
        geonames_provider = GeonamesProvider()
        if CONFIG_VERBOSE:
            print("✓ GeonamesProvider zainicjalizowany")
    except Exception as e:
        print(f"✗ Błąd inicjalizacji GeonamesProvider: {e}")
        print("  Kontynuuję bez Geonames (będą tylko dane z World Bank)")
        geonames_provider = None
    
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
        # Pobierz listę krajów do przetworzenia
        if CONFIG_COUNTRY_CODES:
            country_codes = [code.upper() for code in CONFIG_COUNTRY_CODES]
        else:
            # Wszystkie kraje z PyTrendsCountries (pomijając pusty kod)
            country_codes = [code for code in PyTrendsCountries.COUNTRIES.keys() if code]
        
        print(f"\nLiczba krajów do przetworzenia: {len(country_codes)}")
        
        if CONFIG_SKIP_EXISTING:
            # Sprawdź które kraje już istnieją
            existing_count = 0
            for code in country_codes[:10]:  # Sprawdź pierwsze 10 jako próbkę
                if check_country_exists(conn, code):
                    existing_count += 1
            if existing_count > 0:
                print(f"  (Pomijanie istniejących krajów: {CONFIG_SKIP_EXISTING})")
        
        # Statystyki
        stats = {
            'processed': 0,
            'inserted': 0,
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
                
                # Sprawdź czy pomijać istniejące
                if CONFIG_SKIP_EXISTING and check_country_exists(conn, country_code):
                    if not CONFIG_UPDATE_EXISTING:
                        stats['skipped'] += 1
                        if CONFIG_VERBOSE:
                            print(f"\n[{stats['processed']}/{len(country_codes)}] {country_code}: Pominięto (już istnieje)")
                        continue
                
                if CONFIG_VERBOSE:
                    country_name = PyTrendsCountries.get_country_name(country_code, 'pl')
                    print(f"\n[{stats['processed']}/{len(country_codes)}] {country_code}: {country_name}")
                
                # Pobierz dane z Geonames
                geonames_data = None
                if geonames_provider:
                    if CONFIG_VERBOSE:
                        print("  Pobieranie danych z Geonames...")
                    geonames_data = get_country_data_from_geonames(geonames_provider, country_code)
                
                # Pobierz dane z World Bank
                worldbank_data = None
                if worldbank_service:
                    iso3_code = convert_iso2_to_iso3(country_code)
                    if iso3_code:
                        if CONFIG_VERBOSE:
                            print("  Pobieranie danych z World Bank...")
                        worldbank_data = get_country_data_from_worldbank(worldbank_service, iso3_code)
                
                # Przygotuj dane
                country_data = prepare_country_data(country_code, geonames_data, worldbank_data, conn)
                
                if not country_data:
                    stats['errors'] += 1
                    if CONFIG_VERBOSE:
                        print(f"  ✗ Nie udało się przygotować danych")
                    continue
                
                # Wstaw/aktualizuj w bazie
                success, message = insert_or_update_country(conn, country_data)
                
                if success:
                    if 'Wstawiono' in message:
                        stats['inserted'] += 1
                    elif 'Aktualizowano' in message:
                        stats['updated'] += 1
                    elif 'Pominięto' in message:
                        stats['skipped'] += 1
                    
                    if CONFIG_VERBOSE:
                        print(f"  ✓ {message}")
                else:
                    stats['errors'] += 1
                    if CONFIG_VERBOSE:
                        print(f"  ✗ {message}")
            
            # Krótka przerwa między batchami (aby nie przeciążać API)
            if i + CONFIG_BATCH_SIZE < len(country_codes):
                import time
                time.sleep(1)
        
        # Podsumowanie
        print("\n" + "="*80)
        print("PODSUMOWANIE")
        print("="*80)
        print(f"Przetworzono:     {stats['processed']} krajów")
        print(f"Wstawiono:        {stats['inserted']} krajów")
        print(f"Aktualizowano:    {stats['updated']} krajów")
        print(f"Pominięto:        {stats['skipped']} krajów")
        print(f"Błędy:            {stats['errors']} krajów")
        print("="*80)
        
        # Sprawdź ile krajów jest w bazie
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM countries;")
            total_in_db = cur.fetchone()[0]
            print(f"\nŁączna liczba krajów w bazie: {total_in_db}")
        
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

