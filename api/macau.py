import re, httpx
from bs4 import BeautifulSoup
from collections import Counter

# DATABASE MASTER (Tetap dipertahankan agar rumus sinkron)
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

def fetch_macau_data():
    results = []
    url = "https://dk9if7ik34.salamrupiah.com/history/result-mobile/m17-pool-1"
    try:
        with httpx.Client(timeout=15.0, verify=False) as client:
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', class_='table-history')
            if table:
                for row in table.find('tbody').find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        # SCRAPER KHUSUS: Mengambil angka di dalam tag <a> sesuai respon HTML Bos
                        link_data = tds[2].find('a')
                        if link_data:
                            val = link_data.text.strip()
                            if val.isdigit() and len(val) == 4:
                                results.append(val)
    except: pass
    return results

def get_macau_logic(all_res):
    d0 = all_res[0]
    # Analisa BBFS 6 Putaran Sehari
    limit = 42 
    counts = Counter("".join(all_res[:limit]))
    scores = {n: counts.get(n, 0) + (Counter("".join(all_res[:6])).get(n, 0) * 4) for n in "0123456789"}
    bbfs = [x[0] for x in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:6]]
    
    line = [TY.get(d0[2], '0')+d0[3], ML.get(d0[2], '0')+ID.get(d0[3], '0'), MB.get(d0[0], '0')+d0[3]]
    shio_idx = int(d0[2:]) % 12
    
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 6) % 12)}",
        "twin": f"{d0[2]}{d0[2]}, {d0[3]}{d0[3]}"
    }
