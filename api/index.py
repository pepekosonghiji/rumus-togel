import os, re, httpx
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# --- [LOCKED] DATABASE POLA ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

# --- [LOCKED] TARGET POOLS ---
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263', 
    'HONGKONG POOLS': 'kia_hk', 'SINGAPORE POOLS': 'kia_sgp', 'SYDNEY POOLS': 'kia_sdy',
    'BUSAN POOLS':'p16063','OSAKA':'p28422','JEJU':'p22815','DANANG':'p22816',
    'PENANG':'p22817','SEOUL':'p28502','TORONTOMID':'p13976','SAPPORO':'p22814',
    'PHUKET':'p28435','WUHAN':'p28615'
}

# ==========================================================
#        [ZONE MODIFIKASI LOGIKA PASARAN]
# ==========================================================

# 1. LOGIKA KHUSUS: WUHAN
def get_wuhan_logic(all_res):
    d0 = all_res[0]
    k1, k2 = ML.get(d0[3], '0'), TY.get(d0[3], '0')
    e1, e2 = ML.get(d0[2], '0'), TY.get(d0[3], '0')
    line = [k1+e1, k1+e2, k2+e1, k2+e2, d0[3]+k1, e1+k2]
    counts = Counter("".join(all_res[:20]))
    bbfs = [x[0] for x in counts.most_common(6)]
    shio_idx = int(d0[2:]) % 12
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 6) % 12)}",
        "twin": f"{d0[3]}{d0[3]}, {k1}{k1}"
    }

# 2. LOGIKA KHUSUS: JEJU (NEW)
def get_jeju_logic(all_res):
    d0 = all_res[0] # Result Terakhir: 1924
    # JEJU sering main di pola INDEX silang dari 2D tengah
    k_jeju = ID.get(d0[1], '0') # Index dari KOP
    e_jeju = TY.get(d0[2], '0') # Taysen dari Kepala
    
    line = [k_jeju+e_jeju, e_jeju+k_jeju, d0[3]+k_jeju, ML.get(d0[3])+e_jeju]
    counts = Counter("".join(all_res[:15])) # JEJU sangat sensitif pada data terbaru
    bbfs = [x[0] for x in counts.most_common(6)]
    shio_idx = int(d0[2:]) % 12
    
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 4) % 12)}",
        "twin": f"{d0[2]}{d0[2]}, {d0[3]}{d0[3]}"
    }

# 3. LOGIKA STANDAR
def get_standard_logic(all_res):
    d0 = all_res[0]
    counts = Counter("".join(all_res[:30]))
    bbfs = [x[0] for x in counts.most_common(6)]
    shio_idx = int(d0[2:]) % 12
    line = [d0[3]+ML.get(d0[3]), TY.get(d0[2])+d0[3]]
    return {
        "core": ", ".join(line),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 6) % 12)}",
        "twin": f"{d0[3]}{d0[3]}"
    }

# --- [LOCKED] ENGINE ---
def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False) as client:
            url = f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            for row in soup.find('table', class_='table-history').find('tbody').find_all('tr'):
                tds = row.find_all('td')
                if len(tds) >= 4:
                    val = re.sub(r'\D', '', tds[3].text.strip())
                    if len(val) == 4: results.append(val)
    except: pass
    return results

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    m_code = TARGET_POOLS.get(m_name)
    all_res = fetch_results(m_code)
    if not all_res: return jsonify({"error": "Sync Error"}), 500
    
    if m_name == "WUHAN": data = get_wuhan_logic(all_res)
    elif m_name == "JEJU": data = get_jeju_logic(all_res)
    else: data = get_standard_logic(all_res)
        
    return jsonify({"status":"success", "market":m_name, "last":all_res[0], "data":data})

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

if __name__ == '__main__':
    app.run(debug=True)
