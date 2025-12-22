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
CONFIG_QUERIES_PER_MINUTE = 5                       # Limit zapytań na minutę (PyTrends)
CONFIG_DELAY_BETWEEN_QUERIES = 12                   # Opóźnienie między zapytaniami (sekundy)
CONFIG_DELAY_AFTER_VPN_SWITCH = 5                   # Opóźnienie po przełączeniu VPN (sekundy)
CONFIG_VPN_SWITCH_EVERY_N_QUERIES = 10              # Przełącz VPN co N zapytań
CONFIG_TIMEFRAME = 'now 1-H'                        # Zakres czasowy: ostatnia godzina
CONFIG_LIMIT_PHRASES = None                         # Limit fraz do przetworzenia (None = wszystkie)
CONFIG_COUNTRY_FILTER = None                        # Filtruj po kodzie kraju (None = wszystkie)

# ============================================================================
# KOD PROGRAMU
# ============================================================================

import sys
import os
import time
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
import requests

# Dodaj katalog główny projektu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

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
    try:
        result = subprocess.run(
            ['mullvad', 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        status_text = result.stdout
        
        status_info = {
            'connected': 'Connected' in status_text,
            'location': None,
            'ip': None,
            'relay': None
        }
        
        # Wyciągnij lokalizację
        location_match = re.search(r'Visible location:\s+(.+?)(?:\.|$)', status_text)
        if location_match:
            status_info['location'] = location_match.group(1).strip()
        
        # Wyciągnij IP
        ip_match = re.search(r'IPv4:\s+([\d.]+)', status_text)
        if ip_match:
            status_info['ip'] = ip_match.group(1)
        
        # Wyciągnij relay
        relay_match = re.search(r'Relay:\s+(.+?)(?:\n|$)', status_text)
        if relay_match:
            status_info['relay'] = relay_match.group(1).strip()
        
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
    }
    
    # Sprawdź specjalne mapowanie
    if country_code.upper() in special_mappings:
        return special_mappings[country_code.upper()]
    
    # Domyślnie użyj lowercase kodu kraju
    # Sprawdź czy Mullvad ma taką lokalizację
    try:
        result = subprocess.run(
            ['mullvad', 'relay', 'list'],
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
                ['mullvad', 'relay', 'set', 'location', location_code],
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
                ['mullvad', 'relay', 'set', 'location', 'any'],
                capture_output=True,
                timeout=10
            )
        
        # Rozłącz i połącz ponownie
        subprocess.run(['mullvad', 'disconnect'], capture_output=True, timeout=5)
        time.sleep(2)
        subprocess.run(['mullvad', 'connect'], capture_output=True, timeout=10)
        
        # Poczekaj na połączenie
        time.sleep(CONFIG_DELAY_AFTER_VPN_SWITCH)
        
        return True
    
    except Exception as e:
        if CONFIG_VERBOSE:
            print(f"  ⚠ Błąd przełączania VPN: {e}")
        return False


def get_phrases_from_database(conn, limit: Optional[int] = None, country_filter: Optional[str] = None) -> List[Dict]:
    """
    Pobiera frazy z bazy danych.
    
    Args:
        conn: Połączenie z bazą danych
        limit: Limit liczby fraz (None = wszystkie)
        country_filter: Filtr po kodzie kraju (None = wszystkie)
    
    Returns:
        Lista słowników z frazami
    """
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


def get_trends_data(pytrends, phrase: str, country_code: str, language_code: str) -> Tuple[Optional[int], bool]:
    """
    Pobiera dane z Google Trends dla frazy.
    
    Args:
        pytrends: Instancja TrendReq
        phrase: Fraza do wyszukania
        country_code: Kod kraju ISO 2
        language_code: Kod języka
    
    Returns:
        Tuple: (wartość zainteresowania (0-100) lub None, czy wystąpił błąd limitu)
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
        
        # Pobierz dane
        data = pytrends.interest_over_time()
        
        if data.empty:
            return 0, False
        
        # Zwróć średnią wartość z ostatniej godziny
        if phrase in data.columns:
            return int(data[phrase].mean()), False
        
        return 0, False
    
    except Exception as e:
        # Sprawdź czy to błąd limitu zapytań
        if is_rate_limit_error(e):
            if CONFIG_VERBOSE:
                print(f"    ⚠ Wykryto limit zapytań PyTrends: {e}")
            return None, True  # Zwróć None i flagę błędu limitu
        
        if CONFIG_VERBOSE:
            print(f"    ⚠ Błąd pobierania danych: {e}")
        return None, False  # Zwróć None ale bez flagi limitu


def log_result(phrase_data: Dict, ip: Optional[str], interest_value: Optional[int], vpn_info: Dict):
    """
    Wyświetla log z wynikiem zapytania.
    
    Args:
        phrase_data: Dane frazy
        ip: Adres IP
        interest_value: Wartość zainteresowania
        vpn_info: Informacje o VPN
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    country = phrase_data['country_code']
    country_name = phrase_data['country_name']
    language = phrase_data['language_code']
    phrase = phrase_data['phrase']
    multiplier = phrase_data['multiplier']
    
    ip_display = ip if ip else "N/A"
    interest_display = interest_value if interest_value is not None else "ERROR"
    location_display = vpn_info.get('location', 'N/A')
    
    # Format logu
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


def main():
    """Główna funkcja programu."""
    print("="*100)
    print("POBIERANIE DANYCH Z GOOGLE TRENDS Z UŻYCIEM MULLVAD VPN")
    print("="*100)
    print(f"Limit zapytań: {CONFIG_QUERIES_PER_MINUTE} na minutę")
    print(f"Opóźnienie między zapytaniami: {CONFIG_DELAY_BETWEEN_QUERIES} sekund")
    print(f"Przełączanie VPN co: {CONFIG_VPN_SWITCH_EVERY_N_QUERIES} zapytań")
    print(f"Zakres czasowy: {CONFIG_TIMEFRAME}")
    print("="*100)
    
    # Połącz z bazą danych
    try:
        print("\nŁączenie z bazą danych...")
        conn = get_database_connection()
        print("✓ Połączono z bazą danych")
    except Exception as e:
        print(f"\n✗ Błąd połączenia: {e}")
        return 1
    
    try:
        # Pobierz frazy z bazy
        print("\nPobieranie fraz z bazy danych...")
        phrases = get_phrases_from_database(
            conn,
            limit=CONFIG_LIMIT_PHRASES,
            country_filter=CONFIG_COUNTRY_FILTER
        )
        print(f"✓ Znaleziono {len(phrases)} fraz do przetworzenia")
        
        if not phrases:
            print("\n✗ Brak fraz do przetworzenia")
            return 0
        
        # Sprawdź status VPN
        print("\nSprawdzanie statusu Mullvad VPN...")
        vpn_status = get_mullvad_status()
        if not vpn_status['connected']:
            print("⚠ VPN nie jest połączony, próba połączenia...")
            subprocess.run(['mullvad', 'connect'], capture_output=True, timeout=10)
            time.sleep(3)
            vpn_status = get_mullvad_status()
        
        if vpn_status['connected']:
            print(f"✓ VPN połączony: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
        else:
            print("⚠ VPN nie jest połączony - kontynuowanie bez VPN")
        
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
                
                switch_success = switch_mullvad_location(mullvad_location)
                if switch_success:
                    vpn_status = get_mullvad_status()
                    current_vpn_country = target_country_code
                    stats['vpn_switches'] += 1
                    
                    if CONFIG_VERBOSE:
                        print(f"  ✓ VPN przełączony: {vpn_status.get('location', 'N/A')} ({vpn_status.get('ip', 'N/A')})")
                else:
                    if CONFIG_VERBOSE:
                        print(f"  ⚠ Nie udało się przełączyć VPN na {mullvad_location}, używam aktualnego połączenia")
            elif not mullvad_location:
                if CONFIG_VERBOSE and i == 1:
                    print(f"  ⚠ Kraj {target_country_code} nie jest dostępny w Mullvad, używam aktualnego połączenia")
            
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
            interest_value, is_rate_limit = get_trends_data(
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
                interest_value, is_rate_limit_retry = get_trends_data(
                    pytrends,
                    phrase_data['phrase'],
                    phrase_data['country_code'],
                    phrase_data['language_code']
                )
                
                if is_rate_limit_retry:
                    if CONFIG_VERBOSE:
                        print(f"  ⚠ Limit zapytań nadal aktywny po przełączeniu VPN - pomijam zapytanie")
                    stats['errors'] += 1
                    log_result(phrase_data, current_ip, None, vpn_status)
                    query_count += 1
                    last_query_time = time.time()
                    # Dłuższe oczekiwanie przed następnym zapytaniem
                    time.sleep(30)
                    continue
            
            stats['processed'] += 1
            
            if interest_value is not None:
                stats['success'] += 1
                log_result(phrase_data, current_ip, interest_value, vpn_status)
            else:
                stats['errors'] += 1
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
        print("\n✓ Zakończono pomyślnie!")
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠ Przerwano przez użytkownika")
        return 1
    
    except Exception as e:
        print(f"\n✗ Błąd: {e}")
        import traceback
        if CONFIG_VERBOSE:
            traceback.print_exc()
        return 1
    
    finally:
        conn.close()
        print("\n✓ Połączenie z bazą danych zamknięte")


if __name__ == "__main__":
    sys.exit(main())

