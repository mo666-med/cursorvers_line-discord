"""
Manus Cost Estimator

Manusポイント消費を事前に見積もり、予算超過を防ぐ。
"""

from collections import Counter
import json
import sys

# アクション別のポイント重み
WEIGHTS = Counter({
    "calendar.create": 3,
    "gmail.send": 4,
    "notion.append": 1,
    "supabase.upsert": 0,  # 直接実行（Manusを使わない）
    "line.reply": 0,  # 直接実行
})

BASE_COST = 2  # Plan実行の基本コスト


def estimate_plan_cost(plan: dict) -> int:
    """
    Plan JSONからManusポイント消費を見積もる
    
    Args:
        plan: Plan v1.2 JSON
    
    Returns:
        推定ポイント数
    """
    cost = BASE_COST
    
    for step in plan.get("steps", []):
        action = step.get("action", "")
        payload = step.get("payload", {})
        
        # 基本コスト
        cost += WEIGHTS.get(action, 0)
        
        # gmail.sendの場合、宛先数に応じて加算
        if action == "gmail.send":
            to_field = payload.get("to", "x")
            recipients = len(to_field.split(","))
            cost += max(0, recipients - 1)  # 2人目以降は+1
            
            # 添付ファイルがあれば+2
            if payload.get("attachments"):
                cost += 2
        
        # calendar.createの場合、参加者数に応じて加算
        if action == "calendar.create":
            attendees = payload.get("attendees", [])
            cost += len(attendees)
    
    return cost


def check_budget(plan: dict, budget_day: int = 50, budget_week: int = 200) -> dict:
    """
    予算チェック
    
    Args:
        plan: Plan v1.2 JSON
        budget_day: 1日の予算上限
        budget_week: 1週間の予算上限
    
    Returns:
        {
            "estimated_cost": int,
            "within_budget": bool,
            "recommendation": str
        }
    """
    cost = estimate_plan_cost(plan)
    
    # TODO: 実際の消費履歴を取得して累計を計算
    # 現在は単純に推定コストのみで判定
    
    within_budget = cost <= budget_day
    
    if within_budget:
        recommendation = "OK: 予算内です"
    else:
        recommendation = f"⚠️ 予算超過: {cost}pt > {budget_day}pt/day。デグレード（LINE+ics）を推奨"
    
    return {
        "estimated_cost": cost,
        "within_budget": within_budget,
        "recommendation": recommendation
    }


def suggest_degrade(plan: dict) -> dict:
    """
    デグレード案を提案
    
    Args:
        plan: Plan v1.2 JSON
    
    Returns:
        デグレード版のPlan JSON
    """
    degraded_plan = plan.copy()
    degraded_steps = []
    
    for step in plan.get("steps", []):
        action = step.get("action", "")
        
        # gmail.send → line.reply + ics添付に置き換え
        if action == "gmail.send":
            degraded_steps.append({
                "id": step["id"] + "_degraded",
                "action": "line.reply",
                "connector": "line_bot",
                "payload": {
                    "to": "{{USER_LINE_ID}}",
                    "messages": [
                        {
                            "type": "text",
                            "text": f"【通知】{step['payload'].get('subject', '')}\n\n{step['payload'].get('body', '')}"
                        }
                    ]
                },
                "idempotency_key": step["idempotency_key"] + "_degraded",
                "on_error": "continue"
            })
        
        # calendar.create → ics添付に置き換え
        elif action == "calendar.create":
            degraded_steps.append({
                "id": step["id"] + "_degraded",
                "action": "line.reply",
                "connector": "line_bot",
                "payload": {
                    "to": "{{USER_LINE_ID}}",
                    "messages": [
                        {
                            "type": "text",
                            "text": f"【カレンダー】{step['payload'].get('summary', '')}\n開始: {step['payload'].get('start', '')}\n終了: {step['payload'].get('end', '')}"
                        }
                    ]
                },
                "idempotency_key": step["idempotency_key"] + "_degraded",
                "on_error": "continue"
            })
        
        else:
            # その他はそのまま
            degraded_steps.append(step)
    
    degraded_plan["steps"] = degraded_steps
    degraded_plan["title"] = plan["title"] + " (Degraded)"
    
    return degraded_plan


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cost.py <plan.json>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        plan = json.load(f)
    
    result = check_budget(plan)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if not result["within_budget"]:
        degraded = suggest_degrade(plan)
        print("\n--- Degraded Plan ---")
        print(json.dumps(degraded, indent=2, ensure_ascii=False))
