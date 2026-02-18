import httpx
import re
from bs4 import BeautifulSoup
from collections import Counter

# --- [DATABASE MASTER POLA - KUNCI TETAP] ---
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

def fetch_macau_m17():
    """SCRAPER KUNCI: Pengambilan data dari server M17."""
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
    """
    PENAJAMAN ANALISA V12.5: 
    - Fokus pada 'Gap Overdue' (Angka yang sudah lewat jatuh tempo).
    - Sinkronisasi 100% dengan UI HTML.
    """
    try:
        if not results or len(results) < 2:
            return {"core": "-", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}

        # Result Terakhir (d0) dan Sebelumnya (d1)
        d0 = str(results[0]).zfill(4)
        d1 = str(results[1]).zfill(4)
        
        # --- 1. BBFS SHARPENING (Weighted Gap Analysis) ---
        full_history = "".join(results[:50]) # Pantau 50 putaran untuk akurasi tinggi
        counts = Counter(full_history)
        
        scores = {n: 0 for n in "0123456789"}
        for n in "0123456789":
            # Skor dasar: Semakin jarang muncul (Cold Number), skor semakin tinggi
            scores[n] = (50 - counts.get(n, 0))
            
            # Bonus Gap: Cari jarak absen terakhir angka tersebut
            for i, res in enumerate(results[:30]):
                if n in str(res):
                    scores[n] += (i * 5) # Bobot gap dinaikkan ke 5x lipat
                    break
                if i == 29: scores[n] += 150 # Angka yang hilang > 30 putaran wajib masuk

        # ANTI-REPEAT: Kurangi skor angka yang baru keluar di d0 dan d1 secara signifikan
        for char in set(d0 + d1):
            scores[char] -= 100

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- 2. CORE 2D SHARPENING (Cross-Pattern) ---
        # Rumus A: Mistik Baru dari KOP terakhir + Index AS sebelumnya
        p1 = MB_MC.get(d0[1], '0') + ID_MC.get(d1[0], '0')
        # Rumus B: Taysen dari KEPALA terakhir + Ekor terakhir
        p2 = TY_MC.get(d0[2], '0') + d0[3]
        # Rumus C: Dua angka teratas BBFS (Angka paling 'berhutang')
        p3 = bbfs_final[0] + bbfs_final[1]

        # --- 3. SHIO & MACAU (UI Logic) ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12
        shio_name = shio_map.get(shio_idx, "N/A")
        macau_val = f"{shio_name} - {shio_map.get((shio_idx + 6) % 12, 'N/A')}"

        # --- 4. TWIN SHARPENING ---
        # Twin diambil dari angka dengan skor tertinggi di BBFS
        tw_1 = bbfs_final[0] + bbfs_final[0]
        tw_2 = bbfs_final[1] + bbfs_final[1]

        return {
            "core": f"{p1}, {p2}, {p3}",
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + ID_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + MB_MC.get(d0[2], '0'),
            "shio": shio_name,
            "macau": macau_val,
            "twin": f"{tw_1}, {tw_2}"
        }
    except:
        return {"core": "ERR", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}
