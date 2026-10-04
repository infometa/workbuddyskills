#!/usr/bin/env python3
"""职业能力倾向测评（85题版）评分脚本。

输入作答：推荐 85 位 A-E 紧凑字符序列（约 85 字符，不触发传输截断）；
        亦兼容旧 JSON 对象（键为题号字符串、值 A-E，约 530 字符，不推荐）。

输出：JSON。17 个能力维度的分数（100 分制）、降序排名、Top N 优势维度
      能力卡片（含 highScoreDesc 解读文案）、总分、答题完成状态、缺失题号（如有）。

报告页：上半部分 Top N 能力维度卡片（highScoreDesc 描述），
        下半部分 17 维度得分条；40 分制原始分换算为 100 分制显示。

确定性：维度固定优先级 = 题库 partList→dimensionList 的自然插入顺序；
        分数相同时按此优先级取靠前者，同一输入多次运行结果一致。
"""
import argparse
import json
from pathlib import Path


def load_bank(path: str):
    """加载题库并展平为题目列表 + 维度注册表。

    题库为嵌套结构 questionConfig.partList[].dimensionList[].questionList[]。
    展平后每题携带其所属维度的全部元数据（id/name/sort/desc/highScoreDesc/icon/bgImg），
    便于后续按维度聚合计分与结果卡渲染。

    返回:
        questions: list[dict]，每项 {seq, id, stem, dimension_id, dimension_name, sort, ...}
        dimensions: list[dict]，维度注册表，按题库插入顺序（即固定优先级顺序）
        score_map: dict[str,int]，选项 → 分数（数据驱动，取自题库 answer_options）
        meta: dict，顶层元数据
    """
    with open(path, "r", encoding="utf-8") as f:
        bank = json.load(f)

    meta = {
        "assessment_id": bank.get("assessment_id", "CAREER-ABILITY-85-001"),
        "assessment_name": bank.get("assessment_name", "职业能力倾向测评（85题版）"),
        "question_total": bank.get("question_total"),
        "dimension_count": bank.get("dimension_count"),
    }

    # 数据驱动计分映射：取自题库顶层 answer_options
    score_map = {}
    for opt in bank.get("answer_options", []):
        score_map[str(opt["option"]).upper()] = int(opt["score"])

    questions = []
    dimensions = []            # 固定优先级顺序
    dim_index = {}            # dimension_id -> 注册表中的索引
    qcfg = bank.get("questionConfig", {})
    for part in qcfg.get("partList", []):
        for dim in part.get("dimensionList", []):
            did = dim.get("id")
            dim_record = {
                "id": did,
                "name": dim.get("name", ""),
                "sort": dim.get("sort"),
                "part_id": part.get("id"),
                "part_name": part.get("name", ""),
                "desc": dim.get("desc", ""),
                "highScoreDesc": dim.get("highScoreDesc", ""),
                "icon": dim.get("icon", ""),
                "bgImg": dim.get("bgImg", ""),
            }
            dim_index[did] = len(dimensions)
            dimensions.append(dim_record)
            for q in dim.get("questionList", []):
                questions.append({
                    "seq": q.get("seq"),
                    "id": q.get("id"),
                    "stem": q.get("stem", ""),
                    "dimension_id": did,
                    "dimension_name": dim.get("name", ""),
                    "sort": dim.get("sort"),
                })

    return questions, dimensions, score_map, meta


def normalize_option(value):
    if value is None:
        return ""
    return str(value).strip().upper()


def expand_answers(answers):
    """统一作答输入格式。

    支持两种提交格式（均为合规输入）：
    1. 紧凑序列（推荐）：长度为 85 的 A-E 字符串，按 seq 1..85 顺序排列，
       例如 "ABCABC..."。约 85 字符，远低于系统截断阈值，提交不丢数据。
    2. JSON 对象（旧格式，向后兼容）：键为 seq 字符串、值为 A-E，
       例如 {"1":"A","2":"B"}。约 530 字符，存在被截断风险，不推荐。

    返回统一的 {seq字符串: 规范化选项} 字典。
    """
    if isinstance(answers, str):
        seq = answers.strip()
        # 仅保留合法选项字符，忽略空格等分隔符
        chars = [c.upper() for c in seq
                 if c.strip() and c.upper() in {"A", "B", "C", "D", "E"}]
        if not chars:
            return {}
        # 字符 i 对应 seq=i+1
        return {str(i + 1): c for i, c in enumerate(chars)}
    if isinstance(answers, dict):
        return answers
    return {}


def to100(score, max_score=40):
    """40 分制原始分 → 100 分制显示分（整数，无需四舍五入）。

    计分映射为 8/6/4/2/0，均为偶数；每维 5 题原始分为 0..40 的偶数。
    rawScore * 2.5 = 整数（2.5 × 偶数 = 5 的倍数），故换算必为整数，无小数无四舍五入。
    报告页得分条与维度卡片分数均用 100 分制展示。
    """
    return score * 100 // max_score


