import os, json, http.server, socketserver

# Dizinleri hazırl
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
        data = json.loads(body)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if self.path == "/api/register":
            users = get_data(USER_FILE, {})
            u = data.get("u")
            if u not in users:
                users[u] = {"p": data.get("p"), "role": "user", "authorized": False}
                with open(USER_FILE, "w") as f: json.dump(users, f)
                self.wfile.write(json.dumps({"success": True}).encode())
            else:
                self.wfile.write(json.dumps({"success": False, "msg": "Kullanıcı mevcut"}).encode())

        elif self.path == "/api/login":
            users = get_data(USER_FILE, {})
            u, p = data.get("u"), data.get("p")
            if users.get(u) and users[u]['p'] == p:
                self.wfile.write(json.dumps({"success": True, "role": users[u]['role'], "authorized": users[u].get('authorized', False)}).encode())
            else:
                self.wfile.write(json.dumps({"success": False}).encode())

        elif self.path == "/api/admin/authorize":
            users = get_data(USER_FILE, {})
            users[data["user"]]["authorized"] = True
            with open(USER_FILE, "w") as f: json.dump(users, f)
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/chat":
            chats = get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            reply = None
            if "hey ai" in data['msg'].lower():
                reply = "AI: Veritabanımda bilgim yok."
                for f in os.listdir("dokumanlar"):
                    with open(f"dokumanlar/{f}", "r", encoding="utf-8") as doc:
                        if data['msg'].lower() in doc.read().lower(): reply = "AI: Belgeye göre yanıtlandı."
            
            chats[data['room']].append({"user": data['user'], "msg": data['msg'], "reply": reply})
            with open(CHAT_FILE, "w") as f: json.dump(chats, f)
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/get_data":
            self.wfile.write(json.dumps({"chats": get_data(CHAT_FILE, {}), "users": get_data(USER_FILE, {})}).encode())

if __name__ == "__main__":
    print("Sunucu 8000 portunda çalışıyor...")
    with socketserver.TCPServer(("", 8000), CustomHandler) as httpd:
        httpd.serve_forever()

import os

# Render'ın verdiği portu yakala
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    # Sunucuyu başlat
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, MyHandler)
    print(f"Sunucu {port} portunda çalışıyor...")
    httpd.serve_forever()
