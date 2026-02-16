import os, re, httpx
from flask import Flask, render_template, request, jsonify, session
from collections import Counter

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V7_11_LOCKED_PATTERNS"

# --- DATABASE POLA LENGKAP (TIDAK BOLEH DIUBAH) ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'} # Mistik Lama
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'} # Mistik Baru
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'} # Index
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'} # Taysen

# SHIO MACAU & SHIO JALUR 2026
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

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=30.0, verify=False) as client:
            if market_code.startswith('kia_'):
                # Scraping khusus KIA (Pools)
                url = "https://nomorkiajit.com/hksgpsdy"
                r = client.get(url)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'html.parser')
                col_map = {'kia_hk': 2, 'kia_sgp': 3, 'kia_sdy': 4}
                idx = col_map.get(market_code)
                table = soup.find('table')
                rows = table.find_all('tr')
                for row in rows[1:]:
                    tds = row.find_all('td')
                    if len(tds) > idx:
                        val = re.sub(r'\D', '', tds[idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                # Logika JSON Salamrupiah (Lotto/Cambodia)
                url = f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
                r = client.get(url)
                data_json = r.json()
                for item in data_json['angka_keluar']['data']:
                    val = item.get('angka') # Ambil angka 0946 dkk
                    if val and len(val) == 4:
                        results.append(val)
    except: pass
    return results

def get_v7_analysis(all_res):
    if not all_res or len(all_res) < 8: return None
    last = all_res[0]    # Result Terakhir
    prev = all_res[1]    # Result Sebelumnya
    weekly = all_res[7]  # Result Minggu Lalu
    
    # 1. POLA 2D BELAKANG (Core V7.3 Logic)
    # Kombinasi Mistik Lama & Taysen dari Ekor
    c1 = ML.get(last[3], '0') + TY.get(last[3], '0')
    # Kombinasi Index & Mistik Baru dari Kepala/Ekor
    c2 = ID.get(last[3], '0') + MB.get(last[2], '0')
    # Jalur Cross (Ekor Last vs Ekor Weekly)
    c3 = last[3] + weekly[3]
    
    core_raw = list(dict.fromkeys([c1, c1[::-1], c2, c2[::-1], c3, c3[::-1]]))
    
    # 2. POLA DEPAN & TENGAH (Locked)
    depan = last[0] + ID.get(last[1], '0')
    tengah = last[1] + ML.get(last[2], '0')
    
    # 3. SHIO & SHIO MACAU
    shio_val = int(last[2:]) % 12
    main_shio = SHIO_MAP.get(shio_val, "N/A")
    macau_shio = f"{main_shio} - {SHIO_MAP.get((shio_val+1)%12)}" # Shio Macau (Main + Next)
    
    # 4. BBFS 7-DIGIT (Frequency Analysis 20 Hari)
    counts = Counter("".join(all_res[:20]))
    bbfs = [x[0] for x in counts.most_common(7)]
    
    return {
        "core": ", ".join(core_raw[:8]),
        "shadow": ", ".join([TY.get(last[2], '0')+TY.get(last[3], '0'), MB.get(last[2], '0')+MB.get(last[3], '0')]),
        "depan": depan,
        "tengah": tengah,
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
    if not all_res: return jsonify({"error": "Gagal Tarik Data"})
    data = get_v7_analysis(all_res)
    return jsonify({
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
