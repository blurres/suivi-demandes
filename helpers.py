# helpers.py
import csv
import locale

locale.setlocale(locale.LC_ALL, '')

def get_countries():
    countries = []
    with open('countries.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            countries.append(row['name'])
    return sorted(countries, key=locale.strxfrm)
