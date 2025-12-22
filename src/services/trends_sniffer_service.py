#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serwis do pobierania danych z Google Trends za pomocą PyTrends.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

# Sprawdzenie i naprawa problemu z urllib3 2.0+ i method_whitelist
try:
    import urllib3
    urllib3_version = urllib3.__version__ if hasattr(urllib3, '__version__') else 'unknown'
    major_version = int(urllib3_version.split('.')[0]) if urllib3_version != 'unknown' else 0
    
    if major_version >= 2:
        raise RuntimeError(
            "Wykryto urllib3 2.0+, który nie jest kompatybilny z pytrends. "
            "Aby naprawić, wykonaj: pip3 install 'urllib3==1.26.18' --force-reinstall"
        )
except Exception:
    pass

from pytrends.request import TrendReq

# Opcjonalne importy
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from sqlalchemy import create_engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class TrendsSnifferService:
    """
    Serwis do pobierania i przetwarzania danych z Google Trends.
    """
    
    def __init__(
        self,
        language: str = 'pl-PL',
        timezone: int = -120,
        retries: int = 2,
        backoff_factor: float = 0.1,
        requests_args: Optional[Dict] = None,
        verbose: bool = True
    ):
        """
        Inicjalizacja serwisu.
        
        Args:
            language: Język interfejsu (pl-PL, en-US, de-DE, itp.)
            timezone: Strefa czasowa w minutach od UTC (-120 = UTC-2 dla Polski)
            retries: Liczba ponownych prób przy błędach
            backoff_factor: Czas oczekiwania między ponownymi próbami (w sekundach)
            requests_args: Dodatkowe nagłówki HTTP (None lub dict)
            verbose: Czy wyświetlać szczegółowe informacje
        """
        self.language = language
        self.timezone = timezone
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.requests_args = requests_args
        self.verbose = verbose
        
        self.pytrends = None
        self._init_pytrends()
    
    def _init_pytrends(self):
        """Inicjalizuje połączenie z Google Trends."""
        if self.verbose:
            print("Inicjalizacja połączenia z Google Trends...")
        
        kwargs = {
            'hl': self.language,
            'tz': self.timezone,
            'retries': self.retries,
            'backoff_factor': self.backoff_factor
        }
        
        if self.requests_args:
            kwargs['requests_args'] = self.requests_args
        
        self.pytrends = TrendReq(**kwargs)
        
        if self.verbose:
            print("✓ Połączenie zainicjalizowane")
    
    def build_payload(
        self,
        keywords: List[str],
        category: int = 0,
        timeframe: str = 'now 1-H',
        country: str = 'US',
        region: Optional[str] = None,
        city: Optional[str] = None,
        gprop: str = ''
    ) -> bool:
        """
        Buduje zapytanie do Google Trends.
        
        Args:
            keywords: Lista słów kluczowych (maksymalnie 5)
            category: Kategoria (0 = wszystkie, 7 = Finanse, 71 = Technologia, itd.)
            timeframe: Zakres czasowy ('today 5-y', 'now 7-d', 'YYYY-MM-DD YYYY-MM-DD', itp.)
            country: Kod kraju (PL, US, DE, GB, '' dla całego świata)
            region: Kod regionu (opcjonalnie, np. 'PL-MZ' dla Mazowsza)
            city: Nazwa miasta (opcjonalnie)
            gprop: Typ wyszukiwania ('', 'images', 'news', 'youtube', 'froogle')
        
        Returns:
            True jeśli zapytanie zostało zbudowane pomyślnie
        """
        geo = country
        if region:
            geo = region
        if city:
            # Dla miasta używamy nazwy miasta, ale może wymagać specjalnego formatu
            pass
        
        geo = geo if geo else ''
        
        if self.verbose:
            print(f"Budowanie zapytania dla: {', '.join(keywords)}...")
        
        try:
            self.pytrends.build_payload(
                kw_list=keywords,
                cat=category,
                timeframe=timeframe,
                geo=geo,
                gprop=gprop
            )
            if self.verbose:
                print("✓ Zapytanie zbudowane")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas budowania zapytania: {e}")
            return False
    
    def get_interest_over_time(self) -> Optional[pd.DataFrame]:
        """
        Pobiera dane o zainteresowaniu w czasie.
        
        Returns:
            DataFrame z danymi lub None w przypadku błędu
        """
        if self.verbose:
            print("Pobieranie danych o zainteresowaniu w czasie...")
        
        try:
            data = self.pytrends.interest_over_time()
            
            if data.empty:
                if self.verbose:
                    print("Ostrzeżenie: Brak danych!")
                return None
            
            # Usuń kolumnę isPartial jeśli istnieje
            if 'isPartial' in data.columns:
                data = data.drop('isPartial', axis=1)
            
            if self.verbose:
                print(f"✓ Pobrano {len(data)} rekordów")
                if len(data) > 0:
                    print(f"  Zakres dat: {data.index.min()} - {data.index.max()}")
            
            return data
        
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas pobierania danych: {e}")
            return None
    
    def get_interest_by_region(
        self,
        resolution: str = 'COUNTRY',
        inc_low_vol: bool = True,
        inc_geo_code: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Pobiera dane o zainteresowaniu według regionu.
        
        Args:
            resolution: Poziom szczegółowości ('COUNTRY', 'REGION', 'CITY', 'DMA')
            inc_low_vol: Uwzględnia regiony o niskim wolumenie wyszukiwań
            inc_geo_code: Uwzględnia kody geograficzne w wynikach
        
        Returns:
            DataFrame z danymi regionalnymi lub None w przypadku błędu
        """
        if self.verbose:
            print(f"Pobieranie danych regionalnych (resolution: {resolution})...")
        
        try:
            data = self.pytrends.interest_by_region(
                resolution=resolution,
                inc_low_vol=inc_low_vol,
                inc_geo_code=inc_geo_code
            )
            
            if data.empty:
                if self.verbose:
                    print("Ostrzeżenie: Brak danych regionalnych!")
                return None
            
            if self.verbose:
                print(f"✓ Pobrano dane dla {len(data)} regionów")
            
            return data
        
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas pobierania danych regionalnych: {e}")
            return None
    
    def get_related_queries(self) -> Optional[Dict]:
        """
        Pobiera powiązane zapytania.
        
        Returns:
            Słownik z powiązanymi zapytaniami lub None w przypadku błędu
        """
        if self.verbose:
            print("Pobieranie powiązanych zapytań...")
        
        try:
            related = self.pytrends.related_queries()
            
            if self.verbose:
                print("✓ Pobrano powiązane zapytania")
            
            return related
        
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas pobierania powiązanych zapytań: {e}")
            return None
    
    def export_to_csv(self, data: pd.DataFrame, filepath: str) -> bool:
        """
        Eksportuje dane do pliku CSV.
        
        Args:
            data: DataFrame do eksportu
            filepath: Ścieżka do pliku CSV
        
        Returns:
            True jeśli eksport się powiódł
        """
        if data is None or data.empty:
            return False
        
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        try:
            data.to_csv(filepath, encoding='utf-8')
            if self.verbose:
                print(f"✓ Zapisano do CSV: {filepath}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas zapisywania do CSV: {e}")
            return False
    
    def export_to_json(self, data: pd.DataFrame, filepath: str) -> bool:
        """
        Eksportuje dane do pliku JSON.
        
        Args:
            data: DataFrame do eksportu
            filepath: Ścieżka do pliku JSON
        
        Returns:
            True jeśli eksport się powiódł
        """
        if data is None or data.empty:
            return False
        
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        try:
            data.to_json(filepath, orient='records', date_format='iso', indent=2)
            if self.verbose:
                print(f"✓ Zapisano do JSON: {filepath}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas zapisywania do JSON: {e}")
            return False
    
    def export_to_database(
        self,
        data: pd.DataFrame,
        host: str,
        port: int,
        database: str,
        user: str,
        password: Optional[str],
        table_name: str
    ) -> bool:
        """
        Eksportuje dane do bazy danych PostgreSQL.
        
        Args:
            data: DataFrame do eksportu
            host: Host bazy danych
            port: Port bazy danych
            database: Nazwa bazy danych
            user: Użytkownik bazy danych
            password: Hasło bazy danych (None jeśli nie wymagane)
            table_name: Nazwa tabeli w bazie danych
        
        Returns:
            True jeśli eksport się powiódł
        """
        if not SQLALCHEMY_AVAILABLE:
            if self.verbose:
                print("Błąd: sqlalchemy nie jest zainstalowany")
            return False
        
        if data is None or data.empty:
            return False
        
        try:
            # Buduj connection string
            if password:
                conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                conn_str = f"postgresql://{user}@{host}:{port}/{database}"
            
            engine = create_engine(conn_str)
            
            # Zapisz do bazy
            data.to_sql(table_name, engine, if_exists='append', index=True)
            
            if self.verbose:
                print(f"✓ Zapisano do bazy danych: {database}.{table_name}")
            return True
        
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas zapisywania do bazy danych: {e}")
            return False
    
    def create_plot(
        self,
        data: pd.DataFrame,
        keywords: List[str],
        show: bool = True,
        save: bool = False,
        filepath: Optional[str] = None,
        format: str = 'png'
    ) -> bool:
        """
        Tworzy wykres z danych.
        
        Args:
            data: DataFrame z danymi
            keywords: Lista słów kluczowych (do tytułu)
            show: Czy wyświetlać wykres
            save: Czy zapisywać wykres do pliku
            filepath: Ścieżka do pliku (jeśli None, generowana automatycznie)
            format: Format wykresów (png, pdf, svg)
        
        Returns:
            True jeśli wykres został utworzony pomyślnie
        """
        if not MATPLOTLIB_AVAILABLE or data is None or data.empty:
            if self.verbose and not MATPLOTLIB_AVAILABLE:
                print("Ostrzeżenie: matplotlib nie jest zainstalowany. Wykresy nie będą dostępne.")
            return False
        
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            data.plot(ax=ax)
            ax.set_title(f'Trendy dla: {", ".join(keywords)}')
            ax.set_xlabel('Data')
            ax.set_ylabel('Zainteresowanie (0-100)')
            ax.legend(title='Słowa kluczowe')
            ax.grid(True)
            plt.tight_layout()
            
            if show:
                plt.show()
            
            if save:
                if filepath is None:
                    os.makedirs('output', exist_ok=True)
                    filepath = os.path.join(
                        'output',
                        f"trends_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                    )
                else:
                    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
                
                plt.savefig(filepath, format=format, dpi=300)
                if self.verbose:
                    print(f"✓ Zapisano wykres: {filepath}")
            
            plt.close()
            return True
        
        except Exception as e:
            if self.verbose:
                print(f"Błąd podczas tworzenia wykresów: {e}")
            return False

