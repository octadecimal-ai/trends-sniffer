"""
Database Models
===============
Modele SQLAlchemy dla danych kryptowalutowych.

Używamy:
- TimescaleDB (PostgreSQL) dla danych produkcyjnych - idealny do szeregów czasowych
- SQLite dla development/testów

TimescaleDB automatycznie partycjonuje dane po czasie,
co daje 10-100x lepszą wydajność na dużych zbiorach danych.
"""

from datetime import datetime, timezone
from typing import Optional


def utcnow():
    """Zwraca aktualny czas UTC (kompatybilne z Python 3.12+)."""
    return datetime.now(timezone.utc)
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, BigInteger, UniqueConstraint,
    Index, UniqueConstraint, ForeignKey, Boolean, Text, Enum, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class Exchange(enum.Enum):
    """Obsługiwane giełdy."""
    BINANCE = "binance"
    DYDX = "dydx"
    COINBASE = "coinbase"
    KRAKEN = "kraken"


class MarketType(enum.Enum):
    """Typ rynku."""
    SPOT = "spot"
    PERPETUAL = "perpetual"
    FUTURES = "futures"


# === Główne tabele danych rynkowych ===

class OHLCV(Base):
    """
    Tabela świec OHLCV (Open, High, Low, Close, Volume).
    
    To główna tabela z danymi cenowymi.
    W TimescaleDB zostanie skonwertowana na hypertable.
    """
    __tablename__ = 'ohlcv'
    
    # Używamy Integer dla SQLite compatibility (autoincrement działa lepiej)
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)  # np. BTC/USDT, BTC-USD
    timeframe = Column(String(10), nullable=False, index=True)  # 1m, 5m, 1h, 1d
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Opcjonalne pola
    quote_volume = Column(Float, nullable=True)  # Wolumen w walucie kwotowanej
    trades_count = Column(Integer, nullable=True)  # Liczba transakcji
    
    created_at = Column(DateTime, default=utcnow)
    
    __table_args__ = (
        # Dla TimescaleDB: timestamp musi być pierwszą kolumną w unique constraint
        UniqueConstraint('timestamp', 'exchange', 'symbol', 'timeframe', name='uq_ohlcv'),
        Index('ix_ohlcv_lookup', 'exchange', 'symbol', 'timeframe', 'timestamp'),
        # Dla TimescaleDB: primary key powinien zawierać timestamp
        # Ale SQLAlchemy wymaga id jako primary key, więc używamy unique constraint
    )
    
    def __repr__(self):
        return f"<OHLCV {self.exchange}:{self.symbol} {self.timeframe} @ {self.timestamp}>"


class Ticker(Base):
    """
    Snapshoty tickerów - aktualne ceny i wolumeny.
    Przydatne do analizy sentymentu w czasie rzeczywistym.
    """
    __tablename__ = 'tickers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    
    price = Column(Float, nullable=False)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    
    volume_24h = Column(Float, nullable=True)
    change_24h = Column(Float, nullable=True)
    high_24h = Column(Float, nullable=True)
    low_24h = Column(Float, nullable=True)
    
    # Dla perpetual (dYdX)
    funding_rate = Column(Float, nullable=True)
    open_interest = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('ix_ticker_lookup', 'exchange', 'symbol', 'timestamp'),
        # Unique constraint zapobiega duplikatom (timestamp, exchange, symbol)
        # nawet przy równoległym zapisie
        UniqueConstraint('timestamp', 'exchange', 'symbol', name='uq_ticker_unique'),
    )


class Trade(Base):
    """
    Pojedyncze transakcje - przydatne do analizy on-chain.
    """
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    
    trade_id = Column(String(100), nullable=True)  # ID z giełdy
    side = Column(String(10), nullable=False)  # buy/sell
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('ix_trade_lookup', 'exchange', 'symbol', 'timestamp'),
    )


# === Wskaźniki techniczne (pre-obliczone) ===

class TechnicalIndicator(Base):
    """
    Pre-obliczone wskaźniki techniczne.
    Pozwala na szybkie zapytania bez obliczania w locie.
    """
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    
    # Średnie kroczące
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    ema_9 = Column(Float, nullable=True)
    ema_21 = Column(Float, nullable=True)
    
    # Oscylatory
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    
    # Bollinger Bands
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    
    # Zmienność
    atr = Column(Float, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'exchange', 'symbol', 'timeframe', name='uq_indicators'),
    )


# === Analiza sentymentu ===

