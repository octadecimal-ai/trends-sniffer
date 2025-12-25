#!/bin/bash
# ============================================================================
# Sentiment Propagation Daemon - Start Script
# ============================================================================
# Uruchamia daemon do obliczania metryk propagacji sentymentu między regionami.
#
# Analizuje propagację sentymentu przez strefy czasowe:
# - APAC → EU (lag ~4h)
# - EU → US (lag ~4h)
# - US → APAC (overnight, lag ~12h)
#
# Użycie:
#   ./start_sentiment_propagation_daemon.sh --start    # Uruchom daemon w tle
#   ./start_sentiment_propagation_daemon.sh --stop    # Zatrzymaj daemon
#   ./start_sentiment_propagation_daemon.sh --status  # Sprawdź status
#   ./start_sentiment_propagation_daemon.sh --once     # Jeden cykl (bez tła)
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
PID_FILE="${LOG_DIR}/sentiment_propagation_daemon.pid"
LOG_FILE="${LOG_DIR}/sentiment_propagation_daemon.log"
DAEMON_SCRIPT="${SCRIPT_DIR}/sentiment_propagation_daemon.py"

# === Funkcje daemona ===
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
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
    
    log_info "Uruchamiam Sentiment Propagation Daemon..."
    
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
    --once|--backfill)
        # Tryb jednorazowy - uruchom bezpośrednio (nie w tle)
        if [ -f "$PROJECT_DIR/.env" ]; then
            set -a
            source "$PROJECT_DIR/.env" 2>/dev/null || true
            set +a
        fi
        
        if [ -z "${VIRTUAL_ENV:-}" ]; then
            if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
                source "$PROJECT_DIR/venv/bin/activate"
            elif [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
                source "$PROJECT_DIR/.venv/bin/activate"
            fi
        fi
        
        python "$DAEMON_SCRIPT" "$@"
        ;;
    *)
        if [ $# -eq 0 ]; then
            start_daemon
        else
            log_error "Nieznany parametr: $1"
            echo "Użycie: $0 [--start|--stop|--status|--restart|--once|--backfill DAYS]"
            exit 1
        fi
        ;;
esac

