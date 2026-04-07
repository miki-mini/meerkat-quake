import requests
import logging
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuakeService:
    def __init__(self, api_url: str, persistence_file: str = "data/last_quake.json"):
        self.api_url = api_url
        self.persistence_file = persistence_file

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

            last_notified_id = self._load_last_quake_id()
            notifiable_quakes = []

            for item in data:
                if item.get("code") == 551 and "earthquake" in item:
                    quake_id = item.get("_id") or item.get("id") or item["earthquake"]["time"]
                    
                    if quake_id == last_notified_id:
                        # 過去に通知済みのIDに到達したら、それより古いデータは確認しない
                        break

                    time_str = item["earthquake"]["time"]
                    try:
                        JST = timezone(timedelta(hours=9))
                        quake_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=JST)
                        now = datetime.now(JST)
                        if now - quake_time > timedelta(hours=24):
                            continue # 古すぎるデータは無視
                    except Exception as e:
                        logger.warning(f"Time parsing error: {e}")
                        pass
                    
                    max_scale = item["earthquake"].get("maxScale", -1)
                    if max_scale >= 30:
                        notifiable_quakes.append((item, quake_id, time_str, max_scale))
                    else:
                        logger.info(f"Skipping small quake: Scale score {max_scale}")

            if not notifiable_quakes:
                return {"notify": False, "status": "No new notifiable quakes"}

            # 条件を満たす最も新しい地震（リストの先頭）を通知対象とする
            latest_quake, target_quake_id, target_time_str, target_max_scale = notifiable_quakes[0]

            # メッセージ作成
            message_text = self._create_message(latest_quake, target_time_str, target_max_scale)

            # 新しいIDを保存
            self._save_last_quake_id(target_quake_id)

            return {
                "notify": True,
                "message": message_text,
                "status": "Earthquake Detected",
                "time": target_time_str
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

    def _load_last_quake_id(self) -> Optional[str]:
        """Load the last notified earthquake ID from file."""
        if not os.path.exists(self.persistence_file):
            return None

        try:
            with open(self.persistence_file, "r") as f:
                data = json.load(f)
                return data.get("id")
        except Exception as e:
            logger.warning(f"Failed to load persistence file: {e}")
            return None

    def _save_last_quake_id(self, quake_id: str) -> None:
        """Save the last notified earthquake ID to file."""
        try:
            # ensure directory exists
            os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)

            with open(self.persistence_file, "w") as f:
                json.dump({"id": quake_id, "updated_at": datetime.now().isoformat()}, f)
        except Exception as e:
            logger.error(f"Failed to save persistence file: {e}")
