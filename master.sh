#!/bin/bash
# ============================================================================
# Master Daemon Controller
# ============================================================================
# Skrypt kontrolujący pracę wszystkich daemonów w systemie.
# Monitoruje daemony, próbuje naprawić problemy (restart daemona, VPN, PostgreSQL),
# wysyła powiadomienia email i odtwarza dźwięki alarmowe.
#
# Użycie:
#   ./master.sh --all                                    # Wszystkie daemony
#   ./master.sh --dydx_perpetual_market_trades_service   # Tylko jeden daemon
#   ./master.sh --dydx_perpetual_market_trades_service --trends_sniffer_service
# ============================================================================

set -euo pipefail

# Kolory dla outputu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Katalogi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"  # Katalog główny projektu (master.sh jest w katalogu głównym)
DAEMONS_DIR="${PROJECT_DIR}/daemons"
LOG_DIR="${PROJECT_DIR}/.dev/logs"
STATE_DIR="${PROJECT_DIR}/.dev/state"
PID_FILE="${LOG_DIR}/master_daemon.pid"
ENV_FILE="${PROJECT_DIR}/.env"  # Plik .env zawsze w katalogu głównym

# Utwórz katalogi
mkdir -p "$LOG_DIR"
mkdir -p "$STATE_DIR"

# Konfiguracja
CHECK_INTERVAL=300          # Sprawdzaj co 5 minut
ALERT_THRESHOLD=1800        # 30 minut - próg dla alertów email/dźwięk
EMAIL_RECIPIENT="octadecimal@octadecimal.pl"
SOUND_FILE="/System/Library/Sounds/Basso.aiff"

# Logowanie
LOG_FILE="${LOG_DIR}/master_daemon_$(date +%Y%m%d).log"
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo -e "$message" | tee -a "$LOG_FILE"
}

log_info() {
    log "${CYAN}[INFO]${NC} $*"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    log "${RED}[ERROR]${NC} $*"
}

# ============================================================================
# Konfiguracja daemonów
# ============================================================================

# Lista wszystkich daemonów
ALL_DAEMONS="dydx_perpetual_market_trades_service dydx_top_traders_observer_service trends_sniffer_service btcusdc_updater gdelt_sentiment_daemon market_indices_daemon api_server docs_server database_backup_daemon"

# Funkcja zwracająca konfigurację daemona (kompatybilna z bash 3.2)
get_daemon_config() {
    local daemon_name=$1
    local key=$2
    
    case "$daemon_name" in
        dydx_perpetual_market_trades_service)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/dydx_perpetual_market_trades_service.sh" ;;
                check_method) echo "launchctl" ;;
                service_name) echo "com.octadecimal.dydx-perpetual-market-trades" ;;
                table) echo "dydx_perpetual_market_trades" ;;
                progress_table) echo "dydx_perpetual_market_trades_progress" ;;
                date_column) echo "observed_at" ;;
                *) return 1 ;;
            esac
            ;;
        dydx_top_traders_observer_service)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/dydx_top_traders_observer_service.sh" ;;
                check_method) echo "launchctl" ;;
                service_name) echo "com.octadecimal.dydx-top-traders-observer" ;;
                table) echo "dydx_fills" ;;
                date_column) echo "observed_at" ;;
                *) return 1 ;;
            esac
            ;;
        trends_sniffer_service)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/trends_sniffer_service.sh" ;;
                check_method) echo "launchctl" ;;
                service_name) echo "com.octadecimal.trends-sniffer" ;;
                table) echo "sentiment_measurement" ;;
                date_column) echo "created_at" ;;
                *) return 1 ;;
            esac
            ;;
        btcusdc_updater)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/start_btcusdc_updater.sh" ;;
                check_method) echo "pid" ;;
                pid_file) echo "${LOG_DIR}/btcusdc_updater.pid" ;;
                table) echo "ohlcv" ;;
                date_column) echo "created_at" ;;
                *) return 1 ;;
            esac
            ;;
        gdelt_sentiment_daemon)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/start_gdelt_sentiment_daemon.sh" ;;
                check_method) echo "pid" ;;
                pid_file) echo "${LOG_DIR}/gdelt_sentiment_daemon.pid" ;;
                table) echo "gdelt_sentiment" ;;
                date_column) echo "created_at" ;;
                *) return 1 ;;
            esac
            ;;
        market_indices_daemon)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/start_market_indices_daemon.sh" ;;
                check_method) echo "pid" ;;
                pid_file) echo "${LOG_DIR}/market_indices_daemon.pid" ;;
                table) echo "market_indices" ;;
                date_column) echo "timestamp" ;;
                *) return 1 ;;
            esac
            ;;
        api_server)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/start_api_server.sh" ;;
                check_method) echo "port" ;;
                port) echo "8000" ;;
                table) echo "" ;;
                date_column) echo "" ;;
                *) return 1 ;;
            esac
            ;;
        docs_server)
            case "$key" in
                service_script) echo "${DAEMONS_DIR}/start_docs_server.sh" ;;
                check_method) echo "port" ;;
                port) echo "8080" ;;
                table) echo "" ;;
                date_column) echo "" ;;
                *) return 1 ;;
            esac
            ;;
        *)
            return 1
            ;;
    esac
}

