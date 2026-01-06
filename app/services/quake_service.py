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

            latest_quake = data[0]
            quake_id = latest_quake.get("_id") # Use unique ID from API if available, or generate one
            # As p2pquake doesn't always guarantee a clean top-level ID in all endpoints,
            # we can fallback to checking time + hypocenter if ID is missing.
            # But the 'history' endpoint usually has an ID.
            if not quake_id:
                quake_id = latest_quake.get("id")

            # Fallback if no ID found (unlikely but safe)
            if not quake_id:
                quake_id = latest_quake["earthquake"]["time"]

            # Load last notified ID
            last_notified_id = self._load_last_quake_id()

            if quake_id == last_notified_id:
                 return {"notify": False, "status": "Already notified"}

            time_str = latest_quake["earthquake"]["time"]

            # Timezone handling
            JST = timezone(timedelta(hours=9))
            quake_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=JST)
            now = datetime.now(JST)

            # Sanity Check: Ignore if older than 24 hours (to prevent spamming very old quakes on boot)
            if now - quake_time > timedelta(hours=24):
                 return {"notify": False, "status": "Too old", "time": time_str}

            # Check scale
            max_scale = latest_quake["earthquake"]["maxScale"]
            # API spec: 30 = Scale 3
            if max_scale < 30:
                logger.info(f"Skipping small quake: Scale score {max_scale}")
                # Even if small, we should NOT update the ID yet.
                # If we save it, subsequent updates (e.g. scale correction) with the same ID will be ignored.
                return {"notify": False, "status": "Small quake", "detail": "Skipped notification (Scale < 3)"}

            # Construct message
            message_text = self._create_message(latest_quake, time_str, max_scale)

            # Save ID after successful processing preparation
            self._save_last_quake_id(quake_id)

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
