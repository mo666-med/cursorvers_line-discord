# OpenAI定額プラン対応

## 概要

OpenAI APIの定額プラン（サブスクリプション）に対応するための設定方法です。

## 定額プランの種類

### 1. OpenAI API定額プラン
OpenAI APIには標準的な定額プランはありませんが、以下のオプションがあります：

- **Enterprise API**: 企業向け定額プラン（要問い合わせ）
- **ChatGPT Plus**: ブラウザ版のみ、APIアクセス不可
- **従量課金**: 標準的な使用方法

### 2. 代替サービス（定額プランあり）

以下のサービスには定額プランがあります：

- **Azure OpenAI Service**: 定額プランあり
- **Anthropic API**: 従量課金（高額制限あり）
- **その他のLLMサービス**: 定額プランありのサービス多数

## 設定方法

### OpenAI APIの設定

```bash
# APIキーを設定
gh secret set LLM_API_KEY --body "sk-..."

# エンドポイントを設定（デフォルト: https://api.openai.com/v1/chat/completions）
gh secret set LLM_ENDPOINT --body "https://api.openai.com/v1/chat/completions"

# モデルを設定（Variables、デフォルト: gpt-4o）
gh variable set OPENAI_MODEL --body "gpt-4o"
```

### Azure OpenAI Serviceの設定（定額プラン対応）

```bash
# Azure OpenAIのエンドポイントを設定
gh secret set LLM_ENDPOINT --body "https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT/chat/completions?api-version=2024-02-15-preview"

# APIキーを設定
gh secret set LLM_API_KEY --body "YOUR_AZURE_OPENAI_KEY"

# モデル名を設定
gh variable set OPENAI_MODEL --body "gpt-4"
```

### その他のLLMサービスの設定

```bash
# カスタムエンドポイントを設定
gh secret set LLM_ENDPOINT --body "https://your-llm-service.com/v1/chat/completions"

# APIキーを設定
gh secret set LLM_API_KEY --body "your-api-key"

# モデル名を設定
gh variable set OPENAI_MODEL --body "model-name"
```

## 定額プランの確認方法

### OpenAI APIの使用量確認

```bash
# OpenAI APIの使用量を確認（curlで確認）
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### コスト制限の設定

定額プランがない場合でも、コスト制限を設定できます：

1. OpenAI Dashboardにログイン
2. Settings → Usage limits に移動
3. Hard limit と Soft limit を設定

## コードの変更点

### 環境変数でモデルを設定可能に

```javascript
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o';
```

これにより、GitHub Variablesでモデルを変更できます。

### カスタムエンドポイント対応

```javascript
const OPENAI_ENDPOINT = process.env.OPENAI_ENDPOINT || process.env.LLM_ENDPOINT || 'https://api.openai.com/v1/chat/completions';
```

Azure OpenAIやその他のサービスにも対応可能です。

## 注意事項

### OpenAI APIの定額プランについて

- OpenAI APIには標準的な定額プランはありません
- Enterprise APIを利用する場合は、OpenAIに問い合わせが必要です
- ChatGPT PlusはAPIアクセスには使用できません

### コスト管理

定額プランがない場合でも、以下の方法でコストを管理できます：

1. **使用量制限の設定**: OpenAI Dashboardで設定
2. **モデルの選択**: `gpt-4o`より`gpt-3.5-turbo`の方が安価
3. **トークン数の制限**: `max_tokens`パラメータで制限

## 推奨設定

### コスト効率重視の場合

```bash
# gpt-3.5-turboを使用（gpt-4oより安価）
gh variable set OPENAI_MODEL --body "gpt-3.5-turbo"

# トークン数を制限（scripts/codex-agent.jsで設定）
# max_tokens: 1000 に変更
```

### 定額プランが必要な場合

1. **Azure OpenAI Service**を検討
2. **その他のLLMサービス**の定額プランを検討
3. **OpenAI Enterprise API**に問い合わせ

## 次のステップ

1. **現在の使用量を確認**
   ```bash
   # OpenAI Dashboardで確認
   ```

2. **コスト制限を設定**
   - OpenAI Dashboard → Settings → Usage limits

3. **モデルを変更（必要に応じて）**
   ```bash
   gh variable set OPENAI_MODEL --body "gpt-3.5-turbo"
   ```

