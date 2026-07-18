import os, json
from http.server import SimpleHTTPRequestHandler, HTTPServer

os.makedirs("data", exist_ok=True)
CHAT_FILE = "data/chat.json"
USER_FILE = "data/users.json"

def get_db(f_path, default):
    if os.path.exists(f_path):
        with open(f_path, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return default
    return default

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body)

        if self.path == "/api/chat":
            chats = get_db(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            room = data.get("room", "genel")
            # Mesajı listeye ekle
            chats[room].append({"user": data['user'], "msg": data['msg']})
            with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(chats, f)
            self.send_response(200)
            self.end_headers()
        
        elif self.path == "/api/get_data":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            chats = get_db(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            self.wfile.write(json.dumps(chats).encode())
        
        else: # Diğer işlemler (login vb.)
            self.send_response(200); self.end_headers()

if __name__ == "__main__":
    HTTPServer(('', 8000), CustomHandler).serve_forever()
