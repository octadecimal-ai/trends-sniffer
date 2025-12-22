#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania szczegółowych informacji o kraju na podstawie kodu kraju.
Używa GeonamesProvider do pobierania danych.
"""

# ============================================================================
# KONFIGURACJA - Ustaw tutaj wszystkie parametry
# ============================================================================

# --- Parametry kraju ---
CONFIG_COUNTRY_CODE = "PL"          # Kod kraju (ISO 3166-1 alpha-2)
CONFIG_LANGUAGE = "pl"              # Język odpowiedzi ('pl', 'en', 'de', itp.)

# --- Parametry wyświetlania ---
CONFIG_VERBOSE = True               # Czy wyświetlać szczegółowe informacje
CONFIG_EXPORT_JSON = False          # Czy eksportować do JSON
CONFIG_EXPORT_CSV = False           # Czy eksportować do CSV
CONFIG_OUTPUT_DIR = "output"       # Katalog wyjściowy

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import json
from typing import Dict, List, Optional

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.providers.geonames_provider import GeonamesProvider


def get_country_bounding_box(provider: GeonamesProvider, country_code: str) -> Optional[Dict]:
    """
    Pobiera rozpiętość geograficzną kraju (bounding box).
    
    Args:
        provider: Instancja GeonamesProvider
        country_code: Kod kraju (ISO 3166-1 alpha-2)
    
    Returns:
        Słownik z współrzędnymi bounding box lub None
    """
    try:
        # Pobierz wszystkie miejsca w kraju (używając dużego bounding box)
        # Najpierw pobierz informacje o kraju, aby uzyskać przybliżone współrzędne
        country_info = provider.get_country_info(country_code)
        
        if not country_info or isinstance(country_info, list):
            return None
        
        # Pobierz stolicę, aby uzyskać przybliżone współrzędne
        capital = provider.get_capital(country_code)
        if not capital:
            return None
        
        lat = float(capital.get('lat', 0))
        lng = float(capital.get('lng', 0))
        
        # Pobierz miejsca w szerokim promieniu wokół stolicy
        # Użyjemy search z country code, aby znaleźć skrajne punkty
        places = provider.search(
            country=country_code,
            max_rows=1000,
            lang=CONFIG_LANGUAGE
        )
        
        if not places:
            return None
        
        # Znajdź skrajne współrzędne
        lats = [float(p.get('lat', 0)) for p in places if p.get('lat')]
        lngs = [float(p.get('lng', 0)) for p in places if p.get('lng')]
        
        if not lats or not lngs:
            return None
        
        return {
            'north': max(lats),
            'south': min(lats),
            'east': max(lngs),
            'west': min(lngs),
            'center_lat': lat,
            'center_lng': lng
        }
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"Błąd podczas pobierania bounding box: {e}")
        return None


def get_timezones_for_country(provider: GeonamesProvider, country_code: str) -> List[str]:
    """
    Pobiera wszystkie strefy czasowe dla kraju.
    
    Args:
        provider: Instancja GeonamesProvider
        country_code: Kod kraju (ISO 3166-1 alpha-2)
    
    Returns:
        Lista stref czasowych
    """
    timezones = set()
    
    try:
        # Pobierz stolicę i jej strefę czasową
        capital = provider.get_capital(country_code)
        if capital:
            lat = float(capital.get('lat', 0))
            lng = float(capital.get('lng', 0))
            if lat and lng:
                tz_info = provider.get_timezone(lat, lng)
                if tz_info and 'timezoneId' in tz_info:
                    timezones.add(tz_info['timezoneId'])
        
        # Pobierz kilka dużych miast i ich strefy czasowe
        cities = provider.search_cities('', country=country_code, max_rows=20)
        for city in cities[:10]:  # Sprawdź pierwsze 10 miast
            try:
                lat = float(city.get('lat', 0))
                lng = float(city.get('lng', 0))
                if lat and lng:
                    tz_info = provider.get_timezone(lat, lng)
                    if tz_info and 'timezoneId' in tz_info:
                        timezones.add(tz_info['timezoneId'])
            except:
                continue
        
        return sorted(list(timezones))
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"Błąd podczas pobierania stref czasowych: {e}")
        return []


def get_country_data(provider: GeonamesProvider, country_code: str) -> Dict:
    """
    Pobiera wszystkie dane o kraju.
    
    Args:
        provider: Instancja GeonamesProvider
        country_code: Kod kraju (ISO 3166-1 alpha-2)
    
    Returns:
        Słownik z danymi o kraju
    """
    country_code = country_code.upper()
    
    # Pobierz podstawowe informacje o kraju
    country_info = provider.get_country_info(country_code, CONFIG_LANGUAGE)
    
    if isinstance(country_info, list):
        country_info = country_info[0] if country_info else {}
    
    # Pobierz stolicę
    capital = provider.get_capital(country_code, CONFIG_LANGUAGE)
    
    # Pobierz strefy czasowe
    timezones = get_timezones_for_country(provider, country_code)
    
    # Pobierz bounding box
    bbox = get_country_bounding_box(provider, country_code)
    
    # Przygotuj dane
    data = {
        'country_code': country_code,
        'country_name': country_info.get('countryName', 'N/A'),
        'population': country_info.get('population', 'N/A'),
        'capital': country_info.get('capital', 'N/A'),
        'capital_population': capital.get('population', 'N/A') if capital else 'N/A',
        'area_km2': country_info.get('areaInSqKm', 'N/A'),
        'continent': country_info.get('continentName', 'N/A'),
        'timezones': timezones,
        'timezone_count': len(timezones),
        'bounding_box': bbox if bbox else None
    }
    
    return data


def display_country_info(data: Dict):
    """Wyświetla informacje o kraju w czytelnej formie."""
    print("\n" + "="*70)
    print(f"INFORMACJE O KRAJU: {data['country_name']} ({data['country_code']})")
    print("="*70)
    
    print(f"\nKraj: {data['country_name']}")
    print(f"Kod kraju: {data['country_code']}")
    
    # Populacja kraju
    pop = data['population']
    if pop != 'N/A' and isinstance(pop, (int, str)):
        try:
            pop_int = int(pop)
            print(f"Populacja: {pop_int:,}")
        except (ValueError, TypeError):
            print(f"Populacja: {pop}")
    else:
        print(f"Populacja: {pop}")
    
    print(f"Stolica: {data['capital']}")
    
    # Populacja stolicy
    if data['capital_population'] != 'N/A':
        cap_pop = data['capital_population']
        if isinstance(cap_pop, (int, str)):
            try:
                cap_pop_int = int(cap_pop)
                print(f"Populacja stolicy: {cap_pop_int:,}")
            except (ValueError, TypeError):
                print(f"Populacja stolicy: {cap_pop}")
        else:
            print(f"Populacja stolicy: {cap_pop}")
    else:
        print("Populacja stolicy: N/A")
    
    if data['area_km2'] != 'N/A':
        area = data['area_km2']
        if isinstance(area, (int, float, str)):
            try:
                area_float = float(area)
                print(f"Powierzchnia: {area_float:,.0f} km²")
            except:
                print(f"Powierzchnia: {area} km²")
        else:
            print(f"Powierzchnia: {area} km²")
    else:
        print("Powierzchnia: N/A")
    
    print(f"Kontynent: {data['continent']}")
    
    # Strefy czasowe
    if data['timezones']:
        if len(data['timezones']) == 1:
            print(f"Strefa czasowa: {data['timezones'][0]}")
        else:
            print(f"\nStrefy czasowe ({data['timezone_count']}):")
            for tz in data['timezones']:
                print(f"  - {tz}")
    else:
        print("Strefa czasowa: N/A")
    
    # Rozpiętość geograficzna
    if data['bounding_box']:
        bbox = data['bounding_box']
        print(f"\nRozpiętość geograficzna:")
        print(f"  Północ: {bbox['north']:.6f}°")
        print(f"  Południe: {bbox['south']:.6f}°")
        print(f"  Wschód: {bbox['east']:.6f}°")
        print(f"  Zachód: {bbox['west']:.6f}°")
        print(f"  Środek: {bbox['center_lat']:.6f}°, {bbox['center_lng']:.6f}°")
        print(f"  Rozpiętość N-S: {bbox['north'] - bbox['south']:.2f}°")
        print(f"  Rozpiętość E-W: {bbox['east'] - bbox['west']:.2f}°")
    else:
        print("\nRozpiętość geograficzna: N/A")
    
    print("="*70 + "\n")


def export_to_json(data: Dict, filename: str):
    """Eksportuje dane do pliku JSON."""
    os.makedirs(CONFIG_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(CONFIG_OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if CONFIG_VERBOSE:
            print(f"✓ Zapisano do JSON: {filepath}")
        return True
    except Exception as e:
        print(f"Błąd podczas zapisywania do JSON: {e}")
        return False


def export_to_csv(data: Dict, filename: str):
    """Eksportuje dane do pliku CSV."""
    import csv
    
    os.makedirs(CONFIG_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(CONFIG_OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Parametr', 'Wartość'])
            writer.writerow(['Kraj', data['country_name']])
            writer.writerow(['Kod kraju', data['country_code']])
            writer.writerow(['Populacja', data['population']])
            writer.writerow(['Stolica', data['capital']])
            writer.writerow(['Populacja stolicy', data['capital_population']])
            writer.writerow(['Powierzchnia (km²)', data['area_km2']])
            writer.writerow(['Kontynent', data['continent']])
            writer.writerow(['Strefy czasowe', ', '.join(data['timezones']) if data['timezones'] else 'N/A'])
            
            if data['bounding_box']:
                bbox = data['bounding_box']
                writer.writerow(['Północ', bbox['north']])
                writer.writerow(['Południe', bbox['south']])
                writer.writerow(['Wschód', bbox['east']])
                writer.writerow(['Zachód', bbox['west']])
                writer.writerow(['Środek lat', bbox['center_lat']])
                writer.writerow(['Środek lng', bbox['center_lng']])
        
        if CONFIG_VERBOSE:
            print(f"✓ Zapisano do CSV: {filepath}")
        return True
    except Exception as e:
        print(f"Błąd podczas zapisywania do CSV: {e}")
        return False


def main():
    """Główna funkcja programu."""
    if CONFIG_VERBOSE:
        print("="*70)
        print("SKRYPT INFORMACJI O KRAJU")
        print("="*70)
        print(f"Kod kraju: {CONFIG_COUNTRY_CODE}")
        print(f"Język: {CONFIG_LANGUAGE}")
        print("="*70)
    
    # Inicjalizacja providera
    try:
        provider = GeonamesProvider()
        if CONFIG_VERBOSE:
            print(f"✓ Provider zainicjalizowany (username: {provider.username})")
    except Exception as e:
        print(f"Błąd inicjalizacji providera: {e}")
        return 1
    
    # Pobierz dane o kraju
    if CONFIG_VERBOSE:
        print(f"\nPobieranie danych o kraju {CONFIG_COUNTRY_CODE}...")
    
    try:
        data = get_country_data(provider, CONFIG_COUNTRY_CODE)
        
        if not data or data.get('country_name') == 'N/A':
            print(f"Błąd: Nie znaleziono danych dla kraju {CONFIG_COUNTRY_CODE}")
            return 1
        
        # Wyświetl informacje
        display_country_info(data)
        
        # Eksport
        if CONFIG_EXPORT_JSON:
            filename = f"country_info_{CONFIG_COUNTRY_CODE.lower()}.json"
            export_to_json(data, filename)
        
        if CONFIG_EXPORT_CSV:
            filename = f"country_info_{CONFIG_COUNTRY_CODE.lower()}.csv"
            export_to_csv(data, filename)
        
        if CONFIG_VERBOSE:
            print("Zakończono pomyślnie!")
        
        return 0
    
    except Exception as e:
        print(f"Błąd: {e}")
        import traceback
        if CONFIG_VERBOSE:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

