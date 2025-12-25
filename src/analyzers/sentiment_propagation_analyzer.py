"""
Sentiment Propagation Analyzer
==============================
Analizator propagacji sentymentu między regionami (APAC, EU, US).

Oblicza:
- Korelacje z opóźnieniem czasowym (lagged correlations)
- Prędkość propagacji (propagation speed)
- Amplifikacja/tłumienie sentymentu
- Leading region (region wiodący)
- Global Activity Index (GAI)

Regiony:
- APAC (Asia-Pacific): UTC+8 to UTC+12
- EU (Europe): UTC+0 to UTC+3
- US (Americas): UTC-8 to UTC-3
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class SentimentPropagationAnalyzer:
    """
    Analizator propagacji sentymentu między regionami.
    
    Analizuje jak sentyment propaguje się przez strefy czasowe:
    - APAC → EU (lag ~4h)
    - EU → US (lag ~4h)
    - US → APAC (overnight, lag ~12h)
    """
    
    # Mapowanie UTC offset (w minutach) na region propagacji
    REGION_MAPPING = {
        'APAC': (480, 720),    # UTC+8 to UTC+12
        'EU': (0, 180),        # UTC+0 to UTC+3
        'US': (-480, -180),    # UTC-8 to UTC-3
    }
    
    # Domyślne opóźnienia propagacji (w godzinach)
    DEFAULT_LAG_HOURS = {
        'asia_to_eu': 4,
        'eu_to_us': 4,
        'us_to_asia': 12,  # Overnight
    }
    
    def __init__(self, database_url: str):
        """
        Inicjalizacja analizatora.
        
        Args:
            database_url: URL do bazy PostgreSQL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def map_country_to_region(self, utc_offset_minutes: int) -> Optional[str]:
        """
        Mapuje UTC offset kraju na region propagacji.
        
        Args:
            utc_offset_minutes: UTC offset w minutach
            
        Returns:
            Kod regionu (APAC, EU, US) lub None
        """
        for region, (min_offset, max_offset) in self.REGION_MAPPING.items():
            if min_offset <= utc_offset_minutes <= max_offset:
                return region
        return None
    
    def get_regional_sentiment(
        self,
        start_time: datetime,
        end_time: datetime,
        window_hours: int = 24
    ) -> Dict[str, pd.Series]:
        """
        Pobierz sentyment per region z bazy danych.
        
        Args:
            start_time: Czas początkowy
            end_time: Czas końcowy
            window_hours: Okno czasowe do agregacji (domyślnie 24h)
            
        Returns:
            Dict z seriami czasowymi sentymentu per region
        """
        session = self.Session()
        try:
            # Pobierz dane sentymentu z sentiment_measurement i sentiments_sniff
            # Używamy sentiments_sniff.occurrence_time jako timestamp
            query = text("""
                SELECT 
                    ss.occurrence_time as timestamp,
                    c.utc_offset,
                    sm.stats_mean as interest_value,
                    1 as occurrence_count
                FROM google_trends_sentiments_sniff ss
                JOIN google_trends_sentiment_measurement sm ON ss.measurement_id = sm.id
                JOIN countries c ON sm.country_id = c.id
                WHERE ss.occurrence_time >= :start_time
                  AND ss.occurrence_time <= :end_time
                ORDER BY ss.occurrence_time
            """)
            
            result = session.execute(
                query,
                {"start_time": start_time, "end_time": end_time}
            )
            
            # Przygotuj dane per region
            regional_data = {
                'APAC': [],
                'EU': [],
                'US': []
            }
            
            for row in result:
                utc_offset = row[1] if row[1] is not None else 0
                region = self.map_country_to_region(utc_offset)
                
                if region and region in regional_data:
                    timestamp = row[0]
                    interest_value = float(row[2]) if row[2] else 0.0
                    occurrence_count = int(row[3]) if row[3] else 0
                    
                    # Użyj interest_value jako proxy dla sentymentu
                    # (można też użyć occurrence_count lub kombinacji)
                    regional_data[region].append({
                        'timestamp': timestamp,
                        'sentiment': interest_value,
                        'count': occurrence_count
                    })
            
            # Konwertuj na pandas Series per region
            regional_series = {}
            for region, data in regional_data.items():
                if data:
                    df = pd.DataFrame(data)
                    df.set_index('timestamp', inplace=True)
                    
                    # Agreguj do godzinnych przedziałów
                    df_hourly = df.resample('1h').agg({
                        'sentiment': 'mean',
                        'count': 'sum'
                    })
                    
                    regional_series[region] = df_hourly['sentiment']
                else:
                    regional_series[region] = pd.Series(dtype=float)
            
            return regional_series
            
        except Exception as e:
            logger.error(f"Błąd pobierania sentymentu regionalnego: {e}")
            return {'APAC': pd.Series(dtype=float), 'EU': pd.Series(dtype=float), 'US': pd.Series(dtype=float)}
        finally:
            session.close()
    
    def calculate_lagged_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
        lag_hours: int
    ) -> float:
        """
        Oblicz korelację z opóźnieniem czasowym.
        
        Args:
            series1: Pierwsza seria czasowa (źródło)
            series2: Druga seria czasowa (cel)
            lag_hours: Opóźnienie w godzinach
            
        Returns:
            Współczynnik korelacji (-1.0 do 1.0)
        """
        if series1.empty or series2.empty:
            return 0.0
        
        # Przesuń series1 o lag_hours do przodu
        series1_shifted = series1.shift(-lag_hours)
        
        # Wyrównaj indeksy
        common_index = series1_shifted.index.intersection(series2.index)
        
        if len(common_index) < 2:
            return 0.0
        
        series1_aligned = series1_shifted.loc[common_index]
        series2_aligned = series2.loc[common_index]
        
        # Usuń NaN
        mask = ~(series1_aligned.isna() | series2_aligned.isna())
        series1_clean = series1_aligned[mask]
        series2_clean = series2_aligned[mask]
        
        if len(series1_clean) < 2:
            return 0.0
        
        # Oblicz korelację
        correlation = series1_clean.corr(series2_clean)
        
        return float(correlation) if not pd.isna(correlation) else 0.0
    
    def calculate_propagation_speed(
        self,
        asia_series: pd.Series,
        eu_series: pd.Series,
        us_series: pd.Series
    ) -> float:
        """
        Oblicz średnią prędkość propagacji między regionami.
        
        Args:
            asia_series: Sentyment APAC
            eu_series: Sentyment EU
            us_series: Sentyment US
            
        Returns:
            Średnia prędkość propagacji (w godzinach)
        """
        speeds = []
        
        # Asia → EU
        if not asia_series.empty and not eu_series.empty:
            # Znajdź maksymalne korelacje dla różnych lagów
            max_corr = 0.0
            best_lag = 0
            for lag in range(1, 9):  # Sprawdź lag 1-8 godzin
                corr = abs(self.calculate_lagged_correlation(asia_series, eu_series, lag))
                if corr > max_corr:
                    max_corr = corr
                    best_lag = lag
            if best_lag > 0:
                speeds.append(best_lag)
        
        # EU → US
        if not eu_series.empty and not us_series.empty:
            max_corr = 0.0
            best_lag = 0
            for lag in range(1, 9):
                corr = abs(self.calculate_lagged_correlation(eu_series, us_series, lag))
                if corr > max_corr:
                    max_corr = corr
                    best_lag = lag
            if best_lag > 0:
                speeds.append(best_lag)
        
        return float(np.mean(speeds)) if speeds else 0.0
    
    def calculate_amplification(
        self,
        source_sentiment: float,
        target_sentiment: float
    ) -> float:
        """
        Oblicz współczynnik amplifikacji/tłumienia.
        
        Args:
            source_sentiment: Sentyment źródłowy
            target_sentiment: Sentyment docelowy
            
        Returns:
            Współczynnik amplifikacji (>1.0 = amplifikacja, <1.0 = tłumienie)
        """
        if source_sentiment == 0:
            return 0.0
        return float(target_sentiment / source_sentiment)
    
    def determine_leading_region(
        self,
        asia_sentiment: float,
        eu_sentiment: float,
        us_sentiment: float
    ) -> str:
        """
        Określ region wiodący na podstawie sentymentu.
        
        Args:
            asia_sentiment: Sentyment APAC
            eu_sentiment: Sentyment EU
            us_sentiment: Sentyment US
            
        Returns:
            Kod regionu wiodącego (APAC, EU, US, MIXED, NONE)
        """
        sentiments = {
            'APAC': asia_sentiment,
            'EU': eu_sentiment,
            'US': us_sentiment
        }
        
        # Usuń zera
        non_zero = {k: v for k, v in sentiments.items() if v > 0}
        
        if not non_zero:
            return 'NONE'
        
        if len(non_zero) == 1:
            return list(non_zero.keys())[0]
        
        # Sprawdź czy są równe (w granicach 10%)
        values = list(non_zero.values())
        max_val = max(values)
        min_val = min(values)
        
        if max_val > 0 and (max_val - min_val) / max_val < 0.1:
            return 'MIXED'
        
        # Zwróć region z najwyższym sentymentem
        return max(non_zero.items(), key=lambda x: x[1])[0]
    
    def calculate_gai_score(
        self,
        asia_sentiment: float,
        eu_sentiment: float,
        us_sentiment: float,
        asia_count: int,
        eu_count: int,
        us_count: int
    ) -> float:
        """
        Oblicz Global Activity Index (GAI).
        
        GAI = ważona średnia sentymentu per region (ważone liczbą pomiarów).
        
        Args:
            asia_sentiment: Sentyment APAC
            eu_sentiment: Sentyment EU
            us_sentiment: Sentyment US
            asia_count: Liczba pomiarów APAC
            eu_count: Liczba pomiarów EU
            us_count: Liczba pomiarów US
            
        Returns:
            GAI score
        """
        total_count = asia_count + eu_count + us_count
        
        if total_count == 0:
            return 0.0
        
        # Ważona średnia
        weighted_sum = (
            asia_sentiment * asia_count +
            eu_sentiment * eu_count +
            us_sentiment * us_count
        )
        
        return float(weighted_sum / total_count)
    
    def analyze_propagation(
        self,
        timestamp: datetime,
        window_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Przeanalizuj propagację sentymentu dla danego timestampu.
        
        Args:
            timestamp: Timestamp dla którego obliczyć metryki
            window_hours: Okno czasowe do analizy (domyślnie 24h)
            
        Returns:
            Dict z metrykami propagacji lub None w przypadku błędu
        """
        try:
            # Określ zakres czasowy
            end_time = timestamp
            start_time = timestamp - timedelta(hours=window_hours)
            
            # Pobierz sentyment per region
            regional_series = self.get_regional_sentiment(start_time, end_time, window_hours)
            
            asia_series = regional_series.get('APAC', pd.Series(dtype=float))
            eu_series = regional_series.get('EU', pd.Series(dtype=float))
            us_series = regional_series.get('US', pd.Series(dtype=float))
            
            # Oblicz średni sentyment per region (ostatnie N godzin)
            asia_sentiment = float(asia_series.mean()) if not asia_series.empty else 0.0
            eu_sentiment = float(eu_series.mean()) if not eu_series.empty else 0.0
            us_sentiment = float(us_series.mean()) if not us_series.empty else 0.0
            
            # Liczba pomiarów per region
            asia_count = len(asia_series[asia_series > 0]) if not asia_series.empty else 0
            eu_count = len(eu_series[eu_series > 0]) if not eu_series.empty else 0
            us_count = len(us_series[us_series > 0]) if not us_series.empty else 0
            
            # Oblicz korelacje z opóźnieniem
            asia_to_eu_corr = self.calculate_lagged_correlation(
                asia_series, eu_series, self.DEFAULT_LAG_HOURS['asia_to_eu']
            )
            eu_to_us_corr = self.calculate_lagged_correlation(
                eu_series, us_series, self.DEFAULT_LAG_HOURS['eu_to_us']
            )
            us_to_asia_corr = self.calculate_lagged_correlation(
                us_series, asia_series, self.DEFAULT_LAG_HOURS['us_to_asia']
            )
            
            # Oblicz prędkość propagacji
            propagation_speed = self.calculate_propagation_speed(
                asia_series, eu_series, us_series
            )
            
            # Oblicz amplifikację
            asia_to_eu_amp = self.calculate_amplification(asia_sentiment, eu_sentiment)
            eu_to_us_amp = self.calculate_amplification(eu_sentiment, us_sentiment)
            us_to_asia_amp = self.calculate_amplification(us_sentiment, asia_sentiment)
            
            # Określ region wiodący
            leading_region = self.determine_leading_region(
                asia_sentiment, eu_sentiment, us_sentiment
            )
            
            # Oblicz GAI
            gai_score = self.calculate_gai_score(
                asia_sentiment, eu_sentiment, us_sentiment,
                asia_count, eu_count, us_count
            )
            
            return {
                'timestamp': timestamp,
                'asia_to_eu_corr': asia_to_eu_corr,
                'eu_to_us_corr': eu_to_us_corr,
                'us_to_asia_corr': us_to_asia_corr,
                'propagation_speed_hours': propagation_speed,
                'asia_to_eu_amplification': asia_to_eu_amp,
                'eu_to_us_amplification': eu_to_us_amp,
                'us_to_asia_amplification': us_to_asia_amp,
                'leading_region': leading_region,
                'gai_score': gai_score,
                'asia_sentiment': asia_sentiment,
                'eu_sentiment': eu_sentiment,
                'us_sentiment': us_sentiment,
                'asia_measurements_count': asia_count,
                'eu_measurements_count': eu_count,
                'us_measurements_count': us_count,
                'calculation_window_hours': window_hours,
            }
            
        except Exception as e:
            logger.error(f"Błąd analizy propagacji dla {timestamp}: {e}")
            return None

