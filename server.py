import os, json, time
from http.server import SimpleHTTPRequestHandler, HTTPServer

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

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)
        
        if self.path == "/api/login":
            users = get_data(USER_FILE, {"admin": {"password": "nimda", "role": "admin"}})
            u, p = data.get("u"), data.get("p")
            if u in users and users[u]["password"] == p:
                self.send_response(200); self.end_headers()
                self.wfile.write(json.dumps({"success": True, "role": users[u].get("role", "user")}).encode())
            else:
                self.send_response(401); self.end_headers()
        
        elif self.path == "/api/chat":
            chats = get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            room, msg, user = data['room'], data['msg'], data['user']
            reply = None
            if "hey ai" in msg.lower():
                reply = "AI: Bilgim yok."
                for f in os.listdir("dokumanlar"):
                    with open(f"dokumanlar/{f}", "r", encoding="utf-8") as doc:
                        if any(word in doc.read().lower() for word in msg.lower().split() if len(word) > 3):
                            reply = "AI: Dokümanlarımda eşleşen bilgi bulundu."
            chats[room].append({"user": user, "msg": msg, "reply": reply, "time": time.strftime("%H:%M")})
            with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(chats, f)
            self.send_response(200); self.end_headers()

        elif self.path == "/api/admin/set_role":
            users = get_data(USER_FILE, {})
            users[data["target"]] = {"password": users.get(data["target"], {}).get("password", "123"), "role": "yetkili"}
            with open(USER_FILE, "w", encoding="utf-8") as f: json.dump(users, f)
            self.send_response(200); self.end_headers()

        elif self.path == "/api/get_data":
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"chats": get_data(CHAT_FILE, {}), "users": get_data(USER_FILE, {})}).encode())

if __name__ == "__main__":
    HTTPServer(('', 8000), CustomHandler).serve_forever()
