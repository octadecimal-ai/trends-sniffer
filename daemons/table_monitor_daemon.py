#!/usr/bin/env python3
"""
Table Monitor Daemon
===================
Skrypt działający w tle, który monitoruje aktualizacje tabel w bazie danych.
W przypadku wykrycia, że któraś z tabel nie jest aktualizowana, odtwarza dźwięk
i wysyła email z powiadomieniem.

Użycie:
    python scripts/table_monitor_daemon.py
    python scripts/table_monitor_daemon.py --interval=1800 --threshold-hours=2
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import smtplib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# Dodaj ścieżkę projektu
sys.path.insert(0, str(Path(__file__).parent.parent))

# Załaduj zmienne środowiskowe z .env jeśli istnieje
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                os.environ.setdefault(key, value)

from loguru import logger
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Konfiguracja loggera
logger.remove()
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"table_monitor_daemon_{datetime.now().strftime('%Y%m%d')}.log"
logger.add(
    log_file,
    rotation="00:00",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO"
)
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO"
)


class TableMonitorDaemon:
    """
    Daemon monitorujący aktualizacje tabel w bazie danych.
    """
    
    def __init__(
        self,
        interval: int = 1800,  # 30 minut
        threshold_hours: float = 2.0,  # Próg: jeśli ostatnia aktualizacja starsza niż 2 godziny
        email_recipient: str = "octadecimal@octadecimal.pl",
        sound_file: Optional[str] = None
    ):
        self.interval = interval
        self.threshold_hours = threshold_hours
        self.email_recipient = email_recipient
        self.running = False
        
        # Ścieżka do pliku dźwiękowego (domyślnie użyj systemowego dźwięku na macOS)
        if sound_file:
            self.sound_file = sound_file
        else:
            # Domyślny dźwięk systemowy na macOS
            self.sound_file = "/System/Library/Sounds/Basso.aiff"
        
        # Połącz z bazą danych
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("Brak zmiennej środowiskowej DATABASE_URL")
        
        self.conn = psycopg2.connect(database_url)
        logger.info("✓ Połączono z bazą danych")
        
        # Statystyki
        self.stats = {
            "checks_count": 0,
            "alerts_count": 0,
            "last_check": None
        }
        
        # Obsługa sygnałów
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Obsługuje sygnały zatrzymania."""
        logger.info(f"Otrzymano sygnał {signum} - zatrzymywanie...")
        self.running = False
    
    def _get_table_stats(self) -> List[Dict]:
        """Pobiera statystyki tabel z widoku v_table_stats."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        tabela,
                        liczba_rekordow,
                        ostatnia_aktualizacja,
                        ostatnie_wystapienie
                    FROM v_table_stats
                    ORDER BY tabela
                """)
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'tabela': row[0],
                        'liczba_rekordow': row[1],
                        'ostatnia_aktualizacja': row[2],
                        'ostatnie_wystapienie': row[3]
                    })
                return results
        except Exception as e:
            logger.error(f"Błąd podczas pobierania statystyk tabel: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def _check_tables(self) -> List[Dict]:
        """Sprawdza, które tabele nie są aktualizowane."""
        stats = self._get_table_stats()
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=self.threshold_hours)
        problematic_tables = []
        
        for stat in stats:
            last_update = stat['ostatnia_aktualizacja']
            if last_update and last_update < threshold_time:
                problematic_tables.append({
                    'tabela': stat['tabela'],
                    'liczba_rekordow': stat['liczba_rekordow'],
                    'ostatnia_aktualizacja': last_update,
                    'ostatnie_wystapienie': stat['ostatnie_wystapienie'],
                    'opoznienie_godziny': (datetime.now(timezone.utc) - last_update).total_seconds() / 3600
                })
        
        return problematic_tables
    
    def _play_sound(self):
        """Odtwarza dźwięk alarmowy."""
        try:
            if os.path.exists(self.sound_file):
                subprocess.run(['afplay', self.sound_file], check=False)
                logger.info(f"✓ Odtworzono dźwięk: {self.sound_file}")
            else:
                # Fallback: użyj systemowego polecenia say (text-to-speech)
                subprocess.run(['say', 'Alert! Table update problem detected.'], check=False)
                logger.info("✓ Odtworzono dźwięk przez say")
        except Exception as e:
            logger.warning(f"Nie udało się odtworzyć dźwięku: {e}")
    
    def _send_email(self, problematic_tables: List[Dict]):
        """Wysyła email z powiadomieniem o problemach z tabelami."""
        try:
            # Konfiguracja SMTP z .env
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            smtp_from = os.getenv('SMTP_FROM', smtp_user)
            
            if not smtp_user or not smtp_password:
                logger.warning("Brak konfiguracji SMTP w .env - pomijam wysyłanie emaila")
                return
            
            # Przygotuj treść emaila
            subject = f"⚠️ Alert: Problemy z aktualizacją tabel ({len(problematic_tables)} tabel)"
            
            body_lines = [
                "Wykryto problemy z aktualizacją tabel w bazie danych.",
                "",
                f"Data sprawdzenia: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                f"Próg: {self.threshold_hours} godzin",
                "",
                "Problematyczne tabele:",
                ""
            ]
            
            for table in problematic_tables:
                body_lines.append(f"  • {table['tabela']}")
                body_lines.append(f"    - Liczba rekordów: {table['liczba_rekordow']:,}")
                body_lines.append(f"    - Ostatnia aktualizacja: {table['ostatnia_aktualizacja']}")
                body_lines.append(f"    - Ostatnie wystąpienie: {table['ostatnie_wystapienie']}")
                body_lines.append(f"    - Opóźnienie: {table['opoznienie_godziny']:.2f} godzin")
                body_lines.append("")
            
            body = "\n".join(body_lines)
            
            # Utwórz wiadomość
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = self.email_recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Wyślij email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✓ Wysłano email do {self.email_recipient}")
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania emaila: {e}")
            logger.debug(traceback.format_exc())
    
    def _check_and_alert(self):
        """Sprawdza tabele i wysyła alerty jeśli potrzeba."""
        self.stats["checks_count"] += 1
        self.stats["last_check"] = datetime.now(timezone.utc)
        
        logger.info(f"🔍 Sprawdzanie tabel (sprawdzenie #{self.stats['checks_count']})...")
        
        problematic_tables = self._check_tables()
        
        if problematic_tables:
            self.stats["alerts_count"] += 1
            logger.warning(f"⚠️ Wykryto {len(problematic_tables)} problematycznych tabel:")
            for table in problematic_tables:
                logger.warning(
                    f"  • {table['tabela']}: ostatnia aktualizacja "
                    f"{table['opoznienie_godziny']:.2f} godzin temu "
                    f"({table['ostatnia_aktualizacja']})"
                )
            
            # Odtwórz dźwięk
            self._play_sound()
            
            # Wyślij email
            self._send_email(problematic_tables)
        else:
            logger.info("✓ Wszystkie tabele są aktualizowane prawidłowo")
    
    def run(self):
        """Główna pętla daemona."""
        logger.info("=" * 60)
        logger.info("🚀 Table Monitor Daemon uruchomiony")
        logger.info("=" * 60)
        logger.info(f"Interwał sprawdzania: {self.interval} sekund ({self.interval / 60:.1f} minut)")
        logger.info(f"Próg: {self.threshold_hours} godzin")
        logger.info(f"Email: {self.email_recipient}")
        logger.info(f"Dźwięk: {self.sound_file}")
        logger.info("=" * 60)
        
        self.running = True
        
        while self.running:
            try:
                self._check_and_alert()
                
                # Czekaj do następnego sprawdzenia
                if self.running:
                    logger.info(f"⏳ Czekam {self.interval} sekund do następnego sprawdzenia...")
                    time.sleep(self.interval)
                    
            except KeyboardInterrupt:
                logger.info("Otrzymano KeyboardInterrupt - zatrzymywanie...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Błąd w głównej pętli: {e}")
                logger.debug(traceback.format_exc())
                self.stats["alerts_count"] += 1
                if self.running:
                    time.sleep(60)  # Czekaj 1 minutę przed ponowną próbą
        
        logger.info("=" * 60)
        logger.info("🛑 Table Monitor Daemon zatrzymany")
        logger.info("=" * 60)
        logger.info(f"Statystyki końcowe:")
        logger.info(f"  Sprawdzenia: {self.stats['checks_count']}")
        logger.info(f"  Alerty: {self.stats['alerts_count']}")
        logger.info("=" * 60)
        
        if self.conn:
            self.conn.close()


def main():
    """Główna funkcja."""
    parser = argparse.ArgumentParser(
        description='Daemon monitorujący aktualizacje tabel w bazie danych'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=1800,
        help='Interwał sprawdzania w sekundach (domyślnie: 1800 = 30 minut)'
    )
    parser.add_argument(
        '--threshold-hours',
        type=float,
        default=2.0,
        help='Próg w godzinach - jeśli ostatnia aktualizacja starsza, wyślij alert (domyślnie: 2.0)'
    )
    parser.add_argument(
        '--email',
        type=str,
        default='octadecimal@octadecimal.pl',
        help='Adres email do wysyłania powiadomień (domyślnie: octadecimal@octadecimal.pl)'
    )
    parser.add_argument(
        '--sound',
        type=str,
        default=None,
        help='Ścieżka do pliku dźwiękowego (domyślnie: systemowy dźwięk Basso na macOS)'
    )
    
    args = parser.parse_args()
    
    try:
        daemon = TableMonitorDaemon(
            interval=args.interval,
            threshold_hours=args.threshold_hours,
            email_recipient=args.email,
            sound_file=args.sound
        )
        daemon.run()
    except Exception as e:
        logger.error(f"Błąd uruchomienia daemona: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

