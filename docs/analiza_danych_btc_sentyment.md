# Analiza Danych do Pomiaru Propagacji Trendów BTC

## Wprowadzenie

Dokument ten zawiera analizę wszystkich dostępnych danych, które mogą mieć znaczenie w pomiarze propagacji trendów dotyczących giełdy Bitcoin (BTC) na świecie. Głównym parametrem, który będziemy mierzyć, jest **sentyment rynkowy**, określany na podstawie:

1. Słów kluczowych wpisywanych w ciągu ostatniej 1h w danym kraju (Google Trends)
2. Danych geograficznych i ekonomicznych z serwisów:
   - Geonames (dane geograficzne)
   - World Bank (dane ekonomiczne i społeczne)
   - IMF SDMX (dane finansowe i kursowe)

---

## 1. Dane Geograficzne (Geonames)

### 1.1 Podstawowe Informacje o Krajach

| Parametr | Opis | Znaczenie dla Sentymentu BTC |
|----------|------|------------------------------|
| **Kod kraju ISO 2/3** | Identyfikator kraju | Klucz do łączenia danych z różnych źródeł |
| **Populacja** | Liczba mieszkańców | Potencjalna wielkość rynku, siła wpływu na sentyment globalny |
| **Powierzchnia** | Wielkość kraju (km²) | Gęstość zaludnienia wpływa na dostęp do internetu |
| **Kontynent** | Położenie geograficzne | Strefa czasowa wpływa na moment publikacji trendów |
| **Stolica** | Główne centrum finansowe | Koncentracja instytucji finansowych |
| **Waluta** | Waluta lokalna | Korelacja z kursem BTC/waluta lokalna |
| **Języki** | Języki urzędowe | Dobór słów kluczowych do wyszukiwania |

### 1.2 Dane Geograficzne do Analizy Czasowej

| Parametr | Opis | Znaczenie dla Sentymentu BTC |
|----------|------|------------------------------|
| **Strefa czasowa** | UTC offset | Określenie okna czasowego dla trendów 1h |
| **Rozpiętość geograficzna (bounding box)** | North, South, East, West | Dla krajów rozciągniętych wzdłużnicowo - wiele stref czasowych |
| **Gęstość zaludnienia** | Populacja / Powierzchnia | Koncentracja użytkowników internetu |

### 1.3 Regiony Kluczowe dla BTC (na podstawie regions.md)

| Region | Kraje | Znaczenie |
|--------|-------|-----------|
| **Ameryka Północna** | USA, Kanada | Główny punkt price discovery, największa płynność USD, instytucje, CME, ETF/ETP |
| **Europa** | Niemcy, Francja, Holandia, UK, Szwajcaria | Kapitał, regulacje, infrastruktura finansowa |
| **Azja-Pacyfik** | Korea Płd., Japonia, Singapur, Hongkong, Indie, Wietnam, Pakistan | Największa masa użytkowników, wysoka adopcja |
| **Chiny** | Chiny, Hongkong | Wpływ polityki, wydobycie, infrastruktura |
| **Bliski Wschód** | ZEA, Bahrajn, Arabia Saudyjska, Katar | Rosnący hub kapitału, centra finansowe |
| **Offshore Exchange Hubs** | Kajmany, Seszele, BVI, Bahamy | Jurysdykcje giełd krypto |
| **Emerging Crypto Markets** | Nigeria, Turcja, Argentyna, Wenezuela | Wysoka adopcja, inflacja, ucieczka kapitału |

---

## 2. Dane Ekonomiczne (World Bank)

### 2.1 Wskaźniki Makroekonomiczne

| Kod Wskaźnika | Nazwa | Znaczenie dla Sentymentu BTC |
|---------------|-------|------------------------------|
| **SP.POP.TOTL** | Populacja całkowita | Potencjalna wielkość rynku |
| **NY.GDP.MKTP.CD** | PKB (nominalny, USD) | Siła ekonomiczna kraju, potencjał inwestycyjny |
| **NY.GDP.PCAP.CD** | PKB per capita (USD) | Zamożność obywateli, zdolność do inwestycji |
| **FP.CPI.TOTL.ZG** | Inflacja (CPI) | **KLUCZOWY** - wysoka inflacja = ucieczka do BTC |
| **FR.INR.LEND** | Stopa procentowa | Wpływ na atrakcyjność aktywów ryzykownych |
| **PA.NUS.FCRF** | Kurs waluty lokalnej/USD | Stabilność waluty lokalnej |

