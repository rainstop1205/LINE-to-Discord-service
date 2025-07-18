from flask import Flask, request
import requests
import json
import os
from user_whitelist import user_prefix_whitelist

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
        # source = event.get("source", {})
        # source_type = source.get("type")
        # # 👇抓 group/user 及對應的 ID
        # if source_type == "group":
        #     print(f"🟢 收到來自群組的訊息，groupId：{source.get('groupId')}", flush=True)
        # elif source_type == "room":
        #     print(f"🟣 收到來自多人聊天室的訊息，roomId：{source.get('roomId')}", flush=True)
        # elif source_type == "user":
        #     print(f"🔵 收到來自單一使用者的訊息，userId：{source.get('userId')}", flush=True)
            
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

            elif msg["type"] == "video":
                message_id = msg["id"]
                video_content = download_line_video(message_id)
                if video_content:
                    upload_video_to_discord(video_content, filename="video.mp4", display_name=display_name)

    return "OK"

# 快取 userId ➜ displayName
user_cache = {}
def get_user_display_name(user_id):
    if user_id in user_cache:
        return user_cache[user_id]

    prefix = user_id[:6]

    # 檢查白名單
    if prefix in user_prefix_whitelist:
        display_name = user_prefix_whitelist[prefix]
        user_cache[user_id] = display_name
        return display_name

    # call LINE API 取得 displayName
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        profile = resp.json()
        display_name = profile.get("displayName") or f"(unknown user {prefix})"
        user_cache[user_id] = display_name
        return display_name

    # 只顯示id前六碼
    print(f"⚠️ Failed to get displayName for {user_id}: {resp.status_code}", flush=True)
    return f"(user {prefix})"

def send_to_discord(content):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set", flush=True)
        return

    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
    if response.status_code != 204:
        print(f"⚠️ Discord text post failed: {response.status_code}", flush=True)

def download_line_image(message_id):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"⚠️ Failed to download image: {response.status_code}", flush=True)
        return None

MAX_DISCORD_FILESIZE = 8 * 1024 * 1024  # 8MB
def upload_image_to_discord(image_data, filename="image.jpg", display_name="unknown"):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set", flush=True)
        return

    if len(image_data) > MAX_DISCORD_FILESIZE:
        content = f"👤 {display_name}：圖片🖼️太大啦~ (超過 8MB 限制)"
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        if response.status_code != 204:
            print(f"⚠️ Discord text post failed: {response.status_code}", flush=True)
        return

    files = {
        "file": (filename, image_data)
    }
    payload = {
        "content": f"👤 {display_name}：圖片🖼️"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
    if response.status_code not in [200, 204]:
        print(f"⚠️ Discord image upload failed: {response.status_code}", flush=True)

def send_sticker_to_discord(sticker_id, display_name="unknown"):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set", flush=True)
        return

    image_url = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/ANDROID/sticker.png"
    payload = {
        "content": f"👤 {display_name}：貼圖🧸",
        "embeds": [
            {
                "image": {"url": image_url}
            }
        ]
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code not in [200, 204]:
        print(f"⚠️ Discord sticker embed failed: {response.status_code}", flush=True)

def download_line_video(message_id):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"⚠️ Failed to download video: {response.status_code}", flush=True)
        return None

def upload_video_to_discord(video_data, filename="video.mp4", display_name="unknown"):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL not set", flush=True)
        return

    if len(video_data) > MAX_DISCORD_FILESIZE:
        content = f"👤 {display_name}：影片🎥太大啦~ (超過 8MB 限制)"
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        if response.status_code not in [200, 204]:
            print(f"⚠️ Discord video notice failed: {response.status_code}", flush=True)
        return

    files = {
        "file": (filename, video_data)
    }
    payload = {
        "content": f"👤 {display_name}：影片🎥"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
    if response.status_code not in [200, 204]:
        print(f"⚠️ Discord video upload failed: {response.status_code}", flush=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)