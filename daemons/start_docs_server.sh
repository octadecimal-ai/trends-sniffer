#!/bin/bash

# Skrypt uruchomieniowy serwera dokumentacji
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || exit 1

# Aktywuj środowisko wirtualne jeśli istnieje
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Środowisko wirtualne aktywowane"
fi

# Port serwera (można zmienić przez zmienną środowiskową)
PORT="${DOCS_PORT:-8080}"

echo "🚀 Uruchamianie serwera dokumentacji na porcie $PORT..."
echo "📚 Dokumentacja dostępna pod: http://localhost:$PORT"
echo "📖 Domyślny dokument: http://localhost:$PORT/docs/INDEX.md"
echo ""
echo "Naciśnij Ctrl+C aby zatrzymać serwer"
echo ""

# Uruchom serwer
uvicorn docs_server:app --host 0.0.0.0 --port "$PORT" --reload

