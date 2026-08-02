# WAM NET 障害福祉サービス等情報公表 CSV 仕様

**確認日**: 2026-08-02  
**データ取得元**: https://www.wam.go.jp/content/wamnet/pcpub/top/sfkopendata/  
**関連 Issue**: #594 / #595 / #596 / #597

---

## ダウンロード URL パターン

```
https://www.wam.go.jp/content/files/pcpub/top/sfkopendata/{YYYYMM}/sfkopendata_{YYYYMM}_{NN}.zip
```

- `YYYYMM`: 公表年月（ページをスクレイピングして最新を取得）
- `NN`: サービス種別コード（2桁）

### 利用可能なサービス種別コード（202603 実績）

| コード | 種別       |
| ------ | ---------- |
| 11–15  | 居宅介護系 |
| 21–24  | 生活介護系 |
| 32–34  | 就労系     |
| 41–46  | 入所系     |
| 52–54  | 児童系     |
| 60–70  | その他     |

**最新データ**: 202603（2026年3月）  
**エンコード**: UTF-8 BOM付き（`encoding="utf-8-sig"`で読み込む）  
**更新頻度**: 年数回（公表月をページから自動検出）

---

## CSV カラム定義（実カラム名）

| #     | CSV カラム名                     | 内部フィールド名 | 説明                    |
| ----- | -------------------------------- | ---------------- | ----------------------- |
| 0     | 都道府県コード又は市区町村コード | pref_city_code   | 先頭2桁が都道府県コード |
| 1     | NO（システム内の固有番号）       | —                | 使用しない              |
| 2     | 指定機関名                       | —                | 使用しない              |
| 3     | 法人の名称                       | corporation_name |                         |
| 4     | 法人の名称\_かな                 | —                | 使用しない              |
| 5     | 法人番号                         | corporation_id   |                         |
| 6     | 法人住所（市区町村）             | —                | 使用しない              |
| 7     | 法人住所（番地以降）             | —                | 使用しない              |
| 8     | 法人電話番号                     | —                | 使用しない              |
| 9     | 法人FAX番号                      | —                | 使用しない              |
| 10    | 法人URL                          | —                | 使用しない              |
| 11    | サービス種別                     | service_type     |                         |
| 12    | 事業所の名称                     | facility_name    |                         |
| 13    | 事業所の名称\_かな               | —                | 使用しない              |
| 14    | 事業所番号                       | facility_id      | **主キー**              |
| 15    | 事業所住所（市区町村）           | city             | 都道府県+市区町村が連結 |
| 16    | 事業所住所（番地以降）           | address          |                         |
| 17–19 | 電話・FAX・URL                   | —                | 使用しない              |
| 20    | 事業所緯度                       | —                | 将来利用予定            |
| 21    | 事業所経度                       | —                | 将来利用予定            |
| 22–28 | 利用時間・定休日                 | —                | 22–26使用しない         |
| 28    | 定員                             | capacity         |                         |

### 内部フィールドへのマッピング方法

- `prefecture`: `都道府県コード又は市区町村コード` の先頭2桁を `PREF_CODE_MAP` で変換
- `postal_code`, `opened_date`, `management_type`, `service_detail`: WAM NET CSV には存在しない → 空文字/None

---

## DB への取り込み

```bash
cd backend
# 1. ダウンロード（latest_yearmonth() がページをスクレイピング）
venv/bin/python3 scripts/download_sfk_csv.py 202603 /tmp/sfk_data

# 2. import（WAM_NET_SFK_COLUMNS マッピングが自動適用）
for csv in /tmp/sfk_data/*.csv; do
    venv/bin/python3 scripts/import_facility_csv.py "$csv" 障害
done
```

---

## 検証結果（202603 / csvdownload011.csv）

| 項目                  | 値                                       |
| --------------------- | ---------------------------------------- |
| 総行数                | 25,386 行                                |
| facility_id 取得率    | 100%                                     |
| corporation_id 取得率 | 100%                                     |
| prefecture 変換       | PREF_CODE_MAP で正常変換（01→北海道 等） |

---

## 注意事項

- `opened_date`（開設年月）・`postal_code`（郵便番号）は CSV に含まれない
- 住所は `事業所住所（市区町村）` + `事業所住所（番地以降）` の2フィールド構成（`prefecture` は都道府県コードから別途補完）
- 法人 CSV（`import_corporation_csv.py`）と `corporation_id` で結合可能
