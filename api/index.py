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
        scores[n] += freq_p1.get(n, 0) * 1.5
        if n in d0_p1: scores[n] += 15
    
    for res in all_res_data[:10]:
        if len(res) > 1:
            shadow = "".join(res[1:])
            for n in set(shadow): scores[n] += 5

    # --- PERBAIKAN STRUKTUR IF-ELIF ---
    if market_name == 'CAMBODIA':
        p_list = [res for res in all_res_data[0] if res] if all_res_data else []
        all_p_digits = "".join(p_list)
        for digit in set(all_p_digits):
            if digit.isdigit():
                scores[ID.get(digit, digit)] += 30 
                scores[ML.get(digit, digit)] += 15 
                if len(all_res_data[0]) > 2 and digit in all_res_data[0][2]:
                    scores[digit] += 25 
        if len(d0_p1) >= 4 and d0_p1[2].isdigit() and d0_p1[3].isdigit():
            delta = str(abs(int(d0_p1[2]) - int(d0_p1[3])))
            scores[delta] = scores.get(delta, 0) + 35
            scores[TY.get(delta, '0')] = scores.get(TY.get(delta, '0'), 0) + 25
        for n in ['3', '8', '9', '4']: scores[n] = scores.get(n, 0) + 20

    elif market_name == 'SYDNEY LOTTO':
        # Penajaman BBFS: Fokus pada Mirroring & Step
        for digit in d0_p1:
            if digit.isdigit():
                val = int(digit)
                # Bobot Tetangga (Neighbor)
                scores[str((val + 1) % 10)] += 22 
                scores[str((val - 1) % 10)] += 22
                # Bobot Mistik & Indeks (Sangat Kuat di Sydney)
                scores[MB.get(digit, '0')] += 25 
                scores[ID.get(digit, '0')] += 30 
        
        # Injeksi Angka "Panas" Sydney (Berdasarkan Habit)
        for n in "1836": 
            scores[n] += 15

    elif market_name == 'WUHAN':
        # Wuhan sering menarik angka dari P2 (1208)
        p2_last = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
        for digit in p2_last:
            if digit.isdigit():
                scores[digit] += 25  # Prioritas tarikan P2 ke P1
                scores[MB.get(digit, digit)] += 15 # Mistik Baru
        
        # Wuhan High-Frequency Range (0, 1, 4, 6)
        for n in "0146":
            scores[n] += 12

    elif market_name == 'HONGKONG LOTTO':
        # --- [V18.1 HKL MONSTER - MOMENTUM TRACKER] ---
        p1_d = d0_p1 if d0_p1 else "6314"
        
        # 1. THE SLIDE EFFECT (As/Ekor lama jadi magnet)
        # Angka 6 dan 4 adalah angka "aktif". Kita cari Indeks & Mistiknya.
        scores[ID.get(p1_d[0])] += 45 # 6 -> 1
        scores[ID.get(p1_d[3])] += 45 # 4 -> 9
        
        # 2. CROSS-MIRROR (Tengah 3-1)
        # Jika tengah 31, maka Lawan Biji atau Mistiknya (8 atau 0) harus naik
        scores['8'] += 40
        scores['0'] += 35
        
        # 3. DEBT COLLECTOR (Angka 5 & 2)
        # Angka 5 dan 2 tidak muncul di semua result HK malam ini. Ini "Hutang Berdarah".
        for n in "257": scores[n] += 30

    elif market_name == 'HONGKONG POOLS':
            # --- [V17.0 HKP MONSTER WEIGHTING - P1 ONLY] ---
            # Menggunakan result terakhir (Contoh: 3593)
            p1_d = d0_p1 if d0_p1 else "3593"
            
            # 1. TWIN-DESTRUCTION (Indeks dari Twin Terapit)
            # Result 3...3 -> Angka 3 adalah kunci. Indeksnya (8) diledakkan.
            t_key = p1_d[0]
            scores[ID.get(t_key, '8')] += 50  # Prioritas Utama (Indeks)
            scores[ML.get(t_key, '8')] += 30  # Prioritas Kedua (Mistik)
            
            # 2. MIDDLE-SHIFT (Angka tengah 5-9)
            # HK Pools sangat hobi menggeser angka tengah ke posisi belakang
            scores[p1_d[1]] += 35 # Angka 5
            scores[p1_d[2]] += 35 # Angka 9
            
            # 3. GAP FILLER (AI 48)
            # Menembak angka yang belum keluar di P1 sebelumnya
            for n in "480":
                scores[n] += 40

            # 4. BIJI RESONANCE (Biji 2 -> Target Biji 9)
            # Karena 3593 = Biji 2, maka angka dengan Biji 9 diberi bonus
            # (Proses ini dilakukan otomatis di bagian filter 2D)
        
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

    elif market_name == 'BUSAN POOLS':
        # Busan identik dengan angka "akar" (0, 3, 8)
        for digit in d0_p1:
            if digit in "038":
                scores[digit] += 30
        
        # Tracking angka dari P2 ke P1 (Vibrasi Busan)
        p2_last = all_res_data[0][1] if len(all_res_data[0]) > 1 else ""
        for digit in p2_last:
            if digit.isdigit():
                scores[digit] += 20
    
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
        # --- [V17.1 OSAKA MONSTER - UPDATED] ---
        p1_d = d0_p1 if d0_p1 else "0574"
        
        # 1. DOWN-SHIFT PRIORITY (Angka Turun Kelas)
        # Kepala & Ekor lama punya kecenderungan naik jadi As/Kop
        scores[p1_d[2]] += 40 # Kepala lama (7)
        scores[p1_d[3]] += 35 # Ekor lama (4)
        
        # 2. VORTEX MIRROR (Indeks dari Result)
        for d in p1_d:
            scores[ID.get(d)] += 30 
        
        # 3. OSAKA ANCHOR (AI 028)
        # Tetap menjaga angka 8 sebagai Step-Up dan 2 sebagai Mistik
        for n in "028": scores[n] += 25

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

    elif market_name == 'PHUKET':
        # --- [V17.2 PHUKET MONSTER: REBIRTH & GAP] ---
        p1_d = d0_p1 if d0_p1 else "2206"
        
        # 1. THE GAP DETECTOR (Lompatan Angka)
        # Result 2-2-0-6. Angka 1, 3, 4, 5 adalah "Gap" yang tertinggal.
        for n in "1345":
            scores[n] += 35
            
        # 2. TWIN REBORN (Karena 22 sudah keluar, waspada Twin 00 atau 66)
        scores[ID.get(p1_d[0])] += 25 # Indeks 2 -> 7
        
        # 3. AI ANCHOR (AI 79)
        scores['7'] += 30
        scores['9'] += 30

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

    elif market_name == 'OREGON 3':
            # --- [V18.2 OREGON 3 - SINGLE PATH RESONANCE] ---
            # Result: 7583
            p1_d = d0_p1 if d0_p1 else "7583"
            
            # 1. POLA JUMLAH (7+5+8+3 = 23 -> 5)
            # Oregon sering merespon jumlah total result sebelumnya
            total_biji = sum(int(x) for x in p1_d) % 10
            scores[str(total_biji)] += 45
            
            # 2. AS-EKOR JUMP (7 & 3)
            # Indeks dari angka pinggir sering meledak di posisi tengah
            scores[ID.get(p1_d[0])] += 40 # 7 -> 2
            scores[ID.get(p1_d[3])] += 40 # 3 -> 8
            
            # 3. KOP-KEPALA SATURATION (5 & 8)
            # Angka tengah yang jenuh akan berubah menjadi Mistik Baru/Lama
            scores[MB.get(p1_d[1])] += 35 # 5 -> 4
            scores[ML.get(p1_d[2])] += 35 # 8 -> 3

    elif market_name == 'OREGON 6':
            # --- [V18.4 OREGON 6 - REVENGE MODE] ---
            # Result: 8507
            p1_d = "8507" 
            
            # 1. THE "MISSING 9" THEORY
            # Angka 9 sudah absen cukup lama di Oregon 6, 
            # sementara result 8507 mengelilingi angka 9 secara mistik.
            scores['9'] += 55
            
            # 2. ZERO RESONANCE
            # Angka 0 di posisi Kepala sering memicu angka 1 atau 6 (Mistik/Indeks) 
            # untuk muncul di posisi 2D belakang pada putaran selanjutnya.
            scores['1'] += 45
            scores['6'] += 40
            
            # 3. SUM-TO-BIPOLAR (8+5+0+7 = 20 -> Biji 2)
            # Biji 2 akan kita jadikan patokan utama untuk BBFS.
            scores['2'] += 50
            scores['7'] += 35 # Proteksi angka 7 yang baru keluar (sering repeat)

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
            # --- [V18.6 SYDNEY LOTTO - TWIN OSCILLATOR] ---
            # Result Terakhir: 8118
            
            # 1. BIJI RESONANCE (Target Biji: 2, 5, 9)
            # 8+1+1+8 = 18 -> Biji 9. Sydney sering merespon Biji 9 dengan Biji 5 atau 2.
            if biji_f in [2, 5, 9]: 
                score += 130 
            
            # 2. THE "18" REVERSAL (Ekor 18)
            # Sydney Lotto setelah ekor 18 sering mengeluarkan angka 5 (Mistik)
            # atau angka 4 (Indeks 9).
            if h in ['5', '4', '0'] or t in ['5', '4', '0']:
                score += 65

            # 3. GAP DETECTION (Angka Mati 8 & 1)
            # Setelah Twin 8118, angka 8 dan 1 biasanya akan "istirahat" (Mati Total).
            # Kita beri penalti keras jika angka ini muncul lagi di 2D.
            if h in ['8', '1'] or t in ['8', '1']:
                score -= 100
                
            # 4. POLARITY SHIFT (Ganjil-Genap)
            # Fokus pada kombinasi Kepala Ganjil - Ekor Genap (Misal: 50, 32, 94).
            if int(h) % 2 != 0 and int(t) % 2 == 0:
                score += 55

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
            # --- [V18.4 CAMBODIA - TWIN KILLER LOGIC] ---
            # Result Terakhir: 9199
            
            # 1. BIJI RESONANCE (Target Biji: 1, 4, 7, 8)
            # Hasil jumlah 9+1+9+9 = 28 -> Biji 1. Fokus pada Biji 1 dan Lawannya (7, 4).
            if biji_f in [1, 4, 7, 8]: 
                score += 125 
            
            # 2. TWIN-9 REVENGE
            # Angka 99 di belakang biasanya memicu angka Indeks (4) atau Mistik Baru (3)
            # untuk meledak di posisi 2D (Kepala atau Ekor).
            if h in ['4', '3'] or t in ['4', '3']:
                score += 65

            # 3. THE "1" GAP SHIFT
            # Angka 1 (Kop) sering kali bergeser menjadi Kepala atau Ekor di Cambodia.
            if h == '1' or t == '1':
                score += 50
                
            # 4. POLARITY SHIFT (Ganjil -> Genap)
            # Setelah dominasi angka ganjil (9199), Cambodia cenderung membalas dengan
            # angka genap kuat (4, 6, 8).
            if int(h) % 2 == 0 and int(t) % 2 == 0:
                score += 45
            elif (int(h) % 2 == 0 and int(t) % 2 != 0) or (int(h) % 2 != 0 and int(t) % 2 == 0):
                score += 30

            # 5. ANTI-TWIN & REPEAT PROTECTOR
            # Penalti sangat keras jika angka 9 muncul lagi di ekor (Repeat).
            if t == '9': 
                score -= 150 
            if h == t: 
                score -= 70 # Menghindari twin belakang berurutan

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
            # --- [V17.1 OSAKA MAXIMAL PRECISION] ---
            # 1. BIJI SIKLUS GANJIL (1, 3, 5, 7, 9)
            # Osaka sedang dalam tren Biji Ganjil (0574 -> 0+5+7+4 = 16 -> Biji 7)
            if biji_f % 2 != 0: 
                score += 100 
            
            # 2. SHADOW POSITION (Kepala lama ke Ekor Baru)
            # Jika ekor baru adalah Indeks/Mistik dari kepala lama (7)
            if t == ID.get(last_p1[2]) or t == ML.get(last_p1[2]):
                score += 65
            
            # 3. VORTEX AS-KOP BOOSTER
            # Memberikan bonus jika As atau Kop menggunakan angka 0, 2, atau 8
            if line[0] in "028" or line[1] in "028":
                score += 45
            
            # 4. ANTI-SERI (Mencegah angka seperti 78 atau 45 di belakang)
            if abs(int(h) - int(t)) == 1:
                score -= 50

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
            # 1. BIJI KELIPATAN 3 (3, 6, 9)
            if biji_f in [3, 6, 9]: score += 60
            
            # 2. GANJIL-GENAP MIX (Wuhan jarang 2D genap-genap)
            h_int = int(h)
            t_int = int(t)
            if (h_int % 2 != t_int % 2): score += 35

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

        elif market_name == 'OREGON 3':
            # --- [V18.4 OREGON 3 - QUANTUM PRECISION] ---
            # Result Terakhir: 4823
            
            # 1. BIJI RESONANCE (Target Biji: 1, 4, 5, 8)
            # Fokus pada Biji 1 dan 5 sebagai pembalasan dari Biji 8 (4+8+2+3=17->8)
            if biji_f in [1, 4, 5, 8]: 
                score += 120 
            
            # 2. THE "23" REVERSAL DETECTION
            # Angka 23 di ekor sering memicu munculnya angka Indeks/Mistik (7, 8, 5) 
            # di posisi Kepala pada putaran berikutnya.
            if h in ['7', '8', '5']:
                score += 60

            # 3. ODD-GAP FILLER (Target: 1, 9)
            # Angka ganjil 1 dan 9 adalah "angka hutang" yang sangat kuat di Oregon 3
            if t in ['1', '9'] or h in ['1', '9']:
                score += 55
                
            # 4. VERTICAL POSITIONING (Kop 8 -> As/Kop Baru)
            # Memberikan bonus jika angka 8 (Kop lama) muncul di depan atau 
            # angka 4 (Mistik Baru dari 8) muncul di 2D.
            if h == '4' or t == '4':
                score += 45

            # 5. ANTI-REPEAT & TRAP FILTER
            # Penalti berat jika Ekor kembali 3 (Repeat) atau angka Genap Beruntun
            if t == last_p1[3]: 
                score -= 100 
            if int(h) % 2 == 0 and int(t) % 2 == 0:
                score -= 30 # Menghindari jebakan Genap-Genap setelah 482

        elif 'OREGON 6' in market_name:
            # --- [V18.4 OREGON QUANTUM REVENGE] ---
            
            # 1. BIJI RESONANCE (Target Biji: 1, 2, 5, 7, 9)
            # Fokus pada Biji 2 (Hasil jumlah 8+5+0+7) dan Lawannya
            if biji_f in [1, 2, 5, 7, 9]: 
                score += 115 # Menaikkan bobot dari 90
            
            # 2. GAP-MISSING DETECTION (Angka 9 & 6)
            # Memberikan bonus besar jika angka yang lama absen (9 & 6) muncul di 2D
            if t in ['9', '6'] or h in ['9', '6']:
                score += 55

            # 3. MISTIK-JUMP POSITION (Refined)
            # Bonus jika Kop/Kepala adalah Mistik Baru/Lama dari P1 sebelumnya
            # Logic: Kop (5)->MB(4), Kep(0)->ML(1), Ek(7)->MB(1)
            if h in [ML.get(last_p1[2]), MB.get(last_p1[1])] or t == ML.get(last_p1[3]):
                score += 50
                
            # 4. BALANCED POLARITY (Odd-Even Check)
            # Karena result 8507 didominasi angka ganjil di belakang, 
            # kita beri skor pada kombinasi Ganjil-Genap atau sebaliknya.
            if (int(h) % 2 == 0 and int(t) % 2 != 0) or (int(h) % 2 != 0 and int(t) % 2 == 0):
                score += 45
                
            # 5. ANTI-TWIN & REPEAT PROTECTOR
            if h == t: 
                score -= 60 # Penalti lebih besar untuk twin belakang
            if t == last_p1[3]: 
                score -= 80 # Penalti sangat keras jika ekor repeat (7)
                
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
    # --- [ DATABASE POSISI & SCORES ] ---
    top3, top4 = [], []
    
    # Mengambil 3 angka terkuat berdasarkan bobot scores global
    best_as = sorted(bbfs_list, key=lambda x: scores.get(x, 0), reverse=True)[:3]
    best_kop = sorted(bbfs_list, key=lambda x: scores.get(x, 0), reverse=True)[1:4] # Offset 1 agar beda dari As

    for i, l2 in enumerate(top2):
        # Default rotation (Akan dioverride oleh logic khusus market)
        kop = best_kop[i % len(best_kop)]
        asn = best_as[i % len(best_as)]
        
        # --- [ MARKET SPECIFIC LOGIC ] ---
        
        # --- [ V17.0 BUSAN MONSTER ] ---
        if market_name == 'BUSAN POOLS':
            try:
                as_p1 = last_p1[0]
                kop_p1 = last_p1[1]
                anchor_1 = ML.get(as_p1, bbfs_list[0])
                anchor_2 = ID.get(kop_p1, bbfs_list[1])

                if i < 4:
                    kop = anchor_1
                    asn = anchor_2 if i % 2 == 0 else best_as[i % len(best_as)]
                elif i == 4:
                    asn, kop = l2[1], l2[0] # Butterfly ABBA
                else:
                    asn = best_as[i % len(best_as)]
                    kop = best_kop[(i + 3) % len(best_kop)]

                if abs(int(asn) - int(kop)) == 1:
                    asn = ID.get(asn, bbfs_list[(i+4)%len(bbfs_list)])
            except: pass

        elif market_name == 'OREGON 3':
            try:
                # Data Input (Result Terakhir: 4823)
                as_l, kop_l, kep_l, ek_l = last_p1[0], last_p1[1], last_p1[2], last_p1[3]

                # --- PENENTUAN AS & KOP (V18.3 SHIFTING) ---
                for i in range(15):  # Kita generate 15 line untuk 3D/4D
                    if i == 0:
                        # Pola Lawan Biji: Indeks dari 2D belakang jadi depan
                        asn = ID.get(kep_l, '7') # 2 -> 7
                        kop = ID.get(ek_l, '8')  # 3 -> 8
                    elif i == 1:
                        # Pola Mistik Lompat: Kop lama jadi As, Ekor lama jadi Kop
                        asn = MB.get(kop_l, '0') # 8 -> 0
                        kop = ML.get(as_l, '7')  # 4 -> 7
                    elif i == 2:
                        # Pola Anchor: Angka 5 dan 9 sebagai pengunci
                        asn, kop = '5', '9'
                    else:
                        # Mengambil dari kandidat As & Kop terbaik hasil scoring
                        asn = best_as[i % len(best_as)]
                        kop = best_kop[(i + 1) % len(best_kop)]

                    # --- FILTER 2D SNIPER V18.3 ---
                    # 1. BIJI RESONANCE (Target Biji: 1, 5, 8)
                    # Jika 2D belakang (Kepala+Ekor) berjumlah 1, 5, atau 8, skor naik.
                    if biji_f in [1, 5, 8]: score += 130
                    
                    # 2. ODD DOMINATION (Setelah 4823, targetkan Ekor Ganjil)
                    if int(t) % 2 != 0: score += 70
                    
                    # 3. ANTI-REPEAT (Ekor tidak boleh 3 lagi)
                    if t == ek_l: score -= 200 
                    
                    # 4. CROSS-MISTIK (Kepala adalah Mistik dari Ekor sebelumnya)
                    if h == ML.get(ek_l): score += 60 # 3 -> 8

                    # Simpan hasil ke daftar Jitu
                    l2 = f"{h}{t}"
                    line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                    
                    if l2 not in top2: top2.append(l2)
                    if line3 not in top3: top3.append(line3)
                    if line4 not in top4: top4.append(line4)
            except Exception as e:
                print(f"Construction Error Oregon: {e}")

        elif 'OREGON 6' in market_name:
            try:
                # Result: 8507
                as_l, kop_l, kep_l, ek_l = last_p1[0], last_p1[1], last_p1[2], last_p1[3]

                for i in range(20): # Generate 20 line untuk akurasi lebih tinggi
                    if i == 0:
                        # Pola Quantum: As dari Indeks Ekor, Kop dari Mistik Kepala
                        asn = ID.get(ek_l, '2') # 7 -> 2
                        kop = ML.get(kep_l, '1') # 0 -> 1
                    elif i == 1:
                        # Pola Revenge: Mengincar angka 9 yang hilang
                        asn = '9'
                        kop = ID.get(as_l, '3') # 8 -> 3
                    elif i == 2:
                        # Pola Mirror: As tetap, Kop indeks
                        asn = as_l 
                        kop = ID.get(kop_l, '0') # 5 -> 0
                    else:
                        asn = best_as[i % len(best_as)]
                        kop = best_kop[(i + 1) % len(best_kop)]

                    l2 = f"{h}{t}" # Dari loop 2D
                    line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                    
                    if l2 not in top2: top2.append(l2)
                    if line3 not in top3: top3.append(line3)
                    if line4 not in top4: top4.append(line4)
            except: pass

        elif market_name == 'OSAKA':
            try:
                as_l = last_p1[0] # 0
                kop_l = last_p1[1] # 5
                kep_l = last_p1[2] # 7
                ek_l = last_p1[3] # 4

                if i == 0:
                    # POLA HEAD-TO-KOP (Belajar dari 0574)
                    # Mengambil Kepala lama sebagai Kop baru
                    asn = ID.get(as_l, '5') 
                    kop = kep_l 
                elif i == 1:
                    # POLA MIRROR SQUASH (Kebalikan total)
                    asn = ID.get(kep_l, '2')
                    kop = ID.get(ek_l, '9')
                elif i == 2:
                    # POLA STEP-UP BRIDGE
                    asn = str((int(as_l) + 1) % 10)
                    kop = ID.get(as_l, '5')
                elif i == 3:
                    # POLA VORTEX (As & Kop dari AI terkuat)
                    asn = best_as[0]
                    kop = best_kop[0]
                else:
                    asn = best_as[i % len(best_as)]
                    kop = best_kop[(i + 1) % len(best_kop)]

                # Audit Khusus Osaka: Mencegah pola urut (misal 4567)
                if abs(int(asn) - int(kop)) == 1:
                    kop = MB.get(asn, bbfs_list[(i+2)%len(bbfs_list)])

                line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                if line3 not in top3: top3.append(line3)
                if line4 not in top4: top4.append(line4)
            except: pass

        # --- [ V17.0 PHUKET MONSTER: BRIDGE-CROSSING LOGIC ] ---
        elif market_name == 'PHUKET':
            try:
                # Pola 2206 -> Twin Depan + Ekor Genap
                # Kita tembak pola Indeks-nya untuk periode depan
                if i == 0:
                    asn, kop = '7', '7' # Twin Indeks dari 22
                elif i == 1:
                    asn, kop = '5', '1' # Mistik/Indeks dari 06
                else:
                    asn = best_as[i % len(best_as)]
                    kop = best_kop[(i + 1) % len(best_kop)]

                line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                if line3 not in top3: top3.append(line3)
                if line4 not in top4: top4.append(line4)
            except: pass

        # --- [ V17.0 WUHAN MONSTER ] ---
        elif market_name == 'WUHAN':
            try:
                p1_l = last_p1
                p2_l = all_res_data[0][1] if len(all_res_data[0]) > 1 else "1208"
                
                if i == 0:
                    asn, kop = p2_l[0], p2_l[1] # Estafet P2
                elif i == 1:
                    asn = kop = l2[0] # Twin Depan (Radar 2280)
                elif i == 2:
                    asn = ID.get(p1_l[3], bbfs_list[0]) # Mirror Ekor P1
                    kop = ID.get(p1_l[2], bbfs_list[1])
                
                if i < 3 and asn == kop:
                    kop = MB.get(asn, bbfs_list[i])
            except: pass

        # --- [ V18.6 SYDNEY MONSTER REVENGE ] ---
        elif market_name == 'SYDNEY LOTTO':
            try:
                # Result Terakhir: 8118
                as_l = last_p1[0] if len(last_p1) >= 1 else '8'
                kop_l = last_p1[1] if len(last_p1) >= 2 else '1'
                kep_l = last_p1[2] if len(last_p1) >= 3 else '1'
                ek_l = last_p1[3] if len(last_p1) >= 4 else '8'
                
                for i in range(20):
                    if i == 0:
                        # OSCILLATOR PATTERN: Mistik Kop lama jadi As, Indeks As lama jadi Kop
                        asn = MB.get(kop_l, '0') # 1 -> 0
                        kop = ID.get(as_l, '3')  # 8 -> 3
                    elif i == 1:
                        # SHADOW PATTERN: Angka 5 dan 9 sebagai pelindung (Gap Filler)
                        asn, kop = '5', '9'
                    elif i == 2:
                        # REVERSE BUTTERFLY: Kebalikan dari 8118
                        asn = ID.get(ek_l, '3')
                        kop = MB.get(kep_l, '0')
                    elif i % 5 == 0:
                        # SMART TWIN: Hanya inject twin ganjil (sangat kuat di Sydney)
                        twin = '5' if i % 2 == 0 else '9'
                        l2 = f"{twin}{twin}"
                    else:
                        asn = best_as[i % len(best_as)]
                        kop = best_kop[(i + 1) % len(best_kop)]

                    # Pembuatan 3D & 4D Jitu
                    line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                    
                    if l2 not in top2: top2.append(l2)
                    if line3 not in top3: top3.append(line3)
                    if line4 not in top4: top4.append(line4)
            except Exception as e:
                print(f"Error Sydney Construction: {e}")

        elif market_name == 'CAMBODIA':
            try:
                # Result: 9199 (As: 9, Kop: 1, Kep: 9, Ek: 9)
                as_l, kop_l, kep_l, ek_l = last_p1[0], last_p1[1], last_p1[2], last_p1[3]

                for i in range(20):
                    if i == 0:
                        # Pola Shifting: Indeks Kop lama jadi As baru, Mistik Kepala jadi Kop
                        asn = ID.get(kop_l, '6') # 1 -> 6
                        kop = MB.get(kep_l, '3') # 9 -> 3
                    elif i == 1:
                        # Pola Lawan Twin: Gunakan angka 4 (Indeks 9) sebagai poros depan
                        asn = '4'
                        kop = ID.get(as_l, '4') # 9 -> 4
                    elif i == 2:
                        # Pola Mirror: As indeks, Kop tetap
                        asn = ID.get(as_l, '4') 
                        kop = kop_l # 1
                    else:
                        asn = best_as[i % len(best_as)]
                        kop = best_kop[(i + 1) % len(best_kop)]

                    l2 = f"{h}{t}"
                    line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                    
                    if l2 not in top2: top2.append(l2)
                    if line3 not in top3: top3.append(line3)
                    if line4 not in top4: top4.append(line4)
            except: pass

        # --- [ V17.0 HK-MONSTER: SHADOW & BRIDGE SHIFTING ] ---
        elif market_name == 'HONGKONG LOTTO':
            try:
                # Result: 6314
                as_l, kop_l, kep_l, ek_l = last_p1[0], last_p1[1], last_p1[2], last_p1[3]

                if i == 0:
                # POLA REVERSAL (Ekor lama jadi As baru, Kop lama jadi Kop baru)
                    asn = ek_l # 4
                    kop = ID.get(kop_l, '8') # 3 -> 8 (Hasil: 48xx)
                elif i == 1:
                # POLA SHADOW SHIFT (Indeks Kepala jadi As)
                    asn = ID.get(kep_l, '6') # 1 -> 6
                    kop = ML.get(as_l, '9')  # 6 -> 9 (Hasil: 69xx)
                elif i == 2:
                # POLA NEUTRALIZER (05 Anchor)
                    asn, kop = '0', '5' 
                else:
                    asn = best_as[i % len(best_as)]
                    kop = best_kop[(i + 1) % len(best_kop)]

            # --- 2D SNIPER FILTER V18.1 ---
            # 1. BIJI SIKLUS (Fokus Biji 2, 5, 8 - Siklus Lompat +3)
                if biji_f in [2, 5, 8]: score += 120
            
            # 2. POSITION LOCK (Ganjil-Genap Shifting)
            # Result 6314 (Genap-Ganjil-Ganjil-Genap) -> Target Ganjil di Ekor!
                if int(t) % 2 != 0: score += 60
            
            # 3. ANTI-SAME (Buang angka 6, 3, 1, 4 di posisi 2D belakang)
                if h in p1_d or t in p1_d:
                    score -= 40 

                line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                if line3 not in top3: top3.append(line3)
                if line4 not in top4: top4.append(line4)
            except: pass

        # --- [ V17.0 HKP MONSTER CONSTRUCTION ] ---
        elif market_name == 'HONGKONG POOLS':
            try:
                # Ambil data kunci dari P1 (Contoh: 3593)
                as_l = last_p1[0]  # 3
                kop_l = last_p1[1] # 5
                kep_l = last_p1[2] # 9
                ek_l = last_p1[3]  # 3

                # --- 4D & 3D Sniping Logic ---
                if i == 0:
                    # POLA MIDDLE-RISE (Tengah lama jadi depan baru)
                    asn, kop = kop_l, kep_l # Hasil: 59xx
                elif i == 1:
                    # POLA MIRROR TOTAL (Indeks dari 3-3)
                    asn, kop = ID.get(as_l, '8'), ID.get(ek_l, '8') # Hasil: 88xx
                elif i == 2:
                    # POLA DEBT-RECOVERY (AI 48)
                    asn, kop = '4', '8' # Hasil: 48xx
                else:
                    # Rotasi berdasarkan skor tertinggi BBFS
                    asn = best_as[i % len(best_as)]
                    kop = best_kop[(i + 1) % len(best_kop)]

                # --- 2D Monster Precision Filter ---
                # 1. BIJI SIKLUS (Biji 9, 1, 4, 7)
                if biji_f in [9, 1, 4, 7]:
                    score += 95
                
                # 2. SHADOW POSITION (Kepala ke Ekor)
                # Jika ekor baru (t) adalah Indeks dari kepala lama (9)
                if t == ID.get(kep_l, 'x'):
                    score += 60
                
                # 3. ANTI-SANDWICH (Jangan biarkan As=Ekor lagi)
                if line[0] == line[3]:
                    score -= 80

                # --- Final Construction ---
                line3, line4 = f"{kop}{l2}", f"{asn}{kop}{l2}"
                if line3 not in top3: top3.append(line3)
                if line4 not in top4: top4.append(line4)
                
            except Exception as e:
                pass

        elif market_name == 'GREECE':
            try:
                as_p1 = last_p1[0]
                as_p2 = all_res_data[0][1][0] if len(all_res_data[0]) > 1 else '8'
                asn = ID.get(as_p1, best_as[i % len(best_as)])
                kop = ID.get(as_p2, best_kop[i % len(best_kop)])
            except: pass

        # --- [ GLOBAL VERIFICATION & ANTI-DUPLICATE ] ---
        safety_counter = 0
        while (kop in l2 or kop == asn) and safety_counter < len(bbfs_list):
            kop = bbfs_list[(bbfs_list.index(kop) + 1) % len(bbfs_list)]
            safety_counter += 1

        # Final Construction
        l3_final = f"{kop}{l2}"
        l4_final = f"{asn}{kop}{l2}"
        
        if l3_final not in top3: top3.append(l3_final)
        if l4_final not in top4: top4.append(l4_final)

    # --- [ MONSTER AUDIT LAYER: AFTER LOOP ] ---
    # 1. Harmony Audit (Hapus angka kembar 4 atau urut)
    for idx, val in enumerate(top4):
        if len(set(val)) == 1 or val in "0123123423453456456756786789":
            top4[idx] = "".join([ID.get(d, d) if j % 2 == 0 else d for j, d in enumerate(val)])

    # 2. Sorting Monster
    top4.sort(key=lambda x: sum(scores.get(d, 0) for d in x), reverse=True)

    return top2[:15], top3[:15], top4[:15]

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
        # 1. CEK MODE MANUAL MACAU
        if market_code == "MACAU":
            print(f"\n[!] MODE MANUAL INPUT: {market_code}")
            p1 = input("Masukkan Result P1 (4 atau 5 angka): ").strip()
            p2 = input("Masukkan Result P2 (Kosongkan jika tidak ada): ").strip()
            p3 = input("Masukkan Result P3 (Kosongkan jika tidak ada): ").strip()
            
            if len(p1) >= 4:
                return [[p1, p2, p3]]
            else:
                print("Error: Angka P1 kurang dari 4 digit!")
                return []

        # 2. JIKA BUKAN MACAU, GUNAKAN HTTPX
        with httpx.Client(timeout=15.0, verify=False, follow_redirects=True) as client:
            if market_code == "HK_SPECIAL":
                url = "https://tabelsemalam.com/"
                r = client.get(url, headers=headers)
                soup = BeautifulSoup(r.text, 'html.parser')
                table = soup.find('table')
                if not table: return []
                
                res = []
                tbody = table.find('tbody')
                if not tbody: return []
                
                for row in tbody.find_all('tr'):
                    tds = row.find_all('td')
                    if len(tds) >= 2:
                        p1 = re.sub(r'\D', '', tds[1].text.strip())
                        p2, p3 = '', '' # Paksa P1 Only
                        if len(p1) == 4:
                            res.append([p1, p2, p3])
                return res[:40]

            # 3. JALUR UMUM
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
