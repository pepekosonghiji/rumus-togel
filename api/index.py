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

# --- [V12.4 ENGINE WITH GLOBAL VERIFICATION UPGRADE] ---

def get_weighted_bbfs_v13(all_res, market_name):
    scores = {str(n): 0 for n in range(10)}
    d0 = all_res[0]
    
    # --- 1. FREKUENSI DINAMIS (Optimasi 6 Digit) ---
    freq = Counter("".join(all_res[:30]))
    for n in "0123456789":
        f_val = freq.get(n, 0)
        # Berikan proteksi pada angka yang baru keluar (Repeat Number)
        if n in d0: 
            scores[n] += 15 
        # Angka dingin tetap diberi panggung
        if f_val < 3: scores[n] += 20
        else: scores[n] += f_val * 1.2

    # --- 2. DYNAMIC FREQUENCY ANALYSIS ---
    # Memberikan bobot pada angka 'Dingin' (jarang keluar) agar tidak luput
    freq = Counter("".join(all_res[:40]))
    for n in "0123456789":
        f_val = freq.get(n, 0)
        if f_val < 4: 
            scores[n] += 25  # Prioritas angka yang sudah lama tidak muncul
        else: 
            scores[n] += f_val * 1.5 # Tetap hitung angka panas secara proporsional

    d0 = all_res[0] # Result terakhir sebagai acuan pola
    
    # --- 3. CLUSTER SUB-LOGIC (LOCKED & ISOLATED) ---
    # Gunakan elif agar satu pasaran hanya diproses oleh satu sub-logic spesifik
    if market_name == 'WASHING-MID':
        # Metode Mirror-Gap: Cek result 2 periode ke belakang
        if len(all_res) > 2:
            d2 = all_res[2]
            # Washingmid suka menarik kembali angka dari 2 hari lalu
            for digit in d2: scores[digit] += 18
        # Verifikasi angka tengah
        scores[ID.get(d0[1], '0')] += 22
        scores[TY.get(d0[2], '0')] += 20
        
    elif market_name == 'MACAU':
        next_val = str((int(d0[3]) + 1) % 10)
        prev_val = str((int(d0[3]) - 1) % 10)
        scores[next_val] += 15
        scores[prev_val] += 15
        scores[ID.get(d0[1], '0')] += 10 

    elif market_name == 'ORLANDO':
        # Analisa Mirroring AS-EKOR
        scores[ML.get(d0[0], '0')] += 18
        scores[ID.get(d0[1], '0')] += 15
        # Respon khusus jika result sebelumnya TWIN (seperti 4522)
        if d0[2] == d0[3]:
            for n in [TY.get(d0[2]), ML.get(d0[2]), '5', '9']: 
                scores[n] += 25

    elif market_name == 'COLORADO':
        # Colorado Precision Upgrade: Sensitif terhadap MB & ID dari KOP/KEP
        scores[MB.get(d0[1], '0')] += 20
        scores[ID.get(d0[2], '0')] += 20
        # Tambahkan penguat pada angka Cold dalam 5 result terakhir
        cold_check = "".join(all_res[:5])
        for n in "0123456789":
            if n not in cold_check: scores[n] += 25
        if int(d0[0]) > 4: scores['0'] += 10; scores['1'] += 10

    elif market_name in ['OREGON 3', 'OREGON 6', 'OREGON 9', 'OREGON 12']:
        for digit in d0:
            scores[ML.get(digit)] += 12
            scores[TY.get(digit)] += 10
        # Anti-Jump: Cari angka yang benar-benar hilang dalam 3 result terakhir
        present_digits = set("".join(all_res[:3]))
        missing = set("0123456789") - present_digits
        for m in missing: scores[m] += 22

    elif market_name == 'HONGKONG POOLS':
        scores[ID.get(d0[2], '0')] += 15
        scores[ID.get(d0[3], '0')] += 15
        if int(d0[0]) > 5:
            for n in ['0','1','2']: scores[n] += 12

    # --- 4. GLOBAL SEED VERIFICATION (SAFETY NET) ---
    # Ini berlaku untuk semua market (termasuk yang tidak punya sub-logic)
    m_seeds = [ML.get(d0[0]), ID.get(d0[2]), TY.get(d0[3]), MB.get(d0[1])]
    for s in m_seeds: 
        scores[s] += 10 # Bobot pengaman agar angka tidak melompat terlalu jauh

    # Urutkan berdasarkan skor tertinggi dan ambil 7 digit terbaik
    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:7]]
    
