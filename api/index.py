import os, re, httpx, datetime
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
    'BUSAN POOLS':'p16063', 'OSAKA':'p28422', 'JEJU':'p22815', 'DANANG':'p22816',
    'PENANG':'p22817', 'SEOUL':'p28502', 'TORONTOMID':'p13976', 'SAPPORO':'p22814',
    'PHUKET':'p28435', 'WUHAN':'p28615'
}

# --- ENGINE: DAILY & WEIGHTED ANALYTICS ---
def get_weighted_analytics(all_res, is_big_market=False):
    limit = 60 if is_big_market else 30
    data_7d = "".join(all_res[:7])
    data_full = "".join(all_res[:limit])
    day_now = datetime.datetime.now().strftime("%A")
    
    counts = Counter(data_full)
    counts_7d = Counter(data_7d)
    
    scores = {}
    for n in "0123456789":
        score = counts.get(n, 0) + (counts_7d.get(n, 0) * 2)
        # Daily Strength Calibration
        if day_now == "Tuesday" and n in "1549": score += 5
        if day_now == "Wednesday" and n in "0236": score += 5
        scores[n] = score
        
    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:6]]

# ==========================================================
#        [LOCKED: MICRO MARKET LOGICS]
# ==========================================================

def get_micro_logic(all_res, m_name):
    d0 = all_res[0]
    bbfs = get_weighted_analytics(all_res, False)
    
    # Switcher Logika Khusus Pasaran Mikro (DIPERTAHANKAN)
    if m_name == "OSAKA":
        line = [TY.get(d0[0])+d0[2], MB.get(d0[1])+d0[3], "54", "45"]
    elif m_name == "PHUKET":
        line = [ML.get(d0[3])+d0[2], ID.get(d0[2])+d0[3], "31", "13"]
    elif m_name == "WUHAN":
        line = [ML.get(d0[3])+ML.get(d0[2]), d0[3]+ML.get(d0[3])]
    elif m_name == "JEJU":
        line = [ML.get(d0[2])+TY.get(d0[3]), ML.get(d0[3])+ID.get(d0[2])]
    elif m_name == "SEOUL":
        line = [TY.get(d0[2],'0')+d0[3], d0[2]+ML.get(d0[1],'0')]
    elif m_name == "SAPPORO":
        line = [TY.get(d0[1],'0')+ML.get(d0[0],'0'), d0[2]+ML.get(d0[0],'0'), "23"]
    elif m_name == "TORONTOMID":
        line = [MB.get(d0[1])+TY.get(d0[3]), ID.get(d0[2])+d0[3]]
    else:
        line = [ML.get(d0[2])+d0[3], TY.get(d0[3])+d0[2]]

    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0]) + ID.get(d0[1]),
        "kop_kep": ML.get(d0[1]) + ML.get(d0[2]),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12),
        "macau": "MICRO-LOCKED",
        "twin": f"{d0[3]}{d0[3]}"
    }

# ==========================================================
#        [NEW: BIG MARKET LOGIC]
# ==========================================================

def get_big_market_logic(all_res, m_name):
    d0 = all_res[0]
    # Pola Tarikan Stabilizer Pasaran Besar
    k_big = TY.get(d0[2], '0')
    e_big = ML.get(d0[3], '0')
    line = [k_big + d0[3], d0[2] + e_big, ID.get(d0[1]) + d0[3]]
    bbfs = get_weighted_analytics(all_res, True)
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0]) + ID.get(d0[1]),
        "kop_kep": ML.get(d0[1]) + ML.get(d0[2]),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12),
        "macau": "BIG-MARKET-STABLE",
        "twin": f"{d0[2]}{d0[2]}, {d0[3]}{d0[3]}"
    }

# --- ENGINE & ROUTES ---
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
    
    big_markets = ['CAMBODIA', 'SYDNEY LOTTO', 'HONGKONG LOTTO', 'HONGKONG POOLS', 'SINGAPORE POOLS', 'SYDNEY POOLS']
    
    if m_name in big_markets:
        data = get_big_market_logic(all_res, m_name)
    else:
        data = get_micro_logic(all_res, m_name)
        
    return jsonify({"status":"success", "market":m_name, "last":all_res[0], "data":data})

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

if __name__ == '__main__':
    app.run(debug=True)
