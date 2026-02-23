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
    
    elif market_name == 'JEJU':
        # --- JEJU MIRROR-BRIDGE LOGIC V14.9 ---
        
        # 1. P3 to P1 Bridge (The Jeju Special)
        # Jeju sering mengambil angka dari Prize 3 (3905) dan mengubahnya via Mistik/Indeks
        p3_digits = all_res_data[0][2]
        for d in p3_digits:
            scores[ID.get(d)] += 28 # Indeks (3->8, 9->4, 0->5, 5->0)
            scores[ML.get(d)] += 18 # Mistik Lama
            
        # 2. Resonansi Angka 7 (Angka Keramat Jeju)
        # Secara statistik, Jeju punya frekuensi angka 7 yang cukup tinggi
        scores['7'] += 20
        
        # 3. Delta P1-P2 (Selisih As P1 dan As P2)
        # Seringkali selisih ini muncul di posisi Kop atau Kepala
        delta_as = abs(int(d0_p1[0]) - int(all_res_data[0][1][0]))
        scores[str(delta_as)] += 25

    elif market_name == 'SAPPORO':
        # --- SAPPORO CROSS-INDEX LOGIC V14.9 ---
        
        # 1. Twin-Front Impact (P3: 4461)
        # Angka 44 di depan P3 biasanya akan memicu angka 9 atau 7 di P1 besoknya
        scores['9'] += 35 # Indeks 4
        scores['7'] += 25 # Mistik 4
            
        # 2. P2 to P1 Transfer (Kop & Kepala)
        # Sapporo sering memindahkan Kop/Kepala P2 (3, 1) ke posisi Ekor P1
        p2_digits = all_res_data[0][1]
        scores[p2_digits[1]] += 22 # Angka 3
        scores[p2_digits[2]] += 22 # Angka 1
        
        # 3. Mistik Shio Ayam
        # Karena result terakhir Shio Ayam, Sapporo sering lompat ke Shio sejalur (Ular/Kerbau)
        # Kita perkuat angka 2 dan 6 sebagai angka jalur
        scores['2'] += 15
        scores['6'] += 15
        
    elif market_name == 'OSAKA':
        # --- OSAKA SHADOW-DETECTION V15.2 ---
        
        # 1. Lindungi Angka Indeks & Tyseen (Anti-Meleset 96)
        # Ambil angka dari AM dan cari bayangannya
        for n in "12345": 
            scores[ID.get(n)] += 15 # Indeks (4 jadi 9)
            scores[TY.get(n)] += 15 # Tyseen (3 jadi 6)
            
        # 2. Twin Front Protection
        # Jika P1 terakhir tidak ada twin, maka potensi twin di periode depan naik
        if len(set(d0_p1)) == 4:
            scores[d0_p1[0]] += 20 # Kuatkan angka depan untuk potensi Twin
            
        # 3. Delta P2-P3 (Tetap digunakan)
        if len(all_res_data[0]) >= 3:
            p2_head = int(all_res_data[0][1][0])
            p3_head = int(all_res_data[0][2][0])
            delta = str(abs(p2_head - p3_head))
            scores[delta] += 25

    elif market_name == 'PHUKET':
        # --- PHUKET CROSS-PRIZE FLOW V15.3 ---
        
        # 1. P2 to P1 Transfer (Analisa Angka 1425)
        # Phuket sering menarik angka tengah dari P2 ke posisi krusial
        if len(all_res_data[0]) >= 2:
            p2_mid = all_res_data[0][1][1:3] # Mengambil angka 42
            for d in p2_mid:
                scores[d] += 25
                scores[TY.get(d)] += 15 # Proteksi Tyseen angka tengah P2
        
        # 2. Ekor P1 Resonance (5963 -> 3)
        # Mistik Baru 3 adalah 9, Mistik Lama 3 adalah 8
        ekor_p1 = d0_p1[3]
        scores[MB.get(ekor_p1)] += 22 
        scores[ML.get(ekor_p1)] += 20
        
        # 3. Phuket "Hot" Number (Berdasarkan AM 1256)
        for n in "1256":
            scores[n] += 12

    elif market_name == 'SEOUL':
        # --- SEOUL DOUBLE-MIRROR LOGIC V15.4 ---
        # 1. Lindungi Angka Indeks & Mistik dari P2 dan P3 (Seoul sangat Mirror-Oriented)
        for res_p in all_res_data[0][1:]: # P2 & P3
            for d in res_p:
                scores[ID.get(d)] += 25
                scores[MB.get(d)] += 15

        # 2. Pola Ekor Lompat 2
        # Jika ekor P1 sekarang ganjil, Seoul sering lompat ke angka ganjil lainnya
        ekor_lalu = int(d0_p1[3])
        if ekor_lalu % 2 != 0:
            for n in "13579": scores[n] += 18
        else:
            for n in "02468": scores[n] += 18

        # 3. Prediksi Twin Tengah (Kop & Kepala)
        scores[ID.get(d0_p1[1])] += 20 

    elif market_name == 'WUHAN':
        # --- WUHAN TRI-VIBRATION LOGIC V15.5 ---
        # 1. Dominansi Angka "Kepala" P1, P2, P3
        # Wuhan sering mengulang angka depan (As/Kop) dari periode sebelumnya
        for res_p in all_res_data[0]:
            scores[res_p[0]] += 30 # Fokus As
            scores[res_p[1]] += 22 # Fokus Kop

        # 2. Wuhan "Hot" Delta
        # Selisih antara Kepala P1 dan Ekor P2 sering jadi AI kuat
        delta_wuhan = abs(int(d0_p1[2]) - int(all_res_data[0][1][3]))
        scores[str(delta_wuhan)] += 35
        scores[TY.get(str(delta_wuhan), '0')] += 20

    elif market_name == 'DANANG':
        # --- DANANG TWIN & ANCHOR LOGIC V15.7 ---
        
        # 1. Anchor Protection (Mencegah Angka 0 Terbuang)
        # Danang sering membawa kembali As/Kop P1 (7 dan 0)
        scores[d0_p1[0]] += 25 
        scores[d0_p1[1]] += 25

        # 2. Ekor Chain Transfer (P2 & P3)
        if len(all_res_data[0]) >= 3:
            eko_p2 = all_res_data[0][1][3] 
            eko_p3 = all_res_data[0][2][3] 
            scores[eko_p2] += 28
            scores[eko_p3] += 28
            scores[ID.get(eko_p2)] += 15
            scores[ID.get(eko_p3)] += 15

        # 3. Resonansi Mistik Kop P1 (7093 -> 0)
        kop_p1 = d0_p1[1]
        scores[ML.get(kop_p1)] += 20
        scores[MB.get(kop_p1)] += 20
        
        # 4. Twin-Sense & Biji 9 (0477 -> Total 18/Biji 9)
        # Menambahkan bobot untuk angka yang membentuk harmoni biji 9
        for n in "0479":
            scores[n] += 15

    elif market_name == 'PENANG':
        # --- PENANG DIAGONAL-MIRROR LOGIC V15.8 ---
        
        # 1. P2 & P3 Mirroring (P2: 2509, P3: 4374)
        # Penang sangat sering mengambil Indeks dari angka tengah P2
        if len(all_res_data[0]) >= 3:
            p2_mid = all_res_data[0][1][1:3] # Angka 50
            for d in p2_mid:
                scores[ID.get(d)] += 28 # Indeks 5->0, 0->5 (Double 0/5 protection)
                scores[ML.get(d)] += 18
        
        # 2. Resonansi Angka 4 (Ekor P3: 4374)
        # Ekor P3 yang sama dengan Kop P1 (9465) sering memicu angka Mistik Baru
        scores[MB.get('4')] += 25 # Angka 5
        
        # 3. Penang "High-Frequency" (Berdasarkan AM 1458)
        # Mengunci angka 1, 5, dan 8 sebagai poros BBFS
        for n in "158":
            scores[n] += 15
    
    # --- 3. GLOBAL SEED VERIFICATION ---
    seeds = [ML.get(d0_p1[0]), ID.get(d0_p1[2]), TY.get(d0_p1[3]), MB.get(d0_p1[1])]
    for s in seeds: scores[s] += 12

    # URUTKAN & PAKSA 6 DIGIT
    sorted_res = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_res[:6]], scores

