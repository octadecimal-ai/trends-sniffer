#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy do pobierania maksymalnej ilości informacji o kraju.
Wykorzystuje GeonamesProvider i WorldBankService do pobrania wszystkich dostępnych danych.
"""

# ============================================================================
# KONFIGURACJA - Ustaw tutaj wszystkie parametry
# ============================================================================

# --- Parametry kraju ---
CONFIG_COUNTRY_CODE = "PL"          # Kod kraju (ISO 3166-1 alpha-2, np. 'PL', 'US', 'DE')
CONFIG_LANGUAGE = "pl"              # Język odpowiedzi ('pl', 'en', 'de', itp.)

# --- Parametry wyświetlania ---
CONFIG_VERBOSE = True               # Czy wyświetlać szczegółowe informacje
CONFIG_EXPORT_JSON = False          # Czy eksportować do JSON
CONFIG_EXPORT_CSV = False           # Czy eksportować do CSV
CONFIG_OUTPUT_DIR = "output"       # Katalog wyjściowy

# --- Parametry danych World Bank ---
CONFIG_WB_INDICATORS = [            # Lista wskaźników do pobrania z World Bank
    'SP.POP.TOTL',                  # Populacja całkowita
    'NY.GDP.MKTP.CD',               # PKB (nominalny, USD)
    'NY.GDP.PCAP.CD',               # PKB per capita (USD)
    'SP.DYN.LE00.IN',               # Oczekiwana długość życia
    'SE.ADT.LITR.ZS',               # Wskaźnik alfabetyzacji dorosłych
    'IT.NET.USER.ZS',               # Użytkownicy Internetu (% populacji)
    'EN.ATM.CO2E.PC',               # Emisja CO2 per capita
    'AG.LND.TOTL.K2',               # Powierzchnia lądu (km²)
    'SP.URB.TOTL.IN.ZS',            # Populacja miejska (% całkowitej)
    'SL.UEM.TOTL.ZS',               # Stopa bezrobocia (% siły roboczej)
]

CONFIG_WB_START_YEAR = 2000         # Rok początkowy dla danych World Bank
CONFIG_WB_END_YEAR = 2023           # Rok końcowy dla danych World Bank

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import json
from typing import Dict, List, Optional
from datetime import datetime

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.providers.geonames_provider import GeonamesProvider
from src.services.world_bank_service import WorldBankService


def convert_country_code_iso2_to_iso3(iso2_code: str) -> Optional[str]:
    """
    Konwertuje kod kraju z ISO 3166-1 alpha-2 na ISO 3166-1 alpha-3.
    
    Args:
        iso2_code: Kod kraju ISO 2 (np. 'PL')
    
    Returns:
        Kod kraju ISO 3 (np. 'POL') lub None jeśli nie znaleziono
    """
    # Mapowanie najpopularniejszych kodów
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
    }
    
    return mapping.get(iso2_code.upper())


def get_geonames_info(provider: GeonamesProvider, country_code: str, lang: str) -> Dict:
    """
    Pobiera wszystkie dostępne informacje o kraju z Geonames.
    
    Args:
        provider: Instancja GeonamesProvider
        country_code: Kod kraju ISO 2
        lang: Język odpowiedzi
    
    Returns:
        Słownik z informacjami o kraju z Geonames
    """
    info = {}
    
    try:
        # Podstawowe informacje o kraju
        country_info = provider.get_country_info(country_code, lang=lang)
        if country_info:
            info['basic'] = country_info
        
        # Stolica
        capital_name = country_info.get('capital', '') if country_info else ''
        if capital_name:
            try:
                capital_info = provider.get_capital(country_code, lang=lang)
                if capital_info:
                    info['capital'] = capital_info
            except:
                pass
        
        # Regiony (województwa/provincje)
        try:
            regions = provider.get_regions(country_code, feature_code='ADM1', lang=lang)
            if regions:
                info['regions'] = regions[:20]  # Ogranicz do 20 największych
        except:
            pass
        
        # Największe miasta
        try:
            cities = provider.search_cities('', country=country_code, max_rows=20, lang=lang)
            if cities:
                info['major_cities'] = cities
        except:
            pass
        
        # Strefa czasowa
        try:
            if country_info:
                lat = country_info.get('lat', '')
                lng = country_info.get('lng', '')
                if lat and lng:
                    timezone_info = provider.get_timezone(float(lat), float(lng))
                    if timezone_info:
                        info['timezone'] = timezone_info
        except:
            pass
        
        # Rozpiętość geograficzna (bounding box)
        try:
            if country_info:
                bbox = {
                    'north': country_info.get('north', ''),
                    'south': country_info.get('south', ''),
                    'east': country_info.get('east', ''),
                    'west': country_info.get('west', ''),
                }
                if all(bbox.values()):
                    info['bounding_box'] = bbox
        except:
            pass
        
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"Błąd podczas pobierania danych z Geonames: {e}")
    
    return info


def get_world_bank_info(service: WorldBankService, iso3_code: str) -> Dict:
    """
    Pobiera wszystkie dostępne informacje o kraju z World Bank.
    
    Args:
        service: Instancja WorldBankService
        iso3_code: Kod kraju ISO 3
    
    Returns:
        Słownik z informacjami o kraju z World Bank
    """
    info = {}
    
    try:
        # Informacje o kraju
        country_info = service.get_country_details(iso3_code)
        if country_info:
            info['country_info'] = country_info
        
        # Dane dla różnych wskaźników
        indicators_data = {}
        for indicator_code in CONFIG_WB_INDICATORS:
            try:
                data = service.get_data_for_indicator(
                    indicator_code=indicator_code,
                    country_codes=iso3_code,
                    start_year=CONFIG_WB_START_YEAR,
                    end_year=CONFIG_WB_END_YEAR
                )
                if data:
                    # Pobierz najnowsze dane
                    latest_data = None
                    latest_year = 0
                    for record in data:
                        year = int(record.get('date', '0'))
                        if year > latest_year and record.get('value') is not None:
                            latest_year = year
                            latest_data = record
                    
                    if latest_data:
                        indicator_name = latest_data.get('indicator', {}).get('value', indicator_code)
                        indicators_data[indicator_code] = {
                            'name': indicator_name,
                            'latest_value': latest_data.get('value'),
                            'latest_year': latest_year,
                            'all_data': data[:10]  # Ostatnie 10 lat
                        }
            except Exception as e:
                if CONFIG_VERBOSE:
                    print(f"Błąd podczas pobierania wskaźnika {indicator_code}: {e}")
        
        if indicators_data:
            info['indicators'] = indicators_data
        
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"Błąd podczas pobierania danych z World Bank: {e}")
    
    return info


def display_full_country_info(geonames_info: Dict, world_bank_info: Dict, country_code: str):
    """
    Wyświetla wszystkie zebrane informacje o kraju w czytelnej formie.
    
    Args:
        geonames_info: Informacje z Geonames
        world_bank_info: Informacje z World Bank
        country_code: Kod kraju
    """
    print("\n" + "="*80)
    print(f"PEŁNE INFORMACJE O KRAJU: {country_code}")
    print("="*80)
    
    # Informacje podstawowe z Geonames
    if 'basic' in geonames_info:
        basic = geonames_info['basic']
        print("\n" + "-"*80)
        print("INFORMACJE PODSTAWOWE (Geonames)")
        print("-"*80)
        print(f"Kraj: {basic.get('countryName', 'N/A')}")
        print(f"Kod ISO 2: {basic.get('countryCode', 'N/A')}")
        print(f"Kod ISO 3: {basic.get('isoAlpha3', 'N/A')}")
        print(f"Populacja: {basic.get('population', 'N/A'):,}" if isinstance(basic.get('population'), int) else f"Populacja: {basic.get('population', 'N/A')}")
        print(f"Powierzchnia: {basic.get('areaInSqKm', 'N/A'):,} km²" if isinstance(basic.get('areaInSqKm'), (int, float)) else f"Powierzchnia: {basic.get('areaInSqKm', 'N/A')} km²")
        print(f"Kontynent: {basic.get('continentName', 'N/A')}")
        print(f"Waluta: {basic.get('currencyCode', 'N/A')}")
        print(f"Języki: {basic.get('languages', 'N/A')}")
    
    # Stolica
    if 'capital' in geonames_info:
        capital = geonames_info['capital']
        print(f"\nStolica: {capital.get('name', 'N/A')}")
        if 'population' in capital:
            print(f"  Populacja stolicy: {capital.get('population', 'N/A'):,}" if isinstance(capital.get('population'), int) else f"  Populacja stolicy: {capital.get('population', 'N/A')}")
        if 'lat' in capital and 'lng' in capital:
            print(f"  Współrzędne: {capital.get('lat', 'N/A')}, {capital.get('lng', 'N/A')}")
    
    # Strefa czasowa
    if 'timezone' in geonames_info:
        tz = geonames_info['timezone']
        print(f"\nStrefa czasowa: {tz.get('timezoneId', 'N/A')}")
        print(f"  UTC offset: {tz.get('gmtOffset', 'N/A')}")
    
    # Rozpiętość geograficzna
    if 'bounding_box' in geonames_info:
        bbox = geonames_info['bounding_box']
        print(f"\nRozpiętość geograficzna:")
        print(f"  Północ: {bbox.get('north', 'N/A')}°")
        print(f"  Południe: {bbox.get('south', 'N/A')}°")
        print(f"  Wschód: {bbox.get('east', 'N/A')}°")
        print(f"  Zachód: {bbox.get('west', 'N/A')}°")
    
    # Regiony
    if 'regions' in geonames_info:
        regions = geonames_info['regions']
        print(f"\nRegiony/Województwa ({len(regions)}):")
        for i, region in enumerate(regions[:10], 1):
            print(f"  {i}. {region.get('name', 'N/A')}")
        if len(regions) > 10:
            print(f"  ... i {len(regions) - 10} więcej")
    
    # Największe miasta
    if 'major_cities' in geonames_info:
        cities = geonames_info['major_cities']
        print(f"\nNajwiększe miasta ({len(cities)}):")
        for i, city in enumerate(cities[:10], 1):
            pop = city.get('population', 'N/A')
            if isinstance(pop, int):
                pop = f"{pop:,}"
            print(f"  {i}. {city.get('name', 'N/A')} - {pop} mieszkańców")
        if len(cities) > 10:
            print(f"  ... i {len(cities) - 10} więcej")
    
    # Informacje z World Bank
    if 'country_info' in world_bank_info:
        wb_country = world_bank_info['country_info']
        print("\n" + "-"*80)
        print("INFORMACJE EKONOMICZNE (World Bank)")
        print("-"*80)
        print(f"Region: {wb_country.get('region', {}).get('value', 'N/A')}")
        print(f"Poziom dochodów: {wb_country.get('incomeLevel', {}).get('value', 'N/A')}")
        print(f"Typ pożyczek: {wb_country.get('lendingType', {}).get('value', 'N/A')}")
        if 'capitalCity' in wb_country:
            print(f"Kapitał: {wb_country.get('capitalCity', 'N/A')}")
    
    # Wskaźniki ekonomiczne
    if 'indicators' in world_bank_info:
        indicators = world_bank_info['indicators']
        print(f"\nWskaźniki ekonomiczne i społeczne ({len(indicators)}):")
        for code, data in indicators.items():
            value = data.get('latest_value')
            year = data.get('latest_year')
            name = data.get('name', code)
            
            if value is not None:
                # Formatuj wartość
                try:
                    value_float = float(value)
                    if value_float >= 1000000:
                        value_str = f"{value_float/1000000:.2f}M"
                    elif value_float >= 1000:
                        value_str = f"{value_float/1000:.2f}K"
                    else:
                        value_str = f"{value_float:.2f}"
                except:
                    value_str = str(value)
                
                print(f"  • {name}: {value_str} ({year})")
            else:
                print(f"  • {name}: Brak danych")
    
    print("\n" + "="*80)


def export_data(geonames_info: Dict, world_bank_info: Dict, country_code: str):
    """
    Eksportuje dane do plików JSON i CSV.
    
    Args:
        geonames_info: Informacje z Geonames
        world_bank_info: Informacje z World Bank
        country_code: Kod kraju
    """
    os.makedirs(CONFIG_OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Eksport JSON
    if CONFIG_EXPORT_JSON:
        json_file = os.path.join(CONFIG_OUTPUT_DIR, f"country_full_info_{country_code}_{timestamp}.json")
        all_data = {
            'country_code': country_code,
            'timestamp': timestamp,
            'geonames': geonames_info,
            'world_bank': world_bank_info
        }
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Zapisano dane do JSON: {json_file}")
        except Exception as e:
            print(f"\n✗ Błąd podczas zapisywania JSON: {e}")
    
    # Eksport CSV (tylko wskaźniki World Bank)
    if CONFIG_EXPORT_CSV and 'indicators' in world_bank_info:
        import pandas as pd
        
        csv_file = os.path.join(CONFIG_OUTPUT_DIR, f"country_indicators_{country_code}_{timestamp}.csv")
        
        try:
            rows = []
            for code, data in world_bank_info['indicators'].items():
                rows.append({
                    'indicator_code': code,
                    'indicator_name': data.get('name', code),
                    'latest_value': data.get('latest_value'),
                    'latest_year': data.get('latest_year')
                })
            
            df = pd.DataFrame(rows)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✓ Zapisano wskaźniki do CSV: {csv_file}")
        except Exception as e:
            print(f"✗ Błąd podczas zapisywania CSV: {e}")


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("SKRYPT TESTOWY - PEŁNE INFORMACJE O KRAJU")
    print("="*80)
    print(f"Kod kraju: {CONFIG_COUNTRY_CODE}")
    print(f"Język: {CONFIG_LANGUAGE}")
    print("="*80)
    
    # Konwertuj kod ISO 2 na ISO 3 dla World Bank
    iso3_code = convert_country_code_iso2_to_iso3(CONFIG_COUNTRY_CODE)
    if not iso3_code:
        print(f"\n✗ Nie można znaleźć kodu ISO 3 dla kraju: {CONFIG_COUNTRY_CODE}")
        print("  Użyj kodu ISO 3 bezpośrednio w kodzie źródłowym")
        return 1
    
    if CONFIG_VERBOSE:
        print(f"\nKod ISO 3: {iso3_code}")
    
    # Inicjalizacja providerów
    try:
        geonames_provider = GeonamesProvider()
        if CONFIG_VERBOSE:
            print(f"✓ GeonamesProvider zainicjalizowany")
    except Exception as e:
        print(f"\n✗ Błąd inicjalizacji GeonamesProvider: {e}")
        print("  Upewnij się, że zmienna GEONAMES_LOGIN jest ustawiona w pliku .env")
        geonames_provider = None
    
    world_bank_service = WorldBankService(verbose=CONFIG_VERBOSE)
    if CONFIG_VERBOSE:
        print(f"✓ WorldBankService zainicjalizowany")
    
    # Pobierz informacje
    geonames_info = {}
    if geonames_provider:
        if CONFIG_VERBOSE:
            print(f"\nPobieranie informacji z Geonames...")
        geonames_info = get_geonames_info(geonames_provider, CONFIG_COUNTRY_CODE, CONFIG_LANGUAGE)
    
    if CONFIG_VERBOSE:
        print(f"\nPobieranie informacji z World Bank...")
    world_bank_info = get_world_bank_info(world_bank_service, iso3_code)
    
    # Wyświetl informacje
    display_full_country_info(geonames_info, world_bank_info, CONFIG_COUNTRY_CODE)
    
    # Eksport danych
    if CONFIG_EXPORT_JSON or CONFIG_EXPORT_CSV:
        export_data(geonames_info, world_bank_info, CONFIG_COUNTRY_CODE)
    
    if CONFIG_VERBOSE:
        print("\n✓ Zakończono pomyślnie!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

