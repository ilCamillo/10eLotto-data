import requests
from bs4 import BeautifulSoup
import os
import re

TOKEN = os.environ.get('SCRAPE_DO_TOKEN')
# URL del sito che hai indicato
TARGET_URL = "https://www.estrazionedellotto.it/10elotto/ultime-estrazioni-10elotto"
CSV_FILE = "storico_10elotto.csv"

def scrape():
    api_url = f"http://api.scrape.do?token={TOKEN}&url={TARGET_URL}"
    print(f"Avvio scraping su: {TARGET_URL}")
    try:
        res = requests.get(api_url)
        if res.status_code != 200: 
            print(f"Errore API: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. DATA: La cerchiamo nel testo che contiene "Estrazione Lotto di"
        h1_tag = soup.find('h1')
        if not h1_tag: return None
        # Pulizia: "Estrazione Lotto di Giovedì 25 Giugno 2026" -> "Giovedì 25 Giugno 2026"
        data_estrazione = h1_tag.text.replace("Estrazione Lotto di", "").strip()
        print(f"Data trovata: {data_estrazione}")

        # 2. NUMERI: Nel sito indicato i numeri 10eLotto sono spesso in sfere o celle specifiche
        # Cerchiamo tutti i numeri nel contenitore del 10eLotto
        all_numbers = []
        # Cerchiamo i numeri nelle classi comuni di questo sito (es. 'pallina-10elotto' o simili)
        # In alternativa, prendiamo i numeri dal blocco testo se identificabile
        content = soup.find_all('span', class_=re.compile(r'ball|num|lotto', re.I))
        
        # Tentativo più robusto: cerchiamo i numeri nel contenitore specifico
        # (Adattato alla struttura di estrazionedellotto.it)
        draw_div = soup.find('div', {'id': 'dieci-e-lotto-serale'}) or soup
        balls = draw_div.find_all(text=re.compile(r'^\d{1,2}$'))
        
        # Filtriamo solo i numeri reali (1-90) e rimuoviamo duplicati mantenendo l'ordine
        clean_nums = []
        for b in balls:
            n = b.strip()
            if n.isdigit() and 1 <= int(n) <= 90 and n not in clean_nums:
                clean_nums.append(n)
        
        print(f"Numeri grezzi trovati: {len(clean_nums)}")

        # I primi 20 sono i numeri estratti
        numeri_20 = clean_nums[:20]
        # Il 21esimo e 22esimo sono solitamente Oro e Doppio Oro su questo sito
        oro = clean_nums[20] if len(clean_nums) > 20 else ""
        doro = clean_nums[21] if len(clean_nums) > 21 else ""
        # Dal 23esimo in poi sono gli Extra (solitamente 15)
        extra = clean_nums[22:37] if len(clean_nums) > 22 else []

        if len(numeri_20) < 20:
            print("Non ho trovato abbastanza numeri.")
            return None

        return f"{data_estrazione};{' '.join(numeri_20)};{oro};{doro};{' '.join(extra)}"
        
    except Exception as e:
        print(f"Errore: {e}")
        return None

def update_csv(new_line):
    if not new_line: return
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data_nuova = new_line.split(';')[0].strip()
    if data_nuova in content:
        print(f"Estrazione {data_nuova} già presente.")
        return

    lines = content.splitlines()
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(lines[0] + "\n") # Header
        f.write(new_line + "\n") # Nuova estrazione
        for l in lines[1:]: f.write(l + "\n")
    print("CSV AGGIORNATO!")

update_csv(scrape())
