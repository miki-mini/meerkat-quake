import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import requests
from fastapi import FastAPI
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# ==========================================
# Configuration
# ==========================================

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
TARGET_USER_ID = os.getenv("TARGET_USER_ID")

# P2P地震情報API (これは公開情報なのでそのままでOK)
P2P_API_URL = "https://api.p2pquake.net/v2/history?codes=551&limit=1"




# ==========================================
# Health Check Endpoint
# ==========================================
@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "Meerkat Bot is running 🦦"}


# ==========================================
# Earthquake Check Endpoint
# ==========================================
@app.get("/check_quake")
def check_earthquake() -> Dict[str, Any]:
    logger.info("🦦 Starting earthquake patrol...")

    try:
        # 1. Fetch data from API
        headers = {"User-Agent": "MeerkatBot/1.0"}

        logger.info(f"Accessing: {P2P_API_URL}")
        response = requests.get(P2P_API_URL, headers=headers)

        # Log response status and partial content for debugging
        logger.info(f"Status Code: {response.status_code}")
        logger.debug(f"Response Content: {response.text[:500]}")

        # エラーがあればここで止まる
        response.raise_for_status()

        data = response.json()

        # ... (以下同じ) ...

        if not data:
            return {"status": "No data"}

        latest_quake = data[0]

        # 2. Check timestamp
        time_str = latest_quake["earthquake"]["time"]

        # Define JST timezone
        JST = timezone(timedelta(hours=9))

        # Parse API timestamp as JST
        quake_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=JST)

        # Get current time in JST
        now = datetime.now(JST)

        # Check if the quake is recent (within last 5 minutes)
        if now - quake_time > timedelta(minutes=5):
            return {"status": "No recent earthquake", "time": time_str}

        # --- ここから下は「地震だ！」と判定された時だけ動く ---

        # 3. Create message
        max_scale = latest_quake["earthquake"]["maxScale"]

        # Filter: Ignore earthquakes with seismic intensity less than 3
        # API spec: 10=Scale 1, 20=Scale 2, 30=Scale 3 ...
        if max_scale < 30:
            logger.info(f"Skipping small quake: Scale score {max_scale}")
            return {"status": "Small quake", "detail": "Skipped notification (Scale < 3)"}
        # ==========================================

        # 数字を読みやすい文字に変換
        scale_map = {
            10: "震度1",
            20: "震度2",
            30: "震度3",
            40: "震度4",
            45: "震度5弱",
            50: "震度5強",
            55: "震度6弱",
            60: "震度6強",
            70: "震度7",
        }
        scale_text = scale_map.get(max_scale, f"震度不明({max_scale})")

        hypocenter = latest_quake["earthquake"]["hypocenter"]["name"]
        magnitude = latest_quake["earthquake"]["hypocenter"]["magnitude"]
        tsunami_info = (
            "津波の心配なし"
            if latest_quake["earthquake"]["domesticTsunami"] == "None"
            else "⚠️津波情報に注意！"
        )

        message_text = (
            f"🦦 ミーアキャット地震速報 🦦\n\n"
            f"【発生時刻】{time_str}\n"
            f"【震源地】{hypocenter}\n"
            f"【最大震度】{scale_text}\n"
            f"【M】{magnitude}\n\n"
            f"{tsunami_info}"
        )

        # 4. Send to LINE
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(TARGET_USER_ID, TextSendMessage(text=message_text))

        logger.info(f"Notification sent: {time_str}")
        return {"status": "Notified!", "detail": message_text}

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return {"status": "Error", "msg": str(e)}

# ==========================================
# Watch List
# ==========================================
WATCH_LIST = {
    "Google": "https://www.google.com",
    "P2P Quake API": "https://api.p2pquake.net/v2/history?codes=551&limit=1",
    "URL_USAGI": os.getenv("URL_USAGI"),
    "URL_ROBO": os.getenv("URL_ROBO"),
}

# ==========================================
# Website Health Check Endpoint
# ==========================================
@app.get("/check_health")
def check_website_health() -> Dict[str, Any]:
    logger.info("🦦 Starting website health patrol...")

    error_report = []

    # Check each URL in the watch list
    for name, url in WATCH_LIST.items():
        if not url:
            continue

        try:
            # Timeout after 30 seconds
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                error_report.append(f"⚠️ {name}: Abnormal response (Code: {response.status_code})")
            else:
                logger.info(f"✅ {name}: OK")

        except Exception as e:
            error_report.append(f"❌ {name}: Access failed")

    # Send alert if errors found
    if error_report:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

        alert_text = "🦦 Emergency Alert! \n\n" + "\n".join(error_report)

        line_bot_api.push_message(TARGET_USER_ID, TextSendMessage(text=alert_text))
        return {"status": "Alert Sent", "detail": error_report}

    return {"status": "All Green", "detail": "異常なし"}