class SentimentScore(Base):
    """
    Wyniki analizy sentymentu z różnych źródeł.
    """
    __tablename__ = 'aggregated_sentiment_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # twitter, reddit, news, llm
    
    score = Column(Float, nullable=False)  # -100 do +100
    sentiment = Column(String(20), nullable=False)  # bullish/bearish/neutral
    confidence = Column(Float, nullable=True)  # 0-1
    
    sample_size = Column(Integer, nullable=True)  # Liczba przeanalizowanych tekstów
    raw_data = Column(Text, nullable=True)  # JSON z dodatkowymi danymi
    
    __table_args__ = (
        Index('ix_aggregated_sentiment_scores_lookup', 'symbol', 'source', 'timestamp'),
    )


class LLMSentimentAnalysis(Base):
    """
    Wyniki analizy sentymentu wykonanej przez LLM (Large Language Model).
    
    Zawiera szczegółowe informacje o analizie sentymentu wykonanej przez model językowy,
    w tym koszty zapytania, liczbę tokenów i szczegółowe metryki sentymentu.
    """
    __tablename__ = 'llm_sentiment_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)  # np. BTC/USDC, BTC-USD
    region = Column(String(10), nullable=False, index=True)  # US, CN, JP, KR, DE, etc.
    language = Column(String(10), nullable=False)  # en, zh, ja, ko, etc.
    
    # Informacje o LLM
    llm_model = Column(String(100), nullable=False)  # claude-sonnet-4-20250514, gpt-4, etc.
    input_tokens = Column(Integer, nullable=False)  # Liczba tokenów wejściowych
    output_tokens = Column(Integer, nullable=False)  # Liczba tokenów wyjściowych
    total_tokens = Column(Integer, nullable=False)  # Łączna liczba tokenów
    cost_pln = Column(Float, nullable=False)  # Koszt zapytania w PLN
    
    # Wyniki analizy sentymentu
    sentiment = Column(String(20), nullable=False)  # very_bearish, bearish, neutral, bullish, very_bullish
    score = Column(Float, nullable=False)  # -1.0 do 1.0
    confidence = Column(Float, nullable=True)  # 0.0 do 1.0
    fud_level = Column(Float, nullable=True)  # 0.0 do 1.0
    fomo_level = Column(Float, nullable=True)  # 0.0 do 1.0
    market_impact = Column(String(10), nullable=True)  # high, medium, low
    key_topics = Column(Text, nullable=True)  # JSON array z kluczowymi tematami
    reasoning = Column(Text, nullable=True)  # Wyjaśnienie analizy
    
    # Metadane
    texts_count = Column(Integer, nullable=True)  # Liczba przeanalizowanych tekstów
    created_at = Column(DateTime, default=utcnow)
    
    # Prompt i odpowiedź LLM
    prompt = Column(Text, nullable=True)  # Pełny prompt wysłany do LLM
    response = Column(Text, nullable=True)  # Pełna odpowiedź z LLM (przed parsowaniem JSON)
    
    # Zapytania i odpowiedzi z Web Search (DuckDuckGo/Google/Serper)
    web_search_query = Column(Text, nullable=True)  # Zapytanie wysłane do web search
    web_search_response = Column(Text, nullable=True)  # Pełna odpowiedź z web search (JSON)
    web_search_answer = Column(Text, nullable=True)  # Podsumowanie AI z web search (jeśli dostępne)
    web_search_results_count = Column(Integer, nullable=True)  # Liczba wyników z web search
    
    __table_args__ = (
        Index('ix_llm_sentiment_lookup', 'symbol', 'region', 'timestamp'),
        Index('ix_llm_sentiment_model', 'llm_model', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<LLMSentimentAnalysis {self.symbol} {self.region} @ {self.timestamp} ({self.sentiment}, cost: {self.cost_pln:.4f} PLN)>"


class GDELTSentiment(Base):
    """
    Dane sentymentu z GDELT (Global Database of Events, Language, and Tone).
    
    Zawiera agregowane dane sentymentu z mediów z całego świata,
    pogrupowane po regionach i przedziałach czasowych.
    """
    __tablename__ = 'gdelt_sentiment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    region = Column(String(10), nullable=False, index=True)  # US, CN, JP, KR, DE, GB, etc.
    language = Column(String(10), nullable=True)  # en, zh, ja, ko, etc.
    
    # Zapytanie GDELT
    query = Column(String(500), nullable=False)  # Zapytanie użyte do wyszukiwania
    
    # Dane sentymentu
    tone = Column(Float, nullable=True)  # Średni tone (-100 do +100)
    tone_std = Column(Float, nullable=True)  # Odchylenie standardowe tone
    volume = Column(Integer, nullable=True)  # Liczba artykułów
    positive_count = Column(Integer, nullable=True)  # Liczba pozytywnych artykułów
    negative_count = Column(Integer, nullable=True)  # Liczba negatywnych artykułów
    neutral_count = Column(Integer, nullable=True)  # Liczba neutralnych artykułów
    
    # Metadane
    resolution = Column(String(10), nullable=False, default="hour")  # hour, day
    created_at = Column(DateTime, default=utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'region', 'query', 'resolution', name='uq_gdelt_sentiment'),
        Index('ix_gdelt_sentiment_lookup', 'region', 'timestamp'),
        Index('ix_gdelt_sentiment_query', 'query', 'timestamp'),
        Index('ix_gdelt_sentiment_timestamp', 'timestamp', postgresql_using='brin'),  # For TimescaleDB
    )
    
    def __repr__(self):
        return f"<GDELTSentiment {self.region} @ {self.timestamp} (tone: {self.tone:.2f}, volume: {self.volume})>"


# === Alerty i sygnały ===

class Signal(Base):
    """
    Sygnały handlowe wygenerowane przez system.
    """
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    
    signal_type = Column(String(50), nullable=False)  # buy, sell, hold
    strategy = Column(String(100), nullable=False)  # nazwa strategii
    strength = Column(Float, nullable=True)  # 0-1
    
    price_at_signal = Column(Float, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    notes = Column(Text, nullable=True)
    executed = Column(Boolean, default=False)


# === Konfiguracja portfolio ===

class Portfolio(Base):
    """
    Śledzenie pozycji w portfolio.
    """
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    initial_capital = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class Position(Base):
    """
    Pozycje w portfolio.
    """
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'), nullable=False)
    
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # long/short
    
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False)
    size = Column(Float, nullable=False)
    
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    
    status = Column(String(20), default='open')  # open/closed
    notes = Column(Text, nullable=True)


# === Helper do tworzenia tabel TimescaleDB ===

TIMESCALE_HYPERTABLES = [
    ('ohlcv', 'timestamp'),
    ('tickers', 'timestamp'),
    ('funding_rates', 'timestamp'),
    ('trades', 'timestamp'),
    ('technical_indicators', 'timestamp'),
    ('sentiment_scores', 'timestamp'),
    ('market_indices', 'timestamp'),
    ('fear_greed_index', 'timestamp'),
]

def create_timescale_hypertables(engine):
    """
    Konwertuje tabele na hypertables TimescaleDB.
    Wywoływane po create_all() dla PostgreSQL z TimescaleDB.
    
    Uwaga: Dla tabel z unique constraints, TimescaleDB wymaga aby kolumna timestamp
    była częścią constraint. Unique constraints są tworzone przez SQLAlchemy,
    więc hypertables są tworzone po utworzeniu tabel.
    """
    from sqlalchemy import text
    
    # Sprawdź czy TimescaleDB jest zainstalowany
    with engine.connect() as check_conn:
        result = check_conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'timescaledb'"))
        if not result.fetchone():
            print("TimescaleDB nie jest zainstalowany, używam zwykłych tabel")
            return
    
    # Każda tabela w osobnej transakcji, aby błąd w jednej nie przerywał innych
    for table_name, time_column in TIMESCALE_HYPERTABLES:
        with engine.begin() as conn:
            try:
                # Sprawdź czy hypertable już istnieje
                check_result = conn.execute(text(
                    f"SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = '{table_name}'"
                ))
                if check_result.fetchone():
                    print(f"✓ Hypertable {table_name} już istnieje")
                    continue
                
                # Dla tabel z unique constraints, musimy je tymczasowo usunąć przed utworzeniem hypertable
                # Mapowanie nazw constraintów dla różnych tabel
                constraint_map = {
                    'ohlcv': 'uq_ohlcv',
                    'funding_rates': 'uq_funding',
                    'technical_indicators': 'uq_indicators',
                }
                
                constraint_name = constraint_map.get(table_name)
                constraint_dropped = False
                
                if constraint_name:
                    # Sprawdź czy constraint istnieje
                    check_constraint = conn.execute(text(
                        f"SELECT constraint_name FROM information_schema.table_constraints "
                        f"WHERE table_name = '{table_name}' AND constraint_name = '{constraint_name}'"
                    ))
                    if check_constraint.fetchone():
                        # Tymczasowo usuń constraint
                        conn.execute(text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"))
                        constraint_dropped = True
                        print(f"  → Tymczasowo usunięto constraint {constraint_name}")
                
                # Utwórz hypertable
                conn.execute(text(
                    f"SELECT create_hypertable('{table_name}', '{time_column}', "
                    f"if_not_exists => TRUE, migrate_data => TRUE, "
                    f"chunk_time_interval => INTERVAL '7 days')"
                ))
                print(f"✓ Utworzono hypertable: {table_name}")
                
                # Przywróć constraint jeśli został usunięty
                if constraint_dropped and constraint_name:
                    # Sprawdź czy constraint już istnieje (może być dodany automatycznie)
                    check_existing = conn.execute(text(
                        f"SELECT constraint_name FROM information_schema.table_constraints "
                        f"WHERE table_name = '{table_name}' AND constraint_name = '{constraint_name}'"
                    ))
                    if not check_existing.fetchone():
                        try:
                            if table_name == 'ohlcv':
                                conn.execute(text(
                                    f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                                    f"UNIQUE (timestamp, exchange, symbol, timeframe)"
                                ))
                            elif table_name == 'funding_rates':
                                conn.execute(text(
                                    f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                                    f"UNIQUE (timestamp, exchange, symbol)"
                                ))
                            elif table_name == 'technical_indicators':
                                conn.execute(text(
                                    f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} "
                                    f"UNIQUE (timestamp, exchange, symbol, timeframe)"
                                ))
                            print(f"  → Przywrócono constraint {constraint_name}")
                        except Exception as constraint_error:
                            # Jeśli nie można dodać constraint (np. już istnieje lub problem z hypertable)
                            print(f"  → Nie można przywrócić constraint {constraint_name}: {constraint_error}")
                    else:
                        print(f"  → Constraint {constraint_name} już istnieje")
                    
            except Exception as e:
                error_msg = str(e)
                # Ignoruj błędy jeśli hypertable już istnieje
                if 'already a hypertable' in error_msg.lower() or 'already exists' in error_msg.lower():
                    print(f"✓ Hypertable {table_name} już istnieje")
                elif 'unique index' in error_msg.lower() or 'partitioning' in error_msg.lower():
                    print(f"⚠ Hypertable {table_name}: Problem z unique constraint - pomijam")
                else:
                    print(f"⚠ Hypertable {table_name}: {e}")


# === Regiony i słowniki wydarzeń rynkowych ===

class Region(Base):
    """
    Słownik regionów geograficznych z informacjami przydatnymi dla strategii BTC.
    """
    __tablename__ = 'regions'
    __table_args__ = (
        Index('ix_regions_dominant_participant', 'dominant_participant'),
        Index('ix_regions_regulatory_status', 'regulatory_status'),
        Index('ix_regions_adoption_level', 'crypto_adoption_level'),
    )
    
    region_code = Column(String(10), primary_key=True)
    short_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    timezone = Column(String(20), nullable=False)
    market_share_pct = Column(Float, default=0.0)
    dominant_participant = Column(String(20), nullable=False)  # RETAIL, INSTITUTIONAL, MIXED
    regulatory_status = Column(String(20), nullable=False)  # FRIENDLY, REGULATED, RESTRICTIVE, UNCLEAR, UNKNOWN
    crypto_adoption_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, UNKNOWN
    btc_volume_rank = Column(Integer, default=99)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relacje
    region_events = relationship('DictionaryRegionEvent', back_populates='region', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Region {self.region_code}: {self.short_name} (rank: {self.btc_volume_rank})>"


class DictionaryRegionEvent(Base):
    """
    Słownik wydarzeń specyficznych dla poszczególnych regionów.
    """
    __tablename__ = 'dictionary_region_events'
    __table_args__ = (
        Index('ix_region_events_region', 'region_code'),
        Index('ix_region_events_time', 'utc_start', 'utc_end'),
        Index('ix_region_events_priority', 'priority'),
        Index('ix_region_events_category', 'category'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), ForeignKey('regions.region_code', ondelete='CASCADE'), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)  # TIME jako string dla kompatybilności
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH, EXTREME
    volume_impact = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)  # TRENDING, RANGING, VOLATILE, MIXED
    dominant_actors = Column(String(20), nullable=True)  # RETAIL, INSTITUTIONAL, ALGO, MIXED
    news_sensitivity = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    category = Column(String(20), nullable=True)  # SESSION, OVERLAP, LIQUIDITY, WEEKEND
    created_at = Column(DateTime, default=utcnow)
    
    # Relacje
    region = relationship('Region', back_populates='region_events')
    
    def __repr__(self):
        return f"<DictionaryRegionEvent {self.phase_code} ({self.region_code}) @ {self.utc_start}-{self.utc_end}>"


class DictionaryGlobalEvent(Base):
    """
    Słownik wydarzeń globalnych wpływających na cały rynek BTC.
    """
    __tablename__ = 'dictionary_global_events'
    __table_args__ = (
        Index('ix_global_events_time', 'utc_start', 'utc_end'),
        Index('ix_global_events_priority', 'priority'),
        Index('ix_global_events_category', 'category'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), default='GLOBAL')
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)
    volume_impact = Column(String(20), nullable=True)
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)
    dominant_actors = Column(String(20), nullable=True)
    news_sensitivity = Column(String(20), nullable=True)
    category = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self):
        return f"<DictionaryGlobalEvent {self.phase_code} @ {self.utc_start}-{self.utc_end}>"


