#!/bin/bash
# ============================================================================
# Skrypt do uruchamiania Table Monitor Daemon
# ============================================================================
# Użycie:
#   ./scripts/start_table_monitor_daemon.sh
#   ./scripts/start_table_monitor_daemon.sh --interval=1800 --threshold-hours=2
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DAEMON_SCRIPT="${SCRIPT_DIR}/table_monitor_daemon.py"
LOG_DIR="${PROJECT_DIR}/logs"
PID_FILE="${LOG_DIR}/table_monitor_daemon.pid"

# Utwórz katalog logów jeśli nie istnieje
mkdir -p "$LOG_DIR"

# Funkcja sprawdzająca czy daemon już działa
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Działa
        else
            # PID file istnieje ale proces nie działa - usuń plik
            rm -f "$PID_FILE"
            return 1  # Nie działa
        fi
    fi
    return 1  # Nie działa
}

# Funkcja zatrzymująca daemon
stop_daemon() {
    if check_running; then
        PID=$(cat "$PID_FILE")
        echo "Zatrzymywanie daemona (PID: $PID)..."
        kill "$PID"
        sleep 2
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Wymuszanie zatrzymania..."
            kill -9 "$PID"
        fi
        rm -f "$PID_FILE"
        echo "✓ Daemon zatrzymany"
    else
        echo "Daemon nie jest uruchomiony"
    fi
}

# Funkcja pokazująca status
show_status() {
    if check_running; then
        PID=$(cat "$PID_FILE")
        echo "✓ Daemon działa (PID: $PID)"
        if [ -f "${LOG_DIR}/table_monitor_daemon_$(date +%Y%m%d).log" ]; then
            echo ""
            echo "Ostatnie 20 linii z logów:"
            echo "----------------------------------------"
            tail -n 20 "${LOG_DIR}/table_monitor_daemon_$(date +%Y%m%d).log"
        fi
    else
        echo "✗ Daemon nie jest uruchomiony"
    fi
}

# Parsuj argumenty
ACTION="start"
INTERVAL=""
THRESHOLD=""
EMAIL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --stop)
            ACTION="stop"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        --interval=*)
            INTERVAL="${1#*=}"
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --threshold-hours=*)
            THRESHOLD="${1#*=}"
            shift
            ;;
        --threshold-hours)
            THRESHOLD="$2"
            shift 2
            ;;
        --email=*)
            EMAIL="${1#*=}"
            shift
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        *)
            echo "Nieznany parametr: $1"
            exit 1
            ;;
    esac
done

# Wykonaj akcję
case "$ACTION" in
    start)
        if check_running; then
            echo "⚠ Daemon już jest uruchomiony (PID: $(cat "$PID_FILE"))"
            exit 1
        fi
        
        echo "[INFO] Uruchamiam Table Monitor Daemon..."
        
        # Sprawdź czy skrypt istnieje
        if [ ! -f "$DAEMON_SCRIPT" ]; then
            echo "[ERROR] Skrypt nie istnieje: $DAEMON_SCRIPT"
            exit 1
        fi
        
        # Sprawdź czy skrypt jest wykonywalny
        if [ ! -x "$DAEMON_SCRIPT" ]; then
            chmod +x "$DAEMON_SCRIPT"
        fi
        
        # Przygotuj argumenty
        ARGS=""
        if [ -n "$INTERVAL" ]; then
            ARGS="$ARGS --interval=$INTERVAL"
        fi
        if [ -n "$THRESHOLD" ]; then
            ARGS="$ARGS --threshold-hours=$THRESHOLD"
        fi
        if [ -n "$EMAIL" ]; then
            ARGS="$ARGS --email=$EMAIL"
        fi
        
        # Uruchom w tle
        cd "$PROJECT_DIR"
        nohup python3 "$DAEMON_SCRIPT" $ARGS > /dev/null 2>&1 &
        PID=$!
        
        # Zapisz PID
        echo $PID > "$PID_FILE"
        
        # Poczekaj chwilę i sprawdź czy działa
        sleep 2
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "[SUCCESS] Daemon uruchomiony (PID: $PID)"
            echo "[INFO] Logi: ${LOG_DIR}/table_monitor_daemon_$(date +%Y%m%d).log"
        else
            echo "[ERROR] Nie udało się uruchomić daemona"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
    stop)
        stop_daemon
        ;;
    status)
        show_status
        ;;
    *)
        echo "Użycie: $0 [--start|--stop|--status] [--interval=SECONDS] [--threshold-hours=HOURS] [--email=EMAIL]"
        exit 1
        ;;
esac

