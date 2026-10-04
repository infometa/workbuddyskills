"""行业分析输出校验脚本（沙箱执行）.

校验 industry.json 是否符合 output-spec.md 的 schema。
LLM 写入文件后应调用本脚本自检。

用法：
    python3 verify.py /workspace/industry/industry.json
"""

import json
import sys
import os


REQUIRED_SECTIONS = ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"]

SECTION_FIELDS = {
    "e1": ["summary", "marketRows", "segments", "evidence"],
    "e2": ["summary", "rows", "insights", "evidence"],
    "e3": ["summaryText", "judgments", "evidence"],
    "e4": ["summaryText", "rows", "insights", "evidence"],
    "e5": ["rating", "concentration", "competitors", "insights", "evidence"],
    "e6": ["judgments"],
    "e7": ["fields", "insights"],
    "e8": ["upstream", "downstream", "insights"],
}

VALID_INSIGHT_TYPES = {"ok", "warn", "info", "risk"}
VALID_VARIANTS = {"primary", "success", "warning", "default"}


def verify(data: dict) -> list:
    """校验数据，返回错误列表."""
    errors = []

    # 1. 必需 section
    for section in REQUIRED_SECTIONS:
        if section not in data:
            errors.append(f"缺失 section: {section}")
            continue
        section_data = data[section]
        if not isinstance(section_data, dict):
            errors.append(f"{section} 不是对象")
            continue

        # 2. 必需字段
        for field in SECTION_FIELDS.get(section, []):
            if field not in section_data:
                errors.append(f"{section}.{field} 缺失")

        # 3. evidence 校验（E1-E5 必须有）
        if section in ("e1", "e2", "e3", "e4", "e5"):
            evidence = section_data.get("evidence", [])
            if not isinstance(evidence, list) or len(evidence) == 0:
                errors.append(f"{section}.evidence 不能为空")

        # 4. insights/judgments type 校验
        for field in ("insights", "judgments"):
            items = section_data.get(field, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    item_type = item.get("type", "")
                    if item_type and item_type not in VALID_INSIGHT_TYPES:
                        errors.append(f"{section}.{field}[{i}].type 无效: {item_type}")

        # 5. summary variant 校验
        summary = section_data.get("summary", [])
        if isinstance(summary, list):
            for i, item in enumerate(summary):
                variant = item.get("variant", "")
                if variant and variant not in VALID_VARIANTS:
                    errors.append(f"{section}.summary[{i}].variant 无效: {variant}")

    # 6. E5 competitors 必须包含标的企业
    e5 = data.get("e5", {})
    competitors = e5.get("competitors", [])
    if isinstance(competitors, list):
        has_target = any(c.get("isTarget") for c in competitors)
        if not has_target:
            errors.append("e5.competitors 缺少标的企业（isTarget: true）")

    return errors


def main() -> None:
    """主入口."""
    if len(sys.argv) < 2:
        filepath = "/workspace/industry/industry.json"
    else:
        filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(json.dumps({"valid": False, "errors": [f"文件不存在: {filepath}"]}, ensure_ascii=False))
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps({"valid": False, "errors": [f"JSON 解析失败: {e}"]}, ensure_ascii=False))
        sys.exit(1)

    errors = verify(data)
    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "sections_found": [s for s in REQUIRED_SECTIONS if s in data],
    }
    print(json.dumps(result, ensure_ascii=False))

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
