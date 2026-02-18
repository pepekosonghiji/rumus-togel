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
    LOGIC V13.0 - ULTRA PRECISION 2D FOCUS (MACAU M17)
    Fokus utama: Membedah pola 2D menggunakan Taysen Berantai dan Index Selisih.
    """
    try:
        if not results or len(results) < 2:
            return {"core": "-", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}

        # Result Terakhir: 9452 (d0), 6449 (d1)
        d0 = str(results[0]).zfill(4)
        d1 = str(results[1]).zfill(4)
        
        # --- [PROSES BBFS - TETAP STABIL] ---
        full_history = "".join(results[:40])
        counts = Counter(full_history)
        scores = {n: (40 - counts.get(n, 0)) for n in "0123456789"}
        for char in d0: scores[char] -= 60
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        bbfs_final = [x[0] for x in sorted_scores[:6]]

        # --- [PROSES PENAJAMAN 2D - FOKUS UTAMA] ---
        # Rumus 1: Pola Taysen Berantai (EKOR d0 -> Taysen -> Index)
        # Result 3939 (Ekor 9) -> Taysen 2 -> Index 7. Maka angka 27/72 kuat.
        ekor_d0 = d0[3]
        taysen_ekor = TY_MC.get(ekor_d0, '0')
        p1 = taysen_ekor + ID_MC.get(taysen_ekor, '0')

        # Rumus 2: Pola Selisih Mistis (AS d0 - KEPALA d0)
        # Mencari angka tengah yang sering muncul sebagai 'Jembatan'
        as_val = int(d0[0])
        kep_val = int(d0[2])
        selisih = str(abs(as_val - kep_val))
        p2 = MB_MC.get(selisih, '0') + TY_MC.get(d0[1], '0')

        # Rumus 3: Pola Indeks Silang (KEPALA d0 + EKOR d1)
        # Menangkap pola result 3939 yang sering mengambil indeks dari result sebelumnya
        p3 = ID_MC.get(d0[2], '0') + ID_MC.get(d1[3], '0')

        # Rumus 4: Angka "Hutang" Terkuat (Top 2 BBFS)
        p4 = bbfs_final[0] + bbfs_final[1]

        # Gabungkan dan Hilangkan Duplikat
        core_2d = list(dict.fromkeys([p1, p2, p3, p4]))
        
        # --- [SHIO & MACAU - TETAP SYNC UI] ---
        shio_map = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}
        shio_idx = int(d0[2:]) % 12
        shio_name = shio_map.get(shio_idx, "N/A")
        macau_val = f"{shio_name} - {shio_map.get((shio_idx + 6) % 12, 'N/A')}"

        # --- [TWIN SHARPENING] ---
        # Twin fokus pada angka taysen dari EKOR terakhir (antisipasi twin silang)
        tw_1 = taysen_ekor + taysen_ekor
        tw_2 = bbfs_final[0] + bbfs_final[0]

        return {
            "core": ", ".join(core_2d[:4]), # Menampilkan 4 line 2D paling tajam
            "bbfs": " ".join(sorted(bbfs_final)),
            "as_kop": ID_MC.get(d0[0], '0') + ID_MC.get(d0[1], '0'),
            "kop_kep": ML_MC.get(d0[1], '0') + MB_MC.get(d0[2], '0'),
            "shio": shio_name,
            "macau": macau_val,
            "twin": f"{tw_1}, {tw_2}"
        }
    except Exception as e:
        return {"core": "ERR LOGIC", "bbfs": "-", "as_kop": "00", "kop_kep": "00", "shio": "-", "macau": "-", "twin": "-"}
