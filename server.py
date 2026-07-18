import os, json
from http.server import SimpleHTTPRequestHandler, HTTPServer

os.makedirs("dokumanlar", exist_ok=True)
os.makedirs("data", exist_ok=True)
CHAT_FILE = "data/chat.json"

def get_chats():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"genel": [], "ozel": [], "egitim": []}

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        role = data.get('role', 'user')
        room = data.get('room', 'genel')

        # Rol bazlı erişim matrisi
        access = {
            "admin": ["genel", "ozel", "egitim"],
            "yetkili": ["genel", "ozel"],
            "user": ["genel"]
        }

        # Yetkisiz erişim denetimi
        if room not in access.get(role, []):
            self.send_response(403)
            self.end_headers()
            return

        # Mesaj kaydetme veya Dosya yükleme işlemleri
        if self.path == "/api/chat":
            chats = get_chats()
            chats[room].append({"user": data['username'], "msg": data['message']})
            with open(CHAT_FILE, "w", encoding="utf-8") as f: json.dump(chats, f)
            self.send_response(200)
            self.end_headers()
        
        elif self.path == "/api/admin/upload" and role == "admin":
            with open(f"dokumanlar/{data['name']}", "w", encoding="utf-8") as f:
                f.write(data['content'])
            self.send_response(200)
            self.end_headers()

if __name__ == "__main__":
    HTTPServer(('', 8000), CustomHandler).serve_forever()
