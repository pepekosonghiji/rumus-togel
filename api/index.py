import os, re, httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V7_4_FULL_PATTERN"

# --- DATABASE POLA LENGKAP ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'} # Mistik Lama
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'} # Mistik Baru
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'} # Index
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'} # Taysen

# SHIO 2026 (Jalur Angka)
SHIO = {
    'KUDA': ['01','13','25','37','49','61','73','85','97'],
    'ULAR': ['02','14','26','38','50','62','74','86','98'],
    'NAGA': ['03','15','27','39','51','63','75','87','99']
}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 
    'SYDNEY LOTTO': 'p2262', 
    'HONGKONG LOTTO': 'p2263',
    'HONGKONG POOLS': 'kia_hk',
    'SINGAPORE POOLS': 'kia_sgp', 
    'SYDNEY POOLS': 'kia_sdy'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            is_kia = market_code.startswith('kia_')
            url = "https://nomorkiajit.com/hksgpsdy" if is_kia else f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            if is_kia:
                col_idx = 2 if 'hk' in market_code else (3 if 'sgp' in market_code else 4)
                rows = soup.find('table').find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) > col_idx:
                        val = re.sub(r'\D', '', tds[col_idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                rows = soup.select('tbody tr') or soup.select('table tr')
                for row in rows:
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
    
    # BBFS 7-DIGIT (Frequency + Mistiks)
    counts = Counter("".join(all_res[:15]))
    bbfs_base = [x[0] for x in counts.most_common(7)]
    
    # CORE 2D LOGIC (V7.3 Khusus HK)
    # Persilangan Mistik & Index antara Ekor Last vs Ekor Weekly
    c1 = last[3] + weekly[3]
    c2 = ID.get(last[3]) + ML.get(last[2])
    c3 = MB.get(last[3]) + TY.get(last[3])
    core_raw = list(dict.fromkeys([c1, c1[::-1], c2, c2[::-1], c3, c3[::-1]]))
    
    # SHIO PREDICTION (Berdasarkan 2D Belakang)
    shio_last = int(last[2:]) % 12
    shio_text = "NAGA/ULAR" if shio_last in [3, 2] else "KUDA/HARIMAU"

    return {
        "core": ", ".join(core_raw[:8]),
        "shadow": ", ".join([TY.get(last[2])+TY.get(last[3]), MB.get(last[2])+MB.get(last[3])]),
        "depan": last[0] + ID.get(last[1]),
        "tengah": last[1] + ML.get(last[2]),
        "shio": shio_text,
        "twin_status": "WASPADA" if last[0] == last[1] else "NORMAL",
        "twin_picks": f"{last[3]}{last[3]}, {ML.get(last[3])}{ML.get(last[3])}, {ID.get(last[3])}{ID.get(last[3])}",
        "bbfs": " ".join(sorted(bbfs_base))
    }

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('key') == "ramdani3":
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 401

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    m_code = TARGET_POOLS.get(m_name)
    all_res = fetch_results(m_code)
    if not all_res: return jsonify({"error": "Data Gagal Sinkron"})
    data = get_v7_analysis(all_res, m_name)
    return jsonify({"market": m_name, "last": all_res[0], "weekly": all_res[7], "data": data})

if __name__ == '__main__':
    app.run(debug=True)
