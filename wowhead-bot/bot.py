import os
import time
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1564335678458957874/k-T8sQPIgKuxCfqYETULyuE3NdSVDNqaTnyaXYH-PXt2DBa7xKXIRMZdak_VHfBTzyy9")
NEWS_URL = "https://www.wowhead.com/forever/news"
LAST_ENTRY_FILE = "last_forever_title.txt"

def get_last_title():
    if os.path.exists(LAST_ENTRY_FILE):
        with open(LAST_ENTRY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def set_last_title(title):
    with open(LAST_ENTRY_FILE, "w", encoding="utf-8") as f:
        f.write(title)

def send_to_discord(content):
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        if chunk.strip():
            payload = {"content": chunk}
            res = requests.post(WEBHOOK_URL, json=payload)
            print(f"Discord gönderim durumu: {res.status_code}")
            time.sleep(1)

def run():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Wowhead Forever sayfası çekiliyor...")
    res = requests.get(NEWS_URL, headers=headers)
    print(f"Sayfa yanıt kodu: {res.status_code}")
    
    if res.status_code != 200:
        print("Sayfaya erişilemedi!")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    
    # Sayfadaki haber kartlarını bul
    card = soup.find("div", class_="news-list-card")
    if not card:
        # Alternatif kart seçici
        card = soup.find("div", class_="news-card")
    
    if not card:
        print("Haber kartı bulunamadı. Sayfa yapısı inceleniyor...")
        # Başlık ve içeriği genel linklerden arayalım
        first_h2 = soup.find("h2")
        title = first_h2.get_text(strip=True) if first_h2 else "WoW Forever Güncellemesi"
        snippet = "Detaylar için haber sayfasına bakın."
        link = NEWS_URL
    else:
        title_el = card.find(["h2", "h3", "a"])
        title = title_el.get_text(strip=True) if title_el else "Yeni Haber"
        
        link_el = card.find("a")
        link = "https://www.wowhead.com" + link_el["href"] if link_el and link_el.get("href") else NEWS_URL
        
        desc_el = card.find(["p", "div", "span"], class_=["description", "body", "news-list-card-content"])
        snippet = desc_el.get_text(strip=True) if desc_el else ""

    print(f"Bulunan en son başlık: {title}")
    
    last_saved_title = get_last_title()
    print(f"Kayıtlı önceki başlık: {last_saved_title}")

    # TEST MODU: Doğrudan mesaj atsın (yeni haber kontrolü yapmadan)
    print("Discord'a mesaj iletiliyor...")
    msg = f"⚔️ **[WoW Forever] {title}**\n\n{snippet}\n\n🔗 *{link}*"
    send_to_discord(msg)
    
    # Başlığı kaydet
    set_last_title(title)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Çalışma sırasında hata: {e}")