def generate_titanium_lines_v14(bbfs_list, last_p1, market_name, scores, all_res_data, count=10):
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

        elif market_name == 'JEJU':
            # Jeju dominan di Biji 1, 5, 8
            if biji_f in [1, 5, 8]: score += 65
            
            # Pattern Bridge: Jika ekor adalah Mistik/Indeks dari Kepala P3 (3905 -> 3)
            # Kepala P3 adalah 3, maka ekor jitu adalah 8 (ID) atau 6 (TY)
            if t in [ID.get(last_p1[2]), TY.get(last_p1[2])]: score += 40
            
            # Anti-Clutter: Jeju jarang mengeluarkan angka berurutan (12, 23, dll)
            if abs(int(h) - int(t)) == 1: score -= 15

        elif market_name == 'SAPPORO':
            # Sapporo sangat kuat di Biji 3, 4, 9
            if biji_f in [3, 4, 9]: score += 65
            
            # Khusus Sapporo: Cek jika angka adalah Mistik dari Ekor P1 (5 -> 2)
            if t == ML.get(last_p1[3]): score += 45
            
            # Anti-Twin di posisi 2D Belakang
            if h == t: score -= 30

        # --- [OSAKA SPECIFIC RACIKAN] ---
        elif market_name == 'OSAKA':
            # Osaka dominan di Biji 4, 6, 8
            if biji_f in [4, 6, 8]: score += 65
            # Jika angka belakang sama dengan Mistik Lama dari ekor P1 (5 -> 2)
            if t == ML.get(last_p1[3]): score += 40
            # Bonus untuk angka yang mengandung unsur AI (0 atau 2)
            if '0' in line or '2' in line: score += 25

        # --- [PHUKET SPECIFIC RACIKAN] ---
        elif market_name == 'PHUKET':
            # Phuket dominan di Biji 1, 2, 5, 7
            if biji_f in [1, 2, 5, 7]: score += 65
            # Head-to-Head: Jika angka depan 2D adalah angka dari P3 (3018 -> 1)
            if h in all_res_data[0][2]: score += 35
            # Bonus jika mengandung unsur AI (1 atau 8)
            if '1' in line or '8' in line: score += 25

        elif market_name == 'SEOUL':
            # Seoul identik dengan Biji 1, 4, 7 (Siklus 3)
            if biji_f in [1, 4, 7]: score += 65
            if h == ID.get(last_p1[2]): score += 35 # Indeks Kepala

        elif market_name == 'WUHAN':
            # Wuhan identik dengan Biji 2, 6, 9
            if biji_f in [2, 6, 9]: score += 65
            if t == MB.get(last_p1[3]): score += 40 # Mistik Baru Ekor

        # --- [DANANG MAXIMAL PRECISION V15.7] ---
        elif market_name == 'DANANG':
            # 1. Biji Utama Danang (3, 6, 9)
            if biji_f in [3, 6, 9]: score += 75 # Skor dinaikkan
            
            # 2. Twin Detection (Belajar dari 77)
            # Jika ada potensi twin di 2D belakang, beri bonus skor
            if h == t: score += 50 
            
            # 3. Head-to-Head Logic
            # Jika ekor 2D adalah Mistik/Indeks dari As atau Kop P1
            if t in [ML.get(last_p1[0]), ID.get(last_p1[0]), ML.get(last_p1[1])]:
                score += 45
                
            # 4. Injeksi Angka 0 (Anchor)
            if '0' in line: score += 30

        # --- [PENANG MAXIMAL PRECISION V15.8] ---
        elif market_name == 'PENANG':
            # 1. Biji Favorit Penang (2, 4, 7, 8)
            if biji_f in [2, 4, 7, 8]: score += 70
            
            # 2. Diagonal Check
            # Jika angka depan 2D adalah Indeks dari ekor P1 (9465 -> 5)
            # Indeks 5 adalah 0. Jika ada angka 0 di depan, skor naik.
            if h == ID.get(last_p1[3]): score += 40
            
            # 3. Bonus AI (0 atau 1)
            if '0' in line or '1' in line: score += 30
            
            # 4. Anti-Twin di 2D Belakang (Penang jarang twin belakang)
            if h == t: score -= 25
                
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
    
    # --- [ V15.1 PRE-CALCULATION ] ---
    # Mengambil 3 angka terkuat dari masing-masing posisi berdasarkan bobot scores global
    # Ini memastikan As dan Kop bukan sekadar rotasi, tapi benar-benar angka jitu
    best_as = sorted(res_map['as'], key=lambda x: scores.get(x, 0), reverse=True)[:3]
    best_kop = sorted(res_map['kop'], key=lambda x: scores.get(x, 0), reverse=True)[:3]

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

        # --- [ V15.1 FINAL VERIFICATION LAYER ] ---
        # 1. Validasi Kop & As menggunakan Best Position
        # Jika rotasi menghasilkan angka lemah, ganti dengan salah satu dari 3 angka terkuat
        if i < 5: # Fokus pengetatan pada Top 5 Line
            if scores.get(kop, 0) < scores.get(best_kop[0], 0):
                kop = best_kop[i % len(best_kop)]
            if scores.get(asn, 0) < scores.get(best_as[0], 0):
                asn = best_as[i % len(best_as)]

        # 2. Sum-Biji Harmony Check (Total 4D harus di rentang 10 - 32)
        # Jika total angka terlalu ekstrem, lakukan Shift-Indeks pada As
        line_check = f"{asn}{kop}{l2}"
        total_4d = sum(int(d) for d in line_check)
        
        if total_4d < 10 or total_4d > 32:
            asn = ID.get(asn) # Tukar ke angka bayangan untuk menyeimbangkan vibrasi
            
        top3.append(f"{kop}{l2}")
        top4.append(f"{asn}{kop}{l2}")

    # 3. Final Harmony Sorting
    # Baris yang memiliki jumlah total 15, 18, 24, 27 (Angka Harmoni Bandot) dinaikkan
    top4.sort(key=lambda x: 1 if sum(int(d) for d in x) in [15, 18, 24, 27] else 0, reverse=True)
    
    return top2, top3, top4

