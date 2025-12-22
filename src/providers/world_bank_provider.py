#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Provider do komunikacji z API World Bank (https://api.worldbank.org/).
World Bank API dostarcza dane statystyczne o krajach, wskaźnikach ekonomicznych i społecznych.
"""

import requests
import json
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode


class WorldBankProvider:
    """
    Provider do komunikacji z API World Bank.
    
    API World Bank oferuje dostęp do danych statystycznych o krajach,
    wskaźnikach ekonomicznych, społecznych i innych metrykach.
    API jest bezpłatne i nie wymaga autoryzacji.
    """
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    def __init__(self, format: str = 'json', per_page: int = 50):
        """
        Inicjalizacja providera.
        
        Args:
            format: Format odpowiedzi API ('json' lub 'xml')
            per_page: Liczba wyników na stronę (domyślnie 50, maksymalnie 10000)
        """
        self.format = format
        self.per_page = min(per_page, 10000)  # Maksymalnie 10000 wyników na stronę
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TrendsSniffer/1.0',
            'Accept': 'application/json' if format == 'json' else 'application/xml'
        })
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page: int = 1
    ) -> Union[Dict, str]:
        """
        Wykonuje zapytanie do API World Bank.
        
        Args:
            endpoint: Endpoint API (np. 'country', 'indicator')
            params: Parametry zapytania
            page: Numer strony (domyślnie 1)
        
        Returns:
            Odpowiedź API w formacie JSON (dict) lub XML (str)
        
        Raises:
            requests.RequestException: W przypadku błędu zapytania HTTP
        """
        if params is None:
            params = {}
        
        # Dodaj standardowe parametry
        params['format'] = self.format
        params['per_page'] = self.per_page
        params['page'] = page
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            if self.format == 'json':
                return response.json()
            else:
                return response.text
        
        except requests.RequestException as e:
            raise requests.RequestException(f"Błąd podczas komunikacji z API World Bank: {e}")
    
    def _get_all_pages(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Pobiera wszystkie strony wyników z API.
        
        Args:
            endpoint: Endpoint API
            params: Parametry zapytania
        
        Returns:
            Lista wszystkich wyników ze wszystkich stron
        """
        all_results = []
        page = 1
        
        while True:
            response = self._make_request(endpoint, params, page)
            
            if self.format == 'json':
                if isinstance(response, list) and len(response) >= 2:
                    metadata = response[0]
                    data = response[1]
                    
                    all_results.extend(data)
                    
                    # Sprawdź czy są kolejne strony
                    total_pages = metadata.get('pages', 1)
                    if page >= total_pages:
                        break
                    
                    page += 1
                else:
                    break
            else:
                # Dla XML trzeba by parsować inaczej
                break
        
        return all_results
    
    def get_countries(
        self,
        region: Optional[str] = None,
        income_level: Optional[str] = None,
        lending_type: Optional[str] = None,
        country_code: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera listę krajów dostępnych w API World Bank.
        
        Args:
            region: Kod regionu (np. 'EAS' dla East Asia & Pacific)
            income_level: Poziom dochodów (np. 'HIC' dla High income)
            lending_type: Typ pożyczek (np. 'IBD' dla IBRD)
            country_code: Kod kraju ISO 3 (np. 'POL' dla Polski)
        
        Returns:
            Lista słowników zawierających informacje o krajach
        """
        params = {}
        
        if region:
            params['region'] = region
        if income_level:
            params['incomeLevel'] = income_level
        if lending_type:
            params['lendingType'] = lending_type
        
        if country_code:
            # Pobierz konkretny kraj
            endpoint = f"country/{country_code}"
            response = self._make_request(endpoint, params)
            if self.format == 'json' and isinstance(response, list) and len(response) >= 2:
                return response[1]
            return []
        else:
            # Pobierz wszystkie kraje
            return self._get_all_pages('country', params)
    
    def get_country_info(self, country_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym kraju.
        
        Args:
            country_code: Kod kraju ISO 3 (np. 'POL' dla Polski)
        
        Returns:
            Słownik z informacjami o kraju lub None jeśli nie znaleziono
        """
        countries = self.get_countries(country_code=country_code)
        return countries[0] if countries else None
    
    def get_indicators(
        self,
        indicator_code: Optional[str] = None,
        source: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera listę wskaźników dostępnych w API World Bank.
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
            source: Kod źródła danych
            topic: Kod tematu
        
        Returns:
            Lista słowników zawierających informacje o wskaźnikach
        """
        params = {}
        
        if source:
            params['source'] = source
        if topic:
            params['topic'] = topic
        
        if indicator_code:
            # Pobierz konkretny wskaźnik
            endpoint = f"indicator/{indicator_code}"
            response = self._make_request(endpoint, params)
            if self.format == 'json' and isinstance(response, list) and len(response) >= 2:
                return response[1]
            return []
        else:
            # Pobierz wszystkie wskaźniki
            return self._get_all_pages('indicator', params)
    
    def get_indicator_info(self, indicator_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym wskaźniku.
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
        
        Returns:
            Słownik z informacjami o wskaźniku lub None jeśli nie znaleziono
        """
        indicators = self.get_indicators(indicator_code=indicator_code)
        return indicators[0] if indicators else None
    
    def get_data(
        self,
        indicator_code: str,
        country_codes: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        date: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera dane dla określonego wskaźnika i krajów.
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
            country_codes: Kod kraju ISO 3 lub lista kodów (np. 'POL' lub ['POL', 'USA'])
                          Jeśli None, pobiera dane dla wszystkich krajów
            start_year: Rok początkowy zakresu danych
            end_year: Rok końcowy zakresu danych
            date: Zakres dat w formacie 'YYYY:YYYY' (alternatywa dla start_year/end_year)
        
        Returns:
            Lista słowników zawierających dane dla danego wskaźnika i krajów
        """
        if country_codes is None:
            country_codes = 'all'
        elif isinstance(country_codes, list):
            country_codes = ';'.join(country_codes)
        
        endpoint = f"country/{country_codes}/indicator/{indicator_code}"
        
        params = {}
        
        if date:
            params['date'] = date
        elif start_year is not None or end_year is not None:
            if start_year is None:
                start_year = 1960  # Domyślny początek
            if end_year is None:
                end_year = 2024  # Domyślny koniec
            params['date'] = f"{start_year}:{end_year}"
        
        return self._get_all_pages(endpoint, params)
    
    def get_regions(self) -> List[Dict]:
        """
        Pobiera listę regionów dostępnych w API World Bank.
        
        Returns:
            Lista słowników zawierających informacje o regionach
        """
        return self._get_all_pages('region')
    
    def get_region_info(self, region_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym regionie.
        
        Args:
            region_code: Kod regionu (np. 'EAS' dla East Asia & Pacific)
        
        Returns:
            Słownik z informacjami o regionie lub None jeśli nie znaleziono
        """
        regions = self.get_regions()
        for region in regions:
            if region.get('code') == region_code:
                return region
        return None
    
    def get_topics(self) -> List[Dict]:
        """
        Pobiera listę tematów dostępnych w API World Bank.
        
        Returns:
            Lista słowników zawierających informacje o tematach
        """
        return self._get_all_pages('topic')
    
    def get_topic_info(self, topic_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym temacie.
        
        Args:
            topic_code: Kod tematu
        
        Returns:
            Słownik z informacjami o temacie lub None jeśli nie znaleziono
        """
        topics = self.get_topics()
        for topic in topics:
            if topic.get('id') == topic_code:
                return topic
        return None
    
    def get_sources(self) -> List[Dict]:
        """
        Pobiera listę źródeł danych dostępnych w API World Bank.
        
        Returns:
            Lista słowników zawierających informacje o źródłach danych
        """
        return self._get_all_pages('source')
    
    def get_source_info(self, source_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym źródle danych.
        
        Args:
            source_code: Kod źródła danych
        
        Returns:
            Słownik z informacjami o źródle lub None jeśli nie znaleziono
        """
        sources = self.get_sources()
        for source in sources:
            if source.get('id') == source_code:
                return source
        return None
    
    def get_income_levels(self) -> List[Dict]:
        """
        Pobiera listę poziomów dochodów dostępnych w API World Bank.
        
        Returns:
            Lista słowników zawierających informacje o poziomach dochodów
        """
        return self._get_all_pages('incomeLevel')
    
    def get_lending_types(self) -> List[Dict]:
        """
        Pobiera listę typów pożyczek dostępnych w API World Bank.
        
        Returns:
            Lista słowników zawierających informacje o typach pożyczek
        """
        return self._get_all_pages('lendingType')
    
    def search_countries(self, query: str) -> List[Dict]:
        """
        Wyszukuje kraje na podstawie zapytania tekstowego.
        
        Args:
            query: Tekst do wyszukania (nazwa kraju, kod ISO, itp.)
        
        Returns:
            Lista krajów pasujących do zapytania
        """
        all_countries = self.get_countries()
        query_lower = query.lower()
        
        results = []
        for country in all_countries:
            name = country.get('name', '').lower()
            code = country.get('iso2Code', '').lower()
            iso3_code = country.get('id', '').lower()
            
            if query_lower in name or query_lower in code or query_lower in iso3_code:
                results.append(country)
        
        return results
    
    def search_indicators(self, query: str) -> List[Dict]:
        """
        Wyszukuje wskaźniki na podstawie zapytania tekstowego.
        
        Args:
            query: Tekst do wyszukania (nazwa wskaźnika, kod, itp.)
        
        Returns:
            Lista wskaźników pasujących do zapytania
        """
        all_indicators = self.get_indicators()
        query_lower = query.lower()
        
        results = []
        for indicator in all_indicators:
            name = indicator.get('name', '').lower()
            code = indicator.get('id', '').lower()
            
            if query_lower in name or query_lower in code:
                results.append(indicator)
        
        return results

