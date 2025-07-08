from flask import Flask, request
import requests
import json

app = Flask(__name__)

DISCORD_WEBHOOK_URL = "你的 Discord Webhook URL"
LINE_CHANNEL_ACCESS_TOKEN = "你的 LINE Channel Access Token"

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
                post_to_discord(f"[{user_id}]：{text}")
    return "OK"

def post_to_discord(content):
    data = {"content": content}
    requests.post(DISCORD_WEBHOOK_URL, data=data)

@app.route("/", methods=["GET"])
def hello():
    return "Hello, LINE Bot 👋"

if __name__ == "__main__":
    app.run(debug=True)
