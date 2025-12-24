#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania danych z Google Trends dla fraz z bitcoin_sentiment_phrases
z użyciem Mullvad VPN do przełączania się między serwerami.
"""

# ============================================================================
# KONFIGURACJA
# ============================================================================

CONFIG_VERBOSE = True                               # Czy wyświetlać szczegółowe informacje
CONFIG_QUERIES_PER_MINUTE = 60                      # Limit zapytań na minutę (PyTrends)
CONFIG_DELAY_BETWEEN_QUERIES = 1                    # Opóźnienie między zapytaniami (sekundy)
CONFIG_DELAY_AFTER_VPN_SWITCH = 5                   # Opóźnienie po przełączeniu VPN (sekundy)
CONFIG_VPN_SWITCH_EVERY_N_QUERIES = 4               # Przełącz VPN co N zapytań
CONFIG_TIMEFRAME = 'now 1-H'                        # Zakres czasowy: ostatnia godzina
CONFIG_LIMIT_PHRASES = None                         # Limit fraz do przetworzenia (None = wszystkie)
CONFIG_COUNTRY_FILTER = None                        # Filtruj po kodzie kraju (None = wszystkie)
CONFIG_NOT_ZERO_MULTIPLIER = True                   # Pomijaj frazy z multiplier = 0.0 (True = domyślnie)
CONFIG_RESUME_FROM_LAST = True                      # Wznawiaj od ostatnio sprawdzonych krajów (True = domyślnie)
CONFIG_LOG_FILE = None                              # Plik logu (None = użyj domyślnego w .dev/logs/)
CONFIG_CYCLE_INTERVAL = 3                           # Interwał między cyklami (sekundy, domyślnie 1h = 3600s)
CONFIG_DAEMON_MODE = True                           # Tryb daemon - działa w pętli (True = domyślnie)

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import time
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
# Napraw FutureWarning z pandas
pd.set_option('future.no_silent_downcasting', True)

from dotenv import load_dotenv
import psycopg2
import requests
import logging
from datetime import timedelta

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Sprawdzenie urllib3
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

# Załaduj zmienne środowiskowe
load_dotenv()


def find_mullvad_command() -> str:
    """
    Znajduje ścieżkę do komendy mullvad.
    
    Returns:
        Ścieżka do komendy mullvad lub 'mullvad' jeśli nie znaleziono
    """
    # Sprawdź standardowe lokalizacje
    possible_paths = [
        '/usr/local/bin/mullvad',
        '/opt/homebrew/bin/mullvad',
        '/usr/bin/mullvad',
        '/Applications/Mullvad VPN.app/Contents/Resources/mullvad'
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Spróbuj znaleźć przez which/shutil
    try:
        import shutil
        path = shutil.which('mullvad')
        if path:
            return path
    except Exception:
        pass
    
    # Jeśli nie znaleziono, zwróć 'mullvad' (może być w PATH)
    return 'mullvad'


# Globalna zmienna z ścieżką do mullvad
MULLVAD_CMD = find_mullvad_command()


def get_database_connection():
    """Tworzy połączenie z bazą danych."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL nie jest ustawiony w pliku .env")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Błąd połączenia z bazą danych: {e}")


def get_current_ip() -> Optional[str]:
    """
    Pobiera aktualny adres IP.
    
    Returns:
        Adres IP lub None w przypadku błędu
    """
    try:
        import requests
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd pobierania IP: {e}")
        return None