### 2.2 Wskaźniki Technologiczne i Społeczne

| Kod Wskaźnika | Nazwa | Znaczenie dla Sentymentu BTC |
|---------------|-------|------------------------------|
| **IT.NET.USER.ZS** | Użytkownicy Internetu (% populacji) | Dostęp do giełd krypto |
| **IT.CEL.SETS.P2** | Abonamenty telefonii komórkowej (na 100 osób) | Dostęp do aplikacji tradingowych |
| **SP.URB.TOTL.IN.ZS** | Populacja miejska (% całkowitej) | Koncentracja użytkowników |
| **SE.ADT.LITR.ZS** | Wskaźnik alfabetyzacji | Świadomość finansowa |

### 2.3 Wskaźniki Stabilności Ekonomicznej

| Kod Wskaźnika | Nazwa | Znaczenie dla Sentymentu BTC |
|---------------|-------|------------------------------|
| **SL.UEM.TOTL.ZS** | Stopa bezrobocia | Niepewność ekonomiczna = potencjalne zainteresowanie BTC |
| **BN.CAB.XOKA.CD** | Saldo rachunku bieżącego | Stabilność makroekonomiczna |
| **DT.DOD.DECT.CD** | Dług zewnętrzny | Ryzyko kryzysu walutowego |

### 2.4 Poziom Dochodów (World Bank Classification)

| Kategoria | Opis | Wpływ na Sentyment BTC |
|-----------|------|------------------------|
| **HIC** | High Income Countries | Inwestycje instytucjonalne, stabilny sentyment |
| **UMC** | Upper Middle Income | Rosnące zainteresowanie, spekulacja |
| **LMC** | Lower Middle Income | Wysoka adopcja jako alternatywa dla banków |
| **LIC** | Low Income Countries | Ograniczony dostęp, ale potencjał remittance |

---

## 3. Dane Krypto-Finansowe (IMF SDMX)

### 3.1 Crypto-based Parallel Exchange Rate Premium (WPCPER)

Dane z pliku `dataset_2025-12-22T12_40_16.754606401Z_DEFAULT_INTEGRATION_IMF.STA_WPCPER_6.0.0.csv`:

| Wskaźnik | Kod | Opis | Znaczenie |
|----------|-----|------|-----------|
| **BIT_SHD_PT** | Crypto-based Parallel Exchange Rate Premium (%) | Premia kursu BTC na lokalnym rynku vs USA | **KLUCZOWY** - wysoka premia = restrykcje walutowe, ucieczka kapitału |
| **BIT_SHD_RT** | Crypto-based Parallel Exchange Rate (LCU/USD) | Kurs równoległy BTC/USD w walucie lokalnej | Alternatywny kurs wymiany |

### 3.2 Kraje z Najwyższą Premią BTC (według danych IMF)

Na podstawie analizy danych CSV:

| Kraj | Premia BTC (%) | Interpretacja |
|------|----------------|---------------|
| **Argentyna** | Do 166% (2024-M04) | Ekstremalna ucieczka kapitału, restrykcje walutowe |
| **Nigeria** | Wysoka | Duże ograniczenia forex |
| **Turcja** | Podwyższona | Inflacja, słaba lira |
| **Rosja** | Zmienna | Sankcje, restrykcje |
| **Tajlandia** | Niska (~0-2%) | Stabilny rynek |
| **Australia** | Bliska 0% | Efektywny rynek, brak restrykcji |

### 3.3 Kategorie Rynków (Income Group)

| Kategoria | Przykłady | Charakterystyka |
|-----------|-----------|-----------------|
| **Emerging Markets** | Argentyna, Indonezja, Tajlandia | Wysoka zmienność premii, potencjał spekulacyjny |
| **Advanced Economies** | Australia, Czechy, Japonia | Niska premia, stabilne rynki |

---

## 4. Dane o Wydobyciu BTC (Hashrate)