class DictionaryMacroEvent(Base):
    """
    Słownik wydarzeń makroekonomicznych wpływających na rynek BTC.
    """
    __tablename__ = 'dictionary_macro_events'
    __table_args__ = (
        Index('ix_macro_events_time', 'utc_start', 'utc_end'),
        Index('ix_macro_events_priority', 'priority'),
        Index('ix_macro_events_region', 'region_code'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), nullable=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)
    volume_impact = Column(String(20), nullable=True)
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)
    dominant_actors = Column(String(20), nullable=True)
    news_sensitivity = Column(String(20), nullable=True)
    category = Column(String(20), default='MACRO')
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self):
        return f"<DictionaryMacroEvent {self.phase_code} @ {self.utc_start}-{self.utc_end}>"


class DictionaryOptionsEvent(Base):
    """
    Słownik wydarzeń związanych z wygaśnięciem opcji i futures na BTC.
    """
    __tablename__ = 'dictionary_options_events'
    __table_args__ = (
        Index('ix_options_events_time', 'utc_start', 'utc_end'),
        Index('ix_options_events_priority', 'priority'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), nullable=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)
    volume_impact = Column(String(20), nullable=True)
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)
    dominant_actors = Column(String(20), nullable=True)
    news_sensitivity = Column(String(20), nullable=True)
    category = Column(String(20), default='EVENT')
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self):
        return f"<DictionaryOptionsEvent {self.phase_code} @ {self.utc_start}-{self.utc_end}>"


