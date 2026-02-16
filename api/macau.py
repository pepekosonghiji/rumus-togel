import httpx
from bs4 import BeautifulSoup
import re
from collections import Counter

# RUMUS ABADI MAMANG AI
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

def fetch_macau_m17():
    """Mengambil data dari link m17 dengan penanganan khusus tag <a>"""
    results = []
    # URL ini disesuaikan dengan pola m17-pool-1
    url = "https://dk9if7ik34.salamrupiah.com/history/result-mobile/m17-pool-1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }

    try:
        # Gunakan httpx dengan verify=False untuk bypass SSL jika perlu
        with httpx.Client(timeout=15.0, verify=False, headers=headers) as client:
            response = client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Mencari tabel sesuai HTML Bos
                table = soup.find('table', class_='table-history')
                if table:
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) >= 3:
                            # Mengambil angka di dalam link <a>
                            link_tag = tds[2].find('a')
                            if link_tag:
                                clean_val = re.sub(r'\D', '', link_tag.text.strip())
                                if len(clean_val) == 4:
                                    results.append(clean_val)
    except Exception as e:
        print(f"Error Scraper Macau: {e}")
        
    return results

def calculate_macau_prediction(all_res):
    if not all_res: return None
    
    d0 = all_res[0] # Result Terakhir (misal: 3382)
    
    # POLA BBFS (6 Putaran Sehari)
    # Kita ambil 42 data (1 minggu) untuk mencari frekuensi
    all_digits = "".join(all_res[:42])
    recent_digits = "".join(all_res[:6]) # Data hari ini
    
    freq = Counter(all_digits)
    # Tambahkan bonus untuk angka yang sering muncul di 6 putaran terakhir
    scores = {str(i): freq.get(str(i), 0) + (Counter(recent_digits).get(str(i), 0) * 3) for i in range(10)}
    bbfs = sorted(scores, key=scores.get, reverse=True)[:6]
    
    # RUMUS JITU 2D (Berdasarkan Result Terakhir)
    # Posisi d0: [0]=As, [1]=Kop, [2]=Kepala, [3]=Ekor
    jitu_1 = TY.get(d0[2], '0') + d0[3]             # Taysen Kepala + Ekor Asli
    jitu_2 = ML.get(d0[2], '0') + ID.get(d0[3], '0') # Mistik Lama Kep + Index Ekor
    jitu_3 = MB.get(d0[0], '0') + d0[3]             # Mistik Baru As + Ekor Asli
    
    core_2d = list(dict.fromkeys([jitu_1, jitu_2, jitu_3]))
    
    shio_idx = int(d0[2:]) % 12
    
    return {
        "core": ", ".join(core_2d),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 6) % 12)}",
        "twin": f"{d0[2]}{d0[2]}, {d0[3]}{d0[3]}"
    }
