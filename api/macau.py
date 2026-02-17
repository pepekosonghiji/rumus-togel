import re
from collections import Counter

# DATABASE LOGIC KHUSUS MACAU (MISTIK & TAYSEN TERKALIBRASI)
ML_MC = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY_MC = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
MB_MC = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
ID_MC = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}

def calculate_macau_prediction(results):
    """
    LOGIC V10.1 SHARP: Macau Velocity & Mirroring.
    Dioptimalkan untuk mencegah Server Error 500.
    """
    try:
        if not results or len(results) < 1:
            return None

        d0 = results[0] # Result terakhir (contoh: 4980)
        
        # --- [1. BBFS VELOCITY ANALYSIS] ---
        # Memindai historis untuk mencari angka yang "berhutang"
        full_history = "".join(results[:20])
        counts = Counter(full_history)
        
        mc_scores = {n: 0 for n in "0123456789"}
        for n in "0123456789":
            # Semakin jarang muncul di 20 putaran, skor semakin tinggi
            mc_scores[n] = 20 - counts.get(n, 0) 
            
            # Bonus skor untuk angka yang absen di 10 putaran terakhir
            for i, res in enumerate(results[:15]):
                if n in res:
                    mc_scores[n] += (i * 2.0)
                    break
        
        # Eliminasi paksa angka dari result terakhir (4980) agar tidak meleset
        for char in d0:
            mc_scores[char] -= 15 

        sorted_mc = sorted(mc_scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_mc[:6]]

        # --- [2. CORE 2D: MACAU MIRRORING] ---
        # Rumus utama: MB(Kop) + TY(Ekor) & ID(As) + ML(Kepala)
        # Contoh 4980: MB(9)=3 + TY(0)=7 -> 37
        primary_2d = MB_MC.get(d0[1], '0') + TY_MC.get(d0[3], '0')
        secondary_2d = ID_MC.get(d0[0], '0') + ML_MC.get(d0[2], '0')
        
        line_2d = [
            primary_2d, 
            secondary_2d,
            "17", "35", "62", "18", "57" # Jalur pelarian abadi M17
        ]
        core_2d = list(dict.fromkeys(line_2d))

        # --- [3. STRUKTUR & SHIO] ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12 

        return {
            "core_2d": ", ".join(core_2d),
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + ID_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + MB_MC.get(d0[2], '0'),
            "shio": shio_map.get(shio_idx, "N/A"),
            "macau_twin": f"{d0[2]}{d0[2]}, {TY_MC.get(d0[3], '0')}{TY_MC.get(d0[3], '0')}"
        }
    except Exception as e:
        print(f"Error in macau logic: {e}")
        return None
