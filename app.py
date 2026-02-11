from flask import Flask, render_template, request, jsonify
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import re
import random

app = Flask(__name__)

# --- CONFIG & LOGIKA SCRAPING ---
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'SINGAPORE': 'p2664',
    'BUSAN POOLS': 'p16063', 'HONGKONG LOTTO': 'p2263'
}

TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
BASE_URL = 'https://tgr7grldrc.salamrupiah.com/history/result-mobile/'

def get_day_name(offset=0):
    days_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    idx = (datetime.now().weekday() + offset) % 7
    return days_indo[idx]

def get_data_hybrid(server_code, target_day):
    filtered = []
    # Menggunakan httpx Client dengan follow_redirects=True agar tembus ke situs tujuan
    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        for pg in range(1, 6): # Batasi 5 halaman agar tidak terlalu lambat di hosting
            try:
                r = client.get(f"{BASE_URL}{server_code}-pool-1?page={pg}", headers=HEADERS)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if not table: break
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        tgl_text = cols[0].text.strip()
                        if target_day.lower() in tgl_text.lower():
                            val = re.sub(r'\D', '', cols[3].text.strip())
                            if val and len(val) == 4: filtered.append(val)
                if len(filtered) >= 10: break
            except: break
    return filtered

def proses_hybrid(server_key):
    try:
        code = TARGET_POOLS[server_key]
        target_hari = get_day_name()
        
        with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
            raw_res = client.get(f"{BASE_URL}{code}-pool-1", headers=HEADERS).text
        
        soup = BeautifulSoup(raw_res, 'html.parser')
        tbody = soup.find('tbody')
        if not tbody: return None

        all_res = []
        for r in tbody.find_all('tr'):
            tds = r.find_all('td')
            if len(tds) >= 4:
                clean_val = re.sub(r'\D', '', tds[3].text.strip())
                if len(clean_val) == 4: all_res.append(clean_val)
        
        if not all_res: return None
        
        last_res = all_res[0]
        data_historis = get_data_hybrid(code, target_hari)
        
        # Logika Rumus Analisis
        taysen_last = [TABEL_TAYSEN.get(d, '0') for d in last_res[-2:]]
        vortex = [d for d in "0123456789" if d not in "".join(all_res[:5])]
        count_h = Counter("".join(data_historis if data_historis else all_res[:15]))
        historis = [d for d in [x[0] for x in count_h.most_common(5)]]

        # Menggabungkan semua unsur
        am_hybrid = list(dict.fromkeys(taysen_last + historis + vortex))
        
        # Menambah angka Indeks jika kurang dari 6 digit
        while len(am_hybrid) < 6:
            added = False
            for d in list(am_hybrid):
                indeks = TABEL_INDEKS.get(d)
                if indeks and indeks not in am_hybrid: 
                    am_hybrid.append(indeks)
                    added = True
                if len(am_hybrid) >= 6: break
            if not added: # Jika masih kurang, ambil angka random yang belum ada
                for n in "0123456789":
                    if n not in am_hybrid: am_hybrid.append(n)
                    if len(am_hybrid) >= 6: break
            if len(am_hybrid) >= 6: break

        return {
            "market": server_key.upper(),
            "last": last_res,
            "bbfs": "".join(am_hybrid[:6]),
            "shadow": "".join(list(dict.fromkeys([TABEL_MISTIK.get(d, d) for d in am_hybrid[:6]]))[:6]),
            "jitu": f"{am_hybrid[0]}{am_hybrid[1]}, {am_hybrid[2]}{am_hybrid[3]}, {am_hybrid[4]}{am_hybrid[5]}",
            "posisi": f"Kepala {am_hybrid[0]} | Ekor {am_hybrid[1]}"
        }
    except Exception as e:
        print(f"Error Detail: {e}")
        return None

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', markets=TARGET_POOLS.keys())

@app.route('/analyze', methods=['POST'])
def analyze():
    market = request.form.get('market')
    if not market or market not in TARGET_POOLS:
        return jsonify({"error": "Pasaran tidak valid"}), 400
        
    result = proses_hybrid(market)
    if result:
        return jsonify(result)
    return jsonify({"error": "Gagal mengambil data dari server"}), 500

if __name__ == '__main__':
    app.run(debug=True)