import os, re, httpx
from flask import Flask, render_template, request, jsonify, session
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))
app.secret_key = "MAMANG_V7_2_FINAL"

# --- DATABASE POLA (MISTIK & TAYSEN) ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}

# KONFIGURASI MARKET & SOURCE
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 
    'SYDNEY LOTTO': 'p2262', 
    'HONGKONG LOTTO': 'p2263',
    'OREGON 03': 'p12521',
    'HONGKONG POOLS': 'kia_2', 
    'SINGAPORE POOLS': 'kia_3', 
    'SYDNEY POOLS': 'kia_4'
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_results(code):
    """
    TEKNIK PENGAMBILAN DATA:
    - KIA Source: Menggunakan scrapping pada Nomorkia (Base HK/SGP/SDY Pools).
    - SL Source: Menggunakan API/HTML parsing pada Salamrupiah (Base Lotto).
    """
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            url = "https://nomorkiajit.com/hksgpsdy" if code.startswith('kia_') else f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1"
            
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            # Seleksi baris tabel berdasarkan pola struktur sumber data
            rows = soup.select('tbody tr') or soup.select('table tr')
            
            for row in rows[:35]:
                tds = row.find_all('td')
                for td in tds:
                    val = re.sub(r'\D', '', td.text.strip())
                    if len(val) == 4: 
                        results.append(val)
                        break
    except Exception as e:
        print(f"Error Sync: {e}")
    return results

def get_v7_analysis(all_res, market):
    """
    TEKNIK ANALISA:
    1. Weekly Cross-Sync: Membandingkan Result Hari Ini dengan 7 Hari Lalu.
    2. Frequency Weighting: Mengambil 6 digit paling sering muncul (Hot Digits) untuk BBFS.
    3. Inverse Core Logic: Menghasilkan angka 2D dari persilangan Kepala Harian & Ekor Mingguan.
    """
    if len(all_res) < 8: return None
    last = all_res[0]
    weekly = all_res[7]
    
    # BBFS 6-DIGIT (Proteksi Angka Hantu)
    # Menghitung frekuensi kemunculan angka dari 15 result terakhir
    counts = Counter("".join(all_res[:15]))
    bbfs_6 = sorted([x[0] for x in counts.most_common(6)])
    
    # CORE 2D AUTO-BB (Bolak Balik Otomatis)
    # Logika: [Ekor Kemarin + Ekor Minggu Lalu] & [Mistik Kepala + Ekor Kemarin]
    raw_1 = last[2] + weekly[3]
    raw_2 = ID.get(last[2]) + last[3]
    core_list = list(dict.fromkeys([raw_1, raw_1[::-1], raw_2, raw_2[::-1]]))
    
    # TWIN DETECTOR (Urgensi Tinggi)
    # Menganalisa jika As atau Kop memiliki kesamaan indeks dengan result sebelumnya
    is_twin = (last[0] == weekly[0]) or (last[3] == weekly[3]) or (last[2] == last[3])
    
    return {
        "core": ", ".join(core_list[:6]),
        "shadow": ", ".join([ID.get(last[2])+ID.get(last[3]), TY.get(last[2])+TY.get(last[3])]),
        "depan": last[0] + ID.get(last[1]),
        "tengah": last[1] + ML.get(last[2]),
        "twin_status": "SANGAT WASPADA" if is_twin else "NORMAL (CADANGAN)",
        "twin_picks": f"{last[3]}{last[3]}, {weekly[3]}{weekly[3]}, 00, 44",
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
    market = request.form.get('market')
    all_res = fetch_results(TARGET_POOLS.get(market))
    if not all_res: return jsonify({"error": "Gagal sinkronisasi. Coba lagi."})
    data = get_v7_analysis(all_res, market)
    return jsonify({"market": market, "last": all_res[0], "weekly": all_res[7], "data": data})

if __name__ == '__main__':
    app.run(debug=True)
