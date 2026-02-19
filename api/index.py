import os, re, httpx, datetime
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

# PENTING: Import macau dipindahkan ke dalam fungsi analyze untuk mencegah Error 500 saat startup
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
    'HONGKONG POOLS': 'HK_SPECIAL', 'SINGAPORE POOLS': 'p2264', 'SYDNEY POOLS': 'sydney',
    'BUSAN POOLS':'p16063', 'OSAKA':'p28422', 'JEJU':'p22815', 'DANANG':'p22816',
    'PENANG':'p22817', 'SEOUL':'p28502', 'TORONTOMID':'p13976', 'SAPPORO':'p22814',
    'PHUKET':'p28435', 'WUHAN':'p28615','MACAU 4D':'MACAU_TRIGGER','OREGON 3':'p12521',
    'WASHING-MID': 'p24508','MIAMI-MID':'p24488'
}

# --- [CORE ENGINE V10.0 - PENAJAMAN ANALISA] ---
def get_historical_gap(all_res, gap_day):
    """Mengambil angka dari result n-hari kebelakang untuk deteksi replay"""
    if len(all_res) > gap_day:
        return all_res[gap_day]
    return all_res[-1]

def get_engine_analytics(all_res, is_big=False):
    d0 = all_res[0]
    limit = 60 if is_big else 35
    full_data = "".join(all_res[:limit])
    counts_full = Counter(full_data)
    scores = {n: counts_full.get(n, 0) for n in "0123456789"}
    for n in "0123456789":
        for i, res in enumerate(all_res[:20]):
            if n in res:
                scores[n] += (20 - i) # Penajaman: Score berdasarkan kedekatan hari
                break
    scores[TY.get(d0[0], '0')] += 15 
    scores[ML.get(d0[1], '0')] += 10
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_scores[:6]]

def get_refined_bbfs(all_res, limit=30):
    full_data = "".join(all_res[:limit])
    counts = Counter(full_data)
    sorted_chars = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    # V10 Update: Ambil 4 terkuat + 2 angka dingin (jarang keluar) untuk menutup peluang
    top_4 = [x[0] for x in sorted_chars[:4]]
    bottom_2 = [x[0] for x in sorted_chars[-2:]]
    return list(dict.fromkeys(top_4 + bottom_2))

