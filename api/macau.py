import re
from collections import Counter

# --- [DATABASE MASTER POLA KHUSUS MACAU] ---
# Dikalibrasi untuk ritme cepat pasaran M17
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

def fetch_macau_m17():
    """Fungsi placeholder untuk kompatibilitas import di index.py"""
    return []

def calculate_macau_prediction(results):
    """
    LOGIC V10.2: MACAU VELOCITY & ANTI-CRASH SYSTEM.
    Fokus: Mengunci BBFS angka 'Hutang' dan mencegah Error 500.
    """
    try:
        # Validasi Data Awal agar tidak 500 Error
        if not results or len(results) < 1:
            return {
                "core_2d": "MENUNGGU DATA", "bbfs": "N/A", "as_kop": "00", 
                "kop_kep": "00", "shio": "N/A", "macau_twin": "N/A"
            }

        # Standarisasi Result (Memastikan 4 Digit)
        d0 = str(results[0]).zfill(4)
        
        # --- [1. ANALISA BBFS: VELOCITY GAP] ---
        # Melacak angka yang paling lama absen dalam 20 putaran terakhir
        full_history = "".join(map(str, results[:20]))
        counts = Counter(full_history)
        
        mc_scores = {n: 0 for n in "0123456789"}
        for n in "0123456789":
            # Semakin jarang muncul, semakin tinggi skor hutangnya
            mc_scores[n] = 20 - counts.get(n, 0) 
            
            # Tambahan bobot jika angka tersebut absen di 10 putaran terakhir
            for i, res in enumerate(results[:15]):
                if n in str(res):
                    mc_scores[n] += (i * 2.5) 
                    break
        
        # Filter: Kurangi skor angka yang baru saja keluar (Contoh: 4, 9, 8, 0)
        for char in d0:
            mc_scores[char] -= 15 

        # Urutkan berdasarkan skor tertinggi untuk BBFS 6 Digit
        sorted_mc = sorted(mc_scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_mc[:6]]

        # --- [2. RUMUS CORE 2D: MACAU MIRRORING] ---
        # Menggunakan kombinasi Mistik Baru Kop dan Taysen Ekor
        primary_2d = MB_MC.get(d0[1], '0') + TY_MC.get(d0[3], '0')
        secondary_2d = ID_MC.get(d0[0], '0') + ML_MC.get(d0[2], '0')
        
        line_2d = [
            primary_2d, 
            secondary_2d,
            "17", "35", "62", "18", "57" # Jalur cadangan abadi Macau
        ]
        
        # --- [3. PENETAPAN SHIO & TWIN] ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        # Hitungan Shio berdasarkan 2 digit belakang
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
        # Fallback agar server tidak crash 500 jika terjadi kesalahan tak terduga
        return {
            "core_2d": "ERROR", "bbfs": "ERROR", "as_kop": "00", 
            "kop_kep": "00", "shio": "N/A", "macau_twin": "00"
        }
