"""
Base64エンコードスクリプト

すべての必要なファイルをBase64エンコードし、Plan JSONに埋め込む。
"""

import base64
import json
from pathlib import Path

# エンコード対象ファイル
FILES = {
    "BASE64_CURSORRULES": ".cursorrules",
    "BASE64_WORKFLOW_PROGRESS": ".github/workflows/manus-progress.yml",
    "BASE64_WORKFLOW_LINE": ".github/workflows/line-event.yml",
    "BASE64_FRONTDOOR": "functions/relay/index.ts",
    "BASE64_MANUS_BRIEF": "orchestration/MANUS_EXECUTION_BRIEF_costaware.txt",
    "BASE64_CURRENT_PLAN": "orchestration/plan/current_plan.json",
    "BASE64_COSTPY": "orchestration/cost.py",
    "BASE64_RUNBOOK": "docs/RUNBOOK.md",
    "BASE64_README": "README.md",
}

def encode_file(filepath: str) -> str:
    """ファイルをBase64エンコード"""
    with open(filepath, 'rb') as f:
        content = f.read()
    return base64.b64encode(content).decode('utf-8')

def main():
    # プロジェクトルートに移動
    project_root = Path(__file__).parent.parent
    
    encoded = {}
    
    for key, filepath in FILES.items():
        full_path = project_root / filepath
        if full_path.exists():
            encoded[key] = encode_file(str(full_path))
            print(f"✅ Encoded: {filepath}")
        else:
            print(f"⚠️ Not found: {filepath}")
            encoded[key] = ""
    
    # Plan JSONテンプレートを読み込み
    plan_template_path = project_root / "scripts" / "plan_template.json"
    with open(plan_template_path) as f:
        plan_template = json.load(f)
    
    # Base64値を埋め込み
    plan_json_str = json.dumps(plan_template, indent=2, ensure_ascii=False)
    
    for key, value in encoded.items():
        plan_json_str = plan_json_str.replace(f"{{{{{key}}}}}", value)
    
    # 出力
    output_path = project_root / "scripts" / "plan_with_base64.json"
    with open(output_path, 'w') as f:
        f.write(plan_json_str)
    
    print(f"\n✅ Plan JSON generated: {output_path}")
    print(f"\n📋 Next steps:")
    print(f"1. 変数を置換: {{{{OWNER}}}}, {{{{REPO}}}}, etc.")
    print(f"2. ManusにPlan JSONを投入")

if __name__ == "__main__":
    main()
