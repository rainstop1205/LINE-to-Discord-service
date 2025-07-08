from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# 從環境變數抓設定
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

@app.route("/", methods=["GET"])
def hello():
    return "Hello, LINE Bot is running on Cloud Run!"

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message":
            msg = event["message"]
            user_id = event["source"].get("userId", "unknown")
            display_name = get_user_display_name(user_id)

            if msg["type"] == "text":
                text = msg["text"]
                send_to_discord(f"👤 {display_name}：{text}")

            elif msg["type"] == "image":
                message_id = msg["id"]
                image_content = download_line_image(message_id)
                if image_content:
                    upload_image_to_discord(image_content, filename="line_image.jpg", display_name=display_name)

            elif msg["type"] == "sticker":
                sticker_id = msg.get("stickerId")
                if sticker_id:
                    send_sticker_to_discord(sticker_id, display_name)
    return "OK"

# 快取 userId ➜ displayName
user_cache = {}
def get_user_display_name(user_id):
    if user_id in user_cache:
        return user_cache[user_id]

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        profile = resp.json()
        display_name = profile.get("displayName") or f"(unknown user {user_id[:6]})"
        user_cache[user_id] = display_name
        return display_name
    else:
        print(f"⚠️ Failed to get displayName for {user_id}: {resp.status_code}")
        return f"(user {user_id[:6]})"

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set")
        return

    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
    if response.status_code != 204:
        print(f"⚠️ Discord text post failed: {response.status_code}")

def download_line_image(message_id):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"⚠️ Failed to download image: {response.status_code}")
        return None

MAX_DISCORD_FILESIZE = 8 * 1024 * 1024  # 8MB
def upload_image_to_discord(image_data, filename="image.jpg", display_name="unknown"):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set")
        return

    if len(image_data) > MAX_DISCORD_FILESIZE:
        content = f"🖼️ **{display_name}** 傳的圖片太大啦~ (超過 8MB 限制)"
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        if response.status_code != 204:
            print(f"⚠️ Discord text post failed: {response.status_code}")
        return

    files = {
        "file": (filename, image_data)
    }
    payload = {
        "content": f"🖼️ **{display_name}** 傳了一張圖片"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
    if response.status_code not in [200, 204]:
        print(f"⚠️ Discord image upload failed: {response.status_code}")

def send_sticker_to_discord(sticker_id, display_name="unknown"):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set")
        return

    image_url = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/ANDROID/sticker.png"
    payload = {
        "content": f"🧸 **{display_name}** 傳了一張貼圖",
        "embeds": [
            {
                "image": {"url": image_url}
            }
        ]
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code not in [200, 204]:
        print(f"⚠️ Discord sticker embed failed: {response.status_code}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)