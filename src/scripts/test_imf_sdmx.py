#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy do pobierania maksymalnej ilości informacji z API IMF SDMX 3.0.
Wykorzystuje IMFSDMXService do pobrania wszystkich dostępnych danych.
"""

# ============================================================================
# KONFIGURACJA - Ustaw tutaj wszystkie parametry
# ============================================================================

# --- Parametry API ---
CONFIG_SUBSCRIPTION_KEY = None          # Klucz subskrypcji (None = pobiera z .env jako IMF_SUBSCRIPTION_KEY)
CONFIG_AGENCY_ID = "IMF"                 # Identyfikator agencji (domyślnie 'IMF')

# --- Parametry testowania ---
CONFIG_CONTEXT = "dataflow"              # Kontekst do testowania (np. 'dataflow', 'datastructure')
CONFIG_RESOURCE_ID = "IFS"               # Identyfikator zasobu (np. 'IFS' dla International Financial Statistics)
CONFIG_VERSION = "latest"                 # Wersja zasobu (domyślnie 'latest')
CONFIG_KEY = "*"                         # Klucz identyfikujący dane (domyślnie '*' dla wszystkich)
CONFIG_COMPONENT_ID = None               # Identyfikator komponentu (opcjonalnie)

# --- Parametry wyświetlania ---
CONFIG_VERBOSE = True                    # Czy wyświetlać szczegółowe informacje
CONFIG_EXPORT_JSON = False               # Czy eksportować do JSON
CONFIG_OUTPUT_DIR = "output"             # Katalog wyjściowy

# --- Parametry danych ---
CONFIG_DATAFLOW = "IFS"                   # Dataflow do pobrania danych (np. 'IFS')
CONFIG_START_PERIOD = "2020"             # Okres początkowy (np. '2020', '2020-Q1')
CONFIG_END_PERIOD = "2023"               # Okres końcowy (np. '2023', '2023-Q4')
CONFIG_DATA_KEY = None                   # Klucz danych (opcjonalnie, None = wszystkie)

# --- Parametry wyszukiwania ---
CONFIG_SEARCH_QUERY = None               # Zapytanie do wyszukania dataflow (opcjonalnie)

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import json
from datetime import datetime

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.services.imf_sdmx_service import IMFSDMXService


def display_availability_info(availability: dict):
    """
    Wyświetla informacje o dostępności danych w czytelnej formie.
    
    Args:
        availability: Słownik z informacjami o dostępności danych
    """
    print("\n" + "="*80)
    print("INFORMACJE O DOSTĘPNOŚCI DANYCH")
    print("="*80)
    
    # Struktura odpowiedzi może się różnić w zależności od API
    # Wyświetl podstawowe informacje
    if isinstance(availability, dict):
        for key, value in availability.items():
            if isinstance(value, (dict, list)):
                print(f"\n{key}:")
                if isinstance(value, list) and len(value) > 0:
                    for item in value[:5]:  # Pokaż pierwsze 5 elementów
                        print(f"  - {item}")
                    if len(value) > 5:
                        print(f"  ... i {len(value) - 5} więcej")
                elif isinstance(value, dict):
                    for sub_key, sub_value in list(value.items())[:10]:
                        print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
    else:
        print(json.dumps(availability, indent=2, ensure_ascii=False))
    
    print("="*80)


def display_dataflow_info(info: dict):
    """
    Wyświetla informacje o dataflow w czytelnej formie.
    
    Args:
        info: Słownik z informacjami o dataflow
    """
    print("\n" + "="*80)
    print("INFORMACJE O DATAFLOW")
    print("="*80)
    
    # Struktura odpowiedzi może się różnić
    if isinstance(info, dict):
        for key, value in info.items():
            if isinstance(value, (dict, list)):
                print(f"\n{key}:")
                if isinstance(value, list) and len(value) > 0:
                    for item in value[:5]:
                        print(f"  - {item}")
                    if len(value) > 5:
                        print(f"  ... i {len(value) - 5} więcej")
                elif isinstance(value, dict):
                    for sub_key, sub_value in list(value.items())[:10]:
                        print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
    else:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    print("="*80)


def display_data_info(data: dict):
    """
    Wyświetla informacje o danych w czytelnej formie.
    
    Args:
        data: Słownik z danymi statystycznymi
    """
    print("\n" + "="*80)
    print("DANE STATYSTYCZNE")
    print("="*80)
    
    # Struktura odpowiedzi może się różnić
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"\n{key}:")
                if isinstance(value, list):
                    print(f"  Liczba rekordów: {len(value)}")
                    if len(value) > 0:
                        print(f"  Przykładowe dane (pierwsze 3):")
                        for item in value[:3]:
                            print(f"    {item}")
                elif isinstance(value, dict):
                    for sub_key, sub_value in list(value.items())[:10]:
                        print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("="*80)


def main():
    """Główna funkcja programu."""
    print("="*80)
    print("SKRYPT TESTOWY - API IMF SDMX 3.0")
    print("="*80)
    print(f"Agencja: {CONFIG_AGENCY_ID}")
    print(f"Kontekst: {CONFIG_CONTEXT}")
    print(f"Zasób: {CONFIG_RESOURCE_ID}")
    print(f"Wersja: {CONFIG_VERSION}")
    print("="*80)
    
    # Inicjalizacja serwisu
    try:
        service = IMFSDMXService(
            subscription_key=CONFIG_SUBSCRIPTION_KEY,
            verbose=CONFIG_VERBOSE
        )
        print("\n✓ Serwis zainicjalizowany")
    except ValueError as e:
        print(f"\n✗ Błąd inicjalizacji serwisu: {e}")
        print("\nAby użyć serwisu, ustaw zmienną IMF_SUBSCRIPTION_KEY w pliku .env")
        print("lub podaj subscription_key bezpośrednio w kodzie.")
        print("\nRejestracja: https://portal.api.imf.org/")
        return 1
    
    # Test 1: Pobierz informacje o dostępności danych
    print("\n" + "-"*80)
    print("TEST 1: Informacje o dostępności danych")
    print("-"*80)
    try:
        availability = service.get_availability_info(
            context=CONFIG_CONTEXT,
            agency_id=CONFIG_AGENCY_ID,
            resource_id=CONFIG_RESOURCE_ID,
            version=CONFIG_VERSION,
            key=CONFIG_KEY,
            component_id=CONFIG_COMPONENT_ID
        )
        display_availability_info(availability)
        
        if CONFIG_EXPORT_JSON:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(CONFIG_OUTPUT_DIR, f"imf_availability_{timestamp}.json")
            service.export_data_to_json(availability, json_file)
    except Exception as e:
        print(f"✗ Błąd podczas pobierania informacji o dostępności: {e}")
    
    # Test 2: Pobierz listę dataflow
    print("\n" + "-"*80)
    print("TEST 2: Lista dostępnych dataflow")
    print("-"*80)
    try:
        service.display_dataflow_list(agency_id=CONFIG_AGENCY_ID, limit=20)
    except Exception as e:
        print(f"✗ Błąd podczas pobierania listy dataflow: {e}")
    
    # Test 3: Wyszukaj dataflow (jeśli podano zapytanie)
    if CONFIG_SEARCH_QUERY:
        print("\n" + "-"*80)
        print(f"TEST 3: Wyszukiwanie dataflow: {CONFIG_SEARCH_QUERY}")
        print("-"*80)
        try:
            results = service.search_dataflow(CONFIG_SEARCH_QUERY, CONFIG_AGENCY_ID)
            print(f"\nZnaleziono {len(results)} dataflow:")
            for i, dataflow in enumerate(results[:10], 1):
                name = dataflow.get('name', {})
                if isinstance(name, dict):
                    name = name.get('value', 'N/A')
                print(f"  {i}. {dataflow.get('id', 'N/A')}: {name}")
        except Exception as e:
            print(f"✗ Błąd podczas wyszukiwania: {e}")
    
    # Test 4: Pobierz informacje o konkretnym dataflow
    print("\n" + "-"*80)
    print(f"TEST 4: Informacje o dataflow: {CONFIG_DATAFLOW}")
    print("-"*80)
    try:
        dataflow_info = service.get_dataflow_info(
            dataflow=CONFIG_DATAFLOW,
            agency_id=CONFIG_AGENCY_ID
        )
        display_dataflow_info(dataflow_info)
        
        if CONFIG_EXPORT_JSON:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(CONFIG_OUTPUT_DIR, f"imf_dataflow_{CONFIG_DATAFLOW}_{timestamp}.json")
            service.export_data_to_json(dataflow_info, json_file)
    except Exception as e:
        print(f"✗ Błąd podczas pobierania informacji o dataflow: {e}")
    
    # Test 5: Pobierz dane statystyczne
    print("\n" + "-"*80)
    print(f"TEST 5: Dane statystyczne dla dataflow: {CONFIG_DATAFLOW}")
    print("-"*80)
    try:
        data = service.get_data(
            dataflow=CONFIG_DATAFLOW,
            agency_id=CONFIG_AGENCY_ID,
            key=CONFIG_DATA_KEY,
            start_period=CONFIG_START_PERIOD,
            end_period=CONFIG_END_PERIOD
        )
        display_data_info(data)
        
        if CONFIG_EXPORT_JSON:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(CONFIG_OUTPUT_DIR, f"imf_data_{CONFIG_DATAFLOW}_{timestamp}.json")
            service.export_data_to_json(data, json_file)
    except Exception as e:
        print(f"✗ Błąd podczas pobierania danych: {e}")
    
    # Test 6: Pobierz schemat agencji
    print("\n" + "-"*80)
    print("TEST 6: Schemat agencji")
    print("-"*80)
    try:
        agency_scheme = service.get_agencyscheme_info()
        print("\nSchemat agencji:")
        print(json.dumps(agency_scheme, indent=2, ensure_ascii=False)[:500] + "...")
    except Exception as e:
        print(f"✗ Błąd podczas pobierania schematu agencji: {e}")
    
    if CONFIG_VERBOSE:
        print("\n" + "="*80)
        print("✓ Zakończono testy")
        print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

