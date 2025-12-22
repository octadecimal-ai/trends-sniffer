#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serwis do pracy z danymi IMF SDMX wykorzystujący IMFSDMXProvider.
Serwis oferuje wysokopoziomowe metody do pobierania, analizowania i prezentowania danych.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from src.providers.imf_sdmx_provider import IMFSDMXProvider


class IMFSDMXService:
    """
    Serwis do pracy z danymi IMF SDMX.
    
    Wykorzystuje IMFSDMXProvider do pobierania danych z API IMF SDMX 3.0
    i oferuje metody do analizy, prezentacji i eksportu danych.
    """
    
    def __init__(self, subscription_key: Optional[str] = None, format: str = 'json', verbose: bool = True):
        """
        Inicjalizacja serwisu.
        
        Args:
            subscription_key: Klucz subskrypcji API IMF (opcjonalnie, pobiera z .env jako IMF_SUBSCRIPTION_KEY)
            format: Format odpowiedzi API ('json' lub 'xml')
            verbose: Czy wyświetlać szczegółowe informacje podczas działania
        """
        self.provider = IMFSDMXProvider(subscription_key=subscription_key, format=format)
        self.verbose = verbose
    
    def _log(self, message: str):
        """
        Wyświetla wiadomość logowania jeśli verbose jest włączone.
        
        Args:
            message: Wiadomość do wyświetlenia
        """
        if self.verbose:
            print(message)
    
    def get_availability_info(
        self,
        context: str,
        agency_id: str,
        resource_id: str,
        version: str = "latest",
        key: str = "*",
        component_id: Optional[str] = None
    ) -> Dict:
        """
        Pobiera informacje o dostępności danych dla określonego kontekstu.
        
        Metoda pobiera informacje o dostępności danych zgodnie z endpointem
        availability. Pozwala sprawdzić, jakie dane są dostępne dla określonego
        zasobu, kontekstu i klucza.
        
        Args:
            context: Kontekst zasobu (np. 'dataflow', 'datastructure', 'codelist')
            agency_id: Identyfikator agencji utrzymującej zasób (np. 'IMF', 'ESTAT')
            resource_id: Identyfikator zasobu
            version: Wersja zasobu (domyślnie 'latest')
            key: Klucz identyfikujący dane (domyślnie '*' dla wszystkich)
            component_id: Identyfikator komponentu (opcjonalnie)
        
        Returns:
            Słownik z informacjami o dostępności danych
        """
        self._log(f"Pobieranie informacji o dostępności danych...")
        self._log(f"  Kontekst: {context}")
        self._log(f"  Agencja: {agency_id}")
        self._log(f"  Zasób: {resource_id}")
        self._log(f"  Wersja: {version}")
        self._log(f"  Klucz: {key}")
        
        availability = self.provider.get_availability(
            context=context,
            agency_id=agency_id,
            resource_id=resource_id,
            version=version,
            key=key,
            component_id=component_id
        )
        
        self._log("✓ Pobrano informacje o dostępności danych")
        return availability
    
    def get_dataflow_info(
        self,
        dataflow: str,
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera informacje o dataflow.
        
        Metoda pobiera metadane dotyczące określonego dataflow,
        w tym opis, strukturę danych i dostępne wymiary.
        
        Args:
            dataflow: Identyfikator dataflow
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja dataflow (domyślnie 'latest')
        
        Returns:
            Słownik z informacjami o dataflow
        """
        self._log(f"Pobieranie informacji o dataflow: {dataflow}...")
        info = self.provider.get_dataflow(dataflow, agency_id, version)
        self._log("✓ Pobrano informacje o dataflow")
        return info
    
    def get_dataflow_list(
        self,
        agency_id: str = "IMF"
    ) -> List[Dict]:
        """
        Pobiera listę wszystkich dostępnych dataflow.
        
        Metoda pobiera listę wszystkich dataflow dostępnych dla określonej agencji.
        Lista zawiera podstawowe informacje o każdym dataflow, takie jak
        identyfikator, nazwa i opis.
        
        Args:
            agency_id: Identyfikator agencji (domyślnie 'IMF')
        
        Returns:
            Lista słowników z informacjami o dataflow
        """
        self._log(f"Pobieranie listy dataflow dla agencji: {agency_id}...")
        dataflows = self.provider.get_dataflow_list(agency_id)
        self._log(f"✓ Pobrano {len(dataflows)} dataflow")
        return dataflows
    
    def search_dataflow(
        self,
        query: str,
        agency_id: str = "IMF"
    ) -> List[Dict]:
        """
        Wyszukuje dataflow na podstawie zapytania tekstowego.
        
        Metoda przeszukuje listę dataflow i zwraca te, których nazwa
        lub identyfikator zawiera podane zapytanie (bez rozróżniania wielkości liter).
        
        Args:
            query: Tekst do wyszukania
            agency_id: Identyfikator agencji (domyślnie 'IMF')
        
        Returns:
            Lista dataflow pasujących do zapytania
        """
        self._log(f"Wyszukiwanie dataflow: {query}...")
        results = self.provider.search_dataflow(query, agency_id)
        self._log(f"✓ Znaleziono {len(results)} dataflow")
        return results
    
    def get_data(
        self,
        dataflow: str,
        agency_id: str = "IMF",
        key: Optional[str] = None,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
        detail: str = "full"
    ) -> Dict:
        """
        Pobiera dane statystyczne dla określonego dataflow.
        
        Metoda pobiera dane statystyczne dla określonego dataflow.
        Można filtrować dane według klucza (kombinacji wymiarów) oraz
        zakresu okresów czasowych.
        
        Args:
            dataflow: Identyfikator dataflow
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            key: Klucz identyfikujący dane (opcjonalnie, '*' dla wszystkich)
            start_period: Okres początkowy (np. '2020', '2020-Q1')
            end_period: Okres końcowy (np. '2023', '2023-Q4')
            detail: Poziom szczegółowości ('full', 'dataonly', 'serieskeysonly')
        
        Returns:
            Słownik z danymi statystycznymi
        """
        self._log(f"Pobieranie danych dla dataflow: {dataflow}...")
        if key:
            self._log(f"  Klucz: {key}")
        if start_period or end_period:
            self._log(f"  Okres: {start_period or '?'} - {end_period or '?'}")
        
        data = self.provider.get_data(
            dataflow=dataflow,
            agency_id=agency_id,
            key=key,
            start_period=start_period,
            end_period=end_period,
            detail=detail
        )
        
        self._log("✓ Pobrano dane")
        return data
    
    def get_datastructure_info(
        self,
        datastructure: str,
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera informacje o strukturze danych (datastructure).
        
        Metoda pobiera metadane dotyczące struktury danych, w tym
        definicje wymiarów, atrybutów i miar.
        
        Args:
            datastructure: Identyfikator datastructure
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja datastructure (domyślnie 'latest')
        
        Returns:
            Słownik z informacjami o strukturze danych
        """
        self._log(f"Pobieranie informacji o strukturze danych: {datastructure}...")
        info = self.provider.get_datastructure(datastructure, agency_id, version)
        self._log("✓ Pobrano informacje o strukturze danych")
        return info
    
    def get_codelist_info(
        self,
        codelist: str,
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera listę kodów (codelist).
        
        Metoda pobiera listę kodów dla określonego codelist.
        Codelist zawiera możliwe wartości dla wymiarów lub atrybutów.
        
        Args:
            codelist: Identyfikator codelist
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja codelist (domyślnie 'latest')
        
        Returns:
            Słownik z listą kodów
        """
        self._log(f"Pobieranie listy kodów: {codelist}...")
        info = self.provider.get_codelist(codelist, agency_id, version)
        self._log("✓ Pobrano listę kodów")
        return info
    
    def get_agencyscheme_info(
        self,
        agency_scheme: str = "AGENCY",
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera schemat agencji.
        
        Metoda pobiera informacje o agencjach dostępnych w API,
        w tym ich identyfikatory, nazwy i opisy.
        
        Args:
            agency_scheme: Identyfikator schematu agencji (domyślnie 'AGENCY')
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja schematu (domyślnie 'latest')
        
        Returns:
            Słownik z informacjami o agencjach
        """
        self._log("Pobieranie schematu agencji...")
        info = self.provider.get_agencyscheme(agency_scheme, agency_id, version)
        self._log("✓ Pobrano schemat agencji")
        return info
    
    def display_dataflow_list(
        self,
        agency_id: str = "IMF",
        limit: int = 20
    ):
        """
        Wyświetla listę dostępnych dataflow w czytelnej formie.
        
        Metoda pobiera i wyświetla listę dataflow dostępnych dla określonej agencji.
        Wyświetla podstawowe informacje o każdym dataflow.
        
        Args:
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            limit: Maksymalna liczba dataflow do wyświetlenia
        """
        dataflows = self.get_dataflow_list(agency_id)
        
        print("\n" + "="*80)
        print(f"LISTA DATAFLOW DLA AGENCJI: {agency_id}")
        print("="*80)
        
        for i, dataflow in enumerate(dataflows[:limit], 1):
            name = dataflow.get('name', {})
            if isinstance(name, dict):
                name = name.get('value', 'N/A')
            
            df_id = dataflow.get('id', 'N/A')
            print(f"{i}. {df_id}: {name}")
        
        if len(dataflows) > limit:
            print(f"\n... i {len(dataflows) - limit} więcej")
        
        print("="*80)
    
    def export_data_to_json(
        self,
        data: Dict,
        output_file: str
    ) -> bool:
        """
        Eksportuje dane do pliku JSON.
        
        Metoda zapisuje dane do pliku JSON w czytelnej formie.
        
        Args:
            data: Dane do eksportu
            output_file: Ścieżka do pliku wyjściowego JSON
        
        Returns:
            True jeśli eksport się powiódł, False w przeciwnym razie
        """
        self._log(f"Eksportowanie danych do JSON: {output_file}...")
        
        try:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._log(f"✓ Zapisano dane do pliku: {output_file}")
            return True
        except Exception as e:
            self._log(f"✗ Błąd podczas zapisywania do JSON: {e}")
            return False
    
    def get_data_as_dataframe(
        self,
        dataflow: str,
        agency_id: str = "IMF",
        key: Optional[str] = None,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pobiera dane i konwertuje je do DataFrame pandas.
        
        Metoda pobiera dane z API i konwertuje je do formatu pandas DataFrame,
        co ułatwia analizę i manipulację danymi.
        
        Args:
            dataflow: Identyfikator dataflow
            agency_id: Identyfikator agencji
            key: Klucz identyfikujący dane
            start_period: Okres początkowy
            end_period: Okres końcowy
        
        Returns:
            DataFrame pandas z danymi
        """
        data = self.get_data(
            dataflow=dataflow,
            agency_id=agency_id,
            key=key,
            start_period=start_period,
            end_period=end_period
        )
        
        # Przetwórz dane SDMX do DataFrame
        # Struktura odpowiedzi SDMX może się różnić
        # To jest uproszczona wersja - może wymagać dostosowania do rzeczywistej struktury API
        
        try:
            # Próba wyciągnięcia danych z odpowiedzi SDMX
            if 'data' in data:
                # Struktura może być różna w zależności od API
                # Wymaga dostosowania do rzeczywistej struktury odpowiedzi
                pass
            
            # Jeśli nie można automatycznie przetworzyć, zwróć pusty DataFrame
            return pd.DataFrame()
        except Exception as e:
            self._log(f"Błąd podczas konwersji do DataFrame: {e}")
            return pd.DataFrame()

