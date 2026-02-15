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

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026_ULTRA")
app.permanent_session_lifetime = timedelta(days=1)

# --- DATABASE REFERENSI KOMPLIT ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
TABEL_MISTIK_LAMA = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

# DATA SHIO 2026 (Urutan mengikuti kalender Lunar 2026)
TABEL_SHIO = {
    "KUDA": ["02", "14", "26", "38", "50", "62", "74", "86", "98"],
    "ULAR": ["03", "15", "27", "39", "51", "63", "75", "87", "99"],
    "NAGA": ["04", "16", "28", "40", "52", "64", "76", "88", "00"],
    "KELINCI": ["05", "17", "29", "41", "53", "65", "77", "89"],
    "HARIMAU": ["06", "18", "30", "42", "54", "66", "78", "90"],
    "KERBAU": ["07", "19", "31", "43", "55", "67", "79", "91"],
    "TIKUS": ["08", "20", "32", "44", "56", "68", "80", "92"],
    "BABI": ["09", "21", "33", "45", "57", "69", "81", "93"],
    "ANJING": ["10", "22", "34", "46", "58", "70", "82", "94"],
    "AYAM": ["11", "23", "35", "47", "59", "71", "83", "95"],
    "MONYET": ["12", "24", "36", "48", "60", "72", "84", "96"],
    "KAMBING": ["01", "13", "25", "37", "49", "61", "73", "85", "97"]
}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615', 'JAPAN POOLS': 'custom_japan', 
    'HONGKONG POOLS': 'kia_2', 'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4', 'OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# --- CORE ENGINE ---

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

def get_ultra_sync_5digit(all_res):
    if not all_res: return [str(i) for i in random.sample(range(10), 5)]
    
    # Gabungkan Hot Nums + Mistik Lama + Taysen
    flat_data = "".join(all_res[:15])
    hot_nums = [x[0] for x in Counter(flat_data).most_common(3)]
    
    last_res = all_res[0]
    ml_pattern = TABEL_MISTIK_LAMA.get(last_res[3], last_res[3]) # Mistik Lama Ekor
    taysen_pattern = TABEL_TAYSEN.get(last_res[2], last_res[2]) # Taysen Kepala
    
    final_pool = list(dict.fromkeys(hot_nums + [ml_pattern, taysen_pattern]))
    
    if len(final_pool) < 5:
        all_freq = [x[0] for x in Counter(flat_data).most_common(10)]
        for f in all_freq:
            if f not in final_pool: final_pool.append(f)
            if len(final_pool) == 5: break
            
    return sorted(final_pool[:5])

def get_macau_shio(all_res):
    """Logika Macau Shio: Mencari 2 Shio terkuat dari result terakhir"""
    last_2d = all_res[0][2:] # Ambil 2D belakang
    shio_found = "KUDA"
    for name, nums in TABEL_SHIO.items():
        if last_2d in nums:
            shio_found = name
            break
            
    # Cari pendamping Shio berdasarkan Mistik Lama
    companion_val = TABEL_MISTIK_LAMA.get(last_2d[1], "0")
    companion_shio = "NAGA"
    for name, nums in TABEL_SHIO.items():
        if any(n.endswith(companion_val) for n in nums):
            companion_shio = name
            break
            
    return f"{shio_found} & {companion_shio}"

def hitung_investasi_2d(all_res):
    if not all_res: return ["02", "14", "26", "38"]
    
    # Ambil 2 Shio teratas dari histori
    all_2d = [r[2:] for r in all_res[:10]]
    shio_counts = Counter()
    for d2 in all_2d:
        for name, nums in TABEL_SHIO.items():
            if d2 in nums: shio_counts[name] += 1
            
    top_shio = shio_counts.most_common(1)[0][0] if shio_counts else "KUDA"
    
    # Ambil 4 angka dari Shio terkuat yang paling jarang keluar (Cold Number dlm Shio)
    candidates = TABEL_SHIO[top_shio]
    random.shuffle(candidates)
    return candidates[:4]

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
    if not all_res: all_res = ["0000"]*10
    
    am_base = get_ultra_sync_5digit(all_res)
    raw_2d = ["".join(p) for p in permutations(am_base, 2)]
    shio_macau = get_macau_shio(all_res)
    
    return jsonify({
        "market": market, "last": all_res[0], 
        "bbfs": " ".join(am_base),
        "shio": shio_macau,
        "list2d": ", ".join(sorted(list(set(raw_2d))[:15])),
        "posisi": f"ML: {TABEL_MISTIK_LAMA.get(am_base[0])} | IND: {TABEL_INDEKS.get(am_base[-1])}"
    })

@app.route('/analyze-invest', methods=['POST'])
def analyze_invest():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: all_res = ["0000"]*10
    return jsonify({"market": market, "invest_2d": hitung_investasi_2d(all_res)})

if __name__ == '__main__':
    app.run(debug=True)
