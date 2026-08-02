# e-Stat 介護統計データセット一覧

**確認日**: 2026-08-02  
**関連 Issue**: #588-#593

---

## API セットアップ

API キーは手動申請が必要:

1. https://www.e-stat.go.jp/api/ にアクセス
2. ユーザー登録 → アプリ登録
3. 取得した API キーを環境変数に設定:

```bash
export ESTAT_API_KEY=<your-app-id>
# または gopass に保存
gopass insert infra/e-stat/api-key
```

4. 接続テスト:

```bash
curl "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList?appId=${ESTAT_API_KEY}&searchWord=介護サービス施設&limit=5"
```

---

## 主要データセット

### 介護サービス施設・事業所調査（推奨）

| 項目 | 値 |
| --- | --- |
| 統計コード | 00450027 |
| 提供機関 | 厚生労働省 |
| 更新頻度 | 年次 |
| 地域粒度 | 都道府県別・市区町村別 |
| 主要指標 | 施設数・定員数・入所者数・従事者数 |
| e-Stat URL | https://www.e-stat.go.jp/stat-search/database?toukei=00450027 |

**特徴**: 集計統計（施設個別ではなく地域別集計）。WAM NET SFK と組み合わせてエリア分析に活用。

### 社会福祉施設等調査

| 項目 | 値 |
| --- | --- |
| 統計コード | 00450041 |
| 更新頻度 | 年次 |
| 主要指標 | 施設種類別・都道府県別の施設数・定員 |

### 介護保険事業状況報告

| 項目 | 値 |
| --- | --- |
| 統計コード | 00450026 |
| 更新頻度 | 月次 |
| 主要指標 | 要介護認定者数・サービス利用者数・費用 |

---

## API 利用例（セットアップ後）

```python
import requests

ESTAT_API_KEY = os.getenv("ESTAT_API_KEY")
BASE_URL = "https://api.e-stat.go.jp/rest/3.0/app/json"

# データセット一覧取得
resp = requests.get(f"{BASE_URL}/getStatsList", params={
    "appId": ESTAT_API_KEY,
    "toukei": "00450027",
    "limit": 20,
})

# 統計データ取得（statsDataId は一覧から取得）
resp = requests.get(f"{BASE_URL}/getStatsData", params={
    "appId": ESTAT_API_KEY,
    "statsDataId": "<statsDataId>",
    "cdArea": "13",  # 東京都
})
```

---

## 現在の実装状況

| データソース | 状況 |
| --- | --- |
| WAM NET SFK（障害福祉） | ✅ 実装済み（download_sfk_csv.py + import_sfk_csv.py） |
| 介護サービス情報公表 | ❌ 一括DLなし（#578 調査済み） |
| e-Stat 介護統計 | ⏳ API キー申請待ち |

---

## 注意事項

- e-Stat は個別事業所データではなく**集計統計**を提供
- 施設検索には WAM NET / kaigokensaku を使用する
- e-Stat データは需要予測・地域分析用途に適している
