#!/bin/bash
# Skrypt do uruchomienia API Server
# ==================================
# Uruchamia serwer FastAPI dla trends-sniffer

set -e

# Katalog projektu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Przejdź do katalogu projektu
cd "$PROJECT_DIR"

# Aktywuj venv jeśli istnieje
if [ -d venv ]; then
    source venv/bin/activate
fi

# Sprawdź czy .env istnieje
if [ ! -f .env ]; then
    echo "Błąd: Plik .env nie istnieje!"
    echo "Utwórz plik .env z zmienną DATABASE_URL"
    exit 1
fi

# Uruchom serwer
echo "Uruchamianie Trends Sniffer API Server..."
echo "Dokumentacja dostępna pod: http://localhost:8000/docs"
echo ""

python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

