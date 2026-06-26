import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

TOKEN = os.environ.get('SCRAPE_DO_TOKEN')
TARGET_URL = "https://www.estrazionedellotto.it/10elotto/ultime-estrazioni-10elotto"
CSV_FILE = "storico_10elotto.csv"

def format_date_it(date_str):
    try:
        # Converte 25/06/2026 in "Giovedì 25 giugno 2026"
        d = datetime.strptime(date_str, "%d/%m/%Y")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[d.weekday()]} {d.day} {mesi[d.month]} {d.year}"
    except:
        return date_str

def scrape():
    api_url = f"http://api.scrape.do?token={TOKEN}&url={TARGET_URL}"
    try:
        res = requests.get(api_url)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. DATA (Cerchiamo GG/MM/AAAA e formattiamola)
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', soup.get_text())
        raw_date = date_match.group(1) if date_match else ""
        formatted_date = format_date_it(raw_date)
        print(f"Data formattata: {formatted_date}")

        # 2. NUMERI (Puntiamo solo all'estrazione 10eLotto Serale)
        # Troviamo i numeri escludendo i duplicati che il sito mette per il mobile
        numeri_20 = []
        balls = soup.find_all('span', class_='ball-10elotto')
        for b in balls:
            n = b.text.strip()
            if n and n not in numeri_20:
                numeri_20.append(n)
            if len(numeri_20) == 20: break

        # 3. ORO e DOPPIO ORO
        oro_tag = soup.find('span', class_='ball-oro')
        oro = oro_tag.text.strip() if oro_tag else ""
        
        # Il Doppio Oro è il secondo numero evidenziato
        doro_tags = soup.find_all('span', class_='ball-doppio-oro')
        doro = doro_tags[-1].text.strip() if doro_tags else ""
        
        # 4. EXTRA
        extra = []
        extra_tags = soup.find_all('span', class_='ball-extra')
        for e in extra_tags:
            n = e.text.strip()
            if n and n not in extra:
                extra.append(n)
            if len(extra) == 15: break

        print(f"Recuperati: {len(numeri_20)} num, Oro: {oro}, Doro: {doro}, Extra: {len(extra)}")

        if len(numeri_20) < 20: return None

        return f"{formatted_date};{' '.join(numeri_20)};{oro};{doro};{' '.join(extra)}"
        
    except Exception as e:
        print(f"Errore: {e}")
        return None

def update_csv(new_line):
    if not new_line or "Data non trovata" in new_line: return
    
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("Date;Numbers;Gold;DoubleGold;Extra\n")
            
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_nuova = new_line.split(';')[0].strip()
    header = lines[0]
    filtered_lines = []
    
    for l in lines[1:]:
        # Pulizia: rimuoviamo vecchie righe errate o duplicati
        if "Data non trovata" in l or "25/06/2026" in l or data_nuova in l or not l.strip():
            continue
        filtered_lines.append(l.strip())
    
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(header.strip() + "\n")
        f.write(new_line + "\n")
        for fl in filtered_lines:
            f.write(fl + "\n")
            
    print(f"SUCCESSO: {data_nuova}")

update_csv(scrape())
