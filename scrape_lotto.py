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
            print(f"Errore Scrape.do: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. CERCA LA DATA (Formato: Giorno Numero Mese Anno)
        date_pattern = re.compile(r'(Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica)\s+\d+\s+(Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre)\s+\d{4}', re.I)
        all_text = soup.get_text(separator=' ')
        date_match = date_pattern.search(all_text)
        data_estrazione = date_match.group(0).strip() if date_match else "Data non trovata"
        print(f"Data trovata: {data_estrazione}")

        # 2. CERCA TUTTI I NUMERI (Palline)
        # Cerchiamo i numeri basandoci sulle classi CSS o sul contenuto numerico
        balls = soup.find_all('span', class_=re.compile(r'ball|num|pallina', re.I))
        raw_nums = [b.text.strip() for b in balls if b.text.strip().isdigit()]
        
        # Se non trovati con le classi, cerchiamo qualsiasi numero 1-90 isolato
        if len(raw_nums) < 20:
            raw_nums = [t.strip() for t in soup.find_all(string=re.compile(r'^\b\d{1,2}\b$'))]

        # Rimuoviamo duplicati mantenendo l'ordine originale
        clean_nums = []
        for n in raw_nums:
            if n not in clean_nums:
                clean_nums.append(n)
        
        print(f"Numeri unici trovati: {len(clean_nums)}")

        if len(clean_nums) < 20:
            print("ERRORE: Non ho trovato abbastanza numeri nella pagina.")
            return None

        # 3. ASSEGNAZIONE POSIZIONI
        # I primi 20 numeri sono l'estrazione principale
        numeri_20 = clean_nums[:20]
        # Il 21esimo è l'Oro, il 22esimo il Doppio Oro
        oro = clean_nums[20] if len(clean_nums) > 20 else ""
        doro = clean_nums[21] if len(clean_nums) > 21 else ""
        # Dal 23esimo in poi sono gli Extra (solitamente 15 numeri)
        extra = clean_nums[22:37] if len(clean_nums) > 22 else []

        return f"{data_estrazione};{' '.join(numeri_20)};{oro};{doro};{' '.join(extra)}"
        
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        return None

def update_csv(new_line):
    if not new_line:
        print("Scraping fallito, nessuna riga aggiunta.")
        return
        
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("Date;Numbers;Gold;DoubleGold;Extra\n")
            
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data_nuova = new_line.split(';')[0].strip()
    
    # Controlliamo se la data è già presente per non creare duplicati
    if data_nuova in content:
        print(f"L'estrazione del {data_nuova} è già presente nel file.")
        return

    # Inseriamo la nuova riga in alto dopo l'intestazione
    lines = content.splitlines()
    header = lines[0]
    others = lines[1:]
    
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(header + "\n")
        f.write(new_line + "\n")
        for l in others:
            if l.strip(): # Evita righe vuote
                f.write(l + "\n")
    
    print(f"SUCCESSO! CSV aggiornato con l'estrazione del {data_nuova}")

# Esecuzione script
risultato = scrape()
update_csv(risultato)
