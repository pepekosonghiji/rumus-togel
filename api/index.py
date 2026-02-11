import os
import json
from flask import Flask, render_template, request, jsonify, session
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import re

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# Mengambil Secret Key dari environment Vercel
app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026")

# --- DATABASE KEY AMAN ---
def get_valid_keys():
    try:
        keys_raw = os.environ.get("LIST_KEYS", "{}")
        return json.loads(keys_raw)
    except:
        return {}

# --- LOGIKA SCRAPING & TABEL ---
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'SINGAPORE': 'p2664',
    'BUSAN POOLS': 'p16063', 'HONGKONG LOTTO': 'p2263'
}

# Kamus Data Tambahan untuk Akurasi
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_LAMA = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
BASE_URL = 'https://tgr7grldrc.salamrupiah.com/history/result-mobile/'

def get_day_name():
    days_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    return days_indo[datetime.now().weekday()]

def get_data_hybrid(server_code, target_day):
    filtered = []
    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        for pg in range(1, 4):
            try:
                r = client.get(f"{BASE_URL}{server_code}-pool-1?page={pg}", headers=HEADERS)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.find('table').find('tbody').find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        if target_day.lower() in cols[0].text.strip().lower():
                            val = re.sub(r'\D', '', cols[3].text.strip())
                            if len(val) == 4: filtered.append(val)
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
        all_res = [re.sub(r'\D', '', r.find_all('td')[3].text.strip()) for r in soup.find('tbody').find_all('tr') if len(re.sub(r'\D', '', r.find_all('td')[3].text.strip())) == 4]
        
        if not all_res: return None
        
        last_res = all_res[0] # Contoh: 1234
        
        # 1. POLA BBFS DASAR (Taysen + Historis + Vortex)
        taysen_last = [TABEL_TAYSEN.get(d, '0') for d in last_res[-2:]]
        vortex = [d for d in "0123456789" if d not in "".join(all_res[:5])]
        
        data_historis = get_data_hybrid(code, target_hari)
        count_h = Counter("".join(data_historis if data_historis else all_res[:15]))
        historis = [x[0] for x in count_h.most_common(5)]
        
        am_hybrid = list(dict.fromkeys(taysen_last + historis + vortex))
        
        # Tambal jika kurang dari 7 digit untuk BBFS
        while len(am_hybrid) < 7:
            for n in "0123456789":
                if n not in am_hybrid: 
                    am_hybrid.append(n)
                    if len(am_hybrid) >= 7: break

        # 2. POLA BBFS SHADOW (Mistik Lama & Baru)
        # Mengambil 6 digit dominan dari hasil mistik campuran
        shadow_pool = []
        for d in am_hybrid[:6]:
            shadow_pool.append(TABEL_MISTIK_LAMA.get(d, d))
            shadow_pool.append(TABEL_MISTIK_BARU.get(d, d))
        shadow_final = list(dict.fromkeys(shadow_pool))[:6]

        # 3. POLA ANGKA LARIAN (Berdasarkan Selisih Digit Terakhir)
        # Mengambil pola pergerakan angka dari result terakhir
        d3, d4 = int(last_res[2]), int(last_res[3])
        selisih = str(abs(d3 - d4))
        larian = list(dict.fromkeys([selisih, TABEL_INDEKS.get(selisih, '0'), TABEL_TAYSEN.get(selisih, '0')]))
        angka_larian = "".join(larian + am_hybrid[:2])[:5]

        return {
            "market": server_key.upper(),
            "last": last_res,
            "bbfs": "".join(am_hybrid[:7]),
            "shadow": "".join(shadow_final),
            "larian": angka_larian,
            "jitu": f"{am_hybrid[0]}{am_hybrid[1]}, {am_hybrid[2]}{am_hybrid[3]}, {am_hybrid[4]}{am_hybrid[5]}",
            "posisi": f"Kepala {am_hybrid[0]} | Ekor {am_hybrid[1]}"
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', markets=TARGET_POOLS.keys(), logged_in=session.get('authorized'))

@app.route('/login', methods=['POST'])
def login():
    key = request.form.get('key')
    valid_keys = get_valid_keys()
    
    if key in valid_keys:
        exp_date = datetime.strptime(valid_keys[key], '%Y-%m-%d')
        if datetime.now() <= exp_date:
            session.permanent = True
            session['authorized'] = True
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Lisensi Kedaluwarsa!"}), 403
    return jsonify({"status": "error", "message": "Key Tidak Valid!"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'):
        return jsonify({"error": "Sesi berakhir"}), 403
    market = request.form.get('market')
    result = proses_hybrid(market)
    return jsonify(result) if result else jsonify({"error": "Gagal mengambil data"}), 500

if __name__ == '__main__':
    app.run(debug=True)
