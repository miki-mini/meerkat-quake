import requests
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class HealthService:
    def check_health(self, watch_list: Dict[str, str]) -> List[str]:
        """
        Check health of URLs in the watch list.
        Returns:
             List of error messages. Empty list if all OK.
        """
        error_report = []
        logger.info("🦦 Starting website health patrol...")

        for name, url in watch_list.items():
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
                # We simplify the error message to avoid leaking too much info
                error_report.append(f"❌ {name}: Access failed")

        return error_report
