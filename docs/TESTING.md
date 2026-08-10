# API キー テスト手順書

## 概要

このドキュメントは welfare-facilities-db の API キー機能のテスト方法を説明します。

## 環境構築

### 前提条件

- Docker & Docker Compose
- curl
- jq (JSON パース用、オプション)

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/flipslidersand/welfare-facilities-db.git
cd welfare-facilities-db

# 環境変数設定
cp .env.example .env
# .env を編集して必要な値を設定

# Docker Compose で起動
docker-compose up -d

# DB マイグレーション + 初期化の確認
docker-compose logs backend | tail -20
```

### ヘルスチェック

```bash
# API が起動しているか確認
curl http://localhost:8000/health

# 期待値: {"status":"ok"} または {"uptime":...}
```

## テスト実行

### 1. ローカル Python テスト（推奨）

```bash
cd backend

# 依存関係インストール
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt

# テスト実行
python -m pytest tests/ -v

# カバレッジ報告
python -m pytest tests/ --cov=app --cov-report=html
# htmlcov/index.html をブラウザで開く
```

**期待値**: 16/16 tests passed

### 2. 統合テスト（curl スクリプト）

```bash
# 環境変数設定
export API_BASE="http://localhost:8000"
export API_KEY="your-api-key-here"

# テストスクリプト実行
bash backend/scripts/test-api-keys.sh

# 期待値: ✅ 全テスト成功！
```

### 3. 手動テスト

#### 3.1 API キー一覧取得

```bash
curl http://localhost:8000/api-keys \
  -H "X-API-Key: your-api-key"

# 期待値: [{"id":1,"name":"Default API Key",...}]
```

#### 3.2 API キー作成

```bash
curl -X POST http://localhost:8000/api-keys \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"new-key"}'

# 期待値: {"id":2,"name":"new-key","key":"...","is_active":true,...}
```

#### 3.3 API キー更新

```bash
curl -X PATCH http://localhost:8000/api-keys/1 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"updated-key","is_active":false}'

# 期待値: {"id":1,"name":"updated-key","is_active":false,...}
```

#### 3.4 API キー削除

```bash
curl -X DELETE http://localhost:8000/api-keys/1 \
  -H "X-API-Key: your-api-key"

# 期待値: (204 No Content)
```

#### 3.5 認証エラー

```bash
# 無認証アクセス
curl http://localhost:8000/api-keys
# 期待値: {"detail":"Missing API key"} (401 Unauthorized)

# 無効なキー
curl http://localhost:8000/api-keys \
  -H "X-API-Key: invalid-key"
# 期待値: {"detail":"Invalid API key"} (401 Unauthorized)
```

## テスト項目一覧

| テスト                 | メソッド | エンドポイント  | 期待ステータス | 説明                     |
| ---------------------- | -------- | --------------- | -------------- | ------------------------ |
| 無認証アクセス         | GET      | /api-keys       | 401            | 認証なしでアクセス拒否   |
| キー一覧取得           | GET      | /api-keys       | 200            | 認証済みで一覧返却       |
| キー作成（基本）       | POST     | /api-keys       | 201            | 新しいキーを生成・返却   |
| キー作成（有効期限）   | POST     | /api-keys       | 201            | 有効期限付きキー生成     |
| キー更新（名前）       | PATCH    | /api-keys/{id}  | 200            | キー名を更新             |
| キー更新（無効化）     | PATCH    | /api-keys/{id}  | 200            | is_active フラグを無効化 |
| キー削除               | DELETE   | /api-keys/{id}  | 204            | キーを削除               |
| 存在しないキー更新     | PATCH    | /api-keys/99999 | 404            | 存在しないキーは 404     |
| 有効期限切れキーテスト | GET      | /api-keys       | 401            | 有効期限切れは拒否       |

## トラブルシューティング

### Docker Compose 起動エラー

```bash
# docker daemon 接続エラー
# → docker service が起動しているか確認
systemctl status docker

# ポート競合
# → 既存コンテナを停止
docker-compose down
```

### API キー認証エラー

```bash
# "API key not configured" エラー
# → 環境変数 API_KEY を確認
echo $API_KEY

# "Invalid API key" エラー
# → DB に登録されているキーハッシュと一致するか確認
docker-compose exec backend psql -U dev welfare_facilities_db -c "SELECT * FROM api_keys;"
```

### テスト失敗

```bash
# pytest 失敗時
python -m pytest tests/ -v -s  # 詳細出力

# curl スクリプト失敗時
bash backend/scripts/test-api-keys.sh  # エラーメッセージ確認
```

## 本番環境での考慮事項

- PBKDF2_SALT を安全な値に変更する（環境変数で管理）
- API キー CRUD エンドポイントを管理者のみに制限する
- 定期的にキーをローテーションする
- キー使用ログを監視する（usage_count, last_used_at）
- レート制限を実装する（来るフェーズ）

## 関連ドキュメント

- [README.md](../README.md) — プロジェクト概要
- [docs/API.md](./API.md) — API 仕様（別途作成予定）
