import re
from collections import Counter

# --- [DATABASE DATABASE KHUSUS MACAU] ---
# Menggunakan Mistik dan Taysen yang dikalibrasi untuk putaran cepat M17
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}

def calculate_macau_prediction(results):
    """
    LOGIC V10 SHARP: Khusus Macau M17
    Fokus: Menghindari angka result terakhir (4980) dan mencari angka 'hutang'.
    """
    if not results:
        return None

    d0 = results[0]  # Result terakhir: 4980
    
    # --- [1. RUMUS BBFS: GAP VELOCITY] ---
    # Memindai 15 putaran terakhir untuk mencari angka yang sengaja disimpan bandot
    full_history = "".join(results[:15])
    counts = Counter(full_history)
    
    mc_scores = {n: 0 for n in "0123456789"}
    for n in "0123456789":
        # Skor dasar dari frekuensi kemunculan (semakin jarang semakin tinggi skornya)
        mc_scores[n] = 15 - counts.get(n, 0) 
        
        # Penajaman: Cari jarak (gap) terakhir angka itu muncul
        for i, res in enumerate(results[:20]):
            if n in res:
                mc_scores[n] += (i * 2.5) # Bobot 'Hutang' diperberat
                break
    
    # Eliminasi Angka Result Terakhir (4980) agar tidak meleset
    for char in d0:
        mc_scores[char] -= 10 

    sorted_mc = sorted(mc_scores.items(), key=lambda x: x[1], reverse=True)
    bbfs_final = [x[0] for x in sorted_mc[:6]]

    # --- [2. RUMUS CORE 2D: CROSS-MIRROR] ---
    # Pola: Mistik Baru Kop + Taysen Ekor & Indeks As + Kepala
    # Result 4980 -> Kop: 9, Ekor: 0, As: 4, Kepala: 8
    line_2d = [
        MB_MC.get(d0[1]) + TY_MC.get(d0[3]), # 37
        ML_MC.get(d0[2]) + MB_MC.get(d0[0]), # 38
        "17", "35", "62", "18", "57"         # Angka Pelarian Siklus M17
    ]
    
    # Clean up 2D agar unik
    core_2d = list(dict.fromkeys(line_2d))

    # --- [3. AS, KOP, SHIO] ---
    shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
    shio_idx = int(d0[2:]) % 12 # Berdasarkan 2 digit belakang (80)

    return {
        "core_2d": ", ".join(core_2d),
        "bbfs": " ".join(sorted(bbfs_final)),
        "as_kop": MB_MC.get(d0[0]) + ML_MC.get(d0[1]),
        "kop_kep": TY_MC.get(d0[1]) + MB_MC.get(d0[2]),
        "shio": shio_map.get(shio_idx, "N/A"),
        "macau_twin": f"{d0[1]}{d0[1]}, {TY_MC.get(d0[3])}{TY_MC.get(d0[3])}"
    }
