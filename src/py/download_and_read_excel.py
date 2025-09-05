import requests
import zipfile
import io
import pandas as pd
import pytz
from datetime import date, datetime, timedelta, time

def get_dst_dates(year):
    march_last_sunday = date(year, 3, 31)
    while march_last_sunday.weekday() != 6:
        march_last_sunday -= timedelta(days=1)

    october_last_sunday = date(year, 10, 31)
    while october_last_sunday.weekday() != 6:
        october_last_sunday -= timedelta(days=1)

    return march_last_sunday, october_last_sunday

def create_datetime_with_dst(row, march_dst, october_dst):
    italy_tz = pytz.timezone('Europe/Rome')
    current_date = row['Date']
    hour = row['Hour']

    if current_date == march_dst:
        if hour <= 2:
            naive_dt = datetime.combine(current_date, time(hour - 1, 0))
            return italy_tz.localize(naive_dt, is_dst=False)
        else:
            naive_dt = datetime.combine(current_date, time(hour, 0))
            return italy_tz.localize(naive_dt, is_dst=True)
    elif current_date == october_dst:
        if hour <= 3:
            naive_dt = datetime.combine(current_date, time(hour - 1, 0))
            return italy_tz.localize(naive_dt, is_dst=True)
        elif hour == 4:
            naive_dt = datetime.combine(current_date, time(2, 0))
            return italy_tz.localize(naive_dt, is_dst=False)
        else:
            naive_dt = datetime.combine(current_date, time(hour - 2, 0))
            return italy_tz.localize(naive_dt, is_dst=False)
    else:
        naive_dt = datetime.combine(current_date, time(hour - 1, 0))
        try:
            return italy_tz.localize(naive_dt, is_dst=None)
        except:
            is_dst_period = current_date > march_dst and current_date < october_dst
            return italy_tz.localize(naive_dt, is_dst=is_dst_period)

def get_italian_holidays(year):
    """Festività italiane principali per l'anno specificato"""
    holidays = [
        f"{year}-01-01",  # Capodanno
        f"{year}-01-06",  # Epifania
        f"{year}-04-25",  # Festa della Liberazione
        f"{year}-05-01",  # Festa del Lavoro
        f"{year}-06-02",  # Festa della Repubblica
        f"{year}-08-15",  # Ferragosto
        f"{year}-11-01",  # Ognissanti
        f"{year}-12-08",  # Immacolata Concezione
        f"{year}-12-25",  # Natale
        f"{year}-12-26",  # Santo Stefano
    ]
    return pd.to_datetime(holidays).date

def get_fascia(row, holidays):
    """Determina la fascia oraria basata sulla logica di CalendarTime.pq"""
    date = row['Date']
    hour = row['Hour']

    if date in holidays:
        return "F3"

    weekday = date.weekday()

    if weekday <= 4:
        if 8 <= hour <= 19:
            return "F1"
        elif hour == 7 or (20 <= hour <= 23):
            return "F2"
        else:
            return "F3"
    elif weekday == 5:
        if 7 <= hour <= 23:
            return "F2"
        else:
            return "F3"
    else:
        return "F3"


year = 2024

url = f"https://www.mercatoelettrico.org/it-it/Home/Esiti/Elettricita/MGP/Statistiche/DatiStorici/moduleId/10874/controller/GmeDatiStoriciItem/action/DownloadFile?fileName=Anno{year}.zip"

response = requests.get(url)
response.raise_for_status()

with zipfile.ZipFile(io.BytesIO(response.content)) as z:
    excel_files = [f for f in z.namelist() if f.endswith('.xls') or f.endswith('.xlsx')]
    if not excel_files:
        raise Exception("Nessun file Excel trovato nello zip.")
    excel_filename = excel_files[0]
    with z.open(excel_filename) as excel_file:
        df = pd.read_excel(excel_file, sheet_name='Prezzi-Prices', usecols=[0, 1, 2])

df.columns = ['Date', 'Hour', 'PUN Index GME']
df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.date

march_dst, october_dst = get_dst_dates(year)
df['DateTime'] = df.apply(lambda row: create_datetime_with_dst(row, march_dst, october_dst), axis=1)

italian_holidays = get_italian_holidays(year)
df['Fascia'] = df.apply(lambda row: get_fascia(row, italian_holidays), axis=1)

df = df[['DateTime', 'Date', 'Hour', 'PUN Index GME', 'Fascia']]