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
        
        # 1. Trova il blocco dell'ultima estrazione (serale)
        # Di solito è il primo media-body che contiene i numeri
        draw_block = soup.find('div', class_='media-body')
        if not draw_block:
            print("Blocco estrazione non trovato")
            return None
        
        # 2. Estrai la DATA corretta
        # Cerchiamo il testo che contiene il giorno (es: Giovedì 25 Giugno 2026)
        date_element = draw_block.find(string=re.compile(r'(Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica)', re.I))
        data_estrazione = date_element.strip() if date_element else "Data non trovata"
        print(f"Data trovata: {data_estrazione}")

        # 3. Estrai i 20 NUMERI (ball-10elotto)
        numeri_20 = [n.text.strip() for n in draw_block.find_all('span', class_='ball-10elotto')]
        
        # 4. Estrai ORO e DOPPIO ORO
        oro_tag = draw_block.find('span', class_='ball-oro')
        doro_tag = draw_block.find('span', class_='ball-doppio-oro')
        
        oro = oro_tag.text.strip() if oro_tag else ""
        doro = doro_tag.text.strip() if doro_tag else ""
        
        # 5. Estrai i 15 NUMERI EXTRA (ball-extra)
        extra = [e.text.strip() for e in draw_block.find_all('span', class_='ball-extra')]
        
        # Se ball-extra non ci sono, li prendiamo per posizione
        if not extra:
            all_balls = [b.text.strip() for b in draw_block.find_all('span', class_=re.compile(r'ball'))]
            if len(all_balls) >= 37:
                extra = all_balls[22:37]

        print(f"Parsing completato: {len(numeri_20)} numeri, Oro: {oro}, Doro: {doro}, Extra: {len(extra)}")

        if len(numeri_20) < 20:
            return None

        return f"{data_estrazione};{' '.join(numeri_20)};{oro};{doro};{' '.join(extra)}"
        
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        return None

def update_csv(new_line):
    if not new_line:
        print("Nessun dato valido da aggiungere.")
        return
        
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("Date;Numbers;Gold;DoubleGold;Extra\n")
            
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_nuova = new_line.split(';')[0].strip()
    
    # Pulizia: Creiamo una nuova lista di righe escludendo doppioni e la riga errata precedente
    filtered_lines = [lines[0]] # Teniamo l'header
    for l in lines[1:]:
        # Escludiamo la riga con l'errore precedente e quella con la stessa data
        if "ultimi 60 giorni" in l or data_nuova in l:
            continue
        filtered_lines.append(l)
    
    # Inseriamo la nuova riga in seconda posizione (sotto l'header)
    filtered_lines.insert(1, new_line + "\n")
    
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.writelines(filtered_lines)
    
    print(f"CSV AGGIORNATO: {data_nuova}")

# Esecuzione
nuova_estrazione = scrape()
update_csv(nuova_estrazione)
