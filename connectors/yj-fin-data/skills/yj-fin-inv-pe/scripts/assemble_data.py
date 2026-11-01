#!/usr/bin/env python3
"""
yj-fin-inv-pe 输入校验归一器（v1.0）

把"祜·Care及Gangtise合作股权投研 MCP 工具取数 + 外部核验结论与 BP 材料"组装出的报告输入 JSON 做结构校验与归一，
写出 `{公司}_inv_pe_input.json` 供 `generate_report.py` 消费。

职责边界（与生成器严格分工）：
  - **只校验、不编造**：缺列照实标注，绝不补 0；数值型字段若模型误填 0（如 PE=0、市值=0，
    正常不可能是 0）只告警不阻断，因为 0 也可能是真实值——但 PE/市值 0 几乎必为缺失，故告警。
  - **缺失项非零退出并指名**：必填结构（company、valuation.five_dims 含 5 项且每项子键齐全）
    不齐时 exit(1)，把缺了哪些条目逐一打印到 stderr，stdout 不产出路径。
  - **纯 stdlib**，零第三方依赖；stdout 只打产物绝对路径，诊断走 stderr。

必填结构：
  - top-level `company`: 非空字符串
  - `valuation.five_dims`: 长度恰为 5 的列表，每项含 name(str) / score(number∈[0,5]) /
    coef(number∈[-0.5,0.5]) / basis(str) / evidence(str ∈ {高,中,低})
其余（profile / industry / comparable / risks / conclusion / pending …）可选，但建议至少
提供 comparable.peers 或 valuation 以产出有意义报告；全空时仅告警不阻断。

Usage:
    python3 assemble_data.py --input raw.json
    python3 assemble_data.py --input raw.json --output-dir /path/to/out --company 某某科技
    cat raw.json | python3 assemble_data.py   # 从 stdin 读
"""

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import default_skill_output_dir, data_json_filename

REQUIRED_TOP = ("company",)
EVIDENCE_VALUES = ("高", "中", "低")
# 这些数值型字段若为 0 几乎必是"缺失被误填"，仅告警。
ZERO_SUSPECT_KEYS = ("pe", "pb", "ps", "market_cap", "roe", "revenue_growth", "gross_margin")


def _load_input(args) -> dict:
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.load(sys.stdin)


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(data: dict) -> list[str]:
    """返回问题列表（空 = 通过）。"""
    problems: list[str] = []

    if not isinstance(data, dict):
        return ["根节点必须是 JSON 对象"]

    # ① company
    company = data.get("company")
    if not isinstance(company, str) or not company.strip():
        problems.append("缺失/非法必填项：company（应为非空字符串）")

    # ② valuation.five_dims
    val = data.get("valuation")
    if not isinstance(val, dict):
        problems.append("缺失必填项：valuation（对象，含 five_dims）")
    else:
        fd = val.get("five_dims")
        if not isinstance(fd, list):
            problems.append("缺失必填项：valuation.five_dims（列表）")
        else:
            if len(fd) != 5:
                problems.append(
                    f"valuation.five_dims 必须为 5 项（实际 {len(fd)} 项）——"
                    f"五维雷达/打分需技术壁垒/商业化/团队/政策竞争/经营风险 各一项")
            for i, d in enumerate(fd):
                if not isinstance(d, dict):
                    problems.append(f"valuation.five_dims[{i}] 必须是对象")
                    continue
                name = d.get("name")
                score = d.get("score")
                coef = d.get("coef")
                basis = d.get("basis")
                evidence = d.get("evidence")
                if not isinstance(name, str) or not name.strip():
                    problems.append(f"valuation.five_dims[{i}].name 缺失/非法（应为字符串）")
                if not _is_number(score):
                    problems.append(f"valuation.five_dims[{i}].score 缺失/非法（应为数字）")
                elif not (0 <= float(score) <= 5):
                    problems.append(
                        f"valuation.five_dims[{i}].score={score} 超出 [0,5] 范围")
                if not _is_number(coef):
                    problems.append(f"valuation.five_dims[{i}].coef 缺失/非法（应为数字，如 0.30/-0.20）")
                elif not (-0.5 <= float(coef) <= 0.5):
                    problems.append(
                        f"valuation.five_dims[{i}].coef={coef} 超出合理 [-0.5,0.5] 范围")
                if not isinstance(basis, str) or not basis.strip():
                    problems.append(f"valuation.five_dims[{i}].basis 缺失/非法（应为字符串，打分依据）")
                if evidence not in EVIDENCE_VALUES:
                    problems.append(
                        f"valuation.five_dims[{i}].evidence={evidence!r} 非法"
                        f"（应为 {EVIDENCE_VALUES} 之一）")

    # ③ 软建议：至少有一块实质内容
    has_content = any(
        data.get(k) for k in ("profile", "industry", "comparable", "risks", "conclusion"))
    has_val = isinstance(data.get("valuation"), dict) and (
        data["valuation"].get("five_dims") or data["valuation"].get("layers")
        or data["valuation"].get("neutral_base") is not None)
    if not (has_content or has_val):
        problems.append("（建议）报告内容全空：至少提供 comparable.peers / valuation / 任一分析模块")

    return problems


def _warn_suspect_zero(data: dict) -> list[str]:
    """对可比 peer 数值字段里的疑似缺失 0 告警（不阻断）。"""
    warns: list[str] = []
    for i, p in enumerate((data.get("comparable", {}) or {}).get("peers", []) or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name", f"#{i}")
        for k in ZERO_SUSPECT_KEYS:
            v = p.get(k)
            if v == 0:
                warns.append(
                    f"可比 peer「{nm}」的 {k}=0，疑似缺失被误填为 0（如确为 0 可忽略）")
    return warns


def normalize(data: dict) -> dict:
    """仅做无害归一（不补值、不改语义）。当前保留原结构透传，预留扩展位。"""
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="yj-fin-inv-pe 输入校验归一器")
    ap.add_argument("--input", default="", help="原始组装 JSON（缺省从 stdin 读）")
    ap.add_argument("--output-dir", default="", help="输出目录；默认 {工作目录}/company_inv_pe")
    ap.add_argument("--company", default="", help="公司名称（覆盖 JSON 中的 company 作为文件名）")
    args = ap.parse_args()

    try:
        data = _load_input(args)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[FAIL] 无法读取输入 JSON：{e}", file=sys.stderr)
        return 1

    problems = validate(data)
    if problems:
        print("校验未通过，以下必填项缺失或非法：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\n未产出归一 JSON（exit 1）。", file=sys.stderr)
        return 1

    warns = _warn_suspect_zero(data)
    for w in warns:
        print(f"[warn] {w}", file=sys.stderr)

    norm = normalize(data)
    company = args.company or norm.get("company", "标的")
    out_dir = os.path.abspath(args.output_dir or default_skill_output_dir())
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, data_json_filename(company))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(norm, f, ensure_ascii=False, indent=2)

    print(f"[info] 校验通过：{company}（五维 {len(norm.get('valuation', {}).get('five_dims', []))} 项"
          f" / 可比 {len(norm.get('comparable', {}).get('peers', []))} 家"
          f" / 风险 {len(norm.get('risks', []))} 项）", file=sys.stderr)
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
