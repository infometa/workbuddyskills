#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生涯测评 10 题简版评分脚本。

题库来源：references/questions.md
文案来源：references/tag_profiles.md（6 个生涯方向 × 4 段文案）

算法对齐（与需求方约定）：
  1) 共 10 题，6 个生涯方向标签：A=公考/央国企，B=自由职业，C=打工人，D=留学，E=保研/考研，F=躺平
  2) 同学完成答题后，统计作答中各标签出现次数，数量最多的标签即为结果
  3) 若最高分标签有多个，按以下优先级展示：
       保研/考研(E) > 公考/央国企(A) > 留学(D) > 打工人(C) > 自由职业(B) > 躺平(F)
  4) 文案从 references/tag_profiles.md 查表，固定 4 段（section_1 ~ section_4），
     模型不得自行撰写、改写或省略。

确定性保证：相同 answers 必产生相同 byte-equal JSON：
  - 无随机数、无时间戳、无外部网络/DB 依赖；
  - 所有文案均从本地数据文件（.md / .json）查表；
  - 浮点运算走 decimal.ROUND_HALF_UP；
  - 输出字段顺序固定（dict 按 insertion order 序列化，Python 3.7+ 保证）。
"""
import argparse
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DEFAULT_BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_QUESTIONS_PATH = DEFAULT_BASE_DIR / "references" / "questions.md"
DEFAULT_TAG_PROFILES_PATH = DEFAULT_BASE_DIR / "references" / "tag_profiles.md"

# 6 个生涯方向标签，固定顺序：A 公考/央国企, B 自由职业, C 打工人, D 留学, E 保研/考研, F 躺平
TAGS = ["A", "B", "C", "D", "E", "F"]

# 平局优先级：保研/考研(E) > 公考/央国企(A) > 留学(D) > 打工人(C) > 自由职业(B) > 躺平(F)
# 数值越小优先级越高（1 为最高）
PRIORITY = {"E": 1, "A": 2, "D": 3, "C": 4, "B": 5, "F": 6}

# 标签 → 中文名映射（与 questions.md 的标签说明表一致）
TAG_NAMES = {
    "A": "公考/央国企",
    "B": "自由职业",
    "C": "打工人",
    "D": "留学",
    "E": "保研/考研",
    "F": "躺平",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def parse_md_fields(lines, i):
    """从第 i 行起解析连续的 "- key: value" / "- key: |" / "- key: |-" 字段行。

    返回 (fields, 下一行索引)。literal block 内容缩进 4 空格：
      - "- key: |"  → clip 语义：内容末尾恰好保留一个换行
      - "- key: |-" → strip 语义：内容末尾无换行
    块内空行保留为 "\n"；空行若后接非缩进行则视为块结束。
    """
    fields = {}
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        if not s.startswith("- "):
            break
        body = s[2:].strip()
        key, _, val = body.partition(":")
        key = key.strip()
        val = val.strip()
        if val in ("|", "|-"):
            block = []
            j = i + 1
            while j < n:
                ln = lines[j]
                if ln.startswith("    "):
                    block.append(ln[4:])
                    j += 1
                elif ln.strip() == "":
                    block.append("")
                    j += 1
                else:
                    break
            while block and block[-1] == "":
                block.pop()
            content = "\n".join(block)
            if val == "|":
                content += "\n"
            fields[key] = content
            i = j
        else:
            fields[key] = val
            i += 1
    return fields, i


def load_questions(path):
    """读取题库。.md 走 Markdown 解析；.json 走原 JSON 解析（向后兼容）。

    返回 questions 数组，每项含 id / question / prompt / options。
    """
    p = Path(path)
    if p.suffix.lower() == ".json":
        payload = load_json(p)
        return payload.get("questions", []) if isinstance(payload, dict) else payload

    lines = read_text(p).split("\n")
    questions = []
    i = 0
    n = len(lines)
    while i < n:
        m = re.match(r"^##\s+题目\s+(\d+)\s*$", lines[i].strip())
        if not m:
            i += 1
            continue
        qid = int(m.group(1))
        question = prompt = None
        options = []
        j = i + 1
        while j < n:
            t = lines[j].strip()
            if t.startswith("## "):
                break
            if t.startswith("**题干**"):
                question = t.split("**题干**", 1)[1].strip().lstrip("：:").strip()
            elif t.startswith("**提示语**"):
                prompt = t.split("**提示语**", 1)[1].strip().lstrip("：:").strip()
            elif t.startswith("|"):
                cells = [c.strip() for c in t.strip("|").split("|")]
                if len(cells) >= 3 and cells[0] in TAGS:
                    options.append({"option": cells[0], "content": cells[1], "tag": cells[2]})
            j += 1
        if question is not None and prompt is not None and options:
            questions.append({"id": qid, "question": question, "prompt": prompt, "options": options})
        i = j
    return questions


def load_tag_profiles(path):
    """读取生涯方向档案。.md 走 Markdown 解析；.json 走原 JSON 解析（向后兼容）。

    返回 {TAG_UPPER: {...}} 字典，每个档案含 tag / name / priority /
    section_1_title / section_1 ~ section_4_title / section_4。
    """
    p = Path(path)
    if p.suffix.lower() == ".json":
        items = load_json(p)
        return {item["tag"].upper(): item for item in items}

    lines = read_text(p).split("\n")
    profiles = {}
    current = None
    i = 0
    n = len(lines)
    while i < n:
        m = re.match(r"^##\s+([A-F])[：:]\s*(.+)$", lines[i].strip())
        if m:
            if current is not None:
                profiles[current["tag"]] = current
            current = {"tag": m.group(1), "name": m.group(2).strip()}
            i += 1
            continue
        if current is not None:
            fields, ni = parse_md_fields(lines, i)
            if fields:
                if "priority" in fields:
                    fields["priority"] = int(fields["priority"])
                current.update(fields)
                i = ni
                continue
        i += 1
    if current is not None:
        profiles[current["tag"]] = current
    return profiles


def build_tag_profiles(items):
    """tag_profiles 源数据是一个 list，按 tag 字段建索引字典。"""
    return {item["tag"].upper(): item for item in items}


def normalize_answer(value):
    """把外部传入作答值归一化为 'A'-'F'；未识别返回空串。

    合法 A-F 直通；同时接受 1-6 兼容前端可能的数字变体。
    """
    if value is None:
        return ""
    s = str(value).strip().upper()
    num_mapping = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F"}
    if s in num_mapping:
        return num_mapping[s]
    if s in TAGS:
        return s
    return ""


def round2(num):
    """两位小数四舍五入，与 Java BigDecimal.ROUND_HALF_UP 一致。"""
    return float(Decimal(str(num)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_scores(answers, questions, tag_profiles):
    """主评分函数。

    参数：
      answers: {题目id(str): 'A'-'F'} 用户作答
      questions: 题库 questions 数组（含 id / options[].tag）
      tag_profiles: {TAG_UPPER: {...}} 6 个方向档案字典
    """
    counts = {t: 0 for t in TAGS}
    answered_ids = set()

    for q in questions:
        qid = str(q.get("id"))
        if qid not in answers:
            continue
        answered_ids.add(qid)
        ans = normalize_answer(answers[qid])
        if not ans:
            continue
        for opt in q.get("options", []):
            if opt.get("option", "").upper() == ans:
                tag = opt.get("tag")
                if tag in counts:
                    counts[tag] += 1
                break

    total_questions = len(questions)
    answered_count = len(answered_ids)
    status = "completed" if answered_count >= total_questions else "incomplete"

    # 找最高分标签；并列时按 PRIORITY 升序取优先级最高的（数值越小越优先）
    max_count = max(counts.values()) if counts else 0
    if max_count == 0:
        dominant_tag = None
    else:
        candidates = [t for t in TAGS if counts[t] == max_count]
        dominant_tag = min(candidates, key=lambda t: PRIORITY[t])

    # 各标签百分比（保留两位小数 ROUND_HALF_UP）
    tag_stats = []
    for t in TAGS:
        c = counts[t]
        percent = round2(c * 100.0 / total_questions) if total_questions else 0.0
        tag_stats.append({
            "tag": t,
            "name": TAG_NAMES[t],
            "score": c,
            "percent": percent,
        })

    # display_score：胜出标签的百分比（0-100 整数，ROUND_HALF_UP）
    display_score = 0
    if dominant_tag is not None and total_questions:
        display_score = int(Decimal(str(counts[dominant_tag] * 100.0 / total_questions))
                            .quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    # 标签档案：从 tag_profiles 查表
    tag_detail = None
    if dominant_tag is not None and dominant_tag in tag_profiles:
        rp = tag_profiles[dominant_tag]
        tag_detail = {
            "tag": dominant_tag,
            "name": rp.get("name"),
            "priority": rp.get("priority"),
            "section_1_title": rp.get("section_1_title"),
            "section_1": rp.get("section_1"),
            "section_2_title": rp.get("section_2_title"),
            "section_2": rp.get("section_2"),
            "section_3_title": rp.get("section_3_title"),
            "section_3": rp.get("section_3"),
            "section_4_title": rp.get("section_4_title"),
            "section_4": rp.get("section_4"),
        }

    # 固定模板的总结
    analysis = None
    if dominant_tag is not None and tag_detail:
        analysis_summary = (
            f"用户在 10 道题中，{tag_detail['name']} 方向选了 {counts[dominant_tag]} 次（最多），"
            f"生涯测评结果为：{tag_detail['name']}。"
        )
        analysis = {
            "summary": analysis_summary,
            "recommendation": tag_detail.get("name"),
        }

    result = {
        "assessment_id": "SYCP-10-001",
        "assessment_name": "生涯测评（10题简版）",
        "status": status,
        "answered_count": answered_count,
        "total_questions": total_questions,
        "tag_counts": counts,
        "tag_stats": tag_stats,
        "dominant_tag": dominant_tag,
        "dominant_name": TAG_NAMES.get(dominant_tag) if dominant_tag else None,
        "display_score": display_score,
        "max_score": 100,
        "tag_detail": tag_detail,
        "analysis": analysis,
    }
    if status == "incomplete":
        result["missing_questions"] = [
            str(q.get("id")) for q in questions
            if str(q.get("id")) not in answered_ids
        ]
    return result


def main():
    parser = argparse.ArgumentParser(description="生涯测评 10 题简版评分脚本")
    parser.add_argument("--answers", required=True,
                        help='JSON 字符串，例如 {"1":"A","2":"B"}')
    parser.add_argument("--questions-path", default=str(DEFAULT_QUESTIONS_PATH),
                        help="题库文件路径（.md 或 .json）")
    parser.add_argument("--tag-profiles-path", default=str(DEFAULT_TAG_PROFILES_PATH),
                        help="生涯方向档案路径（.md 或 .json）")
    args = parser.parse_args()

    try:
        answers = json.loads(args.answers)
    except json.JSONDecodeError as exc:
        raise SystemExit("答案格式错误：" + str(exc))

    for label, p in (("题库", args.questions_path),
                     ("生涯方向档案", args.tag_profiles_path)):
        if not Path(p).exists():
            raise SystemExit(f"{label}文件不存在：{p}")

    questions = load_questions(args.questions_path)
    tag_profiles = load_tag_profiles(args.tag_profiles_path)

    result = calculate_scores(answers, questions, tag_profiles)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
