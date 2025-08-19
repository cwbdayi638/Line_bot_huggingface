# cwa_service.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import requests
import re
import pandas as pd
from datetime import datetime, timedelta, timezone
from config import CWA_API_KEY, CWA_ALARM_API, CWA_SIGNIFICANT_API

TAIPEI_TZ = timezone(timedelta(hours=8))

# --- Helper Functions ---
def _to_float(x):
    if x is None: return None
    s = str(x).strip()
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None

def _parse_cwa_time(s: str) -> tuple[str, str]:
    if not s: return ("未知", "未知")
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        tw = dt.astimezone(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M")
        utc = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        return (tw, utc)
    except Exception:
        return (s, "未知")

# --- 地震預警 (CWA_ALARM_API) ---
def fetch_cwa_alarm_list(limit: int = 5) -> str:
    """抓 CWA 地震預警並格式化輸出。"""
    try:
        r = requests.get(CWA_ALARM_API, timeout=10)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        return f"❌ 地震預警查詢失敗：{e}"

    items = payload.get("data", [])
    if not items:
        return "✅ 目前沒有地震預警。"

    def _key(it):
        try:
            return datetime.fromisoformat(it.get("originTime", "").replace("Z", "+00:00"))
        except:
            return datetime.min.replace(tzinfo=timezone.utc)
    
    items = sorted(items, key=_key, reverse=True)
    lines = ["🚨 地震預警（最新）:", "-" * 20]
    for it in items[:limit]:
        mag = _to_float(it.get("magnitudeValue"))
        depth = _to_float(it.get("depth"))
        tw_str, _ = _parse_cwa_time(it.get("originTime", ""))
        identifier = str(it.get('identifier', '—')).replace('{', '{{').replace('}', '}}')
        msg_type = str(it.get('msgType', '—')).replace('{', '{{').replace('}', '}}')
        msg_no = str(it.get('msgNo', '—')).replace('{', '{{').replace('}', '}}')
        areas = str(it.get('alertAreas') or '—').replace('{', '{{').replace('}', '}}')
        mag_str = f"{mag:.1f}" if mag is not None else "—"
        depth_str = f"{depth:.0f}" if depth is not None else "—"
        lines.append(
            f"事件: {identifier} | 類型: {msg_type}#{msg_no}\n"
            f"規模/深度: M{mag_str} / {depth_str} km\n"
            f"時間: {tw_str}（台灣）\n"
            f"預警地區: {areas}"
        )
    return "\n\n".join(lines).strip()

# --- 顯著有感地震 (E-A0015-001) ---
def _parse_significant_earthquakes(obj: dict) -> pd.DataFrame:
    records = obj.get("records") or obj.get("Records") or {}
    quakes = records.get("earthquake") or records.get("Earthquake") or []
    rows = []
    for q in quakes:
        ei = q.get("EarthquakeInfo") or q.get("earthquakeInfo") or {}
        epic = ei.get("Epicenter") or ei.get("epicenter") or {}
        mag_info = ei.get("Magnitude") or ei.get("magnitude") or ei.get("EarthquakeMagnitude") or {}
        depth_raw = ei.get("FocalDepth") or ei.get("depth") or ei.get("Depth")
        mag_raw = mag_info.get("MagnitudeValue") or mag_info.get("magnitudeValue") or mag_info.get("Value") or mag_info.get("value")
        rows.append({
            "ID": q.get("EarthquakeNo"), "Time": ei.get("OriginTime"),
            "Lat": _to_float(epic.get("EpicenterLatitude") or epic.get("epicenterLatitude")),
            "Lon": _to_float(epic.get("EpicenterLongitude") or epic.get("epicenterLongitude")),
            "Depth": _to_float(depth_raw), "Magnitude": _to_float(mag_raw),
            "Location": epic.get("Location") or epic.get("location"),
            "URL": q.get("Web") or q.get("ReportURL"),
        })
    df = pd.DataFrame(rows)
    if not df.empty and "Time" in df.columns:
        time_series = pd.to_datetime(df["Time"], errors="coerce")
        if pd.api.types.is_datetime64_any_dtype(time_series):
            df["Time"] = time_series.dt.tz_localize("UTC").dt.tz_convert(TAIPEI_TZ)
    return df

def fetch_significant_earthquakes(days: int = 7, limit: int = 5) -> str:
    if not CWA_API_KEY: return "❌ 顯著地震查詢失敗：管理者尚未設定 CWA_API_KEY。"
    now = datetime.now(timezone.utc)
    time_from = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {"Authorization": CWA_API_KEY, "format": "JSON", "timeFrom": time_from}
    try:
        r = requests.get(CWA_SIGNIFICANT_API, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = _parse_significant_earthquakes(data)
        if df.empty: return f"✅ 過去 {days} 天內沒有顯著有感地震報告。"
        df = df.sort_values(by="Time", ascending=False).head(limit)
        lines = [f"🚨 CWA 最新顯著有感地震 (近{days}天內):", "-" * 20]
        for _, row in df.iterrows():
            mag_str = f"{row['Magnitude']:.1f}" if pd.notna(row['Magnitude']) else "—"
            depth_str = f"{row['Depth']:.0f}" if pd.notna(row['Depth']) else "—"
            lines.append(
                f"時間: {row['Time'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['Time']) else '—'}\n"
                f"地點: {row['Location'] or '—'}\n"
                f"規模: M{mag_str} | 深度: {depth_str} km\n"
                f"報告: {row['URL'] or '無'}"
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"❌ 顯著地震查詢失敗：{e}"

# --- 最新一筆顯著地震 ---
def fetch_latest_significant_earthquake() -> dict | None:
    """從 CWA 獲取最新一筆顯著地震，並重用現有的解析邏輯"""
    if not CWA_API_KEY:
        raise ValueError("錯誤：尚未設定 CWA_API_KEY Secret。")
    
    now = datetime.now(timezone.utc)
    time_from = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
    params = {"Authorization": CWA_API_KEY, "format": "JSON", "limit": 1}
    
    r = requests.get(CWA_SIGNIFICANT_API, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    df = _parse_significant_earthquakes(data)
    if df.empty:
        return None

    latest_eq_data = df.sort_values(by="Time", ascending=False).iloc[0].to_dict()
    
    quakes = data.get("records", {}).get("Earthquake", [])
    if quakes:
        latest_eq_data["ImageURL"] = quakes[0].get("ReportImageURI")

    if pd.notna(latest_eq_data.get("Time")):
        latest_eq_data["TimeStr"] = latest_eq_data["Time"].strftime('%Y-%m-%d %H:%M')

    return latest_eq_data
