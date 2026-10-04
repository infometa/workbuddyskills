#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MBTI 职业性格测评 44 题评分脚本。

报告文案来源：本地 references 文件 `references/mbti.md`，文件内按 H2 标题切分为 3 段，每段为一段散文说明 + 一个 ```json 代码块：
  - ## 题库                (44 题：id/question/prompt/options[].dimension)
  - ## 16 型人格档案       (16 型档案：name/proportion/description/advantages/disadvantages/careers)
  - ## 维度对详情          (4 维度对 + 每对的 E/I/S/N/T/F/J/P 两端详情)

题库来源：references/mbti.md 的 `## 题库` 段。

文件形态（二选一，均受支持）：
  A. 单文件模式（默认）：`--references-path` 指向一个含全部 3 个 H2 段的 mbti.md；
  B. 多文件拆分模式：可选用 `--questions-path` / `--profiles-path` / `--dimensions-path`
     分别指定 3 个独立 md 文件（每个文件内仍须保留对应的 H2 标题与
     ```json 代码块，解析锚点不变）。任意一个拆分路径被指定即进入多文件模式，未指定的
     section 仍从 `--references-path` 读取；若多文件模式下省略 `--references-path`，
     未指定的 section 会报错。

算法对齐：
  1) 按 dimension 字母计数（E/I/S/N/T/F/J/P 各 +1）
  2) 维度对内计算百分比（保留两位小数 ROUND_HALF_UP）
  3) 取百分比高的一端为结果字母（相等取 option1）
  4) 按 EI -> SN -> TF -> JP 拼出 dominant_type
  5) display_score = 4 个胜出端百分比的平均（保留整数）

确定性保证：相同 answers 必产生相同 byte-equal JSON：
  - 无随机数、无时间戳、无外部网络/DB 依赖；
  - 所有文案均从本地 references 查表，模型不得自行撰写；
  - 浮点运算走 decimal.ROUND_HALF_UP，与 Java BigDecimal.ROUND_HALF_UP 一致；
  - 输出字段顺序固定（dict 按 insertion order 序列化，Python 3.7+ 保证）。
"""
import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DEFAULT_BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCES_PATH = DEFAULT_BASE_DIR / "references" / "mbti.md"
# 多文件形态（形态 B）下各 section 对应的独立文件名，未指定路径时按此自动加载
DEFAULT_FILE_MAP = {
    "questions": "questions.md",
    "profiles": "profiles.md",
    "dimensions": "dimensions.md",
}
# H2 标题作为 md 文件内 3 段 JSON 数据的锚点；改名会破坏脚本解析，禁止改名。
SECTION_QUESTIONS = "题库"
SECTION_ROLE_PROFILES = "16 型人格档案"
SECTION_DIMENSION_DETAILS = "维度对详情"

# 4 对维度对，固定顺序：EI -> SN -> TF -> JP。
# option1 为 >= 判断时胜出的一端（即 E/S/T/J）。
DIMENSION_PAIRS = [
    {"pair": "EI", "option1": "E", "option2": "I", "name1": "外倾", "name2": "内倾", "label": "外倾-内倾"},
    {"pair": "SN", "option1": "S", "option2": "N", "name1": "实感", "name2": "直觉", "label": "实感-直觉"},
    {"pair": "TF", "option1": "T", "option2": "F", "name1": "思维", "name2": "情感", "label": "思维-情感"},
    {"pair": "JP", "option1": "J", "option2": "P", "name1": "判断", "name2": "知觉", "label": "判断-知觉"},
]

# 展示顺序（唯一权威源，与 SKILL.md §3.2.1 的 display_pos_to_real_id 映射表同源，禁止改动）：
# 四段重排后的题号序列——视觉位置 1→44 依次对应序列下标 0→43 的真实题号 id。
# 每段最后一道为该维度的"复盘题"（id 41/42/43/44）。
DISPLAY_ORDER = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 41,          # EI 段（复盘题 id=41）
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 42,  # SN 段（复盘题 id=42）
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 43,  # TF 段（复盘题 id=43）
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 44,  # JP 段（复盘题 id=44）
]
assert len(DISPLAY_ORDER) == 44, "DISPLAY_ORDER 必须恰好 44 项"
assert sorted(DISPLAY_ORDER) == list(range(1, 45)), "DISPLAY_ORDER 必须是 1..44 的排列（不得重复/缺失）"

# 视觉位置(str) -> 真实题号 id(str) 的权威映射，由 DISPLAY_ORDER 派生
DISPLAY_POS_TO_REAL_ID = {str(i + 1): str(rid) for i, rid in enumerate(DISPLAY_ORDER)}


def load_md_section(md_path, section_title):
    """从合并后的 references/mbti.md 中按 H2 标题切出指定段，提取 json 代码块并解析。

    解析规则：
      1. 按行扫描，定位以 `## {section_title}` 开头的行作为段起点；
      2. 从段起点之后找到第一个 ```json 代码块的开 fence（```json）与对应的闭 fence（```）；
      3. 提取 fence 之间的文本作为 JSON 原文，json.loads 解析为 Python 对象返回。

    任意一步失败均抛 ValueError，调用方负责报错说明。
    """
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    header_prefix = "## " + section_title
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == header_prefix:
            start_idx = i
            break
    if start_idx is None:
        raise ValueError("在 md 文件中未找到 H2 段：## " + section_title)
    # 在 start_idx 之后找 ```json fence
    open_fence_idx = None
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip() == "```json":
            open_fence_idx = j
            break
        # 遇到下一个 H2 段说明本段无代码块
        if lines[j].startswith("## "):
            break
    if open_fence_idx is None:
        raise ValueError("段 ## " + section_title + " 内未找到 ```json 代码块")
    # 找闭 fence
    close_fence_idx = None
    for k in range(open_fence_idx + 1, len(lines)):
        if lines[k].strip() == "```":
            close_fence_idx = k
            break
    if close_fence_idx is None:
        raise ValueError("段 ## " + section_title + " 内 ```json 代码块未闭合")
    body = "\n".join(lines[open_fence_idx + 1:close_fence_idx])
    return json.loads(body)


