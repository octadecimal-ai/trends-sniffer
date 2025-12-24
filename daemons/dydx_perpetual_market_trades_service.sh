#!/bin/bash
# ============================================================================
# Skrypt zarządzający usługą dYdX Perpetual Market Trades
# ============================================================================
# Użycie:
#   ./dydx_perpetual_market_trades_service.sh --start    # Uruchom usługę
#   ./dydx_perpetual_market_trades_service.sh --stop     # Zatrzymaj usługę
#   ./dydx_perpetual_market_trades_service.sh --restart  # Restart usługi
#   ./dydx_perpetual_market_trades_service.sh --status   # Status usługi
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_NAME="com.octadecimal.dydx-perpetual-market-trades"
PLIST_FILE="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"
PYTHON_SCRIPT="${SCRIPT_DIR}/dydx_perpetual_market_trades_daemon.py"
LOG_FILE="${PROJECT_DIR}/.dev/logs/dydx_perpetual_market_trades_service.log"
PID_FILE="${PROJECT_DIR}/.dev/dydx_perpetual_market_trades_service.pid"

# Utwórz katalogi jeśli nie istnieją
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$PID_FILE")"

# Domyślne wartości
TICKER="BTC-USD"
DAYS_BACK_START=1

# Funkcja do tworzenia pliku plist dla launchd
create_plist() {
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${SERVICE_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${PYTHON_SCRIPT}</string>
        <string>--ticker=${TICKER}</string>
        <string>--days-back-start=${DAYS_BACK_START}</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    
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
        echo "  Logi szczegółowe (dni): ${SCRIPT_DIR}/.dev/logs/dydx_perpetual_market_trades_days.log"
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
        --ticker=*)
            TICKER="${1#*=}"
            shift
            ;;
        --ticker)
            TICKER="$2"
            shift 2
            ;;
        --days-back-start=*)
            DAYS_BACK_START="${1#*=}"
            shift
            ;;
        --days-back-start)
            DAYS_BACK_START="$2"
            shift 2
            ;;
        --start|--stop|--restart|--status)
            ACTION="$1"
            shift
            break
            ;;
        *)
            # Nieznany parametr - zignoruj i przejdź dalej
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
        if [ -f "${SCRIPT_DIR}/.dev/logs/dydx_perpetual_market_trades_days.log" ]; then
            echo ""
            echo "Ostatnie 10 linii z logów dni:"
            echo "----------------------------------------"
            tail -n 10 "${SCRIPT_DIR}/.dev/logs/dydx_perpetual_market_trades_days.log" 2>/dev/null || echo "Brak logów"
        fi
        ;;
    *)
        echo "Użycie: $0 [--ticker=TICKER] [--days-back-start=N] {--start|--stop|--restart|--status}"
        echo ""
        echo "Opcje:"
        echo "  --start                    Uruchom usługę w tle"
        echo "  --stop                     Zatrzymaj usługę"
        echo "  --restart                  Restart usługi"
        echo "  --status                   Pokaż status usługi i ostatnie logi"
        echo "  --ticker=TICKER            Symbol rynku (domyślnie: BTC-USD)"
        echo "  --days-back-start=N        Od ilu dni wstecz zacząć (domyślnie: 1)"
        exit 1
        ;;
esac

exit $?