class DictionaryAlgoEvent(Base):
    """
    Słownik wydarzeń związanych z handlem algorytmicznym.
    """
    __tablename__ = 'dictionary_algo_events'
    __table_args__ = (
        Index('ix_algo_events_time', 'utc_start', 'utc_end'),
        Index('ix_algo_events_priority', 'priority'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), nullable=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)
    volume_impact = Column(String(20), nullable=True)
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)
    dominant_actors = Column(String(20), default='ALGO')
    news_sensitivity = Column(String(20), nullable=True)
    category = Column(String(20), default='ALGO')
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self):
        return f"<DictionaryAlgoEvent {self.phase_code} @ {self.utc_start}-{self.utc_end}>"


class DictionarySpecialEvent(Base):
    """
    Słownik specjalnych wydarzeń rynkowych (Halving, CME Gap, Funding Rate, etc.).
    """
    __tablename__ = 'dictionary_special_events'
    __table_args__ = (
        Index('ix_special_events_time', 'utc_start', 'utc_end'),
        Index('ix_special_events_priority', 'priority'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), nullable=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)
    volume_impact = Column(String(20), nullable=True)
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)
    dominant_actors = Column(String(20), nullable=True)
    news_sensitivity = Column(String(20), nullable=True)
    category = Column(String(20), default='EVENT')
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self):
        return f"<DictionarySpecialEvent {self.phase_code} @ {self.utc_start}-{self.utc_end}>"