def load_questions(md_path):
    """题库：questions 数组（44 题）。"""
    return load_md_section(md_path, SECTION_QUESTIONS)


def build_role_profiles(items):
    """16 型档案 list，按 type 字段建索引字典。"""
    return {item["type"].upper(): item for item in items}


def build_dimension_details(items):
    """维度对详情 list，按 dimension 字段（如 EI）建索引字典。

    每个维度对象内含 detail[]，按 option（E/I/...）建二级索引。
    """
    index = {}
    for d in items:
        dim = d["dimension"].upper()
        detail_map = {detail["option"].upper(): detail for detail in d.get("detail", [])}
        index[dim] = {"object": d, "detail": detail_map}
    return index


def normalize_answer(value):
    """把外部传入作答值归一化为 'A' 或 'B'；未识别返回空串。

    行为对齐：合法 A/B 直通；同时接受 Y/N/1/2 兼容前端可能的变体。
    """
    if value is None:
        return ""
    s = str(value).strip().upper()
    mapping = {"Y": "A", "YES": "A", "TRUE": "A", "1": "A",
               "N": "B", "NO": "B", "FALSE": "B", "2": "B"}
    if s in mapping:
        return mapping[s]
    if s == "A" or s == "B":
        return s
    return ""


def remap_display_answers(answers):
    """把卡片回传的视觉位置键 JSON remap 为真实题号 id 键 JSON。

    视觉位置（display position）是学员在卡片上看到的顺序号 1→44（数组下标+1），
    与题库真实 id 的映射以 DISPLAY_ORDER 为唯一权威源（与 SKILL.md §3.2.1 同源）。

    内置校验（任一失败抛 ValueError，调用方应拒绝评分）：
      1. 输入必须是 JSON 对象（dict）；
      2. 键必须恰好是视觉位置 1..44 全集（缺一/多一/含非法键均报错）；
      3. 全部值 normalize 后必须为 A/B；
      4. remap 后键集为 1..44 真实 id 全集（由 DISPLAY_ORDER 的排列性构造保证）。

    返回 remap 后 {真实id(str): 'A'/'B'}。
    """
    if not isinstance(answers, dict):
        raise ValueError("答案必须是 JSON 对象（dict），收到：" + type(answers).__name__)

    valid_keys = set(DISPLAY_POS_TO_REAL_ID.keys())
    actual_keys = set(answers.keys())
    if actual_keys != valid_keys:
        missing = sorted(valid_keys - actual_keys, key=int)
        extra = sorted(actual_keys - valid_keys, key=int)
        raise ValueError(
            "答案键不合法：必须恰好提交视觉位置 1..44 共 44 键（值 A/B）。"
            "缺失键=" + (",".join(missing) if missing else "无")
            + "；多余键=" + (",".join(extra) if extra else "无")
        )

    remapped = {}
    for pos_key, value in answers.items():
        real_key = DISPLAY_POS_TO_REAL_ID[pos_key]
        ans = normalize_answer(value)
        if not ans:
            raise ValueError(
                f"视觉位置 {pos_key}（真实 id {real_key}）答案不合法：{value!r}，必须为 A 或 B"
            )
        remapped[real_key] = ans
    return remapped


