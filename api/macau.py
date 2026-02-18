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
from datetime import datetime
import pytz

def calculate_macau_prediction(results):
    """
    LOGIC V16.0 - MULTI-SCHEDULE PRECISION (MACAU M17)
    Menyesuaikan algoritma mengikut waktu putaran: 13, 16, 19, 22, 23, 00.
    """
    try:
        if not results or len(results) < 2:
            return {"core": "-", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}

        d0 = str(results[0]).zfill(4)
        
        # --- [1. PENGESAN WAKTU (WIB)] ---
        tz = pytz.timezone('Asia/Jakarta')
        now = datetime.now(tz)
        hour = now.hour

        # --- [2. PENETAPAN STRATEGI MENGIKUT JAM] ---
        # Siang (13, 16): Biasanya angka 'Repeat' atau 'Taysen' kuat.
        # Malam (19, 22, 23, 00): Biasanya 'Mistik' dan 'Indeks' lebih dominan.
        
        limit_history = 30
        weight_repeat = 5 # Default
        
        if hour in [13, 16]:
            strategy = "SIANG_FLOW"
            weight_repeat = 15 # Lebih cenderung ikut angka yang baru keluar
            limit_history = 25
        elif hour in [19, 22, 23]:
            strategy = "MALAM_MISTIK"
            weight_repeat = -10 # Elak angka repeat, cari angka mistik
            limit_history = 40
        else: # Putaran 00:00 atau Subuh
            strategy = "MIDNIGHT_SHADOW"
            weight_repeat = 0
            limit_history = 50

        # --- [3. BBFS SINKRONISASI (TIME-BASED)] ---
        full_history = "".join(results[:limit_history])
        counts = Counter(full_history)
        scores = {n: (limit_history - counts.get(n, 0)) for n in "0123456789"}
        
        for char in d0:
            scores[char] += weight_repeat # Pengaruh strategi jam

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [4. PENAJAMAN SNIPER 2D MENGIKUT SLOT] ---
        
        if strategy == "SIANG_FLOW":
            # Fokus Taysen & Aliran Angka (Contoh: 52 -> Taysen 87)
            p1 = TY_MC.get(d0[2], '0') + TY_MC.get(d0[3], '0')
            p2 = d0[1] + ID_MC.get(d0[3], '0')
            p3 = "28" if "2" in bbfs_final else "54"
        
        elif strategy == "MALAM_MISTIK":
            # Fokus Mistik & Indeks (Contoh: 52 -> ML 25 atau ID 07)
            p1 = ML_MC.get(d0[2], '0') + ML_MC.get(d0[3], '0')
            p2 = ID_MC.get(d0[0], '0') + MB_MC.get(d0[2], '0')
            p3 = TY_MC.get(d0[1], '0') + d0[3]
            
        else: # MIDNIGHT
            p1 = ID_MC.get(d0[0], '9') + TY_MC.get(d0[3], '9')
            p2 = ML_MC.get(d0[1], '3') + MB_MC.get(d0[2], '4')
            p3 = "71" if "7" in bbfs_final else "04"

        p4 = MB_MC.get(d0[3], '0') + ID_MC.get(d0[2], '0')
        core_2d = list(dict.fromkeys([p1, p2, p3, p4, "15", "90"]))
        
        # --- [5. SHIO & TWIN] ---
        shio_idx = int(d0[2:]) % 12
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        
        # Twin Logic: Jam malam lebih kerap keluar twin ganjil
        twin_val = f"{p1[0]}{p1[0]}, {p2[-1]}{p2[-1]}"
        if hour >= 22:
            twin_val = "99, 77, 11"
        elif hour <= 16:
            twin_val = "22, 44, 88"

        return {
            "core": ", ".join(core_2d[:5]),
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + MB_MC.get(d0[1], '0'),
            "kop_kep": TY_MC.get(d0[1], '0') + ML_MC.get(d0[2], '0'),
            "shio": shio_map.get(shio_idx, "N/A"),
            "macau": f"{shio_map.get(shio_idx)} - {shio_map.get((shio_idx + 6) % 12)}",
            "twin": twin_val,
            "info": f"Slot {hour}:00 ({strategy})" # Untuk debug
        }
    except Exception as e:
        return {"core": "ERR", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}
