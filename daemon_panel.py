"""
Panel WWW do zarządzania daemonami
===================================
Panel FastAPI do zarządzania daemonami używający master.sh
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import importlib.util
from daemons.database_backup_daemon import get_last_backup_info

# Ścieżki
PROJECT_ROOT = Path(__file__).parent
MASTER_SCRIPT = PROJECT_ROOT / "master.sh"
STATE_DIR = PROJECT_ROOT / ".dev" / "state"
LOG_DIR = PROJECT_ROOT / ".dev" / "logs"
ENV_FILE = PROJECT_ROOT / ".env"

# Załaduj zmienne środowiskowe
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Globalny engine z connection poolingiem (jeden dla całego panelu)
_global_engine = None

def get_database_engine():
    """Zwraca globalny engine z connection poolingiem."""
    global _global_engine
    if _global_engine is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL nie jest ustawiony")
        
        # Konfiguracja connection pool
        pool_config = {}
        if 'postgresql' in database_url:
            pool_config = {
                'poolclass': QueuePool,
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600  # Recycle connections after 1 hour
            }
        
        _global_engine = create_engine(
            database_url,
            echo=False,
            **pool_config
        )
        logger.info("Globalny database engine utworzony z connection poolingiem")
    
    return _global_engine

# Konfiguracja daemonów (z master.sh)
# Używamy kolumn reprezentujących rzeczywiste daty danych, nie daty wykonania skryptów
DAEMON_TABLES = {
    "dydx_perpetual_market_trades_service": {
        "table": "dydx_perpetual_market_trades",
        "date_column": "effective_at"  # Rzeczywista data transakcji
    },
    "dydx_top_traders_observer_service": {
        "table": "dydx_fills",
        "date_column": "effective_at"  # Rzeczywista data fill'a (transakcji)
    },
    "trends_sniffer_service": {
        "table": "google_trends_sentiment_measurement",  # Tabela z pomiarami sentymentu
        "date_column": "created_at"  # Data utworzenia rekordu
    },
    "btcusdc_updater": {
        "table": "ohlcv",
        "date_column": "timestamp"  # Rzeczywista data świecy
    },
    "gdelt_sentiment_daemon": {
        "table": "gdelt_sentiment",
        "date_column": "timestamp"  # Rzeczywista data pomiaru sentymentu
    },
    "market_indices_daemon": {
        "table": "market_indices",
        "date_column": "timestamp"  # Rzeczywista data indeksu
    },
    "economic_calendar_daemon": {
        "table": "manual_economic_calendar",
        "date_column": "event_date"  # Data wydarzenia ekonomicznego
    },
    "sentiment_propagation_daemon": {
        "table": "google_trends_sentiment_propagation",
        "date_column": "timestamp"  # Timestamp metryk propagacji
    },
    "technical_indicators_daemon": {
        "table": "technical_indicators",
        "date_column": "timestamp"  # Timestamp wskaźników technicznych
    },
    "order_flow_imbalance_daemon": {
        "table": "dydx_order_flow_imbalance",
        "date_column": "timestamp"  # Timestamp metryk imbalance
    },
    "api_server": {
        "table": None,
        "date_column": None
    },
    "docs_server": {
        "table": None,
        "date_column": None
    }
}

# Lista wszystkich daemonów (z master.sh)
ALL_DAEMONS = [
    "dydx_perpetual_market_trades_service",
    "dydx_top_traders_observer_service",
    "trends_sniffer_service",
    "btcusdc_updater",
    "gdelt_sentiment_daemon",
    "market_indices_daemon",
    "economic_calendar_daemon",
    "sentiment_propagation_daemon",
    "technical_indicators_daemon",
    "order_flow_imbalance_daemon",
    "api_server",
    "docs_server",
    "database_backup_daemon"
]

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Panel zarządzania daemonami uruchomiony")
    logger.info(f"Master script: {MASTER_SCRIPT}")
    if not MASTER_SCRIPT.exists():
        logger.warning(f"Master script nie istnieje: {MASTER_SCRIPT}")
    
    # Inicjalizuj globalny engine przy starcie
    try:
        get_database_engine()
        logger.info("Globalny database engine zainicjalizowany z connection poolingiem")
    except Exception as e:
        logger.error(f"Błąd inicjalizacji bazy danych: {e}")
    
    yield
    
    # Shutdown - zamknij połączenia
    global _global_engine
    if _global_engine is not None:
        _global_engine.dispose()
        logger.info("Połączenia z bazą danych zamknięte")
    
    logger.info("Panel zarządzania daemonami zamykany")


# Utwórz aplikację FastAPI
app = FastAPI(
    title="Trends Sniffer - Panel Zarządzania Daemonami",
    description="Panel do zarządzania daemonami używający master.sh",
    version="1.0.0",
    lifespan=lifespan
)

# Dodaj CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_master_command(args: List[str]) -> Dict:
    """
    Wykonuje komendę master.sh i zwraca wynik.
    
    Args:
        args: Lista argumentów dla master.sh
        
    Returns:
        Dict z wynikiem: {success: bool, output: str, error: str}
    """
    try:
        cmd = ["bash", str(MASTER_SCRIPT)] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Timeout - komenda trwała zbyt długo",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "returncode": -1
        }


def is_daemon_running(daemon_name: str) -> bool:
    """Sprawdza czy daemon działa używając różnych metod w zależności od typu."""
    # Mapowanie daemonów na metody sprawdzania (z master.sh)
    daemon_configs = {
        "dydx_perpetual_market_trades_service": {
            "method": "launchctl",
            "service_name": "com.octadecimal.dydx-perpetual-market-trades"
        },
        "dydx_top_traders_observer_service": {
            "method": "launchctl",
            "service_name": "com.octadecimal.dydx-top-traders-observer"
        },
        "trends_sniffer_service": {
            "method": "launchctl",
            "service_name": "com.octadecimal.trends-sniffer"
        },
        "btcusdc_updater": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "btcusdc_updater.pid")
        },
        "gdelt_sentiment_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "gdelt_sentiment_daemon.pid")
        },
        "market_indices_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "market_indices_daemon.pid")
        },
        "economic_calendar_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "economic_calendar_daemon.pid")
        },
        "sentiment_propagation_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "sentiment_propagation_daemon.pid")
        },
        "technical_indicators_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "technical_indicators_daemon.pid")
        },
        "order_flow_imbalance_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "order_flow_imbalance_daemon.pid")
        },
        "api_server": {
            "method": "port",
            "port": 8000
        },
        "docs_server": {
            "method": "port",
            "port": 8080
        },
        "database_backup_daemon": {
            "method": "pid",
            "pid_file": str(LOG_DIR / "database_backup_daemon.pid")
        }
    }
    
    config = daemon_configs.get(daemon_name)
    if not config:
        return False
    
    method = config["method"]
    
    if method == "launchctl":
        service_name = config["service_name"]
        try:
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return service_name in result.stdout
        except:
            return False
    
    elif method == "pid":
        pid_file = Path(config["pid_file"])
        if not pid_file.exists():
            # Jeśli plik PID nie istnieje, sprawdź czy proces działa po nazwie
            # (może być uruchomiony bezpośrednio, nie przez skrypt)
            daemon_name_to_script = {
                "technical_indicators_daemon": "technical_indicators_daemon.py",
                "order_flow_imbalance_daemon": "order_flow_imbalance_daemon.py",
                "gdelt_sentiment_daemon": "gdelt_sentiment_daemon.py",
                "market_indices_daemon": "market_indices_daemon.py",
                "economic_calendar_daemon": "economic_calendar_daemon.py",
                "sentiment_propagation_daemon": "sentiment_propagation_daemon.py",
                "btcusdc_updater": "btcusdc_updater.py",
                "database_backup_daemon": "database_backup_daemon.py"
            }
            script_name = daemon_name_to_script.get(daemon_name)
            if script_name:
                try:
                    # Sprawdź czy proces z tą nazwą skryptu działa
                    result = subprocess.run(
                        ["pgrep", "-f", script_name],
                        capture_output=True,
                        timeout=5
                    )
                    return result.returncode == 0
                except:
                    pass
            return False
        try:
            pid = int(pid_file.read_text().strip())
            # Sprawdź przez ps (działa na macOS/Unix)
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    elif method == "port":
        port = config["port"]
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    return False


def get_table_stats(daemon_name: str) -> Optional[Dict]:
    """Pobiera statystyki tabeli dla daemona z bazy danych.
    
    Używa kolumn reprezentujących rzeczywiste daty danych (np. effective_at, timestamp),
    a nie daty wykonania skryptów (np. observed_at, created_at).
    """
    config = DAEMON_TABLES.get(daemon_name)
    if not config or not config["table"]:
        return None
    
    table = config["table"]
    date_column = config["date_column"]
    
    try:
        engine = get_database_engine()
        # Sprawdź typ bazy danych z engine
        is_postgresql = 'postgresql' in str(engine.url)
        
        with engine.connect() as conn:
            # Sprawdź czy tabela istnieje
            if is_postgresql:
                check_query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    )
                """)
            else:
                # SQLite
                check_query = text("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name=:table_name
                """)
            
            result = conn.execute(check_query, {"table_name": table})
            table_exists = result.scalar() if is_postgresql else result.scalar() > 0
            
            if not table_exists:
                return {
                    "record_count": 0,
                    "first_record": None,
                    "last_record": None,
                    "time_range": None,
                    "minutes_since_last": None,
                    "is_stale": False,
                    "table_size_bytes": None,
                    "table_size_formatted": None,
                    "error": "Tabela nie istnieje"
                }
            
            # Pobierz statystyki
            stats_query = text(f"""
                SELECT 
                    COUNT(*) as record_count,
                    MIN({date_column}) as first_record,
                    MAX({date_column}) as last_record,
                    EXTRACT(EPOCH FROM (NOW() - MAX({date_column}))) / 60 as minutes_since_last_record,
                    EXTRACT(EPOCH FROM (MAX({date_column}) - MIN({date_column}))) / 86400 as days_between_records
                FROM {table}
            """)
            
            result = conn.execute(stats_query)
            row = result.fetchone()
            
            # Pobierz rozmiar tabeli
            table_size_bytes = None
            table_size_formatted = None
            
            if is_postgresql:
                # PostgreSQL: użyj pg_total_relation_size()
                try:
                    # Używamy quote_ident do bezpiecznego escapowania nazwy tabeli
                    from sqlalchemy import text as sql_text
                    # Bezpośrednie użycie nazwy tabeli w zapytaniu (bezpieczne bo kontrolujemy źródło)
                    size_query = sql_text(f"""
                        SELECT pg_total_relation_size('{table}'::regclass)
                    """)
                    size_result = conn.execute(size_query)
                    table_size_bytes = size_result.scalar()
                    
                    # Formatuj rozmiar
                    if table_size_bytes:
                        size_query_formatted = sql_text(f"""
                            SELECT pg_size_pretty(pg_total_relation_size('{table}'::regclass))
                        """)
                        size_result_formatted = conn.execute(size_query_formatted)
                        table_size_formatted = size_result_formatted.scalar()
                except Exception as e:
                    logger.warning(f"Nie udało się pobrać rozmiaru tabeli {table}: {e}")
            else:
                # SQLite: użyj page_count * page_size
                try:
                    page_info_query = text("""
                        SELECT 
                            page_count,
                            page_size
                        FROM pragma_page_count(),
                             pragma_page_size()
                    """)
                    # Dla SQLite musimy użyć innego podejścia
                    size_query = text(f"""
                        SELECT 
                            (SELECT page_count FROM pragma_page_count()) * 
                            (SELECT page_size FROM pragma_page_size()) as size_bytes
                    """)
                    # Alternatywnie, możemy użyć bezpośredniego zapytania do sqlite_master
                    # Ale lepiej użyć page_count dla konkretnej tabeli
                    # SQLite nie ma łatwego sposobu na rozmiar pojedynczej tabeli
                    # Użyjemy przybliżenia przez page_count całej bazy
                    pass  # SQLite - pomijamy na razie, można dodać później
                except Exception as e:
                    logger.warning(f"Nie udało się pobrać rozmiaru tabeli {table} (SQLite): {e}")
            
            if row:
                record_count = row[0] or 0
                first_record = row[1]
                last_record = row[2]
                minutes_since_last = row[3] if len(row) > 3 else None
                days_between = row[4] if len(row) > 4 else None
                
                # Sprawdź czy ostatni rekord jest starszy niż 30 minut
                is_stale = False
                if minutes_since_last is not None:
                    try:
                        minutes_since_last = float(minutes_since_last)
                        is_stale = minutes_since_last > 30
                    except (ValueError, TypeError):
                        minutes_since_last = None
                
                # Oblicz przedział czasu (lata, miesiące, dni)
                time_range = None
                if days_between is not None and first_record and last_record:
                    try:
                        days_between = float(days_between)
                        if days_between > 0:
                            years = int(days_between // 365.25)
                            remaining_days = days_between - (years * 365.25)
                            months = int(remaining_days // 30.44)  # Średnia długość miesiąca
                            days = int(remaining_days - (months * 30.44))
                            
                            parts = []
                            if years > 0:
                                parts.append(f"{years} {'rok' if years == 1 else 'lata' if years < 5 else 'lat'}")
                            if months > 0:
                                parts.append(f"{months} {'miesiąc' if months == 1 else 'miesiące' if months < 5 else 'miesięcy'}")
                            if days > 0 or len(parts) == 0:
                                parts.append(f"{days} {'dzień' if days == 1 else 'dni'}")
                            
                            time_range = " ".join(parts) if parts else "0 dni"
                    except (ValueError, TypeError):
                        time_range = None
                
                # Konwertuj daty na stringi jeśli są datetime
                if first_record and isinstance(first_record, datetime):
                    first_record = first_record.isoformat()
                elif first_record:
                    first_record = str(first_record)
                
                if last_record and isinstance(last_record, datetime):
                    last_record = last_record.isoformat()
                elif last_record:
                    last_record = str(last_record)
                
                # Formatuj rozmiar jeśli nie mamy sformatowanego
                if table_size_bytes and not table_size_formatted:
                    # Konwertuj bajty na MB/GB
                    if table_size_bytes < 1024:
                        table_size_formatted = f"{table_size_bytes} B"
                    elif table_size_bytes < 1024 * 1024:
                        table_size_formatted = f"{table_size_bytes / 1024:.2f} KB"
                    elif table_size_bytes < 1024 * 1024 * 1024:
                        table_size_formatted = f"{table_size_bytes / (1024 * 1024):.2f} MB"
                    else:
                        table_size_formatted = f"{table_size_bytes / (1024 * 1024 * 1024):.2f} GB"
                
                return {
                    "record_count": record_count,
                    "first_record": first_record,
                    "last_record": last_record,
                    "time_range": time_range,  # Przedział czasu jako string (np. "3 lata 2 miesiące 5 dni")
                    "minutes_since_last": minutes_since_last,
                    "is_stale": is_stale,  # True jeśli ostatni rekord > 30 min
                    "table_size_bytes": table_size_bytes,
                    "table_size_formatted": table_size_formatted,
                    "error": None
                }
            else:
                return {
                    "record_count": 0,
                    "first_record": None,
                    "last_record": None,
                    "time_range": None,
                    "minutes_since_last": None,
                    "is_stale": False,
                    "table_size_bytes": None,
                    "table_size_formatted": None,
                    "error": None
                }
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statystyk dla {daemon_name}: {e}")
        return {
            "record_count": None,
            "first_record": None,
            "last_record": None,
            "time_range": None,
            "minutes_since_last": None,
            "is_stale": False,
            "table_size_bytes": None,
            "table_size_formatted": None,
            "error": str(e)
        }


def get_backup_info() -> Optional[Dict]:
    """Pobiera informacje o ostatnim backupie."""
    try:
        return get_last_backup_info()
    except Exception as e:
        logger.error(f"Błąd podczas pobierania informacji o backupie: {e}")
        return None


def get_daemon_status(daemon_name: str) -> Dict:
    """Pobiera szczegółowy status daemona."""
    running = is_daemon_running(daemon_name)
    
    # Pobierz dodatkowe informacje ze state files
    state_file = STATE_DIR / f"daemon_state_{daemon_name}.txt"
    restart_count_file = STATE_DIR / f"daemon_restart_count_{daemon_name}.txt"
    failure_time_file = STATE_DIR / f"daemon_failure_time_{daemon_name}.txt"
    
    state = "unknown"
    restart_count = 0
    failure_time = None
    
    if state_file.exists():
        try:
            state = state_file.read_text().strip()
        except:
            pass
    
    if restart_count_file.exists():
        try:
            restart_count = int(restart_count_file.read_text().strip())
        except:
            pass
    
    if failure_time_file.exists():
        try:
            failure_time = failure_time_file.read_text().strip()
        except:
            pass
    
    # Pobierz statystyki z bazy danych
    table_stats = get_table_stats(daemon_name)
    
    # Pobierz informacje o backupie dla database_backup_daemon
    backup_info = None
    if daemon_name == "database_backup_daemon":
        backup_info = get_backup_info()
    
    status = {
        "name": daemon_name,
        "running": running,
        "state": state,
        "restart_count": restart_count,
        "failure_time": failure_time
    }
    
    if table_stats:
        status["table_stats"] = table_stats
    
    if backup_info:
        status["backup_info"] = backup_info
    
    return status


@app.get("/")
async def root():
    """Główna strona panelu."""
    return HTMLResponse(content=get_panel_html())


@app.get("/api/status")
async def get_status():
    """Zwraca status wszystkich daemonów."""
    statuses = []
    for daemon_name in ALL_DAEMONS:
        statuses.append(get_daemon_status(daemon_name))
    
    return JSONResponse(content={
        "daemons": statuses,
        "total": len(statuses),
        "running": sum(1 for s in statuses if s["running"]),
        "stopped": sum(1 for s in statuses if not s["running"])
    })


@app.get("/api/status/{daemon_name}")
async def get_daemon_status_endpoint(daemon_name: str):
    """Zwraca status konkretnego daemona."""
    if daemon_name not in ALL_DAEMONS:
        raise HTTPException(status_code=404, detail=f"Nieznany daemon: {daemon_name}")
    
    return JSONResponse(content=get_daemon_status(daemon_name))


@app.post("/api/start/{daemon_name}")
async def start_daemon(daemon_name: str):
    """Uruchamia daemon."""
    if daemon_name not in ALL_DAEMONS:
        raise HTTPException(status_code=404, detail=f"Nieznany daemon: {daemon_name}")
    
    # Mapowanie daemonów na ich skrypty
    daemon_scripts = {
        "dydx_perpetual_market_trades_service": "daemons/dydx_perpetual_market_trades_service.sh",
        "dydx_top_traders_observer_service": "daemons/dydx_top_traders_observer_service.sh",
        "trends_sniffer_service": "daemons/trends_sniffer_service.sh",
        "btcusdc_updater": "daemons/start_btcusdc_updater.sh",
        "gdelt_sentiment_daemon": "daemons/start_gdelt_sentiment_daemon.sh",
        "market_indices_daemon": "daemons/start_market_indices_daemon.sh",
        "economic_calendar_daemon": "daemons/start_economic_calendar_daemon.sh",
        "sentiment_propagation_daemon": "daemons/start_sentiment_propagation_daemon.sh",
        "technical_indicators_daemon": "daemons/start_technical_indicators_daemon.sh",
        "order_flow_imbalance_daemon": "daemons/start_order_flow_imbalance_daemon.sh",
        "api_server": "daemons/start_api_server.sh",
        "docs_server": "daemons/start_docs_server.sh"
    }
    
    script_path = daemon_scripts.get(daemon_name)
    if not script_path:
        return JSONResponse(content={
            "success": False,
            "message": f"Nie znaleziono skryptu dla {daemon_name}",
            "daemon": daemon_name
        })
    
    script_file = PROJECT_ROOT / script_path
    if not script_file.exists():
        return JSONResponse(content={
            "success": False,
            "message": f"Skrypt nie istnieje: {script_file}",
            "daemon": daemon_name
        })
    
    # Wywołaj skrypt z --start
    try:
        cmd = ["bash", str(script_file), "--start"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        
        # Sprawdź czy daemon rzeczywiście się uruchomił
        import asyncio
        await asyncio.sleep(2)
        running = is_daemon_running(daemon_name)
        
        if running:
            return JSONResponse(content={
                "success": True,
                "message": result.stdout.strip() if result.stdout else "Daemon uruchomiony pomyślnie",
                "daemon": daemon_name
            })
        else:
            error_msg = result.stderr.strip() if result.stderr else "Daemon nie został uruchomiony"
            if result.returncode != 0:
                error_msg = f"Kod błędu: {result.returncode}. {error_msg}"
            if result.stdout:
                error_msg = f"{error_msg}\n{result.stdout.strip()}"
            return JSONResponse(content={
                "success": False,
                "message": error_msg,
                "daemon": daemon_name
            })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": str(e),
            "daemon": daemon_name
        })


@app.post("/api/stop/{daemon_name}")
async def stop_daemon(daemon_name: str):
    """Zatrzymuje daemon."""
    if daemon_name not in ALL_DAEMONS:
        raise HTTPException(status_code=404, detail=f"Nieznany daemon: {daemon_name}")
    
    # Mapowanie daemonów na ich skrypty
    daemon_scripts = {
        "dydx_perpetual_market_trades_service": "daemons/dydx_perpetual_market_trades_service.sh",
        "dydx_top_traders_observer_service": "daemons/dydx_top_traders_observer_service.sh",
        "trends_sniffer_service": "daemons/trends_sniffer_service.sh",
        "btcusdc_updater": "daemons/start_btcusdc_updater.sh",
        "gdelt_sentiment_daemon": "daemons/start_gdelt_sentiment_daemon.sh",
        "market_indices_daemon": "daemons/start_market_indices_daemon.sh",
        "economic_calendar_daemon": "daemons/start_economic_calendar_daemon.sh",
        "sentiment_propagation_daemon": "daemons/start_sentiment_propagation_daemon.sh",
        "technical_indicators_daemon": "daemons/start_technical_indicators_daemon.sh",
        "order_flow_imbalance_daemon": "daemons/start_order_flow_imbalance_daemon.sh",
        "api_server": "daemons/start_api_server.sh",
        "docs_server": "daemons/start_docs_server.sh"
    }
    
    script_path = daemon_scripts.get(daemon_name)
    if not script_path:
        return JSONResponse(content={
            "success": False,
            "message": f"Nie znaleziono skryptu dla {daemon_name}",
            "daemon": daemon_name
        })
    
    script_file = PROJECT_ROOT / script_path
    if not script_file.exists():
        return JSONResponse(content={
            "success": False,
            "message": f"Skrypt nie istnieje: {script_file}",
            "daemon": daemon_name
        })
    
    # Wywołaj skrypt z --stop
    try:
        cmd = ["bash", str(script_file), "--stop"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        
        # Sprawdź czy daemon rzeczywiście się zatrzymał
        import asyncio
        await asyncio.sleep(2)
        running = is_daemon_running(daemon_name)
        
        if not running:
            return JSONResponse(content={
                "success": True,
                "message": result.stdout.strip() if result.stdout else "Daemon zatrzymany pomyślnie",
                "daemon": daemon_name
            })
        else:
            error_msg = result.stderr.strip() if result.stderr else "Nie udało się zatrzymać daemona"
            if result.returncode != 0:
                error_msg = f"Kod błędu: {result.returncode}. {error_msg}"
            if result.stdout:
                error_msg = f"{error_msg}\n{result.stdout.strip()}"
            return JSONResponse(content={
                "success": False,
                "message": error_msg,
                "daemon": daemon_name
            })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": str(e),
            "daemon": daemon_name
        })


@app.post("/api/restart/{daemon_name}")
async def restart_daemon(daemon_name: str):
    """Restartuje daemon."""
    if daemon_name not in ALL_DAEMONS:
        raise HTTPException(status_code=404, detail=f"Nieznany daemon: {daemon_name}")
    
    # Najpierw stop, potem start
    stop_result = await stop_daemon(daemon_name)
    stop_data = json.loads(stop_result.body)
    
    import asyncio
    await asyncio.sleep(2)
    
    start_result = await start_daemon(daemon_name)
    start_data = json.loads(start_result.body)
    
    if start_data.get("success", False):
        return JSONResponse(content={
            "success": True,
            "message": f"Restart zakończony pomyślnie. Stop: {stop_data.get('message', 'OK')}. Start: {start_data.get('message', 'OK')}",
            "daemon": daemon_name
        })
    else:
        error_msg = f"Błąd restartu. Stop: {stop_data.get('message', 'OK')}. Start: {start_data.get('message', 'Błąd')}"
        return JSONResponse(content={
            "success": False,
            "message": error_msg,
            "daemon": daemon_name
        })


@app.get("/api/master/status")
async def get_master_status():
    """Zwraca status master daemon."""
    result = run_master_command(["--status"])
    return JSONResponse(content={
        "success": result["success"],
        "output": result["output"],
        "error": result["error"]
    })


@app.post("/api/master/stop")
async def stop_master():
    """Zatrzymuje master daemon."""
    result = run_master_command(["--stop"])
    return JSONResponse(content={
        "success": result["success"],
        "message": result["output"] if result["success"] else result["error"]
    })


@app.post("/api/backup/run")
async def run_backup():
    """Uruchamia backup bazy danych na żądanie."""
    try:
        backup_script = PROJECT_ROOT / "daemons" / "start_database_backup_daemon.sh"
        if not backup_script.exists():
            raise HTTPException(status_code=404, detail="Skrypt backupu nie istnieje")
        
        # Uruchom backup jednorazowo
        cmd = ["bash", str(backup_script), "--once"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 godzina timeout
            cwd=str(PROJECT_ROOT)
        )
        
        # Pobierz informacje o backupie
        backup_info = get_backup_info()
        
        return JSONResponse(content={
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr,
            "backup_info": backup_info
        })
    except subprocess.TimeoutExpired:
        return JSONResponse(content={
            "success": False,
            "message": "Timeout - backup trwał zbyt długo",
            "backup_info": None
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "message": str(e),
            "backup_info": None
        })


@app.get("/api/backup/info")
async def get_backup_info_endpoint():
    """Zwraca informacje o ostatnim backupie."""
    backup_info = get_backup_info()
    return JSONResponse(content=backup_info or {})


@app.get("/api/top-trader-alerts")
async def get_top_trader_alerts(
    limit: int = 50,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    unread_only: bool = False
):
    """
    Zwraca alerty top traderów.
    
    Args:
        limit: Maksymalna liczba alertów do zwrócenia
        severity: Filtr po ważności (low, medium, high, critical)
        alert_type: Filtr po typie (LARGE_TRADE, VOLUME_SPIKE, etc.)
        unread_only: Tylko nieprzeczytane alerty
    """
    try:
        engine = get_database_engine()
        
        query = """
            SELECT 
                id,
                alert_timestamp,
                trader_address,
                subaccount_number,
                trader_rank,
                fill_id,
                ticker,
                side,
                price,
                size,
                volume_usd,
                alert_type,
                alert_severity,
                alert_message,
                threshold_value,
                actual_value,
                is_read,
                created_at
            FROM dydx_top_trader_alerts
            WHERE 1=1
        """
        params = {}
        
        if unread_only:
            query += " AND is_read = FALSE"
        
        if severity:
            query += " AND alert_severity = :severity"
            params['severity'] = severity
        
        if alert_type:
            query += " AND alert_type = :alert_type"
            params['alert_type'] = alert_type
        
        query += " ORDER BY alert_timestamp DESC LIMIT :limit"
        params['limit'] = limit
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            alerts = []
            for row in result:
                alerts.append({
                    'id': row[0],
                    'alert_timestamp': row[1].isoformat() if row[1] else None,
                    'trader_address': row[2],
                    'subaccount_number': row[3],
                    'trader_rank': row[4],
                    'fill_id': row[5],
                    'ticker': row[6],
                    'side': row[7],
                    'price': float(row[8]) if row[8] else None,
                    'size': float(row[9]) if row[9] else None,
                    'volume_usd': float(row[10]) if row[10] else None,
                    'alert_type': row[11],
                    'alert_severity': row[12],
                    'alert_message': row[13],
                    'threshold_value': float(row[14]) if row[14] else None,
                    'actual_value': float(row[15]) if row[15] else None,
                    'is_read': row[16],
                    'created_at': row[17].isoformat() if row[17] else None,
                })
        
        return JSONResponse(content={
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania alertów: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/top-trader-alerts/summary")
async def get_top_trader_alerts_summary(hours: int = 24):
    """
    Zwraca agregowane statystyki alertów.
    
    Args:
        hours: Liczba godzin wstecz do analizy
    """
    try:
        engine = get_database_engine()
        
        query = """
            SELECT 
                alert_type,
                alert_severity,
                COUNT(*) as count,
                COUNT(DISTINCT trader_address || ':' || subaccount_number) as unique_traders,
                SUM(volume_usd) as total_volume_usd,
                AVG(volume_usd) as avg_volume_usd,
                MAX(volume_usd) as max_volume_usd
            FROM dydx_top_trader_alerts
            WHERE alert_timestamp >= NOW() - INTERVAL ':hours hours'
            GROUP BY alert_type, alert_severity
            ORDER BY alert_severity DESC, count DESC
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query.replace(':hours', str(hours))))
            summary = []
            for row in result:
                summary.append({
                    'alert_type': row[0],
                    'alert_severity': row[1],
                    'count': row[2],
                    'unique_traders': row[3],
                    'total_volume_usd': float(row[4]) if row[4] else 0,
                    'avg_volume_usd': float(row[5]) if row[5] else 0,
                    'max_volume_usd': float(row[6]) if row[6] else 0,
                })
        
        return JSONResponse(content={
            'summary': summary,
            'hours': hours
        })
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania podsumowania alertów: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/top-trader-alerts/{alert_id}/read")
async def mark_alert_read(alert_id: int):
    """Oznacza alert jako przeczytany."""
    try:
        engine = get_database_engine()
        
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE dydx_top_trader_alerts SET is_read = TRUE WHERE id = :id"),
                {'id': alert_id}
            )
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Alert {alert_id} nie znaleziony")
        
        return JSONResponse(content={'success': True, 'alert_id': alert_id})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas oznaczania alertu jako przeczytany: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_panel_html() -> str:
    """Generuje HTML panelu zarządzania."""
    return """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Zarządzania Daemonami - Trends Sniffer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #1e1e1e;
            padding: 20px;
            color: #cccccc;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            background: #252526;
            color: #cccccc;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #3e3e42;
        }
        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
            color: #ffffff;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        .stat-card {
            background: #2d2d30;
            padding: 15px 20px;
            border-radius: 8px;
            flex: 1;
            border: 1px solid #3e3e42;
        }
        .stat-label {
            color: #858585;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #ffffff;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #0e639c;
            color: #ffffff;
        }
        .btn-primary:hover {
            background: #1177bb;
        }
        .btn-danger {
            background: #a1260d;
            color: #ffffff;
        }
        .btn-danger:hover {
            background: #c72e1a;
        }
        .btn-success {
            background: #0e7c0e;
            color: #ffffff;
        }
        .btn-success:hover {
            background: #0f9d0f;
        }
        .daemon-grid {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .daemon-card {
            background: #252526;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid #3e3e42;
            width: 100%;
        }
        .daemon-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.5);
            border-color: #505050;
        }
        .daemon-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .daemon-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #ffffff;
        }
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status-running {
            background: #0e7c0e;
            color: #ffffff;
        }
        .status-stopped {
            background: #a1260d;
            color: #ffffff;
        }
        .status-unknown {
            background: #7a5f00;
            color: #ffffff;
        }
        .daemon-info {
            margin: 15px 0;
            font-size: 0.9em;
            color: #cccccc;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
        }
        .daemon-info-item {
            margin: 5px 0;
        }
        .daemon-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            justify-content: flex-end;
        }
        .daemon-actions button {
            padding: 8px 20px;
            font-size: 0.9em;
            min-width: 120px;
        }
        .daemon-actions button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #858585;
        }
        .error {
            background: #3a1d1d;
            color: #f48771;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border: 1px solid #a1260d;
        }
        .success {
            background: #1e3a1e;
            color: #89d185;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border: 1px solid #0e7c0e;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .spinner {
            border: 3px solid #3e3e42;
            border-top: 3px solid #0e639c;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Panel Zarządzania Daemonami</h1>
            <p>Trends Sniffer - Monitorowanie i kontrola daemonów</p>
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-label">Wszystkie</div>
                    <div class="stat-value" id="stat-total">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Działające</div>
                    <div class="stat-value" id="stat-running">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Zatrzymane</div>
                    <div class="stat-value" id="stat-stopped">-</div>
                </div>
            </div>
        </header>
        
        <div class="controls">
            <button class="btn-primary" onclick="refreshStatus()">🔄 Odśwież</button>
            <button class="btn-success" onclick="startAll()">▶️ Uruchom wszystkie</button>
            <button class="btn-danger" onclick="stopAll()">⏹️ Zatrzymaj wszystkie</button>
        </div>
        
        <div id="message"></div>
        
        <div id="daemons" class="daemon-grid">
            <div class="loading">Ładowanie statusu daemonów...</div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        function formatDate(dateStr) {
            if (!dateStr) return 'N/A';
            try {
                const date = new Date(dateStr);
                if (isNaN(date.getTime())) return dateStr;
                return date.toLocaleString('pl-PL', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            } catch (e) {
                return dateStr;
            }
        }
        
        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update stats
                document.getElementById('stat-total').textContent = data.total;
                document.getElementById('stat-running').textContent = data.running;
                document.getElementById('stat-stopped').textContent = data.stopped;
                
                // Render daemons
                const daemonsDiv = document.getElementById('daemons');
                daemonsDiv.innerHTML = data.daemons.map(daemon => `
                    <div class="daemon-card" data-daemon="${daemon.name}">
                        <div class="daemon-header">
                            <div class="daemon-name">${daemon.name}</div>
                            <span class="status-badge ${daemon.running ? 'status-running' : 'status-stopped'}">
                                ${daemon.running ? '✓ Działa' : '✗ Zatrzymany'}
                            </span>
                        </div>
                        <div class="daemon-info">
                            <div class="daemon-info-item">Stan: ${daemon.state}</div>
                            ${daemon.restart_count > 0 ? `<div class="daemon-info-item">Restartów: ${daemon.restart_count}</div>` : ''}
                            ${daemon.failure_time ? `<div class="daemon-info-item">Błąd od: ${new Date(parseInt(daemon.failure_time) * 1000).toLocaleString()}</div>` : ''}
                            ${daemon.table_stats ? `
                                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #3e3e42;">
                                    <div style="font-weight: 600; margin-bottom: 8px; color: #ffffff;">📊 Statystyki tabeli:</div>
                                    ${daemon.table_stats.error 
                                        ? `<div class="daemon-info-item" style="color: #f48771;">Błąd: ${daemon.table_stats.error}</div>`
                                        : `
                                            <div class="daemon-info-item">Rekordów: <strong>${daemon.table_stats.record_count !== null ? daemon.table_stats.record_count.toLocaleString() : 'N/A'}</strong></div>
                                            ${daemon.table_stats.table_size_formatted 
                                                ? `<div class="daemon-info-item">Rozmiar danych: <strong style="color: #4ec9b0;">${daemon.table_stats.table_size_formatted}</strong></div>`
                                                : ''
                                            }
                                            ${daemon.table_stats.first_record 
                                                ? `<div class="daemon-info-item">Pierwszy rekord: ${formatDate(daemon.table_stats.first_record)}</div>`
                                                : '<div class="daemon-info-item">Pierwszy rekord: Brak danych</div>'
                                            }
                                            ${daemon.table_stats.last_record 
                                                ? `<div class="daemon-info-item" ${daemon.table_stats.is_stale ? 'style="color: #f48771; font-weight: 600;"' : ''}>Ostatni rekord: ${formatDate(daemon.table_stats.last_record)}${daemon.table_stats.is_stale && daemon.table_stats.minutes_since_last !== null ? ` <span style="color: #f48771;">⚠️ (${Math.round(daemon.table_stats.minutes_since_last)} min temu)</span>` : ''}${daemon.table_stats.time_range ? `<br><span style="color: #858585; font-size: 0.85em;">Przedział: ${daemon.table_stats.time_range}</span>` : ''}</div>`
                                                : '<div class="daemon-info-item">Ostatni rekord: Brak danych</div>'
                                            }
                                        `
                                    }
                                </div>
                            ` : ''}
                            ${daemon.backup_info ? `
                                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #3e3e42;">
                                    <div style="font-weight: 600; margin-bottom: 8px; color: #ffffff;">💾 Ostatni backup:</div>
                                    ${daemon.backup_info.timestamp 
                                        ? `<div class="daemon-info-item">Data: <strong>${formatDate(daemon.backup_info.timestamp)}</strong></div>`
                                        : '<div class="daemon-info-item">Brak backupu</div>'
                                    }
                                    ${daemon.backup_info.size_formatted 
                                        ? `<div class="daemon-info-item">Rozmiar: <strong style="color: #89d185;">${daemon.backup_info.size_formatted}</strong></div>`
                                        : ''
                                    }
                                    ${daemon.backup_info.file_path 
                                        ? `<div class="daemon-info-item" style="font-size: 0.85em; color: #858585;">${daemon.backup_info.file_path.split('/').pop()}</div>`
                                        : ''
                                    }
                                </div>
                            ` : ''}
                        </div>
                        <div class="daemon-actions">
                            ${daemon.name === 'database_backup_daemon' 
                                ? `<button class="btn-success" onclick="runBackup()" style="width: 100%;">💾 Uruchom backup</button>`
                                : daemon.running 
                                    ? `<button class="btn-danger" onclick="stopDaemon('${daemon.name}')">⏹️ Stop</button>
                                       <button class="btn-primary" onclick="restartDaemon('${daemon.name}')">🔄 Restart</button>`
                                    : `<button class="btn-success" onclick="startDaemon('${daemon.name}')">▶️ Start</button>`
                            }
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                showMessage('Błąd podczas odświeżania statusu: ' + error.message, 'error');
            }
        }
        
        async function startDaemon(name) {
            const card = document.querySelector(`[data-daemon="${name}"]`);
            if (!card) return;
            
            const buttons = card.querySelectorAll('.daemon-actions button');
            const originalButtons = Array.from(buttons).map(btn => ({
                element: btn,
                html: btn.innerHTML,
                disabled: btn.disabled
            }));
            
            // Wyszarz przyciski i pokaż spinner
            buttons.forEach(btn => {
                btn.disabled = true;
                if (btn.textContent.includes('Start')) {
                    btn.innerHTML = '<span class="spinner"></span> Uruchamianie...';
                }
            });
            
            showMessage('Uruchamianie ' + name + '...', 'info');
            
            try {
                const response = await fetch(`/api/start/${name}`, { method: 'POST' });
                const data = await response.json();
                
                // Przywróć przyciski
                originalButtons.forEach(orig => {
                    orig.element.disabled = orig.disabled;
                    orig.element.innerHTML = orig.html;
                });
                
                if (data.success) {
                    showMessage('Daemon ' + name + ' uruchomiony', 'success');
                    setTimeout(refreshStatus, 2000);
                } else {
                    const errorMsg = data.message || 'Nieznany błąd';
                    showMessage('Błąd uruchomienia ' + name + ': ' + errorMsg, 'error');
                }
            } catch (error) {
                // Przywróć przyciski
                originalButtons.forEach(orig => {
                    orig.element.disabled = orig.disabled;
                    orig.element.innerHTML = orig.html;
                });
                
                showMessage('Błąd połączenia: ' + error.message, 'error');
            }
        }
        
        async function stopDaemon(name) {
            const card = document.querySelector(`[data-daemon="${name}"]`);
            if (!card) return;
            
            const buttons = card.querySelectorAll('.daemon-actions button');
            const originalButtons = Array.from(buttons).map(btn => ({
                element: btn,
                html: btn.innerHTML,
                disabled: btn.disabled
            }));
            
            // Wyszarz przyciski i pokaż spinner
            buttons.forEach(btn => {
                btn.disabled = true;
                const btnText = btn.textContent.trim();
                if (btnText.includes('Stop') || btnText.includes('⏹')) {
                    btn.innerHTML = '<span class="spinner"></span> Zatrzymywanie...';
                }
            });
            
            showMessage('Zatrzymywanie ' + name + '...', 'info');
            
            try {
                const response = await fetch(`/api/stop/${name}`, { method: 'POST' });
                const data = await response.json();
                
                // Przywróć przyciski
                originalButtons.forEach(orig => {
                    orig.element.disabled = orig.disabled;
                    orig.element.innerHTML = orig.html;
                });
                
                if (data.success) {
                    showMessage('Daemon ' + name + ' zatrzymany', 'success');
                    setTimeout(refreshStatus, 2000);
                } else {
                    const errorMsg = data.message || 'Nieznany błąd';
                    showMessage('Błąd zatrzymania ' + name + ': ' + errorMsg, 'error');
                }
            } catch (error) {
                // Przywróć przyciski
                originalButtons.forEach(orig => {
                    orig.element.disabled = orig.disabled;
                    orig.element.innerHTML = orig.html;
                });
                
                showMessage('Błąd połączenia: ' + error.message, 'error');
            }
        }
        
        async function restartDaemon(name) {
            const card = document.querySelector(`[data-daemon="${name}"]`);
            if (!card) return;
            
            const buttons = card.querySelectorAll('.daemon-actions button');
            const originalButtons = Array.from(buttons).map(btn => ({
                element: btn,
                html: btn.innerHTML,
                disabled: btn.disabled
            }));
            
            // Wyszarz przyciski i pokaż spinner
            buttons.forEach(btn => {
                btn.disabled = true;
                const btnText = btn.textContent.trim();
                if (btnText.includes('Restart') || btnText.includes('🔄')) {
                    btn.innerHTML = '<span class="spinner"></span> Restartowanie...';
                }
            });
            
            showMessage('Restartowanie ' + name + '...', 'info');
            
            try {
                const response = await fetch(`/api/restart/${name}`, { method: 'POST' });
                const data = await response.json();
                
                // Przywróć przyciski
                originalButtons.forEach(orig => {
                    orig.element.disabled = orig.disabled;
                    orig.element.innerHTML = orig.html;
                });
                
                if (data.success) {
                    showMessage('Daemon ' + name + ' zrestartowany', 'success');
                    setTimeout(refreshStatus, 3000);
                } else {
                    const errorMsg = data.message || 'Nieznany błąd';
                    showMessage('Błąd restartu ' + name + ': ' + errorMsg, 'error');
                }
            } catch (error) {
                // Przywróć przyciski
                originalButtons.forEach(orig => {
                    orig.element.disabled = orig.disabled;
                    orig.element.innerHTML = orig.html;
                });
                
                showMessage('Błąd połączenia: ' + error.message, 'error');
            }
        }
        
        async function startAll() {
            if (!confirm('Uruchomić wszystkie daemony?')) return;
            showMessage('Uruchamianie wszystkich daemonów...', 'info');
            const daemons = await (await fetch('/api/status')).json();
            for (const daemon of daemons.daemons) {
                if (!daemon.running) {
                    await startDaemon(daemon.name);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            setTimeout(refreshStatus, 3000);
        }
        
        async function stopAll() {
            if (!confirm('Zatrzymać wszystkie daemony?')) return;
            showMessage('Zatrzymywanie wszystkich daemonów...', 'info');
            const daemons = await (await fetch('/api/status')).json();
            for (const daemon of daemons.daemons) {
                if (daemon.running) {
                    await stopDaemon(daemon.name);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            setTimeout(refreshStatus, 3000);
        }
        
        async function runBackup() {
            if (!confirm('Uruchomić backup bazy danych? Operacja może zająć kilka minut.')) return;
            showMessage('Uruchamianie backupu bazy danych...', 'info');
            try {
                const response = await fetch('/api/backup/run', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    showMessage('Backup zakończony pomyślnie', 'success');
                    setTimeout(refreshStatus, 2000);
                } else {
                    showMessage('Błąd backupu: ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('Błąd: ' + error.message, 'error');
            }
        }
        
        function showMessage(message, type) {
            const msgDiv = document.getElementById('message');
            msgDiv.className = type;
            msgDiv.textContent = message;
            msgDiv.style.display = 'block';
            if (type !== 'error') {
                setTimeout(() => {
                    msgDiv.style.display = 'none';
                }, 3000);
            }
        }
        
        // Auto-refresh co 1 sekundę
        refreshInterval = setInterval(refreshStatus, 1000);
        
        // Initial load
        refreshStatus();
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)

