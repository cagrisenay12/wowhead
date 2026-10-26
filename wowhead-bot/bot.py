import time
import os
import feedparser
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1564335678458957874/k-T8sQPIgKuxCfqYETULyuE3NdSVDNqaTnyaXYH-PXt2DBa7xKXIRMZdak_VHfBTzyy9")
RSS_URL = "https://www.wowhead.com/forever/news/rss"
LAST_ENTRY_FILE = "last_forever_id.txt"

def get_last_entry_id():
    if os.path.exists(LAST_ENTRY_FILE):
        with open(LAST_ENTRY_FILE, "r") as f:
            return f.read().strip()
    return None

def set_last_entry_id(entry_id):
    with open(LAST_ENTRY_FILE, "w") as f:
        f.write(entry_id)

def send_to_discord(content):
    # Discord tek mesajda 2000 karakter alabildiği için 1900'lük parçalara bölüyoruz
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        if chunk.strip():
            payload = {"content": chunk}
            requests.post(WEBHOOK_URL, json=payload)
            time.sleep(1)

def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # Resim ve reklam gibi gereksiz etiketleri kaldır
    for tag in soup(["script", "style", "noscript", "img"]):
        tag.decompose()
    # Listeleri ve paragrafları düzenli metne çevir
    return soup.get_text(separator="\n", strip=True)

def check_feed():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("RSS beslemesinde içerik bulunamadı.")
        return

    latest_entry = feed.entries[0]
    last_id = get_last_entry_id()

    # Yeni bir içerik varsa veya ilk çalıştırmaysa
    if latest_entry.id != last_id:
        title = latest_entry.title
        link = latest_entry.link
        print(f"Yeni WoW Forever haberi bulundu: {title}")

        # Haberin detayını doğrudan RSS verisinden çekiyoruz:
        raw_content = ""
        if "content" in latest_entry:
            raw_content = latest_entry.content[0].value
        elif "summary" in latest_entry:
            raw_content = latest_entry.summary
        elif "description" in latest_entry:
            raw_content = latest_entry.description

        body_text = clean_html(raw_content)

        # Discord mesajını oluştur
        full_text = f"⚔️ **[WoW Forever] {title}**\n\n{body_text}\n\n🔗 *Kaynak: {link}*"

        send_to_discord(full_text)
        set_last_entry_id(latest_entry.id)
    else:
        print("Yeni bir haber yok, son haber zaten gönderilmiş.")

if __name__ == "__main__":
    try:
        check_feed()
    except Exception as e:
        print(f"Hata oluştu: {e}")
