import os
import re
import random
import httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter
from itertools import permutations, combinations
from datetime import timedelta

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# Config
app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026_PREMIUM")
app.permanent_session_lifetime = timedelta(days=1)

# --- DATA REFERENSI ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263','BUSAN POOLS': 'p16063', 'WUHAN': 'p28615',
    'JAPAN POOLS': 'custom_japan', 'HONGKONG POOLS': 'kia_2',
    'SINGAPORE POOLS': 'kia_3', 'SYDNEY POOLS': 'kia_4','OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}

# --- CORE UTILS ---

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=10.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            if code == 'custom_japan':
                r = client.get("https://tabelupdate.online/data-keluaran-japan/")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows[:30]:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
            elif code.startswith('kia_'):
                idx = int(code.split('_')[1])
                r = client.get("https://nomorkiajit.com/hksgpsdy")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows[:30]:
                    tds = row.find_all('td')
                    if len(tds) >= 5:
                        val = re.sub(r'\D', '', tds[idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                r = client.get(f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1")
                rows = BeautifulSoup(r.text, 'html.parser').select('table tbody tr')
                for row in rows[:30]:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
    except: pass
    return results

def get_weighted_stats(all_res):
    if not all_res: return []
    # Analisis Bobot: 12 data terbaru (x3), sisanya (x1)
    recent = "".join(all_res[:12])
    older = "".join(all_res[12:40])
    weights = Counter()
    for d in recent: weights[d] += 3
    for d in older: weights[d] += 1
    
    # Ambil pondasi 5 angka terkuat
    pool = [x[0] for x in weights.most_common(5)]
    
    # Deteksi Prime Gap (Istirahat 4-7 putaran)
    last_seen = {str(i): 99 for i in range(10)}
    for idx, res in enumerate(all_res[:25]):
        for d in res:
            if last_seen[d] == 99: last_seen[d] = idx
    
    prime_gap = [d for d, g in last_seen.items() if 4 <= g <= 7]
    for g in prime_gap:
        if len(pool) < 6 and g not in pool:
            pool.append(g)
            
    while len(pool) < 5:
        r_digit = str(random.randint(0, 9))
        if r_digit not in pool: pool.append(r_digit)
            
    return pool

def generate_2d(bbfs_str):
    digits = list(set(bbfs_str.replace("-", "")))
    if len(digits) < 2: return ""
    return ", ".join(sorted(["".join(p) for p in permutations(digits, 2)]))

def generate_top_set(bbfs_list, count=2):
    if len(bbfs_list) < 4: return ["-"], ["-"]
    c3 = list(combinations(bbfs_list, 3))
    c4 = list(combinations(bbfs_list, 4))
    m3 = ["".join(x) for x in random.sample(c3, min(count, len(c3)))]
    m4 = ["".join(x) for x in random.sample(c4, min(count, len(c4)))]
    return m3, m4

# --- LOGIKA RUMUS (DULU RUMUS_1.PY) ---

def hitung_rumus_satu(market_key, all_res):
    """Logika Rumus 1 yang diintegrasikan"""
    last_res = all_res[0]
    am_base = get_weighted_stats(all_res)
    
    # BBFS Utama (Strict 6 Digit)
    bbfs_main_list = am_base[:6]
    bbfs_main_str = "-".join(bbfs_main_list)
    
    # Shadow BBFS (Indeks + Mistik Baru)
    shadow_list = list(dict.fromkeys([TABEL_INDEKS.get(d, d) for d in bbfs_main_list]))[:5]
    if len(shadow_list) < 5:
        for d in bbfs_main_list:
            mb = TABEL_MISTIK_BARU.get(d, d)
            if mb not in shadow_list: shadow_list.append(mb)
            if len(shadow_list) == 5: break
            
    bbfs_shadow_str = "-".join(shadow_list)
    m3, m4 = generate_top_set(bbfs_main_list)
    s3, s4 = generate_top_set(shadow_list)

    return {
        "market": market_key, "last": last_res, 
        "bbfs": bbfs_main_str, "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d(bbfs_main_str),
        "top3d": f"Main: {', '.join(m3)} | Shad: {', '.join(s3)}",
        "top4d": f"Main: {', '.join(m4)} | Shad: {', '.join(s4)}",
        "posisi": f"Kpl: {bbfs_main_list[0]} | Ekr: {bbfs_main_list[1]}"
    }

# --- ANALYTICS ENGINE HYBRID V3 ---

def proses_hybrid_v3(market_key, all_res):
    last_res = all_res[0]
    am_base = get_weighted_stats(all_res)
    
    if market_key == 'CAMBODIA':
        mb_ekor = TABEL_MISTIK_BARU.get(last_res[-1])
        if mb_ekor not in am_base: am_base.append(mb_ekor)
    
    bbfs_main_list = am_base[:6]
    bbfs_main_str = "".join(bbfs_main_list)
    
    shadow_list = list(dict.fromkeys([TABEL_INDEKS.get(d, d) for d in bbfs_main_list]))[:5]
    bbfs_shadow_str = "".join(shadow_list)

    m3, m4 = generate_top_set(bbfs_main_list)
    s3, s4 = generate_top_set(shadow_list)

    return {
        "market": market_key, "last": last_res, 
        "bbfs": bbfs_main_str, "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d(bbfs_main_str),
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
    if request.form.get('key') == "MAMANG2026":
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Key Salah!"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    
    market = request.form.get('market')
    rumus_type = request.form.get('rumus_type')
    
    code = TARGET_POOLS.get(market)
    all_res = fetch_results(code)
    
    # Fallback jika fetch gagal
    if not all_res:
        all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]

    if rumus_type == "rumus_1":
        return jsonify(hitung_rumus_satu(market, all_res))
    else:
        return jsonify(proses_hybrid_v3(market, all_res))

if __name__ == '__main__':
    app.run(debug=True)
