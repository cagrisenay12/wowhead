import os
import time
import feedparser
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1564335678458957874/k-T8sQPIgKuxCfqYETULyuE3NdSVDNqaTnyaXYH-PXt2DBa7xKXIRMZdak_VHfBTzyy9")
RSS_URL = "https://www.wowhead.com/news/rss/all"
LAST_ENTRY_FILE = "last_forever_id.txt"

def get_last_id():
    if os.path.exists(LAST_ENTRY_FILE):
        with open(LAST_ENTRY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def set_last_id(entry_id):
    with open(LAST_ENTRY_FILE, "w", encoding="utf-8") as f:
        f.write(entry_id)

def send_to_discord(content):
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        if chunk.strip():
            payload = {"content": chunk}
            res = requests.post(WEBHOOK_URL, json=payload)
            print(f"Discord gönderim yanıtı: {res.status_code}")
            time.sleep(1)

def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "img", "aside"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def is_forever_news(entry):
    title = entry.get("title", "").lower()
    link = entry.get("link", "").lower()
    summary = entry.get("summary", "").lower()
    tags = [t.get("term", "").lower() for t in entry.get("tags", [])]

    # Forever kelimesi başlıkta, linkte veya etiketlerde geçiyor mu?
    if "forever" in title or "forever" in link or any("forever" in t for t in tags):
        return True
    return False

def run():
    print("RSS akışı alınıyor...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("RSS beslemesinden içerik alınamadı!")
        return

    print(f"Toplam {len(feed.entries)} adet haber tarandı. WoW Forever haberleri aranıyor...")
    
    # Haberler arasından sadece WoW Forever olanları filtrele
    forever_entries = [entry for entry in feed.entries if is_forever_news(entry)]
    
    if not forever_entries:
        print("Akışta henüz WoW Forever kategorisine ait haber bulunamadı.")
        return

    latest_entry = forever_entries[0]
    title = latest_entry.title
    link = latest_entry.link
    entry_id = latest_entry.id

    print(f"Bulunan en son WoW Forever haberi: {title}")
    
    last_id = get_last_id()
    
    # İçeriği RSS'ten temiz metin olarak al
    raw_content = ""
    if "content" in latest_entry:
        raw_content = latest_entry.content[0].value
    elif "summary" in latest_entry:
        raw_content = latest_entry.summary
    elif "description" in latest_entry:
        raw_content = latest_entry.description

    body_text = clean_html(raw_content)

    full_message = f"⚔️ **[WoW Forever] {title}**\n\n{body_text}\n\n🔗 *Kaynak: {link}*"
    
    # Discord'a gönder
    print("Discord'a iletiliyor...")
    send_to_discord(full_message)
    set_last_id(entry_id)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Hata: {e}")
