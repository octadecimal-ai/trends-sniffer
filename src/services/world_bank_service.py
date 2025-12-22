#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serwis do pracy z danymi World Bank wykorzystujący WorldBankProvider.
Serwis oferuje wysokopoziomowe metody do pobierania, analizowania i prezentowania danych.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from src.providers.world_bank_provider import WorldBankProvider


class WorldBankService:
    """
    Serwis do pracy z danymi World Bank.
    
    Wykorzystuje WorldBankProvider do pobierania danych z API World Bank
    i oferuje metody do analizy, prezentacji i eksportu danych.
    """
    
    def __init__(self, format: str = 'json', per_page: int = 50, verbose: bool = True):
        """
        Inicjalizacja serwisu.
        
        Args:
            format: Format odpowiedzi API ('json' lub 'xml')
            per_page: Liczba wyników na stronę (domyślnie 50, maksymalnie 10000)
            verbose: Czy wyświetlać szczegółowe informacje podczas działania
        """
        self.provider = WorldBankProvider(format=format, per_page=per_page)
        self.verbose = verbose
    
    def _log(self, message: str):
        """
        Wyświetla wiadomość logowania jeśli verbose jest włączone.
        
        Args:
            message: Wiadomość do wyświetlenia
        """
        if self.verbose:
            print(message)
    
    def get_countries_list(
        self,
        region: Optional[str] = None,
        income_level: Optional[str] = None,
        lending_type: Optional[str] = None,
        country_code: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera listę krajów z API World Bank.
        
        Metoda pobiera informacje o krajach dostępnych w bazie danych World Bank.
        Można filtrować kraje według regionu, poziomu dochodów, typu pożyczek
        lub pobrać informacje o konkretnym kraju.
        
        Args:
            region: Kod regionu (np. 'EAS' dla East Asia & Pacific)
            income_level: Poziom dochodów (np. 'HIC' dla High income)
            lending_type: Typ pożyczek (np. 'IBD' dla IBRD)
            country_code: Kod kraju ISO 3 (np. 'POL' dla Polski)
        
        Returns:
            Lista słowników zawierających informacje o krajach
        """
        self._log("Pobieranie listy krajów z API World Bank...")
        countries = self.provider.get_countries(
            region=region,
            income_level=income_level,
            lending_type=lending_type,
            country_code=country_code
        )
        self._log(f"✓ Pobrano {len(countries)} krajów")
        return countries
    
    def get_country_details(self, country_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym kraju.
        
        Metoda pobiera pełne informacje o kraju, w tym:
        - Nazwę kraju
        - Kod ISO 2 i ISO 3
        - Region
        - Poziom dochodów
        - Typ pożyczek
        - Kapitał
        - Długość geograficzną i szerokość geograficzną
        
        Args:
            country_code: Kod kraju ISO 3 (np. 'POL' dla Polski, 'USA' dla Stanów Zjednoczonych)
        
        Returns:
            Słownik z informacjami o kraju lub None jeśli nie znaleziono
        """
        self._log(f"Pobieranie szczegółowych informacji o kraju: {country_code}...")
        country = self.provider.get_country_info(country_code)
        if country:
            self._log(f"✓ Znaleziono kraj: {country.get('name', 'N/A')}")
        else:
            self._log(f"✗ Nie znaleziono kraju o kodzie: {country_code}")
        return country
    
    def display_country_info(self, country_code: str):
        """
        Wyświetla szczegółowe informacje o kraju w czytelnej formie.
        
        Metoda pobiera i formatuje informacje o kraju, wyświetlając je
        w czytelnej formie tekstowej.
        
        Args:
            country_code: Kod kraju ISO 3 (np. 'POL' dla Polski)
        """
        country = self.get_country_details(country_code)
        if not country:
            print(f"Nie znaleziono kraju o kodzie: {country_code}")
            return
        
        print("\n" + "="*70)
        print(f"INFORMACJE O KRAJU: {country.get('name', 'N/A')}")
        print("="*70)
        print(f"Kod ISO 2: {country.get('iso2Code', 'N/A')}")
        print(f"Kod ISO 3: {country.get('id', 'N/A')}")
        print(f"Region: {country.get('region', {}).get('value', 'N/A')}")
        print(f"Poziom dochodów: {country.get('incomeLevel', {}).get('value', 'N/A')}")
        print(f"Typ pożyczek: {country.get('lendingType', {}).get('value', 'N/A')}")
        print(f"Kapitał: {country.get('capitalCity', 'N/A')}")
        print(f"Długość geograficzna: {country.get('longitude', 'N/A')}")
        print(f"Szerokość geograficzna: {country.get('latitude', 'N/A')}")
        print("="*70)
    
    def get_indicators_list(
        self,
        indicator_code: Optional[str] = None,
        source: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera listę wskaźników dostępnych w API World Bank.
        
        Metoda pobiera informacje o wskaźnikach ekonomicznych, społecznych
        i innych metrykach dostępnych w bazie danych World Bank.
        Można filtrować wskaźniki według źródła danych lub tematu,
        lub pobrać informacje o konkretnym wskaźniku.
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
            source: Kod źródła danych
            topic: Kod tematu
        
        Returns:
            Lista słowników zawierających informacje o wskaźnikach
        """
        self._log("Pobieranie listy wskaźników z API World Bank...")
        indicators = self.provider.get_indicators(
            indicator_code=indicator_code,
            source=source,
            topic=topic
        )
        self._log(f"✓ Pobrano {len(indicators)} wskaźników")
        return indicators
    
    def get_indicator_details(self, indicator_code: str) -> Optional[Dict]:
        """
        Pobiera szczegółowe informacje o konkretnym wskaźniku.
        
        Metoda pobiera pełne informacje o wskaźniku, w tym:
        - Nazwę wskaźnika
        - Kod wskaźnika
        - Opis
        - Źródło danych
        - Temat
        - Jednostkę miary
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
        
        Returns:
            Słownik z informacjami o wskaźniku lub None jeśli nie znaleziono
        """
        self._log(f"Pobieranie szczegółowych informacji o wskaźniku: {indicator_code}...")
        indicator = self.provider.get_indicator_info(indicator_code)
        if indicator:
            self._log(f"✓ Znaleziono wskaźnik: {indicator.get('name', 'N/A')}")
        else:
            self._log(f"✗ Nie znaleziono wskaźnika o kodzie: {indicator_code}")
        return indicator
    
    def display_indicator_info(self, indicator_code: str):
        """
        Wyświetla szczegółowe informacje o wskaźniku w czytelnej formie.
        
        Metoda pobiera i formatuje informacje o wskaźniku, wyświetlając je
        w czytelnej formie tekstowej.
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
        """
        indicator = self.get_indicator_details(indicator_code)
        if not indicator:
            print(f"Nie znaleziono wskaźnika o kodzie: {indicator_code}")
            return
        
        print("\n" + "="*70)
        print(f"INFORMACJE O WSKAŹNIKU: {indicator.get('name', 'N/A')}")
        print("="*70)
        print(f"Kod: {indicator.get('id', 'N/A')}")
        print(f"Źródło: {indicator.get('sourceNote', 'N/A')[:100]}...")
        print(f"Temat: {indicator.get('topics', [{}])[0].get('value', 'N/A') if indicator.get('topics') else 'N/A'}")
        print("="*70)
    
    def get_data_for_indicator(
        self,
        indicator_code: str,
        country_codes: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        date: Optional[str] = None
    ) -> List[Dict]:
        """
        Pobiera dane dla określonego wskaźnika i krajów.
        
        Metoda pobiera dane statystyczne dla określonego wskaźnika
        i krajów w podanym zakresie lat. Dane są zwracane jako lista
        słowników, gdzie każdy słownik zawiera informacje o wartości
        wskaźnika dla konkretnego kraju i roku.
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
            country_codes: Kod kraju ISO 3 lub lista kodów (np. 'POL' lub ['POL', 'USA'])
                          Jeśli None, pobiera dane dla wszystkich krajów
            start_year: Rok początkowy zakresu danych (np. 2000)
            end_year: Rok końcowy zakresu danych (np. 2020)
            date: Zakres dat w formacie 'YYYY:YYYY' (alternatywa dla start_year/end_year)
        
        Returns:
            Lista słowników zawierających dane dla danego wskaźnika i krajów
        """
        self._log(f"Pobieranie danych dla wskaźnika: {indicator_code}...")
        if country_codes:
            if isinstance(country_codes, list):
                self._log(f"  Kraje: {', '.join(country_codes)}")
            else:
                self._log(f"  Kraj: {country_codes}")
        else:
            self._log("  Wszystkie kraje")
        
        if date:
            self._log(f"  Zakres dat: {date}")
        elif start_year or end_year:
            self._log(f"  Zakres lat: {start_year or '?'} - {end_year or '?'}")
        
        data = self.provider.get_data(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            date=date
        )
        
        self._log(f"✓ Pobrano {len(data)} rekordów")
        return data
    
    def get_data_as_dataframe(
        self,
        indicator_code: str,
        country_codes: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pobiera dane dla wskaźnika i konwertuje je do DataFrame pandas.
        
        Metoda pobiera dane z API i konwertuje je do formatu pandas DataFrame,
        co ułatwia analizę i manipulację danymi. DataFrame ma kolumny:
        - country: Nazwa kraju
        - countryCode: Kod kraju ISO 3
        - indicator: Nazwa wskaźnika
        - indicatorCode: Kod wskaźnika
        - date: Rok
        - value: Wartość wskaźnika
        
        Args:
            indicator_code: Kod wskaźnika (np. 'SP.POP.TOTL' dla populacji)
            country_codes: Kod kraju ISO 3 lub lista kodów
            start_year: Rok początkowy zakresu danych
            end_year: Rok końcowy zakresu danych
            date: Zakres dat w formacie 'YYYY:YYYY'
        
        Returns:
            DataFrame pandas z danymi
        """
        data = self.get_data_for_indicator(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            date=date
        )
        
        if not data:
            return pd.DataFrame()
        
        # Konwertuj do DataFrame
        df = pd.DataFrame(data)
        
        # Konwertuj wartość na liczbę jeśli możliwe
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Konwertuj datę na liczbę
        if 'date' in df.columns:
            df['date'] = pd.to_numeric(df['date'], errors='coerce')
        
        return df
    
    def display_data_summary(
        self,
        indicator_code: str,
        country_codes: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ):
        """
        Wyświetla podsumowanie danych dla wskaźnika.
        
        Metoda pobiera dane dla wskaźnika i wyświetla statystyki opisowe,
        w tym średnią, medianę, minimum, maximum i liczbę rekordów.
        
        Args:
            indicator_code: Kod wskaźnika
            country_codes: Kod kraju lub lista kodów
            start_year: Rok początkowy
            end_year: Rok końcowy
        """
        df = self.get_data_as_dataframe(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year
        )
        
        if df.empty:
            print("Brak danych do wyświetlenia")
            return
        
        print("\n" + "="*70)
        print(f"PODSUMOWANIE DANYCH DLA WSKAŹNIKA: {indicator_code}")
        print("="*70)
        print(f"Liczba rekordów: {len(df)}")
        
        if 'value' in df.columns:
            print(f"\nStatystyki wartości:")
            print(f"  Średnia: {df['value'].mean():.2f}")
            print(f"  Mediana: {df['value'].median():.2f}")
            print(f"  Minimum: {df['value'].min():.2f}")
            print(f"  Maximum: {df['value'].max():.2f}")
            print(f"  Odchylenie standardowe: {df['value'].std():.2f}")
        
        if 'date' in df.columns:
            print(f"\nZakres lat: {int(df['date'].min())} - {int(df['date'].max())}")
        
        if 'country' in df.columns:
            unique_countries = df['country'].nunique()
            print(f"Liczba krajów: {unique_countries}")
        
        print("="*70)
    
    def search_countries(self, query: str) -> List[Dict]:
        """
        Wyszukuje kraje na podstawie zapytania tekstowego.
        
        Metoda przeszukuje wszystkie kraje dostępne w API World Bank
        i zwraca te, których nazwa, kod ISO 2 lub kod ISO 3 zawiera
        podane zapytanie (bez rozróżniania wielkości liter).
        
        Args:
            query: Tekst do wyszukania (nazwa kraju, kod ISO, itp.)
        
        Returns:
            Lista krajów pasujących do zapytania
        """
        self._log(f"Wyszukiwanie krajów: {query}...")
        results = self.provider.search_countries(query)
        self._log(f"✓ Znaleziono {len(results)} krajów")
        return results
    
    def search_indicators(self, query: str) -> List[Dict]:
        """
        Wyszukuje wskaźniki na podstawie zapytania tekstowego.
        
        Metoda przeszukuje wszystkie wskaźniki dostępne w API World Bank
        i zwraca te, których nazwa lub kod zawiera podane zapytanie
        (bez rozróżniania wielkości liter).
        
        Args:
            query: Tekst do wyszukania (nazwa wskaźnika, kod, itp.)
        
        Returns:
            Lista wskaźników pasujących do zapytania
        """
        self._log(f"Wyszukiwanie wskaźników: {query}...")
        results = self.provider.search_indicators(query)
        self._log(f"✓ Znaleziono {len(results)} wskaźników")
        return results
    
    def get_regions_list(self) -> List[Dict]:
        """
        Pobiera listę regionów dostępnych w API World Bank.
        
        Metoda pobiera informacje o regionach geograficznych
        dostępnych w bazie danych World Bank.
        
        Returns:
            Lista słowników zawierających informacje o regionach
        """
        self._log("Pobieranie listy regionów z API World Bank...")
        regions = self.provider.get_regions()
        self._log(f"✓ Pobrano {len(regions)} regionów")
        return regions
    
    def get_topics_list(self) -> List[Dict]:
        """
        Pobiera listę tematów dostępnych w API World Bank.
        
        Metoda pobiera informacje o tematach kategoryzujących
        wskaźniki w bazie danych World Bank (np. Health, Education, Economy).
        
        Returns:
            Lista słowników zawierających informacje o tematach
        """
        self._log("Pobieranie listy tematów z API World Bank...")
        topics = self.provider.get_topics()
        self._log(f"✓ Pobrano {len(topics)} tematów")
        return topics
    
    def get_sources_list(self) -> List[Dict]:
        """
        Pobiera listę źródeł danych dostępnych w API World Bank.
        
        Metoda pobiera informacje o źródłach danych, z których
        pochodzą wskaźniki w bazie danych World Bank.
        
        Returns:
            Lista słowników zawierających informacje o źródłach danych
        """
        self._log("Pobieranie listy źródeł danych z API World Bank...")
        sources = self.provider.get_sources()
        self._log(f"✓ Pobrano {len(sources)} źródeł danych")
        return sources
    
    def export_data_to_csv(
        self,
        indicator_code: str,
        output_file: str,
        country_codes: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> bool:
        """
        Eksportuje dane do pliku CSV.
        
        Metoda pobiera dane dla wskaźnika i zapisuje je do pliku CSV.
        Plik zawiera kolumny: country, countryCode, indicator, indicatorCode, date, value.
        
        Args:
            indicator_code: Kod wskaźnika
            output_file: Ścieżka do pliku wyjściowego CSV
            country_codes: Kod kraju lub lista kodów
            start_year: Rok początkowy
            end_year: Rok końcowy
        
        Returns:
            True jeśli eksport się powiódł, False w przeciwnym razie
        """
        self._log(f"Eksportowanie danych do CSV: {output_file}...")
        
        df = self.get_data_as_dataframe(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year
        )
        
        if df.empty:
            self._log("✗ Brak danych do eksportu")
            return False
        
        try:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            df.to_csv(output_file, index=False, encoding='utf-8')
            self._log(f"✓ Zapisano {len(df)} rekordów do pliku: {output_file}")
            return True
        except Exception as e:
            self._log(f"✗ Błąd podczas zapisywania do CSV: {e}")
            return False
    
    def export_data_to_json(
        self,
        indicator_code: str,
        output_file: str,
        country_codes: Optional[Union[str, List[str]]] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> bool:
        """
        Eksportuje dane do pliku JSON.
        
        Metoda pobiera dane dla wskaźnika i zapisuje je do pliku JSON.
        Dane są zapisywane jako lista słowników.
        
        Args:
            indicator_code: Kod wskaźnika
            output_file: Ścieżka do pliku wyjściowego JSON
            country_codes: Kod kraju lub lista kodów
            start_year: Rok początkowy
            end_year: Rok końcowy
        
        Returns:
            True jeśli eksport się powiódł, False w przeciwnym razie
        """
        self._log(f"Eksportowanie danych do JSON: {output_file}...")
        
        data = self.get_data_for_indicator(
            indicator_code=indicator_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year
        )
        
        if not data:
            self._log("✗ Brak danych do eksportu")
            return False
        
        try:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._log(f"✓ Zapisano {len(data)} rekordów do pliku: {output_file}")
            return True
        except Exception as e:
            self._log(f"✗ Błąd podczas zapisywania do JSON: {e}")
            return False
    
    def compare_countries(
        self,
        indicator_code: str,
        country_codes: List[str],
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Porównuje wartości wskaźnika dla różnych krajów.
        
        Metoda pobiera dane dla wskaźnika dla listy krajów i zwraca
        DataFrame z porównaniem wartości. Jeśli podano rok, zwraca
        wartości dla tego roku. W przeciwnym razie zwraca najnowsze
        dostępne wartości dla każdego kraju.
        
        Args:
            indicator_code: Kod wskaźnika
            country_codes: Lista kodów krajów do porównania
            year: Rok do porównania (opcjonalnie, jeśli None, używa najnowszych danych)
        
        Returns:
            DataFrame z porównaniem wartości dla krajów
        """
        self._log(f"Porównywanie krajów dla wskaźnika: {indicator_code}...")
        
        df = self.get_data_as_dataframe(
            indicator_code=indicator_code,
            country_codes=country_codes
        )
        
        if df.empty:
            return pd.DataFrame()
        
        if year:
            df = df[df['date'] == year]
        else:
            # Użyj najnowszych dostępnych danych dla każdego kraju
            df = df.loc[df.groupby('countryCode')['date'].idxmax()]
        
        # Sortuj według wartości
        if 'value' in df.columns:
            df = df.sort_values('value', ascending=False)
        
        return df
    
    def get_trend_data(
        self,
        indicator_code: str,
        country_code: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Pobiera dane trendu dla wskaźnika i kraju w czasie.
        
        Metoda pobiera dane dla wskaźnika dla konkretnego kraju
        w zakresie lat i zwraca DataFrame posortowany chronologicznie,
        co ułatwia analizę trendów w czasie.
        
        Args:
            indicator_code: Kod wskaźnika
            country_code: Kod kraju ISO 3
            start_year: Rok początkowy
            end_year: Rok końcowy
        
        Returns:
            DataFrame z danymi trendu posortowanymi chronologicznie
        """
        self._log(f"Pobieranie danych trendu dla {country_code} i wskaźnika {indicator_code}...")
        
        df = self.get_data_as_dataframe(
            indicator_code=indicator_code,
            country_codes=country_code,
            start_year=start_year,
            end_year=end_year
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # Sortuj według daty
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        return df

