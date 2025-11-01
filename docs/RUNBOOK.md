# RUNBOOK - LINE友だち登録システム運用手順書

## 1. 緊急停止（Kill-Switch）

### 即座に停止する方法

```bash
# Supabase Edge Functionの環境変数を設定
supabase secrets set FEATURE_BOT_ENABLED=false --project-ref <your-project-ref>

# または、LINE Developers ConsoleでWebhookをOFF
```

### 確認

```bash
# Front Doorにリクエストを送信
curl https://<your-domain>/functions/v1/relay

# 503 "Bot is disabled" が返ればOK
```

---

## 2. 復旧手順

### 2-1. Front Door疎通確認

```bash
# 署名なしでテスト（開発環境のみ）
curl -X POST https://<your-domain>/functions/v1/relay \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# 200 OKが返ればFront Doorは正常
```

### 2-2. GitHub Actions疎通確認

```bash
# 手動でワークフローをトリガー
gh workflow run manus-progress.yml

# 実行状況を確認
gh run list --workflow=manus-progress.yml
```

### 2-3. GPT疎通確認

```bash
# GitHub Secretsを確認
gh secret list

# LLM_ENDPOINT, LLM_API_KEYが設定されているか確認
```

### 2-4. Manus疎通確認

```bash
# Manus APIにリクエスト
curl -X POST https://api.manus.im/v1/tasks \
  -H "Authorization: Bearer $MANUS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'
```

### 2-5. 本番復旧

```bash
# FEATURE_BOT_ENABLEDをtrueに戻す
supabase secrets set FEATURE_BOT_ENABLED=true --project-ref <your-project-ref>

# LINE Developers ConsoleでWebhookをON
```

---

## 3. ロールバック手順

### 3-1. 未マージPRのクローズ

```bash
# PRをクローズ
gh pr close <PR番号>

# ブランチを削除
git push origin --delete <ブランチ名>
```

### 3-2. Secrets回収

```bash
# 未使用のSecretsを削除
gh secret delete <SECRET_NAME>

# 監査ログに記録
echo "$(date): Deleted secret <SECRET_NAME>" >> logs/audit.log
git add logs/audit.log
git commit -m "audit: delete unused secret"
git push
```

### 3-3. Front DoorのURL切替

```bash
# DNSを旧URLに戻す
# または、LINE Developers ConsoleでWebhook URLを変更
```

### 3-4. Manusタスクのキャンセル

```bash
# 保留中のタスクを確認
# TODO: Manus APIでタスク一覧を取得

# タスクをキャンセル
# TODO: Manus APIでタスクをキャンセル
```

---

## 4. 監視

### 4-1. 外形監視

- **Front Doorの200率**: UptimeRobotで5分間隔
- **目標**: 99.9% uptime

### 4-2. SLO監視

| 指標 | 目標値 | 確認方法 |
|-----|-------|---------|
| delivery latency (p50) | < 2s | logs/progress/*.json |
| delivery latency (p95) | < 10s | logs/progress/*.json |
| error_rate (5分移動窓) | < 1% | logs/progress/*.json |
| heartbeat_miss | < 2/10min | GitHub Actions logs |

### 4-3. コスト監視

```bash
# 1日のManus使用量を確認
python orchestration/cost.py orchestration/plan/current_plan.json

# 予算超過の場合はデグレード
```

---

## 5. 予算管理

### 5-1. 予算設定

- **BUDGET_DAY**: 50pt/day
- **BUDGET_WEEK**: 200pt/week

### 5-2. デグレード経路

予算超過時は以下に切り替え：

- **gmail.send** → **line.reply** + テキスト通知
- **calendar.create** → **line.reply** + ics添付

```bash
# デグレード版Planを生成
python orchestration/cost.py orchestration/plan/current_plan.json

# 出力されたDegraded Planをcurrent_plan.jsonに上書き
```

---

## 6. 連絡網

### 6-1. 管理者連絡先

- **LINE**: @529ybhfo
- **Gmail**: mo666.med@gmail.com

### 6-2. エスカレーション

| レベル | 対応者 | 連絡方法 |
|-------|-------|---------|
| L1: 軽微な障害 | 開発者 | GitHub Issues |
| L2: 中程度の障害 | 技術責任者 | LINE + Gmail |
| L3: 重大な障害 | 経営層 | 電話 |

### 6-3. 法務・税務窓口

- **法務顧問**: 月3万円／5万円枠
- **税務顧問**: 固定費設計に依拠

---

## 7. よくあるトラブルと対処法

### 7-1. Front Doorが503を返す

**原因**: FEATURE_BOT_ENABLED=false

**対処**: 
```bash
supabase secrets set FEATURE_BOT_ENABLED=true --project-ref <your-project-ref>
```

### 7-2. GitHub Actionsが動かない

**原因**: Secretsが未設定

**対処**:
```bash
gh secret list
# 不足しているSecretsを追加
gh secret set <SECRET_NAME> --body "<value>"
```

### 7-3. GPT解析が失敗する

**原因**: LLM_API_KEYが無効

**対処**:
```bash
# 新しいAPIキーを発行
gh secret set LLM_API_KEY --body "sk-..."
```

### 7-4. Manusポイントが足りない

**原因**: 予算超過

**対処**:
```bash
# デグレード版Planに切り替え
python orchestration/cost.py orchestration/plan/current_plan.json
# 出力されたDegraded Planをcurrent_plan.jsonに上書き
git add orchestration/plan/current_plan.json
git commit -m "chore: switch to degraded plan"
git push
```

---

## 8. 定期メンテナンス

### 8-1. 週次

- [ ] logs/progress/ のログを確認
- [ ] SLO達成状況を確認
- [ ] Manusポイント消費量を確認

### 8-2. 月次

- [ ] Secretsのローテーション
- [ ] Front Doorの証明書更新確認
- [ ] RUNBOOKの更新

---

## 9. 参考リンク

- [GitHub Repository](https://github.com/mo666-med/line-friend-registration-system)
- [LINE Developers Console](https://developers.line.biz/console/)
- [Supabase Dashboard](https://supabase.com/dashboard)
- [Manus API Documentation](https://docs.manus.im)