Dane z pliku `hashrate-by-country.csv`:

### 4.1 Top 10 Krajów wg Hashrate

| Pozycja | Kraj | Hashrate Share (%) | Znaczenie |
|---------|------|-------------------|-----------|
| 1 | **USA** | 37.84% | Dominujący gracz, wpływ na price discovery |
| 2 | **Chiny** | 21.11% | Historyczny lider, nadal istotny mimo banów |
| 3 | **Kazachstan** | 13.22% | Tania energia, hub wydobycia |
| 4 | **Kanada** | 6.48% | Stabilne środowisko regulacyjne |
| 5 | **Rosja** | 4.66% | Tania energia, ale sankcje |
| 6 | **Niemcy** | 3.06% | Instytucjonalne podejście |
| 7 | **Malezja** | 2.51% | Rosnący gracz |
| 8 | **Irlandia** | 1.97% | Centrum danych |
| 9 | **Tajlandia** | 0.96% | Azja-Pacyfik |
| 10 | **Szwecja** | 0.84% | Czysta energia |

### 4.2 Korelacja Hashrate z Sentymentem

| Obserwacja | Znaczenie |
|------------|-----------|
| Kraje z wysokim hashrate mają większy wpływ na price discovery | Monitoring tych krajów jest priorytetowy |
| Koncentracja hashrate w USA i Chinach | Sentyment z tych krajów jest najważniejszy |
| Rosnące hashrate w Kazachstanie, Rosji | Wskazuje na migrację górników |

---

## 5. Słowa Kluczowe do Monitoringu (Google Trends)

### 5.1 Słowa Kluczowe - Sentyment Pozytywny

| Kategoria | Słowa Kluczowe (EN) | Słowa Kluczowe (PL) |
|-----------|---------------------|---------------------|
| **Zakup** | buy bitcoin, how to buy btc, bitcoin purchase | kup bitcoin, jak kupić btc |
| **Inwestycja** | bitcoin investment, btc portfolio, crypto invest | inwestycja bitcoin, portfel krypto |
| **Wzrost** | bitcoin bull, btc moon, bitcoin rally | bitcoin wzrost, btc hossa |
| **Adopcja** | bitcoin ETF, institutional bitcoin, bitcoin legal | bitcoin ETF, instytucje bitcoin |
| **FOMO** | bitcoin all time high, btc ath, bitcoin new high | bitcoin rekord, btc nowy szczyt |

### 5.2 Słowa Kluczowe - Sentyment Negatywny

| Kategoria | Słowa Kluczowe (EN) | Słowa Kluczowe (PL) |
|-----------|---------------------|---------------------|
| **Sprzedaż** | sell bitcoin, bitcoin sell, dump btc | sprzedaj bitcoin, wyprzedaż btc |
| **Strach** | bitcoin crash, btc bear, bitcoin dead | bitcoin krach, btc bessa, bitcoin martwy |
| **Regulacje** | bitcoin ban, crypto regulation, bitcoin illegal | zakaz bitcoin, regulacje krypto |
| **Hack/Scam** | bitcoin hack, crypto scam, bitcoin stolen | bitcoin hack, oszustwo krypto |
| **FUD** | bitcoin energy, bitcoin bubble, bitcoin ponzi | bitcoin energia, bitcoin bańka |

### 5.3 Słowa Kluczowe - Sentyment Neutralny/Informacyjny

| Kategoria | Słowa Kluczowe (EN) | Słowa Kluczowe (PL) |
|-----------|---------------------|---------------------|
| **Cena** | bitcoin price, btc usd, bitcoin rate | cena bitcoin, kurs btc |
| **Informacje** | bitcoin news, crypto news, btc today | bitcoin wiadomości, krypto dziś |
| **Techniczne** | bitcoin halving, btc mining, bitcoin blockchain | bitcoin halving, btc wydobycie |
| **Edukacja** | what is bitcoin, bitcoin explained, how bitcoin works | co to bitcoin, jak działa bitcoin |

### 5.4 Słowa Kluczowe Specyficzne dla Regionów

