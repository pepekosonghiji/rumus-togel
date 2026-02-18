import httpx
import re
from bs4 import BeautifulSoup
from collections import Counter

# --- [DATABASE MASTER POLA - TIDAK DISENTUH] ---
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

def fetch_macau_m17():
    """SCRAPER KUNCI: Mengambil data result dari tabel history M17."""
    url = "https://9yjus6z6kz.salamrupiah.com/history/result-mobile/m17-pool-1"
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False) as client:
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', class_='table-history')
            if table:
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        val = re.sub(r'\D', '', tds[2].text.strip())
                        if len(val) == 4: results.append(val)
        return results
    except:
        return []

def calculate_macau_prediction(results):
    """LOGIC ANALYSA - TIDAK DISENTUH LOGIKANYA, HANYA SINKRONISASI LABEL KE HTML"""
    try:
        if not results:
            return {"core": "-", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}

        d0 = str(results[0]).zfill(4)
        
        # --- [LOGIKA ANALYSA BBFS] ---
        full_history = "".join(results[:40])
        counts = Counter(full_history)
        scores = {n: (40 - counts.get(n, 0)) for n in "0123456789"}
        for char in d0: scores[char] -= 60
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [LOGIKA ANALYSA 2D] ---
        c1 = ID_MC.get(d0[0], '0') + MB_MC.get(d0[1], '0')
        c2 = TY_MC.get(d0[2], '0') + bbfs_final[0]
        c3 = bbfs_final[1] + bbfs_final[2]

        # --- [SHIO & MACAU] ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12
        shio_name = shio_map.get(shio_idx, "N/A")
        
        # PENTING: HTML Bos minta format 'SHIO - SHIO', maka kita buatkan macau_val
        macau_val = f"{shio_name} - {shio_map.get((shio_idx + 6) % 12, 'N/A')}"

        # RETURN HARUS SESUAI DENGAN PANGGILAN DI SCRIPT HTML BOS
        return {
            "core": f"{c1}, {c2}, {c3}",
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + ID_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + MB_MC.get(d0[2], '0'),
            "shio": shio_name,
            "macau": macau_val, # Supaya .split(' - ')[0] di HTML tidak error
            "twin": f"{bbfs_final[0]}{bbfs_final[0]}, {d0[3]}{d0[3]}"
        }
    except:
        return {"core": "ERR", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}
