#!/usr/bin/env python3
"""
academic-tutor · render_three_segments.py

装配 + 校验 三段式回复：引导问题 / 关键提示 / 下一步建议。
依据 references/three-segment-rubric.md 的硬约束做 lint。

Usage:
    python3 render_three_segments.py --input reply.json
    python3 render_three_segments.py --input reply.json --markdown   # 顺便输出 markdown
    python3 render_three_segments.py --input reply.json --simplified # 达阈值后的简化模式校验
    python3 render_three_segments.py --input reply.json --profile-anchor-required  # 强校验 anchoring

退出码：
    0 = 通过
    1 = 参数错
    2 = 校验失败
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# ---------- 标准模式硬约束 ----------
MAX_QUESTIONS = 3
MAX_HINTS = 3
MAX_NEXT_STEPS = 3
# 注：本 Skill 自我闭环，不做跨能力跳转 → skill_referrals 永远应为空 / 不存在

# ---------- 简化模式（attempt_count 达阈值后）硬约束 ----------
SIMPLIFIED_MAX_QUESTIONS = 1
SIMPLIFIED_MAX_HINTS = 1
SIMPLIFIED_MAX_TOTAL_CHARS = 200  # 中文字符容差，含 markdown 修饰

# 含完整答案的危险信号（粗启发，不求完美，只求阻断明显错误）
ANSWER_LEAKS = [
    # —— 数学 / 积分 ——
    re.compile(r"=\s*[\-+]?[0-9.]+"),                # = 一个数
    re.compile(r"等于\s*[0-9]+"),
    re.compile(r"答案是"),
    re.compile(r"最终结果"),
    re.compile(r"=\s*\(?\s*\d?\s*[\-+/*]?\s*[a-zA-Z]+\s*\("),  # = arctan( = ln( = sin(...
    re.compile(r"\barctan\s*\("),                    # 直接给 arctan(...)
    re.compile(r"\bln\s*\("),
    re.compile(r"\+\s*C\b"),                         # + C 不定积分常数
    # —— 物理完整公式（牛顿 / 能量 / 电磁）——
    re.compile(r"F\s*=\s*ma\b"),
    re.compile(r"E\s*=\s*mc[²2]"),
    re.compile(r"PV\s*=\s*nRT"),
    re.compile(r"=\s*\\frac"),                       # LaTeX 完整分式（公式塞答）
    # —— 论文段落代写（连续超长段落 = 代写嫌疑）——
    # 匹配单条 hint 中包含中文句号 ≥ 4 个 = 已经写成完整段落
    # 不在 ANSWER_LEAKS 直接匹配，留给 has_paragraph_ghostwrite 单独处理
    # —— 编程完整代码（含 def / function / for/while + 缩进结构）——
    re.compile(r"```[\s\S]+?```", re.MULTILINE),     # 三反引号代码块直接给 = 代写
    re.compile(r"\bdef\s+\w+\s*\(.*\)\s*:"),         # Python def
    re.compile(r"\bfunction\s+\w+\s*\("),            # JS function
    re.compile(r"\bfor\s*\(.+;.+;.+\)\s*\{"),        # C/Java for(;;) {
    re.compile(r"return\s+[^;\s]{4,}"),              # return 一个非平凡表达式
]

# 论文段落代写检测（独立于 ANSWER_LEAKS，因为不是简单正则能搞定）
def has_paragraph_ghostwrite(text: str) -> bool:
    """单条 hint 中 中文句号 ≥ 4 个 且总字数 ≥ 60，视为段落代写。

    注：阈值取 60 是为了覆盖典型中文段落代写——4 个标点意味着 ≥ 4 个完整子句，
    每子句平均 15 字符已是完整论述；hint 应当是片段化提示，超过此密度即代写嫌疑。
    """
    period_count = text.count("。") + text.count(".")
    return period_count >= 4 and len(text) >= 60


# 用户行为动词（next_step 必须含其一）
USER_ACTION_VERBS = [
    "你来", "你写", "你试", "你算", "你画", "你列",
    "试着", "动手", "推一步", "写出", "复述",
    "贴", "发我", "选 A", "选 B",
]


def is_yes_no(question: str) -> bool:
    """简易判断是否真正的 Yes/No 问题（封闭式）。

    规则：
    - 含 "你能 / 你会 / 能不能 / 是不是 / 对不对 / 懂了吗 / 会了吗 / 可以吗"
      且句中**不含**疑问代词（什么 / 怎么 / 哪 / 多少 / 为什么 / 如何）→ 视为 yes/no。
    - 若句子含上述疑问代词 → 仍是开放式（即使句末"吗"也允许）。
    """
    q = question.strip()
    open_markers = ["什么", "怎么", "哪", "多少", "为什么", "如何", "何时", "几"]
    if any(m in q for m in open_markers):
        return False
    closed_patterns = ["懂了吗", "会了吗", "可以吗", "对不对", "是不是", "对吧",
                        "你会吗", "你懂吗", "明白了吗"]
    return any(p in q for p in closed_patterns)


def has_answer_leak(text: str) -> bool:
    for pat in ANSWER_LEAKS:
        if pat.search(text):
            return True
    if has_paragraph_ghostwrite(text):
        return True
    return False


def contains_user_action(text: str) -> bool:
    # AI 自代劳信号 → 立即否定
    ai_substitution = ["我帮你", "我来算", "我直接", "我来给", "我告诉你",
                       "我来写", "我替你"]
    if any(s in text for s in ai_substitution):
        return False
    return any(v in text for v in USER_ACTION_VERBS)


# ---------- Profile Anchoring 检测 ----------
ANCHORING_MARKERS = [
    "你正在学", "你之前学", "你说的", "我们昨天", "我们上次",
    "你这门", "你这个专业", "你这篇", "你的论文", "你开题",
    "结合你",  # 「结合你计算机大三的背景」
    "记得你",
]


def has_anchoring(questions: list[str]) -> bool:
    """段 1 第一句必须命中 anchoring marker 之一。"""
    if not questions:
        return False
    first_q = questions[0].strip()
    return any(m in first_q for m in ANCHORING_MARKERS)


def validate(reply: dict, simplified: bool = False,
             profile_anchor_required: bool = False) -> list[str]:
    issues: list[str] = []

    questions = reply.get("questions") or []
    hints = reply.get("hints") or []
    next_step = reply.get("next_step") or ""

    # 必填字段
    if not isinstance(questions, list):
        issues.append("FIELD_QUESTIONS_NOT_LIST")
    if not isinstance(hints, list):
        issues.append("FIELD_HINTS_NOT_LIST")
    if not isinstance(next_step, str):
        issues.append("FIELD_NEXT_STEP_NOT_STR")

    # 数量（按模式分支）
    if simplified:
        if len(questions) != SIMPLIFIED_MAX_QUESTIONS:
            issues.append(f"SIMPLIFIED_QUESTIONS_MUST_BE_{SIMPLIFIED_MAX_QUESTIONS}")
        if len(hints) != SIMPLIFIED_MAX_HINTS:
            issues.append(f"SIMPLIFIED_HINTS_MUST_BE_{SIMPLIFIED_MAX_HINTS}")
        # 简化模式总字数审计
        total = sum(len(q) for q in questions) + sum(len(h) for h in hints) + len(next_step)
        if total > SIMPLIFIED_MAX_TOTAL_CHARS:
            issues.append(f"SIMPLIFIED_TOTAL_CHARS_OVER_{SIMPLIFIED_MAX_TOTAL_CHARS}")
    else:
        if len(questions) == 0 or len(questions) > MAX_QUESTIONS:
            issues.append(f"QUESTIONS_COUNT_OUT_OF_RANGE_1_{MAX_QUESTIONS}")
        if len(hints) == 0 or len(hints) > MAX_HINTS:
            issues.append(f"HINTS_COUNT_OUT_OF_RANGE_1_{MAX_HINTS}")

    if not next_step.strip():
        issues.append("NEXT_STEP_EMPTY")

    # Skill 自我闭环：禁止任何跨能力跳转字段
    if reply.get("skill_referrals") or reply.get("skill_referral"):
        issues.append("CROSS_SKILL_REFERRAL_FORBIDDEN")

    # 内容质量
    for i, q in enumerate(questions):
        if not isinstance(q, str) or not q.strip():
            issues.append(f"QUESTION_{i}_EMPTY")
            continue
        if is_yes_no(q):
            issues.append(f"QUESTION_{i}_IS_YES_NO")

    for i, h in enumerate(hints):
        if not isinstance(h, str) or not h.strip():
            issues.append(f"HINT_{i}_EMPTY")
            continue
        if has_answer_leak(h):
            issues.append(f"HINT_{i}_CONTAINS_ANSWER")

    # next_step 必含用户行为
    if next_step.strip() and not contains_user_action(next_step):
        issues.append("NEXT_STEP_NOT_ACTIONABLE")

    # Profile anchoring 校验（NEVER 10）
    if profile_anchor_required:
        if not has_anchoring(questions):
            issues.append("PROFILE_ANCHORING_MISSING")

    return issues


def render_markdown(reply: dict) -> str:
    lines = []
    lines.append("**🤔 先想想**")
    for i, q in enumerate(reply.get("questions", []), start=1):
        lines.append(f"{i}. {q.strip()}")
    lines.append("")
    lines.append("**💡 提示（不是答案）**")
    for h in reply.get("hints", []):
        lines.append(f"- {h.strip()}")
    lines.append("")
    lines.append("**👉 下一步**")
    ns = reply.get("next_step", "").strip()
    lines.append(f"- {ns}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="reply JSON 文件")
    p.add_argument("--markdown", action="store_true", help="同时输出 markdown")
    p.add_argument("--strict", action="store_true",
                   help="校验失败时退出码=2（默认仅报告，退出码=0）")
    p.add_argument("--simplified", action="store_true",
                   help="按 NEVER 11 简化模式校验（attempt_count 达阈值后）")
    p.add_argument("--profile-anchor-required", action="store_true",
                   dest="profile_anchor_required",
                   help="按 NEVER 10 强制要求段 1 第一句做 profile anchoring")
    args = p.parse_args()

    path = pathlib.Path(args.input)
    if not path.exists():
        print(f"ERROR: 文件不存在：{path}", file=sys.stderr)
        return 1

    try:
        reply = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON 解析失败：{e}", file=sys.stderr)
        return 1

    issues = validate(reply, simplified=args.simplified,
                      profile_anchor_required=args.profile_anchor_required)
    out = {"ok": len(issues) == 0, "issues": issues}
    if args.markdown:
        out["markdown"] = render_markdown(reply)
    print(json.dumps(out, indent=2, ensure_ascii=False))

    if issues and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
