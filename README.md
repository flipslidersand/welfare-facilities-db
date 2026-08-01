# Welfare Facilities DB

> **Status**: Activate（本番化進行中） — 2026-08-01 判定
> Critical 4件（データインポート・API認証・認証情報・デプロイ先）のロードマップを策定し本番化へ移行。

社会福祉法人・介護事業者を対象に、法人単位の売上・財務状況と、施設単位の規模・定員などの運営実態を年ごとに可視化するシステム。

政府系公開データ（WAM NET、介護サービス情報公表、障害福祉情報公表）から CSV を取り込み、統合DBで分析・可視化します。

## Overview

- **法人マスタ**: 社会福祉法人の基本情報を年次で管理
- **事業所マスタ**: 介護・障害・児童福祉施設の情報（定員、サービス種別など）
- **法人財務年次**: 法人の売上・経常利益・純資産などを年度別に記録
- **ダッシュボード**: Looker Studio での可視化対応（DB直接接続）


## Quick Start

### 推奨: 自動セットアップスクリプト

初めてのセットアップは、自動セットアップスクリプトを使用することをお勧めします。

```bash
bash setup.sh
```

詳細は [SETUP.md](SETUP.md) を参照してください。

### Docker Compose で起動

```bash
docker-compose up
```

起動後：
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

### ローカル開発

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# データベース初期化
python scripts/init_db.py

# サーバー起動
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
welfare-facilities-db/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI アプリケーション
│   │   ├── database.py          # SQLAlchemy 設定
│   │   ├── models.py            # DB モデル
│   │   ├── schemas.py           # Pydantic スキーマ
│   │   ├── routers/
│   │   │   ├── corporations.py  # 法人 API
│   │   │   ├── facilities.py    # 施設 API
│   │   │   └── analytics.py     # 分析 API
│   │   └── crud/
│   │       ├── corporation_crud.py
│   │       └── facility_crud.py
│   ├── scripts/
│   │   ├── init_db.py
│   │   ├── import_corporation_csv.py
│   │   ├── import_facility_csv.py
│   │   └── match_corporation_facility.py
│   ├── alembic/                 # DB マイグレーション
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── CorporationList.tsx
│   │   │   └── CorporationDetail.tsx
│   │   ├── components/
│   │   ├── api/
│   │   │   └── client.ts        # API クライアント
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml
└── docs/
    ├── DESIGN.md
    ├── data_sources.md
    └── sql_queries.md
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.111.0
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 16
- **Server**: Uvicorn
- **Data**: Pandas, Openpyxl

### Frontend
- **Framework**: React 18.2
- **Language**: TypeScript 5.3
- **Build**: Vite 5
- **Charts**: Recharts 2.10
- **Routing**: React Router 6.20
- **HTTP**: Axios 1.6

### Infrastructure
- **Container**: Docker + Docker Compose
- **Database**: PostgreSQL 16-alpine
- **Server**: Python 3.11-slim, Node 20-alpine

## API Endpoints

### Corporations
- `GET /api/corporations` - 一覧（フィルタ・ページング対応）
- `GET /api/corporations/{id}` - 詳細（財務・事業所関連込み）
- `GET /api/corporations/{id}/financials` - 財務推移
- `GET /api/corporations/{id}/facilities` - 配下事業所

### Facilities
- `GET /api/facilities` - 一覧（都道府県・サービス種別フィルタ）
- `GET /api/facilities/{id}` - 詳細
- `GET /api/facilities/prefecture/{pref}/summary` - 都道府県別サマリー

### Analytics
- `GET /api/analytics/ranking?fiscal_year=2022` - 売上ランキング
- `GET /api/analytics/regional?fiscal_year=2022` - 地域別集計
- `GET /api/analytics/summary` - システム全体統計

### Health
- `GET /health` - ヘルスチェック
- `GET /docs` - Swagger UI（API ドキュメント）

## Frontend Pages

