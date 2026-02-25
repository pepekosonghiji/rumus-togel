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
    scores = {str(n): 0 for n in range(10)}
    p1_history = [res[0] for res in all_res_data]
    d0_p1 = p1_history[0]
    
    freq_p1 = Counter("".join(p1_history[:30]))
    for n in "0123456789":
        # Skor Prize 1 (Utama)
        scores[n] += freq_p1.get(n, 0) * 1.5
        # Repeat Number Protection
        if n in d0_p1: scores[n] += 15
    
    for res in all_res_data[:10]:
        if len(res) > 1:
            shadow = "".join(res[1:])
            for n in set(shadow): scores[n] += 5

    if market_name == 'CAMBODIA':
        # --- [V16.8 CAMBODIA DYNAMIC WEIGHT] ---
        # Ambil semua angka dari P1, P2, P3
        p_list = [res for res in all_res_data[0] if res] if all_res_data else []
        all_p_digits = "".join(p_list)
            
        for digit in set(all_p_digits):
            if digit.isdigit():
                # Indeks & Mistik tetap jadi fondasi
                scores[ID.get(digit, digit)] += 30 
                scores[ML.get(digit, digit)] += 15 
                # Peningkatan: Bobot angka mentah Prize 3 dinaikkan
                if len(all_res_data[0]) > 2 and digit in all_res_data[0][2]:
                    scores[digit] += 25 
        
        # Delta Analysis dengan proteksi error
        if len(d0_p1) >= 4 and d0_p1[2].isdigit() and d0_p1[3].isdigit():
            delta = str(abs(int(d0_p1[2]) - int(d0_p1[3])))
            scores[delta] = scores.get(delta, 0) + 35
            scores[TY.get(delta, '0')] = scores.get(TY.get(delta, '0'), 0) + 25
        
        # Penajaman AI: Angka 9 dan 4 (Mistik/Indeks dari tren saat ini)
        for n in ['3', '8', '9', '4']: 
            scores[n] = scores.get(n, 0) + 20

    elif market_name == 'HONGKONG LOTTO':
        # --- [V16.26 HK-RESONANCE UPGRADE] ---
        # 1. P2/P3 TRANSIT (Tetap dipertahankan)
        p2_res = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
        p3_res = all_res_data[0][2] if len(all_res_data[0]) > 2 else ""
        transit_digits = set(p2_res + p3_res)
        for d in transit_digits:
            scores[ID.get(d, d)] += 35  
            scores[d] += 20          
            
        # 2. ZERO-SLOT DETECTION (Update khusus result 3006)
        # Jika result P1 kemarin mengandung angka kembar (7736), 
        # maka vibrasi angka '0' naik drastis sebagai penetral.
        if d0_p1[0] == d0_p1[1] or d0_p1[2] == d0_p1[3]:
            scores['0'] += 50 # Angka 0 menjadi prioritas utama
            scores['5'] += 30 # Indeks 0 ikut naik

        # 3. EKOR-TO-AS RESONANCE 
        e_lalu = d0_p1[3]
        scores[ID.get(e_lalu, e_lalu)] += 30 
        scores[MB.get(e_lalu, e_lalu)] += 25
        
    elif market_name == 'MACAU':
        scores[str((int(d0_p1[3]) + 1) % 10)] += 15
        scores[str((int(d0_p1[3]) - 1) % 10)] += 15
        scores[ID.get(d0_p1[1], '0')] += 10 

    elif market_name == 'SYDNEY LOTTO':
        # --- [V16.9 SYDNEY NEIGHBOR & COLD POWER] ---
        for digit in d0_p1:
            if digit.isdigit():
                val = int(digit)
                # Logika Tetangga & Lompat (Khas Sydney)
                scores[str((val + 1) % 10)] += 22 
                scores[str((val - 1) % 10)] += 22
                scores[str((val + 2) % 10)] += 20 
                scores[str((val - 2) % 10)] += 20
                
                # Mistik & Indeks (Resonansi Mirror)
                scores[MB.get(digit, '0')] += 25 
                scores[ID.get(digit, '0')] += 30 

        # Cold Number Detection (Angka yang jarang muncul dalam 5 hari terakhir)
        p1_short = "".join([res[0] for res in all_res_data[:5] if res])
        for n in "0123456789":
            if n not in p1_short:
                scores[n] += 30 
            # Prioritas Range Tengah Sydney (2-7)
            if n in "234567":
                scores[n] += 15
    
    elif market_name == 'COLORADO':
        scores[MB.get(d0_p1[1], '0')] += 20
        scores[ID.get(d0_p1[2], '0')] += 20
        cold_check = "".join(p1_history[:5])
        for n in "0123456789":
            if n not in cold_check: scores[n] += 25

    elif market_name == 'BUSAN POOLS':
        for i in range(len(d0_p1)-1):
            if d0_p1[i] == d0_p1[i+1]:
                twin_digit = d0_p1[i]
                scores[ID.get(twin_digit)] += 35 # Indeks (4->9)
                scores[ML.get(twin_digit)] += 25 # Mistik Lama (4->7)
            if '0' in all_res_data[0][2]:
                scores['0'] += 35
        if len(all_res_data[0]) >= 2:
            p2_digits = all_res_data[0][1]
            for d in p2_digits:
                scores[d] += 20
                scores[TY.get(d, '0')] += 15 # Tyseen dari P2
        for n in "0123456789":
            if int(n) % 3 == 0 and n != '0':
                scores[n] += 18
    
    elif market_name == 'JEJU':
        p3_digits = all_res_data[0][2]
        for d in p3_digits:
            scores[ID.get(d)] += 28 # Indeks (3->8, 9->4, 0->5, 5->0)
            scores[ML.get(d)] += 18 # Mistik Lama
        scores['7'] += 20
        delta_as = abs(int(d0_p1[0]) - int(all_res_data[0][1][0]))
        scores[str(delta_as)] += 25

    elif market_name == 'SAPPORO':
        scores['9'] += 35 # Indeks 4
        scores['7'] += 25 # Mistik 4
        p2_digits = all_res_data[0][1]
        scores[p2_digits[1]] += 22 # Angka 3
        scores[p2_digits[2]] += 22 # Angka 1
        scores['2'] += 15
        scores['6'] += 15
        
    elif market_name == 'OSAKA':
        # --- [V16.19 OSAKA VORTEX - STEP-UP & TWIN JUMP] ---
        # 1. TWIN MIRROR JUMP (Result 3357 -> Twin 33)
        # Jika keluar twin, periode depan biasanya angka tersebut di-Indeks atau Mistik
        t_digit = d0_p1[0] # Angka 3
        scores[ID.get(t_digit, '8')] += 35 # 3 -> 8 (Kunci Utama)
        scores[ML.get(t_digit, '8')] += 25 # 3 -> 8 (Double Lock!)
        
        # 2. STEP-UP CORRECTION (Ekor 7)
        # Mengantisipasi bandot yang hobi naik/turun tangga (6->7->8 atau 6->7->6)
        e_lalu = int(d0_p1[3])
        step_up = str((e_lalu + 1) % 10)
        step_down = str((e_lalu - 1) % 10)
        scores[step_up] += 30 # Angka 8
        scores[step_down] += 20 # Angka 6
        
        # 3. GHOST EXTRACTION (Ambil angka dingin dari P2/P3)
        p2_res = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
        p3_res = all_res_data[0][2] if len(all_res_data[0]) > 2 else ""
        ghost_digits = set(p2_res + p3_res)
        for d in ghost_digits:
            scores[d] += 15
            scores[ID.get(d)] += 15

        # 4. OSAKA ANCHOR (AI 82)
        # 8 dari Indeks Twin 3, 2 dari Mistik 5
        scores['8'] += 30
        scores['2'] += 25

    elif market_name == 'SEOUL':
        # --- [V16.16 SEOUL GHOST-PRIZE LOGIC] ---
        # 1. GHOST-PRIZE EXTRACTION (P2 & P3)
        # Menangkap angka yang muncul di P2/P3 tapi tidak ada di P1 (Angka 7 di 9760)
        p1_set = set(d0_p1)
        p2_res = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
        p3_res = all_res_data[0][2] if len(all_res_data[0]) > 2 else ""
        
        ghost_digits = set(p2_res + p3_res) - p1_set
        for d in ghost_digits:
            scores[d] += 40 # Kasih bobot tinggi untuk angka "asing" (Seperti 7 tadi)
            if d in ID: scores[ID[d]] += 20
            
        # 2. THE MIDDLE-MAN (Kop P2 & P3)
        # Seoul sering narik Kop P2/P3 (angka 7 dan 4) ke posisi krusial
        if len(p2_res) > 1: scores[p2_res[1]] += 30
        if len(p3_res) > 1: scores[p3_res[1]] += 30

        # 3. BIJI EVOLUTION (Delta Biji)
        # Menghitung Biji P1 (7) dan Biji P2 (22->4). Selisihnya (3) jadi AI
        b_p1 = sum(int(x) for x in d0_p1) % 9 or 9
        b_p2 = sum(int(x) for x in p2_res) % 9 or 9 if p2_res else 0
        delta_biji = str(abs(b_p1 - b_p2))
        scores[delta_biji] += 25

        # 4. SEOUL ANCHOR 
        # Tetap jaga 4, 7, 8 sebagai angka sirkulasi
        for n in "478": scores[n] += 25

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

    elif market_name == 'PHUKET':
        # --- [V16.21 PHUKET ULTIMATE - SANDWICH & BRIDGE] ---
        # 1. SANDWICH VERIFICATION (Result 2452 -> As=Ekor=2)
        # Jika As & Ekor kembar, periode depan angka tengah (4-5) sering jadi As/Kop
        if d0_p1[0] == d0_p1[3]:
            scores[d0_p1[1]] += 35 # Angka 4
            scores[d0_p1[2]] += 35 # Angka 5
            # Indeks dari angka sandwich (2 -> 7)
            scores[ID.get(d0_p1[0])] += 25 
            
        # 2. THE BRIDGE (Angka Berurutan 4-5)
        # Phuket suka angka berurutan. Setelah 4-5, potensi 6 atau 3 sangat besar.
        bridge_next = str((int(d0_p1[2]) + 1) % 10) # 5 -> 6
        bridge_prev = str((int(d0_p1[1]) - 1) % 10) # 4 -> 3
        scores[bridge_next] += 30 
        scores[bridge_prev] += 20

        # 3. P2-P3 REBORN (P2: 5905, P3: 0184)
        # Angka 9 dan 8 belum keluar di P1. Ini angka "Hutang".
        p2_res = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
        p3_res = all_res_data[0][2] if len(all_res_data[0]) > 2 else ""
        for d in "89":
            if d in (p2_res + p3_res): scores[d] += 40
            
        # 4. PHUKET AI ANCHOR (AI 68)
        scores['6'] += 30
        scores['8'] += 30

    elif market_name == 'DANANG':
        # --- [V16.22 DANANG DIAGONAL SHIFT FIXED] ---
        # 1. Lindungi Indeks/Mirror P1, P2, P3 (Gaya Aman)
        all_p_digits = d0_p1 # Isi P1 (0477)
        if len(all_res_data[0]) > 2:
            # Mengambil P2 dan P3 dari indeks yang sama dengan logic Cambodia/Seoul Mamang
            all_p_digits += all_res_data[0][1] + all_res_data[0][2]
            
        for digit in set(all_p_digits):
            if digit in ID: scores[ID.get(digit)] += 30 
            if digit in TY: scores[TY.get(digit)] += 15 
            
        # 2. TWIN-ESCAPE (Result 0477 -> Ada Twin 77)
        # Jika ada angka kembar, kita ledakkan Indeksnya (7 -> 2)
        if d0_p1[2] == d0_p1[3]:
            scores['2'] += 40 # Indeks dari 7
            scores['5'] += 25 # Mistik dari 2
            
        # 3. PRIZE-CROSS SENSOR
        # Mencari angka yang muncul di P2/P3 tapi tidak ada di P1 (Contoh: Angka 2)
        if len(all_res_data[0]) > 2:
            p23_digits = all_res_data[0][1] + all_res_data[0][2]
            if '2' in p23_digits: scores['2'] += 20
            if '9' in p23_digits: scores['9'] += 20

        # 4. DANANG AI ANCHOR
        scores['2'] += 20
        scores['0'] += 15

    elif market_name == 'GREECE':
        # --- [V16.6 GREECE STEP-DOWN & MIRROR LOGIC] ---
        # 1. ANALISA TRANSIT P2/P3 (Resonansi Cross-Pool)
        if len(all_res_data[0]) >= 2:
            p2_digits = all_res_data[0][1]
            p3_digits = all_res_data[0][2] if len(all_res_data[0]) > 2 else ""
            for d in set(p2_digits + p3_digits):
                if d.isdigit():
                    scores[ID.get(d, d)] += 35 # Indeks adalah prioritas utama Greece
                    scores[TY.get(d, d)] += 20 # Tyseen sebagai cadangan
        
        # 2. INDEKS BALIK (Belajar dari 7121)
        # Jika P1 lama punya angka 1 atau 7, potensi Indeksnya (6 atau 2) sangat besar
        for d in d0_p1:
            if d in ['1', '7', '2']:
                scores[ID.get(d, d)] += 40
                scores[ML.get(d, d)] += 25

        # 3. GREECE SOLID ANCHOR (Angka yang sering bertahan/Stay)
        # Angka 8 dan 4 memiliki persistensi tinggi di Greece
        scores['8'] += 30
        scores['4'] += 25
        
        # 4. ZERO RESONANCE
        if '0' not in d0_p1: scores['0'] += 20

    elif market_name == 'MANHATTAN':
        # --- [V16.5 MANHATTAN REBORN - AS 7 SECURED] ---
        
        # 1. AI Booster (AI 57) -> Pertahankan karena JP AS 7
        scores['7'] += 45 # Naikkan sedikit untuk mengunci As/Kepala
        scores['5'] += 25

        # 2. P2-Tail Transfer Logic (Merespon Result 7101)
        # Manhattan menarik Ekor P2 (6331 -> 1) ke posisi Kop dan Ekor P1
        if len(all_res_data[0]) >= 2:
            eko_p2 = all_res_data[0][1][3]
            scores[eko_p2] += 35 # Angka 1 masuk radar utama
            scores[ID.get(eko_p2)] += 15 # Indeks 1 -> 6 sebagai cadangan

        # 3. As-Mirroring Resonance (Result 7101 -> 7)
        # Jika P1 sebelumnya 5402, Manhattan sering memanggil Mistik Baru As (5 -> 4)
        # atau Indeks As (5 -> 0).
        as_p1 = d0_p1[0]
        scores[MB.get(as_p1)] += 20
        scores[ID.get(as_p1)] += 20

        # 4. Zero & Tyseen Protection (2 -> 9)
        eko_p1_last = d0_p1[3]
        scores[TY.get(eko_p1_last)] += 25 # Angka 9 tetap kuat
        scores['0'] += 15 # Angka 0 tetap dijaga karena muncul di 7101

    elif market_name == 'TORONTOEVE':
        # --- [V16.8 TORONTOEVE REBORN - AS 8 & HEAD 0 SECURED] ---
        
        # 1. Tyseen-As Protection (P1 Ekor 5 -> Result AS 8)
        # Terbukti JP, kita naikkan bobot untuk mengunci As periode depan
        eko_p1 = d0_p1[3]
        scores[TY.get(eko_p1)] += 40 
        
        # 2. Self-Mirroring (As lari ke Ekor via Mistik Lama)
        # Menangkap pola 8 -> 3 (Mistik Lama)
        as_p1 = d0_p1[0]
        scores[ML.get(as_p1)] += 30 
        
        # 3. Direct Prize-Transfer (Merespon Result 8703 yang bawa angka 7)
        # Toronto hobi membawa angka mentah dari P2 (7916) ke P1
        if len(all_res_data[0]) >= 2:
            scores[all_res_data[0][1][0]] += 25 # Angka 7
            scores[all_res_data[0][1][1]] += 25 # Angka 9

        # 4. Toronto AI Strength (AI 01)
        # Angka 0 terbukti JP di Kepala, pertahankan!
        scores['0'] += 20
        scores['1'] += 20

    elif 'OREGON' in market_name:
        # --- [V16.13 OREGON DOUBLE-WRAP & MISTIK JUMP] ---
        
        # 1. Mistik Baru Jump (As 8 -> Result 9)
        # Menangkap perubahan As menjadi Mistik Baru yang sering jadi angka "Wrap" (As & Ekor)
        as_last = d0_p1[0]
        scores[MB.get(as_last, '0')] += 45 # Mengunci angka 9
        
        # 2. Kop-to-Kop Mirror (Kop 8 & Kepala 5 -> Result 2)
        # Oregon menarik Mistik Lama dari angka tengah P1
        scores[ML.get(d0_p1[2], '0')] += 35 # Mistik Lama 5 adalah 2
        
        # 3. Vertical Step-Up (Ekor 5 -> Result 6)
        # Jika pola Vertical Shift gagal (5 jadi 5), biasanya lari ke Step-Up (+1)
        eko_last = d0_p1[3]
        scores[str((int(eko_last) + 1) % 10)] += 30 # Mengunci angka 6
        
        # 4. Oregon AI Stability (AI 16)
        # Angka 6 sudah JP, kita jaga untuk periode berikutnya (Oregon 9)
        scores['1'] += 25
        scores['6'] += 25

    elif market_name == 'WASHINGMID':
        # --- [V16.11 WASHINGMID REBORN - SLIDE & MIRROR CAPTURE] ---
        
        # 1. Slide Position Protection (P1: 4560 -> As 4)
        # Menangkap angka Kop atau Kepala periode sebelumnya untuk naik jadi As
        scores[d0_p1[0]] += 20 # As lama
        scores[d0_p1[1]] += 35 # Kop lama (Sangat rawan jadi As/Kepala)
        
        # 2. Mirror-Echo (Merespon Result 4560)
        # Ambil Indeks dari angka result terbaru untuk periode depan
        for d in d0_p1:
            scores[ID.get(d)] += 28 # Mirroring 4-5-6-0
            
        # 3. Mistik Series AI (38)
        # Mengunci angka 3 dan 8 melalui jalur Mistik Baru/Lama dari ekor 0
        scores[ML.get('0')] += 30 # Mistik Lama 0 adalah 1
        scores[MB.get('0')] += 30 # Mistik Baru 0 adalah 8 (Sesuai AI)
        
        # 4. Washing Anchor Stability
        scores['3'] += 25
        scores['5'] += 20 # Angka 5 sering repeat di Washingmid
        
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
        elif market_name == 'SYDNEY LOTTO':
            # 1. BIJI HARMONY (2, 5, 8) + Biji Cadangan (Sydney Style)
            if biji_f in [2, 5, 8]: 
                score += 75
            elif biji_f in [1, 4, 7]: # Indeks dari 2, 5, 8
                score += 35
                
            # 2. SEQUENTIAL BONUS (Angka Berurutan: 23, 45, 87, dll)
            if abs(int(h) - int(t)) == 1: 
                score += 50
            
            # 3. MIRROR BALANCE (H & T Pasangan Indeks: 27, 38, 05, dll)
            if ID.get(h) == t: 
                score += 45
            
            # 4. ANTI-TWIN (Sydney jarang sekali twin belakang kecuali setelah pola ganjil)
            if h == t:
                score -= 60

        elif market_name == 'HONGKONG LOTTO':
            # 1. BIJI SIKLUS HK (Ditambah Biji 6 sebagai Mistik dari Biji 9)
            # Fokus Biji: 1, 4, 6, 7, 9
            if biji_f in [1, 4, 6, 7, 9]: 
                score += 95 
            
            # 2. TWIN-SLIP DETECTION (Belajar dari 00 di 3006)
            # Jika ada angka 0 di BBFS dan result kemarin twin, beri skor pada twin 00
            if '0' in line and last_p1[0] == last_p1[1]:
                score += 45
                if h == '0' and t == '0': score += 50 # Booster khusus twin 00

            # 3. SHADOW POSITION (Kepala ke Ekor)
            # Kepala 0 -> Ekor 5 (ID) atau 7 (TY)
            if t == TY.get(last_p1[2], 'x') or t == ID.get(last_p1[2], 'x'):
                score += 55
            
            # 4. HK BRIDGE (Kop ke AS)
            # Kop 0 -> AS 5 (ID) atau 1 (ML)
            if line[0] in [ID.get(last_p1[1], 'x'), ML.get(last_p1[1], 'x')]:
                score += 45

            # 5. DYNAMIC TWIN FILTER
            # Setelah 00 keluar, HK biasanya pecah (Anti-Twin belakang aktif lagi)
            if h == t and '0' not in line: 
                score -= 70

        elif market_name == 'CAMBODIA':
            # --- [V16.8 CAMBODIA MAXIMAL PRECISION] ---
            # 1. BIJI KHUSUS (Update: Tambah Biji 9 & 6)
            if biji_f in [1, 2, 4, 5, 7, 9, 6]: 
                score += 85 
            
            # 2. TYSEEN TAIL (Safe Access)
            t_p1 = last_p1[3] if len(last_p1) >= 4 else 'x'
            if t == TY.get(t_p1, 'x'): score += 55 
            
            # 3. DELTA ANALYSIS (Safe Math)
            if len(last_p1) >= 4 and last_p1[2].isdigit() and last_p1[3].isdigit():
                delta_val = str(abs(int(last_p1[2]) - int(last_p1[3])))
                if delta_val in line: score += 35
            
            # 4. TWIN STRATEGY (Belajar dari 99)
            # Jika result P1 mengandung twin (seperti 99), bonus twin belakang aktif
            if len(last_p1) >= 4 and (last_p1[2] == last_p1[3] or last_p1[0] == last_p1[1]):
                if h == t: score += 70 # Bonus besar jika terdeteksi trend twin
            else:
                if h == t: score -= 40 # Anti-twin jika tidak ada trend

            # 5. POSITION CHECK
            if h in ['3', '1', '9']: score += 30

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

        elif market_name == 'OSAKA':
            # --- [V16.19 OSAKA MAXIMAL PRECISION] ---
            # 1. BIJI SPECTRUM (Osaka Siklus: 1, 3, 5, 9)
            # Result 3357 (Biji 9), biasanya akan balik ke Biji Ganjil atau Biji 1
            if biji_f in [1, 3, 5, 9]: 
                score += 95 
            
            # 2. SHADOW-POSITION (Indeks Kepala -> Ekor Baru)
            # Kepala 5 -> Indeks 0. Kita cari angka yang ekornya 0
            if t == ID.get(last_p1[2], 'x'):
                score += 55
            
            # 3. VORTEX AS-KOP (As-Kop dari Mistik/Indeks Result)
            # Mengincar pola 88xx atau 80xx (Indeks dari 33)
            if line[0] == '8' or line[1] == '8':
                score += 45
                
            # 4. STEP-VERIFICATION
            # Bonus jika angka mengandung 8 (Step up dari ekor 7)
            if '8' in line:
                score += 30
                
            # 5. ANTI-TWIN DEPAN (Setelah Twin 11 dan 33, kemungkinan besar pecah)
            if line[0] == line[1]: 
                score -= 60

        elif market_name == 'SEOUL':
            # --- [V16.16 SEOUL MAXIMAL PRECISION] ---
            # 1. BIJI SPECTRUM (Diperluas: 1, 4, 7, 8) -> 8 masuk karena result 7847
            if biji_f in [1, 4, 7, 8]: 
                score += 90 
            
            # 2. DOUBLE-WRAP SENSOR (Pola As = Ekor)
            # Karena 7847 adalah pola bungkus, kita beri bonus untuk angka kembar As-Ekor
            if line[0] == line[3]:
                score += 55
            
            # 3. GHOST POSITION (Angka P2/P3 di posisi As)
            # Jika As adalah angka yang muncul di P2/P3 kemarin
            p2_res = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
            if line[0] in p2_res or line[3] in p2_res:
                score += 45
                
            # 4. KOP STABILITY (Kop 8 terbukti kuat)
            if line[1] == '8':
                score += 40
                
            # 5. ANTI-TWIN BELAKANG (2D Belakang tetap dijaga tidak kembar)
            if h == t: 
                score -= 60
                
        elif market_name == 'WUHAN':
            # Wuhan identik dengan Biji 2, 6, 9
            if biji_f in [2, 6, 9]: score += 65
            if t == MB.get(last_p1[3]): score += 40 # Mistik Baru Ekor

        elif market_name == 'PHUKET':
            # --- [V16.21 PHUKET MAXIMAL PRECISION] ---
            # 1. BIJI PHUKET EVOLUTION (Biji 4, 7, 1)
            # Result 2452 (Biji 4). Siklus Phuket biasanya melompat +3 (4 -> 7 -> 1)
            if biji_f in [4, 7, 1]: 
                score += 100 # Skor tertinggi untuk filter Biji
            
            # 2. AS-KOP MIRRORING
            # Jika As-Kop periode baru adalah Indeks dari Kepala-Ekor lama (52 -> 07)
            if line[0] == ID.get(last_p1[2]) and line[1] == ID.get(last_p1[3]):
                score += 60
            
            # 3. THE BRIDGE SCORE
            # Jika mengandung angka 6 atau 8 (Angka "Hutang" dari P2/P3)
            if '6' in line or '8' in line:
                score += 40
                
            # 4. ANTI-SANDWICH (Jangan pasang As=Ekor lagi, jarang terjadi 2x beruntun)
            if line[0] == line[1]:
                score -= 70
                
            # 5. POSITION LOCK (Ekor Ganjil)
            # Phuket sering selang-seling Genap-Ganjil di Ekor (2 Genap -> x Ganjil)
            if int(t) % 2 != 0:
                score += 35

        elif market_name == 'DANANG':
            # --- [V16.22 DANANG MAXIMAL PRECISION FIXED] ---
            # 1. BIJI SIKLUS (1, 3, 6)
            if biji_f in [1, 3, 6]: 
                score += 90 
            
            # 2. DIAGONAL POSITION (Ekor P1 lama jadi As P1 baru)
            # Tarikan angka 7 dari ekor 0477
            if line[0] == last_p1[3]:
                score += 50
            
            # 3. AI 2 SYNERGY (AI Utama Mamang)
            if '2' in line:
                score += 40
                
            # 4. ANTI-TWIN BACK (Setelah 77, jangan twin belakang lagi)
            if h == t: 
                score -= 75
            
            # 5. MISTIK-SHADOW (0 -> 1, 4 -> 7)
            if line[1] == '1' or line[1] == '7':
                score += 25

        elif market_name == 'GREECE':
            # 1. BIJI HARMONY V16.6 (Ditambah Biji 3 & 6)
            # Siklus: 1, 2, 3, 5, 6, 7, 8
            if biji_f in [1, 2, 3, 5, 6, 7, 8]: 
                score += 95 
            
            # 2. SLIDE LOGIC (Angka Berurutan seperti 21 atau 12)
            # Greece sering mengeluarkan angka selisih 1 (Step-Down/Up)
            if abs(int(h) - int(t)) == 1:
                score += 50
            
            # 3. POSITION REFLECTOR (Kepala P1 -> Ekor Baru)
            # Result 7121 -> Kepala 2. Ekor baru potensi Indeks 2 = 7
            kepala_p1 = last_p1[2] if len(last_p1) >= 3 else 'x'
            if t == ID.get(kepala_p1, 'x'): 
                score += 55 
            
            # 4. CROSS-P3 CENTER (Angka tengah Prize 3)
            # Misal P3: 7167, angka tengah 1 & 6 adalah AI kuat
            if len(all_res_data[0]) > 2:
                p3_res = all_res_data[0][2]
                if len(p3_res) >= 3 and (h in p3_res[1:3] or t in p3_res[1:3]):
                    score += 45

            # 5. ANTI-TWIN (Setelah 7121, peluang twin mengecil kecuali twin AI)
            if h == t:
                if h in ['8', '4', '6']: score += 35
                else: score -= 75
            

        # --- [V16.5 MANHATTAN MAXIMAL PRECISION] ---
        elif market_name == 'MANHATTAN':
            # 1. BIJI HARMONY MANHATTAN (Biji 1, 3, 5, 8) -> Result 7101 biji 9/0
            # Kita tambahkan Biji 9 untuk mengakomodasi pola result terbaru
            if biji_f in [1, 3, 5, 8, 9]: 
                score += 85 
            
            # 2. POSITION VERIFICATION: THE 7-ANCHOR
            # Karena 7 baru saja keluar di AS, potensi 7 pindah ke Kepala atau Ekor sangat besar
            if '7' in line:
                if line.index('7') >= 2: score += 45 # Fokus 7 di 2D belakang
            
            # 3. TAIL CONNECTION (Ekor P2 -> Ekor Sekarang)
            # Verifikasi jika ekor 2D sama dengan ekor P2 (Angka 1)
            if t == all_res_data[0][1][3]: score += 40
            
            # 4. ANTI-TWIN & SLIP DETECTION
            # Manhattan hobi Twin Selip (7101), tapi jarang Twin murni di belakang (xx11)
            if h == t: 
                score -= 35 
            else:
                score += 20 # Beri bonus untuk angka non-twin di belakang

        # --- [V16.8 TORONTOEVE MAXIMAL PRECISION] ---
        elif market_name == 'TORONTOEVE':
            # 1. BIJI FAVORIT TORONTO (Ditambah Biji 9 untuk mengakomodasi 8703)
            if biji_f in [1, 2, 4, 7, 9]: 
                score += 85 
            
            # 2. AS-TO-TAIL VERIFICATION
            # Jika Ekor 2D adalah Mistik Lama dari As Result (8 -> 3)
            if t == ML.get(last_p1[0]): score += 50
            
            # 3. POSITION VERIFICATION (Kepala 0 Terbukti)
            # Jika Kepala 2D adalah AI Utama (0 atau 1)
            if h in ['0', '1']: score += 40
            
            # 4. CROSS-PRIZE VERIF
            # Jika angka 2D muncul di Prize 2 sebelumnya (7916)
            if h in all_res_data[0][1] or t in all_res_data[0][1]:
                score += 35
                
            # 5. ANTI-TWIN (Toronto tetap jarang twin belakang)
            if h == t: score -= 35

        elif 'OREGON' in market_name:
            # --- [V16.13 OREGON MAXIMAL PRECISION] ---
            # 1. BIJI KHUSUS (Biji 3, 4, 6, 8, 9) -> Terbukti JP Biji 8 di 9269
            if biji_f in [3, 4, 6, 8, 9]: 
                score += 90 
            
            # 2. DOUBLE-WRAP VERIFICATION
            # Bonus jika As dan Ekor menggunakan angka yang sama (Pola 9...9)
            if line[0] == line[1]: 
                score += 45
            
            # 3. MISTIK-JUMP POSITION
            # Bonus jika Kop/Kepala menggunakan Mistik Lama/Baru dari result sebelumnya
            if h == ML.get(last_p1[2]) or line[1] == MB.get(last_p1[0]):
                score += 40
                
            # 4. STEP-UP DYNAMICS
            # Memverifikasi angka yang naik 1 tingkat dari result lama
            if t == str((int(last_p1[3]) + 1) % 10):
                score += 35
                
            # 5. ANTI-TWIN BACK (Hanya untuk 2D Belakang)
            if h == t: 
                score -= 45
                
        elif market_name == 'WASHINGMID':
            # --- [V16.11 WASHINGMID PRECISION FILTER] ---
            # 1. BIJI UPGRADE (Menambahkan Biji 6 sesuai trend result 4560)
            # Fokus Biji: 1, 3, 4, 6, 8
            if biji_f in [1, 3, 4, 6, 8]: 
                score += 90 
            
            # 2. POSITION SLIDE VERIFICATION
            # Bonus jika As 4D adalah Kop/Kepala dari result sebelumnya (4 atau 5)
            if line[0] in [last_p1[1], last_p1[2]]:
                score += 50
            
            # 3. THE 3-8 SYNERGY (Berdasarkan AI 38)
            # Jika 2D belakang (Kepala-Ekor) mengandung salah satu AI 38
            if h in ['3', '8'] or t in ['3', '8']:
                score += 40
            
            # 4. HEAD-VIBRATION (Indeks dari Kepala sebelumnya: 6 -> 1)
            # Jika Kepala 2D adalah Indeks dari Kepala periode lalu
            if h == ID.get(last_p1[2]):
                score += 35

            # 5. ANTI-TWIN & ODD-EVEN BALANCING
            if h == t: score -= 40
                
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
        elif market_name == 'SYDNEY LOTTO':
            try:
                # Sydney Logic: As sering kali adalah Indeks dari Kop P1 lama
                # Kop sering kali adalah Mistik Lama dari As P1 lama
                as_p1_lama = last_p1[0] if len(last_p1) >= 1 else '5'
                kop_p1_lama = last_p1[1] if len(last_p1) >= 2 else '2'
                
                # Penentuan AS & KOP Dynamic
                asn = ID.get(kop_p1_lama, best_as[i % len(best_as)])
                kop = ML.get(as_p1_lama, best_kop[i % len(best_kop)])

                # Safety Check: Pastikan masuk dalam BBFS
                if asn not in bbfs_list: asn = best_as[i % len(best_as)]
                if kop not in bbfs_list: kop = best_kop[i % len(best_kop)]

                # Varian Sydney: Pola Selang-Seling (As = Tetangga As lama)
                if i % 2 != 0:
                    val_as = int(as_p1_lama) if as_p1_lama.isdigit() else 5
                    asn = str((val_as + 1) % 10)
                    if asn not in bbfs_list: asn = bbfs_list[0]

                top3.append(f"{kop}{l2}")
                top4.append(f"{asn}{kop}{l2}")
            except (IndexError, ValueError):
                # Fallback Safe Logic
                top3.append(f"{bbfs_list[0]}{l2}")
                top4.append(f"{bbfs_list[1]}{bbfs_list[0]}{l2}")

        elif market_name == 'CAMBODIA':
            try:
                # Ambil AS & KOP dari list terbaik, fallback ke bbfs jika kosong
                asn = best_as[i % len(best_as)] if best_as else bbfs_list[0]
                
                # Logika Twin Tengah/Depan (xAAx)
                if i < 3:
                    kop = asn 
                else:
                    kop = best_kop[i % len(best_kop)] if best_kop else bbfs_list[1]
                
                # Shifting aman jika tabrakan dengan Kepala 2D
                if kop == l2[0]:
                    if kop in bbfs_list:
                        idx = (bbfs_list.index(kop) + 1) % len(bbfs_list)
                        kop = bbfs_list[idx]
                    else:
                        kop = bbfs_list[(i + 2) % len(bbfs_list)]

                top3.append(f"{kop}{l2}")
                top4.append(f"{asn}{kop}{l2}")
            except (IndexError, ValueError):
                # Fallback jika terjadi error data
                top3.append(f"{bbfs_list[0]}{l2}")
                top4.append(f"{bbfs_list[1]}{bbfs_list[0]}{l2}")    

        # --- [ V16.6 GREECE 4D DYNAMIC RADAR ] ---
        elif market_name == 'GREECE':
            try:
                # AS: Mengambil Indeks dari AS P1 (7 -> 2) atau Mistik As P2
                as_p1 = last_p1[0]
                as_p2 = all_res_data[0][1][0] if len(all_res_data[0]) > 1 else '8'
                
                asn = ID.get(as_p1, best_as[i % len(best_as)])
                kop = ID.get(as_p2, best_kop[i % len(best_kop)])

                # Safety BBFS Check
                if asn not in bbfs_list: asn = best_as[i % len(best_as)]
                if kop not in bbfs_list: kop = bbfs_list[(i + 2) % len(bbfs_list)]

                # Pattern Shifting (Mencegah As-Kop Statis)
                if i % 2 == 0: 
                    asn = ID.get(asn, asn) # Double Indeks Shifting
                
                # Logic Twin Tengah (Antisipasi pola x11x atau x66x)
                if i == 1 and '1' in bbfs_list: kop = '1'
                if i == 2 and '6' in bbfs_list: kop = '6'

            except Exception:
                asn = best_as[i % len(best_as)]
                kop = best_kop[i % len(best_kop)]

        safety_counter = 0
        while (kop in l2 or kop == asn) and safety_counter < len(bbfs_list):
            kop = bbfs_list[(bbfs_list.index(kop) + 1) % len(bbfs_list)]
            safety_counter += 1

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
            url = f"https://nfx1avfcy8.salamtarget.com/history/result-mobile/{market_code}-pool-1"
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
    app.run(host='0.0.0.0', port=5000, debug=True)
