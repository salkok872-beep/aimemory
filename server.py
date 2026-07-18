import os
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime

os.makedirs("dokumanlar", exist_ok=True)
os.makedirs("sohbet_gecmis", exist_ok=True)
os.makedirs("kullanicilar", exist_ok=True)

USER_FILE = os.path.join("kullanicilar", "kullanicilar.txt")

def load_users_from_file():
    users = {"admin": {"password": "nimda", "role": "admin", "privateAccess": True}}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("---"):
                    continue
                try:
                    parts = line.split("] ", 1)
                    if len(parts) < 2:
                        continue
                    data_part = parts[1]
                    info = data_part.split(" | ")
                    username = info[0].replace("K:", "").strip()
                    password = info[1].replace("S:", "").strip()
                    private_access = info[2].replace("Izin:", "").strip() == "True"
                    
                    if username != "admin":
                        users[username] = {"password": password, "role": "user", "privateAccess": private_access}
                    else:
                        users["admin"]["privateAccess"] = private_access
                except Exception:
                    continue
    return users

def save_user_to_file(username, password, private_access=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(USER_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] K:{username} | S:{password} | Izin:{private_access}\n")

def rewrite_all_users():
    with open(USER_FILE, "w", encoding="utf-8") as f:
        for username, data in USERS.items():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] K:{username} | S:{data['password']} | Izin:{data['privateAccess']}\n")

USERS = load_users_from_file()

def log_to_file(file_name, text):
    file_path = os.path.join("sohbet_gecmis", file_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n----------------------------------------\n")

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            if os.path.exists("index.html"):
                with open("index.html", "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b"index.html bulunamadi!")
        else:
            super().do_GET()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if parsed_url.path == "/api/login":
            u, p = post_data.get("username"), post_data.get("password")
            if u in USERS and USERS[u]["password"] == p:
                res = {"success": True, "role": USERS[u]["role"], "privateAccess": USERS[u]["privateAccess"]}
            else:
                res = {"success": False, "message": "Hatali kullanici adi veya sifre!"}
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif parsed_url.path == "/api/register":
            u, p = post_data.get("username"), post_data.get("password")
            if not u or not p:
                res = {"success": False, "message": "Kullanici adi ve sifre bos olamaz!"}
            elif u in USERS:
                res = {"success": False, "message": "Bu kullanici adi zaten alinmis!"}
            else:
                USERS[u] = {"password": p, "role": "user", "privateAccess": False}
                save_user_to_file(u, p, False)
                res = {"success": True, "message": "Kayit basariyla tamamlandi! Giris yapabilirsiniz."}
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif parsed_url.path == "/api/chat":
            u = post_data.get("username", "Anonim")
            msg = post_data.get("message", "")
            target_room = post_data.get("targetRoom", False) # Arayüzden seçilen odayı dinle
            
            if target_room:
                file_target = f"{u}_ozel_sohbet.txt"
                reply = f"🤖 [Ozel AI] {u} icin ozel RAG odasi aktif. Dokumanlar taranabilir."
                log_to_file(file_target, f"Kullanici: {msg}")
                log_to_file(file_target, f"Sistem: {reply}")
            else:
                file_target = "genel_sohbet.txt"
                reply = f"🤖 [Genel AI] Ortak havuzdasiniz. Herkes bu odada yazisiyor."
                log_to_file(file_target, f"[{u}] Kullanici: {msg}")
                log_to_file(file_target, f"Sistem: {reply}")
            self.wfile.write(json.dumps({"reply": reply}).encode('utf-8'))

        elif parsed_url.path == "/api/admin/update_permission":
            t, acc = post_data.get("target_user"), post_data.get("privateAccess")
            if t in USERS: 
                USERS[t]["privateAccess"] = acc
                rewrite_all_users()
                res = {"success": True, "users": USERS}
            else:
                res = {"success": False}
            self.wfile.write(json.dumps(res).encode('utf-8'))

        elif parsed_url.path == "/api/admin/users":
            self.wfile.write(json.dumps({"users": USERS}).encode('utf-8'))

if __name__ == "__main__":
    print("🚀 Sunucu http://localhost:8000 adresinde calisiyor...")
    HTTPServer(('', 8000), CustomHandler).serve_forever()
