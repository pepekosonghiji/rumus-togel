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
    🚀 MAMANG ENGINE V.24.8 [GOD MODE] 🚀
    QUANTUM HYPER-DIMENSION - OMNI-INTELLIGENCE
    Sistem Verifikasi Berlapis: Divine Selection, God Analysis, & Holy Verification.
    """
    if not all_res_data:
        return {"error": "No data available"}

    # --- [ DATA INITIALIZATION ] ---
    last_p1 = all_res_data[0][0]  # Result terakhir P1
    p1_list = [d[0] for d in all_res_data] # List histori P1
    
    # Mengambil data Prize 2 dan Prize 3 jika tersedia
    p2_raw = all_res_data[0][1] if len(all_res_data[0]) > 1 else "0000"
    p3_raw = all_res_data[0][2] if len(all_res_data[0]) > 2 else "0000"
    p2_last = p2_raw if p2_raw != "0000" else (all_res_data[1][0] if len(all_res_data) > 1 else "0000")
    p3_last = p3_raw if p3_raw != "0000" else (all_res_data[2][0] if len(all_res_data) > 2 else "0000")

    # --- [ PHASE 1: THE DIVINE SELECTION ] ---
    # Mencari 20 kandidat terkuat dengan metode terbaik di muka bumi.
    divine_pool = []
    
    # 1. Frequency Analysis (30 hari terakhir)
    all_30d = "".join(p1_list[:30])
    freq_map = Counter(all_30d)
    
    # 2. Shadow Target Elements (Mistik, Taysen, Indeks dari Result Terakhir)
    shadow_elements = {
        ML.get(last_p1[2]), ML.get(last_p1[3]), 
        TY.get(last_p1[2]), TY.get(last_p1[3]), 
        ID.get(last_p1[2]), ID.get(last_p1[3]),
        MB.get(last_p1[2]), MB.get(last_p1[3])
    }

    # 3. Gap Analysis Scoring
    gap_scores = {str(i): 0 for i in range(10)}
    for pos in [2, 3]: # Fokus pada ekor 2D
        for digit in range(10):
            gap_count = 0
            for res in p1_list:
                if res[pos] == str(digit): break
                gap_count += 1
            if gap_count > 10: gap_scores[str(digit)] += 150

    # Kalkulasi skor awal untuk seluruh kombinasi 00-99
    for i in range(100):
        line = f"{i:02d}"
        h, t = line[0], line[1]
        
        # Base Score dari Frekuensi & Gap
        score = (freq_map[h] * 20) + (freq_map[t] * 20)
        score += (gap_scores[h] + gap_scores[t])
        
        # Shadow Bonus (Metafisika Digital)
        if h in shadow_elements: score += 200
        if t in shadow_elements: score += 200
        
        # Cluster Bonus (Kaitan dengan P2/P3)
        if h in (p2_last + p3_last): score += 100
        if t in (p2_last + p3_last): score += 100

        divine_pool.append((line, score))

    # FILTER: Ambil "The Elite 20" (Kandidat Terkuat di Muka Bumi)
    elite_20 = sorted(divine_pool, key=lambda x: x[1], reverse=True)[:20]

    # --- [ PHASE 2: THE GOD ANALYSIS ] ---
    # Membedah kembali 20 kandidat dengan analisa sumbu posisi.
    analyzed_20 = []
    for line, score in elite_20:
        god_score = score
        h, t = line[0], line[1]
        
        # Biji Analysis (Sum of Digits)
        biji_val = (int(h) + int(t)) % 9 or 9
        
        # Pola Psikologis Angka (Small/Big, Odd/Even)
        # Memberikan bobot pada keseimbangan distribusi
        if int(line) >= 50: god_score += 50 # Bonus Big
        if int(t) % 2 != 0: god_score += 50 # Bonus Odd Tail
        
        # Pinalti jika angka terlalu sering muncul di histori (Anti-Saturation)
        if line in [res[2:] for res in p1_list[:3]]:
            god_score -= 1000 # Sangat berat untuk angka repeat
            
        analyzed_20.append((line, god_score, biji_val))

    # --- [ PHASE 3: THE HOLY VERIFICATION ] ---
    # Penyaringan akhir dengan metode verifikasi paling ketat.
    final_jitu_2d = []
    shio_off_id = (int(last_p1[2:]) % 12) or 12
    biji_off = (int(last_p1[2]) + int(last_p1[3])) % 9 or 9
    
    # Tail distribution guard untuk mencegah angka dengan ekor yang sama terlalu banyak
    tail_guard = Counter()

    for line, score, biji in sorted(analyzed_20, key=lambda x: x[1], reverse=True):
        shio_val = (int(line) % 12) or 12
        
        # 1. ABSOLUTE FILTER: Shio Mati & Biji Mati
        if shio_val == shio_off_id: continue
        if biji == biji_off: continue
        
        # 2. ABSOLUTE FILTER: History Check P2/P3
        if line in [p2_last[2:], p3_last[2:]]: continue
        
        # 3. DISTRIBUTION FILTER: Maksimal 3 angka dengan ekor yang sama
        if tail_guard[line[1]] >= 3: continue
        
        # 4. TWIN VERIFICATION: Hanya lolos jika skor sangat tinggi
        if line[0] == line[1] and score < 800: continue

        final_jitu_2d.append((line, score))
        tail_guard[line[1]] += 1

    # HASIL FINAL 2D (The Chosen Ones)
    top2 = [x[0] for x in sorted(final_jitu_2d, key=lambda x: x[1], reverse=True)]

    # --- [ 4D & 3D POSITIONING MATRIX GOD - FULL SYNC ] ---
    top3, top4 = [], []
    
    # Ambil urutan digit terkuat untuk posisi depan
    verified_digits = "".join([d[0] for d in Counter("".join(top2)).most_common()])
    if len(verified_digits) < 6: verified_digits += "0123456789"

    # LOOPING DINAMIS: Mengikuti jumlah top2 yang lolos verifikasi
    for i, l2 in enumerate(top2):
        # Ambil Kop dan As berdasarkan index urutan
        kop = verified_digits[(i + 1) % len(verified_digits)]
        as_val = verified_digits[(i + 2) % len(verified_digits)]
        
        # Anti-Clash: Jika angka depan 2D sama dengan Kop, geser index
        if kop == l2[0]:
            kop = verified_digits[(i + 3) % len(verified_digits)]
        
        top3.append(f"{kop}{l2}")
        top4.append(f"{as_val}{kop}{l2}")

    # --- [ FINAL OUTPUT ASSEMBLY ] ---
    return {
        'version': 'V24.8 [GOD MODE]',
        'market': market_name,
        'last_res': last_p1,
        'p2_last': p2_last,
        'p3_last': p3_last,
        'am': verified_digits[:4],
        'ai': verified_digits[4:7],
        'bbfs': "".join(sorted(list(set(verified_digits[:6])))),
        'top2': top2,
        'top3': top3,
        'top4': top4,
        'shio': SHIO_MAP.get((int(last_p1[2:]) % 12) or 12, "N/A"),
        'shio_off': SHIO_MAP.get(shio_off_id, "N/A"),
        'macau': f"{top2[0]} - {top2[1]}" if len(top2) > 1 else (top2[0] if top2 else "-"),
        'verification_status': 'STRICT_GOD_MODE_ACTIVE'
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
