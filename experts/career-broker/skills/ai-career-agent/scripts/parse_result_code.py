#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_result_code.py
解析 DNA 结果码 → 结构化 JSON。

格式：
    DNA:XXX-YY/ZZ|A:TEC8CHL7ENT5MGT4AUT3SER3SEC2LIF1|S:CR4AN3CN2TC2SY1EM0|P:B2.5O4.0E3.5

调用：
    python parse_result_code.py "DNA:TCA-CR/AN|A:TEC8...|..."
"""
import argparse, json, re, sys


ANCHOR_NAMES = {
    "TEC": "技术/职能型", "CHL": "挑战型", "ENT": "创业型", "MGT": "管理型",
    "AUT": "自主/独立型", "SER": "服务/奉献型", "SEC": "安全/稳定型", "LIF": "生活方式型",
}
STYLE_NAMES = {
    "CR": "创造力", "AN": "分析力", "CN": "连接力",
    "TC": "协作力", "SY": "系统力", "EM": "共情力",
}
PSY_NAMES = {"B": "倦怠指数", "O": "开放性", "E": "自我效能感"}


def parse_section(section: str, code_len: int = 3) -> dict:
    """
    A:TEC8CHL7ENT5... 或 S:CR4AN3...
    code_len = 3（A 段）/ 2（S 段）
    """
    pattern = rf"([A-Z]{{{code_len}}})(\d+)"
    return {m.group(1): int(m.group(2)) for m in re.finditer(pattern, section)}


def parse_psy(section: str) -> dict:
    """ P:B2.5O4.0E3.5 """
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"([BOE])(\d+\.\d)", section)}


def parse(code: str) -> dict:
    if not code or not code.startswith("DNA:"):
        raise ValueError("结果码必须以 DNA: 开头")
    parts = code.split("|")
    if len(parts) != 4:
        raise ValueError(f"结果码格式不对，应该有 4 段（DNA / A / S / P），实际 {len(parts)} 段")

    dna_part = parts[0].replace("DNA:", "").strip()
    a_part = parts[1].replace("A:", "")
    s_part = parts[2].replace("S:", "")
    p_part = parts[3].replace("P:", "")

    # 三字母代码 - 双字母变体/双字母亚型
    m = re.match(r"([A-Z]{3})-([A-Z]{2})/([A-Z]{2})", dna_part)
    if not m:
        raise ValueError(f"DNA 代码格式不对: {dna_part}（应该是 XXX-YY/ZZ）")
    main_code, variant, subtype = m.group(1), m.group(2), m.group(3)

    anchors = parse_section(a_part, 3)
    styles = parse_section(s_part, 2)
    psy = parse_psy(p_part)

    # 排序
    anchors_sorted = sorted(anchors.items(), key=lambda x: -x[1])
    styles_sorted = sorted(styles.items(), key=lambda x: -x[1])

    return {
        "raw_code": code,
        "main_code": main_code,
        "variant": variant,
        "subtype": subtype,
        "anchors": [{"code": k, "name": ANCHOR_NAMES.get(k, k), "score": v}
                    for k, v in anchors_sorted],
        "anchors_top3": [k for k, _ in anchors_sorted[:3]],
        "styles": [{"code": k, "name": STYLE_NAMES.get(k, k), "score": v}
                   for k, v in styles_sorted],
        "styles_top2": [k for k, _ in styles_sorted[:2]],
        "psy_state": {k: {"name": PSY_NAMES.get(k), "score": v} for k, v in psy.items()},
        "psy_burnout_alert": psy.get("B", 0) >= 3.5,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code", help="DNA 结果码")
    args = ap.parse_args()
    try:
        result = parse(args.code)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e),
                          "tips": "格式：DNA:XXX-YY/ZZ|A:TEC8...|S:CR4...|P:B2.5..."},
                         ensure_ascii=False))
        sys.exit(2)
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