| Region | Słowa Kluczowe |
|--------|----------------|
| **Argentyna** | bitcoin argentina, dolar blue bitcoin, comprar btc |
| **Nigeria** | buy bitcoin nigeria, naira bitcoin, p2p bitcoin |
| **Turcja** | bitcoin türkiye, btc tl, bitcoin lira |
| **Japonia** | ビットコイン (bitcoin), 仮想通貨 (cryptocurrency) |
| **Korea Płd.** | 비트코인 (bitcoin), 암호화폐 (cryptocurrency), 김치 프리미엄 (kimchi premium) |
| **Rosja** | биткоин (bitcoin), криптовалюта (cryptocurrency) |

---

## 6. Wzorzec Sentymentu - Scoring Model

### 6.1 Formuła Sentymentu dla Kraju

```
SENTYMENT_KRAJU = 
    w1 * SENTYMENT_GOOGLE_TRENDS +
    w2 * PREMIA_BTC_IMF +
    w3 * STABILNOSC_EKONOMICZNA +
    w4 * HASHRATE_SHARE +
    w5 * DOSTEP_INTERNET +
    w6 * INFLACJA_LOKALNA
```

Gdzie wagi (w1-w6) sumują się do 1.0 i są dobierane na podstawie korelacji z ceną BTC.

### 6.2 Wskaźniki Wejściowe

| Wskaźnik | Źródło | Zakres | Interpretacja |
|----------|--------|--------|---------------|
| **SENTYMENT_GOOGLE_TRENDS** | PyTrends | -100 do +100 | Stosunek słów pozytywnych do negatywnych |
| **PREMIA_BTC_IMF** | IMF WPCPER | -10% do +200% | Wyższa premia = negatywny sentyment do waluty lokalnej, pozytywny do BTC |
| **STABILNOSC_EKONOMICZNA** | World Bank | 0 do 100 | Odwrotność inflacji i bezrobocia |
| **HASHRATE_SHARE** | Hashrate CSV | 0% do 40% | Wyższy hashrate = większy wpływ na price discovery |
| **DOSTEP_INTERNET** | World Bank | 0% do 100% | Wyższy dostęp = większy potencjał wpływu |
| **INFLACJA_LOKALNA** | World Bank | 0% do 100%+ | Wyższa inflacja = potencjalnie wyższy sentyment do BTC |

### 6.3 Wagi Sugerowane

| Wskaźnik | Waga | Uzasadnienie |
|----------|------|--------------|
| SENTYMENT_GOOGLE_TRENDS | 0.35 | Bezpośredni pomiar zainteresowania |
| PREMIA_BTC_IMF | 0.20 | Wskaźnik presji kapitałowej |
| STABILNOSC_EKONOMICZNA | 0.15 | Kontekst makroekonomiczny |
| HASHRATE_SHARE | 0.10 | Wpływ na price discovery |
| DOSTEP_INTERNET | 0.10 | Potencjał rynku |
| INFLACJA_LOKALNA | 0.10 | Motywacja do ucieczki w BTC |

---

## 7. Priorytetyzacja Krajów do Monitoringu

### 7.1 Tier 1 - Najwyższy Priorytet (Price Discovery)

| Kraj | Kod | Uzasadnienie |
|------|-----|--------------|
| **USA** | US | Dominujący hashrate (37.84%), CME, ETF, największa płynność |
| **Chiny** | CN | 21% hashrate, wpływ polityki, historyczny lider |
| **Japonia** | JP | Duży rynek retail, yen carry trade |
| **Korea Płd.** | KR | Kimchi premium, silny retail |

### 7.2 Tier 2 - Wysoki Priorytet (Emerging Markets z wysoką adopcją)

| Kraj | Kod | Uzasadnienie |
|------|-----|--------------|
| **Argentyna** | AR | Ekstremalna premia BTC (do 166%), ucieczka kapitału |
| **Nigeria** | NG | Wysoka adopcja, ograniczenia forex |
| **Turcja** | TR | Inflacja, słaba lira |
| **Kazachstan** | KZ | 13% hashrate, hub wydobycia |

### 7.3 Tier 3 - Średni Priorytet (Stabilne rynki)

