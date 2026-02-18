import httpx
import re
from bs4 import BeautifulSoup
from collections import Counter

# --- [DATABASE MASTER POLA KHUSUS MACAU] ---
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

def fetch_macau_m17():
    """
    SCRAPER OTOMATIS: Mengambil data langsung dari base url M17.
    Mencegah Error 500 dengan fallback data jika server target down.
    """
    url = "https://9yjus6z6kz.salamrupiah.com/history/result-mobile/m17-pool-1"
    results = []
    try:
        with httpx.Client(timeout=15.0, verify=False) as client:
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            # Mencari table dengan class table-history sesuai response HTML yang diberikan
            table = soup.find('table', class_='table-history')
            if table:
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        # Mengambil angka dari kolom ke-3 (index 2) yang ada di dalam tag <a>
                        val = tds[2].text.strip()
                        # Pastikan hanya angka 4 digit
                        clean_val = re.sub(r'\D', '', val)
                        if len(clean_val) == 4:
                            results.append(clean_val)
        return results
    except Exception as e:
        print(f"Scraper Macau Error: {e}")
        return []

def calculate_macau_prediction(results):
    """
    LOGIC KUNCI: Pola rumus dan analisa dipertajam di sini.
    Bagian ini tidak akan mengganggu sistem fetch data di atas.
    """
    try:
        if not results or len(results) < 1:
            return {
                "core_2d": "NO DATA", "bbfs": "N/A", "as_kop": "00", 
                "kop_kep": "00", "shio": "N/A", "macau_twin": "N/A"
            }

        # Mengambil result terakhir (misal: 9452)
        d0 = str(results[0]).zfill(4)
        
        # --- [1. BBFS ANALYSER] ---
        # Mencari angka 'hutang' dari 20 putaran terakhir
        full_history = "".join(map(str, results[:20]))
        counts = Counter(full_history)
        
        scores = {n: (20 - counts.get(n, 0)) for n in "0123456789"}
        for n in "0123456789":
            for i, res in enumerate(results[:15]):
                if n in str(res):
                    scores[n] += (i * 2.5)
                    break
        
        # Buang angka yang baru keluar agar tidak meleset
        for char in d0:
            scores[char] -= 20

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [2. RUMUS CORE 2D & SHIO] ---
        # Rumus: MB(Kop) + TY(Ekor)
        line_2d = [
            MB_MC.get(d0[1], '0') + TY_MC.get(d0[3], '0'),
            ID_MC.get(d0[0], '0') + ML_MC.get(d0[2], '0'),
            "17", "35", "62" # Jalur abadi
        ]
        
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12 

        return {
            "core_2d": ", ".join(list(dict.fromkeys(line_2d))),
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + ID_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + MB_MC.get(d0[2], '0'),
            "shio": shio_map.get(shio_idx, "N/A"),
            "macau_twin": f"{d0[2]}{d0[2]}, {TY_MC.get(d0[3], '0')}{TY_MC.get(d0[3], '0')}"
        }
    except Exception:
        return {"core_2d": "ERR", "bbfs": "ERR", "as_kop": "00", "kop_kep": "00", "shio": "N/A", "macau_twin": "00"}
