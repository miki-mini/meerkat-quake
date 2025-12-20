import logging
from linebot import LineBotApi
from linebot.models import TextSendMessage

logger = logging.getLogger(__name__)

class LineNotifier:
    def __init__(self, access_token: str, target_user_id: str):
        if not access_token:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not set.")
        if not target_user_id:
            logger.warning("TARGET_USER_ID is not set.")

        self.line_bot_api = LineBotApi(access_token) if access_token else None
        self.target_user_id = target_user_id

    def send_message(self, text: str):
        """Send a text message to the target user/group."""
        if not self.line_bot_api or not self.target_user_id:
            logger.error("Cannot send message: Missing token or target ID.")
            return False

        try:
            self.line_bot_api.push_message(self.target_user_id, TextSendMessage(text=text))
            logger.info(f"Notification sent to {self.target_user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send LINE message: {e}")
            raise e
