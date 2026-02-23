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
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

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
    all_pairs = list(itertools.permutations(bbfs_list, 2))
    verified_2d = []
    
    for p in all_pairs:
        line = f"{p[0]}{p[1]}"
        h, t = int(p[0]), int(p[1])
        score = 0
        
        # Layer 1: Positional Resonance
        if p[0] in [ML.get(last_p1[3]), ID.get(last_p1[2]), TY.get(last_p1[3])]:
            score += 20
            
        # Layer 2: Cluster Sum-Biji
        sum_val = (h + t) % 10
        if market_name in ['ORLANDO', 'COLORADO', 'WASHINGMID'] or 'OREGON' in market_name:
            if sum_val in [1, 5, 8, 9]: score += 30
        elif market_name in ['HONGKONG POOLS', 'MACAU', 'CAMBODIA']:
            if sum_val in [0, 3, 4, 7]: score += 25
            
        verified_2d.append((line, score))

    verified_2d.sort(key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in verified_2d[:count]]

    # Layer 3: Penembak Jitu 3D/4D
    top3, top4 = [], []
    is_odd = int(last_p1[3]) % 2 != 0
    
    for i in range(count):
        if market_name == 'WASHINGMID':
            as_final = MB.get(last_p1[0]) if i < 5 else TY.get(last_p1[1])
            kop_final = ID.get(last_p1[0]) if i % 2 == 0 else bbfs_list[2]
        elif market_name in ['HONGKONG POOLS', 'MACAU']:
            as_final = ID.get(last_p1[3]) if i < 5 else TY.get(last_p1[0])
            kop_final = MB.get(last_p1[1]) if i % 2 == 0 else ML.get(last_p1[2])
        else:
            if is_odd:
                as_final = TY.get(last_p1[0]) if i < 5 else bbfs_list[0]
                kop_final = ML.get(last_p1[1]) if i % 2 == 0 else ID.get(last_p1[2])
            else:
                as_final = MB.get(last_p1[0]) if i < 5 else ID.get(last_p1[1])
                kop_final = TY.get(last_p1[3]) if i % 2 == 0 else bbfs_list[1]
        
        top3.append(f"{kop_final}{top2[i]}")
        top4.append(f"{as_final}{kop_final}{top2[i]}")
        
    return top2, top3, top4

def get_comprehensive_logic(all_res_data, m_name):
    d0_p1 = all_res_data[0][0]
    bbfs_raw = get_weighted_bbfs_v14_1(all_res_data, m_name) 
    
    bbfs_final = sorted(bbfs_raw)
    # AM sekarang diambil dari 4 skor tertinggi bbfs
    am = sorted(bbfs_raw[:4])
    al = sorted(list(set([ML.get(d0_p1[3], '0'), MB.get(d0_p1[3], '0'), TY.get(d0_p1[3], '0')])))[:3]
    ai = sorted(list(set([ID.get(d0_p1[2], '0'), ID.get(d0_p1[3], '0'), TY.get(d0_p1[2], '0')])))[:3]

    top2, top3, top4 = generate_titanium_lines_v14(bbfs_raw, d0_p1, m_name)
    
    return {
        "bbfs": "".join(bbfs_final),
        "am": "".join(am), "al": "".join(al), "ai": "".join(ai),
        "top2d": top2, "top3d": top3, "top4d": top4,
        "shio": SHIO_MAP.get(int(d0_p1[2:]) % 12 or 12),
        "macau": f"{bbfs_raw[0]}{bbfs_raw[1]} - {bbfs_raw[2]}{bbfs_raw[3]}",
        "twin": f"{bbfs_raw[0]}{bbfs_raw[0]}, {bbfs_raw[1]}{bbfs_raw[1]}"
    }

def fetch_results(market_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with httpx.Client(timeout=10.0, verify=False) as client:
            url = "https://tabelsemalam.com/" if market_code == "HK_SPECIAL" else f"https://4upk6k0qz6.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            r = client.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            if market_code == "HK_SPECIAL":
                table = soup.find('table')
                return [[tds[1].text.strip()] for row in table.find('tbody').find_all('tr') if (tds := row.find_all('td')) and len(tds) >= 2 and tds[1].text.strip().isdigit()][:40]
            
            else:
                table = soup.find('table', class_='table-history')
                if not table: return []
                results = []
                
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) < 3: continue

                    # --- LOGIKA PENENTUAN KOLOM BERDASARKAN PASARAN ---
                    
                    # 1. KHUSUS OREGON (Hanya P1 di kolom ke-5 / indeks 4)
                    if "oregon" in market_code.lower():
                        if len(tds) >= 5:
                            p1_raw = tds[4]
                            p1 = re.sub(r'\D', '', p1_raw.find('a').text if p1_raw.find('a') else p1_raw.text)
                            if len(p1) == 4: results.append([p1])

                    # 2. KHUSUS CAMBODIA & SEJENISNYA (P1, P2, P3 mulai indeks 3)
                    elif len(tds) >= 6: 
                        p1_raw, p2_raw, p3_raw = tds[3], tds[4], tds[5]
                        
                        p1 = re.sub(r'\D', '', p1_raw.find('a').text if p1_raw.find('a') else p1_raw.text)
                        p2 = re.sub(r'\D', '', p2_raw.find('a').text if p2_raw.find('a') else p2_raw.text)
                        p3 = re.sub(r'\D', '', p3_raw.find('a').text if p3_raw.find('a') else p3_raw.text)
                        
                        if len(p1) == 4: results.append([p1, p2, p3])
                    
                    # 3. MACAU & PASARAN STANDAR (P1 di indeks 2)
                    else: 
                        p1_raw = tds[2]
                        p1 = re.sub(r'\D', '', p1_raw.find('a').text if p1_raw.find('a') else p1_raw.text)
                        if len(p1) == 4: results.append([p1])
                            
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
                analysis['last_res'] = res_data[0][0]
            else: analysis = "error"
    return render_template('index.html', markets=markets, analysis=analysis, selected=selected)

if __name__ == "__main__":
    app.run(debug=True)
