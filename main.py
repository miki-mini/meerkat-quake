import os
import requests
import json
from datetime import datetime, timedelta
from fastapi import FastAPI
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime, timedelta, timezone

# ★ここを追加：.envを読み込むための魔法
from dotenv import load_dotenv

# ★これ大事：.envファイルを読み込む
load_dotenv()

app = FastAPI()

# ==========================================
# 設定エリア (金庫から取り出す！)
# ==========================================

# os.getenv("キーの名前") で取り出します
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
Target_User_ID = os.getenv("TARGET_USER_ID")

# P2P地震情報API (これは公開情報なのでそのままでOK)
P2P_API_URL = "https://api.p2pquake.net/v2/history?codes=551&limit=1"




# ==========================================
# ルート確認用 (アクセスできるかテストする場所)
# ==========================================
@app.get("/")
def read_root():
    return {"status": "元気です！ミーアキャット警備中🦦"}


# ==========================================
# 地震チェック本番 (Schedulerがここを叩きます)
# ==========================================
@app.get("/check_quake")
def check_earthquake():
    print("🦦 パトロール開始...")

    try:
        # 1. APIからデータを取得
        # ヘッダーは念のためつけておきます
        headers = {"User-Agent": "MeerkatBot/1.0"}

        print(f"アクセス中: {P2P_API_URL}")  # URL確認
        response = requests.get(P2P_API_URL, headers=headers)

        # ★ ここで中身を無理やり表示させる！
        print(f"ステータスコード: {response.status_code}")
        print(f"返ってきた中身(先頭500文字): {response.text[:500]}")

        # エラーがあればここで止まる
        response.raise_for_status()

        data = response.json()

        # ... (以下同じ) ...

        if not data:
            return {"status": "No data"}

        latest_quake = data[0]

        # 2. 地震の発生時刻を確認
        time_str = latest_quake["earthquake"]["time"]

        # JSTタイムゾーンを定義
        JST = timezone(timedelta(hours=9))

        # APIの時刻をJSTとして解釈
        quake_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=JST)

        # 現在時刻もJSTで取得
        now = datetime.now(JST)

        # 【判定】「直近の地震」じゃなかったら無視する
        # ※Cloud Schedulerが1分おきに来るので、少し余裕を持って「過去5分以内」とします
        # これをしないと、過去の地震を何度も通知しちゃいます
        if now - quake_time > timedelta(minutes=5):
            return {"status": "異常なし（直近の地震ではありません）", "time": time_str}

        # --- ここから下は「地震だ！」と判定された時だけ動く ---

        # 3. メッセージ作成
        max_scale = latest_quake["earthquake"]["maxScale"]

        # ==========================================
        # 🛑 ここにフィルターを追加！ (震度3未満なら無視)
        # ==========================================
        # APIの仕様: 10=震度1, 20=震度2, 30=震度3 ...
        if max_scale < 30:
            print(f"震度が小さいので無視します: 震度スコア {max_scale}")
            return {"status": "Small quake", "detail": "震度3未満のため通知スキップ"}
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

        # 4. LINEに送信
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(Target_User_ID, TextSendMessage(text=message_text))

        print(f"通知しました！: {time_str}")
        return {"status": "Notified!", "detail": message_text}

    except Exception as e:
        print(f"エラー発生: {e}")
        return {"status": "Error", "msg": str(e)}

# ==========================================
# 監視リスト (URLは金庫から出す！)
# ==========================================
WATCH_LIST = {
    "Google先生": "https://www.google.com", # Googleは有名なのでそのままでOK
    "P2P地震API": "https://api.p2pquake.net/v2/history?codes=551&limit=1",

    # ここを変える！
    "🐰 うさぎ": os.getenv("URL_USAGI"),
    "🤖🐈 ロボ猫": os.getenv("URL_ROBO"),
}

# ==========================================
# 🆕 新機能：サイト死活監視 (SRE)
# ==========================================
@app.get("/check_health")
def check_website_health():
    print("🦦 サイト巡回パトロール開始...")

    error_report = []

    # リストにあるURLを順番にノックしていく
    for name, url in WATCH_LIST.items():
        try:
            # 3秒待っても返事がなかったらタイムアウト扱いにする
            response = requests.get(url, timeout=30)

            # ステータスコードが200(OK)じゃなかったらエラーリストに入れる
            if response.status_code != 200:
                error_report.append(f"⚠️ {name}: 応答異常 (Code: {response.status_code})")
            else:
                print(f"✅ {name}: ヨシ！")

        except Exception as e:
            # アクセスすらできなかった場合
            error_report.append(f"❌ {name}: アクセス失敗")

    # もしエラーが1つでもあれば、まとめてLINEで報告！
    if error_report:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

        # エラーメッセージを改行でつなぐ
        alert_text = "🦦 異常発生！緊急連絡です！\n\n" + "\n".join(error_report)

        line_bot_api.push_message(Target_User_ID, TextSendMessage(text=alert_text))
        return {"status": "Alert Sent", "detail": error_report}

    return {"status": "All Green", "detail": "異常なし"}