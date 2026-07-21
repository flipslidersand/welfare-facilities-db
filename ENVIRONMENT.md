# Environment Configuration Guide

Welfare Facilities DB の環境変数設定について説明します。

## Overview

環境変数は `backend/.env` ファイルで管理します。デフォルト値は `backend/.env.example` に記載されています。

## Backend Environment Variables

### 基本設定

| 変数名 | 型 | デフォルト | 説明 | 必須 |
|--------|-----|-----------|------|------|
| `DATABASE_URL` | string | `postgresql://dev:devpass@localhost:5432/welfare_facilities_db` | PostgreSQL 接続文字列 | ✓ |
| `DEBUG` | boolean | `true` | デバッグモード有効化 | - |
| `API_TITLE` | string | `Welfare Facilities DB` | API のタイトル | - |
| `API_VERSION` | string | `0.1.0` | API のバージョン | - |

### CORS 設定

```env
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

フロントエンドが異なるドメイン/ポートで動く場合、このリストに追加してください。

**フォーマット**: JSON 配列（ダブルクォートで囲む）

### Database 接続設定

Docker Compose を使用する場合、以下の設定をそのまま使用してください。

```env
DB_HOST=db
DB_PORT=5432
DB_NAME=welfare_facilities_db
DB_USER=dev
DB_PASSWORD=devpass
```

**ローカル開発時の変更例**:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=welfare_facilities_db
DB_USER=dev
DB_PASSWORD=devpass
```

### バックアップ設定

```env
BACKUP_DIR=/backups
BACKUP_RETENTION_DAYS=7
```

- `BACKUP_DIR`: PostgreSQL バックアップの保存先（Docker volume マウント）
- `BACKUP_RETENTION_DAYS`: バックアップの保持日数

### Grafana 設定

```env
GRAFANA_ADMIN_PASSWORD=admin
```

Grafana の初期管理者パスワード。本番環境では強力なパスワードに変更してください。

### オプション設定

#### Slack 通知

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Slack への通知を有効にする場合に設定してください。

#### データインポートパス

```env
FACILITY_CSV_PATH=/path/to/facility_data.csv
FINANCIAL_CSV_PATH=/path/to/financial_data.csv
```

自動インポート機能を使用する場合に設定してください。

#### カスタムホスト・ポート

```env
HOST=0.0.0.0
PORT=8000
```

API サーバーのバインドアドレスとポート。

## Frontend Environment Variables

`frontend/.env` で設定します（オプション）。

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | バックエンド API ベース URL |

### Docker Compose での設定

`docker-compose.yml` の `frontend` サービスで環境変数を設定：

```yaml
frontend:
  environment:
    VITE_API_BASE_URL: http://localhost:8000/api
```

## Docker Compose 環境変数

`docker-compose.yml` でリード専用に設定される変数：

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `POSTGRES_USER` | `dev` | PostgreSQL ユーザー名 |
| `POSTGRES_PASSWORD` | `devpass` | PostgreSQL パスワード |
| `POSTGRES_DB` | `welfare_facilities_db` | データベース名 |

### ポートマッピング

```yaml
services:
  db:
    ports:
      - "5433:5432"        # 外部:内部
  backend:
    ports:
      - "8000:8000"
  frontend:
    ports:
      - "5173:5173"
  prometheus:
    ports:
      - "9091:9090"
  alertmanager:
    ports:
      - "9093:9093"
  grafana:
    ports:
      - "3002:3000"
```

別のポート番号を使用する場合、`docker-compose.yml` を編集してください。

## 環境別設定例

### ローカル開発環境

```env
DATABASE_URL=postgresql://dev:devpass@localhost:5432/welfare_facilities_db
DEBUG=true
API_TITLE=Welfare Facilities DB (Local)
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
DB_HOST=db
DB_PORT=5432
DB_NAME=welfare_facilities_db
DB_USER=dev
DB_PASSWORD=devpass
BACKUP_DIR=/backups
BACKUP_RETENTION_DAYS=7
GRAFANA_ADMIN_PASSWORD=admin
```

### テスト環境

```env
DATABASE_URL=postgresql://test_user:test_pass@test-db:5432/welfare_test
DEBUG=true
API_TITLE=Welfare Facilities DB (Test)
CORS_ORIGINS=["http://test-ui:5173"]
DB_HOST=test-db
DB_PORT=5432
DB_NAME=welfare_test
DB_USER=test_user
DB_PASSWORD=test_pass
BACKUP_DIR=/backups
BACKUP_RETENTION_DAYS=3
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 12)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TEST/WEBHOOK/URL
```

### 本番環境

```env
DATABASE_URL=postgresql://prod_user:${PROD_DB_PASSWORD}@prod-db.example.com:5432/welfare_prod
DEBUG=false
API_TITLE=Welfare Facilities DB
CORS_ORIGINS=["https://dashboard.example.com"]
DB_HOST=prod-db.example.com
DB_PORT=5432
DB_NAME=welfare_prod
DB_USER=prod_user
DB_PASSWORD=${PROD_DB_PASSWORD}
BACKUP_DIR=/backups
BACKUP_RETENTION_DAYS=30
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
HOST=0.0.0.0
PORT=8000
```

## 環境変数の設定方法

### 1. .env ファイルから読み込み（推奨）

```bash
cp backend/.env.example backend/.env
# 必要に応じて backend/.env を編集
```

### 2. Docker Compose で直接指定

```bash
docker-compose run -e DATABASE_URL=postgresql://... backend python app/main.py
```

### 3. システム環境変数から読み込み

```bash
export DATABASE_URL=postgresql://...
docker-compose up
```

## 環境変数の検証

設定した環境変数が正しいか確認：

```bash
# Python で確認
python -c "from app.config import settings; print(settings.database_url)"

# bash で確認
grep "^[^#]" backend/.env | sort
```

## トラブルシューティング

### DATABASE_URL が認識されない

```bash
# .env ファイルが存在するか確認
ls -la backend/.env

# 形式が正しいか確認
grep "DATABASE_URL" backend/.env

# Docker コンテナから確認
docker-compose exec backend python -c "import os; print(os.getenv('DATABASE_URL'))"
```

### ポートが既に使用中

```bash
# 別のポートを使用するよう docker-compose.yml を編集
# 例: "5434:5432" に変更

docker-compose down
docker-compose up -d
```

### CORS エラーが発生

```bash
# frontend/.env の VITE_API_BASE_URL を確認
cat frontend/.env

# backend/.env の CORS_ORIGINS を確認
grep "CORS_ORIGINS" backend/.env

# 必要に応じて編集して再起動
docker-compose restart backend frontend
```

## セキュリティに関する注意

本番環境での設定時：

1. **パスワード管理**: 強力なパスワードを使用してください
   ```bash
   openssl rand -base64 32
   ```

2. **機密情報の保護**: `.env` ファイルを `.gitignore` に追加
   ```bash
   echo "backend/.env" >> .gitignore
   ```

3. **CORS の制限**: `CORS_ORIGINS` を必要最小限に設定
   ```env
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

4. **DEBUG モードの無効化**: 本番環境では `DEBUG=false`

5. **HTTPS の使用**: 本番環境では必ず HTTPS を使用

---

**最終更新**: 2026-07-21
