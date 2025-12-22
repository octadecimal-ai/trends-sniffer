#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Klasa z listą regionów i przypisanymi kodami krajów dla analizy trendów kryptowalut.
Regiony oparte na dokumentacji regions.md.
"""

from src.models.countries import PyTrendsCountries


class PyTrendsRegions:
    """
    Klasa zawierająca regiony istotne dla analizy trendów kryptowalut
    z przypisanymi kodami krajów z klasy PyTrendsCountries.
    """
    
    # Słownik z regionami i ich opisami oraz kodami krajów
    REGIONS = {
        'north_america': {
            'name_pl': 'Ameryka Północna',
            'name_en': 'North America',
            'description_pl': 'Najczęściej: główny punkt price discovery. Największa płynność w parach USD, duży udział instytucji, wpływ rynków terminowych (np. CME) i przepływów przez spotowe produkty giełdowe (ETF/ETP), które potrafią generować silne napływy/odpływy kapitału.',
            'description_en': 'Most often: main price discovery point. Largest liquidity in USD pairs, large institutional participation, influence of futures markets (e.g. CME) and flows through spot exchange products (ETF/ETP), which can generate strong capital inflows/outflows.',
            'country_codes': ['US', 'CA'],
            'key_countries_pl': ['Stany Zjednoczone', 'Kanada'],
            'key_countries_en': ['United States', 'Canada']
        },
        'europe': {
            'name_pl': 'Europa',
            'name_en': 'Europe',
            'description_pl': 'Regulacje + kapitał, mocna infrastruktura finansowa. Duży kapitał i rozwinięte rynki finansowe; wpływ regulacji (np. w UE) na dostępność usług, giełd i produktów inwestycyjnych. (Często mniejszy "impuls cenowy" niż USA, ale ważny dla trendu i stabilności rynku).',
            'description_en': 'Regulations + capital, strong financial infrastructure. Large capital and developed financial markets; influence of regulations (e.g. in EU) on availability of services, exchanges and investment products. (Often smaller "price impulse" than USA, but important for trend and market stability).',
            'country_codes': ['DE', 'FR', 'NL', 'GB', 'CH', 'IT', 'ES', 'PL', 'BE', 'AT', 'SE', 'DK', 'FI', 'NO', 'IE', 'PT', 'GR', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SK', 'SI', 'LT', 'LV', 'EE', 'LU', 'MT', 'CY'],
            'key_countries_pl': ['Niemcy', 'Francja', 'Holandia', 'Wielka Brytania', 'Szwajcaria'],
            'key_countries_en': ['Germany', 'France', 'Netherlands', 'United Kingdom', 'Switzerland']
        },
        'asia_pacific': {
            'name_pl': 'Azja–Pacyfik',
            'name_en': 'Asia-Pacific',
            'description_pl': 'Największa masa użytkowników i rosnący on-chain. Region jest bardzo duży i szybko rośnie pod względem aktywności krypto; potrafi napędzać popyt i zmienność (zwłaszcza w godzinach azjatyckich).',
            'description_en': 'Largest user base and growing on-chain. The region is very large and growing rapidly in terms of crypto activity; can drive demand and volatility (especially during Asian hours).',
            'country_codes': ['KR', 'JP', 'SG', 'HK', 'IN', 'VN', 'PK', 'AU', 'NZ', 'ID', 'MY', 'TH', 'PH', 'TW', 'BD', 'LK', 'MM', 'KH', 'LA', 'MN'],
            'key_countries_pl': ['Korea Południowa', 'Japonia', 'Singapur', 'Hongkong', 'Indie', 'Wietnam', 'Pakistan'],
            'key_countries_en': ['South Korea', 'Japan', 'Singapore', 'Hong Kong', 'India', 'Vietnam', 'Pakistan']
        },
        'china': {
            'name_pl': 'Chiny',
            'name_en': 'China',
            'description_pl': 'Wpływ głównie przez politykę + wydobycie/infrastrukturę. Decyzje regulacyjne potrafią zmieniać sentyment globalnie, a wątek wydobycia/łańcucha dostaw sprzętu historycznie bywał istotny. (Dziś wpływ jest bardziej "pośredni" niż w czasach dominacji CNY na giełdach).',
            'description_en': 'Influence mainly through policy + mining/infrastructure. Regulatory decisions can change sentiment globally, and the mining/hardware supply chain thread has historically been important. (Today the influence is more "indirect" than in the days of CNY dominance on exchanges).',
            'country_codes': ['CN', 'HK', 'MO', 'TW'],
            'key_countries_pl': ['Chiny', 'Hongkong'],
            'key_countries_en': ['China', 'Hong Kong']
        },
        'middle_east': {
            'name_pl': 'Bliski Wschód',
            'name_en': 'Middle East',
            'description_pl': 'Rosnący hub kapitału + infrastruktura. Rosnąca rola centrów finansowych i regulowanych stref dla firm krypto; coraz częściej miejsce "parkowania" biznesu i kapitału.',
            'description_en': 'Growing capital hub + infrastructure. Growing role of financial centers and regulated zones for crypto companies; increasingly a place for "parking" business and capital.',
            'country_codes': ['AE', 'BH', 'SA', 'QA', 'IL', 'TR', 'JO', 'LB', 'KW', 'OM', 'YE', 'IQ', 'IR'],
            'key_countries_pl': ['Zjednoczone Emiraty Arabskie', 'Bahrajn', 'Arabia Saudyjska', 'Katar'],
            'key_countries_en': ['United Arab Emirates', 'Bahrain', 'Saudi Arabia', 'Qatar']
        },
        'offshore_hubs': {
            'name_pl': 'Offshore exchange hubs',
            'name_en': 'Offshore exchange hubs',
            'description_pl': 'Ważne, choć to bardziej jurysdykcje giełd niż popyt obywateli. Część dużych giełd/emitentów działa z tych jurysdykcji, więc wpływ przechodzi przez miejsce notowania i płynność, nie przez lokalną gospodarkę.',
            'description_en': 'Important, though these are more exchange jurisdictions than citizen demand. Some large exchanges/issuers operate from these jurisdictions, so influence comes through listing location and liquidity, not through local economy.',
            'country_codes': ['KY', 'SC', 'VG', 'BS', 'BM', 'JE', 'GG', 'IM', 'MT', 'MC', 'LI', 'VG', 'VI', 'CW', 'BQ'],
            'key_countries_pl': ['Kajmany', 'Seszele', 'Brytyjskie Wyspy Dziewicze', 'Bahamy'],
            'key_countries_en': ['Cayman Islands', 'Seychelles', 'British Virgin Islands', 'Bahamas']
        },
        'high_adoption': {
            'name_pl': 'Regiony o wysokiej adopcji w walutach słabych/inflacyjnych',
            'name_en': 'High adoption regions with weak/inflationary currencies',
            'description_pl': 'Wpływ bardziej "popytowy" niż "ustalający cenę". Potrafią podbijać popyt (zwłaszcza na stablecoiny/BTC jako "ucieczkę"), ale zwykle nie one ustawiają globalny kurs tak mocno jak rynki USD z instytucjami.',
            'description_en': 'Influence more "demand-driven" than "price-setting". Can boost demand (especially for stablecoins/BTC as "escape"), but usually do not set global price as strongly as USD markets with institutions.',
            'country_codes': ['NG', 'BR', 'AR', 'TR', 'VE', 'ZW', 'ZM', 'KE', 'GH', 'TZ', 'UG', 'ET', 'AO', 'MZ'],
            'key_countries_pl': ['Nigeria', 'Brazylia', 'Argentyna', 'Turcja'],
            'key_countries_en': ['Nigeria', 'Brazil', 'Argentina', 'Turkey']
        }
    }
    
    @classmethod
    def get_region_countries(cls, region_key, language='pl'):
        """
        Zwraca listę krajów dla danego regionu.
        
        Args:
            region_key: Klucz regionu (np. 'north_america', 'europe')
            language: Język nazw ('pl' lub 'en')
        
        Returns:
            list: Lista słowników z informacjami o krajach w regionie
        """
        if region_key not in cls.REGIONS:
            return []
        
        region = cls.REGIONS[region_key]
        countries = []
        
        for code in region['country_codes']:
            country_name = PyTrendsCountries.get_country_name(code, language)
            if country_name:
                countries.append({
                    'code': code,
                    'name': country_name,
                    'name_pl': PyTrendsCountries.get_country_name(code, 'pl'),
                    'name_en': PyTrendsCountries.get_country_name(code, 'en')
                })
        
        return countries
    
    @classmethod
    def get_region_info(cls, region_key, language='pl'):
        """
        Zwraca informacje o regionie.
        
        Args:
            region_key: Klucz regionu
            language: Język ('pl' lub 'en')
        
        Returns:
            dict: Informacje o regionie lub None
        """
        if region_key not in cls.REGIONS:
            return None
        
        region = cls.REGIONS[region_key]
        return {
            'key': region_key,
            'name': region[f'name_{language}'],
            'description': region[f'description_{language}'],
            'country_codes': region['country_codes'],
            'key_countries': region[f'key_countries_{language}'],
            'country_count': len(region['country_codes'])
        }
    
    @classmethod
    def list_all_regions(cls, language='pl'):
        """
        Zwraca listę wszystkich regionów.
        
        Args:
            language: Język ('pl' lub 'en')
        
        Returns:
            list: Lista słowników z informacjami o regionach
        """
        regions = []
        for key, data in cls.REGIONS.items():
            regions.append({
                'key': key,
                'name': data[f'name_{language}'],
                'description': data[f'description_{language}'],
                'country_codes': data['country_codes'],
                'country_count': len(data['country_codes']),
                'key_countries': data[f'key_countries_{language}']
            })
        return regions
    
    @classmethod
    def display_regions(cls, language='pl'):
        """
        Wyświetla listę wszystkich regionów.
        
        Args:
            language: Język ('pl' lub 'en')
        """
        regions = cls.list_all_regions(language)
        
        print(f"\n{'='*70}")
        print(f"Regiony dla analizy trendów kryptowalut ({len(regions)} regionów)")
        print(f"{'='*70}\n")
        
        for region in regions:
            print(f"{region['key']}: {region['name']}")
            print(f"  Kraje: {region['country_count']}")
            print(f"  Kluczowe kraje: {', '.join(region['key_countries'][:5])}")
            print(f"  Opis: {region['description'][:100]}...")
            print()
    
    @classmethod
    def display_region_details(cls, region_key, language='pl'):
        """
        Wyświetla szczegółowe informacje o regionie.
        
        Args:
            region_key: Klucz regionu
            language: Język ('pl' lub 'en')
        """
        region_info = cls.get_region_info(region_key, language)
        if not region_info:
            print(f"Region '{region_key}' nie został znaleziony.")
            return
        
        countries = cls.get_region_countries(region_key, language)
        
        print(f"\n{'='*70}")
        print(f"Region: {region_info['name']}")
        print(f"{'='*70}")
        print(f"Opis: {region_info['description']}")
        print(f"\nLiczba krajów: {region_info['country_count']}")
        print(f"\nKluczowe kraje: {', '.join(region_info['key_countries'])}")
        print(f"\nWszystkie kraje w regionie ({len(countries)}):")
        print(f"{'-'*70}")
        print(f"{'Kod':<6} {'Nazwa':<50}")
        print(f"{'-'*70}")
        
        for country in countries:
            print(f"{country['code']:<6} {country['name']:<50}")
        
        print(f"{'='*70}\n")
    
    @classmethod
    def get_country_region(cls, country_code):
        """
        Zwraca region(y) do którego należy kraj.
        
        Args:
            country_code: Kod kraju (ISO 3166-1 alpha-2)
        
        Returns:
            list: Lista kluczy regionów zawierających ten kraj
        """
        country_code = country_code.upper()
        regions = []
        
        for region_key, region_data in cls.REGIONS.items():
            if country_code in region_data['country_codes']:
                regions.append(region_key)
        
        return regions
    
    @classmethod
    def search_regions(cls, query, language='pl'):
        """
        Wyszukuje regiony na podstawie zapytania.
        
        Args:
            query: Tekst do wyszukania
            language: Język ('pl' lub 'en')
        
        Returns:
            list: Lista pasujących regionów
        """
        query = query.lower()
        results = []
        
        for region_key, region_data in cls.REGIONS.items():
            if (query in region_data[f'name_{language}'].lower() or
                query in region_data[f'description_{language}'].lower() or
                query in region_key.lower()):
                results.append({
                    'key': region_key,
                    'name': region_data[f'name_{language}'],
                    'description': region_data[f'description_{language}'],
                    'country_count': len(region_data['country_codes'])
                })
        
        return results


if __name__ == "__main__":
    # Przykłady użycia
    print("=== Przykłady użycia klasy PyTrendsRegions ===\n")
    
    # Wyświetl wszystkie regiony
    PyTrendsRegions.display_regions(language='pl')
    
    # Wyświetl szczegóły regionu
    print("\n=== Szczegóły regionu: Ameryka Północna ===")
    PyTrendsRegions.display_region_details('north_america', language='pl')
    
    # Wyszukaj regiony
    print("\n=== Wyszukiwanie: 'azja' ===")
    results = PyTrendsRegions.search_regions('azja', language='pl')
    for region in results:
        print(f"{region['key']}: {region['name']} ({region['country_count']} krajów)")
    
    # Sprawdź do jakiego regionu należy kraj
    print("\n=== Regiony dla kraju: PL (Polska) ===")
    regions = PyTrendsRegions.get_country_region('PL')
    for region_key in regions:
        region_info = PyTrendsRegions.get_region_info(region_key, 'pl')
        print(f"{region_key}: {region_info['name']}")
    
    # Lista wszystkich regionów
    print(f"\n=== Łączna liczba regionów: {len(PyTrendsRegions.REGIONS)} ===")

