#!/bin/bash
# Skrypt do kontroli Mullvad VPN
# Użycie: ./vpn_control.sh [on|off|status|toggle]

set -e

VPN_CMD="mullvad"

# Sprawdź czy Mullvad CLI jest dostępny
if ! command -v $VPN_CMD &> /dev/null; then
    echo "❌ Mullvad CLI nie jest zainstalowany lub nie jest w PATH"
    echo "   Zainstaluj: https://mullvad.net/en/download/vpn/linux/"
    exit 1
fi

case "${1:-status}" in
    on|connect)
        echo "🔌 Łączenie z Mullvad VPN..."
        $VPN_CMD connect
        sleep 2
        $VPN_CMD status
        ;;
    off|disconnect)
        echo "🔌 Rozłączanie Mullvad VPN..."
        $VPN_CMD disconnect
        sleep 2
        $VPN_CMD status
        ;;
    status)
        echo "📊 Status Mullvad VPN:"
        $VPN_CMD status
        ;;
    toggle)
        CURRENT_STATUS=$($VPN_CMD status 2>&1 | grep -i "connected" || echo "disconnected")
        if echo "$CURRENT_STATUS" | grep -qi "connected"; then
            echo "🔌 VPN jest połączony - rozłączam..."
            $VPN_CMD disconnect
        else
            echo "🔌 VPN jest rozłączony - łączę..."
            $VPN_CMD connect
        fi
        sleep 2
        $VPN_CMD status
        ;;
    *)
        echo "Użycie: $0 [on|off|status|toggle]"
        echo ""
        echo "Komendy:"
        echo "  on, connect    - Połącz z VPN"
        echo "  off, disconnect - Rozłącz VPN"
        echo "  status         - Pokaż status VPN"
        echo "  toggle         - Przełącz VPN (on/off)"
        exit 1
        ;;
esac

