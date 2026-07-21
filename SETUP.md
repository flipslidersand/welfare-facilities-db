# Setup Guide - Welfare Facilities DB

このドキュメントは、Welfare Facilities DB の環境構築からサービス起動までの手順を説明します。

## Table of Contents

1. [前提条件](#前提条件)
2. [環境構築](#環境構築)
3. [サービス起動](#サービス起動)
4. [動作確認](#動作確認)
5. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

### 必須ツール

以下のツールをインストール済みであることを確認してください。

| ツール | バージョン | 用途 | インストール方法 |
|--------|-----------|------|-----------------|
| **Docker** | 20.10+ | コンテナ実行 | https://docs.docker.com/get-docker/ |
| **Docker Compose** | 2.0+ | マルチコンテナ管理 | https://docs.docker.com/compose/install/ |
| **Python** | 3.11+ | スクリプト実行（ローカル開発時） | https://www.python.org/downloads/ |
| **Node.js** | 18+ | フロントエンド開発（ローカル開発時） | https://nodejs.org/ |
| **Git** | 2.0+ | バージョン管理 | https://git-scm.com/ |

### システム要件

- **ディスク容量**: 最小 2GB 空き容量
- **メモリ**: 最小 4GB（Docker が 2GB 以上必要）
- **OS**: Linux / macOS / Windows (WSL2)

### ポート確認

以下のポートが利用可能であることを確認してください。

| サービス | ポート | 用途 |
|---------|--------|------|
| PostgreSQL | 5433 | データベース |
| FastAPI Backend | 8000 | API サーバー |
| React Frontend | 5173 | Web UI |
| Prometheus | 9091 | メトリクス収集 |
| AlertManager | 9093 | アラート管理 |
| Grafana | 3002 | ダッシュボード |

---

## 環境構築

### 1. リポジトリのクローン

```bash
git clone git@github.com-ordeam:dev-teams-ordeamo/welfare-facilities-db.git
cd welfare-facilities-db
```

### 2. 環境変数の設定

```bash
# Backend 用の .env ファイル作成
cp backend/.env.example backend/.env
```

#### backend/.env のカスタマイズ

デフォルト値でそのまま使用可能です。必要に応じて編集してください。

```env
# 基本設定（デフォルト値で OK）
DATABASE_URL=postgresql://dev:devpass@localhost:5432/welfare_facilities_db
DEBUG=true
API_TITLE=Welfare Facilities DB
API_VERSION=0.1.0

# CORS 設定
CORS_ORIGINS=["http://localhost:5173"]

# データバックアップ設定
BACKUP_DIR=/backups
BACKUP_RETENTION_DAYS=7

# データベース接続（Docker Compose 使用時）
DB_HOST=db
DB_PORT=5432
DB_NAME=welfare_facilities_db
DB_USER=dev
DB_PASSWORD=devpass

# Grafana 管理者パスワード
GRAFANA_ADMIN_PASSWORD=admin

# Slack 通知（オプション）
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. 自動セットアップスクリプト実行（推奨）

```bash
bash scripts/setup.sh
```

このスクリプトは以下を自動実行します：
- ✓ 環境変数のバリデーション
- ✓ ポート確認
- ✓ Docker Compose の起動
- ✓ データベースの初期化
- ✓ ヘルスチェック実行

### 4. 手動セットアップ（トラブル時）

自動スクリプトが失敗した場合、以下の手動手順を実行してください。

#### 4.1 Docker イメージのビルド

```bash
docker-compose build
```

#### 4.2 コンテナの起動

```bash
# バックグラウンド起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

#### 4.3 PostgreSQL の準備待機

PostgreSQL がヘルスチェックに成功するまで待機します（通常 10～30 秒）。

```bash
docker-compose ps
```

#### 4.4 データベーステーブルの初期化

```bash
docker-compose exec backend python scripts/init_db.py
```

---

## サービス起動

### 自動起動（推奨）

```bash
docker-compose up -d
```

### 個別サービス起動

```bash
# データベースのみ
docker-compose up -d db

# バックエンドのみ
docker-compose up -d backend

# フロントエンドのみ
docker-compose up -d frontend
```

### ローカル開発（コンテナなし）

#### Backend ローカル起動

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend ローカル起動

```bash
cd frontend
npm install
npm run dev
```

---

## 動作確認

### 1. ヘルスチェック

```bash
curl http://localhost:8000/health
# 期待される応答: {"status": "healthy", "service": "welfare-facilities-db"}
```

### 2. API ドキュメント

ブラウザで以下にアクセス：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Web UI

```bash
http://localhost:5173
```

### 4. 包括的な動作確認

```bash
python scripts/verify_setup.py
# または
bash scripts/verify_setup.sh
```

---

## トラブルシューティング

### 1. Docker コンテナが起動しない

```bash
# ログ確認
docker-compose logs backend
docker-compose logs db

# 再起動
docker-compose down --remove-orphans
docker-compose up --build
```

### 2. PostgreSQL 接続エラー

```bash
# ポート確認
lsof -i :5433  # macOS/Linux

# DB 再起動
docker-compose restart db
```

### 3. Backend API が応答しない

```bash
# DB が起動完了まで待機（20～30 秒）
docker-compose logs -f backend

# Application startup ログが出るまで待つ
```

### 4. Frontend が API に接続できない

```bash
# 設定確認
grep "VITE_API_BASE_URL" docker-compose.yml

# .env ファイルで設定
echo "VITE_API_BASE_URL=http://localhost:8000/api" > frontend/.env
docker-compose restart frontend
```

### 5. ディスクスペース不足

```bash
docker system prune -a
docker-compose down -v
df -h
```

### 6. メモリ不足（OOM）

```bash
# Docker Desktop のメモリ上限を 4GB 以上に増加
# Docker Desktop > Settings > Resources > Memory

# または docker-compose.yml でメモリ制限追加:
# deploy:
#   resources:
#     limits:
#       memory: 1G
```

### 7. AlertManager 起動エラー

```bash
# 設定ファイル確認
ls -la monitoring/alertmanager.yml

# 設定ファイルが無い場合、デフォルト作成
mkdir -p monitoring
cat > monitoring/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'webhook_receiver'

receivers:
  - name: 'webhook_receiver'
EOF

docker-compose restart alertmanager
```

---

## 次のステップ

セットアップが完了したら：

1. **データインポート**: [README.md - Data Import](README.md#data-import)
2. **Looker Studio ダッシュボード設定**: [docs/DESIGN.md](docs/DESIGN.md)
3. **Slack 通知設定**: backend/.env に SLACK_WEBHOOK_URL を追加

---

**最終更新**: 2026-07-21
