# Instrukcja obsługi biblioteki PyTrends

## Spis treści
1. [Wprowadzenie](#wprowadzenie)
2. [Instalacja](#instalacja)
3. [Podstawowe użycie](#podstawowe-użycie)
4. [Zaawansowane funkcje](#zaawansowane-funkcje)
5. [Przykłady użycia](#przykłady-użycia)
6. [Obsługa błędów](#obsługa-błędów)
7. [Ograniczenia i uwagi](#ograniczenia-i-uwagi)
8. [Dodatkowe zasoby](#dodatkowe-zasoby)

## Wprowadzenie

PyTrends to nieoficjalne API dla Google Trends, które umożliwia automatyczne pobieranie raportów z Google Trends za pomocą prostego interfejsu w języku Python. Biblioteka ta jest przydatna dla analityków danych, badaczy rynku oraz wszystkich zainteresowanych analizą popularności wyszukiwań w Google.

### Główne możliwości PyTrends:
- Pobieranie danych o zainteresowaniu wyszukiwaniami w czasie
- Analiza zainteresowania według regionu/geografii
- Wyszukiwanie powiązanych zapytań
- Analiza trendów dla wielu słów kluczowych jednocześnie
- Eksport danych do formatów DataFrame (pandas)

## Instalacja

### Wymagania systemowe
- Python 3.3 lub nowszy
- pip (menedżer pakietów Python)

### Instalacja przez pip

```bash
pip install pytrends
```

Lub jeśli używasz Python 3:

```bash
pip3 install pytrends
```

### Weryfikacja instalacji

Aby sprawdzić, czy PyTrends został poprawnie zainstalowany:

```python
import pytrends
print(pytrends.__version__)
```

### Zależności

PyTrends automatycznie instaluje następujące zależności:
- `requests` - do wykonywania zapytań HTTP
- `lxml` - do parsowania HTML/XML
- `pandas` - do pracy z danymi w formacie DataFrame

## Podstawowe użycie

### 1. Importowanie biblioteki

Na początku zaimportuj niezbędne moduły:

```python
from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime
```

### 2. Inicjalizacja połączenia

Zainicjalizuj połączenie z Google Trends:

```python
pytrends = TrendReq(hl='pl-PL', tz=360)
```

**Parametry inicjalizacji:**
- `hl='pl-PL'` - język interfejsu (pl-PL dla polskiego, en-US dla angielskiego)
- `tz=360` - strefa czasowa w minutach od UTC (360 = UTC+6, 0 = UTC, -120 = UTC-2 dla Polski użyj -120)
- `retries=2` - liczba ponownych prób przy błędach (opcjonalne)
- `backoff_factor=0.1` - czas oczekiwania między ponownymi próbami (opcjonalne)
- `requests_args={'headers': {...}}` - dodatkowe nagłówki HTTP (opcjonalne)

**Przykład dla Polski:**
```python
pytrends = TrendReq(hl='pl-PL', tz=-120)  # UTC-2 dla Polski
```

### 3. Budowanie zapytania (Payload)

Zdefiniuj listę słów kluczowych i zbuduj zapytanie:

```python
# Lista słów kluczowych (maksymalnie 5)
kw_list = ["Python", "Java", "JavaScript"]

# Budowanie zapytania
pytrends.build_payload(kw_list, cat=0, timeframe='today 12-m', geo='PL', gprop='')
```

**Parametry build_payload:**
- `kw_list` - lista słów kluczowych (maksymalnie 5 elementów)
- `cat=0` - kategoria (0 = wszystkie kategorie, inne wartości: 7=Finanse, 71=Technologia, itd.)
- `timeframe` - zakres czasowy:
  - `'today 5-y'` - ostatnie 5 lat
  - `'today 12-m'` - ostatnie 12 miesięcy
  - `'today 3-m'` - ostatnie 3 miesiące
  - `'today 1-m'` - ostatni miesiąc
  - `'now 7-d'` - ostatnie 7 dni
  - `'now 1-d'` - ostatnie 24 godziny
  - `'YYYY-MM-DD YYYY-MM-DD'` - zakres dat (np. `'2020-01-01 2020-12-31'`)
- `geo='PL'` - kod kraju (PL dla Polski, US dla USA, '' dla całego świata)
- `gprop=''` - typ wyszukiwania:
  - `''` - wyszukiwanie w sieci (domyślnie)
  - `'images'` - wyszukiwanie obrazów
  - `'news'` - wyszukiwanie wiadomości
  - `'youtube'` - wyszukiwanie w YouTube
  - `'froogle'` - wyszukiwanie produktów

### 4. Pobieranie danych

#### Zainteresowanie w czasie (Interest Over Time)

Pobiera dane o zainteresowaniu wyszukiwaniami w określonym przedziale czasowym:

```python
data = pytrends.interest_over_time()
print(data.head())
print(data.info())
```

**Wynik:**
- DataFrame z datami jako indeksem
- Kolumny dla każdego słowa kluczowego z wartościami 0-100
- Kolumna `isPartial` wskazująca, czy dane są częściowe

**Przykład użycia:**
```python
data = pytrends.interest_over_time()
# Usuń kolumnę isPartial jeśli nie jest potrzebna
if 'isPartial' in data.columns:
    data = data.drop('isPartial', axis=1)
    
# Wyświetl statystyki
print(data.describe())

# Zapisz do pliku CSV
data.to_csv('trends_data.csv')
```

#### Zainteresowanie według regionu (Interest By Region)

Pobiera dane o zainteresowaniu według regionu geograficznego:

```python
region_data = pytrends.interest_by_region(
    resolution='COUNTRY', 
    inc_low_vol=True, 
    inc_geo_code=False
)
print(region_data.head())
```

**Parametry interest_by_region:**
- `resolution` - poziom szczegółowości:
  - `'COUNTRY'` - kraje
  - `'REGION'` - regiony (np. województwa w Polsce)
  - `'CITY'` - miasta
  - `'DMA'` - Designated Market Area (tylko dla USA)
- `inc_low_vol=True` - uwzględnia regiony o niskim wolumenie wyszukiwań
- `inc_geo_code=False` - nie uwzględnia kodów geograficznych w wynikach

**Przykład dla Polski:**
```python
# Dane dla województw w Polsce
region_data = pytrends.interest_by_region(
    resolution='REGION',
    inc_low_vol=True,
    inc_geo_code=False
)
print(region_data.sort_values('Python', ascending=False).head(10))
```

#### Powiązane zapytania (Related Queries)

Pobiera zapytania powiązane z wyszukiwanymi słowami kluczowymi:

```python
related_queries = pytrends.related_queries()
print(related_queries)
```

**Wynik:**
- Słownik z kluczami dla każdego słowa kluczowego
- Dla każdego słowa: `'top'` (najpopularniejsze) i `'rising'` (rosnące w popularności)
- Każdy DataFrame zawiera kolumny: `query` (zapytanie) i `value` (wartość)

**Przykład użycia:**
```python
related_queries = pytrends.related_queries()

for keyword in kw_list:
    print(f"\n=== Powiązane zapytania dla: {keyword} ===")
    
    if keyword in related_queries:
        # Najpopularniejsze zapytania
        if 'top' in related_queries[keyword]:
            print("\nTop queries:")
            print(related_queries[keyword]['top'].head(10))
        
        # Rosnące zapytania
        if 'rising' in related_queries[keyword]:
            print("\nRising queries:")
            print(related_queries[keyword]['rising'].head(10))
```

#### Sugestie zapytań (Suggestions)

Pobiera sugestie zapytań dla danego słowa kluczowego:

```python
suggestions = pytrends.suggestions(keyword="Python")
print(suggestions)
```

**Wynik:**
- Lista słowników z sugestiami zawierającymi:
  - `mid` - identyfikator tematu
  - `title` - tytuł sugestii
  - `type` - typ sugestii

## Zaawansowane funkcje

### Pobieranie danych dla wielu zapytań

Jeśli potrzebujesz więcej niż 5 słów kluczowych, musisz wykonać wiele zapytań:

```python
def get_trends_data(keywords_list, timeframe='today 12-m', geo='PL'):
    """
    Pobiera dane trendów dla listy słów kluczowych.
    Automatycznie dzieli na grupy po 5 słów.
    """
    all_data = {}
    
    # Dzielimy na grupy po 5 słów
    for i in range(0, len(keywords_list), 5):
        kw_group = keywords_list[i:i+5]
        
        pytrends = TrendReq(hl='pl-PL', tz=-120)
        pytrends.build_payload(kw_group, timeframe=timeframe, geo=geo)
        
        data = pytrends.interest_over_time()
        if not data.empty:
            # Usuwamy kolumnę isPartial
            if 'isPartial' in data.columns:
                data = data.drop('isPartial', axis=1)
            
            # Dodajemy do słownika
            for kw in kw_group:
                if kw in data.columns:
                    all_data[kw] = data[kw]
    
    # Tworzymy DataFrame z wszystkich danych
    return pd.DataFrame(all_data)

# Użycie
keywords = ["Python", "Java", "JavaScript", "C++", "Go", "Rust", "Swift", "Kotlin"]
trends_data = get_trends_data(keywords)
print(trends_data.head())
```

### Porównywanie trendów

```python
def compare_trends(keywords, timeframe='today 12-m', geo='PL'):
    """
    Porównuje trendy dla wielu słów kluczowych.
    """
    pytrends = TrendReq(hl='pl-PL', tz=-120)
    pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
    
    data = pytrends.interest_over_time()
    if 'isPartial' in data.columns:
        data = data.drop('isPartial', axis=1)
    
    # Oblicz średnią dla każdego słowa
    averages = data.mean().sort_values(ascending=False)
    
    print("Średnie zainteresowanie:")
    print(averages)
    
    return data, averages

# Użycie
keywords = ["Python", "Java", "JavaScript"]
data, averages = compare_trends(keywords)
```

### Eksport danych do bazy danych

```python
import psycopg2
from sqlalchemy import create_engine

def save_to_database(data, table_name='trends_data', db_name='trends_sniffer'):
    """
    Zapisuje dane trendów do bazy danych PostgreSQL.
    """
    # Utwórz połączenie
    engine = create_engine(f'postgresql://octadecimal@localhost/{db_name}')
    
    # Zapisz do bazy
    data.to_sql(table_name, engine, if_exists='append', index=True)
    print(f"Dane zapisane do tabeli {table_name}")

# Użycie
pytrends = TrendReq(hl='pl-PL', tz=-120)
pytrends.build_payload(["Python", "Java"], timeframe='today 12-m', geo='PL')
data = pytrends.interest_over_time()
if 'isPartial' in data.columns:
    data = data.drop('isPartial', axis=1)

save_to_database(data)
```

## Przykłady użycia

### Przykład 1: Analiza trendów technologii

```python
from pytrends.request import TrendReq
import pandas as pd
import matplotlib.pyplot as plt

# Inicjalizacja
pytrends = TrendReq(hl='pl-PL', tz=-120)

# Technologie do analizy
technologies = ["Python", "Java", "JavaScript", "Go", "Rust"]

# Budowanie zapytania
pytrends.build_payload(
    technologies, 
    cat=0, 
    timeframe='today 5-y', 
    geo='PL', 
    gprop=''
)

# Pobieranie danych
data = pytrends.interest_over_time()
if 'isPartial' in data.columns:
    data = data.drop('isPartial', axis=1)

# Wyświetlanie danych
print("Dane o zainteresowaniu technologiami w Polsce (ostatnie 5 lat):")
print(data.head())
print("\nStatystyki:")
print(data.describe())

# Wizualizacja
data.plot(figsize=(12, 6))
plt.title('Trendy technologii w Polsce (ostatnie 5 lat)')
plt.xlabel('Data')
plt.ylabel('Zainteresowanie (0-100)')
plt.legend(title='Technologie')
plt.grid(True)
plt.tight_layout()
plt.savefig('trends_plot.png')
plt.show()
```

### Przykład 2: Analiza regionalna

```python
from pytrends.request import TrendReq
import pandas as pd

# Inicjalizacja
pytrends = TrendReq(hl='pl-PL', tz=-120)

# Słowo kluczowe
pytrends.build_payload(
    ["Python"], 
    cat=0, 
    timeframe='today 12-m', 
    geo='PL', 
    gprop=''
)

# Pobieranie danych regionalnych
region_data = pytrends.interest_by_region(
    resolution='REGION',
    inc_low_vol=True,
    inc_geo_code=False
)

# Sortowanie i wyświetlanie top 10 województw
top_regions = region_data.sort_values('Python', ascending=False).head(10)
print("Top 10 województw pod względem zainteresowania Python:")
print(top_regions)
```

### Przykład 3: Analiza powiązanych zapytań

```python
from pytrends.request import TrendReq

# Inicjalizacja
pytrends = TrendReq(hl='pl-PL', tz=-120)

# Budowanie zapytania
pytrends.build_payload(
    ["Python"], 
    cat=0, 
    timeframe='today 3-m', 
    geo='PL', 
    gprop=''
)

# Pobieranie powiązanych zapytań
related = pytrends.related_queries()

if 'Python' in related:
    print("=== Najpopularniejsze powiązane zapytania ===")
    if 'top' in related['Python']:
        print(related['Python']['top'].head(10))
    
    print("\n=== Rosnące w popularności zapytania ===")
    if 'rising' in related['Python']:
        print(related['Python']['rising'].head(10))
```

### Przykład 4: Porównanie kategorii

```python
from pytrends.request import TrendReq
import pandas as pd

# Inicjalizacja
pytrends = TrendReq(hl='pl-PL', tz=-120)

# Różne kategorie dla tego samego słowa
keyword = "Python"

results = {}

# Kategoria: Wszystkie (0)
pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo='PL')
data_all = pytrends.interest_over_time()
if not data_all.empty and 'isPartial' in data_all.columns:
    data_all = data_all.drop('isPartial', axis=1)
results['Wszystkie'] = data_all[keyword].mean() if keyword in data_all.columns else 0

# Kategoria: Technologia (71)
pytrends.build_payload([keyword], cat=71, timeframe='today 12-m', geo='PL')
data_tech = pytrends.interest_over_time()
if not data_tech.empty and 'isPartial' in data_tech.columns:
    data_tech = data_tech.drop('isPartial', axis=1)
results['Technologia'] = data_tech[keyword].mean() if keyword in data_tech.columns else 0

# Wyświetlanie wyników
print("Średnie zainteresowanie 'Python' w różnych kategoriach:")
for category, value in results.items():
    print(f"{category}: {value:.2f}")
```

## Obsługa błędów

### Typowe błędy i rozwiązania

#### 1. Błąd: "429 Too Many Requests"

Google może ograniczyć liczbę zapytań. Rozwiązanie:

```python
import time
from pytrends.request import TrendReq

pytrends = TrendReq(hl='pl-PL', tz=-120, retries=2, backoff_factor=0.1)

# Dodaj opóźnienia między zapytaniami
def safe_build_payload(pytrends, kw_list, **kwargs):
    try:
        pytrends.build_payload(kw_list, **kwargs)
    except Exception as e:
        print(f"Błąd: {e}")
        print("Oczekiwanie 60 sekund przed ponowną próbą...")
        time.sleep(60)
        pytrends.build_payload(kw_list, **kwargs)
```

#### 2. Błąd: Puste dane

Jeśli otrzymujesz puste dane, sprawdź:

```python
data = pytrends.interest_over_time()

if data.empty:
    print("Brak danych. Sprawdź:")
    print("1. Czy słowa kluczowe są poprawne")
    print("2. Czy zakres czasowy jest odpowiedni")
    print("3. Czy kod kraju jest poprawny")
else:
    print(f"Otrzymano {len(data)} rekordów")
```

#### 3. Błąd: "The request failed: Google returned a response with code 429"

Rozwiązanie - dodaj opóźnienia i obsługę błędów:

```python
import time
from pytrends.request import TrendReq

def get_trends_with_retry(keywords, max_retries=3, delay=60):
    """
    Pobiera dane trendów z automatycznymi ponownymi próbami.
    """
    for attempt in range(max_retries):
        try:
            pytrends = TrendReq(hl='pl-PL', tz=-120)
            pytrends.build_payload(keywords, timeframe='today 12-m', geo='PL')
            data = pytrends.interest_over_time()
            return data
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Błąd (próba {attempt + 1}/{max_retries}): {e}")
                print(f"Oczekiwanie {delay} sekund...")
                time.sleep(delay)
            else:
                raise
    return None

# Użycie
data = get_trends_with_retry(["Python", "Java"])
```

## Ograniczenia i uwagi

### Ważne ograniczenia:

1. **Limit słów kluczowych**: Maksymalnie 5 słów kluczowych na jedno zapytanie
2. **Ograniczenia API Google**: Google może ograniczyć liczbę zapytań (rate limiting)
3. **Dane względne**: Wartości są względne (0-100), nie bezwzględne liczby wyszukiwań
4. **Dane częściowe**: Ostatnie dane mogą być częściowe (kolumna `isPartial`)
5. **Nieoficjalne API**: PyTrends nie jest oficjalnym API Google, może przestać działać po zmianach w Google Trends

### Najlepsze praktyki:

1. **Dodawaj opóźnienia**: Między zapytaniami dodawaj opóźnienia (np. 1-2 sekundy)
2. **Obsługa błędów**: Zawsze obsługuj wyjątki i błędy
3. **Cache danych**: Zapisz pobrane dane, aby uniknąć ponownych zapytań
4. **Sprawdzaj dane**: Zawsze sprawdzaj, czy dane nie są puste
5. **Respektuj limity**: Nie nadużywaj API, aby uniknąć blokady

### Przykład z cache:

```python
import pickle
import os
from datetime import datetime, timedelta

def get_cached_trends(keywords, cache_file='trends_cache.pkl', cache_hours=24):
    """
    Pobiera dane trendów z cache jeśli są świeże.
    """
    # Sprawdź cache
    if os.path.exists(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_time < timedelta(hours=cache_hours):
            print("Używam danych z cache...")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    
    # Pobierz nowe dane
    print("Pobieranie nowych danych...")
    pytrends = TrendReq(hl='pl-PL', tz=-120)
    pytrends.build_payload(keywords, timeframe='today 12-m', geo='PL')
    data = pytrends.interest_over_time()
    
    # Zapisz do cache
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)
    
    return data

# Użycie
data = get_cached_trends(["Python", "Java"])
```

## Dodatkowe zasoby

### Oficjalne źródła:
- **Repozytorium GitHub**: [https://github.com/GeneralMills/pytrends](https://github.com/GeneralMills/pytrends)
- **Dokumentacja PyPI**: [https://pypi.org/project/pytrends/](https://pypi.org/project/pytrends/)
- **Google Trends**: [https://trends.google.com/](https://trends.google.com/)

### Przydatne linki:
- Lista kodów krajów: [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
- Lista kategorii Google Trends: Sprawdź w interfejsie Google Trends lub dokumentacji PyTrends

### Przykładowe kategorie:
- `0` - Wszystkie kategorie
- `7` - Finanse
- `71` - Technologia
- `12` - Wiadomości
- `19` - Rozrywka
- `22` - Podróże

---

## Podsumowanie

PyTrends to potężne narzędzie do analizy trendów Google, które pozwala na:
- Automatyczne pobieranie danych o zainteresowaniu wyszukiwaniami
- Analizę trendów w czasie i przestrzeni
- Wyszukiwanie powiązanych zapytań
- Integrację z pandas i innymi bibliotekami Python

Pamiętaj o ograniczeniach API i zawsze dodawaj odpowiednią obsługę błędów oraz opóźnienia między zapytaniami.

---

*Ostatnia aktualizacja: 2025-12-22*

