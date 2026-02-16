import httpx
from bs4 import BeautifulSoup
import re
from collections import Counter

# --- [DATABASE MASTER POLA ABADI] ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

def fetch_macau_m17():
    """Scraper Tajam khusus M17 dengan pembersihan Regex"""
    results = []
    url = "https://dk9if7ik34.salamrupiah.com/history/result-mobile/m17-pool-1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        with httpx.Client(timeout=15.0, verify=False, headers=headers) as client:
            r = client.get(url)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table', class_='table-history')
                if table:
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) >= 3:
                            link_data = tds[2].find('a')
                            if link_data:
                                # Membersihkan semua karakter kecuali angka
                                val = re.sub(r'\D', '', link_data.text.strip())
                                if len(val) == 4:
                                    results.append(val)
    except Exception as e:
        print(f"Scraper Error: {e}")
    return results

def calculate_macau_prediction(all_res):
    """Engine Analisa V9.0: Penajaman Berdasarkan Karakter Result"""
    if not all_res: return None
    
    d0 = all_res[0]  # Result Terbaru (contoh: 9711)
    
    # 1. DETEKSI TWIN & SHIFTING LOGIC
    is_twin_belakang = d0[2] == d0[3]
    is_twin_depan = d0[0] == d0[1]
    
    # 2. PENAJAMAN BBFS (Weighting 3-Layer)
    # Layer 1: Frekuensi Global (42 putaran)
    # Layer 2: Frekuensi Harian (6 putaran)
    # Layer 3: Mistik/Taysen dari Result Terakhir
    all_digits = "".join(all_res[:42])
    recent_digits = "".join(all_res[:6])
    
    scores = {str(i): 0 for i in range(10)}
    for n in all_digits: scores[n] += 1
    for n in recent_digits: scores[n] += 3 # Angka panas hari ini
    
    # Tambahkan angka pelarian jika result twin
    if is_twin_belakang:
        escape_digit = TY.get(d0[3], '0')
        scores[escape_digit] += 10 # Prioritas angka taysen dari twin
        
    bbfs = sorted(scores, key=scores.get, reverse=True)[:6]

    # 3. PENAJAMAN CORE 2D JITU
    if is_twin_belakang:
        # Pola jika result terakhir twin (seperti 11)
        # Ambil Mistik Baru As + Taysen Ekor
        # Ambil Index Kop + Mistik Lama Kepala
        line = [
            MB.get(d0[0], '0') + TY.get(d0[3], '0'),
            ID.get(d0[1], '0') + ML.get(d0[2], '0'),
            TY.get(d0[2], '0') + MB.get(d0[3], '0')
        ]
    else:
        # Pola Standar Tajam
        line = [
            TY.get(d0[2], '0') + d0[3],
            ML.get(d0[2], '0') + ID.get(d0[3], '0'),
            MB.get(d0[0], '0') + d0[3]
        ]
    
    # 4. SHIO & MACAU (Berdasarkan 2D Belakang)
    shio_idx = int(d0[2:]) % 12
    shio_main = SHIO_MAP.get(shio_idx, "N/A")
    shio_off = SHIO_MAP.get((shio_idx + 6) % 12, "N/A")

    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": shio_main,
        "macau": f"{shio_main} - {shio_off}",
        "twin": f"{ML.get(d0[2])}{ML.get(d0[2])}, {TY.get(d0[3])}{TY.get(d0[3])}"
    }
