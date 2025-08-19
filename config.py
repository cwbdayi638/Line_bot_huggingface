# config.py
import os
import tempfile
from datetime import datetime

# --- 環境設定 ---
HF_HOME_DIR = "/tmp/huggingface"
os.environ["HF_HOME"] = HF_HOME_DIR
os.makedirs(HF_HOME_DIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

# --- LINE Bot 憑證 ---
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

# --- Hugging Face Space URL ---
HF_SPACE_URL = os.getenv("SPACEURL")
if not HF_SPACE_URL:
    sid = os.getenv("SPACE_ID")
    if sid and "/" in sid:
        author, name = sid.split("/", 1)
        HF_SPACE_URL = f"https://{author.replace('_', '-')}-{name.replace('_', '-')}.hf.space"
    else:
        HF_SPACE_URL = ""

# --- 靜態檔案目錄 ---
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(tempfile.gettempdir(), "static"))
os.makedirs(STATIC_DIR, exist_ok=True)

# --- API 端點與金鑰 ---
CWA_API_KEY = os.getenv("CWA_API_KEY")
CWA_ALARM_API = "https://app-2.cwa.gov.tw/api/v1/earthquake/alarm/list"
CWA_SIGNIFICANT_API = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001"
USGS_API_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# --- AI 模型設定 ---
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "google/flan-t5-small")
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "120"))
LLM_TOP_K = int(os.getenv("LLM_TOP_K", "50"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# --- 顯示用當年年份 ---
CURRENT_YEAR = datetime.now().year
