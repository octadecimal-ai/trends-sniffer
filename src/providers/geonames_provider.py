#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Provider do komunikacji z API Geonames (http://api.geonames.org).
Geonames to bezpłatne API geograficzne dostarczające informacje o krajach, regionach, miastach itp.
"""

import os
import requests
import json
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()


class GeonamesProvider:
    """
    Provider do komunikacji z API Geonames.
    
    Wymaga rejestracji na http://www.geonames.org/login (darmowe).
    Username jest pobierany z pliku .env (zmienna GEONAMES_LOGIN) lub można podać bezpośrednio.
    """
    
    BASE_URL = "http://api.geonames.org"
    
    def __init__(self, username: Optional[str] = None):
        """
        Inicjalizacja providera.
        
        Args:
            username: Nazwa użytkownika Geonames (opcjonalne, jeśli None, pobiera z .env jako GEONAMES_LOGIN)
        
        Raises:
            ValueError: Jeśli username nie jest podane i nie ma w .env
        """
        if username is None:
            username = os.getenv('GEONAMES_LOGIN')
            if not username:
                raise ValueError(
                    "Username Geonames nie został znaleziony. "
                    "Ustaw zmienną GEONAMES_LOGIN w pliku .env lub podaj username bezpośrednio w konstruktorze."
                )
        
        self.username = username
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TrendsSniffer/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Dict, format: str = 'JSON') -> Union[Dict, str]:
        """
        Wykonuje zapytanie do API Geonames.
        
        Args:
            endpoint: Endpoint API (np. 'search', 'countryInfo')
            params: Parametry zapytania
            format: Format odpowiedzi ('JSON' lub 'XML')
        
        Returns:
            Odpowiedź z API w formacie JSON (dict) lub XML (str)
        """
        params['username'] = self.username
        params['type'] = format.lower()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            if format.upper() == 'JSON':
                return response.json()
            else:
                return response.text
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Błąd podczas komunikacji z API Geonames: {e}")
    
    def search(self, 
               q: Optional[str] = None,
               name: Optional[str] = None,
               name_equals: Optional[str] = None,
               country: Optional[str] = None,
               continent_code: Optional[str] = None,
               feature_class: Optional[str] = None,
               feature_code: Optional[str] = None,
               max_rows: int = 10,
               start_row: int = 0,
               lang: str = 'pl') -> List[Dict]:
        """
        Wyszukuje miejsca na podstawie różnych kryteriów.
        
        Args:
            q: Ogólne zapytanie wyszukiwania
            name: Nazwa miejsca
            name_equals: Dokładna nazwa miejsca
            country: Kod kraju (ISO 3166-1 alpha-2)
            continent_code: Kod kontynentu (AF, AS, EU, NA, OC, SA, AN)
            feature_class: Klasa obiektu (P=miasto, A=region administracyjny, S=punkt, T=góra, U=podwodny, V=las, H=woda, L=ląd)
            feature_code: Kod obiektu (np. PPLC=stolica, PPL=miasto, ADM1=województwo)
            max_rows: Maksymalna liczba wyników (domyślnie 10, maksymalnie 1000)
            start_row: Numer pierwszego wyniku (dla paginacji)
            lang: Język odpowiedzi ('pl', 'en', 'de', itp.)
        
        Returns:
            Lista słowników z informacjami o miejscach
        """
        params = {
            'maxRows': max_rows,
            'startRow': start_row,
            'lang': lang
        }
        
        if q:
            params['q'] = q
        if name:
            params['name'] = name
        if name_equals:
            params['name_equals'] = name_equals
        if country:
            params['country'] = country.upper()
        if continent_code:
            params['continentCode'] = continent_code.upper()
        if feature_class:
            params['featureClass'] = feature_class.upper()
        if feature_code:
            params['featureCode'] = feature_code
        
        result = self._make_request('search', params, 'JSON')
        
        if 'geonames' in result:
            return result['geonames']
        return []
    
    def get_country_info(self, country_code: Optional[str] = None, lang: str = 'pl') -> Union[Dict, List[Dict]]:
        """
        Pobiera informacje o kraju/krajach.
        
        Args:
            country_code: Kod kraju (ISO 3166-1 alpha-2), None dla wszystkich krajów
            lang: Język odpowiedzi
        
        Returns:
            Słownik z informacjami o kraju lub lista wszystkich krajów
        """
        params = {'lang': lang}
        
        if country_code:
            params['country'] = country_code.upper()
        
        result = self._make_request('countryInfo', params, 'JSON')
        
        if 'geonames' in result:
            if country_code:
                return result['geonames'][0] if result['geonames'] else {}
            return result['geonames']
        return []
    
    def get_children(self, geoname_id: int, lang: str = 'pl') -> List[Dict]:
        """
        Pobiera dzieci (podrzędne jednostki) dla danego miejsca.
        
        Args:
            geoname_id: ID miejsca w Geonames
            lang: Język odpowiedzi
        
        Returns:
            Lista miejsc podrzędnych
        """
        params = {
            'geonameId': geoname_id,
            'lang': lang
        }
        
        result = self._make_request('children', params, 'JSON')
        
        if 'geonames' in result:
            return result['geonames']
        return []
    
    def get_hierarchy(self, geoname_id: int, lang: str = 'pl') -> List[Dict]:
        """
        Pobiera hierarchię miejsc (kraj -> region -> miasto).
        
        Args:
            geoname_id: ID miejsca w Geonames
            lang: Język odpowiedzi
        
        Returns:
            Lista miejsc w hierarchii (od najwyższego do najniższego poziomu)
        """
        params = {
            'geonameId': geoname_id,
            'lang': lang
        }
        
        result = self._make_request('hierarchy', params, 'JSON')
        
        if 'geonames' in result:
            return result['geonames']
        return []
    
    def get_nearby_places(self, 
                         lat: float,
                         lng: float,
                         feature_class: Optional[str] = None,
                         radius_km: float = 10.0,
                         max_rows: int = 10,
                         lang: str = 'pl') -> List[Dict]:
        """
        Pobiera miejsca w pobliżu danej lokalizacji.
        
        Args:
            lat: Szerokość geograficzna
            lng: Długość geograficzna
            feature_class: Klasa obiektu (P=miasto, A=region, itp.)
            radius_km: Promień wyszukiwania w kilometrach
            max_rows: Maksymalna liczba wyników
            lang: Język odpowiedzi
        
        Returns:
            Lista miejsc w pobliżu
        """
        params = {
            'lat': lat,
            'lng': lng,
            'radius': radius_km,
            'maxRows': max_rows,
            'lang': lang
        }
        
        if feature_class:
            params['featureClass'] = feature_class.upper()
        
        result = self._make_request('findNearby', params, 'JSON')
        
        if 'geonames' in result:
            return result['geonames']
        return []
    
    def get_timezone(self, lat: float, lng: float) -> Dict:
        """
        Pobiera informacje o strefie czasowej dla danej lokalizacji.
        
        Args:
            lat: Szerokość geograficzna
            lng: Długość geograficzna
        
        Returns:
            Słownik z informacjami o strefie czasowej
        """
        params = {
            'lat': lat,
            'lng': lng,
            'username': self.username
        }
        
        url = f"{self.BASE_URL}/timezoneJSON"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Sprawdź czy odpowiedź nie jest pusta
            if not response.text or response.text.strip() == '':
                raise Exception("Pusta odpowiedź z API Geonames")
            
            result = response.json()
            
            # Sprawdź czy jest błąd w odpowiedzi
            if 'status' in result and 'message' in result:
                raise Exception(f"Błąd API Geonames: {result['message']}")
            
            return result
        except requests.exceptions.RequestException as e:
            raise Exception(f"Błąd podczas komunikacji z API Geonames: {e}")
        except ValueError as e:
            raise Exception(f"Błąd parsowania JSON z API Geonames: {e}")
    
    def get_postal_code_info(self, 
                            postal_code: str,
                            country: str,
                            max_rows: int = 10) -> List[Dict]:
        """
        Pobiera informacje o kodzie pocztowym.
        
        Args:
            postal_code: Kod pocztowy
            country: Kod kraju (ISO 3166-1 alpha-2)
            max_rows: Maksymalna liczba wyników
        
        Returns:
            Lista miejsc z danym kodem pocztowym
        """
        params = {
            'postalcode': postal_code,
            'country': country.upper(),
            'maxRows': max_rows
        }
        
        result = self._make_request('postalCodeSearch', params, 'JSON')
        
        if 'postalCodes' in result:
            return result['postalCodes']
        return []
    
    def search_cities(self, 
                     city_name: str,
                     country: Optional[str] = None,
                     max_rows: int = 10,
                     lang: str = 'pl') -> List[Dict]:
        """
        Wyszukuje miasta.
        
        Args:
            city_name: Nazwa miasta
            country: Kod kraju (opcjonalnie)
            max_rows: Maksymalna liczba wyników
            lang: Język odpowiedzi
        
        Returns:
            Lista miast
        """
        return self.search(
            name_equals=city_name,
            feature_class='P',  # P = miasto/wsie
            country=country,
            max_rows=max_rows,
            lang=lang
        )
    
    def get_regions(self, 
                   country: str,
                   feature_code: str = 'ADM1',
                   lang: str = 'pl') -> List[Dict]:
        """
        Pobiera regiony administracyjne (województwa, stany) dla danego kraju.
        
        Args:
            country: Kod kraju (ISO 3166-1 alpha-2)
            feature_code: Kod obiektu (ADM1=województwo/stan, ADM2=powiat, ADM3=gmina)
            lang: Język odpowiedzi
        
        Returns:
            Lista regionów
        """
        params = {
            'country': country.upper(),
            'featureCode': feature_code,
            'maxRows': 1000,
            'lang': lang
        }
        
        result = self._make_request('search', params, 'JSON')
        
        if 'geonames' in result:
            return result['geonames']
        return []
    
    def get_capital(self, country: str, lang: str = 'pl') -> Optional[Dict]:
        """
        Pobiera stolicę danego kraju.
        
        Args:
            country: Kod kraju (ISO 3166-1 alpha-2)
            lang: Język odpowiedzi
        
        Returns:
            Słownik z informacjami o stolicy lub None
        """
        cities = self.search(
            country=country,
            feature_code='PPLC',  # PPLC = stolica
            max_rows=1,
            lang=lang
        )
        
        return cities[0] if cities else None
    
    def search_by_bounding_box(self,
                               north: float,
                               south: float,
                               east: float,
                               west: float,
                               feature_class: Optional[str] = None,
                               feature_code: Optional[str] = None,
                               max_rows: int = 10,
                               lang: str = 'pl') -> List[Dict]:
        """
        Wyszukuje miejsca w określonym bounding box (obszarze geograficznym).
        
        Args:
            north: Szerokość geograficzna północnej granicy
            south: Szerokość geograficzna południowej granicy
            east: Długość geograficzna wschodniej granicy
            west: Długość geograficzna zachodniej granicy
            feature_class: Klasa obiektu (P=miasto, A=region, S=punkt, T=góra, itp.)
            feature_code: Kod obiektu (np. PPLC=stolica, PPL=miasto, ADM1=województwo)
            max_rows: Maksymalna liczba wyników (domyślnie 10, maksymalnie 1000)
            lang: Język odpowiedzi ('pl', 'en', 'de', itp.)
        
        Returns:
            Lista słowników z informacjami o miejscach w bounding box
        """
        params = {
            'north': north,
            'south': south,
            'east': east,
            'west': west,
            'maxRows': max_rows,
            'lang': lang
        }
        
        if feature_class:
            params['featureClass'] = feature_class.upper()
        if feature_code:
            params['featureCode'] = feature_code
        
        result = self._make_request('search', params, 'JSON')
        
        if 'geonames' in result:
            return result['geonames']
        return []
    
    def get_cities_in_bounding_box(self,
                                   north: float,
                                   south: float,
                                   east: float,
                                   west: float,
                                   max_rows: int = 10) -> List[Dict]:
        """
        Pobiera miasta w określonym bounding box używając endpointu citiesJSON.
        
        Args:
            north: Szerokość geograficzna północnej granicy
            south: Szerokość geograficzna południowej granicy
            east: Długość geograficzna wschodniej granicy
            west: Długość geograficzna zachodniej granicy
            max_rows: Maksymalna liczba wyników
        
        Returns:
            Lista słowników z informacjami o miastach
        """
        params = {
            'north': north,
            'south': south,
            'east': east,
            'west': west,
            'username': self.username,
            'maxRows': max_rows
        }
        
        url = f"{self.BASE_URL}/citiesJSON"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # citiesJSON zwraca listę w kluczu 'geonames'
            if 'geonames' in result:
                return result['geonames']
            return []
        except requests.exceptions.RequestException as e:
            raise Exception(f"Błąd podczas komunikacji z API Geonames: {e}")


if __name__ == "__main__":
    # Przykłady użycia
    print("=== Przykłady użycia GeonamesProvider ===\n")
    print("UWAGA: Wymagana jest rejestracja na http://www.geonames.org/login")
    print("Po rejestracji ustaw zmienną GEONAMES_LOGIN w pliku .env\n")
    
    # Przykład użycia (username pobierany z .env)
    try:
        provider = GeonamesProvider()  # Username pobierany z .env (GEONAMES_LOGIN)
        print(f"✓ Provider utworzony z username: {provider.username}")
        
        # # Wyszukaj miasto
        # print("=== Wyszukiwanie miasta: Warszawa ===")
        # cities = provider.search_cities('Warsaw', country='PL')
        # for city in cities[:3]:
        #     print(f"{city.get('name', 'N/A')}: {city.get('adminName1', 'N/A')}")
        
        # # Pobierz informacje o kraju
        # print("\n=== Informacje o kraju: PL ===")
        # country_info = provider.get_country_info('PL')
        # print(f"Kraj: {country_info.get('countryName', 'N/A')}")
        # print(f"Stolica: {country_info.get('capital', 'N/A')}")
        # print(f"Populacja: {country_info.get('population', 'N/A')}")
        
        # # Pobierz województwa Polski
        # print("\n=== Województwa Polski ===")
        # regions = provider.get_regions('PL', feature_code='ADM1')
        # for region in regions[:5]:
        #     print(f"{region.get('name', 'N/A')}: {region.get('geonameId', 'N/A')}")
    
    except ValueError as e:
        print(f"Błąd: {e}")
        print("\nAby użyć providera, ustaw zmienną GEONAMES_LOGIN w pliku .env")
        print("lub podaj username bezpośrednio:")
        print("provider = GeonamesProvider(username='twoj_username')")
    
    print("\nDokumentacja API: http://www.geonames.org/export/web-services.html")

