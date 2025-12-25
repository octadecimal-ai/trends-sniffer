"""
Top Trader Alerting Service
===========================
Serwis do generowania alertów dla aktywności top traderów.

Alerty są generowane gdy:
- Top trader wykonuje dużą transakcję (przekracza threshold)
- Top trader zmienia znacząco pozycję (net position change)
- Top trader osiąga określony wolumen w oknie czasowym
- Top trader ma nietypową aktywność (anomalia)
"""

from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.services.dydx_top_traders_service import FillEvent, TopTrader


class AlertType(str, Enum):
    """Typy alertów."""
    LARGE_TRADE = "LARGE_TRADE"
    POSITION_CHANGE = "POSITION_CHANGE"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    ANOMALY = "ANOMALY"


class AlertSeverity(str, Enum):
    """Poziomy ważności alertów."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AlertConfig:
    """Konfiguracja progów dla alertów."""
    # Large trade thresholds (USD)
    large_trade_threshold_usd: float = 10000.0  # $10k
    very_large_trade_threshold_usd: float = 50000.0  # $50k
    critical_trade_threshold_usd: float = 100000.0  # $100k
    
    # Position change thresholds (%)
    position_change_threshold_pct: float = 20.0  # 20% zmiana pozycji
    significant_position_change_pct: float = 50.0  # 50% zmiana
    
    # Volume spike thresholds
    volume_spike_multiplier: float = 3.0  # 3x średnia
    volume_spike_window_hours: int = 1  # Okno 1h
    
    # Anomaly detection
    anomaly_deviation_std: float = 2.5  # 2.5 odchylenia standardowego


@dataclass
class TopTraderAlert:
    """Alert dotyczący aktywności top tradera."""
    trader_address: str
    subaccount_number: int
    trader_rank: Optional[int]
    fill_id: Optional[str]
    ticker: Optional[str]
    side: Optional[str]
    price: Optional[float]
    size: Optional[float]
    volume_usd: Optional[float]
    alert_type: AlertType
    alert_severity: AlertSeverity
    alert_message: str
    threshold_value: Optional[float]
    actual_value: Optional[float]
    net_position_before: Optional[float] = None
    net_position_after: Optional[float] = None
    window_hours: Optional[int] = None
    lookback_hours: Optional[int] = None
    metadata: Optional[Dict] = None
    alert_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TopTraderAlertingService:
    """
    Serwis do generowania i zarządzania alertami top traderów.
    """
    
    def __init__(self, database_url: Optional[str] = None, config: Optional[AlertConfig] = None):
        """
        Inicjalizacja serwisu.
        
        Args:
            database_url: URL do bazy PostgreSQL
            config: Konfiguracja progów alertów
        """
        self.config = config or AlertConfig()
        
        if database_url:
            self.engine = create_engine(database_url)
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.Session = None
        
        # Cache dla metryk traderów (volume, position)
        self._trader_metrics_cache: Dict[tuple, Dict] = {}
    
    def check_fill_event(
        self,
        event: FillEvent,
        trader: Optional[TopTrader] = None
    ) -> Optional[TopTraderAlert]:
        """
        Sprawdza fill event i generuje alert jeśli potrzeba.
        
        Args:
            event: Fill event do sprawdzenia
            trader: Informacje o traderze (opcjonalnie)
            
        Returns:
            Alert jeśli został wygenerowany, None w przeciwnym razie
        """
        alerts = []
        
        # Oblicz volume w USD
        volume_usd = event.size * event.price if event.size and event.price else None
        
        # 1. Sprawdź large trade
        if volume_usd:
            large_trade_alert = self._check_large_trade(event, volume_usd, trader)
            if large_trade_alert:
                alerts.append(large_trade_alert)
        
        # 2. Sprawdź position change (wymaga historii)
        position_alert = self._check_position_change(event, trader)
        if position_alert:
            alerts.append(position_alert)
        
        # 3. Sprawdź volume spike
        volume_alert = self._check_volume_spike(event, volume_usd, trader)
        if volume_alert:
            alerts.append(volume_alert)
        
        # Zwróć najważniejszy alert (najwyższa severity)
        if alerts:
            alerts.sort(key=lambda a: self._severity_value(a.alert_severity), reverse=True)
            return alerts[0]
        
        return None
    
    def _check_large_trade(
        self,
        event: FillEvent,
        volume_usd: float,
        trader: Optional[TopTrader]
    ) -> Optional[TopTraderAlert]:
        """Sprawdza czy transakcja przekracza próg large trade."""
        severity = None
        threshold = None
        
        if volume_usd >= self.config.critical_trade_threshold_usd:
            severity = AlertSeverity.CRITICAL
            threshold = self.config.critical_trade_threshold_usd
        elif volume_usd >= self.config.very_large_trade_threshold_usd:
            severity = AlertSeverity.HIGH
            threshold = self.config.very_large_trade_threshold_usd
        elif volume_usd >= self.config.large_trade_threshold_usd:
            severity = AlertSeverity.MEDIUM
            threshold = self.config.large_trade_threshold_usd
        else:
            return None
        
        rank = trader.rank if trader else None
        
        return TopTraderAlert(
            trader_address=event.address,
            subaccount_number=event.subaccount_number,
            trader_rank=rank,
            fill_id=event.fill_id,
            ticker=event.ticker,
            side=event.side,
            price=event.price,
            size=event.size,
            volume_usd=volume_usd,
            alert_type=AlertType.LARGE_TRADE,
            alert_severity=severity,
            alert_message=f"Top trader #{rank or '?'} wykonał dużą transakcję: {event.ticker} {event.side} ${volume_usd:,.2f}",
            threshold_value=threshold,
            actual_value=volume_usd,
            alert_metadata={
                'realized_pnl': event.realized_pnl,
                'fee': event.fee,
            }
        )
    
    def _check_position_change(
        self,
        event: FillEvent,
        trader: Optional[TopTrader]
    ) -> Optional[TopTraderAlert]:
        """Sprawdza czy transakcja powoduje znaczącą zmianę pozycji."""
        # TODO: Wymaga śledzenia net position per trader
        # Na razie zwracamy None - do implementacji gdy będziemy mieli position tracking
        return None
    
    def _check_volume_spike(
        self,
        event: FillEvent,
        volume_usd: Optional[float],
        trader: Optional[TopTrader]
    ) -> Optional[TopTraderAlert]:
        """Sprawdza czy wolumen w oknie czasowym jest anomalnie wysoki."""
        if not volume_usd:
            return None
        
        # Pobierz średni wolumen tradera w ostatnim oknie
        key = (event.address, event.subaccount_number)
        metrics = self._trader_metrics_cache.get(key, {})
        
        avg_volume = metrics.get('avg_volume_1h', 0)
        
        if avg_volume > 0:
            multiplier = volume_usd / avg_volume
            
            if multiplier >= self.config.volume_spike_multiplier:
                severity = AlertSeverity.HIGH if multiplier >= 5.0 else AlertSeverity.MEDIUM
                
                return TopTraderAlert(
                    trader_address=event.address,
                    subaccount_number=event.subaccount_number,
                    trader_rank=trader.rank if trader else None,
                    fill_id=event.fill_id,
                    ticker=event.ticker,
                    side=event.side,
                    price=event.price,
                    size=event.size,
                    volume_usd=volume_usd,
                    alert_type=AlertType.VOLUME_SPIKE,
                    alert_severity=severity,
                    alert_message=f"Volume spike: {event.ticker} ${volume_usd:,.2f} ({multiplier:.1f}x średnia)",
                    threshold_value=avg_volume * self.config.volume_spike_multiplier,
                    actual_value=volume_usd,
                    window_hours=self.config.volume_spike_window_hours,
                    alert_metadata={
                        'multiplier': multiplier,
                        'avg_volume': avg_volume,
                    }
                )
        
        return None
    
    def _severity_value(self, severity: AlertSeverity) -> int:
        """Zwraca wartość numeryczną severity dla sortowania."""
        values = {
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4,
        }
        return values.get(severity, 0)
    
    def save_alert(self, alert: TopTraderAlert) -> bool:
        """
        Zapisuje alert do bazy danych.
        
        Args:
            alert: Alert do zapisania
            
        Returns:
            True jeśli sukces
        """
        if not self.Session:
            logger.warning("Brak połączenia z bazą, alert nie został zapisany")
            return False
        
        session = self.Session()
        try:
            # Konwertuj metadata do JSON
            metadata_json = None
            if alert.alert_metadata:
                import json
                metadata_json = json.dumps(alert.alert_metadata)
            
            stmt = text("""
                INSERT INTO dydx_top_trader_alerts (
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
                    net_position_before,
                    net_position_after,
                    window_hours,
                    lookback_hours,
                    metadata
                ) VALUES (
                    :alert_timestamp,
                    :trader_address,
                    :subaccount_number,
                    :trader_rank,
                    :fill_id,
                    :ticker,
                    :side,
                    :price,
                    :size,
                    :volume_usd,
                    :alert_type,
                    :alert_severity,
                    :alert_message,
                    :threshold_value,
                    :actual_value,
                    :net_position_before,
                    :net_position_after,
                    :window_hours,
                    :lookback_hours,
                    :metadata::jsonb
                )
            """)
            
            session.execute(stmt, {
                'alert_timestamp': alert.alert_timestamp,
                'trader_address': alert.trader_address,
                'subaccount_number': alert.subaccount_number,
                'trader_rank': alert.trader_rank,
                'fill_id': alert.fill_id,
                'ticker': alert.ticker,
                'side': alert.side,
                'price': alert.price,
                'size': alert.size,
                'volume_usd': alert.volume_usd,
                'alert_type': alert.alert_type.value,
                'alert_severity': alert.alert_severity.value,
                'alert_message': alert.alert_message,
                'threshold_value': alert.threshold_value,
                'actual_value': alert.actual_value,
                'net_position_before': alert.net_position_before,
                'net_position_after': alert.net_position_after,
                'window_hours': alert.window_hours,
                'lookback_hours': alert.lookback_hours,
                'metadata': metadata_json,
            })
            
            session.commit()
            logger.info(f"Alert zapisany: {alert.alert_type.value} - {alert.alert_message}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Błąd zapisu alertu: {e}")
            return False
        finally:
            session.close()
    
    def update_trader_metrics(
        self,
        address: str,
        subaccount_number: int,
        volume_usd: float,
        window_hours: int = 1
    ):
        """
        Aktualizuje metryki tradera w cache.
        
        Args:
            address: Adres tradera
            subaccount_number: Numer subkonta
            volume_usd: Wolumen transakcji w USD
            window_hours: Okno czasowe dla metryk
        """
        key = (address, subaccount_number)
        
        if key not in self._trader_metrics_cache:
            self._trader_metrics_cache[key] = {
                'volumes': [],
                'last_update': datetime.now(timezone.utc),
            }
        
        metrics = self._trader_metrics_cache[key]
        metrics['volumes'].append({
            'volume': volume_usd,
            'timestamp': datetime.now(timezone.utc),
        })
        
        # Usuń stare wpisy (poza oknem)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        metrics['volumes'] = [
            v for v in metrics['volumes']
            if v['timestamp'] >= cutoff
        ]
        
        # Oblicz średnią
        if metrics['volumes']:
            metrics['avg_volume_1h'] = sum(v['volume'] for v in metrics['volumes']) / len(metrics['volumes'])
        else:
            metrics['avg_volume_1h'] = 0

