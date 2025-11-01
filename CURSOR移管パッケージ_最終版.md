# 🎁 Cursor移管パッケージ - 最終版

## 📦 パッケージ内容

以下のファイルがすべて作成され、Base64エンコードされています：

### 1. コアファイル

| ファイル | 説明 |
|---------|------|
| `.cursorrules` | Cursor AIのコーディングルール |
| `functions/relay/index.ts` | Front Door (Edge Function) |
| `.github/workflows/manus-progress.yml` | Manus進捗ハンドラー |
| `.github/workflows/line-event.yml` | LINEイベントハンドラー |
| `orchestration/MANUS_EXECUTION_BRIEF_costaware.txt` | Manus実行指示書（コスト節約版） |
| `orchestration/plan/current_plan.json` | 現在のPlan JSON |
| `orchestration/cost.py` | コスト見積もりツール |
| `docs/RUNBOOK.md` | 運用手順書 |
| `README.md` | プロジェクト説明書 |

### 2. 実行スクリプト

| ファイル | 説明 |
|---------|------|
| `scripts/encode_files.py` | Base64エンコードスクリプト |
| `scripts/plan_template.json` | Plan JSONテンプレート |
| `scripts/plan_with_base64.json` | Base64埋め込み済みPlan JSON |

---

## 🚀 Cursor移管の手順

### Step 1: GitHubリポジトリの確認

```bash
# リポジトリURL
https://github.com/mo666-med/line-friend-registration-system

# クローン
git clone https://github.com/mo666-med/line-friend-registration-system.git
cd line-friend-registration-system
```

### Step 2: Cursorで開く

```bash
# Cursorで開く
cursor .
```

### Step 3: `.cursorrules`を確認

Cursorが自動的に`.cursorrules`を読み込み、コーディングルールを適用します。

### Step 4: 変数を置換

`scripts/plan_with_base64.json`を開き、以下の変数を実際の値に置換してください：

| 変数 | 説明 | 例 |
|-----|------|---|
| `{{OWNER}}` | GitHubオーナー名 | `mo666-med` |
| `{{REPO}}` | リポジトリ名 | `line-friend-registration-system` |
| `{{VERIFIED_DOMAIN}}` | 検証済みドメイン | `gems-medical.jp` |
| `{{PROGRESS_WEBHOOK_URL}}` | 進捗Webhook URL | `https://your-domain.com/functions/v1/relay` |
| `{{STAKEHOLDER_EMAILS}}` | 関係者メール | `mo666.med@gmail.com` |
| `{{CAL_START_ISO}}` | カレンダー開始時刻 | `2025-11-08T10:00:00+09:00` |
| `{{CAL_END_ISO}}` | カレンダー終了時刻 | `2025-11-08T11:00:00+09:00` |
| `{{NOTION_PAGE_CURSOR_HANDOVER}}` | Notionページ | `page_id` |

### Step 5: Manusに投入（オプション）

**Manusポイントを節約するため、Cursorで直接実装することを推奨します。**

ただし、PR作成やIssue作成などの単純作業をManusに任せたい場合は、以下のコマンドを実行してください：

```bash
# Plan JSONをManusに投入
# TODO: Manus APIの呼び出し方法
```

### Step 6: Cursorで実装

Cursorで以下を実装してください：

1. **Front Doorのデプロイ**
   - Supabase Edge Functionとして`functions/relay/index.ts`をデプロイ
   - 環境変数を設定（`GH_OWNER`, `GH_REPO`, `GH_PAT`, `LINE_CHANNEL_SECRET`, `MANUS_API_KEY`, `FEATURE_BOT_ENABLED`）

2. **GitHub Secretsの設定**
   - `LLM_ENDPOINT`, `LLM_API_KEY`
   - `MANUS_API_KEY`, `MANUS_BASE_URL`
   - その他必要なSecrets（Issueを参照）

3. **LINE Developers Consoleの設定**
   - Webhook URLを新しいFront Door URLに変更
   - Webhookを有効化

4. **テスト**
   - `#参加`トリガーをテスト
   - `#完了`トリガーをテスト
   - 進捗WebhookがGitHub Actionsを起動することを確認

---

## 📋 チェックリスト

### 初期セットアップ

- [ ] GitHubリポジトリをクローン
- [ ] Cursorで開く
- [ ] `.cursorrules`が読み込まれることを確認
- [ ] `scripts/plan_with_base64.json`の変数を置換

### Front Doorデプロイ

- [ ] Supabase Edge Functionとして`functions/relay/index.ts`をデプロイ
- [ ] 環境変数を設定
- [ ] 署名検証が動作することを確認

### GitHub Actions設定

- [ ] GitHub Secretsを設定
- [ ] `manus-progress.yml`が動作することを確認
- [ ] `line-event.yml`が動作することを確認

### LINE設定

- [ ] Webhook URLを変更
- [ ] Webhookを有効化
- [ ] テストメッセージを送信

### 運用準備

- [ ] `docs/RUNBOOK.md`を確認
- [ ] 緊急停止手順を理解
- [ ] 監視設定（UptimeRobot等）

---

## 🎯 Cursor開発のポイント

### 1. `.cursorrules`を活用

Cursorは`.cursorrules`を自動的に読み込み、以下のルールを適用します：

- **PHI禁止**: 個人情報を送信・保存しない
- **医療安全ガードレール**: すべてのユーザー向け文面に付記
- **コスト節約**: 大量メール配信や重い処理を避ける
- **冪等性**: `idempotency_key`で二重実行を回避
- **監査可能性**: すべての外部呼び出しをログに記録

### 2. GitHub Actions主導

- **Front Door**: Webhook受信 → `repository_dispatch`
- **GitHub Actions**: イベント処理 → GPT解析 → Manus再指示
- **Manus**: 最後の一押し（PR作成、会議設定など）

### 3. コスト管理

```bash
# コスト見積もり
python orchestration/cost.py orchestration/plan/current_plan.json

# 予算超過の場合はデグレード
```

---

## 📄 添付ファイル

以下のファイルがGitHubリポジトリに含まれています：

1. **Base64エンコード済みファイル**: `scripts/plan_with_base64.json`
2. **実行スクリプト**: `scripts/encode_files.py`
3. **Plan JSONテンプレート**: `scripts/plan_template.json`

---

## 💡 次のアクション

### Cursor開発を開始する場合

1. GitHubリポジトリをクローン
2. Cursorで開く
3. Front Doorをデプロイ
4. GitHub Secretsを設定
5. テスト実行

### Manusに任せる場合（非推奨）

1. `scripts/plan_with_base64.json`の変数を置換
2. Manus APIに投入
3. PRをレビュー

---

## 📞 サポート

不明な点があれば、以下を確認してください：

- **README.md**: プロジェクト全体の説明
- **docs/RUNBOOK.md**: 運用手順書
- **GitHub Issues**: 質問や不具合報告

---

**Cursor移管パッケージの準備が完了しました！🎉**

Cursorで効率的に開発を進めてください。
