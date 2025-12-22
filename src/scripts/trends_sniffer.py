#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania danych z Google Trends za pomocą PyTrends.
Wszystkie parametry konfiguracyjne znajdują się na górze pliku.
"""

# ============================================================================
# KONFIGURACJA - Ustaw tutaj wszystkie parametry
# ============================================================================

# --- Parametry inicjalizacji TrendReq ---
CONFIG_LANGUAGE = 'pl-PL'          # Język interfejsu (pl-PL, en-US, de-DE, itp.)
CONFIG_TIMEZONE = -120             # Strefa czasowa w minutach od UTC (-120 = UTC-2 dla Polski)
CONFIG_RETRIES = 2                 # Liczba ponownych prób przy błędach
CONFIG_BACKOFF_FACTOR = 0.1        # Czas oczekiwania między ponownymi próbami (w sekundach)
CONFIG_REQUESTS_ARGS = None        # Dodatkowe nagłówki HTTP (None lub dict, np. {'headers': {'User-Agent': '...'}})

# --- Parametry zapytania (build_payload) ---
CONFIG_KEYWORDS = ["BTC"]  # Lista słów kluczowych (maksymalnie 5)
CONFIG_CATEGORY = 0                # Kategoria (0 = wszystkie, 7 = Finanse, 71 = Technologia, itd.)
CONFIG_TIMEFRAME = 'now 1-H'   # Zakres czasowy:
                                   #   'today 5-y' - ostatnie 5 lat
                                   #   'today 12-m' - ostatnie 12 miesięcy
                                   #   'today 3-m' - ostatnie 3 miesiące
                                   #   'today 1-m' - ostatni miesiąc
                                   #   'now 7-d' - ostatnie 7 dni
                                   #   'now 1-d' - ostatnie 24 godziny
                                   #   'YYYY-MM-DD YYYY-MM-DD' - zakres dat (np. '2020-01-01 2020-12-31')
CONFIG_COUNTRY = 'US'             # Kod kraju (PL, US, DE, GB, '' dla całego świata)
                                   # Lista kodów: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
CONFIG_REGION = None               # Kod regionu (opcjonalnie, np. 'PL-MZ' dla Mazowsza)
CONFIG_CITY = None                 # Nazwa miasta (opcjonalnie, np. 'Warsaw')
CONFIG_GPROP = ''                  # Typ wyszukiwania:
                                   #   '' - wyszukiwanie w sieci (domyślnie)
                                   #   'images' - wyszukiwanie obrazów
                                   #   'news' - wyszukiwanie wiadomości
                                   #   'youtube' - wyszukiwanie w YouTube
                                   #   'froogle' - wyszukiwanie produktów

# --- Parametry pobierania danych regionalnych (interest_by_region) ---
CONFIG_RESOLUTION = 'COUNTRY'       # Poziom szczegółowości:
                                   #   'COUNTRY' - kraje
                                   #   'REGION' - regiony (np. województwa w Polsce)
                                   #   'CITY' - miasta
                                   #   'DMA' - Designated Market Area (tylko dla USA)
CONFIG_INC_LOW_VOL = True          # Uwzględnia regiony o niskim wolumenie wyszukiwań
CONFIG_INC_GEO_CODE = False        # Uwzględnia kody geograficzne w wynikach

# --- Parametry eksportu danych ---
CONFIG_EXPORT_CSV = False           # Czy eksportować dane do pliku CSV
CONFIG_EXPORT_JSON = False         # Czy eksportować dane do pliku JSON
CONFIG_EXPORT_DB = False           # Czy eksportować dane do bazy PostgreSQL
CONFIG_OUTPUT_DIR = 'output'       # Katalog do zapisu plików wyjściowych
CONFIG_CSV_FILENAME = 'trends_data.csv'  # Nazwa pliku CSV
CONFIG_JSON_FILENAME = 'trends_data.json' # Nazwa pliku JSON

# --- Parametry bazy danych (jeśli CONFIG_EXPORT_DB = True) ---
CONFIG_DB_HOST = 'localhost'       # Host bazy danych
CONFIG_DB_PORT = 5432              # Port bazy danych
CONFIG_DB_NAME = 'trends_sniffer'  # Nazwa bazy danych
CONFIG_DB_USER = 'octadecimal'     # Użytkownik bazy danych
CONFIG_DB_PASSWORD = None          # Hasło bazy danych (None jeśli nie wymagane)
CONFIG_DB_TABLE = 'trends_data'    # Nazwa tabeli w bazie danych

# --- Parametry dodatkowe ---
CONFIG_SHOW_PLOTS = True          # Czy wyświetlać wykresy (wymaga matplotlib)
CONFIG_SAVE_PLOTS = False          # Czy zapisywać wykresy do plików
CONFIG_PLOT_FORMAT = 'png'         # Format wykresów (png, pdf, svg)
CONFIG_VERBOSE = True              # Czy wyświetlać szczegółowe informacje

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import os
import sys
from src.services.trends_sniffer_service import TrendsSnifferService


def print_config():
    """Wyświetla aktualną konfigurację."""
    if not CONFIG_VERBOSE:
        return
    
    print("=" * 70)
    print("KONFIGURACJA TRENDS SNIFFER")
    print("=" * 70)
    print(f"Język: {CONFIG_LANGUAGE}")
    print(f"Strefa czasowa: UTC{CONFIG_TIMEZONE/60:+.0f}")
    print(f"Słowa kluczowe: {', '.join(CONFIG_KEYWORDS)}")
    print(f"Kategoria: {CONFIG_CATEGORY}")
    print(f"Zakres czasowy: {CONFIG_TIMEFRAME}")
    print(f"Kraj: {CONFIG_COUNTRY if CONFIG_COUNTRY else 'Cały świat'}")
    if CONFIG_REGION:
        print(f"Region: {CONFIG_REGION}")
    if CONFIG_CITY:
        print(f"Miasto: {CONFIG_CITY}")
    print(f"Typ wyszukiwania: {CONFIG_GPROP if CONFIG_GPROP else 'Wyszukiwanie w sieci'}")
    print(f"Rozdzielczość regionalna: {CONFIG_RESOLUTION}")
    print("=" * 70)
    print()


def main():
    """Główna funkcja programu."""
    print_config()
    
    # Inicjalizacja serwisu
    service = TrendsSnifferService(
        language=CONFIG_LANGUAGE,
        timezone=CONFIG_TIMEZONE,
        retries=CONFIG_RETRIES,
        backoff_factor=CONFIG_BACKOFF_FACTOR,
        requests_args=CONFIG_REQUESTS_ARGS,
        verbose=CONFIG_VERBOSE
    )
    
    # Budowanie zapytania
    if not service.build_payload(
        keywords=CONFIG_KEYWORDS,
        category=CONFIG_CATEGORY,
        timeframe=CONFIG_TIMEFRAME,
        country=CONFIG_COUNTRY,
        region=CONFIG_REGION,
        city=CONFIG_CITY,
        gprop=CONFIG_GPROP
    ):
        return 1
    
    # Pobieranie danych
    results = {}
    
    # Zainteresowanie w czasie
    data_time = service.get_interest_over_time()
    if data_time is not None:
        results['time'] = data_time
        
        # Wyświetl podgląd
        if CONFIG_VERBOSE:
            print("\nPodgląd danych (pierwsze 5 wierszy):")
            print(data_time.head())
            print("\nStatystyki:")
            print(data_time.describe())
    
    # Zainteresowanie według regionu
    data_region = service.get_interest_by_region(
        resolution=CONFIG_RESOLUTION,
        inc_low_vol=CONFIG_INC_LOW_VOL,
        inc_geo_code=CONFIG_INC_GEO_CODE
    )
    if data_region is not None:
        results['region'] = data_region
        
        if CONFIG_VERBOSE:
            print("\nTop 10 regionów:")
            for keyword in CONFIG_KEYWORDS:
                if keyword in data_region.columns:
                    top_regions = data_region.sort_values(keyword, ascending=False).head(10)
                    print(f"\n{keyword}:")
                    print(top_regions[keyword])
    
    # Powiązane zapytania
    related = service.get_related_queries()
    if related:
        results['related'] = related
        
        if CONFIG_VERBOSE:
            print("\nPowiązane zapytania:")
            for keyword in CONFIG_KEYWORDS:
                if keyword in related:
                    print(f"\n=== {keyword} ===")
                    # Top queries
                    if 'top' in related[keyword] and related[keyword]['top'] is not None:
                        if not related[keyword]['top'].empty:
                            print("Top queries:")
                            print(related[keyword]['top'].head(10))
                        else:
                            print("Top queries: Brak wyników")
                    else:
                        print("Top queries: Brak wyników")
                    
                    # Rising queries
                    if 'rising' in related[keyword] and related[keyword]['rising'] is not None:
                        if not related[keyword]['rising'].empty:
                            print("Rising queries:")
                            print(related[keyword]['rising'].head(10))
                        else:
                            print("Rising queries: Brak wyników")
                    else:
                        print("Rising queries: Brak wyników")
    
    # Eksport danych
    if CONFIG_EXPORT_CSV and 'time' in results:
        csv_path = os.path.join(CONFIG_OUTPUT_DIR, CONFIG_CSV_FILENAME)
        service.export_to_csv(results['time'], csv_path)
    
    if CONFIG_EXPORT_JSON and 'time' in results:
        json_path = os.path.join(CONFIG_OUTPUT_DIR, CONFIG_JSON_FILENAME)
        service.export_to_json(results['time'], json_path)
    
    if CONFIG_EXPORT_DB and 'time' in results:
        service.export_to_database(
            data=results['time'],
            host=CONFIG_DB_HOST,
            port=CONFIG_DB_PORT,
            database=CONFIG_DB_NAME,
            user=CONFIG_DB_USER,
            password=CONFIG_DB_PASSWORD,
            table_name=CONFIG_DB_TABLE
        )
    
    # Wykresy
    if (CONFIG_SHOW_PLOTS or CONFIG_SAVE_PLOTS) and 'time' in results:
        plot_path = None
        if CONFIG_SAVE_PLOTS:
            plot_path = os.path.join(
                CONFIG_OUTPUT_DIR,
                f"trends_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{CONFIG_PLOT_FORMAT}"
            )
        
        service.create_plot(
            data=results['time'],
            keywords=CONFIG_KEYWORDS,
            show=CONFIG_SHOW_PLOTS,
            save=CONFIG_SAVE_PLOTS,
            filepath=plot_path,
            format=CONFIG_PLOT_FORMAT
        )
    
    if CONFIG_VERBOSE:
        print("\n" + "=" * 70)
        print("Zakończono pomyślnie!")
        print("=" * 70)
    
    return 0


if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
