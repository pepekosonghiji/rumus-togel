import os
from flask import Flask, render_template, request
import re
import httpx
import itertools
from collections import Counter
from bs4 import BeautifulSoup

# Setup template directory
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')
app = Flask(__name__, template_folder=template_dir)

# --- [DATABASE MASTER POLA ABADI] ---
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
MB = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '5':'4', '6':'2', '7':'1', '8':'0', '9':'3'}
SHIO_MAP = {
    1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 
    7:"KELINCI", 8:"NAGA", 9:"ULAR", 10:"KUDA", 11:"KAMBING", 0:"MONYET"
}

TARGET_POOLS = {
    'BEIJING': 'p24492', 'BUSAN POOLS':'p16063', 'CAMBODIA': 'p3501', 
    'DANANG':'p22816', 'HONGKONG LOTTO': 'p2263', 'HONGKONG POOLS': 'HK_SPECIAL',
    'JEJU':'p22815', 'MIAMI-MID':'p24488', 'MONTANA':'p23588', 'OREGON 12':'p12524',
    'OREGON 3':'p12521', 'OREGON 6':'p12522', 'OREGON 9':'p12523', 'OSAKA':'p28422',
    'PENANG':'p22817', 'PHUKET':'p28435', 'SAPPORO':'p22814', 'SEOUL':'p28502',
    'SINGAPORE POOLS': 'p2264', 'SYDNEY LOTTO': 'p2262', 'TORONTOMID':'p13976',
    'WASHINGMID':'p24508', 'WUHAN':'p28615', 'MACAU': 'm17','GREECE':'p8584',
    'MANHATTAN':'p23590','TORONTOEVE':'p13975','ORLANDO':'p21384','COLORADO':'p23589'
}

# --- [V14.1 ENGINE - SHADOW DATA & PRECISION TARGETING] ---

