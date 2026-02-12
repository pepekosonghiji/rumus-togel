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

# --- KONFIGURASI ---
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

# Gunakan Proxy/User-Agent yang lebih kuat untuk menghindari blokir
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

# --- CORE SCRAPER WITH FALLBACK ---

def fetch_results(code):
    results = []
    # Kurangi timeout agar tidak kena limit Vercel (maks 10 detik)
    timeout = httpx.Timeout(8.0, connect=3.0) 
    
    try:
        with httpx.Client(timeout=timeout, verify=False, follow_redirects=True, headers=HEADERS) as client:
            if code == 'custom_japan':
                url = "https://tabelupdate.online/data-keluaran-japan/"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.select('tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)

            elif code.startswith('kia_'):
                col_idx = int(code.split('_')[1])
                url = "https://nomorkiajit.com/hksgpsdy"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.select('tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 5:
                        val = re.sub(r'\D', '', tds[col_idx].text.strip())
                        if len(val) == 4: results.append(val)

            else:
                url = f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.select('table tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
    except Exception as e:
        print(f"Fetch failed for {code}: {e}")
    
    return results

# --- ANALISIS ENGINE ---

def generate_2d(bbfs_str):
    digits = list(set(bbfs_str))
    if len(digits) < 2: return ""
    combos = ["".join(p) for p in permutations(digits, 2)]
    return ", ".join(sorted(combos))

def get_statistical_data(all_res):
    if not all_res: return []
    sample = all_res[:40] # Ambil 40 data
    all_digits = "".join(sample)
    
    freq = Counter(all_digits)
    hot = [x[0] for x in freq.most_common(4)]
    
    last_app = {str(i): 99 for i in range(10)}
    for idx, res in enumerate(sample):
        for d in res:
            if last_app[d] == 99: last_app[d] = idx
    
    mid_skip = [d for d, s in last_app.items() if 2 <= s <= 6]
    return list(dict.fromkeys(hot + mid_skip))

def proses_hybrid(market_key):
    code = TARGET_POOLS.get(market_key)
    all_res = fetch_results(code)
    
    if not all_res:
        # Jika scraping gagal total, gunakan angka random berbasis hari (Safety Fallback)
        seed = datetime.now().strftime("%Y%m%d")
        random.seed(seed)
        all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]

    last_res = all_res[0]
    stat_nums = get_statistical_data(all_res)
    
    # Pola Khusus
    if market_key == 'CAMBODIA':
        extra = [TABEL_MISTIK_BARU.get(d, d) for d in last_res]
        am = list(dict.fromkeys(stat_nums + extra))[:7]
    else:
        extra = [TABEL_TAYSEN.get(d, d) for d in last_res[-2:]]
        am = list(dict.fromkeys(stat_nums + extra))[:6]

    # Padding jika kurang
    while len(am) < 5:
        d = random.choice(list(TABEL_INDEKS.values()))
        if d not in am: am.append(d)

    bbfs_main = "".join(am)
    shadow_pool = list(dict.fromkeys([TABEL_MISTIK_BARU.get(d, d) for d in am] + [TABEL_INDEKS.get(d, d) for d in am]))
    bbfs_shadow = "".join(shadow_pool[:6])

    return {
        "market": market_key,
        "last": last_res,
        "bbfs": bbfs_main,
        "shadow": bbfs_shadow,
        "list2d_main": generate_2d(bbfs_main),
        "list2d_shadow": generate_2d(bbfs_shadow),
        "top3d": ", ".join(["".join(random.sample(am, 3)) for _ in range(3)]),
        "top4d": ", ".join(["".join(random.sample(am, 4)) for _ in range(3)]),
        "posisi": f"Kpl: {am[0]} | Ekr: {am[1]}"
    }

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized'))

@app.route('/login', methods=['POST'])
def login():
    key = request.form.get('key')
    valid_keys = get_valid_keys()
    if key in valid_keys:
        session.permanent = True
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Key Salah!"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    res = proses_hybrid(market)
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