# Sprawdź czy daemon istnieje w konfiguracji
is_valid_daemon() {
    local daemon_name=$1
    get_daemon_config "$daemon_name" "service_script" > /dev/null 2>&1
}

# Sprawdź czy daemon działa (launchctl)
check_daemon_launchctl() {
    local service_name=$1
    if launchctl list | grep -q "$service_name" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Sprawdź czy daemon działa (PID file)
check_daemon_pid() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Sprawdź czy daemon działa (port)
check_daemon_port() {
    local port=$1
    if lsof -i ":$port" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Uruchom panel zarządzania daemonami jeśli nie działa
start_daemon_panel_if_needed() {
    local panel_port=8090
    local panel_script="${DAEMONS_DIR}/start_daemon_panel.sh"
    local panel_pid_file="${LOG_DIR}/daemon_panel.pid"
    
    # Sprawdź czy panel już działa
    if check_daemon_port "$panel_port"; then
        log_info "Panel zarządzania daemonami już działa na porcie $panel_port"
        return 0
    fi
    
    # Sprawdź czy skrypt istnieje
    if [ ! -f "$panel_script" ]; then
        log_warning "Skrypt panelu nie istnieje: $panel_script"
        return 1
    fi
    
    log_info "Uruchamianie panelu zarządzania daemonami na porcie $panel_port..."
    
    # Uruchom panel w tle
    cd "$PROJECT_DIR"
    DAEMON_PANEL_BACKGROUND=true nohup bash "$panel_script" > "${LOG_DIR}/daemon_panel.log" 2>&1 &
    local panel_pid=$!
    echo $panel_pid > "$panel_pid_file"
    
    # Poczekaj chwilę i sprawdź czy się uruchomił
    sleep 3
    
    if check_daemon_port "$panel_port"; then
        log_success "Panel zarządzania daemonami uruchomiony (PID: $panel_pid)"
        log_info "Panel dostępny pod: http://localhost:$panel_port"
        return 0
    else
        log_error "Nie udało się uruchomić panelu zarządzania daemonami"
        log_info "Sprawdź logi: ${LOG_DIR}/daemon_panel.log"
        rm -f "$panel_pid_file"
        return 1
    fi
}

# Sprawdź czy daemon działa
is_daemon_running() {
    local daemon_name=$1
    local check_method=$(get_daemon_config "$daemon_name" "check_method")
    
    case "$check_method" in
        launchctl)
            local service_name=$(get_daemon_config "$daemon_name" "service_name")
            check_daemon_launchctl "$service_name"
            ;;
        pid)
            local pid_file=$(get_daemon_config "$daemon_name" "pid_file")
            check_daemon_pid "$pid_file"
            ;;
        port)
            local port=$(get_daemon_config "$daemon_name" "port")
            check_daemon_port "$port"
            ;;
        *)
            return 1
            ;;
    esac
}

# Uruchom daemon
start_daemon() {
    local daemon_name=$1
    local service_script=$(get_daemon_config "$daemon_name" "service_script")
    
    if [ ! -f "$service_script" ]; then
        log_error "Skrypt daemona nie istnieje: $service_script"
        return 1
    fi
    
    log_info "Uruchamianie daemona: $daemon_name"
    
    # Dla launchctl services
    if [[ "$service_script" == *"_service.sh" ]]; then
        "$service_script" --start > /dev/null 2>&1
    else
        # Dla zwykłych skryptów - uruchom w tle
        cd "$PROJECT_DIR"
        nohup bash "$service_script" > "${LOG_DIR}/${daemon_name}.log" 2>&1 &
        local pid=$!
        
        # Zapisz PID jeśli daemon używa PID file
        local pid_file=$(get_daemon_config "$daemon_name" "pid_file")
        if [ -n "$pid_file" ]; then
            echo "$pid" > "$pid_file"
        fi
    fi
    
    sleep 3
    
    sleep 2
    
    if is_daemon_running "$daemon_name"; then
        log_success "Daemon $daemon_name uruchomiony"
        return 0
    else
        log_error "Nie udało się uruchomić daemona $daemon_name"
        log_info "Sprawdź:"
        log_info "  - Czy skrypt $service_script istnieje i jest wykonywalny?"
        log_info "  - Czy są wymagane uprawnienia?"
        log_info "  - Sprawdź logi: ${LOG_DIR}/${daemon_name}.log"
        
        # Sprawdź logi jeśli istnieją
        if [ -f "${LOG_DIR}/${daemon_name}.log" ]; then
            log_info "Ostatnie linie z logów:"
            tail -n 5 "${LOG_DIR}/${daemon_name}.log" 2>/dev/null | while IFS= read -r line; do
                log_info "  $line"
            done || true
        fi
        
        return 1
    fi
}

