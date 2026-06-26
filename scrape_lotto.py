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
        # Trasforma 25/06/2026 in Giovedì 25 giugno 2026
        d = datetime.strptime(date_str, "%d/%m/%Y")
        giorni = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{giorni[d.weekday()]} {d.day} {mesi[d.month]} {d.year}"
    except:
        return date_str

def scrape():
    # USIAMO RENDER=TRUE per far caricare i numeri da JavaScript
    api_url = f"http://api.scrape.do?token={TOKEN}&url={TARGET_URL}&render=true"
    print("Scaricamento pagina con rendering attivo...")
    try:
        res = requests.get(api_url)
        if res.status_code != 200: 
            print(f"Errore Scrape.do: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. RECUPERA DATA
        text_content = soup.get_text()
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text_content)
        raw_date = date_match.group(1) if date_match else ""
        formatted_date = format_date_it(raw_date)
        print(f"Data trovata: {formatted_date}")

        # 2. RECUPERA NUMERI (Miriamo al blocco serale)
        numeri_20 = []
        balls = soup.find_all('span', class_='ball-10elotto')
        for b in balls:
            n = b.text.strip()
            if n and n.isdigit() and n not in numeri_20:
                numeri_20.append(n)
            if len(numeri_20) == 20: break

        # 3. RECUPERA ORO E DOPPIO ORO
        oro_tag = soup.find('span', class_='ball-oro')
        oro = oro_tag.text.strip() if oro_tag else ""
        
        doro_tags = soup.find_all('span', class_='ball-doppio-oro')
        doro = doro_tags[-1].text.strip() if doro_tags else ""
        
        # 4. RECUPERA EXTRA
        extra = []
        extra_tags = soup.find_all('span', class_='ball-extra')
        for e in extra_tags:
            n = e.text.strip()
            if n and n.isdigit() and n not in extra:
                extra.append(n)
            if len(extra) == 15: break

        print(f"Trovati: {len(numeri_20)} num, Oro: {oro}, Doro: {doro}, Extra: {len(extra)}")

        if len(numeri_20) < 20:
            print("Errore: I numeri non sono stati caricati correttamente.")
            return None

        return f"{formatted_date};{' '.join(numeri_20)};{oro};{doro};{' '.join(extra)}"
        
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        return None

def update_csv(new_line):
    if not new_line:
        print("Scraping fallito.")
        return
        
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("Date;Numbers;Gold;DoubleGold;Extra\n")
            
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_nuova = new_line.split(';')[0].strip()
    header = lines[0]
    filtered_lines = []
    
    for l in lines[1:]:
        # Pulizia rigorosa di vecchi errori e duplicati
        if "25/06/2026" in l or "Data non trovata" in l or data_nuova in l or not l.strip():
            continue
        filtered_lines.append(l.strip())
    
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(header.strip() + "\n")
        f.write(new_line + "\n")
        for fl in filtered_lines:
            f.write(fl + "\n")
            
    print(f"OPERAZIONE COMPLETATA: {data_nuova}")

# Esecuzione
update_csv(scrape())
