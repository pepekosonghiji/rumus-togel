import os, re, random, httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter
from datetime import timedelta

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V6_ABSOLUTE"

# --- MASTER DATABASE POLA ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615', 'JAPAN POOLS': 'custom_japan', 
    'HONGKONG POOLS': 'kia_2', 'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4', 'OREGON 03': 'p12521',
    'ULANBATOR':'p28423','TIAPEI':'p28958','CALIFORNIAN':'p6490',
    'DANANG':'p22816','PENANG':'p22817','BATAM':'p28282'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_results(code):
    results = []
    try:
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            url = f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1"
            if code == 'custom_japan': url = "https://tabelupdate.online/data-keluaran-japan/"
            elif code.startswith('kia_'): url = "https://nomorkiajit.com/hksgpsdy"
            
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

def get_v6_analysis(all_res, market):
    if len(all_res) < 8: return None
    
    last = all_res[0]    # Kemarin
    weekly = all_res[7]  # Minggu Lalu
    pref = 'ML' if any(x in market for x in ['SINGAPORE', 'CAMBODIA', 'WUHAN']) else 'TY'
    
    # --- 1. CORE 2D BELAKANG (BOM) ---
    c1 = last[2] + (ML.get(weekly[3]) if pref == 'ML' else TY.get(weekly[3]))
    c2 = (ML.get(last[2]) if pref == 'ML' else TY.get(last[2])) + weekly[3]
    core = list(set([c1, c2, weekly[2:], last[3]+last[2]]))
    
    # --- 2. SHADOW 2D (CADANGAN) ---
    s1 = ID.get(last[2]) + ID.get(last[3])
    s2 = ML.get(last[2]) + TY.get(last[3])
    shadow = list(set([s1, s2, TY.get(last[2])+ID.get(last[3])]))

    # --- 3. POSISI DEPAN & TENGAH ---
    depan = [last[0] + ID.get(last[1]), TY.get(last[0]) + last[1]]
    tengah = [last[1] + ML.get(last[2]), TY.get(last[1]) + last[2]]

    # --- 4. TWIN DETECTOR ---
    has_twin = any(r[2] == r[3] for r in all_res[:10])
    hot_digit = Counter("".join(all_res[:5])).most_common(2)
    twins = [x[0]+x[0] for x in hot_digit]

    # --- 5. BBFS CADANGAN ---
    bbfs = sorted([x[0] for x in Counter("".join(all_res[:15])).most_common()[3:8]])

    return {
        "core": ", ".join([x for x in core if len(x)==2][:8]),
        "shadow": ", ".join([x for x in shadow if len(x)==2][:8]),
        "depan": ", ".join(list(set(depan))),
        "tengah": ", ".join(list(set(tengah))),
        "twin_status": "WASPADA TWIN" if not has_twin else "NORMAL",
        "twin_picks": ", ".join(twins),
        "bbfs": " ".join(bbfs)
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
    if not all_res: return jsonify({"error": "Server Error"})
    
    data = get_v6_analysis(all_res, market)
    return jsonify({
        "market": market, "last": all_res[0], "weekly": all_res[7],
        "data": data, "method": "V6.0 POSITION SYNC"
    })

if __name__ == '__main__':
    app.run(debug=True)
