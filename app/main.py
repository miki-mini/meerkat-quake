from fastapi import FastAPI
import os
from .config import LINE_CHANNEL_ACCESS_TOKEN, TARGET_USER_ID, P2P_API_URL, WATCH_LIST
from .services.line_notifier import LineNotifier
from .services.quake_service import QuakeService
from .services.health_service import HealthService
from typing import Dict, Any

app = FastAPI()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Initialize Services
line_notifier = LineNotifier(LINE_CHANNEL_ACCESS_TOKEN, TARGET_USER_ID)
quake_service = QuakeService(P2P_API_URL)
health_service = HealthService()

@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "Meerkat Bot is running 🦦"}

@app.get("/check_quake")
def check_earthquake() -> Dict[str, Any]:
    result = quake_service.check_quake()

    if result.get("notify"):
        line_notifier.send_message(result["message"])
        result["notified"] = True
    else:
        result["notified"] = False

    return result

@app.get("/check_health")
def check_website_health() -> Dict[str, Any]:
    errors = health_service.check_health(WATCH_LIST)

    if errors:
        alert_text = "🦦 Emergency Alert! \n\n" + "\n".join(errors)
        line_notifier.send_message(alert_text)
        return {"status": "Alert Sent", "detail": errors}

    return {"status": "All Green", "detail": "異常なし"}
