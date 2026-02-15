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

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026_ULTIMATE")
app.permanent_session_lifetime = timedelta(days=1)

# --- DATABASE POLA TERPADU ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
TABEL_ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

# Pola Pelarian Tradisional (Angka Utama: Angka Pelarian)
TABEL_PELARIAN = {
    '01':'95', '02':'35', '03':'85', '04':'05', '05':'40', 
    '06':'51', '07':'57', '08':'04', '09':'33', '10':'18'
}

TABEL_SHIO = {
    "KUDA": ["02", "14", "26", "38", "50", "62", "74", "86", "98"],
    "ULAR": ["03", "15", "27", "39", "51", "63", "75", "87", "99"],
    "NAGA": ["04", "16", "28", "40", "52", "64", "76", "88", "00"],
    "AYAM": ["11", "23", "35", "47", "59", "71", "83", "95"] # Contoh singkat
}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615', 'JAPAN POOLS': 'custom_japan', 
    'HONGKONG POOLS': 'kia_2', 'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4', 'OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# --- CORE ENGINE: TOTAL PATTERN INTEGRATION ---

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

def get_ultimate_5digit(all_res):
    if not all_res: return [str(i) for i in random.sample(range(10), 5)]
    
    last_res = all_res[0]
    kop, kpl, ekr = last_res[1], last_res[2], last_res[3]
    
    # 1. Gabungkan Indeks, MB, ML, dan Taysen dari 2D Belakang
    seeds = set([
        TABEL_INDEKS.get(ekr), TABEL_MB.get(kpl), 
        TABEL_ML.get(ekr), TABEL_TAYSEN.get(ekr)
    ])
    
    # 2. Pola Pelarian (Ambil dari 2D terakhir)
    last_2d = last_res[2:]
    pelarian = TABEL_PELARIAN.get(last_2d, "05") # Default 05 jika tidak ada di tabel
    seeds.add(pelarian[0])
    seeds.add(pelarian[1])
    
    # 3. Statistik Panas (Hot Numbers 10 putaran)
    counts = Counter("".join(all_res[:10]))
    hot = [x[0] for x in counts.most_common(5)]
    
    # 4. Eliminasi Angka Mati (Angka yang keluar di Ekor 2 kali berturut-turut)
    angka_mati = []
    if all_res[0][3] == all_res[1][3]:
        angka_mati.append(all_res[0][3])
        
    # Konstruksi Final
    final_pool = [n for n in list(dict.fromkeys(list(seeds) + hot)) if n not in angka_mati]
    
    # Pastikan 5 Digit
    if len(final_pool) < 5:
        for i in "0123456789":
            if i not in final_pool: final_pool.append(i)
            if len(final_pool) == 5: break
            
    return sorted(final_pool[:5])

def get_macau_shio_ultimate(all_res):
    last_2d = all_res[0][2:]
    # Cari Shio Pelarian
    pola_shio = "KUDA"
    for s, nums in TABEL_SHIO.items():
        if last_2d in nums: pola_shio = s
        
    # Cari Shio Mistik
    mistik_ekr = TABEL_ML.get(all_res[0][3])
    mistik_shio = "NAGA"
    for s, nums in TABEL_SHIO.items():
        if any(n.endswith(mistik_ekr) for n in nums): mistik_shio = s
        
    return f"{pola_shio} x {mistik_shio}"

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
    shio = get_macau_shio_ultimate(all_res)
    
    # Generate 2D dari BBFS
    raw_2d = ["".join(p) for p in permutations(bbfs, 2)]
    
    return jsonify({
        "market": market, "last": all_res[0],
        "bbfs": " ".join(bbfs),
        "shio": shio,
        "list2d": ", ".join(sorted(list(set(raw_2d))[:12])), # Diperketat jadi 12 line
        "posisi": f"KPL: {bbfs[0]} | EKR: {bbfs[-1]}"
    })

@app.route('/analyze-invest', methods=['POST'])
def analyze_invest():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: all_res = ["0000"]*5
    
    # 4-Line Invest berbasis Taysen & ML
    bbfs = get_ultimate_5digit(all_res)
    inv = [bbfs[0]+bbfs[1], bbfs[2]+bbfs[3], bbfs[0]+bbfs[4], bbfs[1]+bbfs[3]]
    return jsonify({"market": market, "invest_2d": inv})

if __name__ == '__main__':
    app.run(debug=True)