def get_mullvad_status() -> Dict[str, str]:
    """
    Pobiera status Mullvad VPN.
    
    Returns:
        Słownik z informacjami o statusie VPN
    """
    # Sprawdź czy mullvad jest dostępny
    if not os.path.exists(MULLVAD_CMD) and MULLVAD_CMD == 'mullvad':
        if CONFIG_VERBOSE:
            print(f"  ⚠ Komenda 'mullvad' nie została znaleziona w systemie")
        return {'connected': False, 'location': None, 'ip': None, 'relay': None, 'error': 'mullvad_not_found'}
    
    try:
        result = subprocess.run(
            [MULLVAD_CMD, 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Sprawdź czy komenda się powiodła
        if result.returncode != 0:
            if CONFIG_VERBOSE:
                print(f"  ⚠ Błąd wykonania 'mullvad status': {result.stderr}")
            return {'connected': False, 'location': None, 'ip': None, 'relay': None, 'error': result.stderr}
        
        status_text = result.stdout
        
        # Sprawdź czy jest połączony (sprawdź pierwszy wiersz)
        first_line = status_text.split('\n')[0].strip() if status_text else ""
        is_connected = 'Connected' in first_line or 'connected' in first_line.lower()
        
        status_info = {
            'connected': is_connected,
            'location': None,
            'ip': None,
            'relay': None
        }
        
        # Wyciągnij lokalizację
        location_match = re.search(r'Visible location:\s+(.+?)(?:\.|$)', status_text, re.MULTILINE)
        if location_match:
            status_info['location'] = location_match.group(1).strip()
        
        # Wyciągnij IP (może być w różnych formatach)
        ip_match = re.search(r'IPv4:\s+([\d.]+)', status_text)
        if not ip_match:
            # Spróbuj alternatywny format
            ip_match = re.search(r'IP:\s+([\d.]+)', status_text)
        if ip_match:
            status_info['ip'] = ip_match.group(1)
        
        # Wyciągnij relay
        relay_match = re.search(r'Relay:\s+(.+?)(?:\n|$)', status_text, re.MULTILINE)
        if relay_match:
            status_info['relay'] = relay_match.group(1).strip()
        
        if CONFIG_VERBOSE and not is_connected:
            print(f"  Debug: Status VPN - {first_line}")
        
        return status_info
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd sprawdzania statusu Mullvad: {e}")
        return {'connected': False, 'location': None, 'ip': None, 'relay': None}


def get_mullvad_location_code(country_code: str) -> Optional[str]:
    """
    Mapuje kod kraju ISO 2 na kod lokalizacji Mullvad VPN.
    
    Args:
        country_code: Kod kraju ISO 2 (np. 'US', 'PL', 'DE')
    
    Returns:
        Kod lokalizacji Mullvad (np. 'us', 'pl', 'de') lub None jeśli nie dostępne
    """
    # Większość kodów jest taka sama, tylko lowercase
    # Mapowanie specjalnych przypadków
    special_mappings = {
        'GB': 'gb',  # United Kingdom
        'US': 'us',
        'CA': 'ca',
        'AU': 'au',
        'DE': 'de',
        'FR': 'fr',
        'IT': 'it',
        'ES': 'es',
        'PL': 'pl',
        'NL': 'nl',
        'BE': 'be',
        'CH': 'ch',
        'AT': 'at',
        'SE': 'se',
        'NO': 'no',
        'DK': 'dk',
        'FI': 'fi',
        'IE': 'ie',
        'PT': 'pt',
        'GR': 'gr',
        'CZ': 'cz',
        'RO': 'ro',
        'HU': 'hu',
        'BG': 'bg',
        'SK': 'sk',
        'SI': 'si',
        'HR': 'hr',
        'EE': 'ee',
        'LV': 'lv',
        'LT': 'lt',
        'JP': 'jp',
        'KR': 'kr',
        'SG': 'sg',
        'HK': 'hk',
        'TW': 'tw',
        'IN': 'in',
        'TH': 'th',
        'VN': 'vn',
        'MY': 'my',
        'ID': 'id',
        'PH': 'ph',
        'BR': 'br',
        'MX': 'mx',
        'AR': 'ar',
        'CL': 'cl',
        'CO': 'co',
        'PE': 'pe',
        'ZA': 'za',
        'EG': 'eg',
        'AE': 'ae',
        'SA': 'sa',
        'IL': 'il',
        'TR': 'tr',
        'RU': 'ru',
        'UA': 'ua',
        'NZ': 'nz',
        'NG': 'ng',  # Nigeria
    }
    
    # Sprawdź specjalne mapowanie
    if country_code.upper() in special_mappings:
        return special_mappings[country_code.upper()]
    
    # Domyślnie użyj lowercase kodu kraju
    # Sprawdź czy Mullvad ma taką lokalizację
    try:
        result = subprocess.run(
            [MULLVAD_CMD, 'relay', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        location_code_lower = country_code.lower()
        # Sprawdź czy kod kraju występuje w liście relay
        if location_code_lower in result.stdout.lower():
            return location_code_lower
        
        return None
    
    except Exception:
        # W przypadku błędu, spróbuj użyć lowercase
        return country_code.lower()


def switch_mullvad_location(location_code: Optional[str] = None) -> bool:
    """
    Przełącza Mullvad VPN na nową lokalizację.
    
    Args:
        location_code: Kod lokalizacji (np. 'us', 'de', 'pl') lub None dla losowej
    
    Returns:
        True jeśli przełączenie się powiodło
    """
    try:
        if location_code:
            # Przełącz na konkretną lokalizację
            result = subprocess.run(
                [MULLVAD_CMD, 'relay', 'set', 'location', location_code],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Sprawdź czy lokalizacja jest dostępna
            if 'not found' in result.stderr.lower() or 'invalid' in result.stderr.lower():
                if CONFIG_VERBOSE:
                    print(f"  ⚠ Lokalizacja {location_code} nie jest dostępna w Mullvad")
                return False
        else:
            # Losowa lokalizacja
            subprocess.run(
                [MULLVAD_CMD, 'relay', 'set', 'location', 'any'],
                capture_output=True,
                timeout=10
            )
        
        # Rozłącz i połącz ponownie
        subprocess.run([MULLVAD_CMD, 'disconnect'], capture_output=True, timeout=5)
        time.sleep(2)
        
        connect_result = subprocess.run(
            [MULLVAD_CMD, 'connect'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if connect_result.returncode != 0:
            if CONFIG_VERBOSE:
                print(f"  ⚠ Błąd podczas łączenia z VPN: {connect_result.stderr}")
            return False
        
        # Poczekaj na połączenie i zweryfikuj
        max_wait = 20  # Zwiększono z 15 do 20 sekund dla wolniejszych połączeń
        wait_interval = 1
        waited = 0
        
        while waited < max_wait:
            time.sleep(wait_interval)
            waited += wait_interval
            status = get_mullvad_status()
            if status['connected']:
                # Weryfikuj czy lokalizacja się zgadza (jeśli była podana)
                if location_code:
                    location_lower = location_code.lower()
                    status_location = status.get('location', '').lower()
                    # Sprawdź czy lokalizacja zawiera kod kraju (np. "nigeria" zawiera "ng")
                    # lub czy kod kraju jest w lokalizacji (np. "ng" w "nigeria, lagos")
                    if location_lower in status_location or any(
                        country_name in status_location 
                        for country_name in ['nigeria', 'new zealand', 'poland', 'germany', 'france'] 
                        if location_lower in country_name[:2]
                    ):
                        if CONFIG_VERBOSE:
                            print(f"  ✓ VPN połączony po {waited}s: {status.get('location', 'N/A')}")
                        return True
                    elif waited >= 10:  # Po 10 sekundach zaakceptuj nawet jeśli lokalizacja się nie zgadza
                        if CONFIG_VERBOSE:
                            print(f"  ⚠ VPN połączony, ale lokalizacja może się nie zgadzać: {status.get('location', 'N/A')} (oczekiwano: {location_code})")
                        return True
                else:
                    # Brak wymaganej lokalizacji - zaakceptuj połączenie
                    if CONFIG_VERBOSE:
                        print(f"  ✓ VPN połączony po {waited}s: {status.get('location', 'N/A')}")
                    return True
        
        if CONFIG_VERBOSE:
            print(f"  ⚠ VPN nie połączył się w ciągu {max_wait}s")
        return False
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd przełączania VPN: {e}")
        return False


def get_recently_checked_countries(conn, hours: int = 24) -> set:
    """
    Pobiera kody krajów, które były sprawdzane w ostatnich N godzinach.
    
    Args:
        conn: Połączenie z bazą danych
        hours: Liczba godzin wstecz do sprawdzenia
    
    Returns:
        Zbiór kodów krajów (ISO 2)
    """
    try:
        with conn.cursor() as cur:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cur.execute("""
                SELECT DISTINCT c.iso2_code
                FROM sentiment_measurement sm
                JOIN countries c ON sm.country_id = c.id
                WHERE sm.created_at >= %s
                ORDER BY c.iso2_code
            """, (cutoff_time,))
            rows = cur.fetchall()
            return {row[0] for row in rows}
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd pobierania ostatnio sprawdzanych krajów: {e}")
        return set()


def get_phrases_from_database(
    conn, 
    limit: Optional[int] = None, 
    country_filter: Optional[str] = None,
    not_zero_multiplier: bool = True,
    skip_recently_checked: bool = True,
    recent_hours: int = 24
) -> List[Dict]:
    """
    Pobiera frazy z bazy danych.
    
    Args:
        conn: Połączenie z bazą danych
        limit: Limit liczby fraz (None = wszystkie)
        country_filter: Filtr po kodzie kraju (None = wszystkie)
        not_zero_multiplier: Jeśli True, pomija frazy z multiplier = 0.0
        skip_recently_checked: Jeśli True, pomija kraje sprawdzane w ostatnich N godzinach
        recent_hours: Liczba godzin wstecz do sprawdzenia (domyślnie 24)
    
    Returns:
        Lista słowników z frazami
    """
    # Pobierz ostatnio sprawdzane kraje
    recently_checked = set()
    if skip_recently_checked:
        recently_checked = get_recently_checked_countries(conn, recent_hours)
        if CONFIG_VERBOSE and recently_checked:
            print(f"  ℹ Pomijam {len(recently_checked)} krajów sprawdzanych w ostatnich {recent_hours}h")
    
    query = """
        SELECT 
            bsp.id,
            bsp.country_id,
            c.iso2_code,
            c.name_en,
            bsp.language_code,
            bsp.phrase,
            bsp.multiplier
        FROM bitcoin_sentiment_phrases bsp
        JOIN countries c ON bsp.country_id = c.id
        WHERE bsp.is_active = TRUE
    """
    
    params = []
    
    if country_filter:
        query += " AND c.iso2_code = %s"
        params.append(country_filter.upper())
    
    if not_zero_multiplier:
        query += " AND bsp.multiplier != 0.0"
    
    # Pomijaj ostatnio sprawdzane kraje
    if skip_recently_checked and recently_checked:
        placeholders = ','.join(['%s'] * len(recently_checked))
        query += f" AND c.iso2_code NOT IN ({placeholders})"
        params.extend(list(recently_checked))
    
    query += " ORDER BY bsp.id"
    
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        
        phrases = []
        for row in rows:
            phrases.append({
                'id': row[0],
                'country_id': row[1],
                'country_code': row[2],
                'country_name': row[3],
                'language_code': row[4],
                'phrase': row[5],
                'multiplier': row[6]
            })
        
        return phrases


def is_rate_limit_error(error: Exception) -> bool:
    """
    Sprawdza czy błąd jest związany z limitem zapytań w PyTrends.
    
    Args:
        error: Wyjątek do sprawdzenia
    
    Returns:
        True jeśli to błąd limitu zapytań
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Typowe komunikaty błędów związanych z limitem zapytań w PyTrends
    rate_limit_indicators = [
        '429',  # HTTP 429 Too Many Requests
        'too many requests',
        'rate limit',
        'quota exceeded',
        'too many',
        'limit exceeded',
        'temporarily unavailable',
        'returned a response with code 429',
        'response code 429',
        'status code 429',
        'google returned a response with code 429',
        'returned status code 429',
    ]
    
    # Sprawdź czy którykolwiek wskaźnik występuje w komunikacie błędu
    for indicator in rate_limit_indicators:
        if indicator in error_str:
            return True
    
    # Sprawdź typ wyjątku
    if 'HTTPError' in error_type or '429' in error_str:
        return True
    
    return False


def get_trends_data(pytrends, phrase: str, country_code: str, language_code: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Pobiera dane z Google Trends dla frazy z pełnymi informacjami.
    
    Args:
        pytrends: Instancja TrendReq
        phrase: Fraza do wyszukania
        country_code: Kod kraju ISO 2
        language_code: Kod języka
    
    Returns:
        Tuple: (słownik z danymi lub None, czy wystąpił błąd limitu)
        Słownik zawiera:
        - interest_value: średnia wartość zainteresowania (0-100)
        - time_data: DataFrame z danymi czasowymi (timestamp, wartość)
        - stats: statystyki (count, mean, std)
        - regions: DataFrame z regionami gdzie wartość > 0
    """
    try:
        # Wyciągnij podstawowy kod języka (en z en-US)
        base_lang = language_code.split('-')[0] if '-' in language_code else language_code
        
        # Zbuduj payload
        pytrends.build_payload(
            [phrase],
            cat=0,
            timeframe=CONFIG_TIMEFRAME,
            geo=country_code,
            gprop=''
        )
        
        # Pobierz dane czasowe
        data_time = pytrends.interest_over_time()
        
        if data_time.empty:
            return {
                'interest_value': 0,
                'time_data': pd.DataFrame(),
                'stats': {'count': 0, 'mean': 0.0, 'std': 0.0},
                'regions': pd.DataFrame()
            }, False
        
        # Usuń kolumnę isPartial jeśli istnieje
        if 'isPartial' in data_time.columns:
            data_time = data_time.drop('isPartial', axis=1)
        
        # Oblicz statystyki
        interest_value = 0
        stats = {'count': 0, 'mean': 0.0, 'std': 0.0}
        
        if phrase in data_time.columns:
            values = data_time[phrase]
            interest_value = int(values.mean())
            stats = {
                'count': len(values),
                'mean': float(values.mean()),
                'std': float(values.std())
            }
        
        # Pobierz dane regionalne (tylko regiony z wartością > 0)
        regions_data = pd.DataFrame()
        try:
            # Pobierz dane regionalne
            data_regions = pytrends.interest_by_region(
                resolution='REGION',
                inc_low_vol=True,
                inc_geo_code=False
            )
            
            if not data_regions.empty and phrase in data_regions.columns:
                # Filtruj tylko regiony z wartością > 0
                regions_data = data_regions[data_regions[phrase] > 0].copy()
                # Sortuj malejąco
                if not regions_data.empty:
                    regions_data = regions_data.sort_values(phrase, ascending=False)
        except Exception as e:
            if CONFIG_VERBOSE:
                print(f"    ⚠ Nie udało się pobrać danych regionalnych: {e}")
            regions_data = pd.DataFrame()
        
        return {
            'interest_value': interest_value,
            'time_data': data_time,
            'stats': stats,
            'regions': regions_data
        }, False
    
    except Exception as e:
        # Sprawdź czy to błąd limitu zapytań
        if is_rate_limit_error(e):
            if CONFIG_VERBOSE:
                print(f"    ⚠ Wykryto limit zapytań PyTrends: {e}")
            return None, True  # Zwróć None i flagę błędu limitu
        
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd pobierania danych: {e}")
        return None, False  # Zwróć None ale bez flagi limitu


def save_measurement_to_database(
    conn,
    phrase_data: Dict,
    ip: Optional[str],
    vpn_country: Optional[str],
    trends_data: Optional[Dict[str, Any]],
    error_message: Optional[str] = None
) -> Optional[int]:
    """
    Zapisuje pomiar sentymentu do bazy danych.
    
    Args:
        conn: Połączenie z bazą danych
        phrase_data: Dane frazy (id, country_id, language_code, phrase)
        ip: Adres IP użyty do zapytania
        vpn_country: Kod kraju VPN (ISO 2)
        trends_data: Słownik z danymi z Google Trends lub None
        error_message: Komunikat błędu (jeśli wystąpił)
    
    Returns:
        ID zapisanego pomiaru (measurement_id) lub None w przypadku błędu
    """
    try:
        with conn.cursor() as cur:
            # Przygotuj dane do zapisu
            phrase_id = phrase_data['id']
            country_id = phrase_data['country_id']
            language_code = phrase_data['language_code']
            
            # Ogranicz vpn_country do 2 znaków (kod ISO 2) - zabezpieczenie przed długimi nazwami
            if vpn_country:
                vpn_country = vpn_country[:2].upper() if len(vpn_country) > 2 else vpn_country.upper()
            
            # Oblicz occurrence_count (liczba timestampów z wartością > 0)
            occurrence_count = 0
            stats_count = 0
            stats_mean = 0.0
            stats_std = 0.0
            
            if trends_data:
                time_data = trends_data.get('time_data', pd.DataFrame())
                phrase = phrase_data['phrase']
                
                if not time_data.empty and phrase in time_data.columns:
                    # Policz wystąpienia z wartością > 0
                    time_with_values = time_data[time_data[phrase] > 0]
                    occurrence_count = len(time_with_values)
                
                stats = trends_data.get('stats', {})
                stats_count = stats.get('count', 0)
                stats_mean = float(stats.get('mean', 0.0))
                stats_std = float(stats.get('std', 0.0))
            
            # Wstaw rekord do sentiment_measurement (zawsze, nawet bez wystąpień)
            insert_measurement = """
                INSERT INTO sentiment_measurement (
                    phrase_id, country_id, language_code, ip, vpn_country,
                    occurrence_count, stats_count, stats_mean, stats_std, error
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            cur.execute(
                insert_measurement,
                (
                    phrase_id,
                    country_id,
                    language_code,
                    ip,
                    vpn_country,
                    occurrence_count,
                    stats_count,
                    stats_mean,
                    stats_std,
                    error_message
                )
            )
            
            measurement_id = cur.fetchone()[0]
            conn.commit()
            
            # Jeśli są wystąpienia (occurrence_count > 0), zapisz je do sentiments_sniff
            if trends_data and occurrence_count > 0:
                time_data = trends_data.get('time_data', pd.DataFrame())
                regions_data = trends_data.get('regions', pd.DataFrame())
                phrase = phrase_data['phrase']
                
                if not time_data.empty and phrase in time_data.columns:
                    time_with_values = time_data[time_data[phrase] > 0]
                    
                    # Przygotuj listę regionów (jeśli dostępne)
                    # Uwaga: regiony z interest_by_region są zagregowane dla całego okresu,
                    # więc nie możemy ich bezpośrednio przypisać do konkretnych timestampów.
                    # Dla każdego timestampu z wartością > 0 zapisujemy wszystkie regiony z wartością > 0
                    # jako osobne rekordy w sentiments_sniff.
                    available_regions = []
                    if not regions_data.empty and phrase in regions_data.columns:
                        for idx, row in regions_data.iterrows():
                            region_name = str(idx)
                            available_regions.append(region_name)
                    
                    # Wstaw rekordy do sentiments_sniff
                    insert_sniff = """
                        INSERT INTO sentiments_sniff (
                            measurement_id, region, occurrence_time
                        ) VALUES (%s, %s, %s)
                    """
                    
                    sniff_records = []
                    
                    # Dla każdego wystąpienia (timestamp z wartością > 0)
                    for idx, row in time_with_values.iterrows():
                        occurrence_time = idx if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx)
                        
                        # Jeśli są dostępne regiony, utwórz rekord dla każdego regionu
                        # (ponieważ regiony są zagregowane dla całego okresu, nie dla konkretnych timestampów)
                        if available_regions:
                            # Dla każdego regionu utwórz rekord z tym samym occurrence_time
                            for region_name in available_regions:
                                sniff_records.append((
                                    measurement_id,
                                    region_name,
                                    occurrence_time
                                ))
                        else:
                            # Jeśli brak regionów, utwórz rekord bez regionu (tylko timestamp)
                            sniff_records.append((
                                measurement_id,
                                None,
                                occurrence_time
                            ))
                    
                    # Wykonaj batch insert
                    if sniff_records:
                        cur.executemany(insert_sniff, sniff_records)
                        conn.commit()
            
            return measurement_id
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd zapisu do bazy danych: {e}")
        conn.rollback()
        # Spróbuj zapisać przynajmniej informację o błędzie
        try:
            with conn.cursor() as cur:
                # Ogranicz vpn_country do 2 znaków (kod ISO 2) - zabezpieczenie przed długimi nazwami
                vpn_country_safe = vpn_country
                if vpn_country_safe:
                    vpn_country_safe = vpn_country_safe[:2].upper() if len(vpn_country_safe) > 2 else vpn_country_safe.upper()
                
                insert_error = """
                    INSERT INTO sentiment_measurement (
                        phrase_id, country_id, language_code, ip, vpn_country, error
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                error_msg = error_message if error_message else f"Błąd zapisu do bazy: {str(e)}"
                cur.execute(
                    insert_error,
                    (
                        phrase_data['id'],
                        phrase_data['country_id'],
                        phrase_data['language_code'],
                        ip,
                        vpn_country_safe,
                        error_msg
                    )
                )
                measurement_id = cur.fetchone()[0]
                conn.commit()
                return measurement_id
        except Exception as e2:
            if CONFIG_VERBOSE:
                print(f"    ✗ Nie udało się zapisać nawet informacji o błędzie: {e2}")
        return None


def log_result(phrase_data: Dict, ip: Optional[str], trends_data: Optional[Dict[str, Any]], vpn_info: Dict):
    """
    Wyświetla log z wynikiem zapytania wraz ze szczegółowymi danymi.
    
    Args:
        phrase_data: Dane frazy
        ip: Adres IP
        trends_data: Słownik z danymi z Google Trends (interest_value, time_data, stats, regions)
        vpn_info: Informacje o VPN
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    country = phrase_data['country_code']
    country_name = phrase_data['country_name']
    language = phrase_data['language_code']
    phrase = phrase_data['phrase']
    multiplier = phrase_data['multiplier']
    
    ip_display = ip if ip else "N/A"
    location_display = vpn_info.get('location', 'N/A')
    
    # Podstawowy log
    if trends_data is None:
        interest_display = "ERROR"
        log_line = (
            f"[{timestamp}] "
            f"Country: {country} ({country_name}) | "
            f"Language: {language} | "
            f"Phrase: \"{phrase}\" | "
            f"Multiplier: {multiplier:+.2f} | "
            f"IP: {ip_display} | "
            f"Location: {location_display} | "
            f"Interest (1h): {interest_display}"
        )
        print(log_line)
        return
    
    interest_value = trends_data.get('interest_value', 0)
    stats = trends_data.get('stats', {})
    time_data = trends_data.get('time_data', pd.DataFrame())
    regions = trends_data.get('regions', pd.DataFrame())
    
    # Podstawowy log
    log_line = (
        f"[{timestamp}] "
        f"Country: {country} ({country_name}) | "
        f"Language: {language} | "
        f"Phrase: \"{phrase}\" | "
        f"Multiplier: {multiplier:+.2f} | "
        f"IP: {ip_display} | "
        f"Location: {location_display} | "
        f"Interest (1h): {interest_value}"
    )
    print(log_line)
    
    # Statystyki
    if stats and stats.get('count', 0) > 0:
        print(f"  📊 Statystyki: count={stats['count']}, mean={stats['mean']:.2f}, std={stats['std']:.2f}")
    
    # Dokładne czasy wystąpień (tylko te z wartością > 0)
    if not time_data.empty and phrase in time_data.columns:
        time_with_values = time_data[time_data[phrase] > 0]
        if not time_with_values.empty:
            print(f"  ⏰ Wystąpienia w czasie (wartość > 0):")
            for idx, row in time_with_values.iterrows():
                timestamp_str = idx.strftime("%Y-%m-%d %H:%M:%S") if hasattr(idx, 'strftime') else str(idx)
                value = int(row[phrase])
                print(f"    {timestamp_str}: {value}")
    
    # Regiony z wartością > 0
    if not regions.empty and phrase in regions.columns:
        print(f"  🌍 Regiony z zainteresowaniem > 0 ({len(regions)} regionów):")
        for idx, row in regions.head(20).iterrows():  # Maksymalnie 20 regionów
            region_name = str(idx)
            value = int(row[phrase])
            print(f"    {region_name}: {value}")
        if len(regions) > 20:
            print(f"    ... i {len(regions) - 20} więcej regionów")


def parse_arguments():
    """Parsuje argumenty wiersza poleceń."""
    global CONFIG_NOT_ZERO_MULTIPLIER
    
    for arg in sys.argv[1:]:
        if arg.startswith('--not_zero_multiplier='):
            value = arg.split('=', 1)[1].lower()
            CONFIG_NOT_ZERO_MULTIPLIER = value in ('true', '1', 'yes', 'on')
        elif arg == '--not_zero_multiplier':
            CONFIG_NOT_ZERO_MULTIPLIER = True
        elif arg == '--not_zero_multiplier=false':
            CONFIG_NOT_ZERO_MULTIPLIER = False


def setup_logging():
    """Konfiguruje logowanie do pliku."""
    log_dir = os.path.join(os.path.dirname(__file__), '../../.dev/logs')
    os.makedirs(log_dir, exist_ok=True)
    
    if CONFIG_LOG_FILE:
        log_file = CONFIG_LOG_FILE
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'trends_sniffer_{timestamp}.log')
    
    # Konfiguruj logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Również na stdout
        ]
    )
    
    return log_file


def generate_system_report(error: Exception, traceback_str: str) -> str:
    """
    Generuje raport systemowy przy błędzie.
    
    Args:
        error: Wyjątek
        traceback_str: Traceback jako string
    
    Returns:
        Raport jako string
    """
    report = []
    report.append("="*100)
    report.append("RAPORT SYSTEMOWY - BŁĄD WYKONANIA")
    report.append("="*100)
    report.append(f"Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Błąd: {type(error).__name__}: {str(error)}")
    report.append("")
    report.append("TRACEBACK:")
    report.append("-"*100)
    report.append(traceback_str)
    report.append("-"*100)
    report.append("")
    report.append("INFORMACJE SYSTEMOWE:")
    report.append(f"  Python: {sys.version}")
    report.append(f"  Platforma: {sys.platform}")
    report.append(f"  Katalog roboczy: {os.getcwd()}")
    report.append(f"  Ścieżka skryptu: {__file__}")
    report.append("")
    
    # Informacje o VPN
    try:
        vpn_status = get_mullvad_status()
        report.append("STATUS VPN:")
        report.append(f"  Połączony: {vpn_status.get('connected', False)}")
        report.append(f"  Lokalizacja: {vpn_status.get('location', 'N/A')}")
        report.append(f"  IP: {vpn_status.get('ip', 'N/A')}")
        report.append("")
    except:
        pass
    
    # Informacje o bazie danych
    try:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Ukryj hasło
            safe_url = re.sub(r':([^:@]+)@', ':***@', database_url)
            report.append(f"  DATABASE_URL: {safe_url}")
    except:
        pass
    
    report.append("="*100)
    return "\n".join(report)


def process_phrases_cycle(conn) -> int:
    """
    Przetwarza jeden cykl fraz.
    
    Args:
        conn: Połączenie z bazą danych
    
    Returns:
        0 jeśli sukces, 1 jeśli błąd, -1 jeśli brak fraz do przetworzenia
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Pobierz frazy z bazy
        print("\nPobieranie fraz z bazy danych...")
        
        # Jeśli pomijamy ostatnio sprawdzane, spróbuj z różnymi oknami czasowymi
        recent_hours = 24
        phrases = []
        
        if CONFIG_RESUME_FROM_LAST:
            # Spróbuj z różnymi oknami czasowymi, jeśli brak fraz
            for hours in [24, 12, 6, 3, 1]:
                phrases = get_phrases_from_database(
                    conn,
                    limit=CONFIG_LIMIT_PHRASES,
                    country_filter=CONFIG_COUNTRY_FILTER,
                    not_zero_multiplier=CONFIG_NOT_ZERO_MULTIPLIER,
                    skip_recently_checked=CONFIG_RESUME_FROM_LAST,
                    recent_hours=hours
                )
                if phrases:
                    if hours < 24:
                        logger.info(f"Znaleziono {len(phrases)} fraz używając okna {hours}h zamiast 24h")
                        print(f"  ℹ Używam okna {hours}h (zamiast 24h) - znaleziono {len(phrases)} fraz")
                    break
                recent_hours = hours
        else:
            phrases = get_phrases_from_database(
                conn,
                limit=CONFIG_LIMIT_PHRASES,
                country_filter=CONFIG_COUNTRY_FILTER,
                not_zero_multiplier=CONFIG_NOT_ZERO_MULTIPLIER,
                skip_recently_checked=CONFIG_RESUME_FROM_LAST,
                recent_hours=recent_hours
            )
        
        print(f"✓ Znaleziono {len(phrases)} fraz do przetworzenia")
        
        if not phrases:
            print("\n✗ Brak fraz do przetworzenia (wszystkie kraje były sprawdzane w ostatnich 24h)")
            logger.info("Brak fraz do przetworzenia w tym cyklu - wszystkie kraje były sprawdzane")
            return -1  # Zwróć -1 aby oznaczyć brak fraz (nie błąd)
        
        # Sprawdź status VPN
        print("\nSprawdzanie statusu Mullvad VPN...")
        if CONFIG_VERBOSE:
            print(f"  Używam komendy: {MULLVAD_CMD}")
        
        vpn_status = get_mullvad_status()
        
        # Sprawdź czy mullvad jest dostępny
        if vpn_status.get('error') == 'mullvad_not_found':
            print("\n✗ BŁĄD: Komenda 'mullvad' nie została znaleziona!")
            print("  Upewnij się, że:")
            print("  1. Mullvad VPN jest zainstalowany")
            print("  2. Komenda 'mullvad' jest dostępna w PATH")
            print("  3. Lub dodaj ścieżkę do mullvad do zmiennej środowiskowej PATH")
            print("\n  Sprawdzane lokalizacje:")
            print("    - /usr/local/bin/mullvad")
            print("    - /opt/homebrew/bin/mullvad")
            print("    - /usr/bin/mullvad")
            print("    - /Applications/Mullvad VPN.app/Contents/Resources/mullvad")
            return 1
        
        if not vpn_status['connected']:
            print("⚠ VPN nie jest połączony, próba połączenia...")
            connect_result = subprocess.run(
                [MULLVAD_CMD, 'connect'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if connect_result.returncode != 0:
                print(f"  ⚠ Błąd podczas łączenia z VPN: {connect_result.stderr}")
            
            # Czekaj na połączenie (maksymalnie 15 sekund)
            max_wait = 15
            wait_interval = 1
            waited = 0
            connected = False
            
            while waited < max_wait:
                time.sleep(wait_interval)
                waited += wait_interval
                vpn_status = get_mullvad_status()
                if vpn_status['connected']:
                    connected = True
                    break
                if CONFIG_VERBOSE:
                    print(f"  ⏳ Oczekiwanie na połączenie VPN... ({waited}s/{max_wait}s)")
            
            if not connected:
                print("  ⚠ Nie udało się połączyć z VPN w ciągu 15 sekund")
        
        if vpn_status['connected']:
            print(f"✓ VPN połączony: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
        else:
            print("⚠ VPN nie jest połączony - kontynuowanie bez VPN")
            print("  Uwaga: Zapytania mogą być ograniczone przez Google Trends")
        
        # Inicjalizuj PyTrends
        print("\nInicjalizacja PyTrends...")
        pytrends = TrendReq(hl='en-US', tz=0, retries=2, backoff_factor=0.1)
        print("✓ PyTrends zainicjalizowany")
        
        # Przetwarzaj frazy
        print("\n" + "="*100)
        print("PRZETWARZANIE FRAZ")
        print("="*100)
        
        stats = {
            'processed': 0,
            'success': 0,
            'errors': 0,
            'vpn_switches': 0
        }
        
        query_count = 0
        last_query_time = time.time()
        
        current_vpn_country = None  # Śledź aktualny kraj VPN
        
        for i, phrase_data in enumerate(phrases, 1):
            # Przełącz VPN na kraj odpowiadający krajowi z tabeli
            target_country_code = phrase_data['country_code']
            mullvad_location = get_mullvad_location_code(target_country_code)
            
            # Przełącz VPN jeśli:
            # 1. To pierwsze zapytanie
            # 2. Kraj się zmienił
            # 3. Minęło N zapytań (dla bezpieczeństwa)
            should_switch = (
                current_vpn_country is None or
                current_vpn_country != target_country_code or
                (query_count > 0 and query_count % CONFIG_VPN_SWITCH_EVERY_N_QUERIES == 0)
            )
            
            if should_switch and mullvad_location:
                if CONFIG_VERBOSE:
                    print(f"\n  🔄 Przełączanie VPN na {target_country_code} ({mullvad_location})...")
                    logger.info(f"Przełączanie VPN na {target_country_code} ({mullvad_location})...")
                
                switch_success = switch_mullvad_location(mullvad_location)
                if switch_success:
                    vpn_status = get_mullvad_status()
                    current_vpn_country = target_country_code
                    stats['vpn_switches'] += 1
                    
                    if CONFIG_VERBOSE:
                        print(f"  ✓ VPN przełączony: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
                    logger.info(f"VPN przełączony: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
                else:
                    if CONFIG_VERBOSE:
                        print(f"  ⚠ Nie udało się przełączyć VPN na {mullvad_location}, używam aktualnego połączenia")
                    logger.warning(f"Nie udało się przełączyć VPN na {mullvad_location} dla kraju {target_country_code}")
            elif not mullvad_location:
                # Kraj nie jest dostępny w Mullvad - losuj dostępne połączenie
                if CONFIG_VERBOSE:
                    print(f"\n  ⚠ Kraj {target_country_code} nie jest dostępny w Mullvad, losuję dostępne połączenie...")
                logger.warning(f"Kraj {target_country_code} nie jest dostępny w Mullvad, losuję dostępne połączenie")
                
                switch_success = switch_mullvad_location(None)  # None = losowa lokalizacja
                if switch_success:
                    vpn_status = get_mullvad_status()
                    stats['vpn_switches'] += 1
                    if CONFIG_VERBOSE:
                        print(f"  ✓ VPN przełączony na losową lokalizację: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
                    logger.info(f"VPN przełączony na losową lokalizację: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
                else:
                    if CONFIG_VERBOSE:
                        print(f"  ⚠ Nie udało się przełączyć VPN na losową lokalizację, używam aktualnego połączenia")
                    logger.warning(f"Nie udało się przełączyć VPN na losową lokalizację dla kraju {target_country_code}")
            
            # Sprawdź limit zapytań na minutę
            current_time = time.time()
            time_since_last = current_time - last_query_time
            
            if time_since_last < (60.0 / CONFIG_QUERIES_PER_MINUTE):
                wait_time = (60.0 / CONFIG_QUERIES_PER_MINUTE) - time_since_last
                if CONFIG_VERBOSE:
                    print(f"  ⏳ Oczekiwanie {wait_time:.1f}s (limit {CONFIG_QUERIES_PER_MINUTE} zapytań/min)...")
                time.sleep(wait_time)
            
            # Pobierz aktualny IP
            current_ip = get_current_ip()
            if not current_ip:
                current_ip = vpn_status.get('ip')
            
            # Pobierz dane z Google Trends
            logger.info(f"Zapytanie: {phrase_data['country_code']} - \"{phrase_data['phrase']}\" (lang: {phrase_data['language_code']})")
            trends_data, is_rate_limit = get_trends_data(
                pytrends,
                phrase_data['phrase'],
                phrase_data['country_code'],
                phrase_data['language_code']
            )
            
            # Jeśli wystąpił błąd limitu zapytań, przełącz VPN i powtórz zapytanie
            if is_rate_limit:
                if CONFIG_VERBOSE:
                    print(f"  🔄 Limit zapytań wykryty - przełączanie VPN i powtarzanie zapytania...")
                
                # Przełącz VPN na losową lokalizację
                switch_mullvad_location()  # Losowa lokalizacja
                vpn_status = get_mullvad_status()
                stats['vpn_switches'] += 1
                current_vpn_country = None  # Reset, aby wymusić przełączenie na właściwy kraj
                
                # Poczekaj dłużej po przełączeniu
                time.sleep(CONFIG_DELAY_AFTER_VPN_SWITCH + 5)
                
                # Pobierz nowy IP
                current_ip = get_current_ip()
                if not current_ip:
                    current_ip = vpn_status.get('ip')
                
                if CONFIG_VERBOSE:
                    print(f"  ✓ VPN przełączony: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
                    print(f"  🔄 Powtarzanie zapytania dla: {phrase_data['country_code']} - \"{phrase_data['phrase']}\"...")
                
                # Przełącz VPN na właściwy kraj przed powtórzeniem
                mullvad_location = get_mullvad_location_code(phrase_data['country_code'])
                if mullvad_location:
                    switch_mullvad_location(mullvad_location)
                    time.sleep(CONFIG_DELAY_AFTER_VPN_SWITCH)
                    vpn_status = get_mullvad_status()
                    current_vpn_country = phrase_data['country_code']
                    current_ip = get_current_ip() or vpn_status.get('ip')
                
                # Powtórz zapytanie
                trends_data, is_rate_limit_retry = get_trends_data(
                    pytrends,
                    phrase_data['phrase'],
                    phrase_data['country_code'],
                    phrase_data['language_code']
                )
                
                if is_rate_limit_retry:
                    if CONFIG_VERBOSE:
                        print(f"  ⚠ Limit zapytań nadal aktywny po przełączeniu VPN - pomijam zapytanie")
                    stats['errors'] += 1
                    # Zapisz do bazy nawet przy błędzie
                    # Użyj kodu kraju z phrase_data (ISO 2) zamiast pełnej nazwy lokalizacji
                    vpn_country_code = phrase_data.get('country_code', None)
                    error_msg = "Limit zapytań PyTrends (HTTP 429) - nadal aktywny po przełączeniu VPN"
                    measurement_id = save_measurement_to_database(
                        conn,
                        phrase_data,
                        current_ip,
                        vpn_country_code,
                        None,
                        error_msg
                    )
                    if CONFIG_VERBOSE and measurement_id:
                        print(f"  💾 Zapisano do bazy (błąd limitu): measurement_id={measurement_id}")
                    log_result(phrase_data, current_ip, None, vpn_status)
                    query_count += 1
                    last_query_time = time.time()
                    # Dłuższe oczekiwanie przed następnym zapytaniem
                    time.sleep(30)
                    continue
            
            stats['processed'] += 1
            
            # Zapisz do bazy danych (zawsze, nawet jeśli błąd)
            # Użyj kodu kraju z phrase_data (ISO 2) zamiast pełnej nazwy lokalizacji
            vpn_country_code = phrase_data.get('country_code', None)
            error_msg = None if trends_data is not None else "Błąd pobierania danych z Google Trends"
            measurement_id = save_measurement_to_database(
                conn,
                phrase_data,
                current_ip,
                vpn_country_code,
                trends_data,
                error_msg
            )
            
            if measurement_id:
                logger.debug(f"Zapisano do bazy: measurement_id={measurement_id}, phrase_id={phrase_data['id']}")
            
            if trends_data is not None:
                stats['success'] += 1
                logger.info(f"Sukces: {phrase_data['country_code']} - \"{phrase_data['phrase']}\" | Interest: {trends_data.get('interest_value', 0)}")
                if CONFIG_VERBOSE and measurement_id:
                    print(f"  💾 Zapisano do bazy: measurement_id={measurement_id}")
                log_result(phrase_data, current_ip, trends_data, vpn_status)
            else:
                stats['errors'] += 1
                logger.warning(f"Błąd: {phrase_data['country_code']} - \"{phrase_data['phrase']}\" | Brak danych")
                if CONFIG_VERBOSE and measurement_id:
                    print(f"  💾 Zapisano do bazy (błąd): measurement_id={measurement_id}")
                log_result(phrase_data, current_ip, None, vpn_status)
            
            query_count += 1
            last_query_time = time.time()
            
            # Opóźnienie między zapytaniami
            if i < len(phrases):
                time.sleep(CONFIG_DELAY_BETWEEN_QUERIES)
        
        # Podsumowanie
        print("\n" + "="*100)
        print("PODSUMOWANIE")
        print("="*100)
        print(f"Przetworzono: {stats['processed']}")
        print(f"Sukces: {stats['success']}")
        print(f"Błędy: {stats['errors']}")
        print(f"Przełączeń VPN: {stats['vpn_switches']}")
        print("\n✓ Cykl zakończony pomyślnie!")
        logger.info(f"Cykl zakończony: przetworzono={stats['processed']}, sukces={stats['success']}, błędy={stats['errors']}, przełączeń VPN={stats['vpn_switches']}")
        return 0
    
    except KeyboardInterrupt:
        logger.warning("Przerwano przez użytkownika")
        print("\n\n⚠ Przerwano przez użytkownika")
        raise  # Przekaż wyjątek dalej, aby można było go obsłużyć w głównej pętli
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        
        # Loguj błąd
        logger.error(f"Błąd wykonania: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback:\n{traceback_str}")
        
        # Generuj raport systemowy
        report = generate_system_report(e, traceback_str)
        
        # Zapisz raport do pliku
        report_file = os.path.join(
            os.path.dirname(__file__), 
            '../../.dev/logs',
            f'error_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Raport systemowy zapisany do: {report_file}")
            print(f"\n✗ Błąd: {e}")
            print(f"  Raport systemowy zapisany do: {report_file}")
        except Exception as save_error:
            logger.error(f"Nie udało się zapisać raportu: {save_error}")
            print(f"\n✗ Błąd: {e}")
            print("\nRaport systemowy:")
            print(report)
        
        if CONFIG_VERBOSE:
            traceback.print_exc()
        return 1


def main():
    """Główna funkcja programu."""
    # Parsuj argumenty wiersza poleceń
    parse_arguments()
    
    # Konfiguruj logowanie
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*100)
    logger.info("POBIERANIE DANYCH Z GOOGLE TRENDS Z UŻYCIEM MULLVAD VPN")
    logger.info("="*100)
    logger.info(f"Limit zapytań: {CONFIG_QUERIES_PER_MINUTE} na minutę")
    logger.info(f"Opóźnienie między zapytaniami: {CONFIG_DELAY_BETWEEN_QUERIES} sekund")
    logger.info(f"Przełączanie VPN co: {CONFIG_VPN_SWITCH_EVERY_N_QUERIES} zapytań")
    logger.info(f"Zakres czasowy: {CONFIG_TIMEFRAME}")
    logger.info(f"Pomijaj frazy z multiplier=0.0: {CONFIG_NOT_ZERO_MULTIPLIER}")
    logger.info(f"Wznawiaj od ostatnio sprawdzonych: {CONFIG_RESUME_FROM_LAST}")
    logger.info(f"Tryb daemon: {CONFIG_DAEMON_MODE}")
    if CONFIG_DAEMON_MODE:
        logger.info(f"Interwał między cyklami: {CONFIG_CYCLE_INTERVAL}s ({CONFIG_CYCLE_INTERVAL/3600:.1f}h)")
    logger.info(f"Plik logu: {log_file}")
    logger.info("="*100)
    
    print("="*100)
    print("POBIERANIE DANYCH Z GOOGLE TRENDS Z UŻYCIEM MULLVAD VPN")
    print("="*100)
    print(f"Limit zapytań: {CONFIG_QUERIES_PER_MINUTE} na minutę")
    print(f"Opóźnienie między zapytaniami: {CONFIG_DELAY_BETWEEN_QUERIES} sekund")
    print(f"Przełączanie VPN co: {CONFIG_VPN_SWITCH_EVERY_N_QUERIES} zapytań")
    print(f"Zakres czasowy: {CONFIG_TIMEFRAME}")
    print(f"Pomijaj frazy z multiplier=0.0: {CONFIG_NOT_ZERO_MULTIPLIER}")
    print(f"Wznawiaj od ostatnio sprawdzonych: {CONFIG_RESUME_FROM_LAST}")
    print(f"Tryb daemon: {CONFIG_DAEMON_MODE}")
    if CONFIG_DAEMON_MODE:
        print(f"Interwał między cyklami: {CONFIG_CYCLE_INTERVAL}s ({CONFIG_CYCLE_INTERVAL/3600:.1f}h)")
    print(f"Plik logu: {log_file}")
    print("="*100)
    
    # Połącz z bazą danych (raz na początku)
    try:
        print("\nŁączenie z bazą danych...")
        conn = get_database_connection()
        print("✓ Połączono z bazą danych")
    except Exception as e:
        print(f"\n✗ Błąd połączenia: {e}")
        return 1
    
    running = True
    cycle_count = 0
    
    try:
        if CONFIG_DAEMON_MODE:
            print("\n🔄 Tryb daemon włączony - skrypt będzie działać w pętli")
            print("Naciśnij Ctrl+C aby zatrzymać\n")
            logger.info("Tryb daemon włączony - skrypt będzie działać w pętli")
        
        while running:
            cycle_count += 1
            cycle_start = datetime.now()
            
            print("\n" + "="*100)
            print(f"🔄 CYKL #{cycle_count} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*100)
            logger.info(f"Rozpoczęcie cyklu #{cycle_count} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
            
            try:
                result = process_phrases_cycle(conn)
                
                if result == -1:
                    # Brak fraz do przetworzenia - to nie jest błąd
                    if CONFIG_DAEMON_MODE:
                        wait_minutes = CONFIG_CYCLE_INTERVAL / 60
                        print(f"\n⏳ Brak fraz do przetworzenia. Czekam {wait_minutes:.1f} minut do następnego cyklu...")
                        logger.info(f"Brak fraz do przetworzenia. Czekam {CONFIG_CYCLE_INTERVAL}s do następnego cyklu")
                        
                        # Loguj co 5 minut podczas czekania, aby było widać że proces działa
                        wait_interval = 300  # 5 minut
                        waited = 0
                        try:
                            while waited < CONFIG_CYCLE_INTERVAL:
                                sleep_time = min(wait_interval, CONFIG_CYCLE_INTERVAL - waited)
                                time.sleep(sleep_time)
                                waited += sleep_time
                                remaining = CONFIG_CYCLE_INTERVAL - waited
                                if remaining > 0:
                                    logger.info(f"Czekam... pozostało {remaining}s ({remaining/60:.1f} min) do następnego cyklu")
                                    if CONFIG_VERBOSE:
                                        print(f"  ⏳ Czekam... pozostało {remaining/60:.1f} min do następnego cyklu")
                        except KeyboardInterrupt:
                            logger.info("Otrzymano KeyboardInterrupt podczas czekania")
                            raise
                        except Exception as e:
                            logger.error(f"Błąd podczas czekania: {e}")
                            # Kontynuuj mimo błędu
                            pass
                    else:
                        # Tryb jednorazowy - zakończ
                        print("\n✓ Zakończono (tryb jednorazowy)")
                        break
                elif result == 0:
                    # Sukces
                    if CONFIG_DAEMON_MODE:
                        wait_minutes = CONFIG_CYCLE_INTERVAL / 60
                        print(f"\n⏳ Cykl zakończony. Czekam {wait_minutes:.1f} minut do następnego cyklu...")
                        logger.info(f"Cykl #{cycle_count} zakończony. Czekam {CONFIG_CYCLE_INTERVAL}s do następnego cyklu")
                        
                        # Loguj co 5 minut podczas czekania, aby było widać że proces działa
                        wait_interval = 300  # 5 minut
                        waited = 0
                        try:
                            while waited < CONFIG_CYCLE_INTERVAL:
                                sleep_time = min(wait_interval, CONFIG_CYCLE_INTERVAL - waited)
                                time.sleep(sleep_time)
                                waited += sleep_time
                                remaining = CONFIG_CYCLE_INTERVAL - waited
                                if remaining > 0:
                                    logger.info(f"Czekam... pozostało {remaining}s ({remaining/60:.1f} min) do następnego cyklu")
                                    if CONFIG_VERBOSE:
                                        print(f"  ⏳ Czekam... pozostało {remaining/60:.1f} min do następnego cyklu")
                        except KeyboardInterrupt:
                            logger.info("Otrzymano KeyboardInterrupt podczas czekania")
                            raise
                        except Exception as e:
                            logger.error(f"Błąd podczas czekania: {e}")
                            # Kontynuuj mimo błędu
                            pass
                    else:
                        # Tryb jednorazowy - zakończ
                        print("\n✓ Zakończono (tryb jednorazowy)")
                        break
                else:
                    # Błąd - w trybie daemon kontynuuj, w trybie jednorazowym zakończ
                    if CONFIG_DAEMON_MODE:
                        print(f"\n⚠ Błąd w cyklu #{cycle_count}. Czekam 60 sekund przed ponowną próbą...")
                        logger.warning(f"Błąd w cyklu #{cycle_count}. Czekam 60s przed ponowną próbą")
                        time.sleep(60)
                    else:
                        print("\n✗ Zakończono z błędem (tryb jednorazowy)")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Otrzymano KeyboardInterrupt - zatrzymywanie...")
                print("\n\n⚠ Przerwano przez użytkownika")
                running = False
                break
            except Exception as e:
                logger.error(f"Nieoczekiwany błąd w głównej pętli: {e}")
                if CONFIG_DAEMON_MODE:
                    print(f"\n⚠ Nieoczekiwany błąd: {e}. Czekam 60 sekund przed ponowną próbą...")
                    time.sleep(60)
                else:
                    raise
    
    finally:
        conn.close()
        print("\n✓ Połączenie z bazą danych zamknięte")
        logger.info(f"Zakończono po {cycle_count} cyklach")


if __name__ == "__main__":
    sys.exit(main())

