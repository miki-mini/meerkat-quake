import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuakeService:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def check_quake(self) -> Dict[str, Any]:
        """
        Check P2P Quake API and determine if a notification is needed.
        Returns:
            dict containing 'notify' (bool), 'message' (str), and other details.
        """
        try:
            headers = {"User-Agent": "MeerkatBot/1.0"}
            logger.info(f"Accessing: {self.api_url}")
            response = requests.get(self.api_url, headers=headers)

            # Log for debugging
            logger.debug(f"Status Code: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            if not data:
                return {"notify": False, "status": "No data"}

            latest_quake = data[0]
            time_str = latest_quake["earthquake"]["time"]

            # Timezone handling
            JST = timezone(timedelta(hours=9))
            quake_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=JST)
            now = datetime.now(JST)

            # Check if recent (5 mins)
            if now - quake_time > timedelta(minutes=5):
                return {"notify": False, "status": "No recent earthquake", "time": time_str}

            # Check scale
            max_scale = latest_quake["earthquake"]["maxScale"]
            # API spec: 30 = Scale 3
            if max_scale < 30:
                logger.info(f"Skipping small quake: Scale score {max_scale}")
                return {"notify": False, "status": "Small quake", "detail": "Skipped notification (Scale < 3)"}

            # Construct message
            message_text = self._create_message(latest_quake, time_str, max_scale)
            return {
                "notify": True,
                "message": message_text,
                "status": "Earthquake Detected",
                "time": time_str
            }

        except Exception as e:
            logger.error(f"Error checking quake: {e}")
            return {"notify": False, "status": "Error", "error": str(e)}

    def _create_message(self, quake_data, time_str, max_scale) -> str:
        scale_map = {
            10: "震度1", 20: "震度2", 30: "震度3", 40: "震度4",
            45: "震度5弱", 50: "震度5強", 55: "震度6弱", 60: "震度6強", 70: "震度7",
        }
        scale_text = scale_map.get(max_scale, f"震度不明({max_scale})")

        hypocenter_data = quake_data["earthquake"]["hypocenter"]
        hypocenter = hypocenter_data["name"]
        magnitude = hypocenter_data["magnitude"]

        tsunami_info = (
            "津波の心配なし"
            if quake_data["earthquake"]["domesticTsunami"] == "None"
            else "⚠️津波情報に注意！"
        )

        return (
            f"🦦 ミーアキャット地震速報 🦦\n\n"
            f"【発生時刻】{time_str}\n"
            f"【震源地】{hypocenter}\n"
            f"【最大震度】{scale_text}\n"
            f"【M】{magnitude}\n\n"
            f"{tsunami_info}"
        )