class DictionarySocialEvent(Base):
    """
    Słownik wydarzeń związanych z aktywnością w mediach społecznościowych.
    """
    __tablename__ = 'dictionary_social_events'
    __table_args__ = (
        Index('ix_social_events_time', 'utc_start', 'utc_end'),
        Index('ix_social_events_priority', 'priority'),
        Index('ix_social_events_region', 'region_code'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_code = Column(String(100), nullable=False, unique=True)
    region_code = Column(String(10), nullable=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    utc_start = Column(String(10), nullable=False)
    utc_end = Column(String(10), nullable=False)
    wraps_midnight = Column(Boolean, default=False)
    priority = Column(Integer, nullable=False, default=10)
    volatility_level = Column(String(20), nullable=True)
    volume_impact = Column(String(20), nullable=True)
    typical_duration_min = Column(Integer, nullable=True)
    trading_pattern = Column(String(20), nullable=True)
    dominant_actors = Column(String(20), default='RETAIL')
    news_sensitivity = Column(String(20), default='HIGH')
    category = Column(String(20), default='SESSION')
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self):
        return f"<DictionarySocialEvent {self.phase_code} ({self.region_code}) @ {self.utc_start}-{self.utc_end}>"


# === Dane Makroekonomiczne i Indeksy Rynkowe ===

class MarketIndex(Base):
    """
    Indeksy rynkowe z tradycyjnych rynków finansowych.
    
    Przechowuje dane o:
    - S&P 500 (^GSPC) - główny indeks US
    - NASDAQ (^IXIC) - indeks technologiczny
    - VIX (^VIX) - indeks zmienności/strachu
    - DXY (DX-Y.NYB) - indeks dolara
    - Złoto (GC=F) - safe haven
    - Obligacje 10Y (^TNX) - yields
    
    Źródło: Yahoo Finance (yfinance)
    """
    __tablename__ = 'market_indices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)  # ^GSPC, ^VIX, DX-Y.NYB
    name = Column(String(50), nullable=False)  # SPX, VIX, DXY, NASDAQ, GOLD
    
    # Dane cenowe
    value = Column(Float, nullable=False)  # Aktualna wartość indeksu
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    
    # Zmiany
    change_1h = Column(Float, nullable=True)  # % zmiana 1h
    change_24h = Column(Float, nullable=True)  # % zmiana 24h
    change_7d = Column(Float, nullable=True)  # % zmiana 7d
    
    # Metadane
    source = Column(String(50), default='yfinance')
    created_at = Column(DateTime, default=utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', 'symbol', name='uq_market_index'),
        Index('ix_market_indices_lookup', 'symbol', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MarketIndex {self.name}={self.value:.2f} @ {self.timestamp}>"


class FearGreedIndex(Base):
    """
    Crypto Fear & Greed Index z alternative.me.
    
    Skala 0-100:
    - 0-24: Extreme Fear (okazja kupna?)
    - 25-44: Fear
    - 45-55: Neutral
    - 56-75: Greed
    - 76-100: Extreme Greed (okazja sprzedaży?)
    
    Aktualizowany raz dziennie.
    Źródło: https://api.alternative.me/fng/
    """
    __tablename__ = 'alternative_me_fear_greed_index'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Wartość indeksu
    value = Column(Integer, nullable=False)  # 0-100
    classification = Column(String(20), nullable=False)  # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
    
    # Kontekst
    btc_price_at_reading = Column(Float, nullable=True)  # Cena BTC w momencie odczytu
    
    # Zmiany
    value_change_24h = Column(Integer, nullable=True)  # Zmiana wartości vs wczoraj
    value_change_7d = Column(Integer, nullable=True)  # Zmiana wartości vs tydzień temu
    
    # Metadane
    time_until_update = Column(String(50), nullable=True)  # Z API
    source = Column(String(50), default='alternative.me')
    created_at = Column(DateTime, default=utcnow)
    
    __table_args__ = (
        UniqueConstraint('timestamp', name='uq_alternative_me_fear_greed_index'),
        Index('ix_alternative_me_fear_greed_index_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<FearGreedIndex {self.value} ({self.classification}) @ {self.timestamp}>"


class EconomicCalendar(Base):
    """
    Kalendarz wydarzeń ekonomicznych (FOMC, CPI, NFP, etc.).
    
    Śledzimy wydarzenia, które historycznie wpływają na BTC:
    - FOMC meetings (8x/rok)
    - CPI releases (miesięcznie)
    - NFP (non-farm payrolls, miesięcznie)
    - GDP releases (kwartalnie)
    - ECB decisions
    
    Źródło: Investing.com, ForexFactory, lub manual
    """
    __tablename__ = 'manual_economic_calendar'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(DateTime, nullable=False, index=True)
    
    # Opis wydarzenia
    event_name = Column(String(100), nullable=False)  # FOMC Rate Decision
    event_type = Column(String(50), nullable=False)  # FOMC, CPI, NFP, GDP, ECB
    country = Column(String(10), nullable=False, default='US')  # US, EU, JP, CN
    
    # Ważność
    importance = Column(String(10), nullable=False)  # high, medium, low
    
    # Dane (wypełniane po publikacji)
    actual = Column(Float, nullable=True)
    forecast = Column(Float, nullable=True)
    previous = Column(Float, nullable=True)
    
    # Wpływ na rynek
    btc_price_before = Column(Float, nullable=True)
    btc_price_after_1h = Column(Float, nullable=True)
    btc_price_after_24h = Column(Float, nullable=True)
    
    # Metadane
    notes = Column(Text, nullable=True)
    source = Column(String(50), default='manual')
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    __table_args__ = (
        UniqueConstraint('event_date', 'event_name', name='uq_economic_event'),
        Index('ix_economic_calendar_lookup', 'event_type', 'event_date'),
        Index('ix_economic_calendar_country', 'country', 'event_date'),
    )
    
    def __repr__(self):
        return f"<EconomicCalendar {self.event_name} @ {self.event_date}>"


class SentimentPropagation(Base):
    """
    Metryki propagacji sentymentu między regionami (APAC, EU, US).
    
    Analizuje jak sentyment propaguje się przez strefy czasowe:
    - APAC (Asia-Pacific): UTC+8 to UTC+12
    - EU (Europe): UTC+0 to UTC+3
    - US (Americas): UTC-8 to UTC-3
    
    Metryki:
    - Korelacje z opóźnieniem czasowym (lagged correlations)
    - Prędkość propagacji (propagation speed)
    - Amplifikacja/tłumienie sentymentu
    - Leading region (region wiodący)
    - Global Activity Index (GAI)
    """
    __tablename__ = 'google_trends_sentiment_propagation'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Korelacje z opóźnieniem czasowym (lagged correlations)
    asia_to_eu_corr = Column(Numeric(5, 4), nullable=True)      # Asia → EU (lag 4h)
    eu_to_us_corr = Column(Numeric(5, 4), nullable=True)        # EU → US (lag 4h)
    us_to_asia_corr = Column(Numeric(5, 4), nullable=True)      # US → Asia (overnight, lag 12h)
    
    # Prędkość propagacji (godziny)
    propagation_speed_hours = Column(Numeric(4, 2), nullable=True)
    
    # Amplifikacja lub tłumienie
    asia_to_eu_amplification = Column(Numeric(5, 4), nullable=True)  # EU_sentiment / Asia_sentiment
    eu_to_us_amplification = Column(Numeric(5, 4), nullable=True)    # US_sentiment / EU_sentiment
    us_to_asia_amplification = Column(Numeric(5, 4), nullable=True)  # Asia_sentiment / US_sentiment
    
    # Leading region
    leading_region = Column(String(10), nullable=True)  # APAC, EU, US, MIXED, NONE
    
    # Global Activity Index
    gai_score = Column(Numeric(10, 4), nullable=True)
    
    # Sentyment per region (surowy)
    asia_sentiment = Column(Numeric(10, 4), nullable=True)
    eu_sentiment = Column(Numeric(10, 4), nullable=True)
    us_sentiment = Column(Numeric(10, 4), nullable=True)
    
    # Liczba pomiarów per region
    asia_measurements_count = Column(Integer, default=0)
    eu_measurements_count = Column(Integer, default=0)
    us_measurements_count = Column(Integer, default=0)
    
    # Metadane
    calculation_window_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=utcnow)
    
    __table_args__ = (
        Index('ix_google_trends_sentiment_propagation_timestamp', 'timestamp'),
        Index('ix_google_trends_sentiment_propagation_leading_region', 'leading_region', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SentimentPropagation @ {self.timestamp} (leading: {self.leading_region}, GAI: {self.gai_score})>"


class TopTraderAlert(Base):
    """
    Alerty dotyczące aktywności top traderów na dYdX.
    
    Alerty są generowane gdy:
    - Top trader wykonuje dużą transakcję (przekracza threshold)
    - Top trader zmienia znacząco pozycję (net position change)
    - Top trader osiąga określony wolumen w oknie czasowym
    - Top trader ma nietypową aktywność (anomalia)
    """
    __tablename__ = 'dydx_top_trader_alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Trader info
    trader_address = Column(String(42), nullable=False, index=True)
    subaccount_number = Column(Integer, nullable=False)
    trader_rank = Column(Integer, nullable=True)
    
    # Fill info
    fill_id = Column(String(255), nullable=True)
    ticker = Column(String(20), nullable=True, index=True)
    side = Column(String(10), nullable=True)  # BUY, SELL
    price = Column(Numeric(20, 8), nullable=True)
    size = Column(Numeric(20, 8), nullable=True)
    volume_usd = Column(Numeric(20, 2), nullable=True)
    
    # Alert type
    alert_type = Column(String(50), nullable=False, index=True)  # LARGE_TRADE, POSITION_CHANGE, VOLUME_SPIKE, ANOMALY
    alert_severity = Column(String(20), nullable=False, default='medium', index=True)  # low, medium, high, critical
    alert_message = Column(Text, nullable=True)
    
    # Metrics
    threshold_value = Column(Numeric(20, 2), nullable=True)
    actual_value = Column(Numeric(20, 2), nullable=True)
    net_position_before = Column(Numeric(20, 8), nullable=True)
    net_position_after = Column(Numeric(20, 8), nullable=True)
    
    # Context
    window_hours = Column(Integer, nullable=True)
    lookback_hours = Column(Integer, nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Metadata
    alert_metadata = Column(Text, nullable=True)  # JSONB jako Text (SQLAlchemy compatibility) - zmienione z 'metadata' (zarezerwowane)
    created_at = Column(DateTime, default=utcnow)
    
    __table_args__ = (
        Index('ix_dydx_top_trader_alerts_trader', 'trader_address', 'subaccount_number', 'alert_timestamp'),
        Index('ix_dydx_top_trader_alerts_type', 'alert_type', 'alert_severity', 'alert_timestamp'),
        Index('ix_dydx_top_trader_alerts_unread', 'is_read', 'alert_timestamp'),
    )
    
    def __repr__(self):
        return f"<TopTraderAlert {self.alert_type} [{self.alert_severity}] @ {self.alert_timestamp}>"


class OrderFlowImbalance(Base):
    """
    Metryki Order Flow Imbalance z dYdX.
    
    Order Flow Imbalance (OFI) to jedna z najbardziej predykcyjnych zmiennych
    w handlu wysokofrequencyjnym. Bazuje na obserwacji, że nierównowaga między
    wolumenem BUY i SELL jest wyprzedzającym wskaźnikiem ruchu ceny.
    
    Metryki obliczane co godzinę dla każdego tickera.
    """
    __tablename__ = 'dydx_order_flow_imbalance'
    
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    ticker = Column(String(20), primary_key=True)
    
    # Wolumeny
    buy_volume = Column(Numeric(30, 8), nullable=False, default=0)
    sell_volume = Column(Numeric(30, 8), nullable=False, default=0)
    total_volume = Column(Numeric(30, 8), nullable=False, default=0)
    
    # Order Flow Imbalance
    order_flow_imbalance = Column(Numeric(10, 6), nullable=False)  # (buy_volume - sell_volume) / total_volume
    buy_sell_ratio = Column(Numeric(10, 4), nullable=True)
    
    # Liczby transakcji
    buy_count = Column(Integer, nullable=False, default=0)
    sell_count = Column(Integer, nullable=False, default=0)
    total_trades = Column(Integer, nullable=False, default=0)
    
    # Duże transakcje
    large_trade_threshold = Column(Numeric(30, 8), nullable=True)
    large_trade_volume = Column(Numeric(30, 8), default=0)
    large_trade_count = Column(Integer, default=0)
    large_trade_ratio = Column(Numeric(10, 6), nullable=True)
    
    # Whale transakcje
    whale_threshold = Column(Numeric(30, 8), nullable=True)
    whale_volume = Column(Numeric(30, 8), default=0)
    whale_count = Column(Integer, default=0)
    whale_ratio = Column(Numeric(10, 6), nullable=True)
    
    # Ceny
    vwap = Column(Numeric(30, 8), nullable=True)
    avg_price = Column(Numeric(30, 8), nullable=True)
    min_price = Column(Numeric(30, 8), nullable=True)
    max_price = Column(Numeric(30, 8), nullable=True)
    price_range = Column(Numeric(30, 8), nullable=True)
    price_range_pct = Column(Numeric(10, 6), nullable=True)
    
    # Intensywność
    trades_per_minute = Column(Numeric(10, 4), nullable=True)
    volume_per_minute = Column(Numeric(30, 8), nullable=True)
    
    # Momentum
    imbalance_change_1h = Column(Numeric(10, 6), nullable=True)
    volume_change_1h = Column(Numeric(10, 6), nullable=True)
    price_change_1h = Column(Numeric(10, 6), nullable=True)
    
    # Korelacja z OHLCV
    ohlcv_close_price = Column(Numeric(30, 8), nullable=True)
    vwap_deviation_pct = Column(Numeric(10, 6), nullable=True)
    
    # Metadane
    calculation_window_minutes = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    __table_args__ = (
        Index('ix_dydx_order_flow_imbalance_timestamp', 'timestamp'),
        Index('ix_dydx_order_flow_imbalance_ticker', 'ticker', 'timestamp'),
        Index('ix_dydx_order_flow_imbalance_imbalance', 'order_flow_imbalance', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<OrderFlowImbalance {self.ticker} @ {self.timestamp} (OFI: {self.order_flow_imbalance:.4f})>"

