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
            if msg["type"] == "text":
                user_id = event["source"].get("userId", "unknown")
                text = msg["text"]
                send_to_discord(f"👤 `{user_id}`：{text}")
    return "OK"

def send_to_discord(content):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
    else:
        print("⚠️ DISCORD_WEBHOOK_URL not set")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)