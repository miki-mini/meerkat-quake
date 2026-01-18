# 🦦 Meerkat Quake Bot (ミーアキャットの地震警備🦦)

![Earthquake Alert](https://img.shields.io/badge/Status-Earthquake_Alert-E91E63?style=for-the-badge&logo=rss)
![Health Check](https://img.shields.io/badge/Status-Health_Check-4CAF50?style=for-the-badge&logo=google-chrome)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121.0-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![P2P Quake](https://img.shields.io/badge/API-P2P_Quake-4285F4?style=for-the-badge&logo=google-cloud)

地震情報の監視と通知、およびWEBサイトの死活監視を行うLINE Botです。
FastAPIで動作し、Cloud Scheduler等から定期実行されることを想定しています。


<img src="images/meerkat.jpg" width="100">

## 🚀 機能 (Features)

### 1. 🌏 地震速報 (Earthquake Notification)
P2P地震情報APIを監視し、新しい地震が発生した場合にLINEで通知します。
- **エンドポイント**: `/check_quake`
- **通知条件**:
  - 最大震度が **震度3以上** であること
  - 発生から **5分以内** であること
- **通知内容**: 発生時刻、震源地、最大震度、マグニチュード、津波情報

### 2. 🏥 サイト死活監視 (Website Health Check)
登録されたURLのステータスをチェックし、異常（ステータスコード200以外、またはタイムアウト）があった場合に警告を通知します。
- **エンドポイント**: `/check_health`
- **監視リスト**:
  - Google (接続確認用)
  - P2P地震情報API
  - ユーザー定義URL (環境変数で設定)

## 🛠️ セットアップ (Setup)

### 必須環境変数 (.env)
以下の変数を設定してください。

| 変数名 | 説明 |
| --- | --- |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging APIのアクセストークン |
| `TARGET_USER_ID` | 通知を送るLINEユーザーまたはグループのID |
| `URL_USAGI` | 監視対象URL 1 (🐰 うさぎ) |
| `URL_ROBO` | 監視対象URL 2 (🤖🐈 ロボ猫) |

### 起動方法
```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# ローカルサーバー起動
uvicorn main:app --reload
```

## 📂 構成 (Structure)
- `app/`: アプリケーションのソースコード
  - `main.py`: FastAPIエントリーポイント
  - `config.py`: 設定ファイル
  - `services/`: ビジネスロジック
    - `line_notifier.py`: LINE送信
    - `quake_service.py`: 地震判定
    - `health_service.py`: 死活監視
- `tests/`: 単体テストコード
- `main.py`: 起動用スクリプト (Entrypoint)
- `requirements.txt`: 依存ライブラリ
- `.env`: 環境変数設定ファイル

## 🧪 テスト (Testing)
`pytest` を使って、地震判定ロジックなどが正しく動くか確認できます。

```bash
# テストの実行
pytest
```

## 📐 アーキテクチャ (Architecture)

```mermaid
graph TD
    Scheduler[🕒 Cloud Scheduler / Cron] -->|GET /check_quake| App
    Scheduler -->|GET /check_health| App

    subgraph "🦦 Meerkat Quake Bot"
        App[FastAPI Server]
    end

    subgraph "🌐 External Services"
        dmdata[P2P Quake API]
        sites[Monitored Websites]
        line[LINE Messaging API]
    end

    App -->|Fetch Data| dmdata
    App -->|Health Check| sites

    App -->|Push Notification| line
    line -->|Message| User[👤 User / Group]
```

### 📸 通知サンプル (Notification Sample)
LINE通知のサンプル画像です。

<img src="./images/sample.png" width="300" alt="通知サンプル">


## [地震通知サンプル](mock_notification.py)

## [監視通知サンプル](mock_health_check.py)

## 📄 ライセンス
MIT License


---
English Summary

Concept: A specialized monitoring bot that alerts users via LINE about real-time earthquake data and website uptime status.

Functionality: Integrates the P2P Earthquake API and custom health check logic to provide reliable, automated notifications.

Purpose: Designed as a lightweight, serverless solution for disaster prevention and proactive system maintenance.
---