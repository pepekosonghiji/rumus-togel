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
    LOGIC V12: FREQUENCY-GAP HYBRID
    Pertajaman BBFS dengan pembobotan ganda dan pengisian otomatis Core 2D.
    """
    try:
        if not results or len(results) < 2:
            return {
                "core_2d": "MENUNGGU DATA", "bbfs": "-", "as_kop": "00", 
                "kop_kep": "00", "shio": "-", "macau_twin": "-"
            }

        # Data Primer: 9452 (d0) dan 6449 (d1)
        d0 = str(results[0]).zfill(4) 
        d1 = str(results[1]).zfill(4)
        
        # --- [1. PERTAJAMAN BBFS: HYBRID SCORING] ---
        full_history = "".join(map(str, results[:40])) # Pantau 40 putaran
        counts = Counter(full_history)
        
        scores = {n: 0 for n in "0123456789"}
        for n in "0123456789":
            # Skor 1: Kelangkaan (Semakin jarang muncul di 40 putaran, semakin tinggi)
            scores[n] = (60 - counts.get(n, 0))
            
            # Skor 2: Gap Absen (Mencari angka yang 'jatuh tempo')
            for i, res in enumerate(results[:25]):
                if n in str(res):
                    scores[n] += (i * 4.5) # Bobot gap ditingkatkan ke 4.5
                    break
        
        # FILTER ANTI-STUCK: Buang angka dari result terakhir (9,4,5,2)
        # Tapi biarkan angka dari result sebelumnya (6,4,4,9) jika gap-nya tinggi
        for char in d0:
            scores[char] -= 80 

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [2. PERBAIKAN CORE 2D: AUTO-FILL SYSTEM] ---
        # Rumus A: Mistik Baru dari (AS d0 + EKOR d1)
        # Rumus B: Index dari (KOP d0 + KEPALA d0)
        
        # Pastikan angka 2D selalu terisi dengan mengambil top skor BBFS
        top1 = bbfs_final[0]
        top2 = bbfs_final[1]
        top3 = bbfs_final[2]

        line_2d = [
            top1 + top2, # Kombinasi 1-2
            top1 + top3, # Kombinasi 1-3
            MB_MC.get(d0[1], '0') + ID_MC.get(d0[3], '0'), # Pola Mistik-Index
            TY_MC.get(d0[2], '0') + top1 # Pola Taysen-Top
        ]
        
        # --- [3. SHIO & TWIN RE-CALIBRATION] ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12 

        # Twin wajib diisi dari 2 angka teratas BBFS
        twin1 = f"{top1}{top1}"
        twin2 = f"{top2}{top2}"

        return {
            "core_2d": ", ".join(list(dict.fromkeys(line_2d))),
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + MB_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + TY_MC.get(d0[2], '0'),
            "shio": shio_map.get(shio_idx, "N/A"),
            "macau_twin": f"{twin1}, {twin2}"
        }
    except Exception as e:
        return {"core_2d": "ERR", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau_twin": "-"}
