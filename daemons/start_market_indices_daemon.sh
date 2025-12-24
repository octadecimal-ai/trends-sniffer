#!/bin/bash
# ============================================================================
# Market Indices Daemon - Start Script
# ============================================================================
# Uruchamia daemon do pobierania danych z tradycyjnych rynków finansowych.
#
# Źródła:
# - Yahoo Finance: S&P 500, NASDAQ, VIX, DXY, Gold, Treasury Yields
# - Alternative.me: Fear & Greed Index
#
# Użycie:
#   ./start_market_indices_daemon.sh --start    # Uruchom daemon w tle
#   ./start_market_indices_daemon.sh --stop    # Zatrzymaj daemon
#   ./start_market_indices_daemon.sh --status  # Sprawdź status
#   ./start_market_indices_daemon.sh --once     # Jeden cykl (bez tła)
#   ./start_market_indices_daemon.sh --historical-days 30  # Pobierz historię
# ============================================================================

set -eo pipefail

# Znajdź katalog projektu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# === Kolory ===
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# === Funkcje ===
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# === Pliki ===
LOG_DIR="${PROJECT_DIR}/.dev/logs"
mkdir -p "$LOG_DIR"
PID_FILE="${LOG_DIR}/market_indices_daemon.pid"
LOG_FILE="${LOG_DIR}/market_indices_daemon.log"
DAEMON_SCRIPT="${SCRIPT_DIR}/market_indices_daemon.py"

# === Funkcje daemona ===
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # PID file istnieje ale proces nie działa - usuń plik
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

start_daemon() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        log_warning "Daemon już działa (PID: $PID)"
        return 1
    fi
    
    log_info "Uruchamiam Market Indices Daemon..."
    
    # Załaduj zmienne środowiskowe
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env" 2>/dev/null || true
        set +a
    fi
    
    # Sprawdź DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL nie jest ustawiony!"
        log_info "Ustaw w .env lub jako zmienną środowiskową"
        return 1
    fi
    
    # Aktywuj venv jeśli istnieje
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
            source "$PROJECT_DIR/venv/bin/activate"
        elif [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
            source "$PROJECT_DIR/.venv/bin/activate"
        fi
    fi
    
    # Sprawdź wymagane pakiety
    python -c "import yfinance" 2>/dev/null || {
        log_warning "yfinance nie jest zainstalowany. Instaluję..."
        pip install "yfinance<1.0" > /dev/null 2>&1
    }
    python -c "import requests" 2>/dev/null || {
        log_warning "requests nie jest zainstalowany. Instaluję..."
        pip install requests > /dev/null 2>&1
    }
    
    # Uruchom daemon w tle z nohup
    nohup python "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
    DAEMON_PID=$!
    
    # Zapisz PID
    echo "$DAEMON_PID" > "$PID_FILE"
    
    # Poczekaj chwilę i sprawdź czy proces nadal działa
    sleep 2
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        log_success "Daemon uruchomiony (PID: $DAEMON_PID)"
        log_info "Logi: $LOG_FILE"
        return 0
    else
        log_error "Daemon nie uruchomił się poprawnie!"
        rm -f "$PID_FILE"
        log_info "Sprawdź logi: $LOG_FILE"
        return 1
    fi
}

stop_daemon() {
    if ! is_running; then
        log_warning "Daemon nie działa"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    log_info "Zatrzymuję daemon (PID: $PID)..."
    
    kill "$PID" 2>/dev/null || true
    
    # Poczekaj na zakończenie
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Jeśli nadal działa, użyj kill -9
    if ps -p "$PID" > /dev/null 2>&1; then
        log_warning "Proces nie zakończył się, używam kill -9..."
        kill -9 "$PID" 2>/dev/null || true
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    log_success "Daemon zatrzymany"
    return 0
}

status_daemon() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        log_success "Daemon działa (PID: $PID)"
        log_info "Logi: $LOG_FILE"
        return 0
    else
        log_warning "Daemon nie działa"
        return 1
    fi
}

# === Parsowanie argumentów ===
case "${1:-}" in
    --start)
        start_daemon
        ;;
    --stop)
        stop_daemon
        ;;
    --status)
        status_daemon
        ;;
    --restart)
        stop_daemon
        sleep 2
        start_daemon
        ;;
    --once|--historical-days)
        # Tryb jednorazowy - uruchom bezpośrednio (nie w tle)
        # Załaduj zmienne środowiskowe
        if [ -f "$PROJECT_DIR/.env" ]; then
            set -a
            source "$PROJECT_DIR/.env" 2>/dev/null || true
            set +a
        fi
        
        # Aktywuj venv
        if [ -z "${VIRTUAL_ENV:-}" ]; then
            if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
                source "$PROJECT_DIR/venv/bin/activate"
            elif [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
                source "$PROJECT_DIR/.venv/bin/activate"
            fi
        fi
        
        # Uruchom daemon z argumentami
        python "$DAEMON_SCRIPT" "$@"
        ;;
    *)
        if [ $# -eq 0 ]; then
            # Brak argumentów - uruchom w tle
            start_daemon
        else
            log_error "Nieznany parametr: $1"
            echo "Użycie: $0 [--start|--stop|--status|--restart|--once|--historical-days N]"
            exit 1
        fi
        ;;
esac

