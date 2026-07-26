#!/usr/bin/env python3
"""
假设翻转测试 (Assumption Flip Test) —— 逐个压力测试模型假设，找出致命假设
原创实现，供 consulting-partners 专家团的测算顾问（valuation-modeler）使用。

核心思路：一个测算模型通常依赖多个假设（增长率、折现率、渗透率、单价等）。
本工具对每个假设做单变量扰动，观察目标指标（如股权价值、IRR）在什么阈值下会
从"结论成立"翻转为"结论不成立"，从而识别出真正的致命假设——而不是笼统地说
"存在不确定性"。

用法示例见 __main__ 部分，用户需要提供一个可调用的估值函数 (model_fn)，
它接受一个假设字典并返回一个数值指标。
"""

import argparse
import json


def flip_test(model_fn, base_assumptions: dict, decision_threshold: float,
              direction: str = "above", step_pct: float = 0.05, max_steps: int = 20):
    """
    对 base_assumptions 中的每个假设做单变量扰动，寻找翻转阈值。

    model_fn: callable(dict) -> float，输入假设字典，输出目标指标（如股权价值/IRR）
    decision_threshold: 决策的临界值，例如 IRR 需要 > 12% 才算"值得投资"
    direction: "above" 表示指标需要高于阈值才算通过；"below" 表示需要低于阈值
    step_pct: 每步扰动的比例幅度
    max_steps: 最多扰动多少步（防止无限循环）
    """
    base_value = model_fn(base_assumptions)
    base_pass = (base_value > decision_threshold) if direction == "above" else (base_value < decision_threshold)

    results = {}
    for key, base_val in base_assumptions.items():
        if not isinstance(base_val, (int, float)):
            continue

        flip_found = False
        flip_value = None
        flip_step = None

        # 按 step_pct 逐步恶化该假设（增长率类假设调低，成本/折现率类假设调高——
        # 这里采用通用做法：同时尝试增大和减小两个方向，找到较近的翻转点）
        for direction_sign in (-1, 1):
            for step in range(1, max_steps + 1):
                trial_assumptions = dict(base_assumptions)
                trial_val = base_val * (1 + direction_sign * step_pct * step)
                trial_assumptions[key] = trial_val
                trial_metric = model_fn(trial_assumptions)
                trial_pass = (trial_metric > decision_threshold) if direction == "above" else (trial_metric < decision_threshold)

                if trial_pass != base_pass:
                    flip_found = True
                    flip_value = trial_val
                    flip_step = direction_sign * step
                    break
            if flip_found:
                break

        results[key] = {
            "base_value": base_val,
            "base_metric": round(base_value, 4),
            "flip_value": round(flip_value, 4) if flip_value is not None else None,
            "flip_pct_change": round(flip_step * step_pct, 4) if flip_step is not None else None,
            "is_fragile": flip_found and abs(flip_step or 999) <= 3,  # 3步以内翻转视为脆弱假设
        }

    # 按翻转所需扰动幅度从小到大排序——扰动越小就能翻转的，越是致命假设
    ranked = sorted(
        [(k, v) for k, v in results.items() if v["flip_value"] is not None],
        key=lambda kv: abs(kv[1]["flip_pct_change"])
    )

    return {
        "base_metric": round(base_value, 4),
        "base_decision": "通过" if base_pass else "不通过",
        "per_assumption": results,
        "most_fragile_assumption": ranked[0][0] if ranked else None,
        "fragility_ranking": [k for k, _ in ranked],
    }


def print_report(report: dict):
    print(f"基准结果：{report['base_metric']}（{report['base_decision']}）\n")
    print("=== 逐个假设翻转测试 ===")
    for key, info in report["per_assumption"].items():
        flag = "⚠️ 脆弱" if info["is_fragile"] else ""
        print(f"- {key}: 基准值={info['base_value']}, "
              f"翻转所需变动={info['flip_pct_change']}, "
              f"翻转后取值={info['flip_value']} {flag}")

    print(f"\n最致命假设：{report['most_fragile_assumption']}")
    print(f"脆弱度排序（越靠前越容易翻转结论）：{report['fragility_ranking']}")


# ---------------- 示例：简化单位经济学模型 ----------------
def _example_unit_economics_model(assumptions: dict) -> float:
    """
    示例模型：简化的 LTV/CAC 比值计算。
    assumptions 需要包含: arpu(月均客单价), gross_margin(毛利率),
    churn_rate(月流失率), cac(获客成本)
    """
    arpu = assumptions["arpu"]
    gross_margin = assumptions["gross_margin"]
    churn_rate = assumptions["churn_rate"]
    cac = assumptions["cac"]

    if churn_rate <= 0:
        return float("inf")

    ltv = (arpu * gross_margin) / churn_rate
    return ltv / cac if cac else float("inf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="假设翻转测试 —— 找出模型的致命假设")
    parser.add_argument("--example", action="store_true", help="运行内置的单位经济学示例")
    parser.add_argument("--assumptions-json", help="自定义假设的 JSON 文件路径，如 {\"arpu\": 100, ...}")
    parser.add_argument("--threshold", type=float, default=3.0, help="决策阈值，示例中 LTV/CAC 常用 3.0 作为健康基准")
    args = parser.parse_args()

    if args.example or not args.assumptions_json:
        base_assumptions = {"arpu": 200.0, "gross_margin": 0.70, "churn_rate": 0.05, "cac": 800.0}
        report = flip_test(
            model_fn=_example_unit_economics_model,
            base_assumptions=base_assumptions,
            decision_threshold=args.threshold,
            direction="above",
        )
        print_report(report)
    else:
        with open(args.assumptions_json, "r", encoding="utf-8") as f:
            base_assumptions = json.load(f)
        print("⚠️ 自定义模型需要在脚本中实现对应的 model_fn，本 CLI 仅提供示例演示。")
        print("请参考 _example_unit_economics_model 的写法，将真实模型函数接入 flip_test()。")