# Zatrzymaj daemon
stop_daemon() {
    local daemon_name=$1
    local service_script=$(get_daemon_config "$daemon_name" "service_script")
    
    log_info "Zatrzymywanie daemona: $daemon_name"
    
    if [[ "$service_script" == *"_service.sh" ]]; then
        "$service_script" --stop > /dev/null 2>&1
    else
        local pid_file=$(get_daemon_config "$daemon_name" "pid_file")
        if [ -n "$pid_file" ] && [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file" 2>/dev/null)
            if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                kill "$pid" 2>/dev/null || true
                sleep 2
                if ps -p "$pid" > /dev/null 2>&1; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
            rm -f "$pid_file"
        fi
    fi
    
    sleep 2
}

# Restart daemon
restart_daemon() {
    local daemon_name=$1
    log_info "Restartowanie daemona: $daemon_name"
    stop_daemon "$daemon_name"
    sleep 2
    start_daemon "$daemon_name"
}

# Sprawdź czy PostgreSQL działa
check_postgresql() {
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Restart PostgreSQL (macOS)
restart_postgresql() {
    log_warning "Próba restartu PostgreSQL..."
    
    # Spróbuj różnych metod w zależności od instalacji
    if command -v brew > /dev/null 2>&1; then
        brew services restart postgresql@14 2>/dev/null || \
        brew services restart postgresql@15 2>/dev/null || \
        brew services restart postgresql 2>/dev/null || true
    fi
    
    # Spróbuj przez launchctl
    launchctl stop org.postgresql.postgres 2>/dev/null || true
    sleep 2
    launchctl start org.postgresql.postgres 2>/dev/null || true
    
    sleep 5
    
    if check_postgresql; then
        log_success "PostgreSQL zrestartowany"
        return 0
    else
        log_error "Nie udało się zrestartować PostgreSQL"
        return 1
    fi
}

# Sprawdź czy Mullvad VPN działa
check_vpn() {
    if command -v mullvad > /dev/null 2>&1; then
        if mullvad status 2>/dev/null | grep -qi "connected"; then
            return 0
        fi
    fi
    return 1
}

# Restart Mullvad VPN
restart_vpn() {
    log_warning "Próba restartu Mullvad VPN..."
    
    if ! command -v mullvad > /dev/null 2>&1; then
        log_error "Mullvad CLI nie jest dostępny"
        return 1
    fi
    
    mullvad disconnect > /dev/null 2>&1 || true
    sleep 3
    mullvad connect > /dev/null 2>&1 || true
    
    sleep 5
    
    if check_vpn; then
        log_success "Mullvad VPN zrestartowany"
        return 0
    else
        log_error "Nie udało się zrestartować Mullvad VPN"
        return 1
    fi
}

# Odtwórz dźwięk alarmowy
play_alert_sound() {
    local error_output=""
    if [ -f "$SOUND_FILE" ]; then
        error_output=$(afplay "$SOUND_FILE" 2>&1)
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            return 0
        else
            echo "$error_output" >&2
            return $exit_code
        fi
    else
        error_output=$(say "Alert! Daemon problem detected." 2>&1)
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            return 0
        else
            echo "$error_output" >&2
            return $exit_code
        fi
    fi
}

# Test dźwięku alarmowego
test_alert_sound() {
    log_info "Testowanie dźwięku alarmowego..."
    log_info "Plik dźwiękowy: $SOUND_FILE"
    
    if [ ! -f "$SOUND_FILE" ]; then
        log_warning "Plik dźwiękowy nie istnieje: $SOUND_FILE"
        log_info "Używam alternatywnej metody: say"
    fi
    
    local error_output
    error_output=$(play_alert_sound 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Dźwięk alarmowy odtworzony pomyślnie"
        return 0
    else
        log_error "Nie udało się odtworzyć dźwięku alarmowego"
        if [ -n "$error_output" ]; then
            log_error "Szczegóły błędu: $error_output"
        fi
        log_info "Sprawdź:"
        log_info "  - Czy plik $SOUND_FILE istnieje?"
        log_info "  - Czy masz uprawnienia do odtwarzania dźwięku?"
        log_info "  - Czy komenda 'say' jest dostępna?"
        return 1
    fi
}

# Wyślij email z alertem
send_alert_email() {
    local daemon_name=$1
    local problem_description=$2
    local duration_minutes=$3
    
    # Sprawdź konfigurację SMTP z .env (zawsze z katalogu głównego projektu)
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Brak pliku .env w katalogu głównym projektu: $ENV_FILE"
        log_info "Utwórz plik .env w katalogu głównym z konfiguracją SMTP"
        return 1
    fi
    
    # Załaduj .env ignorując błędy parsowania
    set +e
    source "$ENV_FILE" 2>/dev/null
    set -e
    
    if [ -z "${SMTP_USER:-}" ] || [ -z "${SMTP_PASSWORD:-}" ]; then
        log_warning "Brak konfiguracji SMTP - pomijam wysyłanie emaila"
        return 1
    fi
    
    local subject="⚠️ Alert: Problem z daemonem $daemon_name"
    local body="Wykryto problem z daemonem $daemon_name.

Problem: $problem_description
Czas trwania: $duration_minutes minut
Data: $(date '+%Y-%m-%d %H:%M:%S')

Próby naprawy zostały wykonane, ale problem nadal występuje.
Proszę sprawdzić logi i stan systemu.

Logi: ${LOG_DIR}/master_daemon_$(date +%Y%m%d).log"
    
    # Wyślij email przez Python (prostsze niż przez bash)
    # Eksportuj zmienne środowiskowe dla Pythona
    export SMTP_HOST="${SMTP_HOST:-smtp.gmail.com}"
    export SMTP_PORT="${SMTP_PORT:-587}"
    export SMTP_USER
    export SMTP_PASSWORD
    export SMTP_FROM="${SMTP_FROM:-$SMTP_USER}"
    
    local email_error_output
    email_error_output=$(python3 << PYEOF 2>&1
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.getenv('SMTP_PORT', '587'))
smtp_user = os.getenv('SMTP_USER')
smtp_password = os.getenv('SMTP_PASSWORD')
smtp_from = os.getenv('SMTP_FROM', smtp_user)

if not smtp_user or not smtp_password:
    print("BŁĄD: Brak SMTP_USER lub SMTP_PASSWORD w zmiennych środowiskowych", file=sys.stderr)
    sys.exit(1)

try:
    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = '$EMAIL_RECIPIENT'
    msg['Subject'] = '$subject'
    msg.attach(MIMEText('''$body''', 'plain', 'utf-8'))
    
    print(f"Łączenie z {smtp_host}:{smtp_port}...", file=sys.stderr)
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        print("Rozpoczynam TLS...", file=sys.stderr)
        server.starttls()
        print(f"Logowanie jako {smtp_user}...", file=sys.stderr)
        server.login(smtp_user, smtp_password)
        print("Wysyłanie wiadomości...", file=sys.stderr)
        server.send_message(msg)
    print("SUCCESS: Email wysłany pomyślnie", file=sys.stderr)
    sys.exit(0)
except smtplib.SMTPAuthenticationError as e:
    print(f"BŁĄD_AUTENTYKACJI: {e}", file=sys.stderr)
    sys.exit(1)
except smtplib.SMTPConnectError as e:
    print(f"BŁĄD_POŁĄCZENIA: Nie można połączyć z {smtp_host}:{smtp_port} - {e}", file=sys.stderr)
    sys.exit(1)
except smtplib.SMTPException as e:
    print(f"BŁĄD_SMTP: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"BŁĄD_NIEOCZEKIWANY: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
PYEOF
    )
    local email_exit_code=$?
    
    if [ $email_exit_code -eq 0 ]; then
        log_success "Email wysłany do $EMAIL_RECIPIENT"
        return 0
    else
        log_error "Nie udało się wysłać emaila"
        if [ -n "$email_error_output" ]; then
            echo ""
            log_error "Szczegóły błędu:"
            echo "$email_error_output" | while IFS= read -r line; do
                log_error "  $line"
            done
        fi
        log_info "Sprawdź konfigurację SMTP w pliku .env:"
        log_info "  - SMTP_HOST=${SMTP_HOST:-BRAK}"
        log_info "  - SMTP_PORT=${SMTP_PORT:-BRAK}"
        log_info "  - SMTP_USER=${SMTP_USER:-BRAK}"
        log_info "  - SMTP_PASSWORD=${SMTP_PASSWORD:+USTAWIONE (ukryte)}"
        log_info "  - SMTP_FROM=${SMTP_FROM:-BRAK}"
        return 1
    fi
}

# Test wysyłki emaila
test_alert_email() {
    log_info "Testowanie wysyłki emaila..."
    log_info "Odbiorca: $EMAIL_RECIPIENT"
    
    # Sprawdź konfigurację przed testem (zawsze z katalogu głównego projektu)
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Brak pliku .env w katalogu głównym projektu: $ENV_FILE"
        log_info "Utwórz plik .env w katalogu głównym z konfiguracją SMTP"
        return 1
    fi
    
    set +e
    source "$ENV_FILE" 2>/dev/null
    set -e
    
    if [ -z "${SMTP_USER:-}" ]; then
        log_error "Brak SMTP_USER w pliku .env"
        return 1
    fi
    
    if [ -z "${SMTP_PASSWORD:-}" ]; then
        log_error "Brak SMTP_PASSWORD w pliku .env"
        return 1
    fi
    
    log_info "Konfiguracja SMTP:"
    log_info "  - Host: ${SMTP_HOST:-smtp.gmail.com}"
    log_info "  - Port: ${SMTP_PORT:-587}"
    log_info "  - User: ${SMTP_USER}"
    log_info "  - From: ${SMTP_FROM:-${SMTP_USER}}"
    
    local test_daemon="TEST_DAEMON"
    local test_description="To jest test wysyłki emaila z master.sh"
    local test_duration=0
    
    if send_alert_email "$test_daemon" "$test_description" "$test_duration"; then
        log_success "Email testowy wysłany pomyślnie do $EMAIL_RECIPIENT"
        return 0
    else
        log_error "Nie udało się wysłać emaila testowego"
        return 1
    fi
}

# Sprawdź i uzupełnij braki w tabelach
check_and_fill_gaps() {
    local daemon_name=$1
    local table=$(get_daemon_config "$daemon_name" "table")
    local date_column=$(get_daemon_config "$daemon_name" "date_column")
    local progress_table=$(get_daemon_config "$daemon_name" "progress_table")
    local progress_date_column=$(get_daemon_config "$daemon_name" "date_column")
    
    if [ -z "$table" ] || [ -z "$date_column" ]; then
        return 0  # Ten daemon nie wymaga uzupełniania braków
    fi
    
    log_info "Sprawdzanie braków w tabeli $table dla daemona $daemon_name..."
    
    # Sprawdź ostatnią datę w bazie i porównaj z oczekiwaną
    python3 << PYEOF
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg2

table = "$table"
date_column = "$date_column"

# Załaduj .env z katalogu głównego projektu
project_dir = "$PROJECT_DIR"
env_path = os.path.join(project_dir, ".env")
load_dotenv(dotenv_path=env_path)

database_url = os.getenv('DATABASE_URL')
if not database_url:
    sys.exit(1)

try:
    conn = psycopg2.connect(database_url)
    
    # Sprawdź ostatnią datę w tabeli
    with conn.cursor() as cur:
        cur.execute(f"SELECT MAX({date_column}) FROM {table}")
        result = cur.fetchone()
        last_date = result[0] if result and result[0] else None
        
        if last_date:
            # Konwertuj na datetime jeśli to string
            if isinstance(last_date, str):
                try:
                    last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
                except:
                    # Fallback - użyj prostego parsowania
                    from datetime import datetime as dt
                    try:
                        last_date = dt.strptime(last_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
                        last_date = last_date.replace(tzinfo=timezone.utc)
                    except:
                        print(f"Nie można sparsować daty: {last_date}")
                        sys.exit(1)
            
            # Upewnij się że ma timezone
            if last_date.tzinfo is None:
                last_date = last_date.replace(tzinfo=timezone.utc)
            
            # Sprawdź czy są braki (ostatnia data starsza niż 2 godziny)
            now = datetime.now(timezone.utc)
            gap = (now - last_date).total_seconds() / 3600
            
            if gap > 2:
                print(f"Wykryto brak: ostatnia data {last_date}, gap: {gap:.2f} godzin")
                sys.exit(1)  # Są braki
            else:
                print(f"Brak braków: ostatnia data {last_date}, gap: {gap:.2f} godzin")
                sys.exit(0)  # Brak braków
        else:
            print("Brak danych w tabeli")
            sys.exit(1)  # Brak danych = są braki
    
    conn.close()
except Exception as e:
    print(f"Błąd: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF
    
    local has_gaps=$?
    
    # Ignoruj błędy - wykrycie braków to nie błąd, tylko informacja
    if [ $has_gaps -eq 1 ]; then
        log_warning "Wykryto braki w tabeli $table - daemon powinien je uzupełnić po wznowieniu"
        # Zapisz informację o brakach do pliku state
        echo "$(date +%s):$daemon_name:$table" >> "${STATE_DIR}/gaps_detected.txt" 2>/dev/null || true
    fi
    
    # Zawsze zwracaj sukces - wykrycie braków nie jest błędem
    return 0
}

# ============================================================================
# Główna logika monitorowania
# ============================================================================

# Stany daemonów (używamy plików zamiast tablic asocjacyjnych)
get_daemon_state() {
    local daemon_name=$1
    local state_file="${STATE_DIR}/daemon_state_${daemon_name}.txt"
    if [ -f "$state_file" ]; then
        cat "$state_file"
    else
        echo "unknown"
    fi
}

set_daemon_state() {
    local daemon_name=$1
    local state=$2
    local state_file="${STATE_DIR}/daemon_state_${daemon_name}.txt"
    echo "$state" > "$state_file"
}

get_daemon_failure_time() {
    local daemon_name=$1
    local time_file="${STATE_DIR}/daemon_failure_time_${daemon_name}.txt"
    if [ -f "$time_file" ]; then
        cat "$time_file"
    else
        echo ""
    fi
}

set_daemon_failure_time() {
    local daemon_name=$1
    local time=$2
    local time_file="${STATE_DIR}/daemon_failure_time_${daemon_name}.txt"
    if [ -n "$time" ]; then
        echo "$time" > "$time_file"
    else
        rm -f "$time_file"
    fi
}

get_daemon_restart_count() {
    local daemon_name=$1
    local count_file="${STATE_DIR}/daemon_restart_count_${daemon_name}.txt"
    if [ -f "$count_file" ]; then
        cat "$count_file"
    else
        echo "0"
    fi
}

set_daemon_restart_count() {
    local daemon_name=$1
    local count=$2
    local count_file="${STATE_DIR}/daemon_restart_count_${daemon_name}.txt"
    echo "$count" > "$count_file"
}

get_daemon_last_alert_time() {
    local daemon_name=$1
    local alert_file="${STATE_DIR}/daemon_last_alert_time_${daemon_name}.txt"
    if [ -f "$alert_file" ]; then
        cat "$alert_file"
    else
        echo ""
    fi
}

set_daemon_last_alert_time() {
    local daemon_name=$1
    local time=$2
    local alert_file="${STATE_DIR}/daemon_last_alert_time_${daemon_name}.txt"
    if [ -n "$time" ]; then
        echo "$time" > "$alert_file"
    else
        rm -f "$alert_file"
    fi
}

# Inicjalizuj stany daemonów
init_daemon_states() {
    for daemon_name in $ALL_DAEMONS; do
        set_daemon_state "$daemon_name" "unknown"
        set_daemon_failure_time "$daemon_name" ""
        set_daemon_restart_count "$daemon_name" "0"
        set_daemon_last_alert_time "$daemon_name" ""
    done
}

# Sprawdź daemon i podejmij akcje naprawcze
check_and_fix_daemon() {
    local daemon_name=$1
    
    if is_daemon_running "$daemon_name"; then
        # Daemon działa
        local current_state=$(get_daemon_state "$daemon_name")
        if [ "$current_state" != "running" ]; then
            log_success "Daemon $daemon_name wznowił pracę"
            set_daemon_state "$daemon_name" "running"
            set_daemon_failure_time "$daemon_name" ""
            set_daemon_restart_count "$daemon_name" "0"
            
            # Sprawdź i uzupełnij braki
            check_and_fill_gaps "$daemon_name"
        fi
        return 0
    else
        # Daemon nie działa
        local current_time=$(date +%s)
        local failure_time=$(get_daemon_failure_time "$daemon_name")
        
        if [ -z "$failure_time" ]; then
            set_daemon_failure_time "$daemon_name" "$current_time"
            log_warning "Wykryto problem z daemonem $daemon_name"
            failure_time=$current_time
        fi
        
        local failure_duration=$((current_time - failure_time))
        set_daemon_state "$daemon_name" "failed"
        
        local restart_count=$(get_daemon_restart_count "$daemon_name")
        
        # Próby naprawy
        if [ "$restart_count" -lt 3 ]; then
            log_info "Próba naprawy daemona $daemon_name (próba $((restart_count + 1))/3)..."
            
            # 1. Restart daemona
            if restart_daemon "$daemon_name"; then
                set_daemon_restart_count "$daemon_name" "$((restart_count + 1))"
                sleep 5
                if is_daemon_running "$daemon_name"; then
                    return 0
                fi
            fi
            
            # 2. Jeśli nie pomogło, restart VPN (dla daemonów które go używają)
            if [ "$failure_duration" -gt 300 ] && [ "$restart_count" -lt 2 ]; then
                if [[ "$daemon_name" == *"trends_sniffer"* ]] || [[ "$daemon_name" == *"gdelt"* ]]; then
                    log_info "Próba restartu VPN dla $daemon_name..."
                    restart_vpn
                    sleep 5
                    if restart_daemon "$daemon_name"; then
                        set_daemon_restart_count "$daemon_name" "$((restart_count + 1))"
                        sleep 5
                        if is_daemon_running "$daemon_name"; then
                            return 0
                        fi
                    fi
                fi
            fi
            
            # 3. Jeśli nadal nie działa, restart PostgreSQL
            if [ "$failure_duration" -gt 600 ] && [ "$restart_count" -lt 3 ]; then
                log_info "Próba restartu PostgreSQL dla $daemon_name..."
                restart_postgresql
                sleep 10
                if restart_daemon "$daemon_name"; then
                    set_daemon_restart_count "$daemon_name" "$((restart_count + 1))"
                    sleep 5
                    if is_daemon_running "$daemon_name"; then
                        return 0
                    fi
                fi
            fi
            
            set_daemon_restart_count "$daemon_name" "$((restart_count + 1))"
        fi
        
        # Jeśli problem trwa dłużej niż próg, wyślij alerty
        if [ "$failure_duration" -ge "$ALERT_THRESHOLD" ]; then
            local duration_minutes=$((failure_duration / 60))
            local last_alert_time=$(get_daemon_last_alert_time "$daemon_name")
            local time_since_last_alert=0
            
            if [ -n "$last_alert_time" ]; then
                time_since_last_alert=$((current_time - last_alert_time))
            fi
            
            # Wyślij alert co 30 minut
            if [ -z "$last_alert_time" ] || [ "$time_since_last_alert" -ge 1800 ]; then
                log_error "Problem z daemonem $daemon_name trwa już $duration_minutes minut - wysyłanie alertów"
                
                play_alert_sound
                send_alert_email "$daemon_name" "Daemon nie działa od $duration_minutes minut. Wykonano $restart_count prób naprawy." "$duration_minutes"
                
                set_daemon_last_alert_time "$daemon_name" "$current_time"
            fi
        fi
        
        return 1
    fi
}

# Główna pętla monitorowania
monitor_loop() {
    local selected_daemons=("$@")
    
    log_info "Rozpoczynam monitorowanie daemonów: ${selected_daemons[*]}"
    log_info "Interwał sprawdzania: $CHECK_INTERVAL sekund"
    log_info "Próg alertów: $ALERT_THRESHOLD sekund (30 minut)"
    
    init_daemon_states
    
    while true; do
        local check_start=$(date +%s)
        
        # Sprawdź wszystkie wybrane daemony
        for daemon_name in "${selected_daemons[@]}"; do
            if ! is_valid_daemon "$daemon_name"; then
                log_error "Nieznany daemon: $daemon_name"
                continue
            fi
            
            # Ignoruj błędy - kontynuuj monitorowanie innych daemonów
            check_and_fix_daemon "$daemon_name" || true
        done
        
        # Zawsze sprawdź api_server, docs_server i database_backup_daemon
        if is_valid_daemon "api_server"; then
            check_and_fix_daemon "api_server" || true
        fi
        if is_valid_daemon "docs_server"; then
            check_and_fix_daemon "docs_server" || true
        fi
        if is_valid_daemon "database_backup_daemon"; then
            check_and_fix_daemon "database_backup_daemon" || true
        fi
        if is_valid_daemon "database_backup_daemon"; then
            check_and_fix_daemon "database_backup_daemon" || true
        fi
        
        # Poczekaj do następnego sprawdzenia
        local check_duration=$(($(date +%s) - check_start))
        local sleep_time=$((CHECK_INTERVAL - check_duration))
        
        if [ $sleep_time -gt 0 ]; then
            sleep $sleep_time
        fi
    done
}

# ============================================================================
# Parsowanie argumentów
# ============================================================================

# WAŻNE: Sprawdź --monitor NAJPIERW, przed parsowaniem innych argumentów
if [ "${1:-}" = "--monitor" ]; then
    shift
    # Przechwytuj sygnały
    trap 'log_info "Otrzymano sygnał zatrzymania - kończenie..."; rm -f "$PID_FILE"; exit 0' SIGTERM SIGINT
    monitor_loop "$@"
    exit 0
fi

selected_daemons=()
all_daemons=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --monitor)
            # Ten parametr jest obsługiwany wcześniej, ale dodajemy go tutaj
            # aby nie wywoływał błędu jeśli przypadkiem trafi tutaj
            shift
            ;;
        --all)
            all_daemons=true
            shift
            ;;
        --dydx_perpetual_market_trades_service)
            selected_daemons+=("dydx_perpetual_market_trades_service")
            shift
            ;;
        --dydx_top_traders_observer_service)
            selected_daemons+=("dydx_top_traders_observer_service")
            shift
            ;;
        --trends_sniffer_service)
            selected_daemons+=("trends_sniffer_service")
            shift
            ;;
        --btcusdc_updater)
            selected_daemons+=("btcusdc_updater")
            shift
            ;;
        --gdelt_sentiment_daemon)
            selected_daemons+=("gdelt_sentiment_daemon")
            shift
            ;;
        --market_indices_daemon)
            selected_daemons+=("market_indices_daemon")
            shift
            ;;
        --docs_server)
            selected_daemons+=("docs_server")
            shift
            ;;
        --database_backup_daemon)
            selected_daemons+=("database_backup_daemon")
            shift
            ;;
        --stop)
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                kill "$PID" 2>/dev/null || true
                rm -f "$PID_FILE"
                log_info "Master daemon zatrzymany"
            else
                log_warning "Master daemon nie jest uruchomiony"
            fi
            exit 0
            ;;
        --status)
            STATUS_TEST_SOUND=false
            STATUS_TEST_EMAIL=false
            shift
            # Sprawdź czy są dodatkowe opcje testowania
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --test-sound)
                        STATUS_TEST_SOUND=true
                        shift
                        ;;
                    --test-email)
                        STATUS_TEST_EMAIL=true
                        shift
                        ;;
                    --test-all)
                        STATUS_TEST_SOUND=true
                        STATUS_TEST_EMAIL=true
                        shift
                        ;;
                    *)
                        # Nieznany argument - zakończ parsowanie
                        break
                        ;;
                esac
            done
            
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if ps -p "$PID" > /dev/null 2>&1; then
                    log_success "Master daemon działa (PID: $PID)"
                    echo ""
                    echo "Status daemonów:"
                    for daemon_name in $ALL_DAEMONS; do
                        if is_daemon_running "$daemon_name"; then
                            echo "  ✓ $daemon_name"
                        else
                            echo "  ✗ $daemon_name"
                        fi
                    done
                else
                    log_warning "Master daemon nie działa (stary PID file)"
                    rm -f "$PID_FILE"
                fi
            else
                log_warning "Master daemon nie jest uruchomiony"
            fi
            
            # Testy jeśli zostały włączone
            if [ "$STATUS_TEST_SOUND" = true ] || [ "$STATUS_TEST_EMAIL" = true ]; then
                echo ""
                echo "─────────────────────────────────────────"
                echo "Testowanie funkcji powiadomień:"
                echo "─────────────────────────────────────────"
            fi
            
            if [ "$STATUS_TEST_SOUND" = true ]; then
                test_alert_sound
            fi
            
            if [ "$STATUS_TEST_EMAIL" = true ]; then
                test_alert_email
            fi
            
            # Uruchom panel zarządzania daemonami jeśli nie działa
            echo ""
            echo "─────────────────────────────────────────"
            echo "Panel zarządzania daemonami:"
            echo "─────────────────────────────────────────"
            start_daemon_panel_if_needed
            
            exit 0
            ;;
        --test-sound)
            test_alert_sound
            exit 0
            ;;
        --test-email)
            test_alert_email
            exit 0
            ;;
        --test-all)
            echo "Testowanie wszystkich funkcji powiadomień..."
            echo ""
            test_alert_sound
            echo ""
            test_alert_email
            exit 0
            ;;
        *)
            log_error "Nieznany parametr: $1"
            echo "Użycie: $0 [--all|--daemon_name...] [--stop|--status [--test-sound|--test-email|--test-all]]"
            echo ""
            echo "Dostępne daemony:"
            echo "  --dydx_perpetual_market_trades_service"
            echo "  --dydx_top_traders_observer_service"
            echo "  --trends_sniffer_service"
            echo "  --btcusdc_updater"
            echo "  --gdelt_sentiment_daemon"
            echo "  --market_indices_daemon"
            echo "  --docs_server"
            echo "  --database_backup_daemon"
            echo "  --all (wszystkie powyższe + api_server + docs_server + database_backup_daemon)"
            echo ""
            echo "Opcje testowania:"
            echo "  --status --test-sound    - Sprawdź status i przetestuj dźwięk"
            echo "  --status --test-email    - Sprawdź status i przetestuj email"
            echo "  --status --test-all      - Sprawdź status i przetestuj wszystko"
            echo "  --test-sound             - Tylko test dźwięku"
            echo "  --test-email             - Tylko test emaila"
            echo "  --test-all               - Test wszystkiego"
            exit 1
            ;;
    esac