# --- [LOGIC BRANCHING] ---
def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    d1 = get_historical_gap(all_res, 1) # Kemarin
    d7 = get_historical_gap(all_res, 7) # Minggu lalu
    
    is_big = m_name in ['SYDNEY POOLS', 'SINGAPORE POOLS', 'HONGKONG POOLS', 'CAMBODIA']
    bbfs = get_engine_analytics(all_res, is_big)
    line = [TY.get(d0[2], '0')+d0[3], ML.get(d0[2], '0')+ID.get(d0[1], '0')]
    
    if m_name == "OSAKA":
        bbfs_os = get_refined_bbfs(all_res, limit=30)
        l1 = ML.get(d0[0], '0') + ID.get(d0[3], '0')
        l2 = d0[1] + d1[2] # Pola geser tengah
        l3 = TY.get(d0[2], '0') + MB.get(d0[1], '0')
        if l2[0] == l2[1]: l2 = l2[0] + TY.get(l2[0], '1')
        core_lines = list(dict.fromkeys([l1, l2, l3, "23", "10"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs_os)),
            "as_kop": ID.get(d0[0], '0') + MB.get(d0[1], '0'),
            "kop_kep": TY.get(d1[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{d0[0]} - {d0[3]}",
            "twin": f"11, {bbfs_os[0]}{bbfs_os[0]}"
        }

    elif m_name == "OREGON 3":
        ganjil_count = sum(1 for x in d0 if int(x) % 2 != 0)
        gap_ai = str(abs(int(d0[0]) - int(d0[3])))
        mb_kop = MB.get(d0[1], '0')
        bbfs_oregon = get_refined_bbfs(all_res, limit=40)
        
        l1 = ID.get(d0[2], '0') + TY.get(d0[3], '0') 
        l2 = mb_kop + d0[0]
        l3 = gap_ai + ML.get(d0[3], '0')
        l4 = d7[3] + d0[3] # Tarikan mingguan
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "28", "70"]))

        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs_oregon)),
            "as_kop": MB.get(d0[0], '0') + ID.get(d0[1], '0'),
            "kop_kep": TY.get(d0[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{gap_ai} - {d0[3]}",
            "twin": "44, 22, 88" if ganjil_count >= 3 else f"{d0[3]}{d0[3]}, 00"
        }

    elif m_name == "PENANG":
        bbfs_pe = get_refined_bbfs(all_res, limit=40)
        l1 = TY.get(d0[2], '0') + MB.get(d0[3], '0')
        l2 = ID.get(d7[0], '0') + ML.get(d0[1], '0') # Analisa Gap 7 hari
        l3 = d0[2] + ID.get(d0[3], '3')
        core_lines = list(dict.fromkeys([l1, l2, l3, "51", "88", "43"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs_pe)),
            "as_kop": MB.get(d0[0], '0') + TY.get(d0[1], '0'),
            "kop_kep": ID.get(d0[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{d0[3]} - {d7[2]}",
            "twin": f"88, 55, 33"
        }

    elif m_name == "CAMBODIA":
        l1 = ID.get(d0[0]) + ML.get(d0[3])
        l2 = TY.get(d1[2]) + d0[3]
        l3 = str((int(d0[2]) + int(d7[2])) % 10) + d0[3] # Replay Mingguan
        core_lines = list(dict.fromkeys([l1, l2, l3, "41", "87", "70"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs)),
            "as_kop": ID.get(d0[0]) + ML.get(d0[1]),
            "kop_kep": TY.get(d0[1]) + d0[2],
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{d0[2]} - {d7[3]}",
            "twin": f"{d0[3]}{d0[3]}, 55"
        }

    elif "HONGKONG" in m_name:
        bbfs_hk = get_refined_bbfs(all_res, limit=55)
        l1 = ML.get(d0[3], '0') + TY.get(d0[0], '0')
        l2 = ID.get(d1[1], '0') + MB.get(d0[2], '0')
        l3 = d7[3] + d0[3]
        core_lines = list(dict.fromkeys([l1, l2, l3, "15", "98", "05"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs_hk)),
            "as_kop": TY.get(d0[0], '0') + ML.get(d0[1], '0'),
            "kop_kep": ID.get(d0[1], '0') + MB.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{d0[1]} - {d1[3]}",
            "twin": "00, 55, 99"
        }

    # --- FALLBACK UNTUK PASARAN LAIN (WUHAN, BUSAN, SEOUL, DLL) ---
    shio_idx = int(d0[2:]) % 12
    l_gen1 = TY.get(d0[2]) + d0[3]
    l_gen2 = ML.get(d1[1]) + ID.get(d0[2])
    core_lines = list(dict.fromkeys([l_gen1, l_gen2, d7[2]+d0[3]] + line))
    
    return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": ML.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{SHIO_MAP.get(shio_idx)} - {d0[3]}",
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

# --- [ROUTE ANALYZE - FIX TOTAL] ---
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        market = request.form.get('market')
        if not market: return jsonify({"status": "error", "msg": "Pilih Pasaran"}), 400

        if market == "MACAU 4D":
            from .macau import fetch_macau_m17, calculate_macau_prediction 
            results = fetch_macau_m17()
            if not results: 
                return jsonify({"status": "error", "msg": "Sync Macau Gagal"}), 500
            data = calculate_macau_prediction(results)
            return jsonify({"status": "success", "market": "MACAU 4D (M17)", "last": results[0], "data": data})

        else:
            market_code = TARGET_POOLS.get(market)
            if not market_code: return jsonify({"status": "error", "msg": "Kode Pasaran Hilang"}), 400
            
            results = fetch_results(market_code)
            if not results: return jsonify({"status": "error", "msg": f"Gagal Sinkronisasi {market}"}), 500
            
            data = get_comprehensive_logic(results, market)
            return jsonify({"status": "success", "market": market, "last": results[0], "data": data})
    
    except Exception as e:
        return jsonify({"status": "error", "msg": f"Sistem Crash: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

app_handler = app
