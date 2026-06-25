    import requests
    from bs4 import BeautifulSoup
    import os

    TOKEN = os.environ.get('SCRAPE_DO_TOKEN')
    TARGET_URL = "https://www.estrazionidellotto.it/10-e-lotto/estrazioni-10-e-lotto-serale.html"
    CSV_FILE = "storico_10elotto.csv"

    def scrape():
        api_url = f"http://api.scrape.do?token={TOKEN}&url={TARGET_URL}"
        res = requests.get(api_url)
        if res.status_code != 200: return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        try:
            # Parsing della data
            h1_text = soup.find('h1').text
            data_estrazione = h1_text.replace("Estrazione 10eLotto del ", "").strip()
            
            # Parsing numeri (20 numeri)
            numeri_divs = soup.find_all('div', class_='num_estratto_10_e_lotto')
            numeri = " ".join([n.text.strip() for n in numeri_divs[:20]])
            
            # Oro e Doppio Oro
            oro = soup.find('div', class_='num_estratto_oro').text.strip()
            doro = soup.find('div', class_='num_estratto_doppio_oro').text.strip()
            
            # Extra (15 numeri)
            extra_divs = soup.find_all('div', class_='num_estratto_extra')
            extra = " ".join([e.text.strip() for e in extra_divs])
            
            return f"{data_estrazione};{numeri};{oro};{doro};{extra}"
        except Exception as e:
            print(f"Errore parsing: {e}")
            return None

    def update_csv(new_line):
        if not new_line: return
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w') as f: f.write("Date;Numbers;Gold;DoubleGold;Extra\n")
            
        with open(CSV_FILE, 'r') as f:
            lines = f.readlines()
        
        if any(new_line in l for l in lines):
            print("Dati già presenti.")
            return

        header = lines[0]
        old_data = lines[1:]
        with open(CSV_FILE, 'w') as f:
            f.write(header)
            f.write(new_line + "\n")
            f.writelines(old_data)
        print(f"Aggiunta estrazione: {new_line}")

    line = scrape()
    update_csv(line)
    
