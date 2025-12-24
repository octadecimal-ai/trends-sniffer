# 🎯 Plan Badań: Alternatywne Źródła Danych dla Predykcji BTC

## Przegląd Projektu

**Cel:** Identyfikacja i analiza wszystkich potencjalnych źródeł danych, które mogłyby poprawić predykcję kierunku ruchu ceny Bitcoin w horyzoncie 1 godziny.

**Data rozpoczęcia:** 2025-12-24  
**Status:** W trakcie realizacji  
**Autor:** Claude Opus 4.5 + trends-sniffer

---

## 📋 Etapy Realizacji

### Etap 1: Fundament i Planowanie
- [x] Analiza istniejącej struktury bazy danych
- [x] Utworzenie 5 podstawowych kwerend ML
- [x] Eksport początkowych datasetów
- [x] Utworzenie dokumentu z planem etapów
- [ ] Definicja kryteriów oceny źródeł danych
- [ ] Utworzenie szablonu analizy dla każdego źródła

### Etap 2: Profesjonalne Dane Finansowe
- [ ] 2.1 Dane on-chain (blockchain)
  - [ ] NUPL (Net Unrealized Profit/Loss)
  - [ ] MVRV (Market Value to Realized Value)
  - [ ] Exchange Net Flows
  - [ ] Stablecoin Supply Ratio
  - [ ] Miner flows i revenue
  - [ ] Whale wallet movements
- [ ] 2.2 Dane makroekonomiczne
  - [ ] Stopy procentowe (Fed, ECB, BoJ)
  - [ ] Indeksy strachu (VIX, Fear & Greed)
  - [ ] Globalna płynność (M2)
  - [ ] DXY (Dollar Index)
- [ ] 2.3 Korelacje z innymi aktywami
  - [ ] Złoto (XAU)
  - [ ] Ropa (WTI, Brent)
  - [ ] S&P 500, NASDAQ
  - [ ] Bond yields (US10Y)

### Etap 3: Dane z Pogranicza Biznesu (Testowane Historycznie)
- [ ] 3.1 Aktywność deweloperów
  - [ ] GitHub commits/contributors
  - [ ] Protocol upgrades
  - [ ] Developer retention
- [ ] 3.2 Dane społecznościowe
  - [ ] Reddit sentiment/activity
  - [ ] Twitter/X volume i sentiment
  - [ ] Discord/Telegram activity
- [ ] 3.3 Google Trends rozszerzone
  - [ ] Korelacje z wyszukiwaniami
  - [ ] Regional patterns
- [ ] 3.4 Kalendarz wydarzeń
  - [ ] Święta regionalne/globalne
  - [ ] Publikacje ekonomiczne
  - [ ] Events krypto (halvings, upgrades)

### Etap 4: Innowacyjne/Alternatywne Źródła Danych
- [ ] 4.1 Geopolityka i stabilność globalna
  - [ ] Konflikty zbrojne
  - [ ] Sankcje ekonomiczne
  - [ ] Zmiany rządów
- [ ] 4.2 Czynniki środowiskowe
  - [ ] Aktywność słoneczna (sunspots)
  - [ ] Pogoda w kluczowych regionach
  - [ ] Klęski żywiołowe
- [ ] 4.3 Infrastruktura
  - [ ] Obciążenie sieci energetycznej
  - [ ] Ruch internetowy
  - [ ] Awarie infrastruktury
- [ ] 4.4 Czynniki społeczne/psychologiczne
  - [ ] Wyniki sportowe
  - [ ] Nastroje społeczne
  - [ ] Mentalność kulturowa regionów
- [ ] 4.5 Czynniki ezoteryczne/eksperymentalne
  - [ ] Układy planet (astrologia finansowa)
  - [ ] Cykle lunarne
  - [ ] Teorie numeryczne (Fibonacci, Gann)
  - [ ] Butterfly effect / chaos theory
  - [ ] Teorie organizmów (rynek jako organizm)
- [ ] 4.6 **Propagacja Spatio-Temporal** ⭐
  - [ ] Fale sentymentu przez strefy czasowe
  - [ ] Regional Google Trends (minutowe)
  - [ ] GDELT per country/region
  - [ ] Asia → EU → US handoff analysis
  - [ ] Lokalne czynniki (pogoda Silicon Valley, ERCOT grid)
  - [ ] Top Trader Tracking (dYdX whales)
  - [ ] Kimchi Premium (Korea)
  - [ ] Scandinavia daylight/SAD effects
  - [ ] Global Activity Index (GAI)
