# Table Monitor Daemon

Daemon monitorujący aktualizacje tabel w bazie danych. W przypadku wykrycia, że któraś z tabel nie jest aktualizowana, odtwarza dźwięk alarmowy i wysyła email z powiadomieniem.

## Funkcjonalność

- Sprawdza widok `v_table_stats` co 30 minut (domyślnie)
- Wykrywa tabele, które nie były aktualizowane dłużej niż określony próg (domyślnie 2 godziny)
- Odtwarza dźwięk alarmowy (na macOS używa `afplay` lub `say`)
- Wysyła email z informacją o problematycznych tabelach

## Konfiguracja

### Zmienne środowiskowe (.env)

Dodaj następujące zmienne do pliku `.env`:

```bash
# Baza danych (wymagane)
DATABASE_URL=postgresql://user:password@localhost:5432/database

# SMTP - konfiguracja email (wymagane do wysyłania emaili)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=twoj_email@gmail.com
SMTP_PASSWORD=twoje_haslo_aplikacji
SMTP_FROM=twoj_email@gmail.com
```

**Uwaga dla Gmail:**
- Musisz użyć hasła aplikacji, nie zwykłego hasła
- Włącz "Mniej bezpieczne aplikacje" lub użyj OAuth2
- Hasło aplikacji możesz wygenerować w ustawieniach konta Google

## Użycie

### Uruchomienie daemona

```bash
# Uruchom z domyślnymi ustawieniami (30 min interwał, 2h próg)
./scripts/start_table_monitor_daemon.sh

# Uruchom z własnymi parametrami
./scripts/start_table_monitor_daemon.sh --interval=1800 --threshold-hours=2 --email=octadecimal@octadecimal.pl

# Sprawdź status
./scripts/start_table_monitor_daemon.sh --status

# Zatrzymaj daemon
./scripts/start_table_monitor_daemon.sh --stop
```

### Bezpośrednie uruchomienie (bez skryptu shell)

```bash
python scripts/table_monitor_daemon.py
python scripts/table_monitor_daemon.py --interval=1800 --threshold-hours=2
python scripts/table_monitor_daemon.py --email=octadecimal@octadecimal.pl
python scripts/table_monitor_daemon.py --sound=/path/to/sound.aiff
```

## Parametry

- `--interval` - Interwał sprawdzania w sekundach (domyślnie: 1800 = 30 minut)
- `--threshold-hours` - Próg w godzinach - jeśli ostatnia aktualizacja starsza, wyślij alert (domyślnie: 2.0)
- `--email` - Adres email do wysyłania powiadomień (domyślnie: octadecimal@octadecimal.pl)
- `--sound` - Ścieżka do pliku dźwiękowego (domyślnie: systemowy dźwięk Basso na macOS)

## Monitorowane tabele

Daemon sprawdza następujące tabele:
- `sentiments_sniff`
- `ohlcv`
- `gdelt_sentiment`
- `dydx_traders`
- `dydx_perpetual_market_trades`

## Logi

Logi są zapisywane w:
```
logs/table_monitor_daemon_YYYYMMDD.log
```

## Przykład emaila

```
Temat: ⚠️ Alert: Problemy z aktualizacją tabel (2 tabel)

Wykryto problemy z aktualizacją tabel w bazie danych.

Data sprawdzenia: 2025-12-24 03:55:00 UTC
Próg: 2.0 godzin

Problematyczne tabele:

  • gdelt_sentiment
    - Liczba rekordów: 175,809
    - Ostatnia aktualizacja: 2025-12-22 19:20:37+01:00
    - Ostatnie wystąpienie: 2025-12-22 18:30:00+01:00
    - Opóźnienie: 32.58 godzin

  • dydx_traders
    - Liczba rekordów: 176
    - Ostatnia aktualizacja: 2025-12-23 22:50:50+01:00
    - Ostatnie wystąpienie: 2025-12-23 22:50:49+01:00
    - Opóźnienie: 5.07 godzin
```

## Rozwiązywanie problemów

### Daemon nie wysyła emaili

1. Sprawdź czy zmienne SMTP są ustawione w `.env`
2. Sprawdź logi: `tail -f logs/table_monitor_daemon_*.log`
3. Przetestuj połączenie SMTP ręcznie

### Dźwięk nie działa

1. Sprawdź czy plik dźwiękowy istnieje (domyślnie: `/System/Library/Sounds/Basso.aiff`)
2. Na macOS użyj `afplay /path/to/sound.aiff` do testu
3. Możesz użyć własnego pliku dźwiękowego: `--sound=/path/to/sound.aiff`

### Daemon nie wykrywa problemów

1. Sprawdź czy widok `v_table_stats` istnieje w bazie
2. Sprawdź czy próg (`--threshold-hours`) nie jest zbyt wysoki
3. Sprawdź logi daemona

