# LINE友だち登録システム - GitHub Actions中心運用 v2.0

## 概要

LINE Official Accountの友だち登録システムを、GitHub Actions中心で運用する堅牢なアーキテクチャです。

### アーキテクチャ

```
[LINE] ─┐
        ├→ Front Door（Supabase Edge Function）→ GitHub API repository_dispatch
[Manus Progress] ─┘                                   └→ GitHub Actions
                                                            ├→ GPT（解析/シミュレーション）
                                                            ├→ Manus API（実行指示）
                                                            ├→ Supabase（ログ/指標）
                                                            └→ LINE返信
```

### 特徴

- ✅ **止めない入口**: Front Doorは薄い関数（100～200行）で常時稼働
- ✅ **見える運用**: すべての進捗・差分をGitに記録
- ✅ **自動対策**: GPTが進捗を解析し、異常時は自動で対策
- ✅ **完全な監査**: 全イベント・差分・ログを永続化
- ✅ **段階的改善**: バージョン管理で安全にロールバック可能

---

## ディレクトリ構造

```
.
├── .github/workflows/          # GitHub Actionsワークフロー
│   ├── manus-progress.yml      # Manus進捗ハンドラ
│   ├── line-event.yml          # LINE受信ハンドラ
│   ├── db-migrate.yml          # DBマイグレーション
│   ├── backup.yml              # 設定バックアップ
│   └── slo-monitor.yml         # SLO監視
├── database/migrations/        # Supabaseマイグレーション
├── functions/relay/            # Front Door（Edge Function）
│   └── index.ts                # Webhook受信→repository_dispatch
├── orchestration/              # オーケストレーション
│   ├── plan/                   # Plan JSON
│   │   ├── current_plan.json   # 現在のPlan
│   │   └── plan_delta.json     # GPT解析結果
│   └── MANUS_EXECUTION_BRIEF_v2.0.txt  # Manus実行指示書
└── logs/progress/              # 進捗ログ（自動記録）
```

---

## データ契約

### Plan v1.2（GPT → Manus）

```json
{
  "title": "友だち登録時のウェルカムメッセージ送信",
  "risk": {
    "level": "low",
    "reasons": ["定型メッセージのみ"],
    "approval": "not_required"
  },
  "steps": [
    {
      "id": "s1",
      "action": "supabase.upsert",
      "connector": "supabase",
      "payload": {
        "table": "line_members",
        "data": {"line_user_id": "...", "display_name": "..."}
      },
      "idempotency_key": "hash(eventId+userId+step)",
      "on_error": "abort"
    },
    {
      "id": "s2",
      "action": "line.reply",
      "connector": "line_bot",
      "payload": {
        "to": "...",
        "messages": [{"type": "text", "text": "ウェルカムメッセージ"}]
      },
      "idempotency_key": "hash(eventId+userId+step)",
      "on_error": "compensate"
    }
  ],
  "rollback": ["s1: Supabaseからレコード削除"],
  "observability": {
    "success_metrics": ["line_members.count", "line.reply.success"],
    "logs": ["step毎のlatency", "retries"]
  }
}
```

### ProgressEvent v1.1（Manus → GitHub Actions → GPT）

```json
{
  "event_type": "step_succeeded",
  "task_id": "task-123",
  "step_id": "s1",
  "ts": "2025-11-01T12:34:56Z",
  "idempotency_key": "hash-abc123",
  "plan_title": "友だち登録時のウェルカムメッセージ送信",
  "metrics": {
    "latency_ms": 1234,
    "retries": 0,
    "queue_ms": 50
  },
  "context": {
    "trigger": "#参加",
    "user_ref": "hashed_line_user_id",
    "risk_level": "low"
  },
  "preview": null,
  "error": null
}
```

### PlanDelta v1.1（GPT解析結果 → Manus）

