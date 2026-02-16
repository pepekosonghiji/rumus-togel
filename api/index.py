import os, re, httpx
from flask import Flask, render_template, request, jsonify
from collections import Counter
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../templates'))

# DATABASE POLA ABADI (LOCKED)
ML = {'1':'0', '2':'5', '3':'8', '4':'7', '6':'9', '0':'1', '5':'2', '8':'3', '7':'4', '9':'6'}
TY = {'0':'7', '1':'4', '2':'9', '3':'6', '4':'1', '5':'8', '6':'3', '7':'0', '8':'5', '9':'2'}
ID = {'0':'5', '1':'6', '2':'7', '3':'8', '4':'9', '5':'0', '6':'1', '7':'2', '8':'3', '9':'4'}
SHIO_MAP = {10:"KUDA", 11:"KAMBING", 0:"MONYET", 1:"AYAM", 2:"ANJING", 3:"BABI", 4:"TIKUS", 5:"KERBAU", 6:"MACAN", 7:"KELINCI", 8:"NAGA", 9:"ULAR"}

TARGET_POOLS = {
    'WUHAN':'p28615', 'CAMBODIA': 'p3501', 'SYDNEY LOTTO': 'p2262', 
    'BUSAN POOLS':'p16063', 'OSAKA':'p28422', 'JEJU':'p22815'
}

# --- LOGIKA KHUSUS WUHAN (ISOLATED) ---
def get_wuhan_logic(all_res):
    d0 = all_res[0] # Result terakhir (misal 4146)
    
    # 1. Pola "Ekor Jadi Kepala" (Ciri Khas Wuhan)
    # Wuhan sering ambil Mistik/Taysen dari Ekor kemarin buat jadi Kepala hari ini
    k_1 = ML.get(d0[3], '0')
    k_2 = TY.get(d0[3], '0')
    k_3 = ID.get(d0[3], '0')
    
    # 2. Pola "Loncatan Mistik" untuk Ekor
    e_1 = ML.get(d0[2], '0')
    e_2 = TY.get(d0[2], '0')
    e_3 = d0[3] # Ekor tetap
    
    # Racikan 2D khusus Wuhan (Siklus Pendek)
    w_line = [
        k_1+e_1, k_1+e_2, k_2+e_1, k_2+e_3, 
        k_3+e_2, k_3+d0[3], e_1+k_1, e_2+k_2
    ]
    
    # BBFS Wuhan (Fokus pada 20 data terakhir saja agar tidak basi)
    counts = Counter("".join(all_res[:20]))
    bbfs = [x[0] for x in counts.most_common(6)]
    
    return {
        "core": ", ".join(list(dict.fromkeys(w_line))),
        "bbfs": " ".join(sorted(bbfs)),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "twin": f"{d0[3]}{d0[3]}, {k_1}{k_1}"
    }

# --- LOGIKA STANDAR (MARKET LAIN) ---
def get_standard_logic(all_res):
    d0 = all_res[0]
    counts = Counter("".join(all_res[:30]))
    bbfs = [x[0] for x in counts.most_common(6)]
    line = [d0[3]+ML.get(d0[3]), TY.get(d0[2])+d0[3], ID.get(d0[3])+d0[2]]
    return {
        "core": ", ".join(line),
        "bbfs": " ".join(sorted(bbfs)),
        "shio": SHIO_MAP.get(int(d0[2:]) % 12, "N/A"),
        "twin": f"{d0[3]}{d0[3]}"
    }

def fetch_results(market_code):
    results = []
    try:
        with httpx.Client(timeout=20.0, verify=False, follow_redirects=True) as client:
            url = f"https://dk9if7ik34.salamrupiah.com/history/result-mobile/{market_code}-pool-1"
            r = client.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            for row in soup.find('table', class_='table-history').find('tbody').find_all('tr'):
                tds = row.find_all('td')
                if len(tds) >= 4:
                    val = re.sub(r'\D', '', tds[3].text.strip())
                    if len(val) == 4: results.append(val)
    except: pass
    return results

@app.route('/analyze', methods=['POST'])
def analyze():
    m_name = request.form.get('market')
    m_code = TARGET_POOLS.get(m_name)
    all_res = fetch_results(m_code)
    if not all_res: return jsonify({"error": "Gagal"}), 500
    
    # Switch Logika berdasarkan Nama Market
    if m_name == "WUHAN":
        data = get_wuhan_logic(all_res)
    else:
        data = get_standard_logic(all_res)
        
    return jsonify({"status":"success", "market":m_name, "last":all_res[0], "data":data})

@app.route('/')
def index():
    return render_template('index.html', markets=sorted(TARGET_POOLS.keys()))

if __name__ == '__main__':
    app.run(debug=True)
