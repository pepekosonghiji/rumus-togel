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
    LOGIC V14.0 - ULTRA PRECISION (MACAU M17)
    Fokus: Penajaman 2D Sniper & Sinkronisasi BBFS Anti-Bandot.
    Update: Transisi Ganjil ke Genap setelah Result 5319.
    """
    try:
        if not results or len(results) < 2:
            return {
                "core": "-", "bbfs": "-", "as_kop": "00", 
                "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"
            }

        # d0: 5319 (Result Terakhir), d1: 9950 (Result Sebelumnya)
        d0 = str(results[0]).zfill(4)
        d1 = str(results[1]).zfill(4)
        
        # --- [1. BBFS SINKRONISASI V14.0] ---
        # Menggunakan teknik 'Inversion Weighting' (Memburu angka yang jatuh tempo)
        full_history = "".join(results[:45])
        counts = Counter(full_history)
        
        # Beri nilai tinggi pada angka yang jarang muncul (Hutang)
        # Tapi kurangi nilai angka yang baru saja keluar (5,3,1,9) agar tidak repeat
        scores = {n: (45 - counts.get(n, 0)) for n in "0123456789"}
        for char in d0: scores[char] -= 50 # Anti-Repeat Filter
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [2. PENAJAMAN SNIPER 2D (CORE)] ---
        
        # Jalur A: Taysen Berantai (Ekor d0 -> Taysen -> Index)
        # Ekor 9 -> Taysen 2 -> Index 7. Maka 27/72 kuat.
        t_ekor = TY_MC.get(d0[3], '2')
        p1 = t_ekor + ID_MC.get(t_ekor, '7')

        # Jalur B: Mistik Rebound (Kepala d0 -> Mistik Baru + Kop d0 -> Taysen)
        # Kepala 1 -> MB 7, Kop 3 -> TY 6. Maka 76 kuat.
        p2 = MB_MC.get(d0[2], '7') + TY_MC.get(d0[1], '6')

        # Jalur C: Shadow AS-KOP (AS d0 -> Index + Ekor d0 -> Mistik Lama)
        # AS 5 -> ID 0, Ekor 9 -> ML 6. Maka 06 kuat.
        p3 = ID_MC.get(d0[0], '0') + ML_MC.get(d0[3], '6')

        # Jalur D: Pola Rebound Ekor (Ekor d0 - 1 & Ekor d0 + 1)
        # Mengincar angka 8 atau 0 jika ekor sebelumnya 9.
        p4 = "58" if "8" in bbfs_final else "50"

        # Gabungkan semua sniper, prioritaskan p1 dan p2
        core_2d = list(dict.fromkeys([p1, p2, p3, p4, "72", "06"]))
        
        # --- [3. DATA TAMBAHAN (SHIO & TWIN)] ---
        shio_map = {
            10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 
            3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 
            8:"NAGA", 9:"ULAR"
        }
        # Hitungan Shio berdasarkan 2D belakang
        shio_idx = int(d0[2:]) % 12
        shio_name = shio_map.get(shio_idx, "N/A")
        macau_val = f"{shio_name} - {shio_map.get((
