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
    'PHUKET':'p28435', 'WUHAN':'p28615','MACAU 4D':'MACAU_TRIGGER','OREGON 3':'p12521'
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
def get_refined_bbfs(all_res, limit=30):
    full_data = "".join(all_res[:limit])
    counts = Counter(full_data)
    sorted_chars = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_chars[:6]]
# --- [LOGIC BRANCHING - TIDAK DISENTUH] ---
def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    is_big = m_name in ['SYDNEY POOLS']
    bbfs = get_engine_analytics(all_res, is_big)
    line = [TY.get(d0[2], '0')+d0[3], ML.get(d0[2], '0')+ID.get(d0[1], '0')]
    
    if m_name == "OSAKA":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=30)
        l1 = ML.get(d0[0], '0') + ID.get(d0[3], '0')
        l2 = TY.get(d0[2], '0') + MB.get(d0[1], '0')
        if l2[0] == l2[1]: l2 = l2[0] + TY.get(l2[0], '1')
        selisih = str(abs(int(d0[0]) - int(d0[3])))
        l3 = MB.get(selisih, '0') + bbfs[0]
        l4 = d0[1] + d0[2]
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "10"]))
        return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + MB.get(d0[1], '0'),
        "kop_kep": TY.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"11, {bbfs[0]}{bbfs[0]}" # Antisipasi twin 11 setelah 55
    }
    elif m_name == "OREGON 3":
        ganjil_count = sum(1 for x in d0 if int(x) % 2 != 0)
        gap_ai = str(abs(int(d0[0]) - int(d0[3])))
        mb_kop = MB.get(d0[1], '0')
        full_data = "".join(all_res[:40])
        counts = Counter(full_data)
        sorted_chars = sorted(counts.items(), key=lambda x: x[1])
        bbfs_oregon = [x[0] for x in sorted_chars[2:8]]
        if gap_ai not in bbfs_oregon: bbfs_oregon[0] = gap_ai
        l1 = ID.get(d0[2], '0') + TY.get(d0[3], '0') 
        l2 = mb_kop + d0[0]
        l3 = "46" if ganjil_count >= 3 else "15"
        l4 = gap_ai + ML.get(d0[3], '0')
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "28", "70"]))

        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs_oregon)),
            "as_kop": MB.get(d0[0], '0') + ID.get(d0[1], '0'),
            "kop_kep": TY.get(d0[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
            "twin": "44, 22, 88" if ganjil_count >= 3 else f"{d0[3]}{d0[3]}, 00"
        }
    elif m_name == "PENANG":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=40)
        l1 = TY.get(d0[2], '0') + MB.get(d0[3], '0')
        l2 = ID.get(d0[0], '0') + ML.get(d0[1], '0')
        l3 = d0[2] + ID.get(d0[3], '3')
        l4 = "19" if "1" in bbfs else "37"
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "48", "84"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs)),
            "as_kop": MB.get(d0[0], '0') + TY.get(d0[1], '0'),
            "kop_kep": ID.get(d0[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
            "twin": f"00, 33, 55" # Antisipasi twin baru setelah pola sandwich 8-4-8
        }
    elif m_name == "SINGAPORE POOLS":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=55)
        l1 = ID.get(d0[2], '0') + MB.get(d0[3], '0')
        l2 = TY.get(d0[0], '0') + ML.get(d0[2], '0')
        l3 = "9" + bbfs[0] if "9" in bbfs else "7" + bbfs[0]
        l4 = d0[3] + d0[2]
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "86"]))
        return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs[:6])),
        "as_kop": MB.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": TY.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"66, 00" # Twin 11 biasanya memancing twin 66 atau 00
    }
    elif m_name == "DANANG":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=45)
        l1 = MB.get(d0[1], '1') + TY.get(d0[3], '7')
        l2 = ID.get(d0[0], '0') + ML.get(d0[2], '5')
        selisih_tengah = str(abs(int(d0[1]) - int(d0[2])))
        l3 = bbfs[0] + MB.get(selisih_tengah, '4')
        l4 = "94" if "9" in bbfs else "41"
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "71", "49"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs)),
            "as_kop": TY.get(d0[0], '0') + ML.get(d0[1], '4'),
            "kop_kep": ID.get(d0[1], '2') + MB.get(d0[2], '6'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
            "twin": f"11, 44, 77" # Danang sering keluarkan twin ganjil setelah JP 4D
        }
    elif m_name == "SAPPORO":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=40)
        l1 = ML.get(d0[1], '0') + TY.get(d0[3], '5')
        l2 = ID.get(d0[0], '0') + MB.get(d0[2], '7')
        if l2[0] == l2[1]: l2 = l2[0] + ID.get(l2[1], '2')
        l3 = bbfs[0] + bbfs[2]
        l4 = d0[2] + ID.get(d0[0], '7')
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "18"]))
        return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": TY.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": MB.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"{d0[2]}{d0[2]}, {bbfs[0]}{bbfs[0]}"
    }
    elif m_name == "SEOUL":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=35)
        l1 = ID.get(d0[3], '0') + ML.get(d0[2], '1')
        l2 = TY.get(d0[1], '0') + bbfs[0]
        l3 = MB.get(d0[0], '0') + MB.get(d0[3], '0')
        l4 = "0" + ID.get(d0[3], '8')
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "03"]))
        return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": MB.get(d0[0], '0') + ID.get(d0[1], '0'),
        "kop_kep": TY.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"33, {bbfs[0]}{bbfs[0]}" # Antisipasi twin pindah ke belakang
    }
    elif m_name == "JEJU":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=40)
        l1 = TY.get(d0[2], '0') + MB.get(d0[3], '0')
        l2 = ID.get(d0[1], '0') + ML.get(d0[0], '0')
        l3 = bbfs[0] + bbfs[1]
        l4 = d0[3] + ID.get(d0[3], '5')
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "10"]))
        return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": ID.get(d0[0], '0') + TY.get(d0[1], '0'),
        "kop_kep": MB.get(d0[1], '0') + ML.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"{d0[3]}{d0[3]}, {bbfs[0]}{bbfs[0]}"
    }
    elif m_name == "TORONTOMID": 
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=35)
        if '1' not in bbfs: bbfs.append('1')
        l1 = TY.get(d0[2], '0') + MB.get(d0[3], '0')
        l2 = ML.get(d0[0], '0') + ID.get(d0[1], '0')
        l3 = "02" if "0" in bbfs else "39"
        l4 = d0[3] + d0[2]
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "42", "72"]))
        return {
        "core": ", ".join(core_lines[:5]),
        "bbfs": " ".join(sorted(bbfs[:6])), # Batasi tetap 6 digit
        "as_kop": TY.get(d0[0], '0') + TY.get(d0[1], '0'), # Antisipasi twin lagi
        "kop_kep": ID.get(d0[1], '0') + MB.get(d0[2], '0'),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"{d0[0]}{d0[0]}, 11" # Fokus twin 22 atau 11
    }
    elif m_name == "HONGKONG LOTTO":
        d0 = all_res[0]
        d1 = all_res[1]
        bbfs = get_refined_bbfs(all_res, limit=50)
        l1 = TY.get(d0[1], '0') + ML.get(d0[2], '0')
        l2 = ID.get(d0[0], '0') + MB.get(d0[3], '0')
        l3 = d0[2] + d1[3]
        l4 = "05" if "0" in bbfs else "50"
        if MB.get(d0[3]) not in bbfs: bbfs.append(MB.get(d0[3]))
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "15", "51", "84"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(list(set(bbfs[:7])))), # BBFS 7 Digit lebih aman
            "as_kop": MB.get(d0[0], '0') + ID.get(d0[1], '0'),
            "kop_kep": TY.get(d0[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
            "twin": f"55, 00, 11"
        }
    elif m_name == "HONGKONG POOLS":
        d0 = all_res[0]
        bbfs = get_refined_bbfs(all_res, limit=60)
        l1 = ML.get(d0[3], '0') + TY.get(d0[0], '0')
        l2 = ID.get(d0[1], '0') + MB.get(d0[2], '0')
        l3 = d0[1] + ID.get(d0[3], '0') 
        l4 = "29" if "2" in bbfs else "40"
        if "0" not in bbfs: bbfs.append("0")
        
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "75", "15"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(list(set(bbfs[:7])))),
            "as_kop": TY.get(d0[0], '0') + ML.get(d0[1], '0'),
            "kop_kep": ID.get(d0[1], '0') + MB.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
            "twin": f"99, 66, 00"
        }
    elif m_name == "CAMBODIA":
        d0 = all_res[0]
        d1 = all_res[1] if len(all_res) > 1 else d0
        jalur_main = ID.get(d0[0]) + ML.get(d0[3])
        jalur_bom = TY.get(d0[1]) + ID.get(d0[2])
        cadangan_presisi = d0[3] + TY.get(d0[3])
        line.extend([jalur_main, jalur_bom, cadangan_presisi, d1[2]+d0[3]])
    elif m_name == "SYDNEY LOTTO":
        d0 = all_res[0]
        d1 = all_res[1]
        bbfs = get_refined_bbfs(all_res, limit=45)
        line1 = TY.get(d0[3], '0') + ML.get(d0[2], '0')
        line2 = ID.get(d0[0], '0') + d1[3]
        selisih_idx = ID.get(str(abs(int(d0[1]) - int(d0[2]))), '0')
        line3 = selisih_idx + bbfs[0]
        line4 = "54" if "5" in bbfs else "58"
        core_lines = list(dict.fromkeys([line1, line2, line3, line4, "12", "37"]))
        askop_final = MB.get(d0[0], '0') + ID.get(d0[1], '0')
        kopkep_final = TY.get(d0[1], '0') + ML.get(d0[2], '0')
        return {
        "core": ", ".join(core_lines[:5]), # Ambil 5 line terbaik
        "bbfs": " ".join(sorted(bbfs)),
        "as_kop": askop_final,
        "kop_kep": kopkep_final,
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
        "twin": f"{d0[3]}{d0[3]}, {bbfs[0]}{bbfs[0]}"
    }
    elif m_name == "PHUKET":
        d0 = all_res[0]
        bbfs = get_engine_analytics(all_res, is_big=False)
        l1 = ID.get(d0[2], '0') + ML.get(d0[3], '0')
        l2 = TY.get(d0[0], '0') + MB.get(d0[1], '0')
        l3 = "0" + bbfs[0]
        l4 = "71" if "7" in bbfs else "12"
        core_lines = list(dict.fromkeys([l1, l2, l3, l4, "17"]))
        return {
            "core": ", ".join(core_lines[:5]),
            "bbfs": " ".join(sorted(bbfs)),
            "as_kop": TY.get(d0[0], '0') + ID.get(d0[1], '0'),
            "kop_kep": MB.get(d0[1], '0') + ML.get(d0[2], '0'),
            "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
            "macau": f"{SHIO_MAP.get(int(d0[2:]) % 12)} - {SHIO_MAP.get((int(d0[2:]) % 12 + 6) % 12)}",
            "twin": f"{d0[1]}{d0[1]}, {bbfs[0]}{bbfs[0]}"
        }
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

# --- [ROUTE ANALYZE - FIX TOTAL] ---
@app.route('/analyze', methods=['POST'])
def analyze():
    # Perbaikan 1: Inisialisasi results di awal agar tidak UnboundLocalError
    results = [] 
    try:
        market = request.form.get('market')
        if not market: return jsonify({"status": "error", "msg": "Pilih Pasaran"}), 400

        # Perbaikan 2: Percabangan Terpisah untuk MACAU vs Pasaran Lain
        if market == "MACAU 4D":
            from .macau import fetch_macau_m17, calculate_macau_prediction 
            results = fetch_macau_m17()
            if not results: 
                return jsonify({"status": "error", "msg": "Sync Macau Gagal"}), 500
            data = calculate_macau_prediction(results)
            return jsonify({"status": "success", "market": "MACAU 4D (M17)", "last": results[0], "data": data})

        else:
            # Pasaran Normal
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