- [ ] 4.7 **NOWE: Rynek jako Żywy Organizm** 🫀
  - [ ] Vital Signs (puls, ciśnienie, temperatura, saturacja)
  - [ ] Stany patologiczne (gorączka, hipotermia, arytmia)
  - [ ] Cykle życiowe (dobowy, tygodniowy, 4-letni)
  - [ ] Health Score composite
  - [ ] Medical features dla ML
  - [ ] Health Dashboard wizualizacja
  - [ ] Diagnoza i prognoza stanów rynkowych

### Etap 5: Technologie Predykcyjne
- [ ] 5.1 Analiza ML vs LLM
  - [ ] Porównanie architektur
  - [ ] Wymagania danych
  - [ ] Trade-offs
- [ ] 5.2 Możliwości LLM
  - [ ] Reasoning o wydarzeniach
  - [ ] Interpretacja newsów
  - [ ] Multi-modal analysis
- [ ] 5.3 Hybrydowe podejścia
  - [ ] LLM + ML ensemble
  - [ ] Feature extraction przez LLM

### Etap 6: Implementacja i Dokumentacja
- [ ] 6.1 Priorytetyzacja źródeł danych
- [ ] 6.2 Implementacja API/scraperów
- [ ] 6.3 Rozszerzenie schematu bazy
- [ ] 6.4 Nowe kwerendy ML
- [ ] 6.5 Dokumentacja końcowa

---

## 📊 Kryteria Oceny Źródeł Danych

Każde źródło danych będzie oceniane według następujących kryteriów:

| Kryterium | Waga | Opis |
|-----------|------|------|
| **Potencjał predykcyjny** | 30% | Teoretyczny i empiryczny wpływ na cenę |
| **Dostępność danych** | 20% | Czy dane są dostępne (API, scraping, purchase) |
| **Opóźnienie (latency)** | 15% | Jak szybko dane są dostępne |
| **Koszt** | 15% | Bezpłatne vs płatne vs enterprise |
| **Jakość/wiarygodność** | 10% | Konsystencja, brakujące dane |
| **Udokumentowanie** | 10% | Czy są badania potwierdzające |

**Skala oceny:** 1-5 (1 = słaby, 5 = doskonały)

### ⚠️ Filozofia Projektu

> **NIE ODRZUCAMY ŻADNEJ HIPOTEZY BEZ EMPIRYCZNEJ WERYFIKACJI.**
> 
> Wszystko co można zmierzyć, można przetestować.
> ML nie ma uprzedzeń - jeśli korelacja istnieje, model ją znajdzie.
> Nawet "szalone" pomysły (lunar cycles, pogoda) mają peer-reviewed papers!

---

## 📁 Struktura Dokumentacji

```
docs/alternative_data_research/
├── 00_PLAN_ETAPOW.md                    # Ten dokument
├── 01_PROFESJONALNE_FINANSOWE/
│   ├── on_chain_metrics.md
│   ├── makroekonomia.md
│   └── korelacje_aktywa.md
├── 02_POGRANICZE_BIZNESU/
│   ├── developer_activity.md
│   ├── social_media.md
│   └── kalendarz_wydarzen.md
├── 03_ALTERNATYWNE_INNOWACYJNE/
│   ├── geopolityka.md
│   ├── czynniki_srodowiskowe.md
│   ├── infrastruktura.md
│   ├── psychologia_spoleczna.md
│   └── ezoteryczne.md
├── 04_ML_VS_LLM_ANALIZA/
│   ├── porownanie_technologii.md
│   ├── rekomendacje.md
│   └── architektura_hybrydowa.md
└── 05_IMPLEMENTACJA/
    ├── priorytetyzacja.md
    ├── api_sources.md
    └── schemat_bazy.md
```

---

## 🔄 Aktualny Status

| Etap | Status | Postęp |
|------|--------|--------|
| Etap 1 | ✅ Ukończono | 100% |
| Etap 2 | ✅ Ukończono | 100% |
| Etap 3 | ✅ Ukończono | 100% |
| Etap 4 | ✅ Ukończono | 100% |
| Etap 5 | ✅ Ukończono | 100% |
| Etap 6 | ⏳ Implementacja | 30% |

---

## 📝 Notatki i Decyzje

### 2025-12-24
- Rozpoczęcie projektu badawczego
- Zdefiniowanie struktury dokumentacji
- Następny krok: Analiza profesjonalnych danych finansowych (on-chain)

---

*Dokument aktualizowany na bieżąco w trakcie realizacji projektu*

