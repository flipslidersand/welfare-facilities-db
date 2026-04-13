# SQL クエリ集

Looker Studio データソース作成用のクエリ集です。

## 基本クエリ

### 1. 法人マスタ一覧

```sql
SELECT 
  corporation_id,
  name,
  type,
  prefecture,
  city,
  address,
  established_date,
  updated_at
FROM corporations
WHERE prefecture IS NOT NULL
ORDER BY name
```

### 2. 事業所一覧（法人情報付き）

```sql
SELECT 
  f.facility_id,
  f.name,
  f.corporation_id,
  c.name AS corporation_name,
  f.service_type,
  f.service_detail,
  f.capacity,
  f.prefecture,
  f.city,
  f.opened_date,
  f.match_status
FROM facilities f
LEFT JOIN corporations c ON f.corporation_id = c.corporation_id
ORDER BY f.prefecture, f.name
```

## 分析用クエリ

### 3. 売上ランキング（年度別）

```sql
SELECT 
  ROW_NUMBER() OVER (ORDER BY cf.revenue DESC) AS rank,
  cf.fiscal_year,
  cf.corporation_id,
  c.name,
  c.prefecture,
  cf.revenue,
  COUNT(f.facility_id) AS facility_count,
  COALESCE(SUM(f.capacity), 0) AS total_capacity
FROM corporation_financials cf
JOIN corporations c ON cf.corporation_id = c.corporation_id
LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
WHERE cf.revenue IS NOT NULL
GROUP BY cf.fiscal_year, cf.corporation_id, c.name, c.prefecture, cf.revenue
ORDER BY cf.fiscal_year DESC, cf.revenue DESC
LIMIT 50
```

### 4. 地域別集計（都道府県）

```sql
SELECT 
  cf.fiscal_year,
  c.prefecture,
  COUNT(DISTINCT cf.corporation_id) AS corporation_count,
  COUNT(DISTINCT f.facility_id) AS facility_count,
  COALESCE(SUM(f.capacity), 0) AS total_capacity,
  ROUND(AVG(f.capacity)::numeric, 2) AS avg_capacity,
  SUM(cf.revenue) AS total_revenue,
  AVG(cf.revenue)::bigint AS avg_revenue
FROM corporation_financials cf
JOIN corporations c ON cf.corporation_id = c.corporation_id
LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
WHERE c.prefecture IS NOT NULL
GROUP BY cf.fiscal_year, c.prefecture
ORDER BY cf.fiscal_year DESC, total_revenue DESC
```

### 5. サービス種別別集計

```sql
SELECT 
  cf.fiscal_year,
  f.service_type,
  COUNT(DISTINCT f.facility_id) AS facility_count,
  COALESCE(SUM(f.capacity), 0) AS total_capacity,
  COUNT(DISTINCT f.corporation_id) AS corporation_count,
  SUM(cf.revenue) AS total_revenue
FROM facilities f
LEFT JOIN corporation_financials cf 
  ON f.corporation_id = cf.corporation_id
WHERE f.service_type IS NOT NULL
GROUP BY cf.fiscal_year, f.service_type
ORDER BY cf.fiscal_year DESC, facility_count DESC
```

### 6. 法人詳細（法人ID指定）

```sql
SELECT 
  c.corporation_id,
  c.name,
  c.type,
  c.prefecture,
  c.city,
  COUNT(DISTINCT f.facility_id) AS facility_count,
  COALESCE(SUM(f.capacity), 0) AS total_capacity,
  MAX(cf.fiscal_year) AS latest_fiscal_year,
  MAX(cf.revenue) AS latest_revenue
FROM corporations c
LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
LEFT JOIN corporation_financials cf ON c.corporation_id = cf.corporation_id
WHERE c.corporation_id = @corporation_id
GROUP BY c.corporation_id, c.name, c.type, c.prefecture, c.city
```

### 7. 法人財務推移（法人ID指定）

```sql
SELECT 
  corporation_id,
  fiscal_year,
  revenue,
  ordinary_profit,
  net_assets,
  total_assets,
  employees,
  CASE 
    WHEN LAG(revenue) OVER (ORDER BY fiscal_year) IS NULL THEN NULL
    ELSE (revenue - LAG(revenue) OVER (ORDER BY fiscal_year))::float / 
         LAG(revenue) OVER (ORDER BY fiscal_year) * 100
  END AS revenue_growth_pct
FROM corporation_financials
WHERE corporation_id = @corporation_id
ORDER BY fiscal_year DESC
```

### 8. 時系列推移（全体）

```sql
SELECT 
  cf.fiscal_year,
  COUNT(DISTINCT cf.corporation_id) AS corporation_count,
  SUM(cf.revenue) AS total_revenue,
  AVG(cf.revenue)::bigint AS avg_revenue,
  COUNT(DISTINCT f.facility_id) AS facility_count,
  COALESCE(SUM(f.capacity), 0) AS total_capacity
FROM corporation_financials cf
LEFT JOIN corporations c ON cf.corporation_id = c.corporation_id
LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
GROUP BY cf.fiscal_year
ORDER BY cf.fiscal_year DESC
```

### 9. マッチング状況

```sql
SELECT 
  match_status,
  COUNT(*) AS facility_count,
  COUNT(DISTINCT corporation_id) AS corporation_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM facilities
GROUP BY match_status
```

## Looker Studio ダッシュボード用 パラメータ付きクエリ

### 10. 法人一覧（都道府県フィルタ）

```sql
SELECT 
  corporation_id,
  name,
  type,
  prefecture,
  city,
  established_date
FROM corporations
WHERE (@prefecture IS NULL OR prefecture = @prefecture)
ORDER BY name
LIMIT 100
```

### 11. 事業所一覧（複数条件フィルタ）

```sql
SELECT 
  f.facility_id,
  f.name,
  f.corporation_id,
  c.name AS corporation_name,
  f.service_type,
  f.capacity,
  f.prefecture
FROM facilities f
LEFT JOIN corporations c ON f.corporation_id = c.corporation_id
WHERE (@prefecture IS NULL OR f.prefecture = @prefecture)
  AND (@service_type IS NULL OR f.service_type = @service_type)
ORDER BY f.name
LIMIT 200
```

## パフォーマンス最適化

- 大量データ（>100万行）の場合は、年度範囲制限を推奨
- 複数結合では、インデックスが有効に機能していることを確認
- Looker Studio への大量データ読み込みは、事前集計ビューの利用を検討

```sql
-- 事前集計ビュー例（毎月更新）
CREATE VIEW corporation_summary AS
SELECT 
  cf.fiscal_year,
  cf.corporation_id,
  c.name,
  c.prefecture,
  cf.revenue,
  COUNT(f.facility_id) AS facility_count,
  SUM(f.capacity) AS total_capacity,
  CURRENT_TIMESTAMP AS updated_at
FROM corporation_financials cf
JOIN corporations c ON cf.corporation_id = c.corporation_id
LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
GROUP BY cf.fiscal_year, cf.corporation_id, c.name, c.prefecture, cf.revenue;
```
