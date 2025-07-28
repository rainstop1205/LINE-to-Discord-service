from flask import Flask, request
import requests
import json
import os
from user_whitelist import user_prefix_whitelist
from logger import logger

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
MAX_DISCORD_FILESIZE = 8 * 1024 * 1024  # 8MB
user_cache = {}

# 檢查環境變數
if not DISCORD_WEBHOOK_URL or not LINE_CHANNEL_ACCESS_TOKEN:
    raise RuntimeError("Missing required environment variables: DISCORD_WEBHOOK_URL or LINE_CHANNEL_ACCESS_TOKEN")

def get_line_auth_headers():
    return {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}

def post_to_discord(payload=None, files=None):
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload if not files else None, data=payload if files else None, files=files, timeout=10)
        if response.status_code not in [200, 204]:
            logger.error(f"⚠️ Discord post failed: {response.status_code} - {response.text}")
            return False
        return True
    except Exception as e:
        logger.exception(f"⚠️ Discord post exception: {e}")
        return False

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
    try:
        resp = requests.get(f"https://api.line.me/v2/bot/profile/{user_id}", headers=get_line_auth_headers(), timeout=10)
        if resp.status_code == 200:
            profile = resp.json()
            display_name = profile.get("displayName") or f"(unknown user {prefix})"
            user_cache[user_id] = display_name
            return display_name
        else:
            logger.warning(f"⚠️ Failed to get displayName for {user_id}: {resp.status_code}")
    except Exception as e:
        logger.exception(f"⚠️ Exception getting displayName for {user_id}: {e}")

    # 只顯示id前六碼
    return f"(user {prefix})"

def download_line_content(message_id):
    try:
        resp = requests.get(f"https://api-data.line.me/v2/bot/message/{message_id}/content", headers=get_line_auth_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.content
        else:
            logger.error(f"⚠️ Failed to download content: {resp.status_code}")
    except Exception as e:
        logger.error(f"⚠️ Exception downloading content: {e}")
    return None

def handle_text(user_id, text):
    display_name = get_user_display_name(user_id)
    post_to_discord({"content": f"👤 {display_name}：{text}"})

def handle_sticker(user_id, sticker_id):
    display_name = get_user_display_name(user_id)
    image_url = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{sticker_id}/ANDROID/sticker.png"
    payload = {
        "content": f"👤 {display_name}：貼圖🧸",
        "embeds": [{"image": {"url": image_url}}]
    }
    post_to_discord(payload)

def handle_media(user_id, message_id, media_type="image"):
    content = download_line_content(message_id)
    if not content:
        return

    type_text = {
        "image": "圖片🖼️",
        "video": "影片🎥"
    }.get(media_type, media_type)

    display_name = get_user_display_name(user_id)
    if len(content) > MAX_DISCORD_FILESIZE:
        post_to_discord({"content": f"👤 {display_name}：{type_text}檔案太大啦~ (超過限制)"})
        return

    file_ext = "jpg" if media_type == "image" else "mp4"
    files = {"file": (f"{media_type}.{file_ext}", content)}
    payload = {"content": f"👤 {display_name}：{type_text}"}
    post_to_discord(payload, files)

@app.route("/", methods=["GET"])
def health():
    return "Hello, LINE Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        source = event.get("source", {})
        source_type = source.get("type")
        # 👇抓 group/room/user 對應的 ID
        if source_type == "group":
            logger.info(f"🟢 收到來自group的訊息，groupId：{source.get('groupId')}")
        elif source_type == "room":
            logger.info(f"🟣 收到來自room的訊息，roomId：{source.get('roomId')}")
        elif source_type == "user":
            logger.info(f"🔵 收到來自user的訊息，userId：{source.get('userId')}")
        
        if event.get("type") != "message":
            continue
        msg = event["message"]
        user_id = event.get("source", {}).get("userId", "(unknown)")

        match msg.get("type"):
            case "text":
                handle_text(user_id, msg.get("text", ""))
            case "sticker":
                handle_sticker(user_id, msg.get("stickerId"))
            case "image":
                handle_media(user_id, msg.get("id"), "image")
            case "video":
                handle_media(user_id, msg.get("id"), "video")
            case _:
                logger.debug(f"🪧 Unsupported message type: {msg.get('type')}")
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)