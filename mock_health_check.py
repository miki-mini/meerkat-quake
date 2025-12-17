
import main
import requests
from unittest.mock import MagicMock

# -------------------------------------------------
# 🧪 エラー再現用のテストスクリプト
# 実際には通信せず、わざとエラーを発生させます
# -------------------------------------------------

def run_simulation():
    print("🧪 エラー通知のシミュレーションを開始します...")

    # 1. requests.get を騙して、エラーを返すようにします
    original_get = requests.get

    def mock_get_behavior(url, timeout=30):
        # うさぎさんは「アクセス失敗（通信エラー）」役
        if "usagi" in url:
            raise requests.exceptions.ConnectTimeout("Read timed out")

        # ロボ猫さんは「405 Method Not Allowed」役
        if "robo" in url:
            mock_resp = MagicMock()
            mock_resp.status_code = 405
            return mock_resp

        # その他は正常
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        return mock_resp

    # モックを注入
    main.requests.get = mock_get_behavior

    # 2. 監視リストを一時的に書き換え
    # 本物のリストは触らず、テスト用のリストを使わせます
    backup_list = main.WATCH_LIST
    main.WATCH_LIST = {
        "🐰 うさぎ": "http://dummy.usagi",
        "🤖🐈 ロボ猫": "http://dummy.robo"
    }

    try:
        # 3. テスト実行！
        # これで LINE に通知が飛びます（通知機能自体は本物を使います）
        # ※ LINEトークンが設定されていないとエラーになります
        result = main.check_website_health()

        print("\n✅ シミュレーション終了！")
        print("LINEに以下のような通知が届いているはずです：")
        print("-" * 30)
        # LINE通知の内容を print で再現してあげる
        if "detail" in result:
             print("\n".join(result["detail"]))
        print("-" * 30)

    except Exception as e:
        print(f"シミュレーション中にエラーが発生しました: {e}")
    finally:
        # 後始末（元に戻す）
        main.requests.get = original_get
        main.WATCH_LIST = backup_list

if __name__ == "__main__":
    run_simulation()
