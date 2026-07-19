from flask import Flask, request, jsonify, send_from_directory
import json, os, difflib, requests
from groq import Groq

app = Flask(__name__, static_folder='.', static_url_path='')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR, DOC_DIR = os.path.join(BASE_DIR, "data"), os.path.join(BASE_DIR, "dokumanlar")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
EGITIM_FILE = os.path.join(DOC_DIR, "egitim.txt")

# API Anahtarların
WEATHER_API_KEY = "openweathermap api key"
# Groq İstemcisi
client = Groq(api_key="Grog api key girin")

os.makedirs(DATA_DIR, exist_ok=True); os.makedirs(DOC_DIR, exist_ok=True)

# Groq ile cevaplayan fonksiyon
def groq_ile_cevapla(soru):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": soru}],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return "Üzgünüm, genel bilgilere şu an erişemiyorum."

def hava_durumu_getir(sehir):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={WEATHER_API_KEY}&units=metric&lang=tr"
    try:
        cevap = requests.get(url).json()
        if cevap["cod"] == 200:
            return f"{sehir.capitalize()} şu an {cevap['main']['temp']}°C ve {cevap['weather'][0]['description']}."
        return "Şehri bulamadım."
    except: return "Hava durumuna bağlanamadım."

def load_users():
    if not os.path.exists(USERS_FILE): return {"admin": {"p": "admin", "role": "admin", "auth": True}}
    with open(USERS_FILE, "r") as f: return json.load(f)

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    users = load_users()
    if d['u'] in users and users[d['u']]['p'] == d['p']:
        return jsonify({"success": True, "role": users[d['u']]['role'], "auth": users[d['u']].get('auth', False)})
    return jsonify({"success": False})

@app.route('/api/chat', methods=['POST'])
def chat():
    d = request.json
    u, m, room = d['user'], d['msg'], d['room']
    
    if room == 'egitim':
        if "===" in m:
            q, a = m.split("===", 1)
            with open(EGITIM_FILE, "a", encoding="utf-8") as f: 
                f.write(json.dumps({"q": q.strip(), "a": a.strip()}) + "\n")
        return jsonify({"success": True})

    path = os.path.join(DATA_DIR, "genel.txt") if room == 'genel' else os.path.join(DATA_DIR, f"ozel_{u}.txt")
    with open(path, "a", encoding="utf-8") as f: f.write(json.dumps({"u": u, "m": m}) + "\n")
    
    if "hey ai" in m.lower():
        temiz_mesaj = m.lower().replace("hey ai", "").strip()
        resp = None

        # 1. Hava Durumu
        if "hava" in m.lower():
            kelimeler = temiz_mesaj.split()
            sehir = next((k.replace("'da", "").replace("'de", "") for k in kelimeler if k not in ["hava", "nasıl", "durumu", "ne"]), None)
            resp = hava_durumu_getir(sehir) if sehir else "Hangi şehri sordun?"
        
        # 2. Eğitim Dosyası (cutoff 0.75)
        if not resp and os.path.exists(EGITIM_FILE):
            with open(EGITIM_FILE, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f if line.strip()]
                qs = [l['q'].lower() for l in lines]
                best = difflib.get_close_matches(temiz_mesaj, qs, n=1, cutoff=0.75)
                if best:
                    for l in lines:
                        if l['q'].lower() == best[0]: resp = l['a']
        
        # 3. Groq (Genel Bilgiler)
        if not resp:
            resp = groq_ile_cevapla(temiz_mesaj)
        
        with open(path, "a", encoding="utf-8") as f: f.write(json.dumps({"u": "AI", "m": resp}) + "\n")
    return jsonify({"success": True})

@app.route('/api/get_msgs', methods=['POST'])
def get_msgs():
    d = request.json
    path = os.path.join(DATA_DIR, "genel.txt") if d['room'] == 'genel' else (os.path.join(DATA_DIR, f"ozel_{d['user']}.txt") if d['room'] == 'ozel' else EGITIM_FILE)
    if not os.path.exists(path): return jsonify([])
    if d['room'] == 'egitim': return jsonify([{"u": "Admin", "m": f"{json.loads(l)['q']} === {json.loads(l)['a']}"} for l in open(path, encoding="utf-8")])
    with open(path, "r", encoding="utf-8") as f: return jsonify([json.loads(l) for l in f if l.strip()])

if __name__ == "__main__": app.run()