- **Dashboard** - 年度別ランキング（棒グラフ）、都道府県別サマリー、施設分布（円グラフ）
- **Corporations** - 法人一覧・検索
- **Corporation Detail** - 法人詳細、財務推移（折れ線グラフ）、配下事業所一覧

## Data Import

### Step 1: 法人財務データ

1. [WAM NET](https://www.wam.go.jp/) からログイン・申請
2. 現況報告書 CSV をダウンロード
3. インポート実行

```bash
python scripts/import_corporation_csv.py --master corporations.csv
python scripts/import_corporation_csv.py --financials financials.csv
```

### Step 2: 施設基本データ

1. [介護サービス情報公表システム](https://www.kaigo.mhlw.go.jp/) から CSV ダウンロード
2. インポート実行

```bash
python scripts/import_facility_csv.py facilities.csv 介護
```

### Step 3: マッチング（法人番号欠損対策）

```bash
python scripts/match_corporation_facility.py 0.8
```

## Data Model

### Corporations (法人マスタ)
- `corporation_id` CHAR(13) - PK
- `name`, `type`, `prefecture`, `city`, `address`
- `established_date`, `updated_at`

### Facilities (事業所マスタ)
- `facility_id` VARCHAR(20) - PK
- `corporation_id` VARCHAR(13) - FK
- `name`, `service_type`, `service_detail`
- `capacity`, `opened_date`
- `prefecture`, `city`, `address`
- `match_status` - 法人マッチング状態

### CorporationFinancials (法人財務年次)
- `id` SERIAL - PK
- `corporation_id` VARCHAR(13) - FK
- `fiscal_year`, `revenue`, `ordinary_profit`
- `net_assets`, `total_assets`, `employees`
- `report_url`, `collected_at`

## Environment Variables

**Backend (.env)**
```
DATABASE_URL=postgresql://dev:devpass@localhost:5432/welfare_facilities_db
DEBUG=true
API_TITLE=Welfare Facilities DB
API_VERSION=0.1.0
CORS_ORIGINS=["http://localhost:5173"]
```

**Frontend (.env)**
```
VITE_API_BASE_URL=http://localhost:8000/api
```

## Testing

### API テスト

```bash
# 健全性確認
curl http://localhost:8000/health

# 法人一覧
curl http://localhost:8000/api/corporations

# 分析（ランキング）
curl "http://localhost:8000/api/analytics/ranking?fiscal_year=2022"
```

### Frontend ビルド

```bash
cd frontend
npm run type-check  # TypeScript チェック
npm run build       # 本番ビルド
```

## Development Roadmap

### Phase 1 (実装済み)
- ✅ DB スキーマ（3テーブル）
- ✅ CSV インポートスクリプト
- ✅ FastAPI ルーター
- ✅ React フロントエンド（Dashboard, List, Detail）

### Phase 2 (次)
- ⏳ Looker Studio ダッシュボード作成
- ⏳ 複数年度データ自動更新バッチ
- ⏳ 障害福祉・児童福祉データ統合

### Phase 3 (本運用)
- ⏳ 月次/年次スケジュール更新
- ⏳ 権限管理（読取用ユーザー）
- ⏳ Slack 通知

## Troubleshooting

### Docker エラー
```bash
# コンテナ再起動
docker-compose down
docker-compose up --build
```

### DB 接続エラー
```bash
# PostgreSQL が起動しているか確認
docker ps

# DB 直接接続確認
psql postgresql://dev:devpass@localhost:5432/welfare_facilities_db
```

### API が応答しない
```bash
# Backend ログ確認
docker logs welfare-api

# 手動起動（ローカル）
cd backend && uvicorn app.main:app --reload
```

## Documentation

- [設計書](docs/DESIGN.md) - DB スキーマ、ビジネスロジック詳細
- [データソース](docs/data_sources.md) - 外部データソース一覧
- [SQL クエリ集](docs/sql_queries.md) - Looker Studio 用クエリ

## License

MIT

## Contributing

プルリクエストを歓迎します。
