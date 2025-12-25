"""
Economic Calendar Provider
==========================
Provider dla kalendarza wydarzeń ekonomicznych.

Źródła:
- FOMC meeting dates (Federal Reserve - znane z góry)
- CPI release dates (Bureau of Labor Statistics - zwykle 2 tydzień miesiąca)
- NFP release dates (Bureau of Labor Statistics - pierwszy piątek miesiąca)
- GDP release dates (Bureau of Economic Analysis - kwartalnie)

Uwaga: Większość dat jest znana z góry lub ma przewidywalny pattern.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EconomicCalendarProvider:
    """
    Provider dla kalendarza wydarzeń ekonomicznych.
    
    Obsługuje:
    - FOMC meetings (8x/rok, znane z góry)
    - CPI releases (miesięcznie, ~10-15 dzień miesiąca)
    - NFP releases (miesięcznie, pierwszy piątek)
    - GDP releases (kwartalnie)
    """
    
    def __init__(self):
        """Inicjalizacja providera."""
        pass
    
    def get_fomc_dates_2025(self) -> List[Dict[str, Any]]:
        """
        Zwraca znane daty FOMC meetings na 2025.
        
        FOMC spotyka się 8 razy w roku (co ~6 tygodni).
        Daty są publikowane z wyprzedzeniem.
        """
        # FOMC dates 2025 (znane z góry)
        fomc_2025 = [
            {"date": "2025-01-29", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-03-19", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-04-30", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-06-18", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-07-30", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-09-17", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-11-05", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2025-12-17", "time": "14:00", "type": "FOMC", "importance": "high"},
        ]
        
        # FOMC dates 2026 (planowane)
        fomc_2026 = [
            {"date": "2026-01-28", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-03-18", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-04-29", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-06-17", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-07-29", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-09-16", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-11-04", "time": "14:00", "type": "FOMC", "importance": "high"},
            {"date": "2026-12-16", "time": "14:00", "type": "FOMC", "importance": "high"},
        ]
        
        return fomc_2025 + fomc_2026
    
    def get_cpi_dates_2025(self) -> List[Dict[str, Any]]:
        """
        Zwraca przewidywalne daty CPI releases na 2025.
        
        CPI jest publikowany zwykle w 2 tygodniu miesiąca (10-15 dzień).
        Dokładne daty mogą się zmieniać, ale pattern jest przewidywalny.
        """
        # CPI dates 2025 (przewidywalne - zwykle 10-15 dzień miesiąca)
        cpi_2025 = [
            {"date": "2025-01-14", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-02-12", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-03-12", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-04-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-05-14", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-06-11", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-07-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-08-13", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-09-11", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-10-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-11-12", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2025-12-11", "time": "08:30", "type": "CPI", "importance": "high"},
        ]
        
        # CPI dates 2026 (przewidywalne)
        cpi_2026 = [
            {"date": "2026-01-14", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-02-11", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-03-11", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-04-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-05-13", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-06-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-07-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-08-12", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-09-10", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-10-14", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-11-11", "time": "08:30", "type": "CPI", "importance": "high"},
            {"date": "2026-12-10", "time": "08:30", "type": "CPI", "importance": "high"},
        ]
        
        return cpi_2025 + cpi_2026
    
    def get_nfp_dates_2025(self) -> List[Dict[str, Any]]:
        """
        Zwraca przewidywalne daty NFP releases na 2025.
        
        NFP (Non-Farm Payrolls) jest publikowany w pierwszy piątek miesiąca.
        """
        # NFP dates 2025 (pierwszy piątek miesiąca)
        nfp_2025 = [
            {"date": "2025-01-03", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-02-07", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-03-07", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-04-04", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-05-02", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-06-06", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-07-04", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-08-01", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-09-05", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-10-03", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-11-07", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2025-12-05", "time": "08:30", "type": "NFP", "importance": "high"},
        ]
        
        # NFP dates 2026 (pierwszy piątek miesiąca)
        nfp_2026 = [
            {"date": "2026-01-02", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-02-06", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-03-06", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-04-03", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-05-01", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-06-05", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-07-03", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-08-07", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-09-04", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-10-02", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-11-06", "time": "08:30", "type": "NFP", "importance": "high"},
            {"date": "2026-12-04", "time": "08:30", "type": "NFP", "importance": "high"},
        ]
        
        return nfp_2025 + nfp_2026
    
    def get_gdp_dates_2025(self) -> List[Dict[str, Any]]:
        """
        Zwraca przewidywalne daty GDP releases na 2025.
        
        GDP jest publikowany kwartalnie (preliminary, revised, final).
        """
        # GDP dates 2025 (kwartalnie - preliminary estimates)
        gdp_2025 = [
            {"date": "2025-01-30", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q4 2024 Preliminary"},
            {"date": "2025-04-24", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q1 2025 Preliminary"},
            {"date": "2025-07-24", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q2 2025 Preliminary"},
            {"date": "2025-10-29", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q3 2025 Preliminary"},
        ]
        
        # GDP dates 2026 (kwartalnie - preliminary estimates)
        gdp_2026 = [
            {"date": "2026-01-29", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q4 2025 Preliminary"},
            {"date": "2026-04-23", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q1 2026 Preliminary"},
            {"date": "2026-07-23", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q2 2026 Preliminary"},
            {"date": "2026-10-28", "time": "08:30", "type": "GDP", "importance": "high", "notes": "Q3 2026 Preliminary"},
        ]
        
        return gdp_2025 + gdp_2026
    
    def get_all_events(self, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Zwraca wszystkie wydarzenia ekonomiczne w zadanym zakresie dat.
        
        Args:
            start_date: Data początkowa (domyślnie dzisiaj)
            end_date: Data końcowa (domyślnie +1 rok)
            
        Returns:
            Lista wydarzeń z polami: event_date, event_name, event_type, importance, country
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc)
        if end_date is None:
            end_date = start_date + timedelta(days=365)
        
        all_events = []
        
        # Zbierz wszystkie typy wydarzeń
        for event in self.get_fomc_dates_2025():
            event_date = datetime.strptime(event['date'], "%Y-%m-%d").replace(
                hour=int(event['time'].split(':')[0]),
                minute=int(event['time'].split(':')[1]),
                tzinfo=timezone.utc
            )
            if start_date <= event_date <= end_date:
                all_events.append({
                    'event_date': event_date,
                    'event_name': 'FOMC Rate Decision',
                    'event_type': 'FOMC',
                    'country': 'US',
                    'importance': event['importance'],
                })
        
        for event in self.get_cpi_dates_2025():
            event_date = datetime.strptime(event['date'], "%Y-%m-%d").replace(
                hour=int(event['time'].split(':')[0]),
                minute=int(event['time'].split(':')[1]),
                tzinfo=timezone.utc
            )
            if start_date <= event_date <= end_date:
                all_events.append({
                    'event_date': event_date,
                    'event_name': 'CPI (Consumer Price Index)',
                    'event_type': 'CPI',
                    'country': 'US',
                    'importance': event['importance'],
                })
        
        for event in self.get_nfp_dates_2025():
            event_date = datetime.strptime(event['date'], "%Y-%m-%d").replace(
                hour=int(event['time'].split(':')[0]),
                minute=int(event['time'].split(':')[1]),
                tzinfo=timezone.utc
            )
            if start_date <= event_date <= end_date:
                all_events.append({
                    'event_date': event_date,
                    'event_name': 'NFP (Non-Farm Payrolls)',
                    'event_type': 'NFP',
                    'country': 'US',
                    'importance': event['importance'],
                })
        
        for event in self.get_gdp_dates_2025():
            event_date = datetime.strptime(event['date'], "%Y-%m-%d").replace(
                hour=int(event['time'].split(':')[0]),
                minute=int(event['time'].split(':')[1]),
                tzinfo=timezone.utc
            )
            if start_date <= event_date <= end_date:
                all_events.append({
                    'event_date': event_date,
                    'event_name': f"GDP {event.get('notes', 'Release')}",
                    'event_type': 'GDP',
                    'country': 'US',
                    'importance': event['importance'],
                })
        
        # Sortuj po dacie
        all_events.sort(key=lambda x: x['event_date'])
        
        return all_events
    
    def get_upcoming_events(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Zwraca nadchodzące wydarzenia w ciągu następnych N dni.
        
        Args:
            days_ahead: Liczba dni do przodu
            
        Returns:
            Lista nadchodzących wydarzeń
        """
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=days_ahead)
        
        events = self.get_all_events(start_date=start_date, end_date=end_date)
        
        # Filtruj tylko przyszłe wydarzenia
        now = datetime.now(timezone.utc)
        upcoming = [e for e in events if e['event_date'] >= now]
        
        return upcoming


