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

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026")

# --- TABEL REFERENSI ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'CHINA POOLS': 'p2670', 'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615',
    'JAPAN POOLS': 'custom_japan', 'HONGKONG POOLS': 'kia_2',
    'SINGAPORE POOLS': 'kia_3', 'SYDNEY POOLS': 'kia_4'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

# --- CORE ENGINE ---

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

def get_weighted_stats(all_res):
    if not all_res: return []
    # Analisis Bobot: 10 data terbaru (x3), 30 data lama (x1)
    recent = "".join(all_res[:10])
    older = "".join(all_res[10:40])
    weights = Counter()
    for d in recent: weights[d] += 3
    for d in older: weights[d] += 1
    hot_weighted = [x[0] for x in weights.most_common(4)]
    
    # Deteksi Prime Gap (Skip 3-5 hari)
    last_seen = {str(i): 99 for i in range(10)}
    for idx, res in enumerate(all_res[:20]):
        for d in res:
            if last_seen[d] == 99: last_seen[d] = idx
    prime_gap = [d for d, gap in last_seen.items() if 3 <= gap <= 5]
    
    return list(dict.fromkeys(hot_weighted + prime_gap))[:6]

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

def proses_hybrid_v3(market_key):
    code = TARGET_POOLS.get(market_key)
    all_res = fetch_results(code)
    if not all_res: 
        all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]
    
    last_res = all_res[0]
    am_base = get_weighted_stats(all_res) # Kerucutkan ke maksimal 6 digit
    
    if market_key == 'CAMBODIA':
        mb_ekor = TABEL_MISTIK_BARU.get(last_res[-1])
        if mb_ekor not in am_base: am_base.append(mb_ekor)
    
    bbfs_main_list = am_base[:6]
    bbfs_main_str = "".join(bbfs_main_list)
    
    # Shadow BBFS (Pola Indeks - 5 Digit)
    shadow_list = list(dict.fromkeys([TABEL_INDEKS.get(d, d) for d in bbfs_main_list]))[:5]
    bbfs_shadow_str = "".join(shadow_list)

    # Generate TOP Sets
    m3, m4 = generate_top_set(bbfs_main_list)
    s3, s4 = generate_top_set(shadow_list)

    return {
        "market": market_key,
        "last": last_res,
        "bbfs": bbfs_main_str,
        "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d(bbfs_main_str),
        "list2d_shadow": generate_2d(bbfs_shadow_str),
        "top3d": f"Main: {', '.join(m3)} | Shad: {', '.join(s3)}",
        "top4d": f"Main: {', '.join(m4)} | Shad: {', '.join(s4)}",
        "posisi": f"Kpl: {bbfs_main_list[0]} | Ekr: {bbfs_main_list[1]}"
    }

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('key') == "MAMANG2026": # Contoh key sederhana
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Key Salah!"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    return jsonify(proses_hybrid_v3(request.form.get('market')))

if __name__ == '__main__':
    app.run(debug=True)
