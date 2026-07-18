import threading
import time
from datetime import datetime, timedelta

# Aktiflik takibi için sözlük
last_activity = {}

def check_activity():
    while True:
        now = datetime.now()
        for u in USERS:
            # 60 saniye mesaj yoksa çevrimdışı yap
            if u in last_activity and now - last_activity[u] > timedelta(seconds=60):
                USERS[u]['active'] = False
        time.sleep(10) # 10 saniyede bir kontrol et

# Sunucu başlarken arka plan görevlerini başlat
if __name__ == "__main__":
    threading.Thread(target=check_activity, daemon=True).start()
    threading.Thread(target=auto_rag_scanner, daemon=True).start()
    HTTPServer(('', 8000), CustomHandler).serve_forever()

# Admin kontrolü ve dosya yükleme için örnek mantık:
def upload_file_logic(admin_user, filename, content):
    if USERS.get(admin_user, {}).get("role") == "admin":
        with open(os.path.join("dokumanlar", filename), "w", encoding="utf-8") as f:
            f.write(content)
        scan_documents() # Admin isteğiyle anlık tarama
        return True
    return False