def round2(num):
    """两位小数四舍五入，与 Java BigDecimal.ROUND_HALF_UP 一致。"""
    return float(Decimal(str(num)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_scores(answers, questions, role_profiles, dimension_details):
    """主评分函数。

    参数：
      answers: {题目id(str): 'A'/'B'} 用户作答
      questions: 题库 questions 数组（含 id / options[].dimension）
      role_profiles: {TYPE_UPPER: {...}} 16 型档案字典
      dimension_details: {"EI": {"object":..., "detail":{"E":...,"I":...}}} 维度详情字典
    """
    counts = {dim: 0 for pair in DIMENSION_PAIRS for dim in (pair["option1"], pair["option2"])}
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
                dim = opt.get("dimension")
                if dim in counts:
                    counts[dim] += 1
                break

    total_questions = len(questions)
    answered_count = len(answered_ids)
    status = "completed" if answered_count >= total_questions else "incomplete"

    pair_results = []
    result_letters = []
    dominant_percents = []
    for pair in DIMENSION_PAIRS:
        o1, o2 = pair["option1"], pair["option2"]
        s1, s2 = counts[o1], counts[o2]
        total = s1 + s2
        if total == 0:
            p1, p2 = 0.0, 0.0
            result = None
        else:
            p1 = round2(s1 * 100.0 / total)
            p2 = round2(s2 * 100.0 / total)
            # 对齐规则：>= 取 option1（E/S/T/J）
            result = o1 if s1 >= s2 else o2
        if result is not None:
            result_letters.append(result)
            dominant_percents.append(p1 if result == o1 else p2)

        # 维度对详情：从 references/mbti.md 的 ## 维度对详情 段查表
        dim_pair_key = pair["pair"]
        dim_obj_entry = dimension_details.get(dim_pair_key, {})
        dim_obj = dim_obj_entry.get("object", {}) if dim_obj_entry else {}
        detail_map = dim_obj_entry.get("detail", {}) if dim_obj_entry else {}

        def _detail_for(letter):
            d = detail_map.get(letter, {})
            return {
                "name": d.get("title"),
                "feature": d.get("feature"),
                "traits": d.get("traits"),
                "characteristics": d.get("characteristics"),
            }

        winner_detail = _detail_for(result) if result else {}

        pair_results.append({
            "pair": pair["pair"],
            "label": pair["label"],
            "option1": o1, "name1": pair["name1"], "score1": s1, "percent1": p1,
            "option2": o2, "name2": pair["name2"], "score2": s2, "percent2": p2,
            "result": result,
            "result_name": winner_detail.get("name"),
            "result_feature": winner_detail.get("feature"),
            "result_traits": winner_detail.get("traits"),
            "result_characteristics": winner_detail.get("characteristics"),
            "option1_detail": _detail_for(o1),
            "option2_detail": _detail_for(o2),
            "dimension_name": dim_obj.get("name"),
            "dimension_description": dim_obj.get("description"),
            "dimension_prompt": dim_obj.get("prompt"),
        })

    # 按 EI -> SN -> TF -> JP 拼接；任一维度对缺数据则 dominant_type 为 None
    dominant_type = "".join(result_letters) if len(result_letters) == 4 else None

    # display_score = 4 个胜出端百分比的平均（保留整数）
    if dominant_percents:
        display_score = int(Decimal(str(sum(dominant_percents) / len(dominant_percents)))
                            .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    else:
        display_score = 0

    # 角色档案：从 references/mbti.md 的 ## 16 型人格档案 段查表
    role_detail = None
    if dominant_type and dominant_type in role_profiles:
        rp = role_profiles[dominant_type]
        role_detail = {
            "type": dominant_type,
            "name": rp.get("name"),
            "proportion": rp.get("proportion"),
            "description": rp.get("description"),
            "advantages": rp.get("advantages"),
            "disadvantages": rp.get("disadvantages"),
            "careers": rp.get("careers"),
        }

    # 固定模板的总结与职业推荐数组
    analysis = None
    if dominant_type and role_detail:
        letters_str = "、".join(result_letters)
        role_name = role_detail.get("name") or ""
        careers_str = role_detail.get("careers") or ""
        # careers 是顿号分隔的字符串，按顿号切分为数组，顺序固定
        careers_arr = [c.strip() for c in careers_str.split("、") if c.strip()]
        analysis_summary = (
            f"用户在 {letters_str} 四个维度胜出，人格类型为 {dominant_type}（{role_name}），"
            f"适合 {('、'.join(careers_arr[:5]) + ' 等') if careers_arr else ''}方向。"
        )
        analysis = {
            "summary": analysis_summary,
            "recommendations": careers_arr,
        }

    result = {
        "assessment_id": "MBTI-44-001",
        "assessment_name": "MBTI 职业性格测评",
        "status": status,
        "answered_count": answered_count,
        "total_questions": total_questions,
        "dimension_counts": counts,
        "dimension_pairs": pair_results,
        "dominant_type": dominant_type,
        "display_score": display_score,
        "max_score": 100,
        "role_detail": role_detail,
        "analysis": analysis,
    }
    if status == "incomplete":
        result["missing_questions"] = [
            str(q.get("id")) for q in questions
            if str(q.get("id")) not in answered_ids
        ]
    return result


def main():
    parser = argparse.ArgumentParser(description="MBTI 职业性格测评 44 题简版评分脚本")
    parser.add_argument("--answers", default=None,
                        help='（二选一）真实题号 id 键 JSON，例如 {"1":"A","2":"B"}，按题库 id 直接评分；仅测试/内部场景使用')
    parser.add_argument("--display-answers", default=None,
                        help='（二选一，推荐）卡片回传的视觉位置键 JSON，例如 {"1":"A","2":"B",...,"44":"B"}；脚本按 DISPLAY_ORDER 自动 remap 为真实 id 并内置 44 键/A-B 校验，任一校验失败直接报错不评分')
    parser.add_argument("--references-path", default=None,
                        help="（可选）合并后的 references/mbti.md 路径，含全部 3 个 H2 段。省略时自动加载多文件形态：questions.md / profiles.md / dimensions.md")
    parser.add_argument("--questions-path", default=None,
                        help="多文件拆分模式：仅含 `## 题库` 段的独立 md 文件路径（可选）")
    parser.add_argument("--profiles-path", default=None,
                        help="多文件拆分模式：仅含 `## 16 型人格档案` 段的独立 md 文件路径（可选）")
    parser.add_argument("--dimensions-path", default=None,
                        help="多文件拆分模式：仅含 `## 维度对详情` 段的独立 md 文件路径（可选）")
    parser.add_argument("--compact", action="store_true",
                        help="（可选）紧凑输出：JSON 不带缩进，减小输出体积（默认带缩进便于阅读）")
    args = parser.parse_args()

    if bool(args.answers) == bool(args.display_answers):
        raise SystemExit("必须且只能提供 --answers 或 --display-answers 其中之一"
                         "（--display-answers 为推荐用法：脚本自动 remap 视觉位置→真实 id 并校验）")

    raw_answers = args.display_answers if args.display_answers is not None else args.answers
    try:
        answers = json.loads(raw_answers)
    except json.JSONDecodeError as exc:
        raise SystemExit("答案格式错误：" + str(exc))

    if args.display_answers is not None:
        try:
            answers = remap_display_answers(answers)
        except ValueError as exc:
            raise SystemExit("remap 校验失败，拒绝评分：" + str(exc))

    md_path = Path(args.references_path) if args.references_path else None
    if md_path is not None and not md_path.exists():
        raise SystemExit("references 文件不存在：" + str(md_path))

    # 3 个 section 的来源优先级：独立拆分路径 > 单文件 --references-path > 默认多文件（形态 B）
    section_sources = [
        ("questions", SECTION_QUESTIONS, args.questions_path),
        ("profiles", SECTION_ROLE_PROFILES, args.profiles_path),
        ("dimensions", SECTION_DIMENSION_DETAILS, args.dimensions_path),
    ]
    loaded = {}
    for key, section_title, custom_path in section_sources:
        if custom_path:
            src = Path(custom_path)
        elif md_path is not None:
            src = md_path
        else:
            src = DEFAULT_BASE_DIR / "references" / DEFAULT_FILE_MAP[key]
        if not src.exists():
            raise SystemExit(f"references 文件不存在（section: {section_title}）：{src}")
        loaded[key] = load_md_section(src, section_title)

    questions = loaded["questions"]
    role_profiles = build_role_profiles(loaded["profiles"])
    dimension_details = build_dimension_details(loaded["dimensions"])

    result = calculate_scores(answers, questions, role_profiles, dimension_details)
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))


if __name__ == "__main__":
    main()
