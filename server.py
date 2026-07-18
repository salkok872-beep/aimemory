import os, json
from http.server import SimpleHTTPRequestHandler, HTTPServer

os.makedirs("dokumanlar", exist_ok=True)
os.makedirs("data", exist_ok=True)
CHAT_FILE = "data/chat.json"
USER_FILE = "data/users.json"

def get_db():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f: return json.load(f)
    return {"admin": {"password": "123", "role": "admin"}}

def get_chats():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f: return json.load(f)
    return {"genel": [], "ozel": [], "egitim": []}

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        # Giriş Kontrolü
        if self.path == "/api/login":
            db = get_db()
            u, p = data.get("u"), data.get("p")
            if u in db and db[u]["password"] == p:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "role": db[u]["role"]}).encode())
            return

        # Oda Yetki Kontrolü
        room, role = data.get("room"), data.get("role")
        access = {"admin": ["genel", "ozel", "egitim"], "yetkili": ["genel", "ozel"], "user": ["genel"]}
        
        if room not in access.get(role, []):
            self.send_response(403); self.end_headers(); return

        # Sohbet Yazma
        if self.path == "/api/chat":
            chats = get_chats()
            chats[room].append({"user": data['user'], "msg": data['msg']})
            with open(CHAT_FILE, "w") as f: json.dump(chats, f)
            self.send_response(200); self.end_headers()

        # Admin Dosya Yükleme
        elif self.path == "/api/admin/upload" and role == "admin":
            with open(f"dokumanlar/{data['name']}", "w") as f: f.write(data['content'])
            self.send_response(200); self.end_headers()

        # Veri Çekme
        elif self.path == "/api/get_data":
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps(get_chats()).encode())

if __name__ == "__main__":
    HTTPServer(('', 8000), CustomHandler).serve_forever()
