import os, json
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Dizinleri oluştur
os.makedirs("data", exist_ok=True)
os.makedirs("dokumanlar", exist_ok=True)

USER_FILE = "data/users.json"
CHAT_FILE = "data/chat.json"

def get_data(f, default):
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as file: return json.load(file)
    return default

def get_ai_reply(msg):
    # Hey AI tetikleyicisi ve RAG Mantığı
    if "hey ai" in msg.lower():
        files = os.listdir("dokumanlar")
        for f in files:
            with open(f"dokumanlar/{f}", "r", encoding="utf-8") as doc:
                content = doc.read().lower()
                # Eğer mesajın içindeki kelime dokümanda geçiyorsa cevapla
                words = [w for w in msg.lower().split() if len(w) > 3]
                for word in words:
                    if word in content: return f"AI: Bilgilerime göre {word} hakkında: {content[:150]}..."
        return "AI: Üzgünüm, bu konuda yeterli veri setine sahip değilim."
    return None

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        # Giriş/Kayıt
        if self.path == "/api/login":
            users = get_data(USER_FILE, {"admin": {"password": "nimda", "role": "admin"}})
            u, p = data.get("u"), data.get("p")
            if u in users and users[u]["password"] == p:
                self.send_response(200); self.end_headers()
                self.wfile.write(json.dumps({"success": True, "role": users[u]["role"]}).encode())
            else: self.send_response(401); self.end_headers()
            return

        # Yetki Verme (Sadece Admin)
        if self.path == "/api/set_role":
            if data.get("admin_p") == "nimda":
                users = get_data(USER_FILE, {})
                users[data["target"]] = {"password": "123", "role": "yetkili"}
                with open(USER_FILE, "w") as f: json.dump(users, f)
                self.send_response(200); self.end_headers()
            return

        # Sohbet
        if self.path == "/api/chat":
            chats = get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})
            reply = get_ai_reply(data['msg'])
            chats[data['room']].append({"user": data['user'], "msg": data['msg'], "reply": reply})
            with open(CHAT_FILE, "w") as f: json.dump(chats, f)
            self.send_response(200); self.end_headers()
            return

        # Dosya/Eğitim Yükleme
        if self.path == "/api/upload":
            if data.get("role") == "admin":
                with open(f"dokumanlar/{data['name']}.txt", "w", encoding="utf-8") as f: f.write(data['content'])
                self.send_response(200); self.end_headers()
            return

        # Veri Getir
        if self.path == "/api/get":
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps(get_data(CHAT_FILE, {"genel": [], "ozel": [], "egitim": []})).encode())

if __name__ == "__main__":
    HTTPServer(('', 8000), Handler).serve_forever()
