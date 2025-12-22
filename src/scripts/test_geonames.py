#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy do testowania GeonamesProvider.
Wszystkie parametry konfiguracyjne znajdują się na górze pliku.
"""

# ============================================================================
# KONFIGURACJA - Ustaw tutaj wszystkie parametry
# ============================================================================

# --- Parametry inicjalizacji providera ---
CONFIG_USERNAME = None              # Username Geonames (None = pobiera z .env jako GEONAMES_LOGIN)

# --- Parametry wyszukiwania (search) ---
CONFIG_SEARCH_QUERY = "Warsaw"      # Ogólne zapytanie wyszukiwania
CONFIG_SEARCH_NAME = None           # Nazwa miejsca (None = nie używane)
CONFIG_SEARCH_NAME_EQUALS = None    # Dokładna nazwa miejsca (None = nie używane)
CONFIG_SEARCH_COUNTRY = "PL"        # Kod kraju (ISO 3166-1 alpha-2, None = wszystkie)
CONFIG_SEARCH_CONTINENT = None      # Kod kontynentu (AF, AS, EU, NA, OC, SA, AN, None = wszystkie)
CONFIG_SEARCH_FEATURE_CLASS = None  # Klasa obiektu (P=miasto, A=region, S=punkt, T=góra, U=podwodny, V=las, H=woda, L=ląd, None = wszystkie)
CONFIG_SEARCH_FEATURE_CODE = None   # Kod obiektu (np. PPLC=stolica, PPL=miasto, ADM1=województwo, None = wszystkie)
CONFIG_SEARCH_MAX_ROWS = 10         # Maksymalna liczba wyników (1-1000)
CONFIG_SEARCH_START_ROW = 0         # Numer pierwszego wyniku (dla paginacji)
CONFIG_SEARCH_LANG = "pl"           # Język odpowiedzi ('pl', 'en', 'de', itp.)

# --- Parametry informacji o kraju (get_country_info) ---
CONFIG_COUNTRY_CODE = "PL"          # Kod kraju (ISO 3166-1 alpha-2, None = wszystkie kraje)
CONFIG_COUNTRY_LANG = "pl"          # Język odpowiedzi

# --- Parametry dzieci miejsca (get_children) ---
CONFIG_CHILDREN_GEONAME_ID = None  # ID miejsca w Geonames (None = nie używane)
CONFIG_CHILDREN_LANG = "pl"         # Język odpowiedzi

# --- Parametry hierarchii (get_hierarchy) ---
CONFIG_HIERARCHY_GEONAME_ID = None # ID miejsca w Geonames (None = nie używane)
CONFIG_HIERARCHY_LANG = "pl"       # Język odpowiedzi

# --- Parametry miejsc w pobliżu (get_nearby_places) ---
CONFIG_NEARBY_LAT = 52.2297        # Szerokość geograficzna (Warszawa)
CONFIG_NEARBY_LNG = 21.0122        # Długość geograficzna (Warszawa)
CONFIG_NEARBY_FEATURE_CLASS = None # Klasa obiektu (None = wszystkie)
CONFIG_NEARBY_RADIUS_KM = 10.0     # Promień wyszukiwania w kilometrach
CONFIG_NEARBY_MAX_ROWS = 10        # Maksymalna liczba wyników
CONFIG_NEARBY_LANG = "pl"          # Język odpowiedzi

# --- Parametry strefy czasowej (get_timezone) ---
CONFIG_TIMEZONE_LAT = 52.2297      # Szerokość geograficzna
CONFIG_TIMEZONE_LNG = 21.0122      # Długość geograficzna

# --- Parametry kodu pocztowego (get_postal_code_info) ---
CONFIG_POSTAL_CODE = None          # Kod pocztowy (None = nie używane)
CONFIG_POSTAL_COUNTRY = "PL"       # Kod kraju (ISO 3166-1 alpha-2)
CONFIG_POSTAL_MAX_ROWS = 10        # Maksymalna liczba wyników

# --- Parametry wyszukiwania miast (search_cities) ---
CONFIG_CITY_NAME = "Warsaw"        # Nazwa miasta
CONFIG_CITY_COUNTRY = "PL"         # Kod kraju (None = wszystkie)
CONFIG_CITY_MAX_ROWS = 10          # Maksymalna liczba wyników
CONFIG_CITY_LANG = "pl"            # Język odpowiedzi

# --- Parametry regionów (get_regions) ---
CONFIG_REGIONS_COUNTRY = "PL"      # Kod kraju (ISO 3166-1 alpha-2)
CONFIG_REGIONS_FEATURE_CODE = "ADM1"  # Kod obiektu (ADM1=województwo/stan, ADM2=powiat, ADM3=gmina)
CONFIG_REGIONS_LANG = "pl"         # Język odpowiedzi

# --- Parametry stolicy (get_capital) ---
CONFIG_CAPITAL_COUNTRY = "PL"      # Kod kraju (ISO 3166-1 alpha-2)
CONFIG_CAPITAL_LANG = "pl"         # Język odpowiedzi

# --- Parametry bounding box (search_by_bounding_box) ---
CONFIG_BBOX_NORTH = 54.0           # Szerokość geograficzna północnej granicy (Polska)
CONFIG_BBOX_SOUTH = 49.0           # Szerokość geograficzna południowej granicy
CONFIG_BBOX_EAST = 24.0            # Długość geograficzna wschodniej granicy
CONFIG_BBOX_WEST = 14.0            # Długość geograficzna zachodniej granicy
CONFIG_BBOX_FEATURE_CLASS = None   # Klasa obiektu (None = wszystkie)
CONFIG_BBOX_FEATURE_CODE = None    # Kod obiektu (None = wszystkie)
CONFIG_BBOX_MAX_ROWS = 10          # Maksymalna liczba wyników
CONFIG_BBOX_LANG = "pl"            # Język odpowiedzi

# --- Parametry cities w bounding box (get_cities_in_bounding_box) ---
CONFIG_CITIES_BBOX_NORTH = 54.0    # Szerokość geograficzna północnej granicy
CONFIG_CITIES_BBOX_SOUTH = 49.0    # Szerokość geograficzna południowej granicy
CONFIG_CITIES_BBOX_EAST = 24.0     # Długość geograficzna wschodniej granicy
CONFIG_CITIES_BBOX_WEST = 14.0     # Długość geograficzna zachodniej granicy
CONFIG_CITIES_BBOX_MAX_ROWS = 10   # Maksymalna liczba wyników

# --- Parametry testowania ---
CONFIG_TEST_SEARCH = True          # Testować wyszukiwanie (search)
CONFIG_TEST_COUNTRY_INFO = True    # Testować informacje o kraju
CONFIG_TEST_CHILDREN = False       # Testować dzieci miejsca (wymaga CONFIG_CHILDREN_GEONAME_ID)
CONFIG_TEST_HIERARCHY = False     # Testować hierarchię (wymaga CONFIG_HIERARCHY_GEONAME_ID)
CONFIG_TEST_NEARBY = True          # Testować miejsca w pobliżu
CONFIG_TEST_TIMEZONE = True        # Testować strefę czasową
CONFIG_TEST_POSTAL_CODE = False    # Testować kod pocztowy (wymaga CONFIG_POSTAL_CODE)
CONFIG_TEST_CITIES = True          # Testować wyszukiwanie miast
CONFIG_TEST_REGIONS = True         # Testować regiony
CONFIG_TEST_CAPITAL = True         # Testować stolicę
CONFIG_TEST_BOUNDING_BOX = True    # Testować wyszukiwanie w bounding box
CONFIG_TEST_CITIES_BBOX = True     # Testować miasta w bounding box
CONFIG_VERBOSE = True              # Czy wyświetlać szczegółowe informacje

import sys
import os

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.providers.geonames_provider import GeonamesProvider


def print_section(title):
    """Wyświetla nagłówek sekcji."""
    if CONFIG_VERBOSE:
        print(f"\n{'='*70}")
        print(f"{title}")
        print(f"{'='*70}")


def test_search(provider):
    """Testuje wyszukiwanie miejsc."""
    if not CONFIG_TEST_SEARCH:
        return
    
    print_section("TEST: Wyszukiwanie miejsc (search)")
    
    try:
        params = {}
        if CONFIG_SEARCH_QUERY:
            params['q'] = CONFIG_SEARCH_QUERY
        if CONFIG_SEARCH_NAME:
            params['name'] = CONFIG_SEARCH_NAME
        if CONFIG_SEARCH_NAME_EQUALS:
            params['name_equals'] = CONFIG_SEARCH_NAME_EQUALS
        if CONFIG_SEARCH_COUNTRY:
            params['country'] = CONFIG_SEARCH_COUNTRY
        if CONFIG_SEARCH_CONTINENT:
            params['continent_code'] = CONFIG_SEARCH_CONTINENT
        if CONFIG_SEARCH_FEATURE_CLASS:
            params['feature_class'] = CONFIG_SEARCH_FEATURE_CLASS
        if CONFIG_SEARCH_FEATURE_CODE:
            params['feature_code'] = CONFIG_SEARCH_FEATURE_CODE
        
        results = provider.search(
            max_rows=CONFIG_SEARCH_MAX_ROWS,
            start_row=CONFIG_SEARCH_START_ROW,
            lang=CONFIG_SEARCH_LANG,
            **params
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} wyników:")
            for i, place in enumerate(results[:5], 1):
                print(f"{i}. {place.get('name', 'N/A')} ({place.get('countryName', 'N/A')})")
                print(f"   Typ: {place.get('fcodeName', 'N/A')}, ID: {place.get('geonameId', 'N/A')}")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_country_info(provider):
    """Testuje pobieranie informacji o kraju."""
    if not CONFIG_TEST_COUNTRY_INFO:
        return
    
    print_section(f"TEST: Informacje o kraju ({CONFIG_COUNTRY_CODE})")
    
    try:
        result = provider.get_country_info(CONFIG_COUNTRY_CODE, CONFIG_COUNTRY_LANG)
        
        if CONFIG_VERBOSE:
            if isinstance(result, list):
                print(f"Znaleziono {len(result)} krajów")
                for country in result[:3]:
                    print(f"- {country.get('countryName', 'N/A')} ({country.get('countryCode', 'N/A')})")
            else:
                print(f"Kraj: {result.get('countryName', 'N/A')}")
                print(f"Kod: {result.get('countryCode', 'N/A')}")
                print(f"Stolica: {result.get('capital', 'N/A')}")
                print(f"Populacja: {result.get('population', 'N/A')}")
                print(f"Powierzchnia: {result.get('areaInSqKm', 'N/A')} km²")
                print(f"Kontynent: {result.get('continentName', 'N/A')}")
        
        return result
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_children(provider):
    """Testuje pobieranie dzieci miejsca."""
    if not CONFIG_TEST_CHILDREN or not CONFIG_CHILDREN_GEONAME_ID:
        return
    
    print_section(f"TEST: Dzieci miejsca (ID: {CONFIG_CHILDREN_GEONAME_ID})")
    
    try:
        results = provider.get_children(CONFIG_CHILDREN_GEONAME_ID, CONFIG_CHILDREN_LANG)
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} miejsc podrzędnych:")
            for i, place in enumerate(results[:5], 1):
                print(f"{i}. {place.get('name', 'N/A')} - {place.get('fcodeName', 'N/A')}")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_hierarchy(provider):
    """Testuje pobieranie hierarchii miejsca."""
    if not CONFIG_TEST_HIERARCHY or not CONFIG_HIERARCHY_GEONAME_ID:
        return
    
    print_section(f"TEST: Hierarchia miejsca (ID: {CONFIG_HIERARCHY_GEONAME_ID})")
    
    try:
        results = provider.get_hierarchy(CONFIG_HIERARCHY_GEONAME_ID, CONFIG_HIERARCHY_LANG)
        
        if CONFIG_VERBOSE:
            print(f"Hierarchia ({len(results)} poziomów):")
            for i, place in enumerate(results, 1):
                print(f"{i}. {place.get('name', 'N/A')} ({place.get('fcodeName', 'N/A')})")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_nearby_places(provider):
    """Testuje pobieranie miejsc w pobliżu."""
    if not CONFIG_TEST_NEARBY:
        return
    
    print_section(f"TEST: Miejsca w pobliżu ({CONFIG_NEARBY_LAT}, {CONFIG_NEARBY_LNG})")
    
    try:
        results = provider.get_nearby_places(
            lat=CONFIG_NEARBY_LAT,
            lng=CONFIG_NEARBY_LNG,
            feature_class=CONFIG_NEARBY_FEATURE_CLASS,
            radius_km=CONFIG_NEARBY_RADIUS_KM,
            max_rows=CONFIG_NEARBY_MAX_ROWS,
            lang=CONFIG_NEARBY_LANG
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} miejsc w promieniu {CONFIG_NEARBY_RADIUS_KM} km:")
            for i, place in enumerate(results[:5], 1):
                print(f"{i}. {place.get('name', 'N/A')} - {place.get('fcodeName', 'N/A')}")
                print(f"   Odległość: {place.get('distance', 'N/A')} km")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_timezone(provider):
    """Testuje pobieranie strefy czasowej."""
    if not CONFIG_TEST_TIMEZONE:
        return
    
    print_section(f"TEST: Strefa czasowa ({CONFIG_TIMEZONE_LAT}, {CONFIG_TIMEZONE_LNG})")
    
    try:
        result = provider.get_timezone(CONFIG_TIMEZONE_LAT, CONFIG_TIMEZONE_LNG)
        
        if CONFIG_VERBOSE:
            print(f"Strefa czasowa: {result.get('timezoneId', 'N/A')}")
            print(f"Offset UTC: {result.get('rawOffset', 'N/A')} godzin")
            print(f"DST offset: {result.get('dstOffset', 'N/A')} godzin")
        
        return result
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_postal_code(provider):
    """Testuje pobieranie informacji o kodzie pocztowym."""
    if not CONFIG_TEST_POSTAL_CODE or not CONFIG_POSTAL_CODE:
        return
    
    print_section(f"TEST: Kod pocztowy ({CONFIG_POSTAL_CODE}, {CONFIG_POSTAL_COUNTRY})")
    
    try:
        results = provider.get_postal_code_info(
            CONFIG_POSTAL_CODE,
            CONFIG_POSTAL_COUNTRY,
            CONFIG_POSTAL_MAX_ROWS
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} miejsc:")
            for i, place in enumerate(results[:5], 1):
                print(f"{i}. {place.get('placeName', 'N/A')}, {place.get('adminName1', 'N/A')}")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_cities(provider):
    """Testuje wyszukiwanie miast."""
    if not CONFIG_TEST_CITIES:
        return
    
    print_section(f"TEST: Wyszukiwanie miast ({CONFIG_CITY_NAME})")
    
    try:
        results = provider.search_cities(
            CONFIG_CITY_NAME,
            country=CONFIG_CITY_COUNTRY,
            max_rows=CONFIG_CITY_MAX_ROWS,
            lang=CONFIG_CITY_LANG
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} miast:")
            for i, city in enumerate(results[:5], 1):
                print(f"{i}. {city.get('name', 'N/A')}, {city.get('adminName1', 'N/A')}, {city.get('countryName', 'N/A')}")
                print(f"   Populacja: {city.get('population', 'N/A')}, ID: {city.get('geonameId', 'N/A')}")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_regions(provider):
    """Testuje pobieranie regionów."""
    if not CONFIG_TEST_REGIONS:
        return
    
    print_section(f"TEST: Regiony ({CONFIG_REGIONS_COUNTRY}, {CONFIG_REGIONS_FEATURE_CODE})")
    
    try:
        results = provider.get_regions(
            CONFIG_REGIONS_COUNTRY,
            feature_code=CONFIG_REGIONS_FEATURE_CODE,
            lang=CONFIG_REGIONS_LANG
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} regionów:")
            for i, region in enumerate(results[:10], 1):
                print(f"{i}. {region.get('name', 'N/A')} (ID: {region.get('geonameId', 'N/A')})")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_capital(provider):
    """Testuje pobieranie stolicy."""
    if not CONFIG_TEST_CAPITAL:
        return
    
    print_section(f"TEST: Stolica kraju ({CONFIG_CAPITAL_COUNTRY})")
    
    try:
        result = provider.get_capital(CONFIG_CAPITAL_COUNTRY, CONFIG_CAPITAL_LANG)
        
        if CONFIG_VERBOSE:
            if result:
                print(f"Stolica: {result.get('name', 'N/A')}")
                print(f"Populacja: {result.get('population', 'N/A')}")
                print(f"ID: {result.get('geonameId', 'N/A')}")
                print(f"Współrzędne: {result.get('lat', 'N/A')}, {result.get('lng', 'N/A')}")
            else:
                print("Nie znaleziono stolicy")
        
        return result
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_bounding_box(provider):
    """Testuje wyszukiwanie w bounding box."""
    if not CONFIG_TEST_BOUNDING_BOX:
        return
    
    print_section(f"TEST: Wyszukiwanie w bounding box (N:{CONFIG_BBOX_NORTH}, S:{CONFIG_BBOX_SOUTH}, E:{CONFIG_BBOX_EAST}, W:{CONFIG_BBOX_WEST})")
    
    try:
        results = provider.search_by_bounding_box(
            north=CONFIG_BBOX_NORTH,
            south=CONFIG_BBOX_SOUTH,
            east=CONFIG_BBOX_EAST,
            west=CONFIG_BBOX_WEST,
            feature_class=CONFIG_BBOX_FEATURE_CLASS,
            feature_code=CONFIG_BBOX_FEATURE_CODE,
            max_rows=CONFIG_BBOX_MAX_ROWS,
            lang=CONFIG_BBOX_LANG
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} miejsc w bounding box:")
            for i, place in enumerate(results[:5], 1):
                print(f"{i}. {place.get('name', 'N/A')} ({place.get('countryName', 'N/A')})")
                print(f"   Typ: {place.get('fcodeName', 'N/A')}, Współrzędne: {place.get('lat', 'N/A')}, {place.get('lng', 'N/A')}")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def test_cities_bounding_box(provider):
    """Testuje pobieranie miast w bounding box."""
    if not CONFIG_TEST_CITIES_BBOX:
        return
    
    print_section(f"TEST: Miasta w bounding box (N:{CONFIG_CITIES_BBOX_NORTH}, S:{CONFIG_CITIES_BBOX_SOUTH}, E:{CONFIG_CITIES_BBOX_EAST}, W:{CONFIG_CITIES_BBOX_WEST})")
    
    try:
        results = provider.get_cities_in_bounding_box(
            north=CONFIG_CITIES_BBOX_NORTH,
            south=CONFIG_CITIES_BBOX_SOUTH,
            east=CONFIG_CITIES_BBOX_EAST,
            west=CONFIG_CITIES_BBOX_WEST,
            max_rows=CONFIG_CITIES_BBOX_MAX_ROWS
        )
        
        if CONFIG_VERBOSE:
            print(f"Znaleziono {len(results)} miast w bounding box:")
            for i, city in enumerate(results[:5], 1):
                print(f"{i}. {city.get('name', 'N/A')}, {city.get('countrycode', 'N/A')}")
                print(f"   Populacja: {city.get('population', 'N/A')}, Współrzędne: {city.get('lat', 'N/A')}, {city.get('lng', 'N/A')}")
        
        return results
    
    except Exception as e:
        print(f"Błąd: {e}")
        return None


def main():
    """Główna funkcja programu."""
    if CONFIG_VERBOSE:
        print("="*70)
        print("SKRYPT TESTOWY GEONAMES PROVIDER")
        print("="*70)
        print(f"Username: {CONFIG_USERNAME if CONFIG_USERNAME else 'z .env (GEONAMES_LOGIN)'}")
        print("="*70)
    
    # Inicjalizacja providera
    try:
        if CONFIG_USERNAME:
            provider = GeonamesProvider(username=CONFIG_USERNAME)
        else:
            provider = GeonamesProvider()
        
        if CONFIG_VERBOSE:
            print(f"✓ Provider zainicjalizowany (username: {provider.username})")
    
    except Exception as e:
        print(f"Błąd inicjalizacji providera: {e}")
        return 1
    
    # Wykonanie testów
    results = {}
    
    results['search'] = test_search(provider)
    results['country_info'] = test_country_info(provider)
    results['children'] = test_children(provider)
    results['hierarchy'] = test_hierarchy(provider)
    results['nearby'] = test_nearby_places(provider)
    results['timezone'] = test_timezone(provider)
    results['postal_code'] = test_postal_code(provider)
    results['cities'] = test_cities(provider)
    results['regions'] = test_regions(provider)
    results['capital'] = test_capital(provider)
    results['bounding_box'] = test_bounding_box(provider)
    results['cities_bbox'] = test_cities_bounding_box(provider)
    
    # Podsumowanie
    if CONFIG_VERBOSE:
        print_section("PODSUMOWANIE")
        successful = sum(1 for r in results.values() if r is not None)
        total = sum(1 for r in results.values() if r is not False)
        print(f"Wykonano testów: {total}")
        print(f"Udanych: {successful}")
        print(f"Nieudanych: {total - successful}")
        print("="*70)
        print("Zakończono pomyślnie!")
        print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

