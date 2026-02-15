import os, re, random, httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter
from datetime import timedelta

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = os.environ.get("SECRET_KEY", "MAMANG_V5_ULTRA_SHADOW")

# --- MASTER DATABASE POLA ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615', 'JAPAN POOLS': 'custom_japan', 
    'HONGKONG POOLS': 'kia_2', 'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4', 'OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            if code == 'custom_japan':
                r = client.get("https://tabelupdate.online/data-keluaran-japan/")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows[:30]: # Ambil 30 data untuk analisa mingguan
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

def process_logic_v5(all_res, market):
    if len(all_res) < 8: return {"core": [], "shadow": [], "bbfs": []}

    daily = all_res[0]   # Result Kemarin
    weekly = all_res[7]  # Result Minggu Lalu (Hari yang sama)
    
    # Karakteristik Market
    pref = 'ML' if 'SINGAPORE' in market or 'CAMBODIA' in market else 'TY'
    
    # --- MENCARI CORE 2D (BOM) ---
    # Teknik: Persilangan Kepala Kemarin & Mistik Ekor Minggu Lalu
    core_1 = daily[2] + (ML.get(weekly[3]) if pref == 'ML' else TY.get(weekly[3]))
    core_2 = (ML.get(daily[2]) if pref == 'ML' else TY.get(daily[2])) + weekly[3]
    core_3 = weekly[2:] # Replay angka minggu lalu
    
    core_list = list(set([core_1, core_2, core_3]))
    # Tambah variasi taysen dari ekor kemarin
    core_list.append(TY.get(daily[3]) + daily[3])
    
    # --- MENCARI SHADOW 2D (CADANGAN) ---
    # Teknik: Angka Indeks dan Angka yang belum keluar (Cold)
    shadow_1 = ID.get(daily[2]) + ID.get(daily[3])
    shadow_2 = ML.get(daily[2]) + TY.get(daily[3])
    shadow_3 = str((int(daily[2])+5)%10) + str((int(daily[3])+5)%10)
    
    shadow_list = list(set([shadow_1, shadow_2, shadow_3]))

    # --- BBFS CADANGAN (5-DIGIT) ---
    all_digits = "".join(all_res[:15])
    counts = Counter(all_digits)
    # Ambil angka yang frekuensinya menengah (bukan paling sering, bukan paling jarang)
    sorted_digits = [x[0] for x in counts.most_common()]
    bbfs = sorted(sorted_digits[3:8]) 

    return {
        "core": [x for x in core_list if len(x)==2][:10],
        "shadow": [x for x in shadow_list if len(x)==2][:10],
        "bbfs": bbfs
    }

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
    
    if not all_res: return jsonify({"error": "Data server tidak terjangkau"})
    
    data = process_logic_v5(all_res, market)
    
    return jsonify({
        "market": market,
        "last": all_res[0],
        "weekly": all_res[7] if len(all_res) > 7 else "N/A",
        "core_2d": ", ".join(data['core']),
        "shadow_2d": ", ".join(data['shadow']),
        "bbfs": " ".join(data['bbfs']),
        "method": "V5.0 WEEKLY CROSS-SYNC"
    })

if __name__ == '__main__':
    app.run(debug=True)
