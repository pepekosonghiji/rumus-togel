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

app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_TECH_2026_PREMIUM")
app.permanent_session_lifetime = timedelta(days=1)

# --- TABEL REFERENSI LENGKAP ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
TABEL_MISTIK_LAMA = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_TAYSEN = {
    '0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'
}

# Data Shio 2026 (Tahun Kuda) - Jalur Utama
SHIO_2026 = {
    "KUDA": ["02", "14", "26", "38", "50", "62", "74", "86", "98"],
    "AYAM": ["05", "17", "29", "41", "53", "65", "77", "89"],
    "NAGA": ["08", "20", "32", "44", "56", "68", "80", "92"]
}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263','BUSAN POOLS': 'p16063', 'WUHAN': 'p28615',
    'JAPAN POOLS': 'custom_japan', 'HONGKONG POOLS': 'kia_2',
    'SINGAPORE POOLS': 'kia_3', 'SYDNEY POOLS': 'kia_4','OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

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

def get_advanced_filter(all_res):
    """Fungsi baru untuk memperkecil angka berdasarkan 4 pola mistik/taysen"""
    if not all_res: return []
    
    last_4d = all_res[0] # Contoh: '1234'
    d1, d2, d3, d4 = last_4d[0], last_4d[1], last_4d[2], last_4d[3]
    
    # Kumpulkan bibit angka dari pola
    seeds = [
        TABEL_INDEKS.get(d4), 
        TABEL_MISTIK_BARU.get(d3), 
        TABEL_MISTIK_LAMA.get(d4),
        TABEL_TAYSEN.get(d2),
        TABEL_TAYSEN.get(d4)
    ]
    
    # Statistik frekuensi tetap digunakan sebagai penyeimbang
    flat_data = "".join(all_res[:15])
    counts = Counter(flat_data)
    hot = [x[0] for x in counts.most_common(3)]
    
    # Gabungkan dan hilangkan duplikat, ambil 6 digit terbaik
    final_bbfs = list(dict.fromkeys(seeds + hot))
    return final_bbfs[:6]

def generate_2d_filtered(bbfs_list):
    """Menghasilkan 2D yang sudah difilter agar tidak terlalu banyak"""
    raw_2d = ["".join(p) for p in permutations(bbfs_list, 2)]
    # Filter: Ambil angka yang sering muncul di result terakhir (pola tarikan)
    return ", ".join(sorted(list(set(raw_2d))[:25])) 

def generate_top_set(bbfs_list, count=2):
    if len(bbfs_list) < 4: return ["-"], ["-"]
    c3 = list(combinations(bbfs_list, 3))
    c4 = list(combinations(bbfs_list, 4))
    m3 = ["".join(x) for x in random.sample(c3, min(count, len(c3)))]
    m4 = ["".join(x) for x in random.sample(c4, min(count, len(c4)))]
    return m3, m4

# --- LOGIKA RUMUS INTEGRASI ---

def hitung_rumus_satu(market_key, all_res):
    last_res = all_res[0]
    # Menggunakan filter advanced (Indeks, Mistik, Taysen)
    am_base = get_advanced_filter(all_res)
    
    bbfs_main_str = "-".join(am_base)
    
    # Shadow BBFS menggunakan Mistik Lama dari BBFS utama
    shadow_list = list(dict.fromkeys([TABEL_MISTIK_LAMA.get(d, d) for d in am_base]))[:5]
    bbfs_shadow_str = "-".join(shadow_list)

    m3, m4 = generate_top_set(am_base)
    
    # Ambil Shio Kuda sebagai penguat posisi
    shio_kuda = random.choice(SHIO_2026["KUDA"])

    return {
        "market": market_key, "last": last_res, 
        "bbfs": bbfs_main_str, "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d_filtered(am_base),
        "top3d": f"Main: {', '.join(m3)}",
        "top4d": f"Shio Kuda: {shio_kuda}",
        "posisi": f"Kpl: {am_base[0]} | Ekr: {am_base[-1]}"
    }

def proses_hybrid_v3(market_key, all_res):
    last_res = all_res[0]
    am_base = get_advanced_filter(all_res)
    
    # Logika tambahan Taysen untuk Hybrid
    taysen_ekor = TABEL_TAYSEN.get(last_res[-1])
    if taysen_ekor not in am_base: am_base.append(taysen_ekor)
    
    bbfs_main_list = am_base[:6]
    bbfs_main_str = "".join(bbfs_main_list)
    
    shadow_list = list(dict.fromkeys([TABEL_INDEKS.get(d, d) for d in bbfs_main_list]))[:5]
    bbfs_shadow_str = "".join(shadow_list)

    m3, m4 = generate_top_set(bbfs_main_list)

    return {
        "market": market_key, "last": last_res, 
        "bbfs": bbfs_main_str, "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d_filtered(bbfs_main_list),
        "top3d": f"Mistik: {', '.join(m3)}",
        "top4d": f"Taysen: {', '.join(m4)}",
        "posisi": f"Kpl: {bbfs_main_list[1]} | Ekr: {bbfs_main_list[0]}"
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
    
    if not all_res:
        all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]

    if rumus_type == "rumus_1":
        return jsonify(hitung_rumus_satu(market, all_res))
    else:
        return jsonify(proses_hybrid_v3(market, all_res))

if __name__ == '__main__':
    app.run(debug=True)
