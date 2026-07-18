import os, json, time
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Ensure directories exist
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

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)
        
        if self.path == "/api/login":
            users = get_data(USER_FILE, {"admin": {"password": "nimda", "role": "admin", "authorized": True}})
            u, p = data.get("u"), data.get("p")
            if u not in users: users[u] = {"password": p, "role": "user", "authorized": False}
            if users[u]["password"] == p:
                save_data(USER_FILE, users)
                self.send_response(200); self.end_headers()
                self.wfile.write(json.dumps({"success": True, "role": users[u]["role"], "authorized": users[u]["authorized"]}).encode())
            else: self.send_response(401); self.end_headers()

        elif self.path == "/api/chat":
            chats = get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            room, msg, user = data['room'], data['msg'], data['user']
            reply = None
            if "hey ai" in msg.lower():
                reply = "AI: Verilerim taranıyor..."
                for f in os.listdir("dokumanlar"):
                    with open(f"dokumanlar/{f}", "r", encoding="utf-8") as doc:
                        if msg.lower() in doc.read().lower(): reply = "AI: Dokümanlarımda eşleşen bilgi bulundu."
            
            chats[room].append({"user": user, "msg": msg, "reply": reply, "time": time.strftime("%H:%M")})
            save_data(CHAT_FILE, chats)
            self.send_response(200); self.end_headers()

        elif self.path == "/api/admin/set_role":
            users = get_data(USER_FILE, {})
            if data.get("admin_u") == "admin":
                users[data["target"]]["authorized"] = data["status"]
                save_data(USER_FILE, users)
            self.send_response(200); self.end_headers()

        elif self.path == "/api/admin/train":
            with open(f"dokumanlar/{int(time.time())}.txt", "w", encoding="utf-8") as f:
                f.write(data["content"])
            self.send_response(200); self.end_headers()

        elif self.path == "/api/get_data":
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"chats": get_data(CHAT_FILE, {}), "users": get_data(USER_FILE, {})}).encode())

if __name__ == "__main__":
    HTTPServer(('', 8000), CustomHandler).serve_forever()
