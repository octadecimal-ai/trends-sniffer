#!/bin/bash
# ============================================================================
# Database Backup Daemon - Start Script
# ============================================================================
# Uruchamia daemon do wykonywania backupu bazy danych.
#
# Użycie:
#   ./start_database_backup_daemon.sh --start    # Uruchom daemon w tle
#   ./start_database_backup_daemon.sh --stop     # Zatrzymaj daemon
#   ./start_database_backup_daemon.sh --status    # Sprawdź status
#   ./start_database_backup_daemon.sh --once      # Wykonaj backup raz
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

# === Konfiguracja ===
DAEMON_SCRIPT="${SCRIPT_DIR}/database_backup_daemon.py"
PID_FILE="${PROJECT_DIR}/.dev/logs/database_backup_daemon.pid"
LOG_DIR="${PROJECT_DIR}/.dev/logs"

# Utwórz katalogi
mkdir -p "$LOG_DIR"

# === Funkcje zarządzania ===
start_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warning "Daemon już działa (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    log_info "Uruchamianie daemona backupu bazy danych..."
    
    # Aktywuj środowisko wirtualne jeśli istnieje
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
    
    # Uruchom w tle
    nohup python3 "$DAEMON_SCRIPT" --daemon >> "${LOG_DIR}/database_backup_daemon.log" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Daemon uruchomiony (PID: $PID)"
        return 0
    else
        log_error "Nie udało się uruchomić daemona"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        log_warning "Daemon nie jest uruchomiony"
        return 1
    fi
    
    PID=$(cat "$PID_FILE" 2>/dev/null)
    
    if ps -p "$PID" > /dev/null 2>&1; then
        log_info "Zatrzymywanie daemona (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 2
        
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warning "Wymuszanie zatrzymania..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE"
        log_success "Daemon zatrzymany"
        return 0
    else
        log_warning "Daemon nie działa (stary PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if ps -p "$PID" > /dev/null 2>&1; then
            log_success "Daemon działa (PID: $PID)"
            return 0
        else
            log_warning "Daemon nie działa (stary PID file)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        log_warning "Daemon nie jest uruchomiony"
        return 1
    fi
}

run_once() {
    log_info "Wykonuję backup jednorazowo..."
    
    # Aktywuj środowisko wirtualne jeśli istnieje
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi
    
    python3 "$DAEMON_SCRIPT" --once
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
        check_status
        ;;
    --once)
        run_once
        ;;
    *)
        echo "Użycie: $0 [--start|--stop|--status|--once]"
        echo ""
        echo "Opcje:"
        echo "  --start    Uruchom daemon w tle (backup raz dziennie)"
        echo "  --stop     Zatrzymaj daemon"
        echo "  --status   Sprawdź status daemona"
        echo "  --once     Wykonaj backup raz i zakończ"
        exit 1
        ;;
esac

