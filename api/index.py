import os, re, httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V7_3_FIXED"

# --- DATABASE POLA ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}

TARGET_POOLS = {
    'CAMBODIA': 'p3501', 
    'SYDNEY LOTTO': 'p2262', 
    'HONGKONG LOTTO': 'p2263',
    'HONGKONG POOLS': 'kia_hk', # Flag khusus HK
    'SINGAPORE POOLS': 'kia_sgp', 
    'SYDNEY POOLS': 'kia_sdy'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            # Menggunakan URL yang sesuai dengan bukti gambar tabel rekap
            url = "https://nomorkiajit.com/hksgpsdy"
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table')
            rows = table.find_all('tr')
            
            # Penentuan Index Kolom berdasarkan Struktur Tabel di Gambar image_e1ef2a.png
            # Index 2 = HK, Index 3 = SGP, Index 4 = SDY
            col_idx = 2 if 'hk' in market_code else (3 if 'sgp' in market_code else 4)
            
            for row in rows:
                tds = row.find_all('td')
                if len(tds) > col_idx:
                    raw_val = tds[col_idx].text.strip()
                    # Menghapus karakter non-angka dan memastikan panjang 4 digit
                    val = re.sub(r'\D', '', raw_val)
                    if len(val) == 4:
                        results.append(val)
    except Exception as e:
        print(f"Error Fetching: {e}")
    return results

def get_v7_analysis(all_res):
    if len(all_res) < 8: return None
    last = all_res[0]    # Target: 7445
    weekly = all_res[7]  # Target: 4223
    
    # BBFS 6-DIGIT (Frequency Analysis)
    counts = Counter("".join(all_res[:15]))
    bbfs_6 = sorted([x[0] for x in counts.most_common(6)])
    
    # CORE 2D AUTO-BB
    # Rumus: [Ekor Last + Ekor Weekly] & [Mistik Index Ekor Last]
    c1 = last[3] + weekly[3]
    c2 = ID.get(last[3]) + last[2]
    core_raw = list(dict.fromkeys([c1, c1[::-1], c2, c2[::-1]]))
    
    # TWIN DETECTION (Urgensi Tinggi jika result terakhir Twin)
    # Hasil 7445 memiliki twin belakang '45' (bukan twin identik tapi berpola)
    # Namun 4223 memiliki twin tengah '22'
    is_twin = (last[2] == last[3]) or (weekly[1] == weekly[2])
    
    return {
        "core": ", ".join(core_raw[:6]),
        "shadow": ", ".join([ID.get(last[2])+ID.get(last[3]), ML.get(last[3])+ID.get(last[3])]),
        "depan": last[0] + ID.get(last[1]),
        "tengah": last[1] + ML.get(last[2]),
        "twin_status": "WASPADA TWIN" if is_twin else "NORMAL",
        "twin_picks": f"{last[3]}{last[3]}, {weekly[2]}{weekly[2]}, 11, 77",
        "bbfs": " ".join(bbfs_6)
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
    m_name = request.form.get('market')
    m_code = TARGET_POOLS.get(m_name)
    all_res = fetch_results(m_code)
    if not all_res: return jsonify({"error": "Data Kolom Tidak Ditemukan"})
    data = get_v7_analysis(all_res)
    return jsonify({"market": m_name, "last": all_res[0], "weekly": all_res[7], "data": data})

if __name__ == '__main__':
    app.run(debug=True)