def get_weighted_bbfs_v14_1(all_res_data, market_name):
    """
    all_res_data: list of lists [[p1, p2, p3], ...]
    """
    scores = {str(n): 0 for n in range(10)}
    p1_history = [res[0] for res in all_res_data]
    d0_p1 = p1_history[0]
    
    # --- 1. FREKUENSI & SHADOW WEIGHTING ---
    freq_p1 = Counter("".join(p1_history[:30]))
    for n in "0123456789":
        # Skor Prize 1 (Utama)
        scores[n] += freq_p1.get(n, 0) * 1.5
        # Repeat Number Protection
        if n in d0_p1: scores[n] += 15
    
    # Bonus dari Prize 2 & 3 (Shadow Data)
    for res in all_res_data[:10]:
        if len(res) > 1:
            shadow = "".join(res[1:])
            for n in set(shadow): scores[n] += 5

    # --- 2. CLUSTER SUB-LOGIC ---
    if market_name == 'WASHINGMID':
        if len(all_res_data) > 2:
            d2 = all_res_data[2][0] # Prize 1 dari 2 periode lalu
            for digit in d2: scores[digit] += 18
        # Verifikasi vibrasi angka tengah terakhir
        scores[ID.get(d0_p1[1], '0')] += 22
        scores[TY.get(d0_p1[2], '0')] += 20

    elif market_name == 'CAMBODIA':
        # --- CAMBODIA ELITE SUB-LOGIC V14.6 ---
        # 1. Lindungi Angka Indeks/Mirror dari P1, P2, P3 (Anti-Meleset)
        all_p_digits = "".join([res[0] for res in all_res_data[:1]]) 
        if len(all_res_data[0]) > 2:
            all_p_digits += all_res_data[0][1] + all_res_data[0][2]
            
        for digit in set(all_p_digits):
            scores[ID.get(digit)] += 28  # Indeks punya bobot tertinggi di Cambodia
            scores[ML.get(digit)] += 18  # Mistik Lama sebagai cadangan
            
        # 2. Analisa Selisih (Delta) Kepala-Ekor
        # Pola Cambodia sering muncul dari selisih P1 periode sebelumnya
        d_kep = int(d0_p1[2])
        d_eko = int(d0_p1[3])
        delta = str(abs(d_kep - d_eko))
        scores[delta] += 30
        scores[TY.get(delta, '0')] += 20 # Tyseen dari selisih
    
    elif market_name == 'MACAU':
        scores[str((int(d0_p1[3]) + 1) % 10)] += 15
        scores[str((int(d0_p1[3]) - 1) % 10)] += 15
        scores[ID.get(d0_p1[1], '0')] += 10 

    elif market_name == 'SYDNEY LOTTO':
        # --- SYDNEY ELITE HYBRID LOGIC V14.7 (COMBINED) ---
        
        # 1. Pola Angka Tetangga & Lompat (Neighboring & Skip-Two)
        # Menangkap pergerakan angka +/- 1 dan +/- 2 dari P1 terakhir
        for digit in d0_p1:
            val = int(digit)
            scores[str((val + 1) % 10)] += 22 # Tetangga
            scores[str((val - 1) % 10)] += 22
            scores[str((val + 2) % 10)] += 20 # Lompat 2 (V14.7 Update)
            scores[str((val - 2) % 10)] += 20
            
        # 2. Resonansi Mistik & Mirror (MB & ID)
        # Sydney sangat sensitif terhadap bayangan angka (seperti 72 yang muncul tadi)
        for digit in d0_p1:
            scores[MB.get(digit, '0')] += 25 # Mistik Baru (Sub-Logic Lama)
            scores[ID.get(digit, '0')] += 30 # Mirror/Indeks (V14.7 Update - Menangkap 7 & 2)
            
        # 3. Analisa Angka "Dingin" & Middle-Range
        # Mengincar angka yang jarang keluar + angka tengah (2-7)
        p1_short = "".join([res[0] for res in all_res_data[:5]])
        for n in "0123456789":
            if n not in p1_short:
                scores[n] += 30 # Cold Number Power
            if n in "234567":
                scores[n] += 15 # Sydney Middle-Range Priority
    
    elif market_name == 'COLORADO':
        scores[MB.get(d0_p1[1], '0')] += 20
        scores[ID.get(d0_p1[2], '0')] += 20
        cold_check = "".join(p1_history[:5])
        for n in "0123456789":
            if n not in cold_check: scores[n] += 25

    elif market_name == 'BUSAN POOLS':
        # --- BUSAN POOLS ELITE LOGIC V14.8 ---
        
        # 1. Twin-Detection & Mirroring
        # Jika ada angka kembar (seperti 44), beri bobot besar pada Indeks & Mistiknya
        for i in range(len(d0_p1)-1):
            if d0_p1[i] == d0_p1[i+1]:
                twin_digit = d0_p1[i]
                scores[ID.get(twin_digit)] += 35 # Indeks (4->9)
                scores[ML.get(twin_digit)] += 25 # Mistik Lama (4->7)
            if '0' in all_res_data[0][2]:
                scores['0'] += 35
        
        # 2. Cross-Prize Validation (P2 & P3)
        # Busan sering memindahkan angka dari P2 ke P1 di periode berikutnya
        if len(all_res_data[0]) >= 2:
            p2_digits = all_res_data[0][1]
            for d in p2_digits:
                scores[d] += 20
                scores[TY.get(d, '0')] += 15 # Tyseen dari P2

        # 3. Pola Biji Genap-Ganjil Busan
        # Secara statistik Busan sering mendarat di Biji 3, 6, 9
        for n in "0123456789":
            if int(n) % 3 == 0 and n != '0':
                scores[n] += 18

    # --- 3. GLOBAL SEED VERIFICATION ---
    seeds = [ML.get(d0_p1[0]), ID.get(d0_p1[2]), TY.get(d0_p1[3]), MB.get(d0_p1[1])]
    for s in seeds: scores[s] += 12

    # URUTKAN & PAKSA 6 DIGIT
    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:6]]

