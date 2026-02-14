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

# --- TABEL REFERENSI ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

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

def get_dynamic_sync(all_res):
    if not all_res: return [str(random.randint(0,9)) for _ in range(6)]
    last_res = all_res[0]
    base_pool = []
    for num in last_res:
        base_pool.append(TABEL_MISTIK_BARU.get(num, num))
        base_pool.append(TABEL_TAYSEN.get(num, num))
    flat_data = "".join(all_res[:10])
    hot_nums = [x[0] for x in Counter(flat_data).most_common(4)]
    final_bbfs = list(dict.fromkeys(base_pool + hot_nums))
    return final_bbfs[:6]

def hitung_investasi_2d(all_res):
    if not all_res: return ["00", "11", "22", "33"]
    kepala_list = [res[2] for res in all_res[:15]]
    ekor_list = [res[3] for res in all_res[:15]]
    top_kepala = [x[0] for x in Counter(kepala_list).most_common(2)]
    top_ekor = [x[0] for x in Counter(ekor_list).most_common(2)]
    last_ekor = all_res[0][3]
    invest_set = set()
    has_twin = any(res[2] == res[3] for res in all_res[:5])
    if not has_twin: invest_set.add(last_ekor + last_ekor)
    for k in top_kepala:
        for e in top_ekor:
            invest_set.add(k + e)
    result_invest = sorted(list(invest_set))[:4]
    while len(result_invest) < 4:
        rand = str(random.randint(0,9))
        if (rand+rand) not in result_invest: result_invest.append(rand+rand)
    return result_invest

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
    if not all_res: all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]
    
    am_base = get_dynamic_sync(all_res)
    raw_2d = ["".join(p) for p in permutations(am_base, 2)]
    
    return jsonify({
        "market": market, "last": all_res[0], "bbfs": "".join(am_base),
        "shadow": "".join([TABEL_INDEKS.get(d, d) for d in am_base])[:5],
        "list2d_main": ", ".join(sorted(list(set(raw_2d))[:25])),
        "posisi": f"Kpl: {am_base[0]} | Ekr: {am_base[-1]}"
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
