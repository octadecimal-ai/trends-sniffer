#!/bin/bash
# ============================================================================
# Technical Indicators Daemon - Start Script
# ============================================================================
# Skrypt do zarządzania daemonem obliczającym wskaźniki techniczne
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/.dev/logs/technical_indicators_daemon.pid"
LOG_FILE="$PROJECT_ROOT/.dev/logs/technical_indicators_daemon.log"
DAEMON_SCRIPT="$PROJECT_ROOT/daemons/technical_indicators_daemon.py"

# Funkcje pomocnicze
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
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
        echo "⚠ Daemon już działa (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    echo "🚀 Uruchamianie Technical Indicators Daemon..."
    cd "$PROJECT_ROOT"
    source .venv/bin/activate
    
    nohup python "$DAEMON_SCRIPT" >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    if is_running; then
        echo "✅ Daemon uruchomiony (PID: $PID)"
        echo "   Log: $LOG_FILE"
    else
        echo "❌ Nie udało się uruchomić daemona"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    if ! is_running; then
        echo "⚠ Daemon nie działa"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo "🛑 Zatrzymywanie daemona (PID: $PID)..."
    kill "$PID"
    
    # Czekaj maksymalnie 10 sekund
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            echo "✅ Daemon zatrzymany"
            return 0
        fi
        sleep 1
    done
    
    # Jeśli nadal działa, wymuś zatrzymanie
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠ Wymuszanie zatrzymania..."
        kill -9 "$PID"
        rm -f "$PID_FILE"
        echo "✅ Daemon zatrzymany (wymuszony)"
    fi
}

status_daemon() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "✅ Daemon działa (PID: $PID)"
        echo "   Log: $LOG_FILE"
        ps -p "$PID" -o pid,etime,cmd | tail -1
    else
        echo "❌ Daemon nie działa"
    fi
}

restart_daemon() {
    stop_daemon
    sleep 2
    start_daemon
}

# Główna logika
case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        status_daemon
        ;;
    *)
        echo "Użycie: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0

