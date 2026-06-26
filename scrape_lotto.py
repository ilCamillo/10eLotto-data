import requests
from bs4 import BeautifulSoup
import os
import re

TOKEN = os.environ.get('SCRAPE_DO_TOKEN')
TARGET_URL = "https://www.estrazionedellotto.it/10elotto/ultime-estrazioni-10elotto"
CSV_FILE = "storico_10elotto.csv"

def scrape():
    api_url = f"http://api.scrape.do?token={TOKEN}&url={TARGET_URL}"
    try:
        res = requests.get(api_url)
        if res.status_code != 200: 
            print(f"Errore API: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        all_text = soup.get_text()
        
        # 1. CERCA LA DATA (GG/MM/AAAA)
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', all_text)
        data_estrazione = date_match.group(0) if date_match else "Data non trovata"
        print(f"Data trovata: {data_estrazione}")

        # 2. CERCA I NUMERI (Classi specifiche del sito)
        balls_20 = soup.find_all('span', class_='ball-10elotto')
        numeri_20 = [b.text.strip() for b in balls_20[:20]]
        
        oro_tag = soup.find('span', class_='ball-oro')
        oro = oro_tag.text.strip() if oro_tag else ""
        
        doro_tag = soup.find('span', class_='ball-doppio-oro')
        doro = doro_tag.text.strip() if doro_tag else ""
        
        balls_extra = soup.find_all('span', class_='ball-extra')
        extra = [b.text.strip() for b in balls_extra[:15]]

        # FALLBACK se le classi non vengono trovate
        if len(numeri_20) < 20:
            all_balls = [b.text.strip() for b in soup.find_all('span', class_=re.compile(r'ball'))]
            if len(all_balls) >= 37:
                numeri_20 = all_balls[:20]
                oro = all_balls[20]
                doro = all_balls[21]
                extra = all_balls[22:37]

        if len(numeri_20) < 20:
            print("Errore: Numeri non trovati.")
            return None

        return f"{data_estrazione};{' '.join(numeri_20)};{oro};{doro};{' '.join(extra)}"
        
    except Exception as e:
        print(f"Errore: {e}")
        return None

def update_csv(new_line):
    if not new_line or "Data non trovata" in new_line:
        print("Dati non validi.")
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
        if "Data non trovata" in l or data_nuova in l or not l.strip():
            continue
        filtered_lines.append(l.strip())
    
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(header.strip() + "\n")
        f.write(new_line + "\n")
        for fl in filtered_lines:
            f.write(fl + "\n")
            
    print(f"CSV AGGIORNATO: {data_nuova}")

update_csv(scrape())
