#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Klasa z listą wszystkich krajów obsługiwanych przez Google Trends/PyTrends.
Używa kodów ISO 3166-1 alpha-2.
"""


class PyTrendsCountries:
    """
    Klasa zawierająca listę wszystkich krajów obsługiwanych przez Google Trends.
    Zawiera kody ISO 3166-1 alpha-2 oraz nazwy krajów w języku polskim i angielskim.
    """
    
    # Słownik z kodami krajów i ich nazwami
    COUNTRIES = {
        '': {'pl': 'Cały świat', 'en': 'Worldwide', 'code': ''},
        'AD': {'pl': 'Andora', 'en': 'Andorra', 'code': 'AD'},
        'AE': {'pl': 'Zjednoczone Emiraty Arabskie', 'en': 'United Arab Emirates', 'code': 'AE'},
        'AF': {'pl': 'Afganistan', 'en': 'Afghanistan', 'code': 'AF'},
        'AG': {'pl': 'Antigua i Barbuda', 'en': 'Antigua and Barbuda', 'code': 'AG'},
        'AI': {'pl': 'Anguilla', 'en': 'Anguilla', 'code': 'AI'},
        'AL': {'pl': 'Albania', 'en': 'Albania', 'code': 'AL'},
        'AM': {'pl': 'Armenia', 'en': 'Armenia', 'code': 'AM'},
        'AO': {'pl': 'Angola', 'en': 'Angola', 'code': 'AO'},
        'AQ': {'pl': 'Antarktyda', 'en': 'Antarctica', 'code': 'AQ'},
        'AR': {'pl': 'Argentyna', 'en': 'Argentina', 'code': 'AR'},
        'AS': {'pl': 'Samoa Amerykańskie', 'en': 'American Samoa', 'code': 'AS'},
        'AT': {'pl': 'Austria', 'en': 'Austria', 'code': 'AT'},
        'AU': {'pl': 'Australia', 'en': 'Australia', 'code': 'AU'},
        'AW': {'pl': 'Aruba', 'en': 'Aruba', 'code': 'AW'},
        'AX': {'pl': 'Wyspy Alandzkie', 'en': 'Åland Islands', 'code': 'AX'},
        'AZ': {'pl': 'Azerbejdżan', 'en': 'Azerbaijan', 'code': 'AZ'},
        'BA': {'pl': 'Bośnia i Hercegowina', 'en': 'Bosnia and Herzegovina', 'code': 'BA'},
        'BB': {'pl': 'Barbados', 'en': 'Barbados', 'code': 'BB'},
        'BD': {'pl': 'Bangladesz', 'en': 'Bangladesh', 'code': 'BD'},
        'BE': {'pl': 'Belgia', 'en': 'Belgium', 'code': 'BE'},
        'BF': {'pl': 'Burkina Faso', 'en': 'Burkina Faso', 'code': 'BF'},
        'BG': {'pl': 'Bułgaria', 'en': 'Bulgaria', 'code': 'BG'},
        'BH': {'pl': 'Bahrajn', 'en': 'Bahrain', 'code': 'BH'},
        'BI': {'pl': 'Burundi', 'en': 'Burundi', 'code': 'BI'},
        'BJ': {'pl': 'Benin', 'en': 'Benin', 'code': 'BJ'},
        'BL': {'pl': 'Saint-Barthélemy', 'en': 'Saint Barthélemy', 'code': 'BL'},
        'BM': {'pl': 'Bermudy', 'en': 'Bermuda', 'code': 'BM'},
        'BN': {'pl': 'Brunei', 'en': 'Brunei', 'code': 'BN'},
        'BO': {'pl': 'Boliwia', 'en': 'Bolivia', 'code': 'BO'},
        'BQ': {'pl': 'Karaiby Holenderskie', 'en': 'Caribbean Netherlands', 'code': 'BQ'},
        'BR': {'pl': 'Brazylia', 'en': 'Brazil', 'code': 'BR'},
        'BS': {'pl': 'Bahamy', 'en': 'Bahamas', 'code': 'BS'},
        'BT': {'pl': 'Bhutan', 'en': 'Bhutan', 'code': 'BT'},
        'BV': {'pl': 'Wyspa Bouveta', 'en': 'Bouvet Island', 'code': 'BV'},
        'BW': {'pl': 'Botswana', 'en': 'Botswana', 'code': 'BW'},
        'BY': {'pl': 'Białoruś', 'en': 'Belarus', 'code': 'BY'},
        'BZ': {'pl': 'Belize', 'en': 'Belize', 'code': 'BZ'},
        'CA': {'pl': 'Kanada', 'en': 'Canada', 'code': 'CA'},
        'CC': {'pl': 'Wyspy Kokosowe', 'en': 'Cocos Islands', 'code': 'CC'},
        'CD': {'pl': 'Demokratyczna Republika Konga', 'en': 'DR Congo', 'code': 'CD'},
        'CF': {'pl': 'Republika Środkowoafrykańska', 'en': 'Central African Republic', 'code': 'CF'},
        'CG': {'pl': 'Kongo', 'en': 'Congo', 'code': 'CG'},
        'CH': {'pl': 'Szwajcaria', 'en': 'Switzerland', 'code': 'CH'},
        'CI': {'pl': 'Wybrzeże Kości Słoniowej', 'en': 'Ivory Coast', 'code': 'CI'},
        'CK': {'pl': 'Wyspy Cooka', 'en': 'Cook Islands', 'code': 'CK'},
        'CL': {'pl': 'Chile', 'en': 'Chile', 'code': 'CL'},
        'CM': {'pl': 'Kamerun', 'en': 'Cameroon', 'code': 'CM'},
        'CN': {'pl': 'Chiny', 'en': 'China', 'code': 'CN'},
        'CO': {'pl': 'Kolumbia', 'en': 'Colombia', 'code': 'CO'},
        'CR': {'pl': 'Kostaryka', 'en': 'Costa Rica', 'code': 'CR'},
        'CU': {'pl': 'Kuba', 'en': 'Cuba', 'code': 'CU'},
        'CV': {'pl': 'Republika Zielonego Przylądka', 'en': 'Cape Verde', 'code': 'CV'},
        'CW': {'pl': 'Curaçao', 'en': 'Curaçao', 'code': 'CW'},
        'CX': {'pl': 'Wyspa Bożego Narodzenia', 'en': 'Christmas Island', 'code': 'CX'},
        'CY': {'pl': 'Cypr', 'en': 'Cyprus', 'code': 'CY'},
        'CZ': {'pl': 'Czechy', 'en': 'Czech Republic', 'code': 'CZ'},
        'DE': {'pl': 'Niemcy', 'en': 'Germany', 'code': 'DE'},
        'DJ': {'pl': 'Dżibuti', 'en': 'Djibouti', 'code': 'DJ'},
        'DK': {'pl': 'Dania', 'en': 'Denmark', 'code': 'DK'},
        'DM': {'pl': 'Dominika', 'en': 'Dominica', 'code': 'DM'},
        'DO': {'pl': 'Dominikana', 'en': 'Dominican Republic', 'code': 'DO'},
        'DZ': {'pl': 'Algieria', 'en': 'Algeria', 'code': 'DZ'},
        'EC': {'pl': 'Ekwador', 'en': 'Ecuador', 'code': 'EC'},
        'EE': {'pl': 'Estonia', 'en': 'Estonia', 'code': 'EE'},
        'EG': {'pl': 'Egipt', 'en': 'Egypt', 'code': 'EG'},
        'EH': {'pl': 'Sahara Zachodnia', 'en': 'Western Sahara', 'code': 'EH'},
        'ER': {'pl': 'Erytrea', 'en': 'Eritrea', 'code': 'ER'},
        'ES': {'pl': 'Hiszpania', 'en': 'Spain', 'code': 'ES'},
        'ET': {'pl': 'Etiopia', 'en': 'Ethiopia', 'code': 'ET'},
        'FI': {'pl': 'Finlandia', 'en': 'Finland', 'code': 'FI'},
        'FJ': {'pl': 'Fidżi', 'en': 'Fiji', 'code': 'FJ'},
        'FK': {'pl': 'Falklandy', 'en': 'Falkland Islands', 'code': 'FK'},
        'FM': {'pl': 'Mikronezja', 'en': 'Micronesia', 'code': 'FM'},
        'FO': {'pl': 'Wyspy Owcze', 'en': 'Faroe Islands', 'code': 'FO'},
        'FR': {'pl': 'Francja', 'en': 'France', 'code': 'FR'},
        'GA': {'pl': 'Gabon', 'en': 'Gabon', 'code': 'GA'},
        'GB': {'pl': 'Wielka Brytania', 'en': 'United Kingdom', 'code': 'GB'},
        'GD': {'pl': 'Grenada', 'en': 'Grenada', 'code': 'GD'},
        'GE': {'pl': 'Gruzja', 'en': 'Georgia', 'code': 'GE'},
        'GF': {'pl': 'Gujana Francuska', 'en': 'French Guiana', 'code': 'GF'},
        'GG': {'pl': 'Guernsey', 'en': 'Guernsey', 'code': 'GG'},
        'GH': {'pl': 'Ghana', 'en': 'Ghana', 'code': 'GH'},
        'GI': {'pl': 'Gibraltar', 'en': 'Gibraltar', 'code': 'GI'},
        'GL': {'pl': 'Grenlandia', 'en': 'Greenland', 'code': 'GL'},
        'GM': {'pl': 'Gambia', 'en': 'Gambia', 'code': 'GM'},
        'GN': {'pl': 'Gwinea', 'en': 'Guinea', 'code': 'GN'},
        'GP': {'pl': 'Gwadelupa', 'en': 'Guadeloupe', 'code': 'GP'},
        'GQ': {'pl': 'Gwinea Równikowa', 'en': 'Equatorial Guinea', 'code': 'GQ'},
        'GR': {'pl': 'Grecja', 'en': 'Greece', 'code': 'GR'},
        'GS': {'pl': 'Georgia Południowa i Sandwich Południowy', 'en': 'South Georgia', 'code': 'GS'},
        'GT': {'pl': 'Gwatemala', 'en': 'Guatemala', 'code': 'GT'},
        'GU': {'pl': 'Guam', 'en': 'Guam', 'code': 'GU'},
        'GW': {'pl': 'Gwinea-Bissau', 'en': 'Guinea-Bissau', 'code': 'GW'},
        'GY': {'pl': 'Gujana', 'en': 'Guyana', 'code': 'GY'},
        'HK': {'pl': 'Hongkong', 'en': 'Hong Kong', 'code': 'HK'},
        'HM': {'pl': 'Wyspy Heard i McDonalda', 'en': 'Heard Island', 'code': 'HM'},
        'HN': {'pl': 'Honduras', 'en': 'Honduras', 'code': 'HN'},
        'HR': {'pl': 'Chorwacja', 'en': 'Croatia', 'code': 'HR'},
        'HT': {'pl': 'Haiti', 'en': 'Haiti', 'code': 'HT'},
        'HU': {'pl': 'Węgry', 'en': 'Hungary', 'code': 'HU'},
        'ID': {'pl': 'Indonezja', 'en': 'Indonesia', 'code': 'ID'},
        'IE': {'pl': 'Irlandia', 'en': 'Ireland', 'code': 'IE'},
        'IL': {'pl': 'Izrael', 'en': 'Israel', 'code': 'IL'},
        'IM': {'pl': 'Wyspa Man', 'en': 'Isle of Man', 'code': 'IM'},
        'IN': {'pl': 'Indie', 'en': 'India', 'code': 'IN'},
        'IO': {'pl': 'Brytyjskie Terytorium Oceanu Indyjskiego', 'en': 'British Indian Ocean Territory', 'code': 'IO'},
        'IQ': {'pl': 'Irak', 'en': 'Iraq', 'code': 'IQ'},
        'IR': {'pl': 'Iran', 'en': 'Iran', 'code': 'IR'},
        'IS': {'pl': 'Islandia', 'en': 'Iceland', 'code': 'IS'},
        'IT': {'pl': 'Włochy', 'en': 'Italy', 'code': 'IT'},
        'JE': {'pl': 'Jersey', 'en': 'Jersey', 'code': 'JE'},
        'JM': {'pl': 'Jamajka', 'en': 'Jamaica', 'code': 'JM'},
        'JO': {'pl': 'Jordania', 'en': 'Jordan', 'code': 'JO'},
        'JP': {'pl': 'Japonia', 'en': 'Japan', 'code': 'JP'},
        'KE': {'pl': 'Kenia', 'en': 'Kenya', 'code': 'KE'},
        'KG': {'pl': 'Kirgistan', 'en': 'Kyrgyzstan', 'code': 'KG'},
        'KH': {'pl': 'Kambodża', 'en': 'Cambodia', 'code': 'KH'},
        'KI': {'pl': 'Kiribati', 'en': 'Kiribati', 'code': 'KI'},
        'KM': {'pl': 'Komory', 'en': 'Comoros', 'code': 'KM'},
        'KN': {'pl': 'Saint Kitts i Nevis', 'en': 'Saint Kitts and Nevis', 'code': 'KN'},
        'KP': {'pl': 'Korea Północna', 'en': 'North Korea', 'code': 'KP'},
        'KR': {'pl': 'Korea Południowa', 'en': 'South Korea', 'code': 'KR'},
        'KW': {'pl': 'Kuwejt', 'en': 'Kuwait', 'code': 'KW'},
        'KY': {'pl': 'Kajmany', 'en': 'Cayman Islands', 'code': 'KY'},
        'KZ': {'pl': 'Kazachstan', 'en': 'Kazakhstan', 'code': 'KZ'},
        'LA': {'pl': 'Laos', 'en': 'Laos', 'code': 'LA'},
        'LB': {'pl': 'Liban', 'en': 'Lebanon', 'code': 'LB'},
        'LC': {'pl': 'Saint Lucia', 'en': 'Saint Lucia', 'code': 'LC'},
        'LI': {'pl': 'Liechtenstein', 'en': 'Liechtenstein', 'code': 'LI'},
        'LK': {'pl': 'Sri Lanka', 'en': 'Sri Lanka', 'code': 'LK'},
        'LR': {'pl': 'Liberia', 'en': 'Liberia', 'code': 'LR'},
        'LS': {'pl': 'Lesotho', 'en': 'Lesotho', 'code': 'LS'},
        'LT': {'pl': 'Litwa', 'en': 'Lithuania', 'code': 'LT'},
        'LU': {'pl': 'Luksemburg', 'en': 'Luxembourg', 'code': 'LU'},
        'LV': {'pl': 'Łotwa', 'en': 'Latvia', 'code': 'LV'},
        'LY': {'pl': 'Libia', 'en': 'Libya', 'code': 'LY'},
        'MA': {'pl': 'Maroko', 'en': 'Morocco', 'code': 'MA'},
        'MC': {'pl': 'Monako', 'en': 'Monaco', 'code': 'MC'},
        'MD': {'pl': 'Mołdawia', 'en': 'Moldova', 'code': 'MD'},
        'ME': {'pl': 'Czarnogóra', 'en': 'Montenegro', 'code': 'ME'},
        'MF': {'pl': 'Saint-Martin', 'en': 'Saint Martin', 'code': 'MF'},
        'MG': {'pl': 'Madagaskar', 'en': 'Madagascar', 'code': 'MG'},
        'MH': {'pl': 'Wyspy Marshalla', 'en': 'Marshall Islands', 'code': 'MH'},
        'MK': {'pl': 'Macedonia Północna', 'en': 'North Macedonia', 'code': 'MK'},
        'ML': {'pl': 'Mali', 'en': 'Mali', 'code': 'ML'},
        'MM': {'pl': 'Mjanma', 'en': 'Myanmar', 'code': 'MM'},
        'MN': {'pl': 'Mongolia', 'en': 'Mongolia', 'code': 'MN'},
        'MO': {'pl': 'Makau', 'en': 'Macau', 'code': 'MO'},
        'MP': {'pl': 'Mariany Północne', 'en': 'Northern Mariana Islands', 'code': 'MP'},
        'MQ': {'pl': 'Martynika', 'en': 'Martinique', 'code': 'MQ'},
        'MR': {'pl': 'Mauretania', 'en': 'Mauritania', 'code': 'MR'},
        'MS': {'pl': 'Montserrat', 'en': 'Montserrat', 'code': 'MS'},
        'MT': {'pl': 'Malta', 'en': 'Malta', 'code': 'MT'},
        'MU': {'pl': 'Mauritius', 'en': 'Mauritius', 'code': 'MU'},
        'MV': {'pl': 'Malediwy', 'en': 'Maldives', 'code': 'MV'},
        'MW': {'pl': 'Malawi', 'en': 'Malawi', 'code': 'MW'},
        'MX': {'pl': 'Meksyk', 'en': 'Mexico', 'code': 'MX'},
        'MY': {'pl': 'Malezja', 'en': 'Malaysia', 'code': 'MY'},
        'MZ': {'pl': 'Mozambik', 'en': 'Mozambique', 'code': 'MZ'},
        'NA': {'pl': 'Namibia', 'en': 'Namibia', 'code': 'NA'},
        'NC': {'pl': 'Nowa Kaledonia', 'en': 'New Caledonia', 'code': 'NC'},
        'NE': {'pl': 'Niger', 'en': 'Niger', 'code': 'NE'},
        'NF': {'pl': 'Norfolk', 'en': 'Norfolk Island', 'code': 'NF'},
        'NG': {'pl': 'Nigeria', 'en': 'Nigeria', 'code': 'NG'},
        'NI': {'pl': 'Nikaragua', 'en': 'Nicaragua', 'code': 'NI'},
        'NL': {'pl': 'Holandia', 'en': 'Netherlands', 'code': 'NL'},
        'NO': {'pl': 'Norwegia', 'en': 'Norway', 'code': 'NO'},
        'NP': {'pl': 'Nepal', 'en': 'Nepal', 'code': 'NP'},
        'NR': {'pl': 'Nauru', 'en': 'Nauru', 'code': 'NR'},
        'NU': {'pl': 'Niue', 'en': 'Niue', 'code': 'NU'},
        'NZ': {'pl': 'Nowa Zelandia', 'en': 'New Zealand', 'code': 'NZ'},
        'OM': {'pl': 'Oman', 'en': 'Oman', 'code': 'OM'},
        'PA': {'pl': 'Panama', 'en': 'Panama', 'code': 'PA'},
        'PE': {'pl': 'Peru', 'en': 'Peru', 'code': 'PE'},
        'PF': {'pl': 'Polinezja Francuska', 'en': 'French Polynesia', 'code': 'PF'},
        'PG': {'pl': 'Papua-Nowa Gwinea', 'en': 'Papua New Guinea', 'code': 'PG'},
        'PH': {'pl': 'Filipiny', 'en': 'Philippines', 'code': 'PH'},
        'PK': {'pl': 'Pakistan', 'en': 'Pakistan', 'code': 'PK'},
        'PL': {'pl': 'Polska', 'en': 'Poland', 'code': 'PL'},
        'PM': {'pl': 'Saint-Pierre i Miquelon', 'en': 'Saint Pierre and Miquelon', 'code': 'PM'},
        'PN': {'pl': 'Pitcairn', 'en': 'Pitcairn Islands', 'code': 'PN'},
        'PR': {'pl': 'Portoryko', 'en': 'Puerto Rico', 'code': 'PR'},
        'PS': {'pl': 'Palestyna', 'en': 'Palestine', 'code': 'PS'},
        'PT': {'pl': 'Portugalia', 'en': 'Portugal', 'code': 'PT'},
        'PW': {'pl': 'Palau', 'en': 'Palau', 'code': 'PW'},
        'PY': {'pl': 'Paragwaj', 'en': 'Paraguay', 'code': 'PY'},
        'QA': {'pl': 'Katar', 'en': 'Qatar', 'code': 'QA'},
        'RE': {'pl': 'Reunion', 'en': 'Réunion', 'code': 'RE'},
        'RO': {'pl': 'Rumunia', 'en': 'Romania', 'code': 'RO'},
        'RS': {'pl': 'Serbia', 'en': 'Serbia', 'code': 'RS'},
        'RU': {'pl': 'Rosja', 'en': 'Russia', 'code': 'RU'},
        'RW': {'pl': 'Rwanda', 'en': 'Rwanda', 'code': 'RW'},
        'SA': {'pl': 'Arabia Saudyjska', 'en': 'Saudi Arabia', 'code': 'SA'},
        'SB': {'pl': 'Wyspy Salomona', 'en': 'Solomon Islands', 'code': 'SB'},
        'SC': {'pl': 'Seszele', 'en': 'Seychelles', 'code': 'SC'},
        'SD': {'pl': 'Sudan', 'en': 'Sudan', 'code': 'SD'},
        'SE': {'pl': 'Szwecja', 'en': 'Sweden', 'code': 'SE'},
        'SG': {'pl': 'Singapur', 'en': 'Singapore', 'code': 'SG'},
        'SH': {'pl': 'Święta Helena', 'en': 'Saint Helena', 'code': 'SH'},
        'SI': {'pl': 'Słowenia', 'en': 'Slovenia', 'code': 'SI'},
        'SJ': {'pl': 'Svalbard i Jan Mayen', 'en': 'Svalbard and Jan Mayen', 'code': 'SJ'},
        'SK': {'pl': 'Słowacja', 'en': 'Slovakia', 'code': 'SK'},
        'SL': {'pl': 'Sierra Leone', 'en': 'Sierra Leone', 'code': 'SL'},
        'SM': {'pl': 'San Marino', 'en': 'San Marino', 'code': 'SM'},
        'SN': {'pl': 'Senegal', 'en': 'Senegal', 'code': 'SN'},
        'SO': {'pl': 'Somalia', 'en': 'Somalia', 'code': 'SO'},
        'SR': {'pl': 'Surinam', 'en': 'Suriname', 'code': 'SR'},
        'SS': {'pl': 'Sudan Południowy', 'en': 'South Sudan', 'code': 'SS'},
        'ST': {'pl': 'Wyspy Świętego Tomasza i Książęca', 'en': 'São Tomé and Príncipe', 'code': 'ST'},
        'SV': {'pl': 'Salwador', 'en': 'El Salvador', 'code': 'SV'},
        'SX': {'pl': 'Sint Maarten', 'en': 'Sint Maarten', 'code': 'SX'},
        'SY': {'pl': 'Syria', 'en': 'Syria', 'code': 'SY'},
        'SZ': {'pl': 'Eswatini', 'en': 'Eswatini', 'code': 'SZ'},
        'TC': {'pl': 'Turks i Caicos', 'en': 'Turks and Caicos Islands', 'code': 'TC'},
        'TD': {'pl': 'Czad', 'en': 'Chad', 'code': 'TD'},
        'TF': {'pl': 'Francuskie Terytoria Południowe', 'en': 'French Southern Territories', 'code': 'TF'},
        'TG': {'pl': 'Togo', 'en': 'Togo', 'code': 'TG'},
        'TH': {'pl': 'Tajlandia', 'en': 'Thailand', 'code': 'TH'},
        'TJ': {'pl': 'Tadżykistan', 'en': 'Tajikistan', 'code': 'TJ'},
        'TK': {'pl': 'Tokelau', 'en': 'Tokelau', 'code': 'TK'},
        'TL': {'pl': 'Timor Wschodni', 'en': 'East Timor', 'code': 'TL'},
        'TM': {'pl': 'Turkmenistan', 'en': 'Turkmenistan', 'code': 'TM'},
        'TN': {'pl': 'Tunezja', 'en': 'Tunisia', 'code': 'TN'},
        'TO': {'pl': 'Tonga', 'en': 'Tonga', 'code': 'TO'},
        'TR': {'pl': 'Turcja', 'en': 'Turkey', 'code': 'TR'},
        'TT': {'pl': 'Trynidad i Tobago', 'en': 'Trinidad and Tobago', 'code': 'TT'},
        'TV': {'pl': 'Tuvalu', 'en': 'Tuvalu', 'code': 'TV'},
        'TW': {'pl': 'Tajwan', 'en': 'Taiwan', 'code': 'TW'},
        'TZ': {'pl': 'Tanzania', 'en': 'Tanzania', 'code': 'TZ'},
        'UA': {'pl': 'Ukraina', 'en': 'Ukraine', 'code': 'UA'},
        'UG': {'pl': 'Uganda', 'en': 'Uganda', 'code': 'UG'},
        'UM': {'pl': 'Dalekie Wyspy Mniejsze Stanów Zjednoczonych', 'en': 'United States Minor Outlying Islands', 'code': 'UM'},
        'US': {'pl': 'Stany Zjednoczone', 'en': 'United States', 'code': 'US'},
        'UY': {'pl': 'Urugwaj', 'en': 'Uruguay', 'code': 'UY'},
        'UZ': {'pl': 'Uzbekistan', 'en': 'Uzbekistan', 'code': 'UZ'},
        'VA': {'pl': 'Watykan', 'en': 'Vatican City', 'code': 'VA'},
        'VC': {'pl': 'Saint Vincent i Grenadyny', 'en': 'Saint Vincent and the Grenadines', 'code': 'VC'},
        'VE': {'pl': 'Wenezuela', 'en': 'Venezuela', 'code': 'VE'},
        'VG': {'pl': 'Brytyjskie Wyspy Dziewicze', 'en': 'British Virgin Islands', 'code': 'VG'},
        'VI': {'pl': 'Amerykańskie Wyspy Dziewicze', 'en': 'US Virgin Islands', 'code': 'VI'},
        'VN': {'pl': 'Wietnam', 'en': 'Vietnam', 'code': 'VN'},
        'VU': {'pl': 'Vanuatu', 'en': 'Vanuatu', 'code': 'VU'},
        'WF': {'pl': 'Wallis i Futuna', 'en': 'Wallis and Futuna', 'code': 'WF'},
        'WS': {'pl': 'Samoa', 'en': 'Samoa', 'code': 'WS'},
        'XK': {'pl': 'Kosowo', 'en': 'Kosovo', 'code': 'XK'},
        'YE': {'pl': 'Jemen', 'en': 'Yemen', 'code': 'YE'},
        'YT': {'pl': 'Mayotte', 'en': 'Mayotte', 'code': 'YT'},
        'ZA': {'pl': 'Republika Południowej Afryki', 'en': 'South Africa', 'code': 'ZA'},
        'ZM': {'pl': 'Zambia', 'en': 'Zambia', 'code': 'ZM'},
        'ZW': {'pl': 'Zimbabwe', 'en': 'Zimbabwe', 'code': 'ZW'},
    }
    
    @classmethod
    def get_country_code(cls, country_name_pl=None, country_name_en=None, code=None):
        """
        Zwraca kod kraju na podstawie nazwy lub kodu.
        
        Args:
            country_name_pl: Nazwa kraju po polsku
            country_name_en: Nazwa kraju po angielsku
            code: Kod kraju (ISO 3166-1 alpha-2)
        
        Returns:
            str: Kod kraju lub None jeśli nie znaleziono
        """
        if code:
            code = code.upper()
            if code in cls.COUNTRIES:
                return code
            return None
        
        if country_name_pl:
            for code, data in cls.COUNTRIES.items():
                if data['pl'].lower() == country_name_pl.lower():
                    return code
        
        if country_name_en:
            for code, data in cls.COUNTRIES.items():
                if data['en'].lower() == country_name_en.lower():
                    return code
        
        return None
    
    @classmethod
    def get_country_name(cls, code, language='pl'):
        """
        Zwraca nazwę kraju na podstawie kodu.
        
        Args:
            code: Kod kraju (ISO 3166-1 alpha-2)
            language: Język nazwy ('pl' lub 'en')
        
        Returns:
            str: Nazwa kraju lub None jeśli nie znaleziono
        """
        code = code.upper() if code else ''
        if code in cls.COUNTRIES:
            return cls.COUNTRIES[code].get(language, None)
        return None
    
    @classmethod
    def list_all_countries(cls, language='pl', sort_by='code'):
        """
        Zwraca listę wszystkich krajów.
        
        Args:
            language: Język nazw ('pl' lub 'en')
            sort_by: Sortowanie ('code', 'name')
        
        Returns:
            list: Lista słowników z informacjami o krajach
        """
        countries = []
        for code, data in cls.COUNTRIES.items():
            countries.append({
                'code': code,
                'name_pl': data['pl'],
                'name_en': data['en'],
                'name': data[language]
            })
        
        if sort_by == 'code':
            countries.sort(key=lambda x: x['code'])
        elif sort_by == 'name':
            countries.sort(key=lambda x: x['name'])
        
        return countries
    
    @classmethod
    def display_countries(cls, language='pl', sort_by='name', limit=None):
        """
        Wyświetla listę krajów.
        
        Args:
            language: Język nazw ('pl' lub 'en')
            sort_by: Sortowanie ('code', 'name')
            limit: Maksymalna liczba krajów do wyświetlenia (None = wszystkie)
        """
        countries = cls.list_all_countries(language, sort_by)
        
        if limit:
            countries = countries[:limit]
        
        print(f"\n{'='*70}")
        print(f"Lista krajów obsługiwanych przez Google Trends ({len(countries)} krajów)")
        print(f"{'='*70}")
        print(f"{'Kod':<6} {'Nazwa':<50}")
        print(f"{'-'*70}")
        
        for country in countries:
            print(f"{country['code']:<6} {country['name']:<50}")
        
        print(f"{'='*70}\n")
    
    @classmethod
    def search_countries(cls, query, language='pl'):
        """
        Wyszukuje kraje na podstawie zapytania.
        
        Args:
            query: Tekst do wyszukania (w nazwie kraju lub kodzie)
            language: Język nazw ('pl' lub 'en')
        
        Returns:
            list: Lista pasujących krajów
        """
        query = query.lower()
        results = []
        
        for code, data in cls.COUNTRIES.items():
            if (query in data['pl'].lower() or 
                query in data['en'].lower() or 
                query in code.lower()):
                results.append({
                    'code': code,
                    'name_pl': data['pl'],
                    'name_en': data['en'],
                    'name': data[language]
                })
        
        return results


if __name__ == "__main__":
    # Przykłady użycia
    print("=== Przykłady użycia klasy PyTrendsCountries ===\n")
    
    # Wyświetl wszystkie kraje
    PyTrendsCountries.display_countries(language='pl', sort_by='name', limit=20)
    
    # Wyszukaj kraj
    print("\n=== Wyszukiwanie: 'pol' ===")
    results = PyTrendsCountries.search_countries('pol', language='pl')
    for country in results:
        print(f"{country['code']}: {country['name']}")
    
    # Pobierz kod kraju
    print("\n=== Pobieranie kodu dla 'Polska' ===")
    code = PyTrendsCountries.get_country_code(country_name_pl='Polska')
    print(f"Kod: {code}")
    
    # Pobierz nazwę kraju
    print("\n=== Pobieranie nazwy dla kodu 'PL' ===")
    name = PyTrendsCountries.get_country_name('PL', language='pl')
    print(f"Nazwa: {name}")
    
    # Lista wszystkich krajów
    print(f"\n=== Łączna liczba krajów: {len(PyTrendsCountries.COUNTRIES)} ===")

