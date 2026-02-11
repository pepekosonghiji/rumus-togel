import os
import json
from flask import Flask, render_template, request, jsonify, session
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import Counter
import re
import random

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
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'SINGAPORE POOLS': 'p2664',
    'BUSAN POOLS': 'p16063', 'HONGKONG LOTTO': 'p2263', 'WUHAN': 'p28615',
    'SEOUL': 'p28502', 'OSAKA': 'p28422', 'toto macau 4d': 'm17'        
}

TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_LAMA = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
BASE_URL = 'https://tgr7grldrc.salamrupiah.com/history/result-mobile/'

def get_day_name(offset=0):
    days_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    target_date = datetime.now() - timedelta(days=offset)
    return days_indo[target_date.weekday()]

# --- ENGINE ANALISIS ---

def get_statistical_data(server_code):
    all_digits = ""
    last_appearance = {str(i): 0 for i in range(10)}
    try:
        with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
            for pg in range(1, 4): 
                r = client.get(f"{BASE_URL}{server_code}-pool-1?page={pg}", headers=HEADERS)
                soup = BeautifulSoup(r.text, 'html.parser')
                rows = soup.find('table').find('tbody').find_all('tr')
                for idx, row in enumerate(rows):
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        res = re.sub(r'\D', '', cols[3].text.strip())
                        if len(res) == 4:
                            all_digits += res
                            for d in res:
                                if last_appearance[d] == 0:
                                    last_appearance[d] = idx + ((pg-1) * 10)
        freq = Counter(all_digits)
        hot = [x[0] for x in freq.most_common(5)]
        cold = sorted(last_appearance, key=last_appearance.get, reverse=True)[:2]
        return list(dict.fromkeys(hot + cold))
    except:
        return []

def proses_hybrid(server_key):
    try:
        code = TARGET_POOLS[server_key]
        with httpx.Client(timeout=30, verify=False) as client:
            raw_res = client.get(f"{BASE_URL}{code}-pool-1", headers=HEADERS).text
        soup = BeautifulSoup(raw_res, 'html.parser')
        all_res = [re.sub(r'\D', '', r.find_all('td')[3].text.strip()) for r in soup.find('tbody').find_all('tr') if len(re.sub(r'\D', '', r.find_all('td')[3].text.strip())) == 4]
        
        if not all_res: return None
        last_res = all_res[0]

        # Kerucutkan BBFS ke 5-6 digit terkuat
        stat_numbers = get_statistical_data(code)
        taysen_last = [TABEL_TAYSEN.get(d, '0') for d in last_res[-2:]]
        
        # Prioritas penggabungan angka
        combined = list(dict.fromkeys(stat_numbers + taysen_last))
        
        # KERUCUTKAN: Ambil hanya 6 digit terbaik
        am_hybrid = combined[:6]
        
        # Jika kurang dari 5, tambahkan indeks
        if len(am_hybrid) < 5:
            for d in list(am_hybrid):
                idx_val = TABEL_INDEKS.get(d)
                if idx_val not in am_hybrid: am_hybrid.append(idx_val)
                if len(am_hybrid) >= 6: break

        # Generate TOP 3D & 4D (Sistem Acak dari BBFS)
        bbfs_str = am_hybrid
        top_3d = []
        top_4d = []
        
        for _ in range(2):
            top_3d.append("".join(random.sample(bbfs_str, 3)))
            top_4d.append("".join(random.sample(bbfs_str, 4)))

        # Shadow BBFS (5 Digit)
        shadow_pool = [TABEL_MISTIK_LAMA.get(d, d) for d in am_hybrid]
        shadow_final = "".join(list(dict.fromkeys(shadow_pool))[:5])

        return {
            "market": server_key.upper(),
            "last": last_res,
            "bbfs": "".join(am_hybrid),
            "shadow": shadow_final,
            "jitu": f"{am_hybrid[0]}{am_hybrid[1]}, {am_hybrid[2]}{am_hybrid[3]}",
            "top3d": ", ".join(top_3d),
            "top4d": ", ".join(top_4d),
            "posisi": f"Kpl: {am_hybrid[0]} | Ekr: {am_hybrid[1]}"
        }
    except:
        return None

# --- ROUTES (SAMA SEPERTI SEBELUMNYA) ---
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
    return jsonify({"status": "error", "message": "Invalid/Expired Key!"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('authorized'): return jsonify({"error": "Unauthorized"}), 403
    market = request.form.get('market')
    result = proses_hybrid(market)
    return jsonify(result) if result else jsonify({"error": "Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
