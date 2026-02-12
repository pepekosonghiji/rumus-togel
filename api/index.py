import os
import json
from flask import Flask, render_template, request, jsonify, session
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import Counter
import re
import random
from itertools import permutations

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026")

# --- DATABASE KEY ---
def get_valid_keys():
    try:
        keys_raw = os.environ.get("LIST_KEYS", "{}")
        return json.loads(keys_raw)
    except:
        return {}

# --- KONFIGURASI & TABEL ---
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 
    'SYDNEY LOTTO': 'p2262', 
    'HONGKONG LOTTO': 'p2263', 
    'CHINA POOLS': 'p2670',
    'CHINA LOTTO': 'p2670',
    'BUSAN POOLS': 'p16063', 
    'WUHAN': 'p28615',
    'SEOUL': 'p28502', 
    'OSAKA': 'p28422', 
    'toto macau 4d': 'm17',
    'JAPAN POOLS': 'custom_japan',
    'HONGKONG POOLS': 'kia_2',
    'SINGAPORE POOLS': 'kia_3',
    'SYDNEY POOLS': 'kia_4'
}

JAPAN_URL = "https://tabelupdate.online/data-keluaran-japan/"
KIAJIT_URL = "https://nomorkiajit.com/hksgpsdy"
BASE_URL = 'https://tgr7grldrc.salamrupiah.com/history/result-mobile/'

TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_LAMA = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# --- CORE SCRAPER ENGINE ---

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=30, verify=False, follow_redirects=True) as client:
            if code == 'custom_japan':
                r = client.get(JAPAN_URL, headers=HEADERS)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.find('tbody').find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        val = re.sub(r'\D', '', cols[3].text.strip())
                        if len(val) == 4: results.append(val)
            elif code.startswith('kia_'):
                col_idx = int(code.split('_')[1])
                r = client.get(KIAJIT_URL, headers=HEADERS)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.find('tbody').find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        val = re.sub(r'\D', '', cols[col_idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                r = client.get(f"{BASE_URL}{code}-pool-1", headers=HEADERS)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if table:
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 4:
                            val = re.sub(r'\D', '', cols[3].text.strip())
                            if len(val) == 4: results.append(val)
    except Exception as e:
        print(f"Scraping Error: {e}")
    return results

# --- ANALISIS KHUSUS & GENERATOR ---

def generate_2d(bbfs_str):
    """Menghasilkan daftar 2D Full dari angka BBFS"""
    digits = list(set(bbfs_str))
    combos = ["".join(p) for p in permutations(digits, 2)]
    return ", ".join(sorted(combos))

def pola_khusus_cambodia(last_res, stat_numbers):
    mistik_baru = [TABEL_MISTIK_BARU.get(d, d) for d in last_res]
    indeks_val = [TABEL_INDEKS.get(d, d) for d in last_res[-2:]]
    combined = list(dict.fromkeys(stat_numbers + mistik_baru + indeks_val))
    return combined[:7]

def get_statistical_data(server_code):
    all_res = fetch_results(server_code)
    if not all_res: return []
    sample_data = all_res[:50]
    all_digits = "".join(sample_data)
    
    freq = Counter(all_digits)
    hot_numbers = [x[0] for x in freq.most_common(4)]
    
    last_appearance = {str(i): 99 for i in range(10)}
    for idx, res in enumerate(sample_data):
        for d in res:
            if last_appearance[d] == 99:
                last_appearance[d] = idx
    mid_skip = [d for d, skip in last_appearance.items() if 3 <= skip <= 7]

    correlation_numbers = []
    if len(sample_data) > 14:
        correlation_numbers = list(set(sample_data[7] + sample_data[14]))

    return list(dict.fromkeys(hot_numbers + mid_skip + correlation_numbers))

def proses_hybrid(server_key):
    try:
        code = TARGET_POOLS[server_key]
        all_res = fetch_results(code)
        if not all_res: return None
        last_res = all_res[0]

        stat_numbers = get_statistical_data(code)
        
        if server_key == 'CAMBODIA':
            am_hybrid = pola_khusus_cambodia(last_res, stat_numbers)
        else:
            taysen_ref = [TABEL_TAYSEN.get(d, '0') for d in last_res[-2:]]
            combined = list(dict.fromkeys(stat_numbers + taysen_ref))
            am_hybrid = combined[:6]
        
        if len(am_hybrid) < 5:
            for d in list(am_hybrid):
                idx_v = TABEL_INDEKS.get(d)
                if idx_v not in am_hybrid: am_hybrid.append(idx_v)
                if len(am_hybrid) >= 6: break

        bbfs_main = "".join(am_hybrid)
        
        # Shadow BBFS Logic
        shadow_pool = []
        for d in am_hybrid:
            shadow_pool.append(TABEL_MISTIK_BARU.get(d, d))
            shadow_pool.append(TABEL_INDEKS.get(d, d))
        bbfs_shadow = "".join(list(dict.fromkeys(shadow_pool))[:6])

        # Generate 2D Lists
        list_2d_main = generate_2d(bbfs_main)
        list_2d_shadow = generate_2d(bbfs_shadow)

        top_3d = [ "".join(random.sample(am_hybrid, 3)) for _ in range(3) ]
        top_4d = [ "".join(random.sample(am_hybrid, 4)) for _ in range(3) ]

        return {
            "market": server_key.upper(),
            "last": last_res,
            "bbfs": bbfs_main,
            "shadow": bbfs_shadow,
            "list2d_main": list_2d_main,
            "list2d_shadow": list_2d_shadow,
            "jitu": f"{am_hybrid[0]}{am_hybrid[1]}, {am_hybrid[2]}{am_hybrid[3]}",
            "top3d": ", ".join(top_3d),
            "top4d": ", ".join(top_4d),
            "posisi": f"Kpl: {am_hybrid[0]} | Ekr: {am_hybrid[1]}"
        }
    except Exception as e:
        print(f"Hybrid Error: {e}")
        return None

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized'))

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
    return jsonify({"status": "error", "message": "Invalid/Expired Key!"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    result = proses_hybrid(market)
    return jsonify(result) if result else jsonify({"error": "Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
