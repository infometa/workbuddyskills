
#!/usr/bin/env python3
"""
经营分析校验脚本

验证 Skill 输出的 JSON 是否符合 output-spec.md 定义的 schema。
输入（stdin）：完整的经营分析输出 JSON
输出（stdout）：校验结果 JSON
"""

import json
import sys

REQUIRED_TABS = ["c1_layout", "c2_management", "c3_revenue", "c4_supply",
                 "c5_customer", "c6_tax", "c7_production", "c8_cashflow"]

JUDGMENT_TYPES = {"ok", "warn", "info"}
RISK_LEVELS = {"high", "medium", "low", "note"}
RISK_CATEGORIES = {"经营布局", "管理模式", "营收质量", "供应集中度",
                   "客户集中度", "账税一致", "产销", "流水"}


def validate_judgments(judgments: list, tab: str) -> list:
    """校验 judgments 数组"""
    errors = []
    if not isinstance(judgments, list):
        errors.append(f"{tab}.judgments 必须是数组")
        return errors
    if len(judgments) == 0:
        errors.append(f"{tab}.judgments 不能为空，至少 1 条研判结论")
    for i, j in enumerate(judgments):
        if not isinstance(j, dict):
            errors.append(f"{tab}.judgments[{i}] 必须是对象")
            continue
        if j.get("type") not in JUDGMENT_TYPES:
            errors.append(f"{tab}.judgments[{i}].type 必须是 ok/warn/info")
        if not j.get("text"):
            errors.append(f"{tab}.judgments[{i}].text 不能为空")
    return errors


def validate_risk_points(risk_points: list) -> list:
    """校验 riskPoints 数组"""
    errors = []
    if not isinstance(risk_points, list):
        errors.append("riskPoints 必须是数组")
        return errors
    if len(risk_points) < 3:
        errors.append(f"riskPoints 至少 3 条，当前 {len(risk_points)} 条")
    if len(risk_points) > 8:
        errors.append(f"riskPoints 最多 8 条，当前 {len(risk_points)} 条")
    for i, rp in enumerate(risk_points):
        if rp.get("level") not in RISK_LEVELS:
            errors.append(f"riskPoints[{i}].level 必须是 high/medium/low/note")
        if not rp.get("title"):
            errors.append(f"riskPoints[{i}].title 不能为空")
        if not rp.get("detail"):
            errors.append(f"riskPoints[{i}].detail 不能为空")
        if not rp.get("suggest"):
            errors.append(f"riskPoints[{i}].suggest 不能为空")
    return errors


def validate(data: dict) -> dict:
    """主校验逻辑"""
    errors = []
    warnings = []

    # 检查 riskPoints
    if "riskPoints" not in data:
        errors.append("缺少 riskPoints 字段")
    else:
        errors.extend(validate_risk_points(data["riskPoints"]))

    # 检查各 tab
    null_tabs = []
    for tab in REQUIRED_TABS:
        if tab not in data:
            warnings.append(f"缺少 {tab} 字段")
            null_tabs.append(tab)
        elif data[tab] is None:
            warnings.append(f"{tab} 为 null（材料不足）")
            null_tabs.append(tab)
        else:
            # 检查 source 字段
            if not data[tab].get("source"):
                errors.append(f"{tab}.source 不能为空")
            # 检查 judgments（C2-C8 有 judgments）
            if tab in ["c2_management", "c3_revenue", "c6_tax", "c7_production", "c8_cashflow"]:
                if "judgments" in data[tab]:
                    errors.extend(validate_judgments(data[tab]["judgments"], tab))

    if len(null_tabs) > 4:
        errors.append(f"超过一半的 tab 为 null（{len(null_tabs)}/8），材料严重不足")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "null_tabs": null_tabs,
    }


def main():
    data = json.loads(sys.stdin.read())
    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