```json
{
  "decision": "retry",
  "reasons": ["Supabase一時的な503エラー"],
  "actions": [
    {
      "type": "retry",
      "step_id": "s1",
      "backoff_ms": 5000,
      "max_retries": 2
    }
  ],
  "amended_plan": {
    "...": "修正されたPlan v1.2"
  },
  "simulated_outcomes": [
    {
      "scenario": "retry+backoff",
      "p_success": 0.78,
      "risk": "low"
    }
  ]
}
```

---

## SLO（Service Level Objectives）

| 指標 | 目標値 |
|-----|-------|
| delivery latency (p50) | < 2s |
| delivery latency (p95) | < 10s |
| error_rate (5分移動窓) | < 1% |
| heartbeat_miss | < 2/10min |
| uptime | ≥ 99.9% |

---

## 安全装置

1. **MAX_FEEDBACK_HOPS=3**: GPT⇄Manus往復の上限
2. **COOLDOWN=60s**: 同一idempotency_keyの再指示制限
3. **承認ゲート**: 大量配信・外部送信は必ず承認
4. **Kill-Switch**: `FEATURE_BOT_ENABLED=false`で即停止
5. **署名検証**: LINE・Manusの署名を必ず検証
6. **冪等性**: idempotency_keyで二重実行を回避

---

## セットアップ

### 1. GitHub Secrets設定

```bash
# GPT解析用
gh secret set LLM_ENDPOINT --body "https://api.openai.com/v1/chat/completions"
gh secret set LLM_API_KEY --body "sk-..."

# Manus API
gh secret set MANUS_API_KEY --body "..."
gh secret set PROGRESS_WEBHOOK_URL --body "https://your-domain.jp/functions/relay"

# Connectors
gh secret set CONNECTOR_GCAL --body "uuid-..."
gh secret set CONNECTOR_GMAIL --body "uuid-..."
gh secret set CONNECTOR_NOTION --body "uuid-..."
gh secret set CONNECTOR_SUPABASE --body "uuid-..."
gh secret set CONNECTOR_LINEBOT --body "uuid-..."

# Supabase
gh secret set SUPABASE_ACCESS_TOKEN --body "..."
```

### 2. GitHub Variables設定

```bash
gh variable set MANUS_BASE_URL --body "https://api.manus.im"
gh variable set VERIFIED_DOMAIN --body "https://your-verified-domain.jp"
```

### 3. Front Door（Supabase Edge Function）デプロイ

```bash
cd functions/relay
supabase functions deploy relay --project-ref <your-project-ref>
```

### 4. LINE Developers ConsoleでWebhook URL設定

```
https://<your-project-ref>.supabase.co/functions/v1/relay
```

---

## 運用

### 進捗確認

```bash
# 最新の進捗ログを確認
cat logs/progress/*.json | jq -s 'sort_by(.ts) | .[-5:]'

# Plan差分を確認
cat orchestration/plan/plan_delta.json | jq
```

### 手動でManusを実行

```bash
# current_plan.jsonを編集
vim orchestration/plan/current_plan.json

# GitHub Actionsを手動トリガー
gh workflow run manus-progress.yml
```

### Kill-Switch（緊急停止）

```bash
# Front Doorの環境変数を設定
supabase secrets set FEATURE_BOT_ENABLED=false --project-ref <your-project-ref>
```

---

## テスト

### 正常系

```bash
# #参加イベントをシミュレート
curl -X POST https://<your-project-ref>.supabase.co/functions/v1/relay \
  -H "Content-Type: application/json" \
  -d '{"event_type":"task_created","task_id":"test-123","plan_title":"友だち登録"}'
```

### エラー系

```bash
# Supabase 503エラーをシミュレート
# → GPTがretry/backoffを提案
```

### 承認系

```bash
# 大量配信（>50件）をシミュレート
# → Manusがstatus="ask"で承認待ち
```

---

## ライセンス

MIT License

---

## 連絡先

- GitHub: [@mo666-med](https://github.com/mo666-med)
- LINE Official Account: @529ybhfo
