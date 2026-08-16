---
title: "Render API: PUT /env-vars で fromDatabase が使えない"
tags: [render, deployment, postgresql, env-vars]
severity: high
date: "2026-08-16"
---

## 症状

Render API `PUT /services/{id}/env-vars` に `fromDatabase` 参照を含む JSON を送ると
`400 missing environment variable value` が返る。

## 原因

Render API v1 の env-vars エンドポイントは `fromDatabase` を未サポート。
`render.yaml` の Blueprint 経由でのみ有効（GUI/IaC 専用機能）。

## 解決策

DATABASE_URL を文字列値として直接設定する必要がある。
Render ダッシュボードの「Internal Database URL」を取得して直接 env var に貼る。

```bash
# ダッシュボードで Internal Database URL を取得後:
RENDER_KEY="..."
SVC_ID="..."
curl -X PUT -H "Authorization: Bearer $RENDER_KEY" \
  -H "Content-Type: application/json" \
  "https://api.render.com/v1/services/$SVC_ID/env-vars" \
  -d '[{"key": "DATABASE_URL", "value": "postgresql://..."}]'
```

## 予防

- Render で DB をサービスに紐付ける場合は render.yaml Blueprint か GUI を使う
- API 経由で繋ぐ場合は接続文字列を Vault に保存する運用を先に決める
- DB 作成時に必ず接続文字列を Vault(`secret/data/infra/welfare-db`)に保存する
