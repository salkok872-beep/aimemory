import os, json
from http.server import SimpleHTTPRequestHandler, HTTPServer

os.makedirs("data", exist_ok=True)
os.makedirs("dokumanlar", exist_ok=True)

CHAT_FILE = "data/chat.json"
USER_FILE = "data/users.json"

def get_db(f, d):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as f_obj: return json.load(f_obj)
    return d

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)

        if self.path == "/api/login":
            users = get_db(USER_FILE, {"admin": {"password": "nimda", "role": "admin"}})
            u, p = data.get("u"), data.get("p")
            if u in users and users[u]["password"] == p:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "role": users[u]["role"]}).encode())
            else:
                self.send_response(401); self.end_headers()
        
        elif self.path == "/api/chat":
            chats = get_db(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            room = data['room']
            msg_obj = {"user": data['user'], "msg": data['msg']}
            
            # Hey AI Tetikleyicisi
            if "hey ai" in data['msg'].lower():
                msg_obj["reply"] = "AI: [Veri İşlendi]" 
            
            chats[room].append(msg_obj)
            with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(chats, f)
            self.send_response(200); self.end_headers()

        elif self.path == "/api/get_data":
            chats = get_db(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(chats).encode())

        elif self.path == "/api/admin/set_role":
            users = get_db(USER_FILE, {})
            users[data['target']] = {"password": "123", "role": "yetkili"}
            with open(USER_FILE, "w") as f: json.dump(users, f)
            self.send_response(200); self.end_headers()

if __name__ == "__main__":
    HTTPServer(('', 8000), Handler).serve_forever()