def calculate_scores(answers, questions, dimensions, score_map, meta, top_n=5):
    """计算 17 个能力维度分数并输出确定性结果。

    维度固定优先级 = dimensions 列表的自然顺序（题库 partList→dimensionList 插入顺序）。
    分数相同时按此优先级取靠前者，确保同输入→同输出。
    """
    answers = expand_answers(answers)

    # 维度固定优先级：dimensions 顺序即优先级（索引越小越靠前）
    dim_priority = {d["id"]: i for i, d in enumerate(dimensions)}

    scores = {d["id"]: 0 for d in dimensions}
    answered_seqs = set()

    for q in questions:
        seq_str = str(q["seq"])
        if seq_str in answers:
            answered_seqs.add(seq_str)
            option = normalize_option(answers[seq_str])
            if option in score_map:
                did = q["dimension_id"]
                scores[did] += score_map[option]

    total_questions = len(questions)
    answered_count = len(answered_seqs)
    status = "completed" if answered_count >= total_questions else "incomplete"

    # details：按固定优先级顺序输出 17 维原始分 + 100 分制
    details = []
    for d in dimensions:
        raw = scores[d["id"]]
        details.append({
            "id": d["id"],
            "name": d["name"],
            "sort": d["sort"],
            "score": to100(raw),          # 100 分制显示分（报告页得分条用）
            "rawScore": raw,               # 40 分制原始分（保留用于校验）
            "maxScore": 100,
        })

    # ranked_dimensions：按分数降序；分数相同按固定优先级取靠前者
    ranked = sorted(
        dimensions,
        key=lambda d: (-scores[d["id"]], dim_priority[d["id"]]),
    )
    ranked_dimensions = [
        {
            "id": d["id"],
            "name": d["name"],
            "sort": d["sort"],
            "score": to100(scores[d["id"]]),
        }
        for d in ranked
    ]

    # Top N 优势维度（默认 5，报告页上半部分能力卡片用）
    top_dimensions = ranked_dimensions[:top_n]

    # runnerUp：与第 N 名同分但未入选卡片的维度（并列处理）
    # 第 N 名（索引 top_n-1）的分数若与后续维度相同，这些维度属于"并列第N"，需在卡片下方补说明
    if len(ranked_dimensions) > top_n:
        nth_score = ranked_dimensions[top_n - 1]["score"]
        runner_up = [
            {"id": d["id"], "name": d["name"], "score": to100(scores[d["id"]])}
            for d in ranked_dimensions[top_n:]
            if to100(scores[d["id"]]) == nth_score
        ]
    else:
        runner_up = []

    # reportTextList：Top N 能力卡片，含 highScoreDesc 解读文案（取自题库预定义）
    # 卡片只展示维度名 + 分数 + 详情文案，不渲染图片（避免外部图床加载失败）
    dim_by_id = {d["id"]: d for d in dimensions}
    report_text_list = []
    for item in top_dimensions:
        d = dim_by_id[item["id"]]
        report_text_list.append({
            "id": d["id"],
            "name": d["name"],
            "score": item["score"],          # 100 分制
            "highScoreDesc": d.get("highScoreDesc", ""),
        })

    total_raw = sum(scores.values())             # 满分 17×40 = 680

    result = {
        "assessment_id": meta["assessment_id"],
        "status": status,
        "answered_count": answered_count,
        "total_questions": total_questions,
        "dimension_count": len(dimensions),
        "totalScore": to100(total_raw, max_score=len(dimensions) * 40),  # 100 分制总分（满分 100）
        "maxTotalScore": 100,
        "top_n": top_n,
        "details": details,
        "ranked_dimensions": ranked_dimensions,
        "top_dimensions": top_dimensions,
        "reportTextList": report_text_list,
        "runnerUp": runner_up,
        "qrCodePath": "pages/career-ability/index",
    }
    if status == "incomplete":
        missing = [str(q["seq"]) for q in questions
                   if str(q["seq"]) not in answered_seqs]
        result["missing_questions"] = missing
    return result


def main():
    parser = argparse.ArgumentParser(description="职业能力倾向测评 85 题版评分脚本")
    parser.add_argument(
        "--answers",
        required=True,
        help='作答内容：推荐紧凑序列（85 位 A-E 字符串，如 "ABCABC..."，约 85 字符，'
             '不会触发传输截断）；亦兼容旧 JSON 对象（如 \'{"1":"A","2":"B"}\'，'
             '约 530 字符，不推荐）',
    )
    parser.add_argument(
        "--questions-path",
        default=str(Path(__file__).resolve().parent.parent / "references" / "questions.json"),
        help="题库 JSON 路径（默认为脚本同级 references/questions.json）",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Top 优势维度数量（默认 5，报告页能力卡片数）",
    )
    args = parser.parse_args()

    raw = args.answers.strip()

    # 兼容两种格式：紧凑序列（A-E 字符串）或 JSON 对象
    if raw.startswith("{"):
        try:
            answers = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"答案格式错误：{exc}")
    else:
        answers = raw

    bank_file = Path(args.questions_path)
    if not bank_file.exists():
        raise SystemExit(f"题库文件不存在：{bank_file}")

    questions, dimensions, score_map, meta = load_bank(str(bank_file))
    result = calculate_scores(answers, questions, dimensions, score_map, meta, top_n=args.top_n)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
