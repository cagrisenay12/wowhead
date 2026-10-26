import os
import time
import feedparser
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1564335678458957874/k-T8sQPIgKuxCfqYETULyuE3NdSVDNqaTnyaXYH-PXt2DBa7xKXIRMZdak_VHfBTzyy9")
RSS_URL = "https://www.wowhead.com/news/rss/all"
LAST_ENTRY_FILE = "last_forever_id.txt"

def get_last_entry_id():
    if os.path.exists(LAST_ENTRY_FILE):
        with open(LAST_ENTRY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def set_last_entry_id(entry_id):
    with open(LAST_ENTRY_FILE, "w", encoding="utf-8") as f:
        f.write(entry_id)

def send_to_discord(content):
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        if chunk.strip():
            payload = {"content": chunk}
            res = requests.post(WEBHOOK_URL, json=payload)
            print(f"Discord gönderim durumu: {res.status_code}")
            time.sleep(1)

def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript", "img"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def is_forever_news(entry):
    title = entry.get("title", "").lower()
    if "forever" in title:
        return True
    
    link = entry.get("link", "").lower()
    if "/forever" in link:
        return True

    if "tags" in entry:
        for t in entry.tags:
            term = t.get("term", "").lower()
            if "forever" in term:
                return True
                
    return False

def run():
    print("Wowhead RSS akışı çekiliyor...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("RSS beslemesi boş veya alınamadı.")
        return

    print(f"Toplam {len(feed.entries)} haber inceleniyor...")

    target_entry = None
    for entry in feed.entries:
        if is_forever_news(entry):
            target_entry = entry
            break

    if not target_entry:
        print("Akışta henüz WoW Forever ile ilgili bir haber bulunamadı.")
        return

    title = target_entry.title
    link = target_entry.link
    entry_id = target_entry.id
    last_id = get_last_entry_id()

    print(f"Bulunan en son WoW Forever haberi: {title}")

    # Sadece yeni bir haber geldiğinde çalışır:
    if entry_id != last_id:
        print("Yeni haber bulundu, Discord'a gönderiliyor...")
        
        raw_content = ""
        if "content" in target_entry:
            raw_content = target_entry.content[0].value
        elif "summary" in target_entry:
            raw_content = target_entry.summary

        body_text = clean_html(raw_content)

        msg = f"⚔️ **[WoW Forever] {title}**\n\n{body_text}\n\n🔗 *Kaynak: {link}*"
        send_to_discord(msg)
        set_last_entry_id(entry_id)
    else:
        print("Yeni haber yok. Bu haber zaten daha önce Discord'a iletilmiş.")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Hata: {e}")