def generate_titanium_lines(bbfs_list, all_res, market_name, count=10):
    """
    METODE: DYNAMIC POSITIONAL RESONANCE (DPR)
    V13.5 Premium Edition - Fokus pada akurasi tembakan spesifik 2D/3D/4D
    """
    d0 = all_res[0]
    # Pool diperluas dengan perlindungan angka cadangan
    ext_pool = list(set(bbfs_list[:6] + [ML.get(bbfs_list[0]), TY.get(bbfs_list[0])]))
    all_pairs = list(itertools.permutations(ext_pool, 2))
    
    verified_2d = []
    for p in all_pairs:
        line = f"{p[0]}{p[1]}"
        h, t = int(p[0]), int(p[1])
        score = 0
        
        # --- LAYER 1: POSITIONAL RESONANCE ---
        # Verifikasi Kepala: Harus punya resonansi kuat dengan Ekor/Kepala sebelumnya
        if p[0] in [ML.get(d0[3]), ID.get(d0[2]), TY.get(d0[3])]: 
            score += 20
        
        # --- LAYER 2: SUM-BIJI & RATIO FILTER ---
        sum_val = (h + t) % 10
        # Filter khusus Cluster Amerika & Oregon
        if market_name in ['ORLANDO', 'COLORADO', 'MANHATTAN','WASHINGMID'] or 'OREGON' in market_name:
            if sum_val in [1, 5, 8, 9]: score += 30 
        # Filter khusus Cluster Asia (HK, Macau, Cambodia)
        elif market_name in ['HONGKONG POOLS', 'MACAU', 'CAMBODIA', 'SINGAPORE POOLS']:
            if sum_val in [0, 3, 4, 7]: score += 25
        else:
            if sum_val in [2, 6, 8]: score += 15
        
        # Respon terhadap pola Twin
        if h == t:
            score += 35 if d0[2] == d0[3] else -25
            
        verified_2d.append((line, score))

    verified_2d.sort(key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in verified_2d[:count]]

    # --- LAYER 3: 4D PRECISION TARGETING (PENEMBAK JITU) ---
    top3, top4 = [], []
    for i in range(count):
        # Penentuan AS & KOP tidak lagi statis, tapi berdasarkan 'Vibrasi' result terakhir
        # Jika result genap, gunakan Mistik Baru. Jika ganjil, gunakan Taysen.
        is_odd = int(d0[3]) % 2 != 0
        
        if market_name == 'COLORADO':
            as_final = ML.get(d0[0]) if i < 5 else ID.get(d0[3])
            kop_final = TY.get(d0[2]) if i % 2 == 0 else bbfs_list[1]
        
        elif market_name in ['HONGKONG POOLS', 'MACAU']:
            # Karakter Asia: AS sering kali Mirror (Index) dari Ekor terakhir
            as_final = ID.get(d0[3]) if i < 5 else TY.get(d0[0])
            kop_final = MB.get(d0[1]) if i % 2 == 0 else ML.get(d0[2])
            
        else:
            # Karakter Global: Mengikuti vibrasi ganjil/genap
            if is_odd:
                as_final = TY.get(d0[0]) if i < 5 else bbfs_list[0]
                kop_final = ML.get(d0[1]) if i % 2 == 0 else ID.get(d0[2])
            else:
                as_final = MB.get(d0[0]) if i < 5 else ID.get(d0[1])
                kop_final = TY.get(d0[3]) if i % 2 == 0 else bbfs_list[2]
        
        # Final Assembly
        line_2d = top2[i]
        line_3d = f"{kop_final}{line_2d}"
        line_4d = f"{as_final}{line_3d}"
        
        top3.append(line_3d)
        top4.append(line_4d)

    return top2, top3, top4
    
def get_comprehensive_logic(all_res, m_name):
    d0 = all_res[0]
    bbfs_raw = get_weighted_bbfs_v13(all_res, m_name) 
    
    bbfs_final = sorted(bbfs_raw)
    am = sorted(bbfs_raw[:4])
    al = sorted(list(set([ML.get(d0[3], '0'), MB.get(d0[3], '0'), TY.get(d0[3], '0')])))[:3]
    ai = sorted(list(set([ID.get(d0[2], '0'), ID.get(d0[3], '0'), TY.get(d0[2], '0')])))[:3]

    top2, top3, top4 = generate_titanium_lines(bbfs_raw, all_res, m_name)
    
    return {
        "bbfs": "".join(bbfs_final),
        "am": "".join(am), "al": "".join(al), "ai": "".join(ai),
        "top2d": top2, "top3d": top3, "top4d": top4,
        "shio": SHIO_MAP.get(int(d0[2:]) % 12 or 12),
        "macau": f"{bbfs_raw[0]}{bbfs_raw[1]} - {bbfs_raw[2]}{bbfs_raw[3]}",
        "twin": f"{bbfs_raw[0]}{bbfs_raw[0]}, {bbfs_raw[1]}{bbfs_raw[1]}"
    }

def fetch_results(market_code):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with httpx.Client(timeout=10.0, verify=False) as client:
            if market_code == "HK_SPECIAL":
                url = "https://tabelsemalam.com/"
            else:
                url = f"https://4upk6k0qz6.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            
            r = client.get(url, headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            if market_code == "HK_SPECIAL":
                table = soup.find('table')
                if not table: return []
                return [tds[1].text.strip() for row in table.find('tbody').find_all('tr') 
                        if (tds := row.find_all('td')) and len(tds) >= 2 and tds[1].text.strip().isdigit()][:40]
            
            else:
                table = soup.find('table', class_='table-history')
                if not table: return []
                
                rows = table.find('tbody').find_all('tr')
                results = []
                
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 3:
                        # LOGIC DETEKSI KOLOM:
                        # Jika pasaran Cambodia/Lainnya, result biasanya ada di kolom indeks 3 (kolom ke-4)
                        # karena ada kolom Periode di indeks 2.
                        # Khusus Macau biasanya result langsung di indeks 2.
                        
                        target_idx = 3 if len(tds) >= 4 and market_code != 'm17' else 2
                        
                        val_cell = tds[target_idx]
                        anchor = val_cell.find('a')
                        val = anchor.text.strip() if anchor else val_cell.text.strip()
                        
                        clean_val = re.sub(r'\D', '', val)
                        if len(clean_val) == 4:
                            results.append(clean_val)
                            
                return results[:40]
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

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
            else: analysis = "error"
    return render_template('index.html', markets=markets, analysis=analysis, selected=selected)

if __name__ == "__main__":
    app.run(debug=True)
