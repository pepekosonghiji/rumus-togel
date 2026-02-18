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
    """
    LOGIC V11.0: ADAPTIVE WEIGHTED GAP (AWG)
    Fokus: Memperkuat akurasi BBFS & 2D dengan sistem skor 'Hutang Angka'.
    """
    try:
        if not results or len(results) < 1:
            return {
                "core_2d": "SYNC GAGAL", "bbfs": "-", "as_kop": "00", 
                "kop_kep": "00", "shio": "-", "macau_twin": "-"
            }

        # Mengambil result terakhir (d0) dan result sebelumnya (d1)
        d0 = str(results[0]).zfill(4) 
        d1 = str(results[1]).zfill(4) if len(results) > 1 else "0000"
        
        # --- [1. BBFS SHARPENING: AWG SYSTEM] ---
        # Mengambil histori 30 putaran untuk akurasi lebih dalam
        full_history = "".join(map(str, results[:30])) 
        counts = Counter(full_history)
        
        scores = {n: 0 for n in "0123456789"}
        for n in "0123456789":
            # Semakin jarang muncul secara keseluruhan, skor semakin tinggi
            scores[n] = (40 - counts.get(n, 0))
            
            # Bonus skor berdasarkan jarak (Gap) absennya angka
            for i, res in enumerate(results[:20]):
                if n in str(res):
                    scores[n] += (i * 3.5) # Bobot jarak ditingkatkan menjadi 3.5
                    break
                if i == 19: # Angka yang benar-benar hilang > 20 putaran
                    scores[n] += 100
        
        # FILTER ANTI-STUCK: Memangkas skor angka yang muncul di 2 result terakhir
        # Mencegah jebakan angka repeat (seperti kasus HK 3907)
        combined_last = d0 + d1
        for char in set(combined_last):
            scores[char] -= 60 # Penalti berat agar angka baru bisa naik ke BBFS

        # Urutkan angka berdasarkan skor hutang tertinggi
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [2. RUMUS 2D: CROSS-MIRROR ANALYTICS] ---
        # Kombinasi silang Index, Mistik Baru, dan Taysen
        p1 = ID_MC.get(d0[0], '0') + MB_MC.get(d0[1], '0') # Index As + Mistik Kop
        p2 = TY_MC.get(d0[2], '0') + ID_MC.get(d0[3], '0') # Taysen Kepala + Index Ekor
        
        # Jalur cadangan dari 2 angka BBFS terkuat
        top_gap = bbfs_final[0] + bbfs_final[1]
        
        line_2d = [p1, p2, top_gap, "17", "62", "38"]
        
        # --- [3. SHIO & TWIN] ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12 

        # Twin diambil dari angka hutang tertinggi (bbfs_final[0])
        twin_angka = bbfs_final[0]

        return {
            "core_2d": ", ".join(list(dict.fromkeys(line_2d))),
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + MB_MC.get(d0[1], '0'),
            "kop_kep": TY_MC.get(d0[1], '0') + ML_MC.get(d0[2], '0'),
            "shio": shio_map.get(shio_idx, "N/A"),
            "macau_twin": f"{twin_angka}{twin_angka}, {d0[3]}{d0[3]}"
        }
    except Exception:
        # Emergency Fallback agar tidak Error 500
        return {
            "core_2d": "ERR LOGIC", "bbfs": "-", "as_kop": "00", 
            "kop_kep": "00", "shio": "-", "macau_twin": "-"
        }
