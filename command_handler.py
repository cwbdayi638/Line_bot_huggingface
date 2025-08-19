# command_handler.py
import pandas as pd
from linebot.v3.messaging import TextMessage, ImageMessage

# 匯入服務函式
from cwa_service import fetch_cwa_alarm_list, fetch_significant_earthquakes, fetch_latest_significant_earthquake
from usgs_service import fetch_global_last24h_text, fetch_taiwan_df_this_year
from plotting_service import create_and_save_map
from ai_service import generate_ai_text
from config import CURRENT_YEAR, HF_SPACE_URL

def get_help_message() -> TextMessage:
    """回傳包含所有可用指令的說明訊息。"""
    text = (
        "📖 指令列表 (輸入 #數字 即可)\n\n"
        "【地震資訊】\n"
        "• #1 - 最新一筆顯著地震 (含圖)\n"
        "• #2 - 全球近24小時顯著地震（USGS)\n"
        "• #3 - 今年台灣顯著地震列表（USGS)\n"
        "• #4 - CWA 地震目錄查詢 (外部連結)\n"
        "• #5 - CWA 最新地震預警\n"
        "• #6 - CWA 最近7天顯著有感地震\n\n"
        "【AI 與工具】\n"
        "• #7 <問題> - 與 AI 助理對話\n\n"
        "【基本指令】\n"
        "• #8 - 關於此機器人\n"
        "• #9 - 顯示此說明"
    )
    return TextMessage(text=text)

def get_info_message() -> TextMessage:
    """回傳機器人資訊。"""
    text = (
        "🤖 關於我\n\n"
        "我是一個多功能助理機器人，提供地震查詢與 AI 對話功能。\n\n"
        "• 版本: 4.1\n"
        "• 資料來源: CWA, USGS, Hugging Face\n"
        "• 開發者: dayichen"
    )
    return TextMessage(text=text)

def get_taiwan_earthquake_list() -> TextMessage:
    """回傳近期的台灣地震文字列表。"""
    result = fetch_taiwan_df_this_year()
    if isinstance(result, pd.DataFrame):
        count = len(result)
        lines = [f"🇹🇼 今年 ({CURRENT_YEAR} 年) 台灣區域顯著地震 (M≥5.0)，共 {count} 筆:", "-" * 20]
        for _, row in result.head(15).iterrows():
            t = row["time_utc"].strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"規模: {row['magnitude']:.1f} | 日期時間: {t} (UTC)\n"
                f"地點: {row['place']}\n"
                f"報告連結: {row.get('url', '無')}"
            )
        if count > 15:
            lines.append(f"... (還有 {count} 筆資料)")
        reply_text = "\n\n".join(lines)
    else:
        reply_text = result
    return TextMessage(text=reply_text)

def get_latest_earthquake_reply() -> list:
    """獲取最新地震資訊並組合成 LINE 訊息"""
    try:
        latest_eq = fetch_latest_significant_earthquake()
        if not latest_eq:
            return [TextMessage(text="✅ 近期無顯著有感地震報告。")]

        mag_str = f"{latest_eq['Magnitude']:.1f}" if latest_eq.get('Magnitude') is not None else "—"
        depth_str = f"{latest_eq['Depth']:.0f}" if latest_eq.get('Depth') is not None else "—"
        
        text_message_content = (
            f"🚨 CWA 最新顯著有感地震\n"
            f"----------------------------------\n"
            f"時間: {latest_eq.get('TimeStr', '—')}\n"
            f"地點: {latest_eq.get('Location', '—')}\n"
            f"規模: M{mag_str} | 深度: {depth_str} km\n"
            f"報告: {latest_eq.get('URL', '無')}"
        )
        reply_messages = [TextMessage(text=text_message_content)]

        if latest_eq.get("ImageURL"):
            image_url = latest_eq["ImageURL"]
            reply_messages.append(
                ImageMessage(original_content_url=image_url, preview_image_url=image_url)
            )
        
        return reply_messages
    except Exception as e:
        return [TextMessage(text=f"❌ 查詢最新地震失敗：{e}")]

def process_message(user_message_raw: str, request_base_url: str) -> list:
    """處理使用者的文字訊息並回傳一個包含回覆訊息的列表。"""
    user_message = (user_message_raw or "").strip()
    
    # --- 指令對應 ---
    cmd_map = {
        '#1': '/latest', '#2': '/global', '#3': '/taiwan',
        '#4': '/map', '#5': '/alert', '#6': '/significant',
        '#7': '/ai', '#8': '/info', '#9': '/help',
        '地震': '/global', 'quake': '/global',
        '台灣地震': '/taiwan', '臺灣地震': '/taiwan',
        '台灣地震畫圖': '/map', '臺灣地震畫圖': '/map',
        '地震預警': '/alert',
        '/help': '/help'
    }

    command = ""
    arg = ""
    
    if user_message.startswith('#') and len(user_message) > 1:
        parts = user_message.split(' ', 1)
        key = parts[0]
        if key in cmd_map:
            command = cmd_map[key]
            arg = parts[1] if len(parts) > 1 else ""
    
    elif user_message.startswith('/'):
        parts = user_message.split(' ', 1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
    else:
        for key, value in cmd_map.items():
            if user_message.lower() == key:
                command = value
                break

    # --- 指令處理 ---
    if command:
        if command == '/help' or command == '/info':
            return [get_info_message()] if command == '/info' else [get_help_message()]
        elif command == '/latest':
            return get_latest_earthquake_reply()
        elif command == '/global':
            return [TextMessage(text=fetch_global_last24h_text())]
        elif command == '/taiwan':
            return [get_taiwan_earthquake_list()]
        elif command == '/map':
            reply_text = (
                "🗺️ 外部地震查詢服務\n\n"
                "此服務提供中央氣象署地震目錄資料供查詢。\n\n"
                "請點擊以下連結進行查詢：\n"
                "https://huggingface.co/spaces/cwadayi/MCP-2"
            )
            return [TextMessage(text=reply_text)]
        elif command == '/alert':
            return [TextMessage(text=fetch_cwa_alarm_list(limit=5))]
        elif command == '/significant':
            return [TextMessage(text=fetch_significant_earthquakes(limit=5))]
        elif command == '/ai':
            prompt = arg or user_message[2:].lstrip()
            if not prompt:
                return [TextMessage(text="請輸入問題，例如：#7 台灣最高的山是哪座？")]
            return [TextMessage(text=generate_ai_text(prompt))]

    # 若非任何指令，則預設交給 AI 處理
    return [TextMessage(text=generate_ai_text(user_message))]