def get_comprehensive_logic(all_res_data, m_name):
    d0_p1 = all_res_data[0][0] # Ambil P1 terakhir (4 digit)
    bbfs_raw, scores_data = get_weighted_bbfs_v14_1(all_res_data, m_name) 
    
    # 2D Belakang untuk Shio
    dua_d_belakang = int(d0_p1[2:])
    shio_idx = dua_d_belakang % 12
    
    top2, top3, top4 = generate_titanium_lines_v14(bbfs_raw, d0_p1, m_name, scores_data, all_res_data)
    
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True) as client:
            if market_code == "HK_SPECIAL":
                url = "https://tabelsemalam.com/"
                r = client.get(url, headers=headers)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if not table: return []
                res = []
                for row in table.find('tbody').find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 4: # Pastikan kolom cukup untuk P1, P2, P3
                        p1 = re.sub(r'\D', '', tds[1].text.strip())
                        p2 = re.sub(r'\D', '', tds[2].text.strip())
                        p3 = re.sub(r'\D', '', tds[3].text.strip())
                        if len(p1) == 4:
                            # Masukkan ketiga prize ke dalam list
                            res.append([p1, p2, p3])
                return res[:40]
            
            # Jalur Umum (Tetap sama, tapi tambahkan proteksi list)
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
                        # Proteksi: Jika P2 atau P3 kosong di web, isi '0000' biar gak error
                        p2 = get_num(tds[4]) if len(tds) >= 5 else "0000"
                        p3 = get_num(tds[5]) if len(tds) >= 6 else "0000"
                        results.append([p1, p2, p3])
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

if __name__ == '__main__':
    app.run(debug=True)
