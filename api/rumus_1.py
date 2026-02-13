import re
import random
import httpx
from bs4 import BeautifulSoup
from collections import Counter
from itertools import permutations, combinations

# --- TABEL REFERENSI ---
TABEL_INDEKS = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
TABEL_MISTIK_BARU = {'0':'8', '1':'7', '2':'6', '3':'9', '4':'5', '8':'0', '7':'1', '6':'2', '9':'3', '5':'4'}
TABEL_TAYSEN = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}

# Re-use Target Pools & Headers untuk fungsi fetch internal
TARGET_POOLS = {
    'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 'HONGKONG LOTTO': 'p2263',
    'CHINA POOLS': 'p2670', 'BUSAN POOLS': 'p16063', 'WUHAN': 'p28615',
    'JAPAN POOLS': 'custom_japan', 'HONGKONG POOLS': 'kia_2',
    'SINGAPORE POOLS': 'kia_3', 'SYDNEY POOLS': 'kia_4'
}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# --- CORE UTILS (Copy dari index agar mandiri) ---

def fetch_results_internal(code):
    results = []
    try:
        with httpx.Client(timeout=8.0, verify=False, follow_redirects=True, headers=HEADERS) as client:
            if code == 'custom_japan':
                r = client.get("https://tabelupdate.online/data-keluaran-japan/")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
            elif code.startswith('kia_'):
                idx = int(code.split('_')[1])
                r = client.get("https://nomorkiajit.com/hksgpsdy")
                rows = BeautifulSoup(r.text, 'html.parser').select('tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 5:
                        val = re.sub(r'\D', '', tds[idx].text.strip())
                        if len(val) == 4: results.append(val)
            else:
                r = client.get(f"https://tgr7grldrc.salamrupiah.com/history/result-mobile/{code}-pool-1")
                rows = BeautifulSoup(r.text, 'html.parser').select('table tbody tr')
                for row in rows:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        val = re.sub(r'\D', '', tds[3].text.strip())
                        if len(val) == 4: results.append(val)
    except: pass
    return results

def get_weighted_stats(all_res):
    if not all_res: return []
    recent = "".join(all_res[:10])
    older = "".join(all_res[10:40])
    weights = Counter()
    for d in recent: weights[d] += 3
    for d in older: weights[d] += 1
    hot_weighted = [x[0] for x in weights.most_common(4)]
    
    last_seen = {str(i): 99 for i in range(10)}
    for idx, res in enumerate(all_res[:20]):
        for d in res:
            if last_seen[d] == 99: last_seen[d] = idx
    prime_gap = [d for d, gap in last_seen.items() if 3 <= gap <= 5]
    return list(dict.fromkeys(hot_weighted + prime_gap))[:6]

def generate_2d(bbfs_str):
    digits = list(set(bbfs_str))
    if len(digits) < 2: return ""
    return ", ".join(sorted(["".join(p) for p in permutations(digits, 2)]))

def generate_top_set(bbfs_list, count=2):
    if len(bbfs_list) < 4: return ["-"], ["-"]
    c3 = list(combinations(bbfs_list, 3))
    c4 = list(combinations(bbfs_list, 4))
    return ["".join(x) for x in random.sample(c3, min(count, len(c3)))], \
           ["".join(x) for x in random.sample(c4, min(count, len(c4)))]

# --- FUNGSI UTAMA YANG DIPANGGIL INDEX.PY ---

def hitung_rumus_satu(market_key, external_res=None):
    """
    Fungsi ini akan dipanggil oleh index.py.
    Jika index.py sudah punya data (external_res), gunakan itu.
    Jika tidak, fetch data sendiri.
    """
    code = TARGET_POOLS.get(market_key)
    all_res = external_res if external_res else fetch_results_internal(code)
    
    if not all_res:
        all_res = ["".join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(10)]
    
    last_res = all_res[0]
    am_base = get_weighted_stats(all_res)
    
    # Tambahan logika khusus Cambodia jika dipilih
    if market_key == 'CAMBODIA':
        mb_ekor = TABEL_MISTIK_BARU.get(last_res[-1])
        if mb_ekor not in am_base: am_base.append(mb_ekor)
    
    # Pengunci BBFS Utama (Min 5, Max 6)
    bbfs_main_list = am_base[:6]
    while len(bbfs_main_list) < 5: # Pastikan minimal 5
        r_digit = str(random.randint(0,9))
        if r_digit not in bbfs_main_list: bbfs_main_list.append(r_digit)
    
    bbfs_main_str = "".join(bbfs_main_list)
    
    # Shadow BBFS (Pola Indeks - Minimal 5 Digit)
    shadow_raw = [TABEL_INDEKS.get(d, d) for d in bbfs_main_list]
    shadow_list = []
    for s in shadow_raw:
        if s not in shadow_list: shadow_list.append(s)
    
    # Pastikan Shadow minimal 5 digit
    if len(shadow_list) < 5:
        for d in bbfs_main_list:
            mb = TABEL_MISTIK_BARU.get(d, d)
            if mb not in shadow_list: shadow_list.append(mb)
            if len(shadow_list) == 5: break
            
    bbfs_shadow_str = "".join(shadow_list[:5])

    m3, m4 = generate_top_set(bbfs_main_list)
    s3, s4 = generate_top_set(shadow_list[:5])

    return {
        "market": market_key,
        "last": last_res,
        "bbfs": bbfs_main_str,
        "shadow": bbfs_shadow_str,
        "list2d_main": generate_2d(bbfs_main_str),
        "list2d_shadow": generate_2d(bbfs_shadow_str),
        "top3d": f"Main: {', '.join(m3)} | Shad: {', '.join(s3)}",
        "top4d": f"Main: {', '.join(m4)} | Shad: {', '.join(s4)}",
        "posisi": f"Kpl: {bbfs_main_list[0]} | Ekr: {bbfs_main_list[1]}"
    }
