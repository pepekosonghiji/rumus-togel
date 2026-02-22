import os
from flask import Flask, render_template, request
import re
import httpx
from collections import Counter
from bs4 import BeautifulSoup

# Setup Flask
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# --- [DATABASE MASTER POLA V12.4] ---
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
    'WASHING-MID':'p24508', 'WUHAN':'p28615'
}

# --- [V12.4 CORE ENGINE LOGIC] ---

def get_weighted_bbfs_v124(all_res, market):
    """Pertajaman BBFS Khusus Danang & Penyeimbang Umum"""
    scores = {str(n): 0 for n in range(10)}
    freq = Counter("".join(all_res[:40]))
    for n in freq: scores[n] += freq[n] * 1.5
    
    # Analisa Struktur Posisi
    for i, res in enumerate(all_res[:7]):
        w = 7 - i
        # Jika Danang, perkuat deteksi angka AS (Depan)
        as_weight = 1.2 if market == 'DANANG' else 0.8
        scores[res[0]] += w * as_weight  
        scores[res[1]] += w * 0.6  
        scores[res[2]] += w * 1.2  
        scores[res[3]] += w * 1.2  

    d0 = all_res[0] # Result Terakhir
    
    # EKSPANSI MISTIK (Menangkap Angka Hilang Seperti '7')
    # Mengambil pelarian dari posisi AS terakhir untuk Danang
    exp_seeds = [
        ML.get(d0[0], '0'), MB.get(d0[0], '0'), # Pelarian AS
        ID.get(d0[1], '0'), TY.get(d0[1], '0'), # Pelarian KOP
        ML.get(d0[2], '0'), ID.get(d0[3], '0')  
    ]
    for s in exp_seeds: scores[s] += 10 if market == 'DANANG' else 7 

    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:7]]

def generate_lines_v124(bbfs_list, all_res, market, count=10):
    """Generator Line 2D, 3D, 4D dengan Filter Akurasi Tinggi"""
    d0 = all_res[0]
    
    # 1. TOP 2D (Optimasi Jarak Danang)
    heads = bbfs_list[:5]
    tails = bbfs_list[::-1][:5]
    raw_2d = [f"{h}{t}" for h in heads for t in tails if h != t]
    
    v2d = []
    for line in raw_2d:
        sc = 0
        h, t = int(line[0]), int(line[1])
        # Danang cenderung memiliki selisih angka > 1
        if abs(h - t) >= 2: sc += 5 if market == 'DANANG' else 3
        if line[1] in [d0[2], d0[3]]: sc += 2 
        v2d.append((line, sc))
    
    v2d.sort(key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in v2d[:count]]

    # 2. TOP 3D & 4D (Locking System)
    top3, top4 = [], []
    for i in range(count):
        # Gunakan digit BBFS yang tidak ada di 2D sebagai KOP/AS
        kop = bbfs_list[i % 3]
        top3.append(f"{kop}{top2[i]}")
        
        as_ptr = bbfs_list[(i+2) % 4]
        top4.append(f"{as_ptr}{kop}{top2[i]}")

    return top2, top3, top4

def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    bbfs_raw = get_weighted_bbfs_v124(all_res, m_name)
    bbfs_sorted = "".join(sorted(bbfs_raw))
    
    # AM: 4 Digit Dominan
    am = "".join(sorted(bbfs_raw[:4]))
    
    # AL: Pelarian (Mistik AS & Ekor)
    al = "".join(sorted(list(set([ML.get(d0[0]), TY.get(d0[3])]))))
    
    # AI: Angka Ikut (Kuncian Danang dari 3D 093)
    ai = "".join(sorted(list(set([ID.get(d0[1]), MB.get(d0[2]), d0[3]])))[:3])

    top2, top3, top4 = generate_lines_v124(bbfs_raw, all_res, m_name)
    
    return {
        "bbfs": bbfs_sorted,
        "am": am,
        "al": al,
        "ai": ai,
        "top2d": top2, 
        "top3d": top3, 
        "top4d": top4,
        "shio": SHIO_MAP.get(int(d0[2:]) % 12 or 12),
        "macau": f"{bbfs_raw[0]}{bbfs_raw[1]} - {bbfs_raw[2]}{bbfs_raw[3]}",
        "twin": f"{bbfs_raw[0]}{bbfs_raw[0]}, {bbfs_raw[1]}{bbfs_raw[1]}"
    }

# --- [SCRAPER ENGINE] ---
def fetch_results(market_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with httpx.Client(timeout=10.0, verify=False) as client:
            if market_code == "HK_SPECIAL":
                r = client.get("https://tabelsemalam.com/", headers=headers)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if table:
                    return [tds[1].text.strip() for row in table.find('tbody').find_all('tr') 
                            if (tds := row.find_all('td')) and len(tds) >= 2 and tds[1].text.strip().isdigit()][:40]
            else:
                url = f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
                r = client.get(url, headers=headers)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table', class_='table-history')
                if table:
                    rows = table.find('tbody').find_all('tr')
                    return [re.sub(r'\D', '', tds[3].text.strip()) for row in rows 
                            if (tds := row.find_all('td')) and len(tds) >= 4 and len(re.sub(r'\D', '', tds[3].text.strip())) == 4][:40]
    except:
        return []
    return []

# --- [ROUTES] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    analysis, selected = None, None
    markets = sorted(TARGET_POOLS.keys())
    
    if request.method == 'POST':
        selected = request.form.get('market')
        if selected in TARGET_POOLS:
            res = fetch_results(TARGET_POOLS[selected])
            if res and len(res) >= 8:
                analysis = get_comprehensive_logic(res, selected)
                analysis['last_res'] = res[0]
            else:
                analysis = "error"

    return render_template('index.html', markets=markets, analysis=analysis, selected=selected)

if __name__ == "__main__":
    app.run(debug=True)
