import os, re, httpx, datetime
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# --- [DATABASE MASTER POLA ABADI] ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263', 
    'HONGKONG POOLS': 'HK_SPECIAL', 
    'SINGAPORE POOLS': 'singapore', 'SYDNEY POOLS': 'sydney',
    'BUSAN POOLS':'p16063', 'OSAKA':'p28422', 'JEJU':'p22815', 'DANANG':'p22816',
    'PENANG':'p22817', 'SEOUL':'p28502', 'TORONTOMID':'p13976', 'SAPPORO':'p22814',
    'PHUKET':'p28435', 'WUHAN':'p28615'
}

# --- [CORE ENGINE: WEIGHTING SYSTEM] ---
def get_engine_analytics(all_res, is_big=False):
    day_name = datetime.datetime.now().strftime("%A")
    limit = 60 if is_big else 30
    
    # Filter histori: Mingguan & Harian
    daily_hist = "".join([all_res[i] for i in range(len(all_res)) if i % 7 == 0][:5])
    recent_7d = "".join(all_res[:7])
    full_data = "".join(all_res[:limit])
    
    counts_full = Counter(full_data)
    counts_daily = Counter(daily_hist)
    counts_7d = Counter(recent_7d)
    
    scores = {}
    for n in "0123456789":
        base = counts_full.get(n, 0)
        hot = counts_7d.get(n, 0) * 3
        daily = counts_daily.get(n, 0) * 5
        
        matrix = {"Monday":"1257","Tuesday":"4905","Wednesday":"8361","Thursday":"2740","Friday":"3891","Saturday":"6150","Sunday":"0572"}
        day_bonus = 5 if n in matrix.get(day_name, "") else 0
        scores[n] = base + hot + daily + day_bonus
        
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_scores[:6]]

# --- [LOGIC BRANCHING: MIKRO & BIG] ---
def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    is_big = m_name in ['CAMBODIA', 'SYDNEY LOTTO', 'HONGKONG LOTTO', 'HONGKONG POOLS', 'SINGAPORE POOLS', 'SYDNEY POOLS']
    bbfs = get_engine_analytics(all_res, is_big)
    
    # Jalur Utama 2D
    line = [TY.get(d0[2], '0')+d0[3], ML.get(d0[2], '0')+ID.get(d0[1], '0'), MB.get(d0[0], '0')+d0[3]]
    
    # Penajaman Pasaran Mikro (Locked)
    if m_name == "OSAKA": line.extend([TY.get(d0[0])+d0[2], "54"])
    elif m_name == "PHUKET": line.extend([ML.get(d0[3])+d0[2], "31"])
    elif m_name == "WUHAN": line.extend([ML.get(d0[3])+ML.get(d0[2])])
    elif m_name == "JEJU": line.extend([ML.get(d0[2])+TY.get(d0[3])])
    elif m_name == "SEOUL": line.extend([TY.get(d0[2])+d0[3]])
    elif m_name == "SAPPORO": line.extend([TY.get(d0[1])+ML.get(d0[0]), "23"])
    elif m_name == "TORONTOMID": line.extend([MB.get(d0[1])+TY.get(d0[3])])
    elif is_big:
        line.append(ID.get(d0[1]) + d0[3])
        line.append(TY.get(d0[0]) + ML.get(d0[3]))

    shio_idx = int(d0[2:]) % 12
    return {
        "core": ", ".join(list(dict.fromkeys(line))),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {SHIO_MAP.get((shio_idx + 6) % 12)}",
        "twin": f"{d0[2]}{d0[2]}, {d0[3]}{d0[3]}"
    }

# --- [MULTI-SOURCE SCRAPER] ---
def fetch_results(market_code):
    results = []
    
    # SOURCE 1: tabelsemalam.com (Khusus HK Pools)
    if market_code == "HK_SPECIAL":
        try:
            with httpx.Client(timeout=15.0, verify=False) as client:
                r = client.get("https://tabelsemalam.com/")
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if table:
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) >= 2:
                            val = tds[1].text.strip() # Kolom index 1 = HK
                            if val.isdigit() and len(val) == 4:
                                results.append(val)
            if results: return results
        except: pass

    # SOURCE 2: salamrupiah (Standard & Micro)
    urls = [
        f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1",
        f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/kia_{market_code}"
    ]
    for url in urls:
        try:
            with httpx.Client(timeout=15.0, verify=False) as client:
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table', class_='table-history')
                if table:
                    for row in table.find('tbody').find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            val = re.sub(r'\D', '', tds[3].text.strip())
                            if len(val) == 4: results.append(val)
            if results: break
        except: continue
    return results

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(m_name))
    if not all_res: return jsonify({"error": "Sync Error: Data tidak ditemukan"}), 500
    data = get_comprehensive_logic(all_res, m_name)
    return jsonify({"status":"success", "market":m_name, "last":all_res[0], "data":data})

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

if __name__ == '__main__':
    app.run(debug=True)
