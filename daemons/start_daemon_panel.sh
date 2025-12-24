#!/bin/bash

# Skrypt uruchomieniowy panelu zarządzania daemonami
# ===================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || exit 1

# Aktywuj środowisko wirtualne jeśli istnieje
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Środowisko wirtualne aktywowane"
fi

# Port serwera (można zmienić przez zmienną środowiskową)
PORT="${DAEMON_PANEL_PORT:-8090}"

# Sprawdź czy uruchamiamy w tle (gdy wywołany z master.sh)
if [ "${DAEMON_PANEL_BACKGROUND:-false}" = "true" ]; then
    # Tryb tła - bez reload
    uvicorn daemon_panel:app --host 0.0.0.0 --port "$PORT" > /dev/null 2>&1
else
    # Tryb interaktywny - z reload
    echo "🚀 Uruchamianie panelu zarządzania daemonami na porcie $PORT..."
    echo "📊 Panel dostępny pod: http://localhost:$PORT"
    echo ""
    echo "Naciśnij Ctrl+C aby zatrzymać serwer"
    echo ""
    uvicorn daemon_panel:app --host 0.0.0.0 --port "$PORT" --reload
fi

