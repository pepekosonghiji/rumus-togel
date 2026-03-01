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

def get_comprehensive_logic(all_res_data, market_name):
    """
    QUANTUM HYPER-DIMENSION V24.7 [ULTIMATE-SNIPER]
    Pembaruan: Triple-Layer Verification (Shadow Logic, Balance Sum, Tail Control).
    """
    if not all_res_data:
        return {"error": "No data available"}

    # --- [INISIALISASI DATA] ---
    last_p1 = all_res_data[0][0]  
    p1_list = [d[0] for d in all_res_data] 

    p2_raw = all_res_data[0][1] if len(all_res_data[0]) > 1 else "0000"
    p3_raw = all_res_data[0][2] if len(all_res_data[0]) > 2 else "0000"

    p2_last = p2_raw if p2_raw != "0000" else (all_res_data[1][0] if len(all_res_data) > 1 else "0000")
    p3_last = p3_raw if p3_raw != "0000" else (all_res_data[2][0] if len(all_res_data) > 2 else "0000")

    # --- [A. ANALISA SHIO MATI] ---
    shio_off_id = (int(last_p1[2:]) % 12) or 12

    # --- [B. INTERVAL GAP ANALYSIS] ---
    gap_scores = {str(i): 0 for i in range(10)}
    for pos in [0, 3]: 
        for digit in range(10):
            gap_count = 0
            for res in p1_list:
                if res[pos] == str(digit): break
                gap_count += 1
            if gap_count > 10:
                gap_scores[str(digit)] += 180

    # --- [C. NEURAL & CLUSTER SCORING] ---
    all_30d = "".join(p1_list[:30])
    freq_map = Counter(all_30d)
    cold_digits = [d for d in "0123456789" if freq_map[d] < (len(all_30d)/10)]
    all_p_data = last_p1 + p2_last + p3_last
    cluster_map = Counter(all_p_data)
    hot_clusters = [num for num, count in cluster_map.items() if count >= 2]
    
    scores = {str(i): 0 for i in range(10)}
    for d in scores:
        if d in hot_clusters: scores[d] += 220 
        if d in [ID.get(x) for x in (p2_last + p3_last)]: scores[d] += 85
        if d in cold_digits: scores[d] += 150 
        scores[d] += gap_scores[d] 

        for pos in range(4):
            if len(all_res_data) > 2:
                if d == all_res_data[1][0][pos] == all_res_data[2][0][pos]:
                    scores[d] += 120

    # Mengambil 9 digit terkuat (Layer 1)
    top_digits = "".join([x[0] for x in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:9]])

    # --- [D. BIJI TARGETING] ---
    biji_p1 = (int(last_p1[2]) + int(last_p1[3])) % 9 or 9
    biji_p2 = (int(p2_last[2]) + int(p2_last[3])) % 9 or 9
    biji_off = {biji_p1, biji_p2}
    biji_target = [b for b in range(1, 10) if b not in biji_off]

    # --- [E. LAYER 1: GENERASI 30 KANDIDAT AWAL] ---
    raw_2d = [''.join(p) for p in itertools.product(top_digits, repeat=2)]
    candidates_pool = []
    seen = set()

    shadow_targets = [ML.get(last_p1[2]), TY.get(last_p1[3]), ID.get(last_p1[3])]

    for line in raw_2d:
        if line in seen: continue
        h, t = line[0], line[1]
        b_line = (int(h) + int(t)) % 9 or 9
        
        score_cand = 0
        if (h in cold_digits and t in hot_clusters) or (t in cold_digits and h in hot_clusters): score_cand += 500
        if (int(h) % 2) != (int(t) % 2): score_cand += 120
        
        if h in shadow_targets or t in shadow_targets: score_cand += 150
        
        if line in [res[2:] for res in p1_list[:2]]: score_cand -= 300

        candidates_pool.append((line, score_cand, b_line))
        seen.add(line)

    pre_top_30 = sorted(candidates_pool, key=lambda x: x[1], reverse=True)[:30]

    # --- [F. LAYER 2: VERIFIKASI FINAL & ELIMINASI SAMPAH DINAMIS] ---
    final_jitu_2d = []
    tail_counts = Counter() 

    for line, base_score, b_val in pre_top_30:
        shio_check = (int(line) % 12) or 12
        final_v_score = base_score
        
        # 1. Verifikasi Biji (Wajib)
        if b_val not in biji_target: continue
        
        # 2. Verifikasi Shio Mati (Hukuman sangat berat -1000)
        if shio_check == shio_off_id: final_v_score -= 1000
        
        # 3. Verifikasi Histori P2/P3 (Anti-Zonk)
        if line in [p2_last[2:], p3_last[2:]]: final_v_score -= 600
        
        # 4. Filter Balance Sum (Buang angka terlalu kecil/besar)
        if int(line) < 7 or int(line) > 93: final_v_score -= 400
        
        # 5. Tail Distribution (Maksimal 3 angka per ekor)
        if tail_counts[line[1]] >= 3: final_v_score -= 500
        
        # 6. Verifikasi Twin (Hanya jika ada indikasi twin sebelumnya)
        if line[0] == line[1]:
            if not (last_p1[0] == last_p1[1] or last_p1[2] == last_p1[3]):
                final_v_score -= 500

        # --- [KRITERIA ELIMINASI LANJUTAN] ---
        # Hanya masukkan angka yang memiliki skor akhir benar-benar kuat (> 350)
        # Angka yang skornya di bawah ini dianggap SAMPAH statistik.
        if final_v_score > 350: 
            final_jitu_2d.append((line, final_v_score))
            tail_counts[line[1]] += 1

    # Sorting hasil akhir berdasarkan kekuatan verifikasi (Best of the Best)
    # Tidak lagi memaksa harus 15 baris. Jika hanya 6 yang jitu, tampilkan 6.
    final_sorted_data = sorted(final_jitu_2d, key=lambda x: x[1], reverse=True)
    top2 = [x[0] for x in final_sorted_data]

    # --- [G. 3D & 4D MATRIX POSITIONING] ---
    top3, top4 = [], []
    pos_candidates = [x[0] for x in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8]]

    for i, l2 in enumerate(top2):
        try:
            kop = TY.get(p3_last[i % 4], pos_candidates[(i+1) % 8])
            as_val = MB.get(all_res_data[1][0][0] if len(all_res_data) > 1 else last_p1[0], pos_candidates[(i+2) % 8])
            
            # Anti-Clash Logic: Kop tidak boleh sama dengan Kepala
            if kop == l2[0]:
                kop = ID.get(kop, pos_candidates[(i+3) % 8])
            
            top3.append(f"{kop}{l2}")
            top4.append(f"{as_val}{kop}{l2}")
        except:
            top3.append(f"0{l2}")
            top4.append(f"00{l2}")

    if top2:
        combined_digits = "".join(top2)
        top2_freq = Counter(combined_digits)
        refined_bbfs = "".join([x[0] for x in top2_freq.most_common(6)])
        if len(refined_bbfs) < 6:
            for d in top_digits:
                if d not in refined_bbfs: refined_bbfs += d
                if len(refined_bbfs) == 6: break
    else:
        refined_bbfs = top_digits[:6]
    refined_bbfs = "".join(sorted(refined_bbfs))

    return {
        'version': 'V24.7 [ULTIMATE-SNIPER]',
        'market': market_name,
        'last_res': last_p1,
        'p2_last': p2_last,
        'p3_last': p3_last,
        'am': top_digits[:4], 
        'ai': top_digits[4:7],
        'bbfs': refined_bbfs,
        'top2': top2,
        'top3': top3, 
        'top4': top4,
        'shio': SHIO_MAP.get((int(last_p1[2:]) % 12) or 12, "N/A"),
        'shio_off': SHIO_MAP.get(shio_off_id, "N/A"),
        'macau': f"{top2[0]} - {top2[1]}" if len(top2) > 1 else (top2[0] if top2 else "-")
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
                analysis = get_comprehensive_logic(res_data, selected)
            else:
                analysis = "ERROR: Data tidak ditemukan atau koneksi gagal."
    return render_template('index.html', markets=markets, analysis=analysis, selected=selected)

if __name__ == '__main__':
    app.run(debug=True)
