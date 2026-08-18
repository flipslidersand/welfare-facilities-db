# Looker Studio 連携設定手順

## 概要

Looker Studio を使用して、PostgreSQL データベースの福祉施設データを可視化します。

## セットアップ手順

### 1. Looker Studio 用ユーザーとビューの作成

```bash
cd ~/projects/welfare-facilities-db/backend

# データベース環境変数を設定
export DB_HOST=localhost
export DB_NAME=welfare_facilities_db
export DB_USER=dev
export DB_PASSWORD=devpass

# セットアップスクリプト実行（Looker パスワード指定）
python scripts/setup_looker.py "your-looker-password"
```

**スクリプトが作成するもの**:
- ✅ `looker_viewer` ユーザー（読取専用）
- ✅ `v_corporation_summary` ビュー（法人×年度別集計）
- ✅ `v_regional_summary` ビュー（地域×年度別集計）
- ✅ `v_service_type_summary` ビュー（サービス種別別集計）

### 2. Looker Studio でデータソースを追加

1. [Looker Studio](https://lookerstudio.google.com) にログイン
2. **新規レポート** → **新しいデータソース** を選択
3. **コネクタ** から **PostgreSQL** を選択
4. 接続詳細を入力：
   - **ホスト**: `localhost` (または お使いのサーバーIP)
   - **ポート**: `5432`
   - **データベース**: `welfare_facilities_db`
   - **ユーザー名**: `looker_viewer`
   - **パスワード**: セットアップスクリプトで指定したパスワード
5. **認証** をクリック

### 3. ビューからデータセットを作成

Looker Studio でデータセットを作成するには、以下の3つのビューを使用します：

#### 3.1 法人別ランキング（v_corporation_summary）

```sql
SELECT
  fiscal_year,
  corporation_id,
  name,
  prefecture,
  type,
  revenue,
  facility_count,
  total_capacity
FROM v_corporation_summary
WHERE fiscal_year = @fiscal_year_param
ORDER BY revenue DESC
LIMIT 20
```

**ダッシュボード用チャート**:
- 棒グラフ: X軸 = name, Y軸 = revenue
- テーブル: 全カラム表示

#### 3.2 都道府県別集計（v_regional_summary）

```sql
SELECT
  fiscal_year,
  prefecture,
  corporation_count,
  facility_count,
  total_capacity,
  total_revenue,
  avg_capacity
FROM v_regional_summary
WHERE fiscal_year = @fiscal_year_param
ORDER BY total_revenue DESC
```

**ダッシュボード用チャート**:
- 地図: 都道府県別カラーマップ（revenue による色分け）
- 折れ線グラフ: fiscal_year 時系列（revenue の推移）

#### 3.3 サービス種別別（v_service_type_summary）

```sql
SELECT
  service_type,
  prefecture,
  facility_count,
  total_capacity,
  corporation_count
FROM v_service_type_summary
ORDER BY service_type, facility_count DESC
```

**ダッシュボード用チャート**:
- 積み上げ棒グラフ: X軸 = service_type, Y軸 = facility_count （色分け = prefecture）

### 4. パラメータの設定

Looker Studio のレポートにフィルタを追加するには、**パラメータ** を定義します：

```
@fiscal_year_param (整数型)
  - デフォルト値: 2022
  - 有効な値の範囲: 2020-2023
```

## 推奨ダッシュボード構成

### ページ1: Executive Summary
- **KPI カード**: 総法人数、総施設数、総定員
- **棒グラフ**: 売上ランキングトップ20
- **ヒートマップ**: 都道府県別売上分布

### ページ2: 時系列分析
- **折れ線グラフ**: 法人売上の年度推移（複数法人）
- **折れ線グラフ**: 都道府県別売上推移
- **テーブル**: 年度比較（前年比）

### ページ3: セグメント別分析
- **積み上げ棒グラフ**: サービス種別別施設数（都道府県別色分け）
- **テーブル**: サービス種別別の詳細統計

## トラブルシューティング

### 接続できない場合
```bash
# PostgreSQL 接続確認
psql -h localhost -U looker_viewer -d welfare_facilities_db

# ファイアウォール確認（ポート5432が開いているか）
sudo ufw status
sudo ufw allow 5432/tcp
```

### ビューが見つからない場合
```bash
# ビューが作成されているか確認
psql -h localhost -U dev -d welfare_facilities_db
SELECT * FROM information_schema.views WHERE table_name LIKE 'v_%';
```

### パフォーマンスが遅い場合
- Looker Studio の **キャッシュを更新** してください
- PostgreSQL で **ANALYZE** を実行してください：
```sql
ANALYZE v_corporation_summary;
ANALYZE v_regional_summary;
ANALYZE v_service_type_summary;
```

## 参考
- [Looker Studio ドキュメント](https://support.google.com/looker-studio)
- [PostgreSQL コネクタ](https://support.google.com/looker-studio/answer/7288087)