def generate_titanium_lines_v14(bbfs_list, last_p1, market_name, count=10):
    """
    ULTIMATE MULTI-LAYER VERIFICATION ENGINE V14.8
    Special Sub-Logic: Sydney, Cambodia, & Busan Pools Optimization
    """
    # 1. POSITIONAL MAPPING
    res_map = {
        'as': [n for n in bbfs_list if n in [ML.get(last_p1[0]), TY.get(last_p1[0]), ID.get(last_p1[0])]],
        'kop': [n for n in bbfs_list if n in [ML.get(last_p1[1]), TY.get(last_p1[1]), ID.get(last_p1[1])]],
        'kep': [n for n in bbfs_list if n in [ML.get(last_p1[2]), TY.get(last_p1[2]), ID.get(last_p1[2])]],
        'eko': [n for n in bbfs_list if n in [ML.get(last_p1[3]), TY.get(last_p1[3]), ID.get(last_p1[3])]]
    }
    for pos in res_map:
        if not res_map[pos]: res_map[pos] = bbfs_list

    # 2. SCORING LAYER
    scored_2d = []
    raw_combinations = list(itertools.permutations(bbfs_list, 2))
    
    for h, t in raw_combinations:
        line = f"{h}{t}"
        score = 0
        biji = (int(h) + int(t))
        biji_f = (biji if biji < 10 else biji % 9 or 9)
        
        # --- [SYDNEY SPECIFIC RACIKAN] ---
        if market_name == 'SYDNEY LOTTO':
            # Sydney sangat identik dengan Biji 2, 5, 8
            if biji_f in [2, 5, 8]: score += 65
            # Sequential Bonus (+/- 1)
            if abs(int(h) - int(t)) == 1: score += 40
            # NEW: Mirror Balance (Jika H dan T adalah pasangan Indeks, skor naik)
            if ID.get(h) == t: score += 35
            
        # --- [CAMBODIA SPECIFIC RACIKAN] ---
        elif market_name == 'CAMBODIA':
            if biji_f in [1, 4, 7]: score += 60
            if t == TY.get(last_p1[3]): score += 45
            delta = abs(int(last_p1[2]) - int(last_p1[3]))
            if str(delta) in line: score += 25

        # --- [BUSAN POOLS SPECIFIC RACIKAN] ---
        elif market_name == 'BUSAN POOLS':
            # Busan sangat akurat pada Biji 3, 6, 9 (Kelipatan 3)
            if biji_f in [3, 6, 9]: score += 65
            # Twin-Mirror Detection: Resonansi angka kembar P1 terakhir (44 -> 9)
            if h == ID.get(last_p1[1]) or t == ID.get(last_p1[2]): score += 40
            # Verifikasi Mistik Baru dari Ekor P1 terakhir
            if t == MB.get(last_p1[3]): score += 30

        # --- [GENERAL MARKETS] ---
        else:
            if market_name in ['HONGKONG POOLS', 'MACAU', 'SINGAPORE POOLS']:
                if biji_f in [1, 4, 7, 9]: score += 30
            else:
                if biji_f in [2, 5, 8, 3]: score += 30
        
        if h == t: score -= 20
        scored_2d.append((line, score))

    scored_2d.sort(key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in scored_2d[:count]]

    # 3. 3D & 4D CONSTRUCTION (LAYER 3 & 4)
    top3, top4 = [], []
    for i, l2 in enumerate(top2):
        k_idx = i % len(res_map['kop'])
        a_idx = i % len(res_map['as'])
        
        kop = res_map['kop'][k_idx]
        asn = res_map['as'][a_idx]
        
        # Busan Logic: Injeksi Kop dari vibrasi primer
        if market_name == 'BUSAN POOLS' and i < 5:
            kop = res_map['kop'][0]

        # Sydney Anti-Crash: Keseimbangan Ganjil-Genap
        if market_name == 'SYDNEY LOTTO':
            if int(kop) % 2 == int(l2[0]) % 2:
                kop = bbfs_list[(bbfs_list.index(kop) + 1) % len(bbfs_list)]

        if kop == l2[0]: 
            kop = bbfs_list[(bbfs_list.index(kop) + 1) % len(bbfs_list)]
            
        top3.append(f"{kop}{l2}")
        top4.append(f"{asn}{kop}{l2}")

    return top2, top3, top4

