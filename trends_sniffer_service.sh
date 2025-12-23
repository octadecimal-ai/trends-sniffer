#!/bin/bash
# ============================================================================
# Skrypt zarządzający usługą trends-sniffer
# ============================================================================
# Użycie:
#   ./trends_sniffer_service.sh --start    # Uruchom usługę
#   ./trends_sniffer_service.sh --stop     # Zatrzymaj usługę
#   ./trends_sniffer_service.sh --restart  # Restart usługi
#   ./trends_sniffer_service.sh --status   # Status usługi
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="com.octadecimal.trends-sniffer"
PLIST_FILE="$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist"
PYTHON_SCRIPT="${SCRIPT_DIR}/src/scripts/fetch_trends_with_vpn.py"
LOG_FILE="${SCRIPT_DIR}/.dev/logs/trends_sniffer_service.log"
PID_FILE="${SCRIPT_DIR}/.dev/trends_sniffer_service.pid"

# Utwórz katalogi jeśli nie istnieją
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$(dirname "$PID_FILE")"

# Domyślna wartość dla --not_zero_multiplier
NOT_ZERO_MULTIPLIER="true"

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
        <string>--not_zero_multiplier=${NOT_ZERO_MULTIPLIER}</string>
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

# Parsuj argumenty (przed główną logiką)
ACTION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --not_zero_multiplier=*)
            NOT_ZERO_MULTIPLIER="${1#*=}"
            shift
            ;;
        --not_zero_multiplier)
            NOT_ZERO_MULTIPLIER="true"
            shift
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
        ;;
    *)
        echo "Użycie: $0 [--not_zero_multiplier=true|false] {--start|--stop|--restart|--status}"
        echo ""
        echo "Opcje:"
        echo "  --start                    Uruchom usługę w tle"
        echo "  --stop                     Zatrzymaj usługę"
        echo "  --restart                  Restart usługi"
        echo "  --status                   Pokaż status usługi i ostatnie logi"
        echo "  --not_zero_multiplier=VAL  Pomijaj frazy z multiplier=0.0 (true/false, domyślnie: true)"
        exit 1
        ;;
esac

exit $?

