import os
import json
import http.server
from http.server import HTTPServer

# Dizinleri hazırla
os.makedirs("data", exist_ok=True)
os.makedirs("dokumanlar", exist_ok=True)

USER_FILE = "data/users.json"
CHAT_FILE = "data/chat.json"

def get_data(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return default
    return default

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body)
        except:
            data = {}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if self.path == "/api/register":
            users = get_data(USER_FILE, {})
            u = data.get("u")
            if u and u not in users:
                users[u] = {"p": data.get("p"), "role": "user", "authorized": False}
                with open(USER_FILE, "w", encoding="utf-8") as f: json.dump(users, f)
                self.wfile.write(json.dumps({"success": True}).encode())
            else:
                self.wfile.write(json.dumps({"success": False, "msg": "Kullanici mevcut veya gecersiz"}).encode())

        elif self.path == "/api/login":
            users = get_data(USER_FILE, {})
            u, p = data.get("u"), data.get("p")
            if users.get(u) and users[u]['p'] == p:
                self.wfile.write(json.dumps({"success": True, "role": users[u]['role'], "authorized": users[u].get('authorized', False)}).encode())
            else:
                self.wfile.write(json.dumps({"success": False}).encode())

        elif self.path == "/api/admin/authorize":
            users = get_data(USER_FILE, {})
            target_user = data.get("user")
            status = data.get("status", False)
            if target_user in users:
                users[target_user]["authorized"] = status
                with open(USER_FILE, "w", encoding="utf-8") as f: json.dump(users, f)
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/chat":
            chats = get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            reply = None
            msg = data.get('msg', '')
            
            if "hey ai" in msg.lower():
                reply = "AI: Veritabanımda bilgim yok."
                for f_name in os.listdir("dokumanlar"):
                    file_path = os.path.join("dokumanlar", f_name)
                    with open(file_path, "r", encoding="utf-8") as doc:
                        if msg.lower() in doc.read().lower(): 
                            reply = "AI: Belgeye göre yanıtlandı."
                            break
            
            room = data.get('room', 'genel')
            chats.setdefault(room, []).append({
                "user": data.get('user', 'Anonim'), 
                "msg": msg, 
                "reply": reply
            })
            with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(chats, f)
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/get_data":
            self.wfile.write(json.dumps({
                "chats": get_data(CHAT_FILE, {}), 
                "users": get_data(USER_FILE, {})
            }).encode())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server_address = ('0.0.0.0', port)
    print(f"Sunucu {port} portunda çalışıyor...")
    httpd = HTTPServer(server_address, CustomHandler)
    httpd.serve_forever()
