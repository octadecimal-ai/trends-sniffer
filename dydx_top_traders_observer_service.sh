#!/bin/bash
# ============================================================================
# Skrypt zarządzający usługą dYdX Top Traders Observer
# ============================================================================
# Użycie:
#   ./dydx_top_traders_observer_service.sh --start    # Uruchom usługę
#   ./dydx_top_traders_observer_service.sh --stop     # Zatrzymaj usługę
#   ./dydx_top_traders_observer_service.sh --restart  # Restart usługi
#   ./dydx_top_traders_observer_service.sh --status   # Status usługi
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="com.octadecimal.dydx-top-traders-observer"
PLIST_FILE="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"
PYTHON_SCRIPT="${SCRIPT_DIR}/src/scripts/dydx_top_traders_observer.py"
LOG_FILE="${SCRIPT_DIR}/.dev/logs/dydx_top_traders_observer.log"
PID_FILE="${SCRIPT_DIR}/.dev/dydx_top_traders_observer.pid"

# Utwórz katalogi jeśli nie istnieją
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$PID_FILE")"

# Domyślne wartości parametrów
UPDATE_INTERVAL=3600      # 1 godzina
WATCH_INTERVAL=300        # 5 minut
TOP_N=50
TICKERS="BTC-USD ETH-USD"
WINDOW_HOURS=24
TESTNET=""

# Funkcja do tworzenia pliku plist dla launchd
create_plist() {
    # Sprawdź czy .venv istnieje
    if [ -d "${SCRIPT_DIR}/.venv" ]; then
        PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python3"
    elif [ -d "${SCRIPT_DIR}/venv" ]; then
        PYTHON_BIN="${SCRIPT_DIR}/venv/bin/python3"
    else
        PYTHON_BIN="/usr/bin/python3"
    fi
    
    # Buduj argumenty
    ARGS=("${PYTHON_SCRIPT}")
    ARGS+=("--update-interval=${UPDATE_INTERVAL}")
    ARGS+=("--watch-interval=${WATCH_INTERVAL}")
    ARGS+=("--top-n=${TOP_N}")
    ARGS+=("--window-hours=${WINDOW_HOURS}")
    
    if [ -n "$TESTNET" ]; then
        ARGS+=("--testnet")
    fi
    
    # Dodaj tickers
    for ticker in $TICKERS; do
        ARGS+=("--tickers")
        ARGS+=("$ticker")
    done
    
    # Konwertuj array na string dla plist
    ARGS_STR=""
    for arg in "${ARGS[@]}"; do
        ARGS_STR="${ARGS_STR}<string>${arg}</string>"
    done
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${SERVICE_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_BIN}</string>
        ${ARGS_STR}
    </array>
    
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
    
    <key>StandardOutPath</key>
    <string>${LOG_FILE}</string>
    
    <key>StandardErrorPath</key>
    <string>${LOG_FILE}</string>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>ProcessType</key>
    <string>Background</string>
    
    <key>Nice</key>
    <integer>1</integer>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
    chmod 644 "$PLIST_FILE"
}

# Funkcja sprawdzająca status
check_status() {
    if launchctl list | grep -q "${SERVICE_NAME}"; then
        echo "✓ Usługa jest uruchomiona"
        launchctl list | grep "${SERVICE_NAME}"
        return 0
    else
        echo "✗ Usługa nie jest uruchomiona"
        return 1
    fi
}

# Funkcja startująca usługę
start_service() {
    if check_status > /dev/null 2>&1; then
        echo "⚠ Usługa już jest uruchomiona"
        return 1
    fi
    
    echo "Uruchamianie usługi ${SERVICE_NAME}..."
    
    # Sprawdź czy skrypt istnieje
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo "✗ Błąd: Skrypt nie istnieje: $PYTHON_SCRIPT"
        return 1
    fi
    
    # Sprawdź czy skrypt jest wykonywalny
    if [ ! -x "$PYTHON_SCRIPT" ]; then
        chmod +x "$PYTHON_SCRIPT"
    fi
    
    # Utwórz plik plist
    create_plist
    
    # Załaduj usługę
    launchctl load "$PLIST_FILE" 2>/dev/null || launchctl bootstrap gui/$(id -u) "$PLIST_FILE"
    
    # Poczekaj chwilę i sprawdź status
    sleep 2
    
    if check_status > /dev/null 2>&1; then
        echo "✓ Usługa została uruchomiona pomyślnie"
        echo "  Logi: $LOG_FILE"
        return 0
    else
        echo "✗ Nie udało się uruchomić usługi"
        return 1
    fi
}

# Funkcja zatrzymująca usługę
stop_service() {
    if ! check_status > /dev/null 2>&1; then
        echo "⚠ Usługa nie jest uruchomiona"
        return 1
    fi
    
    echo "Zatrzymywanie usługi ${SERVICE_NAME}..."
    
    # Wyładuj usługę
    launchctl unload "$PLIST_FILE" 2>/dev/null || launchctl bootout gui/$(id -u) "$PLIST_FILE" 2>/dev/null
    
    # Poczekaj chwilę
    sleep 2
    
    if ! check_status > /dev/null 2>&1; then
        echo "✓ Usługa została zatrzymana"
        return 0
    else
        echo "✗ Nie udało się zatrzymać usługi"
        return 1
    fi
}

# Funkcja restartująca usługę
restart_service() {
    echo "Restartowanie usługi ${SERVICE_NAME}..."
    stop_service
    sleep 1
    start_service
}

# Parsuj argumenty
ACTION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --update-interval=*)
            UPDATE_INTERVAL="${1#*=}"
            shift
            ;;
        --watch-interval=*)
            WATCH_INTERVAL="${1#*=}"
            shift
            ;;
        --top-n=*)
            TOP_N="${1#*=}"
            shift
            ;;
        --tickers=*)
            TICKERS="${1#*=}"
            shift
            ;;
        --window-hours=*)
            WINDOW_HOURS="${1#*=}"
            shift
            ;;
        --testnet)
            TESTNET="true"
            shift
            ;;
        --start|--stop|--restart|--status)
            ACTION="$1"
            shift
            break
            ;;
        *)
            shift
            ;;
    esac
done

# Główna logika
case "$ACTION" in
    --start)
        start_service
        ;;
    --stop)
        stop_service
        ;;
    --restart)
        restart_service
        ;;
    --status)
        check_status
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "Ostatnie 20 linii z logów:"
            echo "----------------------------------------"
            tail -n 20 "$LOG_FILE" 2>/dev/null || echo "Brak logów"
        fi
        ;;
    *)
        echo "Użycie: $0 [opcje] {--start|--stop|--restart|--status}"
        echo ""
        echo "Opcje:"
        echo "  --start                    Uruchom usługę w tle"
        echo "  --stop                     Zatrzymaj usługę"
        echo "  --restart                  Restart usługi"
        echo "  --status                   Pokaż status usługi i ostatnie logi"
        echo ""
        echo "Parametry konfiguracyjne:"
        echo "  --update-interval=SEC      Interwał aktualizacji rankingu (domyślnie: 3600)"
        echo "  --watch-interval=SEC       Interwał sprawdzania fill'ów (domyślnie: 300)"
        echo "  --top-n=N                  Liczba top traderów (domyślnie: 50)"
        echo "  --tickers=\"T1 T2\"          Lista rynków (domyślnie: \"BTC-USD ETH-USD\")"
        echo "  --window-hours=H           Okno czasowe rankingu (domyślnie: 24)"
        echo "  --testnet                  Użyj testnet API"
        exit 1
        ;;
esac

exit $?

