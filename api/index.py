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
    7:"KELINCI", 8:"NAGA", 9:"ULAR", 10:"KUDA", 11:"KAMBING", 12:"MONYET"
}

# --- [SOURCE DATA - DOMAIN UMUM] ---
# URL: nfx1avfcy8.salamtarget.com
TARGET_POOLS = {
    'BEIJING': 'p24492', 'BUSAN POOLS':'p16063', 'CAMBODIA': 'p3501', 
    'DANANG':'p22816', 'HONGKONG LOTTO': 'p2263', 'HONGKONG POOLS': 'HK_SPECIAL','JEJU':'p22815',
    'OREGON 3':'p12521', 'OREGON 6':'p12522', 'OREGON 9':'p12523', 'OSAKA':'p28422',
    'PENANG':'p22817', 'PHUKET':'p28435', 'SAPPORO':'p22814', 'SEOUL':'p28502',
    'SINGAPORE POOLS': 'p2264', 'SYDNEY LOTTO': 'p2262', 'TORONTOMID':'p13976',
    'WASHINGMID':'p24508', 'WUHAN':'p28615', 'MACAU': 'm17','GREECE':'p8584'
}

# --- [SOURCE DATA - DOMAIN BARU] ---
# URL: ux0sa.percaya4d.live
SPECIAL_POOLS = {
    'TAIWAN': 'p12501','CHINA':'p12499','JAPAN':'p24128',
    'PCSO':'p32340','ACEH':'p29593','BALI':'p28800','BANDUNG':'p29590',
    'NTT POOLS':'p30577','DEWATA':'p27489'
}

