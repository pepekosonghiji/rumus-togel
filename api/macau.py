import httpx
import re
from bs4 import BeautifulSoup
from collections import Counter

# --- [DATABASE MASTER POLA KHUSUS MACAU] ---
# Master index dan mistik yang dikalibrasi untuk ritme M17
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

def fetch_macau_m17():
    """
    SCRAPER KUNCI: Mengambil data result dari tabel history M17.
    Jangan diubah kecuali struktur URL atau HTML target berubah.
    """
    url = "https://9yjus6z6kz.salamrupiah.com/history/result-mobile/m17-pool-1"
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False) as client:
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            # Menargetkan tabel dengan class legend table-history
            table = soup.find('table', class_='table-history')
            if table:
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    # Berdasarkan response HTML, angka berada di kolom ke-3 (index 2)
                    if len(tds) >= 3:
                        val = tds[2].text.strip()
                        clean_val = re.sub(r'\D', '', val)
                        if len(clean_val) == 4:
                            results.append(clean_val)
        return results
    except Exception:
        return []

def calculate_macau_prediction(results):
    try:
        if not results or len(results) < 2:
            return {"core": "DATA MINIM", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "twin": "-"}

        d0 = str(results[0]).zfill(4)
        
        # Penajaman BBFS (Mencari angka yang paling lama tidak muncul)
        full_data = "".join(results[:30])
        counts = Counter(full_data)
        scores = {n: (30 - counts.get(n, 0)) for n in "0123456789"}
        
        # Buang angka yang baru keluar (9452)
        for char in d0: scores[char] -= 50
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]
        
        # Kunci CORE 2D agar TIDAK KOSONG
        # Mengambil kombinasi angka BBFS terkuat
        c1 = bbfs_final[0] + bbfs_final[1]
        c2 = bbfs_final[2] + bbfs_final[3]
        c3 = MB_MC.get(d0[1], '0') + TY_MC.get(d0[3], '0')

        return {
            "core": f"{c1}, {c2}, {c3}", # Ganti 'core_2d' jadi 'core' agar sinkron dengan template
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + ID_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + MB_MC.get(d0[2], '0'),
            "shio": SHIO_MAP_MACAU_M17(d0), # Gunakan fungsi shio yang sudah ada
            "twin": f"{bbfs_final[0]}{bbfs_final[0]}, {bbfs_final[1]}{bbfs_final[1]}"
        }
    except:
        return {"core": "ERR", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "twin": "-"}
