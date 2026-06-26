import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get('SCRAPE_DO_TOKEN')
# Puntiamo alla pagina che contiene l'ultima estrazione serale
TARGET_URL = "https://www.estrazionidellotto.it/10-e-lotto/estrazioni-10-e-lotto-serale.html"
CSV_FILE = "storico_10elotto.csv"

def scrape():
    api_url = f"http://api.scrape.do?token={TOKEN}&url={TARGET_URL}"
    try:
        res = requests.get(api_url)
        if res.status_code != 200: 
            print(f"Errore Scrape.do: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Parsing della DATA
        # Cerchiamo il titolo che contiene la data dell'estrazione
        h1_tag = soup.find('h1')
        if not h1_tag:
            print("ERRORE: Titolo H1 non trovato nella pagina")
            return None
            
        # Puliamo la stringa per ottenere solo la data (es: "Giovedì 25 Giugno 2026")
        data_estrazione = h1_tag.text.replace("Estrazione 10eLotto del ", "").strip()
        print(f"Data rilevata sul sito: {data_estrazione}")
        
        # 2. Parsing dei 20 NUMERI
        numeri_list = []
        divs = soup.find_all('div', class_='num_estratto_10_e_lotto')
        for d in divs[:20]:
            numeri_list.append(d.text.strip())
        
        if len(numeri_list) < 20:
            print(f"ERRORE: Trovati solo {len(numeri_list)} numeri invece di 20")
            return None
        numeri_str = " ".join(numeri_list)

        # 3. ORO e DOPPIO ORO
        oro_div = soup.find('div', class_='num_estratto_oro')
        doro_div = soup.find('div', class_='num_estratto_doppio_oro')
        
        oro = oro_div.text.strip() if oro_div else ""
        doro = doro_div.text.strip() if doro_div else ""

        # 4. Numeri EXTRA
        extra_list = []
        extra_divs = soup.find_all('div', class_='num_estratto_extra')
        for ed in extra_divs:
            extra_list.append(ed.text.strip())
        extra_str = " ".join(extra_list)

        return f"{data_estrazione};{numeri_str};{oro};{doro};{extra_str}"
        
    except Exception as e:
        print(f"ERRORE durante lo scraping: {e}")
        return None

def update_csv(new_line):
    if not new_line: 
        print("Scraping fallito, nessuna riga da aggiungere.")
        return
        
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write("Date;Numbers;Gold;DoubleGold;Extra\n")
            
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Prendiamo solo la data della nuova estrazione per vedere se c'è già
    nuova_data = new_line.split(';')[0].strip()
    
    # Controlliamo se la data esiste già nel file
    for line in lines:
        if nuova_data.lower() in line.lower():
            print(f"L'estrazione del {nuova_data} è già presente nel CSV. Salto l'aggiornamento.")
            return

    # Se non c'è, la aggiungiamo in cima (subito dopo l'header)
    header = lines[0]
    vecchi_dati = lines[1:]
    with open(CSV_FILE, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(new_line + "\n")
        f.writelines(vecchi_dati)
    print(f"EVVIVA! Aggiunta nuova estrazione: {nuova_data}")

# Esecuzione
risultato = scrape()
update_csv(risultato)
