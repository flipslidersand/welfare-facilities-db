# 運用自動化ガイド - Operations Guide

## 概要

本ドキュメントでは、福祉施設データベースの自動データ収集、エラー監視、Slack 通知の設定方法を説明します。

## セットアップ手順

### 1. 環境変数の設定

`backend/.env` に以下を追加：

```bash
# データインポートパス（CSV ファイルのフルパス）
FACILITY_CSV_PATH=/path/to/facility_data.csv
FINANCIAL_CSV_PATH=/path/to/financial_data.csv

# Slack webhook URL（オプション、通知機能を使用する場合）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**パス設定例（Linux/Mac）**:
```bash
FACILITY_CSV_PATH=/home/user/data/facilities_2024.csv
FINANCIAL_CSV_PATH=/home/user/data/financials_2024.csv
```

**パス設定例（Windows）**:
```bash
FACILITY_CSV_PATH=C:\\Users\\user\\data\\facilities_2024.csv
FINANCIAL_CSV_PATH=C:\\Users\\user\\data\\financials_2024.csv
```

### 2. Slack ウェブフック URL の取得

Slack 通知を有効にするには：

1. [Slack App Directory](https://api.slack.com/apps) にアクセス
2. **Create New App** → **From scratch**
3. App Name: `welfare-facilities-notify`、Workspace を選択
4. 左メニューから **Incoming Webhooks** を選択
5. **Add New Webhook to Workspace** をクリック
6. 通知を送信するチャネル（例：`#data-pipeline`）を選択
7. 生成された Webhook URL を `SLACK_WEBHOOK_URL` に設定

**Webhook URL 例**:
```
https://YOUR-SLACK-WEBHOOK-URL-HERE
```

## スケジューラの動作

### 月次スケジュール

**実行時間**: 毎月 1 日 3:00 AM（JST）

**処理内容**:
- `import_facility_csv.py` を実行
- `FACILITY_CSV_PATH` から施設データをインポート
- DataCollectionLog テーブルに結果を記録
- 成功/失敗時に Slack へ通知

### 年次スケジュール

**実行時間**: 4 月 1 日 2:00 AM（JST）※日本の会計年度開始

**処理内容**:
- `import_corporation_csv.py` を実行
- `FINANCIAL_CSV_PATH` から法人財務データをインポート
- DataCollectionLog テーブルに結果を記録
- 成功/失敗時に Slack へ通知

## 手動実行

### API エンドポイント経由

スケジュールを待たずに手動でデータ取得を実行：

```bash
# 施設データをインポート
curl -X POST http://localhost:8000/api/collection-logs/trigger/facility

# 法人財務データをインポート
curl -X POST http://localhost:8000/api/collection-logs/trigger/financial
```

**レスポンス例**:
```json
{
  "status": "triggered",
  "script": "facility",
  "message": "Facility import triggered"
}
```

### Dashboard 経由

1. Dashboard ページを開く
2. **Latest Data Collection Logs** パネルで最新 5 件の実行ログを確認
3. 手動実行が必要な場合は上記の API を呼び出す

## 実行ログの確認

### API エンドポイント

```bash
# 最新 10 件のログを取得
curl http://localhost:8000/api/collection-logs?limit=10

# 特定のスクリプトのログをフィルタ
curl http://localhost:8000/api/collection-logs?script_name=import_facility_csv

# 失敗したログのみを表示
curl http://localhost:8000/api/collection-logs?status=failed

# 統計情報を取得
curl http://localhost:8000/api/collection-logs/stats/summary
```

### Dashboard パネル

Dashboard の **Latest Data Collection Logs** セクションで最新 5 件のログをリアルタイム確認：

- ✅ **SUCCESS（緑）** - インポート成功、処理件数を表示
- ❌ **FAILED（赤）** - インポート失敗、エラーメッセージを表示
- ⏳ **RUNNING（黄）** - 実行中
- ⏭️ **SKIPPED（グレー）** - CSV パス未設定などで実行スキップ

## トラブルシューティング

### スクリプトが実行されない場合

```bash
# 環境変数が正しく設定されているか確認
echo $FACILITY_CSV_PATH
echo $FINANCIAL_CSV_PATH

# ファイルが存在するか確認
test -f $FACILITY_CSV_PATH && echo "✓ File exists" || echo "✗ File not found"

# スケジューラが起動しているか確認（ログで確認）
tail -f backend/logs/app.log | grep "Scheduler"
```

### Slack 通知が来ない場合

```bash
# Webhook URL が正しいか確認
echo $SLACK_WEBHOOK_URL

# 手動でテスト通知を送信
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test notification from welfare-facilities-db"}' \
  $SLACK_WEBHOOK_URL
```

### CSV ファイルがインポートされない場合

1. CSV ファイルのエンコーディング確認（UTF-8 推奨）
2. CSV ファイルが正しい列構造を持つ確認

**期待される列**（施設データ）:
- `facility_id`, `facility_name`, `corporation_id`, `service_type`
- `capacity`, `opened_date`, `prefecture`, `city`, `address`

3. ログで詳細エラーを確認:
```bash
curl http://localhost:8000/api/collection-logs?status=failed | jq '.data[0].error_message'
```

## 本番環境での cron 設定

サーバーのシステム cron で定期実行を設定する場合：

### 1. スクリプトの作成

`/home/welfare-db/run_import.sh`:
```bash
#!/bin/bash
cd /home/welfare-db/backend
source .env
python scripts/import_facility_csv.py "$FACILITY_CSV_PATH" "介護"
```

### 2. Cron ジョブの登録

```bash
# crontab を編集
crontab -e

# 毎月 1 日 3:00 AM に施設データをインポート
0 3 1 * * /home/welfare-db/run_import.sh >> /home/welfare-db/logs/facility_import.log 2>&1

# 4 月 1 日 2:00 AM に財務データをインポート
0 2 1 4 * cd /home/welfare-db/backend && python scripts/import_corporation_csv.py "$FINANCIAL_CSV_PATH" >> /home/welfare-db/logs/financial_import.log 2>&1
```

## 参考

- [APScheduler ドキュメント](https://apscheduler.readthedocs.io/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [PostgreSQL Cron](https://www.postgresql.org/docs/current/modules-contrib.html)
