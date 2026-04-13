# 福祉施設データベース設計書（法人・施設ハイブリッド型）

## 1. システム概要

### 目的
社会福祉法人・介護事業者を対象に、法人単位の売上・財務状況と、施設単位の規模・定員などの運営実態を年ごとに可視化する。

### 対象データソース（政府系公開データに限定）

| データ種 | ソース名 | 単位 | 提供形式 | 更新頻度 |
|---------|--------|------|--------|---------|
| 法人財務情報 | 社会福祉法人現況報告書等情報検索（WAM NET） | 法人 | CSV（要ログイン・申請） | 年次 |
| 施設基本情報 | 介護サービス情報公表システム（オープンデータ） | 事業所 | CSV | 年数回 |
| 施設基本情報 | 障害福祉サービス等情報公表システム（オープンデータ） | 事業所 | CSV | 年数回 |
| 補助統計 | e-Stat（介護サービス施設・事業所調査） | 地域・種別集計 | CSV | 年次 |

## 2. 全体アーキテクチャ

```
[データ収集層] → [統合DB層] → [分析・可視化層]

法人財務CSV ──┐
              ├──> PostgreSQL 16 ──> Looker Studio / Python
施設基本CSV ──┘      （結合キー：法人番号・事業所番号）
```

## 3. 論理データモデル

### 3.1 主要エンティティとリレーション

```
【法人マスタ】 1 ── * 【事業所マスタ】
       │
       └── 1 ── * 【法人財務年次】
```

### 3.2 テーブル定義

#### (1) 法人マスタ（corporations）

| フィールド名 | 型 | 説明 | キー |
|-------------|-----|------|------|
| corporation_id | CHAR(13) | 国税庁法人番号 | PK |
| name | VARCHAR(200) | 法人名称 | |
| type | VARCHAR(20) | 法人種別（社会福祉法人/株式会社/医療法人等） | |
| postal_code | CHAR(7) | 郵便番号 | |
| prefecture | VARCHAR(10) | 都道府県 | IDX |
| city | VARCHAR(50) | 市区町村 | |
| address | VARCHAR(200) | 詳細住所 | |
| established_date | DATE | 設立年月 | |
| updated_at | DATETIME | 最終更新日時 | |

#### (2) 事業所マスタ（facilities）

| フィールド名 | 型 | 説明 | キー |
|-------------|-----|------|------|
| facility_id | VARCHAR(20) | 公表システム上のID | PK |
| corporation_id | CHAR(13) | FK → 法人マスタ | FK, IDX |
| name | VARCHAR(200) | 事業所名称 | |
| service_type | VARCHAR(50) | サービス種別（介護/障害/児童等） | IDX |
| service_detail | VARCHAR(100) | 具体的サービス（訪問介護/デイサービス等） | |
| capacity | INTEGER | 定員 | |
| opened_date | DATE | 開設年月 | |
| postal_code | CHAR(7) | 郵便番号 | |
| prefecture | VARCHAR(10) | 都道府県 | IDX |
| city | VARCHAR(50) | 市区町村 | |
| address | VARCHAR(200) | 詳細住所 | |
| management_type | VARCHAR(30) | 経営主体種別（社会福祉法人/営利法人等） | |
| match_status | VARCHAR(20) | マッチング状態（matched/unmatched） | |
| updated_at | DATETIME | 最終更新日時 | |

#### (3) 法人財務年次（corporation_financials）

| フィールド名 | 型 | 説明 | キー |
|-------------|-----|------|------|
| id | SERIAL | 自動採番 | PK |
| corporation_id | CHAR(13) | FK → 法人マスタ | FK, IDX |
| fiscal_year | INTEGER | 対象年度（例：2022） | IDX |
| revenue | BIGINT | 売上高（事業収益） | |
| ordinary_profit | BIGINT | 経常利益 | |
| net_assets | BIGINT | 純資産額 | |
| total_assets | BIGINT | 総資産額 | |
| employees | INTEGER | 常勤換算職員数 | |
| report_url | VARCHAR(500) | 報告書URL（原本PDF） | |
| collected_at | DATETIME | データ収集日 | |
| updated_at | DATETIME | 最終更新日時 | |

## 4. インデックス設計

```sql
-- corporations テーブル
CREATE INDEX idx_corporation_prefecture ON corporations(prefecture);
CREATE INDEX idx_corporation_type ON corporations(type);

-- facilities テーブル
CREATE INDEX idx_facility_corporation ON facilities(corporation_id);
CREATE INDEX idx_facility_prefecture ON facilities(prefecture);
CREATE INDEX idx_facility_service_type ON facilities(service_type);

-- corporation_financials テーブル
CREATE INDEX idx_financial_corporation_year ON corporation_financials(corporation_id, fiscal_year);
CREATE INDEX idx_financial_corporation ON corporation_financials(corporation_id);
CREATE INDEX idx_financial_year ON corporation_financials(fiscal_year);
```

## 5. 分析クエリ例

### 年度ごとの法人売上と総定員の関係

```sql
SELECT 
    f.fiscal_year,
    f.corporation_id,
    m.name,
    f.revenue,
    COALESCE(SUM(s.capacity),0) AS total_capacity,
    COUNT(s.facility_id) AS facility_count
FROM corporation_financials f
JOIN corporations m ON f.corporation_id = m.corporation_id
LEFT JOIN facilities s ON m.corporation_id = s.corporation_id
    AND s.opened_date <= MAKE_DATE(f.fiscal_year, 4, 1)
GROUP BY f.fiscal_year, f.corporation_id, m.name, f.revenue
ORDER BY f.revenue DESC;
```

### 地域別の法人売上集計

```sql
SELECT 
    f.fiscal_year,
    m.prefecture,
    SUM(f.revenue) AS regional_revenue,
    COUNT(DISTINCT f.corporation_id) AS corporation_count,
    COUNT(DISTINCT s.facility_id) AS facility_count
FROM corporation_financials f
JOIN corporations m ON f.corporation_id = m.corporation_id
LEFT JOIN facilities s ON m.corporation_id = s.corporation_id
GROUP BY f.fiscal_year, m.prefecture
ORDER BY f.fiscal_year DESC, regional_revenue DESC;
```

## 6. 実装上の注意点・制約

| 項目 | 内容 |
|-----|------|
| 法人番号の欠損 | 古いデータでは欠番が多い。マッチングには工数がかかるため、法人番号がある年度から始めることを推奨。 |
| 社会福祉法人以外 | 「現況報告書」には社会福祉法人しか含まれない。株式会社運営の施設は別途調査が必要。 |
| データ更新ラグ | 現況報告書の公開は事業年度終了後1〜2年かかる場合がある。 |
| 施設の開設・廃止 | 「廃止年月」が含まれていない場合、年次ごとの正確な存在事業所を把握するのは困難。 |
| スクレイピング禁止 | 各サイトの利用規約を遵守し、APIや公式ダウンロード機能を使用すること。 |

## 7. Looker Studio 連携

データベースを Looker Studio に直接接続し、ダッシュボード作成が可能。

**推奨可視化例**:
- 年度別売上トップ20（棒グラフ）
- 都道府県別売上分布（地図/ヒートマップ）
- サービス種別ごとの施設数推移（折れ線）
- 法人詳細（選択フィルタ）