def fetch_results(market_code, max_pages=3):
    """
    Fetch results with Deep History Support (Upgrade V24.0: Default max_pages=3)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    results = []
    
    try:
        # Penanganan Khusus HK_SPECIAL
        if market_code == "HK_SPECIAL":
            with httpx.Client(timeout=15.0, verify=False, follow_redirects=True) as client:
                url = "https://tabelsemalam.com/"
                r = client.get(url, headers=headers)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if not table: return []
                tbody = table.find('tbody')
                if not tbody: return []
                for row in tbody.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        p1 = re.sub(r'\D', '', tds[1].text.strip())
                        if len(p1) == 4:
                            results.append([p1, '0000', '0000'])
                return results[:40]

        # LOGIKA PEMILIHAN DOMAIN OTOMATIS
        # Jika kode ada di SPECIAL_POOLS, gunakan domain baru.
        if market_code in SPECIAL_POOLS.values():
            target_domain = "ux0sa.percaya4d.live"
        else:
            target_domain = "nfx1avfcy8.salamtarget.com"

        # JALUR FETCHING
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                url = f"https://{target_domain}/history/result-mobile/{market_code}-pool-{page}"
                r = client.get(url, headers=headers)
                if r.status_code != 200: break
                
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table', class_='table-history')
                if not table: break
                
                rows = table.find('tbody').find_all('tr')
                page_data_found = False
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        def get_num(td_elem):
                            link = td_elem.find('a')
                            return re.sub(r'\D', '', link.text if link else td_elem.text)
                        
                        p1 = get_num(tds[3])
                        if len(p1) == 4:
                            p2 = get_num(tds[4]) if len(tds) >= 5 else "0000"
                            p3 = get_num(tds[5]) if len(tds) >= 6 else "0000"
                            results.append([p1, p2, p3])
                            page_data_found = True
                if not page_data_found: break
            return results[:100] 

    except Exception as e:
        print(f"Deep Fetch Error: {e}")
        return results

def get_comprehensive_logic_god(all_res_data, market_name):
    """
    🚀 MAMANG ENGINE V.25.2 [GOD MODE - ELITE SNIPER] 🚀
    Sistem Verifikasi Berlapis: Divine Selection, God Analysis, & Holy Verification.
    
    Update Log V25.2:
    - New: Vertical Alignment Logic (Penyusunan 3D/4D presisi, bukan comot BBFS).
    - New: Biji-Sum Filter (Menyaring line 3D/4D berdasarkan total jumlah digit).
    - Legacy: Long-Gap Recovery, AS-Indeks Rebound, MB_POWER, & Heritage tetap ON.
    """
    if not all_res_data:
        return {"error": "No data available"}

    # --- [ DATA INITIALIZATION ] ---
    last_p1 = all_res_data[0][0]  # Result terakhir P1
    p1_list = [d[0] for d in all_res_data] 
    
    p2_raw = all_res_data[0][1] if len(all_res_data[0]) > 1 else "0000"
    p3_raw = all_res_data[0][2] if len(all_res_data[0]) > 2 else "0000"
    p2_last = p2_raw if p2_raw != "0000" else (all_res_data[1][0] if len(all_res_data) > 1 else "0000")
    p3_last = p3_raw if p3_raw != "0000" else (all_res_data[2][0] if len(all_res_data) > 2 else "0000")

    # --- [ PHASE 1: THE DIVINE SELECTION ] ---
    divine_pool = []
    all_30d = "".join(p1_list[:30])
    freq_map = Counter(all_30d)
    
    # MB Power Elements
    mb_elements = {MB.get(last_p1[2]), MB.get(last_p1[3]), MB.get(last_p1[1])}
    
    # Shadow & Heritage Elements
    shadow_other = {
        ML.get(last_p1[2]), ML.get(last_p1[3]), 
        TY.get(last_p1[2]), TY.get(last_p1[3]), 
        ID.get(last_p1[2]), ID.get(last_p1[3])
    }
    heritage_elements = {
        last_p1[0], last_p1[1], 
        ID.get(last_p1[0]), ID.get(last_p1[1])
    }

    # Gap Analysis Scoring
    gap_scores = {str(i): 0 for i in range(10)}
    for pos in [2, 3]: 
        for digit in range(10):
            gap_count = 0
            for res in p1_list:
                if res[pos] == str(digit): break
                gap_count += 1
            if gap_count > 10: gap_scores[str(digit)] += 150
            if gap_count > 20: gap_scores[str(digit)] += 350

    # Odd-Even Shift Detection
    last_two_digits = [int(last_p1[2]), int(last_p1[3])]
    trigger_shift = (last_two_digits[0] % 2 == last_two_digits[1] % 2)

    # --- [ THE OMNI SCORING ENGINE ] ---
    for i in range(100):
        line = f"{i:02d}"
        h, t = line[0], line[1]
        score = (freq_map[h] * 20) + (freq_map[t] * 20) + (gap_scores[h] + gap_scores[t])
        
        if h in shadow_other: score += 200
        if t in shadow_other: score += 200
        if h in mb_elements: score += 400
        if t in mb_elements: score += 400
        if h in heritage_elements: score += 300
        if t in heritage_elements: score += 300
        if trigger_shift and int(t) % 2 != last_two_digits[1] % 2: score += 250
        if h in (p2_last + p3_last): score += 100
        if t in (p2_last + p3_last): score += 100

        divine_pool.append((line, score))

    # --- [ PHASE 2: ELITE VERIFICATION ] ---
    analyzed_pool = []
    shio_off_id = (int(last_p1[2:]) % 12) or 12
    biji_off = (int(last_p1[2]) + int(last_p1[3])) % 9 or 9
    
    for line, score in sorted(divine_pool, key=lambda x: x[1], reverse=True)[:35]:
        h, t = line[0], line[1]
        biji_val = (int(h) + int(t)) % 9 or 9
        shio_val = (int(line) % 12) or 12
        
        if shio_val == shio_off_id or biji_val == biji_off: continue
        if line in [res[2:] for res in p1_list[:3]]: continue
        
        analyzed_pool.append((line, score))

    # --- [ PHASE 3: SNIPER POSITIONING MATRIX ] ---
    top2_final = [x[0] for x in sorted(analyzed_pool, key=lambda x: x[1], reverse=True)[:12]]
    
    # Penentuan Digit AS & KOP Strategis (Vertical Alignment)
    # Diambil dari statistik frekuensi tapi di-filter agar tidak bentrok dengan 2D
    as_candidates = [d for d, c in freq_map.most_common() if d not in "".join(top2_final[:2])]
    kop_candidates = [ID.get(d) for d in as_candidates] 

    top3, top4 = [], []
    for i, l2 in enumerate(top2_final):
        # 1. Pilih Kop & As dari kandidat terbaik
        kop = kop_candidates[i % len(kop_candidates)]
        as_val = as_candidates[(i + 1) % len(as_candidates)]
        
        # 2. BIJI-SUM FILTER (Verifikasi total digit agar tidak amsyong)
        # Jika biji 3D (Kop+Kep+Ek) sama dengan biji mati, geser digit Kop
        sum_3d = (int(kop) + int(l2[0]) + int(l2[1])) % 9 or 9
        if sum_3d == biji_off:
            kop = str((int(kop) + 1) % 10)
            
        # 3. ANTI-CLASH P2/P3 (Jangan pasang line yang kemarin keluar di prize 2/3)
        line4d = f"{as_val}{kop}{l2}"
        if line4d == p2_last or line4d == p3_last:
            as_val = str((int(as_val) + 1) % 10)
            line4d = f"{as_val}{kop}{l2}"
            
        top3.append(f"{kop}{l2}")
        top4.append(line4d)

    # Re-build Verified Digits untuk BBFS (Hasil dari Sniper terkuat)
    all_sniped_digits = "".join(top4[:5])
    verified_digits = "".join([d[0] for d in Counter(all_sniped_digits).most_common()])
    if len(verified_digits) < 6: verified_digits += "0123456789"

    return {
        'version': 'V25.2 [GOD MODE - ELITE SNIPER]',
        'market': market_name,
        'last_res': last_p1,
        'p2_last': p2_last,
        'p3_last': p3_last,
        'am': verified_digits[:4],
        'ai': verified_digits[4:7],
        'bbfs': "".join(sorted(list(set(verified_digits[:6])))),
        'top2': top2_final,
        'top3': top3[:10],
        'top4': top4[:10],
        'shio': SHIO_MAP.get((int(last_p1[2:]) % 12) or 12, "N/A"),
        'shio_off': SHIO_MAP.get(shio_off_id, "N/A"),
        'macau': f"{top2_final[0]} - {top2_final[1]}",
        'verification_status': 'ELITE_SNIPER_POSITION_LOCKED'
    }

    
@app.route('/', methods=['GET', 'POST'])
def index():
    analysis, selected = None, None
    # Gabungkan semua pasaran untuk dropdown menu
    ALL_POOLS = {**TARGET_POOLS, **SPECIAL_POOLS}
    markets = sorted(ALL_POOLS.keys())
    
    if request.method == 'POST':
        selected = request.form.get('market')
        if selected in ALL_POOLS:
            market_code = ALL_POOLS[selected]
            res_data = fetch_results(market_code, max_pages=3)
            if res_data and len(res_data) >= 8:
                analysis = get_comprehensive_logic_god(res_data, selected)
            else:
                analysis = "ERROR: Data tidak ditemukan atau koneksi gagal."
    return render_template('index.html', markets=markets, analysis=analysis, selected=selected)

if __name__ == '__main__':
    app.run(debug=True)
