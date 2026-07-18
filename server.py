import os, json, http.server, socketserver

os.makedirs("data", exist_ok=True)
os.makedirs("dokumanlar", exist_ok=True)

USER_FILE = "data/users.json"
CHAT_FILE = "data/chat.json"

def get_data(f, default):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as f_obj: return json.load(f_obj)
    return default

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.path == "/api/register":
            users = get_data(USER_FILE, {"admin": {"password": "nimda", "role": "admin"}})
            if data['u'] not in users:
                users[data['u']] = {"password": data['p'], "role": "user"}
                with open(USER_FILE, "w", encoding="utf-8") as f: json.dump(users, f)
                self.wfile.write(json.dumps({"success": True}).encode())
            else: self.wfile.write(json.dumps({"success": False}).encode())

        elif self.path == "/api/login":
            users = get_data(USER_FILE, {"admin": {"password": "nimda", "role": "admin"}})
            u, p = data.get("u"), data.get("p")
            if users.get(u) and users[u]['password'] == p:
                self.wfile.write(json.dumps({"success": True, "role": users[u]['role']}).encode())
            else: self.wfile.write(json.dumps({"success": False}).encode())

        elif self.path == "/api/chat":
            chats = get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            reply = None
            if "hey ai" in data['msg'].lower():
                reply = "AI: Belge bulunamadı."
                for f in os.listdir("dokumanlar"):
                    with open(f"dokumanlar/{f}", "r", encoding="utf-8") as doc:
                        if data['msg'].lower() in doc.read().lower(): reply = "AI: Bilgi mevcut."
            chats[data['room']].append({"user": data['user'], "msg": data['msg'], "reply": reply})
            with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(chats, f)
            self.wfile.write(json.dumps({"success": True}).encode())

        elif self.path == "/api/get_data":
            self.wfile.write(json.dumps({"chats": get_data(CHAT_FILE, {}), "users": get_data(USER_FILE, {})}).encode())

        elif self.path == "/api/admin/auth":
            users = get_data(USER_FILE, {})
            users[data['target']]['role'] = 'yetkili'
            with open(USER_FILE, "w") as f: json.dump(users, f)
            self.wfile.write(json.dumps({"success": True}).encode())

if __name__ == "__main__":
    socketserver.TCPServer(('', 8000), Handler).serve_forever()
