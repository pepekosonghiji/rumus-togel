import os, re, httpx
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# --- [LOCKED] DATABASE POLA ABADI ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263', 
    'HONGKONG POOLS': 'kia_hk', 'SINGAPORE POOLS': 'kia_sgp', 'SYDNEY POOLS': 'kia_sdy',
    'BUSAN POOLS':'p16063','OSAKA':'p28422','JEJU':'p22815','DANANG':'p22816',
    'PENANG':'p22817','SEOUL':'p28502','TORONTOMID':'p13976','SAPPORO':'p22814',
    'PHUKET':'p28435','WUHAN':'p28615'
}

# ==========================================================
#        [CORE ANALYTICS: WEIGHTING ENGINE]
# ==========================================================

def get_weighted_bbfs(all_res, limit=30):
    """Logika Bobot: Menggabungkan Angka Panas (Sering) & Dingin (Jarang)"""
    data_7d = "".join(all_res[:7])   # Data 7 Hari
    data_full = "".join(all_res[:limit]) # Data 30 Hari
    
    count_full = Counter(data_full)
    count_7d = Counter(data_7d)
    
    # Beri bobot lebih tinggi pada angka yang muncul dalam 7 hari terakhir
    weighted_scores = {}
    for num in "0123456789":
        score = count_full.get(num, 0) + (count_7d.get(num, 0) * 2)
        weighted_scores[num] = score
        
    # Ambil 6 angka dengan skor bobot tertinggi
    sorted_nums = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_nums[:6]]

# ==========================================================
#        [MARKET LOGIC: ISOLATED & UNIVERSAL]
# ==========================================================

def get_standard_logic(all_res):
    """Universal Logic V8 - Rebuilt with Weighting & 1D Tracking"""
    d0 = all_res[0] # Last Result
    d1 = all_res[1] if len(all_res) > 1 else d0 # Yesterday
    
    # Kombinasi Mistik/Taysen dari Last Result & 1 Day Ago
    line = [
        d0[3] + ML.get(d0[3], '0'),       # Ekor Last + ML
        TY.get(d0[2], '0') + d0[3],       # TY Kepala + Ekor
        ID.get(d1[3], '0') + d0[3],       # ID Ekor Lama + Ekor Baru
        ML.get(d0[1], '0') + TY.get(d1[2], '0') # ML Kop + TY Kepala Lama
    ]
    
    bbfs = get_weighted_bbfs(all_res)
    shio_idx = int(d0[2:]) % 12
    
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 6) % 12)}",
        "twin": f"{d0[3]}{d0[3]}, {ML.get(d0[3])}{ML.get(d0[3])}"
    }

def get_seoul_logic(all_res):
    d0 = all_res[0]
    k_fix, e_fix = TY.get(d0[2], '0'), ML.get(d0[1], '0')
    line = [k_fix + d0[3], d0[2] + e_fix, ID.get(d0[2]) + d0[3]]
    bbfs = get_weighted_bbfs(all_res, limit=15)
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": "MACAN-KUDA",
        "twin": f"{d0[0]}{d0[1]}"
    }

def get_sapporo_logic(all_res):
    d0 = all_res[0]
    k_sap, e_sap = TY.get(d0[1], '0'), ML.get(d0[0], '0')
    line = [k_sap + e_sap, d0[2] + ML.get(d0[0]), "23"] # 23 is tracking
    bbfs = get_weighted_bbfs(all_res, limit=20)
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": "AYAM-KELINCI",
        "twin": f"{d0[0]}{d0[1]}"
    }

# --- LOGIKA LAIN (WUHAN, JEJU, TORONTO) TETAP DIJAGA ---
def get_wuhan_logic(all_res):
    d0 = all_res[0]
    k1, e1 = ML.get(d0[3], '0'), ML.get(d0[2], '0')
    line = [k1+e1, d0[3]+k1]
    bbfs = get_weighted_bbfs(all_res)
    return {"core": ", ".join(line), "bbfs": " ".join(sorted(bbfs)), "as_kop": ID.get(d0[0], '0')+ID.get(d0[1], '0'), "kop_kep": ML.get(d0[1], '0')+ML.get(d0[2], '0'), "shio": SHIO_MAP.get(int(d0[2:])%12), "macau": "N/A", "twin": d0[3]+d0[3]}

def get_jeju_logic(all_res):
    d0 = all_res[0]
    line = [ML.get(d0[2])+TY.get(d0[3]), ML.get(d0[3])+ID.get(d0[2])]
    bbfs = get_weighted_bbfs(all_res, limit=10)
    return {"core": ", ".join(line), "bbfs": " ".join(sorted(bbfs)), "as_kop": ID.get(d0[0], '0')+ID.get(d0[1], '0'), "kop_kep": ML.get(d0[1], '0')+ML.get(d0[2], '0'), "shio": SHIO_MAP.get(int(d0[2:])%12), "macau": "N/A", "twin": d0[3]+d0[3]}

def get_toronto_logic(all_res):
    d0 = all_res[0]
    line = [MB.get(d0[1])+TY.get(d0[3]), ID.get(d0[2])+d0[3]]
    bbfs = get_weighted_bbfs(all_res)
    return {"core": ", ".join(line), "bbfs": " ".join(sorted(bbfs)), "as_kop": ID.get(d0[0], '0')+ID.get(d0[1], '0'), "kop_kep": ML.get(d0[1], '0')+ML.get(d0[2], '0'), "shio": SHIO_MAP.get(int(d0[2:])%12), "macau": "N/A", "twin": d0[3]+d0[3]}

# ==========================================================
#        [LOCKED: ENGINE & ROUTES]
# ==========================================================

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False) as client:
            url = f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', class_='table-history')
            if table:
                for row in table.find('tbody').find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
    except: pass
    return results

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(m_name))
    if not all_res: return jsonify({"error": "Sync Error"}), 500
    
    if m_name == "WUHAN": data = get_wuhan_logic(all_res)
    elif m_name == "JEJU": data = get_jeju_logic(all_res)
    elif m_name == "SEOUL": data = get_seoul_logic(all_res)
    elif m_name == "TORONTOMID": data = get_toronto_logic(all_res)
    elif m_name == "SAPPORO": data = get_sapporo_logic(all_res)
    else: data = get_standard_logic(all_res)
        
    return jsonify({"status":"success", "market":m_name, "last":all_res[0], "data":data})

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

if __name__ == '__main__':
    app.run(debug=True)
