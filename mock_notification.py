import os
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage

# .envを読み込み
load_dotenv()

# 設定読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
TARGET_USER_ID = os.getenv("TARGET_USER_ID")

def send_mock_quake():
    print("🦦 避難訓練：テスト警報・サンプル通知を作成します...")

    # README掲載用のサンプル文面
    # 実際よりも少し大げさすぎない、一般的な内容にします
    message_text = (
        "🦦 ミーアキャット地震速報 🦦\n\n"
        "【発生時刻】2024/01/01 12:34:56\n"
        "【震源地】ミーアキャット王国\n"
        "【最大震度】震度5弱\n"
        "【M】4.5\n\n"
        "津波の心配なし"
    )

    try:
        if not LINE_CHANNEL_ACCESS_TOKEN or not TARGET_USER_ID:
            raise ValueError(".envの設定が足りません！確認してください。")

        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(TARGET_USER_ID, TextSendMessage(text=message_text))
        print("✅ 送信完了！LINEを確認して、スクリーンショットを撮ってください📸")
    except Exception as e:
        print(f"❌ 送信失敗...: {e}")

if __name__ == "__main__":
    send_mock_quake()
