# 🌈 LINE to Discord Relay Bot

by 魷魚

用 Python + Flask + Google Cloud Run 架設的超簡易訊息同步工具

📱 LINE 群組訊息 ➜ ⛓️ 轉送到 Discord 頻道！支援文字、圖片、貼圖、影片！（支援中）

---

## 🚀 功能介紹

- 接收 LINE 群組中的訊息（文字、圖片）
- 自動上傳到指定 Discord 頻道
- 顯示送出者的暱稱（不是 userId）
- 完全 serverless：用 Google Cloud Run 永久免費跑起來
- 使用環境變數管理 token，安全又彈性

---

## 📦 專案架構
 ```
├── app.py # 主程式：處理 LINE webhook 並轉發至 Discord
├── requirements.txt # 相依套件（Flask, requests）
├── Dockerfile # 打包部署用
├── cloudbuild.yaml # GCP Cloud Build 自動部署設定檔
└── README.md # 你現在看的這個檔
 ```

---

## ☁️ 部署方式（使用 Google Cloud Run）

### 📋 前置準備

1. 已安裝並登入好 `gcloud CLI`
2. 有 GCP 專案、啟用 Cloud Run
3. 有安裝 Docker（想在本機 build 的話）
4. 有 LINE Messaging API 的 Channel（取得 Access Token、Channel Secret）
5. 建好 Discord Webhook 並複製網址

### 🛠️ 建立 `.env` 檔（或在 Cloud Run 設定）

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
LINE_CHANNEL_ACCESS_TOKEN=你的LINE存取權杖
```

### 🔗 設定 LINE Webhook
到 LINE Developers 控制台，把 Webhook URL 設成你 Cloud Run 的外部網址，例如：
```
https://line-discord-bot-xxxxx.a.run.app/callback
```

### 💬 使用說明
把機器人加入想要同步訊息的 LINE 群組

傳送訊息(含emoji)/圖片/影片 ➜ Discord 頻道同步更新！


### 🛠️ TODO
- ✅ 文字訊息同步
- ✅ 圖片同步
- ✅ 顯示 LINE 暱稱
- ✅ 支援貼圖同步
- ✅ 支援影片(<8MB)
- [ ] LINE ➜ 多個 Discord 頻道自動分類