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
        
    elif market_name == 'MACAU':
        scores[str((int(d0_p1[3]) + 1) % 10)] += 15
        scores[str((int(d0_p1[3]) - 1) % 10)] += 15
        scores[ID.get(d0_p1[1], '0')] += 10 

    elif market_name == 'COLORADO':
        scores[MB.get(d0_p1[1], '0')] += 20
        scores[ID.get(d0_p1[2], '0')] += 20
        cold_check = "".join(p1_history[:5])
        for n in "0123456789":
            if n not in cold_check: scores[n] += 25

    # --- 3. GLOBAL SEED VERIFICATION ---
    seeds = [ML.get(d0_p1[0]), ID.get(d0_p1[2]), TY.get(d0_p1[3]), MB.get(d0_p1[1])]
    for s in seeds: scores[s] += 12

    # URUTKAN & PAKSA 6 DIGIT
    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:6]]

def generate_titanium_lines_v14(bbfs_list, last_p1, market_name, count=10):
    # bbfs_list: hasil weighted bbfs (6 digit)
    # last_p1: prize 1 terakhir (contoh: '4569')
    
    # 1. PECAH BBFS MENJADI KEKUATAN POSISI (Positional Resonance)
    # Kita ambil angka dari BBFS yang punya vibrasi dengan result terakhir
    as_pool = [n for n in bbfs_list if n in [ML.get(last_p1[0]), TY.get(last_p1[0]), ID.get(last_p1[0])]] or bbfs_list[:3]
    kop_pool = [n for n in bbfs_list if n in [ML.get(last_p1[1]), TY.get(last_p1[1]), ID.get(last_p1[1])]] or bbfs_list[1:4]
    kep_pool = [n for n in bbfs_list if n in [ML.get(last_p1[2]), TY.get(last_p1[2]), ID.get(last_p1[2])]] or bbfs_list[2:5]
    ekor_pool = [n for n in bbfs_list if n in [ML.get(last_p1[3]), TY.get(last_p1[3]), ID.get(last_p1[3])]] or bbfs_list[3:]

    # 2. GENERATE TOP 2D (Fokus Kepala & Ekor)
    # Kita pakai kombinasi kepala-ekor yang paling masuk akal secara sum-biji
    all_2d = []
    for h in kep_pool:
        for t in ekor_pool:
            if h == t: continue # Skip twin di top 2d jitu
            line = f"{h}{t}"
            
            # Filter Biji (Sum 2D)
            biji = (int(h) + int(t))
            biji = (biji if biji < 10 else biji % 9 or 9) # Rumus Biji Sembilan
            
            score = 0
            # Cluster Biji Sakti berdasarkan Market
            if market_name in ['HONGKONG POOLS', 'MACAU', 'CAMBODIA']:
                if biji in [1, 4, 7, 9]: score += 50
            else:
                if biji in [2, 5, 8, 3]: score += 50
                
            all_2d.append((line, score))
    
    # Urutkan dan ambil 10 line terbaik
    all_2d.sort(key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in all_2d[:count]]

    # 3. GENERATE 3D & 4D (Precision Insertion)
    top3, top4 = [], []
    for i in range(len(top2)):
        # Rotasi As dan Kop agar tidak monoton
        idx_as = i % len(as_pool)
        idx_kop = i % len(kop_pool)
        
        a = as_pool[idx_as]
        k = kop_pool[idx_kop]
        
        top3.append(f"{k}{top2[i]}")
        top4.append(f"{a}{k}{top2[i]}")

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
