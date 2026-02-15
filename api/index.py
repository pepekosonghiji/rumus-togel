import os, re, random, httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V7_ULTRA"

# --- MASTER DATABASE POLA ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'HONGKONG POOLS': 'kia_2', 'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4', 'OREGON 03': 'p12521'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            url = f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1"
            if code.startswith('kia_'): url = "https://nomorkiajit.com/hksgpsdy"
            
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.select('tbody tr') or soup.select('table tr')
            for row in rows[:30]:
                tds = row.find_all('td')
                for td in tds:
                    val = re.sub(r'\D', '', td.text.strip())
                    if len(val) == 4: 
                        results.append(val)
                        break
    except: pass
    return results

def get_v7_analysis(all_res, market):
    if len(all_res) < 8: return None
    last = all_res[0]
    weekly = all_res[7]
    
    # 1. BBFS 6-DIGIT (Cakupan Luas)
    counts = Counter("".join(all_res[:15]))
    bbfs_6 = sorted([x[0] for x in counts.most_common(6)])
    
    # 2. CORE 2D DENGAN PROTEKSI BB
    c1 = last[2] + weekly[3]
    c2 = weekly[2] + last[3]
    core_raw = list(dict.fromkeys([c1, c1[::-1], c2, c2[::-1]]))
    
    # 3. TWIN & POSISI
    is_pot_twin = (last[0] == weekly[0]) or (last[3] == weekly[3])
    
    return {
        "core": ", ".join(core_raw[:6]),
        "shadow": ", ".join([ID.get(last[2])+ID.get(last[3]), ML.get(last[2])+TY.get(last[3])]),
        "depan": last[0] + ID.get(last[1]),
        "tengah": last[1] + ML.get(last[2]),
        "twin_status": "SANGAT WASPADA" if is_pot_twin else "NORMAL",
        "twin_picks": f"{last[3]}{last[3]}, {weekly[3]}{weekly[3]}, 00, 11",
        "bbfs": " ".join(bbfs_6)
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
    market = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: return jsonify({"error": "Server Timeout"})
    data = get_v7_analysis(all_res, market)
    return jsonify({"market": market, "last": all_res[0], "weekly": all_res[7], "data": data})

if __name__ == '__main__':
    app.run(debug=True)
