import httpx
import re
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime
import pytz

# --- [DATABASE MASTER POLA - KUNCI TETAP] ---
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

# Database Angka Harian (Data statistik sering muncul)
DAY_MAP = {
    0: "0159", # Senin
    1: "2367", # Selasa
    2: "0489", # Rabu
    3: "1256", # Kamis
    4: "3789", # Jumat
    5: "0247", # Sabtu
    6: "1358"  # Minggu
}

def calculate_macau_prediction(results):
    """
    LOGIC V17.0 - PRECISION ENGINE (MACAU M17)
    Penajaman: Anti-Triple, Day-Weighting, & Gap Analysis.
    """
    try:
        if not results or len(results) < 2:
            return {"core": "-", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}

        d0 = str(results[0]).zfill(4) # Result Terakhir
        d1 = str(results[1]).zfill(4) # Result Sebelumnya
        
        # --- [1. PENGESAN WAKTU & HARI (WIB)] ---
        tz = pytz.timezone('Asia/Jakarta')
        now = datetime.now(tz)
        hour = now.hour
        weekday = now.weekday() # 0 = Senin, 6 = Minggu

        # --- [2. DETEKSI ANOMALI (TRIPLE/TWIN)] ---
        is_triple = (d0[0] == d0[1] == d0[2]) or (d0[1] == d0[2] == d0[3])
        is_twin = (len(set(d0)) < 4) and not is_triple

        # --- [3. PENETAPAN STRATEGI & LIMIT] ---
        if hour in [13, 16]:
            strategy = "SIANG_FLOW"
            weight_repeat = 15 
            limit_history = 30
        elif hour in [19, 22, 23]:
            strategy = "MALAM_MISTIK"
            weight_repeat = -10 
            limit_history = 45
        else:
            strategy = "MIDNIGHT_SHADOW"
            weight_repeat = 5
            limit_history = 60

        # --- [4. BBFS SINKRONISASI (TIME + DAY BASED)] ---
        full_history = "".join(results[:limit_history])
        counts = Counter(full_history)
        scores = {n: counts.get(n, 0) for n in "0123456789"}
        
        # Tambahkan bobot angka harian
        day_leads = DAY_MAP.get(weekday, "")
        for n in day_leads:
            scores[n] += 10

        # Penyesuaian angka repeat berdasarkan jam
        for char in d0:
            scores[char] += weight_repeat

        # JIKA HABIS TRIPLE: Angka triple tersebut biasanya 'mati' di putaran berikutnya
        if is_triple:
            scores[d0[1]] -= 50 

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [5. PENAJAMAN SNIPER 2D (LOGIKA CROSS-GAP)] ---
        # Selisih Ekor d0 dan d1 untuk mencari angka main
        selisih_ekor = str(abs(int(d0[3]) - int(d1[3])))
        angka_ikut = MB_MC.get(selisih_ekor, '5')

        if strategy == "SIANG_FLOW":
            p1 = TY_MC.get(d0[2], '0') + TY_MC.get(d0[3], '0')
            p2 = d0[1] + ID_MC.get(d0[3], '0')
            p3 = angka_ikut + bbfs_final[0]
        
        elif strategy == "MALAM_MISTIK":
            p1 = ML_MC.get(d0[2], '0') + ML_MC.get(d0[3], '0')
            p2 = ID_MC.get(d0[0], '0') + MB_MC.get(d0[2], '0')
            p3 = TY_MC.get(d0[3], '0') + ML_MC.get(d0[1], '0')
            
        else: # MIDNIGHT
            p1 = ID_MC.get(d0[0], '9') + TY_MC.get(d0[3], '9')
            p2 = ML_MC.get(d1[3], '3') + MB_MC.get(d0[2], '4') # Ambil ekor d1
            p3 = bbfs_final[0] + bbfs_final[1]

        # Jalur Cadangan: Antisipasi angka urut/naik
        p4 = str((int(d0[2:]) + 11) % 100).zfill(2) 
        
        core_2d = list(dict.fromkeys([p1, p2, p3, p4, "15", "90"]))
        
        # --- [6. SHIO & TWIN REFINED] ---
        # Shio tetap pakai perhitungan d0
        shio_idx = int(d0[2:]) % 12
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        
        # Logika Twin Pasca Anomali
        if is_triple:
            twin_val = "00, 11, 55" # Penetral setelah triple
        elif hour >= 20:
            twin_val = "99, 77, 33"
        else:
            twin_val = f"{d0[3]}{d0[3]}, {bbfs_final[0]}{bbfs_final[0]}"

        return {
            "core": ", ".join(core_2d[:5]),
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + MB_MC.get(d0[1], '0'),
            "kop_kep": TY_MC.get(d0[1], '0') + ML_MC.get(d0[2], '0'),
            "shio": shio_map.get(shio_idx, "N/A"),
            "macau": f"{shio_map.get(shio_idx)} - {shio_map.get((shio_idx + 6) % 12)}",
            "twin": twin_val,
            "info": f"{strategy} | {'TRIPLE-DETECT' if is_triple else 'NORMAL'}"
        }
    except Exception as e:
        return {"core": "ERR", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}
