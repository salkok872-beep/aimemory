import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Klasörleri hazırla
os.makedirs("data", exist_ok=True)
os.makedirs("dokumanlar", exist_ok=True)

USER_FILE = "data/users.json"
GENEL_CHAT = "data/genel_sohbet.txt"

def load_users():
    if not os.path.exists(USER_FILE): return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

# Admin hesap oluşturma
if "admin" not in load_users():
    u = load_users()
    u["admin"] = {"p": "nimda", "role": "admin", "authorized": True}
    save_users(u)

def append_line(file_path, data):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def read_lines(file_path):
    if not os.path.exists(file_path): return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self): self.send_response(200); self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        if self.path == "/api/register":
            users = load_users()
            u = data.get("u")
            if u and u not in users:
                users[u] = {"p": data.get("p"), "role": "user", "authorized": False}
                save_users(users)
                self.wfile.write(json.dumps({"success": True}).encode())
            else:
                self.wfile.write(json.dumps({"success": False, "msg": "Kullanıcı mevcut"}).encode())

        elif self.path == "/api/login":
            users = load_users()
            u, p = data.get("u"), data.get("p")
            if users.get(u) and users[u]['p'] == p:
                self.wfile.write(json.dumps({"success": True, "role": users[u]['role'], "authorized": users[u].get('authorized', False)}).encode())
            else:
                self.wfile.write(json.dumps({"success": False}).encode())

        elif self.path == "/api/admin/authorize":
            users = load_users()
            target = data.get("user")
            if target in users:
                users[target]["authorized"] = data.get("status", False)
                save_users(users)
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/chat":
            room = data.get('room', 'genel')
            path = "data/genel_sohbet.txt" if room == "genel" else ("dokumanlar/egitim.txt" if room == "egitim" else f"data/{room}.txt")
            append_line(path, {"user": data.get('user'), "msg": data.get('msg')})
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/get_data":
            res = {
                "genel": read_lines(GENEL_CHAT),
                "egitim": read_lines("dokumanlar/egitim.txt"),
                "ozel": {f: read_lines(f"data/{f}") for f in os.listdir("data") if "_sohbeti" in f}
            }
            self.wfile.write(json.dumps(res).encode())

if __name__ == "__main__":
    HTTPServer(('0.0.0.0', 8000), CustomHandler).serve_forever()
