import os, re, httpx
from flask import Flask, render_template, request, jsonify, session
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V7_14_HTML_FIX"

# --- DATABASE POLA LENGKAP (LOCKED - JANGAN DIUBAH) ---
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False, headers=HEADERS, follow_redirects=True) as client:
            if market_code.startswith('kia_'):
                # JALUR KIA (NOMORKIAJIT)
                url = "https://nomorkiajit.com/hksgpsdy"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                col_map = {'kia_hk': 2, 'kia_sgp': 3, 'kia_sdy': 4}
                idx = col_map.get(market_code)
                table = soup.find('table')
                if table:
                    for row in table.find_all('tr')[1:]:
                        tds = row.find_all('td')
                        if len(tds) > idx:
                            val = re.sub(r'\D', '', tds[idx].text.strip())
                            if len(val) == 4: results.append(val)
            else:
                # JALUR SALAMRUPIAH HTML (URL RESULT-MOBILE)
                url = f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
                r = client.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Cari tabel dengan class legend
                table = soup.find('table', class_='table-history')
                if table:
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            # Ambil text dari tag <a> di kolom ke-4 (index 3)
                            link_val = tds[3].find('a')
                            if link_val:
                                val = re.sub(r'\D', '', link_val.text.strip())
                                if len(val) == 4:
                                    results.append(val)
    except Exception as e:
        print(f"Error Fetching: {e}")
    return results

def get_v7_analysis(all_res):
    if not all_res or len(all_res) < 8: return None
    last = all_res[0]    # 0946
    weekly = all_res[7]  # Angka 7 hari lalu
    
    # POLA V7.3 KUNCI MATI (ML, MB, ID, TY)
    c1 = ML.get(last[3], '0') + TY.get(last[3], '0')
    c2 = ID.get(last[3], '0') + MB.get(last[2], '0')
    c3 = last[3] + weekly[3]
    core_raw = list(dict.fromkeys([c1, c1[::-1], c2, c2[::-1], c3, c3[::-1]]))
    
    # Shio & Shio Macau
    shio_val = int(last[2:]) % 12
    main_shio = SHIO_MAP.get(shio_val, "N/A")
    macau_shio = f"{main_shio} - {SHIO_MAP.get((shio_val+1)%12)}"
    
    # BBFS & Pola Depan/Tengah
    counts = Counter("".join(all_res[:20]))
    bbfs = [x[0] for x in counts.most_common(7)]
    
    return {
        "core": ", ".join(core_raw[:8]),
        "shadow": f"{TY.get(last[2], '0')}{TY.get(last[3], '0')}, {MB.get(last[2], '0')}{MB.get(last[3], '0')}",
        "depan": last[0] + ID.get(last[1], '0'),
        "tengah": last[1] + ML.get(last[2], '0'),
        "shio": main_shio,
        "macau": macau_shio,
        "twin": f"{last[3]}{last[3]}, {ML.get(last[3], '0')}{ML.get(last[3], '0')}, {ID.get(last[3], '0')}{ID.get(last[3], '0')}",
        "bbfs": " ".join(sorted(bbfs))
    }

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    m_code = TARGET_POOLS.get(m_name)
    all_res = fetch_results(m_code)
    
    if not all_res:
        return jsonify({"error": f"Gagal Sinkron Data {m_name}. Coba Lagi."}), 500
        
    data = get_v7_analysis(all_res)
    return jsonify({
        "status": "success",
        "market": m_name, 
        "last": all_res[0], 
        "weekly": all_res[7] if len(all_res)>7 else "N/A", 
        "data": data
    })

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()), logged_in=session.get('authorized'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('key') == "MAMANG2026":
        session['authorized'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 401

if __name__ == '__main__':
    app.run(debug=True)