| Kraj | Kod | Uzasadnienie |
|------|-----|--------------|
| **Niemcy** | DE | Największa gospodarka UE, 3% hashrate |
| **Kanada** | CA | 6.5% hashrate, stabilne regulacje |
| **Australia** | AU | Efektywny rynek, bliska 0% premia |
| **UK** | GB | Centrum finansowe |

### 7.4 Tier 4 - Monitoring Tła (Hub Giełd)

| Kraj/Terytorium | Kod | Uzasadnienie |
|-----------------|-----|--------------|
| **Singapur** | SG | Hub giełd, centrum finansowe |
| **Hongkong** | HK | Brama do Chin |
| **Bahamy** | BS | FTX (historycznie), regulacje krypto |
| **Seszele** | SC | OKX, inne giełdy |

---

## 8. Implementacja w Kodzie

### 8.1 Struktura Danych

```python
class CountrySentimentData:
    country_code: str           # ISO 3166-1 alpha-2
    country_name: str
    timestamp: datetime
    
    # Google Trends (ostatnia 1h)
    trend_score_positive: float  # 0-100
    trend_score_negative: float  # 0-100
    trend_keywords_top: List[str]
    
    # Dane geograficzne (Geonames)
    population: int
    timezone: str
    capital: str
    
    # Dane ekonomiczne (World Bank)
    gdp_per_capita: float
    inflation_rate: float
    internet_users_percent: float
    unemployment_rate: float
    
    # Dane krypto (IMF SDMX)
    btc_premium_percent: float
    btc_parallel_rate: float
    
    # Dane wydobycia
    hashrate_share_percent: float
    
    # Obliczony sentyment
    sentiment_score: float      # -100 do +100
    sentiment_label: str        # 'bullish', 'bearish', 'neutral'
```

### 8.2 Źródła Danych

| Dane | Serwis | Metoda |
|------|--------|--------|
| Trendy wyszukiwań | TrendsSnifferService | get_interest_over_time() |
| Dane geograficzne | GeonamesProvider | get_country_info() |
| Dane ekonomiczne | WorldBankService | get_data_for_indicator() |
| Premia BTC | IMFSDMXService | get_data() (WPCPER) |
| Hashrate | Plik CSV | pandas.read_csv() |

---

## 9. Wnioski i Rekomendacje

### 9.1 Kluczowe Obserwacje

1. **Premia BTC jest najsilniejszym wskaźnikiem** presji kapitałowej w krajach z restrykcjami walutowymi (Argentyna do 166%)
2. **Koncentracja hashrate w USA i Chinach** (łącznie ~59%) oznacza, że sentyment z tych krajów ma największy wpływ na cenę
3. **Rynki wschodzące** (Emerging Markets) wykazują największą zmienność premii BTC
4. **Strefy czasowe** są kluczowe dla określenia okien 1h - Azja, Europa i Ameryka mają różne godziny aktywności

### 9.2 Rekomendacje

1. **Priorytetyzacja monitoringu** krajów Tier 1 i Tier 2
2. **Automatyczne pobieranie danych** co 1h dla krajów z wysokim priorytetem
3. **Korelacja sentymentu z ceną BTC** w celu walidacji modelu
4. **Wielojęzyczne słowa kluczowe** dla kluczowych rynków (Korea, Japonia, Rosja)
5. **Alert system** dla skokowych zmian premii BTC (>10% zmiana)

---

## 10. Załączniki

### 10.1 Lista Krajów z Danymi IMF WPCPER

Kraje dostępne w datasecie IMF:
- Tajlandia (THB)
- Argentyna (ARS) - **najwyższa premia**
- Indonezja (IDR)
- Australia (AUD)
- Czechy (CZK)
- Japonia (JPY)
- i inne...

### 10.2 Lista Krajów z Danymi Hashrate

50 krajów z danymi o udziale w globalnym hashrate.

### 10.3 Źródła

- [IMF SDMX API](https://portal.api.imf.org/)
- [World Bank API](https://api.worldbank.org/)
- [Geonames API](http://api.geonames.org/)
- [Google Trends (PyTrends)](https://trends.google.com/)
- [Cambridge Bitcoin Electricity Consumption Index](https://cbeci.org/mining_map)

---

*Dokument wygenerowany: 2024-12-22*
*Wersja: 1.0*

