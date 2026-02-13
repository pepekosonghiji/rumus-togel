import os
import json
from flask import Flask, render_template, request, jsonify, session
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter
import re
import random
from itertools import permutations, combinations

# --- IMPORT RUMUS TAMBAHAN ---
try:
    from rumus_1 import hitung_rumus_satu
except ImportError:
    # Fallback jika file rumus_1.py belum dibuat
    def hitung_rumus_satu(m, r): 
        return {"error": "File rumus_1.py tidak ditemukan di server!"}

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026_ULTIMATE")

# --- TABEL REFERENSI ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'CHINA POOLS': 'p2670', 'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615',
    'JAPAN POOLS': 'custom_japan', 'HONGKONG POOLS': 'kia_2',
    'SINGAPORE POOLS': 'kia_3', 'SYDNEY POOLS': 'kia_4'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

# --- CORE UTILITIES ---

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=8.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            if code == 'custom_japan':
                r = client.get("https://tabelupdate.online/data-keluaran-japan/")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
            elif code.startswith('kia_'):
                idx = int(code.split('_')[1])
                r = client.get("https://nomorkiajit.com/hksgpsdy")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 5:
                        val = re.sub(r'\D', '', tds[idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                r = client.get(f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1")
                rows = BeautifulSoup(r.text, 'html.parser').select('table tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
    except: pass
    return results

def generate_2d(bbfs_str):
    digits = list(set(bbfs_str))
    if len(digits) < 2: return ""
    return ", ".join(sorted(["".join(p) for p in permutations(digits, 2)]))

def generate_top_set(bbfs_list, count=2):
    if len(bbfs_list) < 4: return ["-"], ["-"]
    c3 = list(combinations(bbfs_list, 3))
    c4 = list(combinations(bbfs_list, 4))
    return ["".join(x) for x in random.sample(c3, min(count, len(c3)))], \
           ["".join(x) for x in random.sample(c4, min(count, len(c4)))]

# --- ALGORITMA DEFAULT (HYBRID V3) ---

def proses_hybrid_v3(market_key, all_res):
    last_res = all_res[0]
    # Analisis Bobot
    recent = "".join(all_res[:12]); older = "".join(all_res[12:40])
    weights = Counter()
    for d in recent: weights[d] += 3
    for d in older: weights[d] += 1
    
    pool = [x[0] for x in weights.most_common(5)]
    
    # BBFS Utama (Min 5, Max 6)
    bbfs_main_list = pool[:6]
    bbfs_main_str = "".join(bbfs_main_list)
    
    # Shadow (Strict 5 Digit)
    shadow_list = list(dict.fromkeys([TABEL_INDEKS.get(d, d) for d in bbfs_main_list]))[:5]
    bbfs_shadow_str = "".join(shadow_list)

    m3, m4 = generate_top_set(bbfs_main_list)
    s3, s4 = generate_top_set(shadow_list)

    return {
        "market": market_key, "last": last_res, "bbfs": bbfs_main_str, "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d(bbfs_main_str), "list2d_shadow": generate_2d(bbfs_shadow_str),
        "top3d": f"Main: {', '.join(m3)} | Shad: {', '.join(s3)}",
        "top4d": f"Main: {', '.join(m4)} | Shad: {', '.join(s4)}",
        "posisi": f"Kpl: {bbfs_main_list[0]} | Ekr: {bbfs_main_list[1]}"
    }

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized', False))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('key') == "MAMANG2026":
        session.permanent = True
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Access Denied"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    
    market = request.form.get('market')
    rumus_type = request.form.get('rumus_type')
    
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: 
        all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]

    if rumus_type == "rumus_1":
        return jsonify(hitung_rumus_satu(market, all_res))
    else:
        return jsonify(proses_hybrid_v3(market, all_res))

if __name__ == '__main__':
    app.run(debug=True)
