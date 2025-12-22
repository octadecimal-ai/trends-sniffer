#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Provider do komunikacji z API SDMX 3.0 IMF (International Monetary Fund).
IMF SDMX API dostarcza dane statystyczne ekonomiczne i finansowe.
"""

import requests
import json
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode


class IMFSDMXProvider:
    """
    Provider do komunikacji z API SDMX 3.0 IMF.
    
    API IMF SDMX 3.0 oferuje dostęp do danych statystycznych ekonomicznych
    i finansowych Międzynarodowego Funduszu Walutowego.
    API wymaga rejestracji i klucza API (subscription key).
    """
    
    BASE_URL = "https://api.imf.org/rest"
    
    def __init__(self, subscription_key: Optional[str] = None, format: str = 'json'):
        """
        Inicjalizacja providera.
        
        Args:
            subscription_key: Klucz subskrypcji API IMF (opcjonalnie, można ustawić w .env jako IMF_SUBSCRIPTION_KEY)
            format: Format odpowiedzi API ('json' lub 'xml')
        
        Raises:
            ValueError: Jeśli subscription_key nie jest podane
        """
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        if subscription_key is None:
            subscription_key = os.getenv('IMF_SUBSCRIPTION_KEY')
        
        if not subscription_key:
            raise ValueError(
                "Klucz subskrypcji IMF nie został znaleziony. "
                "Ustaw zmienną IMF_SUBSCRIPTION_KEY w pliku .env lub podaj subscription_key bezpośrednio."
            )
        
        self.subscription_key = subscription_key
        self.format = format
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TrendsSniffer/1.0',
            'Accept': 'application/json' if format == 'json' else 'application/xml',
            'Subscription-Key': self.subscription_key
        })
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Union[Dict, str]:
        """
        Wykonuje zapytanie do API IMF SDMX 3.0.
        
        Args:
            endpoint: Endpoint API (np. 'availability/dataflow/IMF/...')
            params: Parametry zapytania
        
        Returns:
            Odpowiedź API w formacie JSON (dict) lub XML (str)
        
        Raises:
            requests.RequestException: W przypadku błędu zapytania HTTP
        """
        if params is None:
            params = {}
        
        # Dodaj format jeśli nie jest w endpoint
        if 'format' not in endpoint.lower():
            params['format'] = self.format
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            if self.format == 'json':
                return response.json()
            else:
                return response.text
        
        except requests.RequestException as e:
            raise requests.RequestException(f"Błąd podczas komunikacji z API IMF SDMX: {e}")
    
    def get_availability(
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
        
        Metoda pobiera informacje o dostępności danych zgodnie z endpointem:
        /availability/{context}/{agencyid}/{resourceid}/{version}/{key}/{componentid}
        
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
        endpoint = f"availability/{context}/{agency_id}/{resource_id}/{version}/{key}"
        
        if component_id:
            endpoint += f"/{component_id}"
        
        return self._make_request(endpoint)
    
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
        Pobiera dane dla określonego dataflow.
        
        Metoda pobiera dane statystyczne dla określonego dataflow.
        
        Args:
            dataflow: Identyfikator dataflow
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            key: Klucz identyfikujący dane (opcjonalnie, '*' dla wszystkich)
            start_period: Okres początkowy (np. '2020')
            end_period: Okres końcowy (np. '2023')
            detail: Poziom szczegółowości ('full', 'dataonly', 'serieskeysonly')
        
        Returns:
            Słownik z danymi statystycznymi
        """
        endpoint = f"data/{dataflow}/{agency_id}"
        
        params = {
            'detail': detail
        }
        
        if key:
            endpoint += f"/{key}"
        
        if start_period:
            params['startPeriod'] = start_period
        
        if end_period:
            params['endPeriod'] = end_period
        
        return self._make_request(endpoint, params)
    
    def get_dataflow(
        self,
        dataflow: str,
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera informacje o dataflow.
        
        Metoda pobiera metadane dotyczące określonego dataflow.
        
        Args:
            dataflow: Identyfikator dataflow
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja dataflow (domyślnie 'latest')
        
        Returns:
            Słownik z informacjami o dataflow
        """
        endpoint = f"dataflow/{dataflow}/{agency_id}"
        
        if version != "latest":
            endpoint += f"/{version}"
        
        return self._make_request(endpoint)
    
    def get_datastructure(
        self,
        datastructure: str,
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera informacje o strukturze danych (datastructure).
        
        Metoda pobiera metadane dotyczące struktury danych.
        
        Args:
            datastructure: Identyfikator datastructure
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja datastructure (domyślnie 'latest')
        
        Returns:
            Słownik z informacjami o strukturze danych
        """
        endpoint = f"datastructure/{datastructure}/{agency_id}"
        
        if version != "latest":
            endpoint += f"/{version}"
        
        return self._make_request(endpoint)
    
    def get_codelist(
        self,
        codelist: str,
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera listę kodów (codelist).
        
        Metoda pobiera listę kodów dla określonego codelist.
        
        Args:
            codelist: Identyfikator codelist
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja codelist (domyślnie 'latest')
        
        Returns:
            Słownik z listą kodów
        """
        endpoint = f"codelist/{codelist}/{agency_id}"
        
        if version != "latest":
            endpoint += f"/{version}"
        
        return self._make_request(endpoint)
    
    def get_agencyscheme(
        self,
        agency_scheme: str = "AGENCY",
        agency_id: str = "IMF",
        version: str = "latest"
    ) -> Dict:
        """
        Pobiera schemat agencji.
        
        Metoda pobiera informacje o agencjach dostępnych w API.
        
        Args:
            agency_scheme: Identyfikator schematu agencji (domyślnie 'AGENCY')
            agency_id: Identyfikator agencji (domyślnie 'IMF')
            version: Wersja schematu (domyślnie 'latest')
        
        Returns:
            Słownik z informacjami o agencjach
        """
        endpoint = f"agencyscheme/{agency_scheme}/{agency_id}"
        
        if version != "latest":
            endpoint += f"/{version}"
        
        return self._make_request(endpoint)
    
    def get_dataflow_list(
        self,
        agency_id: str = "IMF"
    ) -> List[Dict]:
        """
        Pobiera listę wszystkich dostępnych dataflow.
        
        Metoda pobiera listę wszystkich dataflow dostępnych dla określonej agencji.
        
        Args:
            agency_id: Identyfikator agencji (domyślnie 'IMF')
        
        Returns:
            Lista słowników z informacjami o dataflow
        """
        endpoint = f"dataflow/{agency_id}"
        response = self._make_request(endpoint)
        
        # Przetwórz odpowiedź w zależności od formatu
        if isinstance(response, dict):
            # Struktura może się różnić w zależności od API
            if 'dataflows' in response:
                return response['dataflows']
            elif 'structure' in response and 'dataflows' in response['structure']:
                return response['structure']['dataflows']
        
        return []
    
    def search_dataflow(
        self,
        query: str,
        agency_id: str = "IMF"
    ) -> List[Dict]:
        """
        Wyszukuje dataflow na podstawie zapytania tekstowego.
        
        Metoda przeszukuje listę dataflow i zwraca te, które pasują do zapytania.
        
        Args:
            query: Tekst do wyszukania
            agency_id: Identyfikator agencji (domyślnie 'IMF')
        
        Returns:
            Lista dataflow pasujących do zapytania
        """
        all_dataflows = self.get_dataflow_list(agency_id)
        query_lower = query.lower()
        
        results = []
        for dataflow in all_dataflows:
            name = dataflow.get('name', {}).get('value', '').lower() if isinstance(dataflow.get('name'), dict) else str(dataflow.get('name', '')).lower()
            id_value = dataflow.get('id', '').lower()
            
            if query_lower in name or query_lower in id_value:
                results.append(dataflow)
        
        return results