done

if [ "$all_daemons" = true ]; then
    selected_daemons=(
        "dydx_perpetual_market_trades_service"
        "dydx_top_traders_observer_service"
        "trends_sniffer_service"
        "btcusdc_updater"
        "gdelt_sentiment_daemon"
        "market_indices_daemon"
    )
    # api_server, docs_server i database_backup_daemon są zawsze monitorowane
fi

if [ ${#selected_daemons[@]} -eq 0 ] && [ "$all_daemons" = false ]; then
    log_error "Nie wybrano żadnych daemonów do monitorowania"
    echo "Użycie: $0 [--all|--daemon_name...]"
    exit 1
fi

# Uruchom w tle jeśli nie jest to status/stop
if [ ! -f "$PID_FILE" ] || ! ps -p "$(cat "$PID_FILE" 2>/dev/null)" > /dev/null 2>&1; then
    log_info "Uruchamianie master daemon w tle..."
    
    # Uruchom w tle (z katalogu głównego projektu)
    cd "$PROJECT_DIR"
    nohup bash "$0" --monitor "${selected_daemons[@]}" >> "$LOG_FILE" 2>&1 &
    MASTER_PID=$!
    echo $MASTER_PID > "$PID_FILE"
    
    sleep 2
    if ps -p "$MASTER_PID" > /dev/null 2>&1; then
        log_success "Master daemon uruchomiony (PID: $MASTER_PID)"
        log_info "Logi: $LOG_FILE"
    else
        log_error "Nie udało się uruchomić master daemon"
        rm -f "$PID_FILE"
        exit 1
    fi
else
    log_warning "Master daemon już działa (PID: $(cat "$PID_FILE"))"
    exit 1
fi

