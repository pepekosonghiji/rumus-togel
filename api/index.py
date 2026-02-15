import os
import re
import random
import httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter
from itertools import permutations
from datetime import timedelta

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026_ULTIMATE_V38")
app.permanent_session_lifetime = timedelta(days=1)

# --- DATABASE POLA TERPADU ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
TABEL_ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
TABEL_PELARIAN = {'01':'95', '02':'35', '03':'85', '04':'05', '05':'40', '06':'51', '07':'57', '08':'04', '09':'33', '10':'18'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615', 'JAPAN POOLS': 'custom_japan', 
    'HONGKONG POOLS': 'kia_2', 'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4', 'OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# --- CORE LOGIC ---

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            if code == 'custom_japan':
                r = client.get("https://tabelupdate.online/data-keluaran-japan/")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows[:20]:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
            elif code.startswith('kia_'):
                idx = int(code.split('_')[1])
                r = client.get("https://nomorkiajit.com/hksgpsdy")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows[:20]:
                    tds = row.find_all('td')
                    if len(tds) >= 5:
                        val = re.sub(r'\D', '', tds[idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                r = client.get(f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1")
                rows = BeautifulSoup(r.text, 'html.parser').select('table tbody tr')
                for row in rows[:20]:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
    except: pass
    return results

def detect_twin_probability(all_res):
    if not all_res: return False, []
    has_twin = any(r[2] == r[3] for r in all_res[:10])
    if not has_twin:
        # Rekomendasi 2 pasang twin terkuat dari Hot Number
        hot = Counter("".join(all_res[:10])).most_common(2)
        return True, [x[0]+x[0] for x in hot]
    return False, []

def get_ultimate_5digit(all_res):
    if not all_res: return [str(i) for i in random.sample(range(10), 5)]
    last_res = all_res[0]
    # Gabungan pola matematis
    seeds = {TABEL_INDEKS.get(last_res[3]), TABEL_MB.get(last_res[2]), 
             TABEL_ML.get(last_res[3]), TABEL_TAYSEN.get(last_res[3])}
    # Tambah pelarian
    p = TABEL_PELARIAN.get(last_res[2:], "05")
    seeds.update([p[0], p[1]])
    # Statistik Hot
    hot = [x[0] for x in Counter("".join(all_res[:15])).most_common(5)]
    final = list(dict.fromkeys(list(seeds) + hot))
    # Eliminasi Angka Mati (Ekor beruntun)
    if all_res[0][3] == all_res[1][3]:
        final = [n for n in final if n != all_res[0][3]]
    while len(final) < 5:
        for i in "0123456789":
            if i not in final: final.append(i)
            if len(final) == 5: break
    return sorted(final[:5])

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('key') == "MAMANG2026":
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: all_res = ["0000"]*5
    bbfs = get_ultimate_5digit(all_res)
    is_twin, twins = detect_twin_probability(all_res)
    raw_2d = ["".join(p) for p in permutations(bbfs, 2)]
    return jsonify({
        "market": market, "last": all_res[0], "bbfs": " ".join(bbfs),
        "twin_needed": is_twin, "twin_list": ", ".join(twins),
        "list2d": ", ".join(sorted(list(set(raw_2d))[:12]))
    })

@app.route('/analyze-invest', methods=['POST'])
def analyze_invest():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: all_res = ["0000"]*5
    bbfs = get_ultimate_5digit(all_res)
    # Invest 4-Line murni
    inv = [bbfs[0]+bbfs[4], bbfs[1]+bbfs[3], bbfs[2]+bbfs[0], bbfs[3]+bbfs[2]]
    return jsonify({"market": market, "invest_2d": inv})

if __name__ == '__main__':
    app.run(debug=True)
