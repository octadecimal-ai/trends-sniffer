#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Backup Daemon
======================
Daemon wykonujący backup bazy danych PostgreSQL raz dziennie lub na żądanie.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from loguru import logger
import psycopg2
from urllib.parse import urlparse

# Konfiguracja
PROJECT_ROOT = Path(__file__).parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
STATE_DIR = PROJECT_ROOT / ".dev" / "state"
LOG_DIR = PROJECT_ROOT / ".dev" / "logs"

# Utwórz katalogi
BACKUP_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Załaduj zmienne środowiskowe
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Konfiguracja
BACKUP_TIME = os.getenv("BACKUP_TIME", "02:00")  # Domyślnie 2:00 w nocy
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))  # Przechowuj 30 dni


def get_database_url():
    """Pobiera DATABASE_URL z zmiennych środowiskowych."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL nie jest ustawiony w pliku .env")
    return database_url


def parse_database_url(database_url: str) -> dict:
    """Parsuje DATABASE_URL i zwraca komponenty."""
    parsed = urlparse(database_url)
    database = parsed.path.lstrip('/')
    
    # Jeśli database jest puste, spróbuj wyciągnąć z query string
    if not database:
        from urllib.parse import parse_qs
        query_params = parse_qs(parsed.query)
        if 'dbname' in query_params:
            database = query_params['dbname'][0]
    
    # Jeśli nadal puste, użyj domyślnej nazwy
    if not database:
        database = "trends_sniffer"  # Domyślna nazwa bazy
    
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": database,
        "user": parsed.username,
        "password": parsed.password
    }


def perform_backup() -> dict:
    """
    Wykonuje backup bazy danych.
    
    Returns:
        dict: Informacje o backupie {success: bool, file_path: str, size: int, error: str}
    """
    try:
        database_url = get_database_url()
        db_info = parse_database_url(database_url)
        
        # Walidacja
        if not db_info.get("database"):
            raise ValueError("Nie można określić nazwy bazy danych z DATABASE_URL")
        if not db_info.get("user"):
            raise ValueError("Brak użytkownika w DATABASE_URL")
        
        # Utwórz nazwę pliku backupu
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"backup_{db_info['database']}_{timestamp}.sql.gz"
        
        logger.info(f"Rozpoczynam backup bazy danych: {db_info['database']}")
        
        # Wykonaj pg_dump
        pg_dump_cmd = [
            "pg_dump",
            "-h", db_info["host"],
            "-p", str(db_info["port"]),
            "-U", db_info["user"],
            "-d", db_info["database"],
            "-F", "c",  # Custom format (binarny, kompresowany)
            "-f", str(backup_file)
        ]
        
        # Ustaw zmienną środowiskową z hasłem (jeśli dostępne)
        env = os.environ.copy()
        if db_info.get("password"):
            env["PGPASSWORD"] = db_info["password"]
        # Jeśli brak hasła, pg_dump użyje peer authentication lub .pgpass
        
        # Wykonaj backup
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600  # 1 godzina timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Nieznany błąd"
            logger.error(f"Błąd podczas backupu: {error_msg}")
            return {
                "success": False,
                "file_path": None,
                "size": 0,
                "error": error_msg
            }
        
        # Sprawdź rozmiar pliku
        backup_size = backup_file.stat().st_size if backup_file.exists() else 0
        
        logger.success(f"Backup zakończony pomyślnie: {backup_file.name} ({backup_size / (1024*1024):.2f} MB)")
        
        # Zapisz informacje o backupie
        save_backup_info(backup_file, backup_size)
        
        # Usuń stare backupy
        cleanup_old_backups()
        
        return {
            "success": True,
            "file_path": str(backup_file),
            "size": backup_size,
            "error": None
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "Timeout - backup trwał zbyt długo (>1h)"
        logger.error(error_msg)
        return {
            "success": False,
            "file_path": None,
            "size": 0,
            "error": error_msg
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Błąd podczas backupu: {error_msg}")
        return {
            "success": False,
            "file_path": None,
            "size": 0,
            "error": error_msg
        }


def save_backup_info(backup_file: Path, backup_size: int):
    """Zapisuje informacje o backupie do pliku state."""
    info_file = STATE_DIR / "last_backup_info.txt"
    with open(info_file, 'w') as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"{backup_file}\n")
        f.write(f"{backup_size}\n")


def get_last_backup_info() -> dict:
    """Pobiera informacje o ostatnim backupie."""
    info_file = STATE_DIR / "last_backup_info.txt"
    if not info_file.exists():
        return {
            "timestamp": None,
            "file_path": None,
            "size": None,
            "size_formatted": None
        }
    
    try:
        with open(info_file, 'r') as f:
            lines = f.readlines()
            timestamp = lines[0].strip() if len(lines) > 0 else None
            file_path = lines[1].strip() if len(lines) > 1 else None
            size_str = lines[2].strip() if len(lines) > 2 else None
            
            size = int(size_str) if size_str and size_str.isdigit() else None
            size_formatted = format_size(size) if size else None
            
            return {
                "timestamp": timestamp,
                "file_path": file_path,
                "size": size,
                "size_formatted": size_formatted
            }
    except Exception as e:
        logger.warning(f"Błąd podczas odczytu informacji o backupie: {e}")
        return {
            "timestamp": None,
            "file_path": None,
            "size": None,
            "size_formatted": None
        }


def format_size(size_bytes: int) -> str:
    """Formatuje rozmiar w bajtach do czytelnej formy."""
    if not size_bytes:
        return "N/A"
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def cleanup_old_backups():
    """Usuwa stare backupy starsze niż BACKUP_RETENTION_DAYS."""
    try:
        cutoff_time = time.time() - (BACKUP_RETENTION_DAYS * 24 * 60 * 60)
        deleted_count = 0
        
        for backup_file in BACKUP_DIR.glob("backup_*.sql.gz"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"Usunięto stary backup: {backup_file.name}")
        
        if deleted_count > 0:
            logger.info(f"Usunięto {deleted_count} starych backupów")
    except Exception as e:
        logger.warning(f"Błąd podczas czyszczenia starych backupów: {e}")


def wait_until_time(target_time: str):
    """Czeka do określonej godziny."""
    target_hour, target_minute = map(int, target_time.split(':'))
    
    while True:
        now = datetime.now()
        target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Jeśli już minęła dzisiejsza godzina, ustaw na jutro
        if target < now:
            from datetime import timedelta
            target += timedelta(days=1)
        
        wait_seconds = (target - now).total_seconds()
        logger.info(f"Czekam do {target_time} ({wait_seconds / 3600:.1f} godzin)")
        time.sleep(min(wait_seconds, 3600))  # Sprawdzaj co godzinę
        
        # Sprawdź czy już czas
        now = datetime.now()
        if now.hour == target_hour and now.minute >= target_minute:
            break


def main():
    """Główna funkcja daemona."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Backup Daemon")
    parser.add_argument("--once", action="store_true", help="Wykonaj backup raz i zakończ")
    parser.add_argument("--daemon", action="store_true", help="Uruchom jako daemon (raz dziennie)")
    args = parser.parse_args()
    
    # Konfiguracja logowania
    log_file = LOG_DIR / f"database_backup_daemon_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(log_file, rotation="1 day", retention="30 days")
    
    logger.info("=" * 80)
    logger.info("Database Backup Daemon uruchomiony")
    logger.info(f"Katalog backupów: {BACKUP_DIR}")
    logger.info(f"Czas backupu: {BACKUP_TIME}")
    logger.info(f"Retention: {BACKUP_RETENTION_DAYS} dni")
    logger.info("=" * 80)
    
    if args.once:
        # Wykonaj backup raz
        logger.info("Tryb jednorazowy - wykonuję backup...")
        result = perform_backup()
        if result["success"]:
            logger.success("Backup zakończony pomyślnie")
            sys.exit(0)
        else:
            logger.error(f"Backup zakończony błędem: {result['error']}")
            sys.exit(1)
    
    elif args.daemon:
        # Uruchom jako daemon
        logger.info("Tryb daemon - backup raz dziennie o {BACKUP_TIME}")
        
        while True:
            try:
                # Wykonaj backup
                result = perform_backup()
                if result["success"]:
                    logger.success("Backup zakończony pomyślnie")
                else:
                    logger.error(f"Backup zakończony błędem: {result['error']}")
                
                # Czekaj do następnego dnia
                wait_until_time(BACKUP_TIME)
                
            except KeyboardInterrupt:
                logger.info("Otrzymano sygnał przerwania - kończenie...")
                break
            except Exception as e:
                logger.error(f"Nieoczekiwany błąd: {e}")
                time.sleep(3600)  # Czekaj godzinę przed ponowną próbą
    
    else:
        # Domyślnie wykonaj backup raz
        logger.info("Wykonuję backup...")
        result = perform_backup()
        if result["success"]:
            logger.success("Backup zakończony pomyślnie")
            sys.exit(0)
        else:
            logger.error(f"Backup zakończony błędem: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()

