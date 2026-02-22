import os
from flask import Flask, render_template, request
import re
import httpx
import itertools
from collections import Counter
from bs4 import BeautifulSoup

# Setup template directory secara eksplisit untuk Vercel
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
    'WASHING-MID':'p24508', 'WUHAN':'p28615'
}

# --- [V12.4 SUB-LOGIC INJECTOR FOR PENANG] ---

def get_weighted_bbfs_v12(all_res, market_name):
    """Logika BBFS dengan Injector Khusus Penang"""
    scores = {str(n): 0 for n in range(10)}
    freq = Counter("".join(all_res[:35]))
    for n in freq: scores[n] += freq[n] * 1.5 
    
    for i, res in enumerate(all_res[:8]):
        weight = 8 - i
        scores[res[0]] += weight * 1.2 # AS
        scores[res[1]] += weight * 0.8 # KOP
        scores[res[2]] += weight * 1.5 # KEPALA
        scores[res[3]] += weight * 1.5 # EKOR

    d0 = all_res[0]

    # >>> PERBAIKAN: SUB-LOGIC PENANG <<<
    if market_name == 'PENANG':
        as_last = d0[0]
        scores[ML.get(as_last, '0')] += 15 
        scores[ID.get(as_last, '0')] += 10 
        scores[d0[1]] += 12 
        scores[TY.get(d0[3], '0')] += 8

    m_seeds = [
        ML.get(d0[0], '0'), ML.get(d0[2], '0'),
        ID.get(d0[3], '0'), TY.get(d0[3], '0'), MB.get(d0[2], '0')
    ]
    for s in m_seeds: scores[s] += 10

    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:7]]

def generate_verified_lines(bbfs_list, all_res, market_name, count=10):
    """Filter Line Khusus Penang"""
    d0 = all_res[0]
    all_pairs = list(itertools.permutations(bbfs_list, 2))
    
    verified_2d_list = []
    for p in all_pairs:
        line = f"{p[0]}{p[1]}"
        score = 0
        h_digit, t_digit = int(p[0]), int(p[1])
        
        if abs(h_digit - t_digit) > 1: score += 5 
        
        if market_name == 'PENANG':
            if h_digit % 2 == t_digit % 2: score += 4
            if line == d0[2:]: score -= 20 
        
        verified_2d_list.append((line, score))
    
    verified_2d_list.sort(key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in verified_2d_list[:count]]

    top3, top4 = [], []
    for i in range(count):
        kop = bbfs_list[(i % 2) + 1] 
        top3.append(f"{kop}{top2[i]}")
        as_digit = bbfs_list[0] if i < 5 else bbfs_list[(i % 3)]
        top4.append(f"{as_digit}{kop}{top2[i]}")

    return top2, top3, top4

def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    # PERBAIKAN: Menambahkan parameter m_name agar sub-logic aktif
    bbfs_raw = get_weighted_bbfs_v12(all_res, m_name)
    bbfs_final = sorted(bbfs_raw)
    
    am = sorted(bbfs_raw[:4])
    al = sorted(list(set([ML.get(d0[3], '0'), MB.get(d0[3], '0'), TY.get(d0[3], '0')])))[:3]
    ai = sorted(list(set([ID.get(d0[2], '0'), ID.get(d0[3], '0'), TY.get(d0[2], '0')])))[:3]

    # PERBAIKAN: Menambahkan parameter m_name
    top2, top3, top4 = generate_verified_lines(bbfs_raw, all_res, m_name)
    
    return {
        "bbfs": "".join(bbfs_final),
        "am": "".join(am),
        "al": "".join(al),
        "ai": "".join(ai),
        "top2d": top2, 
        "top3d": top3, 
        "top4d": top4,
        "shio": SHIO_MAP.get(int(d0[2:]) % 12 or 12),
        "macau": f"{bbfs_raw[0]}{bbfs_raw[1]} - {bbfs_raw[2]}{bbfs_raw[3]}",
        "twin": f"{bbfs_raw[0]}{bbfs_raw[0]}, {bbfs_raw[1]}{bbfs_raw[1]}"
    }

# --- [SCRAPER ENGINE - UNCHANGED] ---
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
