from flask import Flask, render_template, request
import re
import httpx
import itertools
from collections import Counter
from bs4 import BeautifulSoup
import os
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

# --- [DATABASE & LOGIC - Tetap Sama] ---
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

def get_weighted_bbfs_v12(all_res):
    scores = {str(n): 0 for n in range(10)}
    freq = Counter("".join(all_res[:40]))
    for n in freq: scores[n] += freq[n] * 1.5
    gaps = [(1, 5), (3, 3), (7, 4)] 
    for idx, weight in gaps:
        if len(all_res) > idx:
            for char in all_res[idx]: scores[char] += weight
    d0 = all_res[0]
    m_seeds = [ML.get(d0[2], '0'), ID.get(d0[3], '0'), TY.get(d0[3], '0'), MB.get(d0[2], '0'), ML.get(d0[3], '0')]
    for s in m_seeds: scores[s] += 6
    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:7]]

def generate_top_lines(bbfs_list, count=10):
    t2 = ["".join(p) for p in itertools.permutations(bbfs_list, 2)]
    t3 = ["".join(p) for p in itertools.permutations(bbfs_list, 3)]
    t4 = ["".join(p) for p in itertools.permutations(bbfs_list, 4)]
    return t2[:count], t3[:count], t4[:count]

def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    bbfs_raw = get_weighted_bbfs_v12(all_res)
    if m_name == "HONGKONG POOLS":
        if MB.get(d0[3]) not in bbfs_raw: bbfs_raw.append(MB.get(d0[3]))
        if "5" not in bbfs_raw: bbfs_raw.append("5")
    elif m_name == "HONGKONG LOTTO":
        if "0" not in bbfs_raw: bbfs_raw.append("0")
        if "1" not in bbfs_raw: bbfs_raw.append("1")
    bbfs_final = sorted(list(set(bbfs_raw)))[:7]
    top2, top3, top4 = generate_top_lines(bbfs_final)
    return {
        "bbfs": " ".join(bbfs_final),
        "top2d": top2, "top3d": top3, "top4d": top4,
        "shio": SHIO_MAP.get(int(d0[2:]) % 12 or 12),
        "macau": f"{bbfs_final[0]} - {bbfs_final[1]}",
        "twin": f"{bbfs_final[0]}{bbfs_final[0]}, {bbfs_final[1]}{bbfs_final[1]}"
    }

def fetch_results(market_code):
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    if market_code == "HK_SPECIAL":
        try:
            with httpx.Client(timeout=10.0, verify=False) as client:
                r = client.get("https://tabelsemalam.com/", headers=headers)
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
    
    urls = [f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"]
    for url in urls:
        try:
            with httpx.Client(timeout=10.0, verify=False) as client:
                r = client.get(url, headers=headers)
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

# --- [ROUTES] ---

@app.route('/', methods=['GET', 'POST'])
def index():
    analysis = None
    selected = None
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
