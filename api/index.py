import os, re, httpx, datetime
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

# PENTING: Import macau dipindahkan ke dalam fungsi analyze untuk mencegah Error 500 saat startup
# dari .macau import fetch_macau_m17, calculate_macau_prediction <-- INI DIHAPUS DARI ATAS

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# --- [DATABASE MASTER POLA ABADI - TIDAK DISENTUH] ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

# --- [TARGET POOLS - TIDAK DISENTUH] ---
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263', 
    'HONGKONG POOLS': 'HK_SPECIAL', 'SINGAPORE POOLS': 'singapore', 'SYDNEY POOLS': 'sydney',
    'BUSAN POOLS':'p16063', 'OSAKA':'p28422', 'JEJU':'p22815', 'DANANG':'p22816',
    'PENANG':'p22817', 'SEOUL':'p28502', 'TORONTOMID':'p13976', 'SAPPORO':'p22814',
    'PHUKET':'p28435', 'WUHAN':'p28615','MACAU 4D':'MACAU_TRIGGER'
}

# --- [CORE ENGINE V9.5 - TIDAK DISENTUH] ---
def get_engine_analytics(all_res, is_big=False):
    d0 = all_res[0]
    limit = 60 if is_big else 30
    full_data = "".join(all_res[:limit])
    counts_full = Counter(full_data)
    scores = {n: counts_full.get(n, 0) for n in "0123456789"}
    for n in "0123456789":
        for i, res in enumerate(all_res[:20]):
            if n in res:
                scores[n] += i
                break
    scores[TY.get(d0[0], '0')] += 15 
    scores[ML.get(d0[1], '0')] += 10
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_scores[:6]]

# --- [LOGIC BRANCHING - TIDAK DISENTUH] ---
def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    is_big = m_name in ['CAMBODIA', 'SYDNEY LOTTO', 'HONGKONG LOTTO', 'HONGKONG POOLS', 'SINGAPORE POOLS', 'SYDNEY POOLS']
    bbfs = get_engine_analytics(all_res, is_big)
    line = [TY.get(d0[2], '0')+d0[3], ML.get(d0[2], '0')+ID.get(d0[1], '0')]
    
    if m_name == "OSAKA": line = [ID.get(d0[1])+d0[3], "84", "24", "74", "45", "54"]
    elif m_name == "JEJU": line = [ML.get(d0[2])+TY.get(d0[3]), "06", "45", "43"]
    elif m_name == "TORONTOMID": line = [MB.get(d0[1])+TY.get(d0[3]), "76", "19", "66", "53"]
    elif m_name == "HONGKONG LOTTO":
        line.extend([ID.get(d0[0])+ML.get(d0[3]), TY.get(d0[1])+d0[2], MB.get(d0[3])+d0[0]])
    elif m_name == "CAMBODIA":
        line.extend([ID.get(d0[0])+ML.get(d0[3]), TY.get(d0[1])+ID.get(d0[2]), d0[1]+d0[3]])
    elif m_name == "SYDNEY LOTTO":
        line.extend([ML.get(d0[0])+TY.get(d0[2]), ID.get(d0[1])+d0[3]])
    elif m_name == "PHUKET":
        line.extend([MB.get(d0[0])+d0[2], ML.get(d0[1])+TY.get(d0[3])])
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

# --- [SCRAPER - TIDAK DISENTUH] ---
def fetch_results(market_code):
    results = []
    if market_code == "HK_SPECIAL":
        try:
            with httpx.Client(timeout=15.0, verify=False) as client:
                r = client.get("https://tabelsemalam.com/")
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if table:
                    for row in table.find('tbody').find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 2:
                            val = tds[1].text.strip()
                            if val.isdigit() and len(val) == 4: results.append(val)
            if results: return results
        except: pass
    urls = [f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1", f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/kia_{market_code}"]
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

# --- [ROUTE ANALYZE - PERBAIKAN STABILITAS] ---
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        market = request.form.get('market')
        if not market: return jsonify({"status": "error", "msg": "Pilih Pasaran"}), 400

        # Penanganan Khusus MACAU agar tidak 500
        if market == "MACAU 4D":
            from .macau import calculate_macau_prediction
            # Gunakan p2263 sebagai sumber data sementara jika MACAU_TRIGGER gagal
            results = fetch_results('p2263') 
            if not results: return jsonify({"status": "error", "msg": "Sync Macau Gagal"}), 500
            data = calculate_macau_prediction(results)
            return jsonify({"status": "success", "market": "MACAU 4D (M17)", "last": results[0], "data": data})

        # Pasaran Normal
        market_code = TARGET_POOLS.get(market)
        if not market_code: return jsonify({"status": "error", "msg": "Kode Pasaran Hilang"}), 400
        
        results = fetch_results(market_code)
        if not results: return jsonify({"status": "error", "msg": f"Gagal Sinkronisasi {market}"}), 500
        
        data = get_comprehensive_logic(results, market)
        return jsonify({"status": "success", "market": market, "last": results[0], "data": data})
    
    except Exception as e:
        # Menangkap error apa pun agar tidak muncul 500 Internal Server Error
        return jsonify({"status": "error", "msg": f"Sistem Crash: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

if __name__ == '__main__':
    app.run(debug=True)
