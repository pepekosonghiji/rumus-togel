import os, re, httpx
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# --- DATABASE POLA ABADI (LOCKED) ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

SHIO_MAP = {
    10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 
    4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"
}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 
    'SYDNEY LOTTO': 'p2262', 
    'HONGKONG LOTTO': 'p2263',
    'HONGKONG POOLS': 'kia_hk',
    'SINGAPORE POOLS': 'kia_sgp', 
    'SYDNEY POOLS': 'kia_sdy'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False, headers=HEADERS, follow_redirects=True) as client:
            if market_code.startswith('kia_'):
                url = "https://nomorkiajit.com/hksgpsdy"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                col_map = {'kia_hk': 2, 'kia_sgp': 3, 'kia_sdy': 4}
                idx = col_map.get(market_code)
                for row in soup.find('table').find_all('tr')[1:]:
                    tds = row.find_all('td')
                    if len(tds) > idx:
                        val = re.sub(r'\D', '', tds[idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                url = f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table', class_='table-history')
                if table:
                    for row in table.find('tbody').find_all('tr'):
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            link_val = tds[3].find('a')
                            if link_val:
                                val = re.sub(r'\D', '', link_val.text.strip())
                                if len(val) == 4: results.append(val)
    except: pass
    return results

def get_v8_analysis(all_res):
    if not all_res or len(all_res) < 8: return None
    
    d0 = all_res[0] # Hari Ini
    d1 = all_res[1] # Kemarin
    d7 = all_res[7] # Minggu Lalu
    
    # 1. ANALISA MULTI-PERIOD (CORE)
    # Mencari titik temu Mistik/Taysen antara Result Hari ini vs Kemarin
    p1 = ML.get(d0[3], '0') + TY.get(d1[3], '0')
    p2 = ID.get(d0[3], '0') + MB.get(d1[2], '0')
    p3 = d0[3] + d7[3]
    
    core_list = list(dict.fromkeys([p1, p1[::-1], p2, p2[::-1], p3, p3[::-1]]))
    
    # 2. SHIO MACAU (Kombinasi Shio Induk & Shio Cadangan)
    shio_idx = int(d0[2:]) % 12
    main_shio = SHIO_MAP.get(shio_idx, "N/A")
    macau_shio = f"{main_shio} - {SHIO_MAP.get((shio_idx + 6) % 12)}" # Shio Berseberangan
    
    # 3. BBFS FREKUENSI 30 DATA
    counts = Counter("".join(all_res[:30]))
    bbfs = [x[0] for x in counts.most_common(7)]
    
    return {
        "core": ", ".join(core_list[:8]),
        "shadow": f"{TY.get(d0[2])}{TY.get(d0[3])}, {MB.get(d0[2])}{MB.get(d0[3])}",
        "depan": d0[0] + ID.get(d0[1], '0'),
        "tengah": d0[1] + ML.get(d0[2], '0'),
        "shio": main_shio,
        "macau": macau_shio,
        "twin": f"{d0[3]}{d0[3]}, {ML.get(d0[3])}{ML.get(d0[3])}, {ID.get(d0[3])}{ID.get(d0[3])}",
        "bbfs": " ".join(sorted(bbfs))
    }

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    m_code = TARGET_POOLS.get(m_name)
    all_res = fetch_results(m_code)
    if not all_res: return jsonify({"error": "Sinkronisasi Gagal"}), 500
    data = get_v8_analysis(all_res)
    return jsonify({"status":"success", "market":m_name, "last":all_res[0], "weekly":all_res[7], "data":data})

if __name__ == '__main__':
    app.run(debug=True)
