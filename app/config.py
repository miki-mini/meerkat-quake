import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if LINE_CHANNEL_ACCESS_TOKEN:
    LINE_CHANNEL_ACCESS_TOKEN = LINE_CHANNEL_ACCESS_TOKEN.strip()

TARGET_USER_ID = os.getenv("TARGET_USER_ID")
if TARGET_USER_ID:
    TARGET_USER_ID = TARGET_USER_ID.strip()

# P2P Quake API
P2P_API_URL = "https://api.p2pquake.net/v2/history?codes=551&limit=1"

# Watch List for Health Check
WATCH_LIST = {
    "Google": "https://www.google.com",
    "P2P Quake API": "https://api.p2pquake.net/v2/history?codes=551&limit=1",
    "URL_USAGI": os.getenv("URL_USAGI"),
    "URL_ROBO": os.getenv("URL_ROBO"),
}