def get_comprehensive_logic(all_res_data, m_name):
    d0_p1 = all_res_data[0][0] # Ambil P1 terakhir (4 digit)
    bbfs_raw = get_weighted_bbfs_v14_1(all_res_data, m_name) 
    
    # 2D Belakang untuk Shio
    dua_d_belakang = int(d0_p1[2:])
    shio_idx = dua_d_belakang % 12
    
    top2, top3, top4 = generate_titanium_lines_v14(bbfs_raw, d0_p1, m_name)
    
    return {
        "bbfs": "".join(sorted(bbfs_raw)),
        "am": "".join(sorted(bbfs_raw[:4])), # 4 digit terkuat
        "al": "".join(sorted(list(set([ML.get(d0_p1[3], '0'), TY.get(d0_p1[3], '0')])))),
        "ai": "".join(sorted(list(set([ID.get(d0_p1[2], '0'), ID.get(d0_p1[3], '0')])))),
        "top2d": top2, "top3d": top3, "top4d": top4,
        "shio": SHIO_MAP.get(shio_idx, "N/A"),
        "macau": f"{bbfs_raw[0]}{bbfs_raw[1]} - {bbfs_raw[2]}{bbfs_raw[3]}",
        "twin": f"{bbfs_raw[0]}{bbfs_raw[0]}, {bbfs_raw[1]}{bbfs_raw[1]}"
    }

def fetch_results(market_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with httpx.Client(timeout=10.0, verify=False) as client:
            if market_code == "HK_SPECIAL":
                url = "https://tabelsemalam.com/"
                r = client.get(url, headers=headers)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if not table: return []
                res = []
                for row in table.find('tbody').find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        val = re.sub(r'\D', '', tds[1].text.strip())
                        if len(val) == 4: res.append([val])
                return res[:40]
            
            # Jalur Umum
            url = f"https://4upk6k0qz6.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            r = client.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', class_='table-history')
            if not table: return []
            
            results = []
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 4:
                    def get_num(td_elem):
                        link = td_elem.find('a')
                        return re.sub(r'\D', '', link.text if link else td_elem.text)

                    p1 = get_num(tds[3])
                    if len(p1) == 4:
                        if len(tds) >= 6:
                            results.append([p1, get_num(tds[4]), get_num(tds[5])])
                        else:
                            results.append([p1])
            return results[:40]
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []


@app.route('/', methods=['GET', 'POST'])
def index():
    analysis, selected = None, None
    markets = sorted(TARGET_POOLS.keys())
    
    if request.method == 'POST':
        selected = request.form.get('market')
        if selected in TARGET_POOLS:
            res_data = fetch_results(TARGET_POOLS[selected])
            
            if res_data and len(res_data) >= 8:
                analysis = get_comprehensive_logic(res_data, selected)
                # --- TARUH DI SINI (Di dalam kondisi data sukses ada) ---
                analysis['last_res'] = res_data[0][0]
                analysis['p2_last'] = res_data[0][1] if len(res_data[0]) > 1 else "-"
                analysis['p3_last'] = res_data[0][2] if len(res_data[0]) > 2 else "-"
            else: 
                analysis = "error"
                
    return render_template('index.html', markets=markets, analysis=analysis, selected=selected)
    app.run(debug=True)