# === Convenience functions ===

def get_next_fomc() -> Optional[Dict[str, Any]]:
    """Zwraca następne spotkanie FOMC."""
    provider = EconomicCalendarProvider()
    events = provider.get_all_events()
    fomc_events = [e for e in events if e['event_type'] == 'FOMC']
    upcoming = [e for e in fomc_events if e['event_date'] >= datetime.now(timezone.utc)]
    return upcoming[0] if upcoming else None


def get_next_cpi() -> Optional[Dict[str, Any]]:
    """Zwraca następną publikację CPI."""
    provider = EconomicCalendarProvider()
    events = provider.get_all_events()
    cpi_events = [e for e in events if e['event_type'] == 'CPI']
    upcoming = [e for e in cpi_events if e['event_date'] >= datetime.now(timezone.utc)]
    return upcoming[0] if upcoming else None


# === Test ===

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("📅 Economic Calendar Provider Test")
    print("=" * 60)
    
    provider = EconomicCalendarProvider()
    
    # Nadchodzące wydarzenia
    print("\n📊 Nadchodzące wydarzenia (30 dni):")
    upcoming = provider.get_upcoming_events(days_ahead=30)
    for event in upcoming[:10]:
        print(f"  {event['event_date'].strftime('%Y-%m-%d %H:%M')} | {event['event_type']:4s} | {event['event_name']}")
    
    # Następne FOMC
    print("\n🏦 Następne FOMC:")
    next_fomc = get_next_fomc()
    if next_fomc:
        print(f"  {next_fomc['event_date'].strftime('%Y-%m-%d %H:%M')} - {next_fomc['event_name']}")
    
    # Następne CPI
    print("\n📈 Następne CPI:")
    next_cpi = get_next_cpi()
    if next_cpi:
        print(f"  {next_cpi['event_date'].strftime('%Y-%m-%d %H:%M')} - {next_cpi['event_name']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed")

