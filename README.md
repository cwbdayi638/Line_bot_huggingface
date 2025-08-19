---
title: LINE Earthquake Bot
sdk: docker
app_port: 7860
---

# LINE 地震查詢機器人

這是一個部署在 Hugging Face Spaces 上的 LINE Bot 後端服務，旨在提供即時的地震資訊查詢，並整合了 AI 對話功能。

## 如何使用
這是一個 LINE Bot 的後端服務。您需要將此機器人加為好友，然後在 LINE 聊天室中與它互動。

## 主要功能與指令
您可以透過在聊天室中輸入以下指令來使用機器人的功能：

* `地震` 或 `quake`
    * 查詢過去 24 小時全球的顯著地震。
* `臺灣地震` 或 `台灣地震`
    * 以列表形式顯示今年以來台灣地區的顯著地震。
* `臺灣地震畫圖` 或 `台灣地震畫圖`
    * 將今年以來台灣地區的顯著地震繪製成地圖並回傳。
* `地震預警`
    * 獲取台灣中央氣象署 (CWA) 最新的地震預警。
* `ai <你的問題>`
    * 與 AI 助理進行對話 (例如：`ai 台北今天天氣如何？`)。
* `/help`
    * 顯示所有可用的指令列表。

## 技術棧
* **後端**: Python, Flask, Gunicorn
* **LINE 整合**: `line-bot-sdk-python`
* **AI 模型**: Hugging Face `transformers` (`bigscience/bloomz-560m`)
* **部署**: Docker on Hugging Face Spaces
