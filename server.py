import os, json, threading, time
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Dizinleri oluştur
os.makedirs("dokumanlar", exist_ok=True)
os.makedirs("kullanicilar", exist_ok=True)
os.makedirs("sohbet_gecmis", exist_ok=True)

USERS_FILE = "kullanicilar/users.json"

def load_db():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f: return json.load(f)
    return {"admin": {"password": "nimda", "role": "admin", "active": False, "privateAccess": True}}

def save_db(db):
    with open(USERS_FILE, "w") as f: json.dump(db, f)

DB = load_db()

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        # Giriş/Kayıt/Yetki işlemleri burada DB değişkenine yazılır
        if self.path == "/api/admin/update_permission":
            DB[data['target_user']]['privateAccess'] = data['privateAccess']
            save_db(DB)
            
        # Admin dosya yükleme (dokumanlar klasörüne)
        if self.path == "/api/admin/upload":
            if DB.get(data['admin_user'], {}).get("role") == "admin":
                with open(f"dokumanlar/{data['name']}", "w", encoding="utf-8") as f:
                    f.write(data['content'])
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(DB).encode())

# Otomatik Tarama (RAG)
def rag_worker():
    while True:
        # dokumanlar klasöründeki dosyaları oku ve yapay zekaya bağla
        time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=rag_worker, daemon=True).start()
    HTTPServer(('', 8000), CustomHandler).serve_forever()
