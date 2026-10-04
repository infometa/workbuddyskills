#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

DIMENSIONS = ["R", "I", "A", "S", "E", "C"]

# 维度详情：字段名与前端 reportTextList 契约一致（驼峰），去掉海报背景图字段
DIMENSION_PROFILES = {
    "R": {
        "type": "R",
        "name": "现实型",
        "commonFeatures": "愿意使用工具从事操作性工作，动手能力强，做事手脚灵活，动作协调。偏好于具体任务，不善言辞，做事保守，较为谦虚。缺乏社交能力，通常喜欢独立做事。",
        "typicalOccupations": "喜欢使用工具、机器，需要基本操作技能的工作，对要求具备机械方面才能、体力或从事与物件、机器、工具、运动器材、植物、动物相关的职业有兴趣，并具备相应能力。如:技术性职业(计算机硬件人员、摄影师、制图员、机械装配工)，技能性职业(木匠、厨师、技工、修理工、农民、一般劳动)。"
    },
    "I": {
        "type": "I",
        "name": "研究型",
        "commonFeatures": "思想家而非实干家,抽象思维能力强，求知欲强，肯动脑，善思考，不愿动手。喜欢独立的和富有创造性的工作。知识渊博，有学识才能，不善于领导他人。考虑问题理性，做事喜欢精确，喜欢逻辑分析和推理，不断探讨未知的领域。",
        "typicalOccupations": "喜欢智力的、抽象的、分析的、独立的定向任务，要求具备智力或分析才能，并将其用于观察、估测、衡量、形成理论、解决问题的工作，并具备相应的能力。如科学研究人员、教师、工程师、电脑编程人员、医生、系统分析员。"
    },
    "A": {
        "type": "A",
        "name": "艺术型",
        "commonFeatures": "有创造力，乐于创造新颖、与众不同的成果，渴望表现自己的个性，实现自身的价值。做事理想化，追求完美，不重实际。具有一定的艺术才能和个性。善于表达、怀旧、心态较为复杂。",
        "typicalOccupations": "喜欢的工作要求具备艺术修养、创造力、表达能力和直觉，并将其用于语言、行为、声音、颜色和形式的审美、思索和感受，具备相应的能力。不善于事务性工作。如艺术方面(演员、导演、艺术设计师、雕刻家、建筑师、摄影家、广告制作人)，音乐方面(歌唱家、作曲家、乐队指挥)，文学方面(小说家、诗人、剧作家)。"
    },
    "S": {
        "type": "S",
        "name": "社会型",
        "commonFeatures": "喜欢与人交往、不断结交新的朋友、善言谈、愿意教导别人。关心社会问题、渴望发挥自己的社会作用。寻求广泛的人际关系，比较看重社会义务和社会道德。",
        "typicalOccupations": "喜欢要求与人打交道的工作，能够不断结交新的朋友，从事提供信息、启迪、帮助、培训、开发或治疗等事务，并具备相应能力。如: 教育工作者(教师、教育行政人员)，社会工作者(咨询人员、公关人员)。"
    },
    "E": {
        "type": "E",
        "name": "企业型",
        "commonFeatures": "追求权力、权威和物质财富，具有领导才能。喜欢竞争、敢冒风险、有野心、抱负。为人务实，习惯以利益得失，权利、地位、金钱等来衡量做事的价值；做事有较强的目的性。",
        "typicalOccupations": "喜欢要求具备经营、管理、劝服、监督和领导才能，以实现机构、政治、社会及经济目标的工作，并具备相应的能力。如项目经理、销售人员、营销管理人员、政府官员、企业领导、法官、律师。"
    },
    "C": {
        "type": "C",
        "name": "常规型",
        "commonFeatures": "尊重权威和规章制度，喜欢按计划办事，细心、有条理，习惯接受他人的指挥和领导，自己不谋求领导职务。喜欢关注实际和细节情况，通常较为谨慎和保守，缺乏创造性，不喜欢冒险和竞争，富有自我牺牲精神。",
        "typicalOccupations": "喜欢要求注意细节、精确度、有系统有条理，具有记录、归档、据特定要求或程序组织数据和文字信息的职业，并具备相应能力。如:秘书、办公室人员、记事员、会计、行政助理、图书馆管理员、出纳员、打字员、投资分析员。"
    }
}


def load_questions(path: str):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("questions", [])


def normalize_answer(value):
    if value is None:
        return ""
    return str(value).strip().upper()


def expand_answers(answers):
    """统一作答输入格式。

    支持两种提交格式（均为合规输入）：
    1. 紧凑序列（推荐）：长度为 60 的 Y/N 字符串，按题号 1..60 顺序排列，
       例如 "YYNNYY..."。约 60 字符，远低于系统截断阈值，提交不丢数据。
    2. JSON 对象（旧格式，向后兼容）：键为题号字符串、值为 Y/N，
       例如 {"1":"Y","2":"N"}。约 530 字符，存在被截断风险，不推荐。

    返回统一的 {题号字符串: 规范化答案} 字典。
    """
    # 紧凑序列：纯字符串（非 dict）
    if isinstance(answers, str):
        seq = answers.strip()
        # 仅保留 Y/N 字符，忽略空格/分隔符
        chars = [c.upper() for c in seq if c.strip() and c.upper() in {"Y", "N"}]
        if not chars:
            return {}
        # 字符 i 对应题号 i+1
        return {str(i + 1): c for i, c in enumerate(chars)}
    # JSON 对象：直接返回，后续按题号取值
    if isinstance(answers, dict):
        return answers
    return {}


def calculate_scores(answers, questions: list):
    # 统一为 {题号: 答案} 字典，兼容紧凑序列与 JSON 对象
    answers = expand_answers(answers)
    scores = {d: 0 for d in DIMENSIONS}
    answered_ids = set()
    for q in questions:
        qid = str(q.get("id"))
        if qid in answers:
            answered_ids.add(qid)
            answer = normalize_answer(answers[qid])
            if answer in {"Y", "YES", "TRUE", "1"}:
                dim = q.get("dimension")
                if dim in scores:
                    scores[dim] += 1

    # 维度固定优先级（与 SKILL 规则 3 一致）：R, I, A, S, E, C
    dim_priority = {dim: i for i, dim in enumerate(DIMENSIONS)}

    # 按分数降序排列；分数相同时按固定优先级 R, I, A, S, E, C 取靠前者
    sorted_dims = sorted(
        scores.keys(), key=lambda d: (-scores[d], dim_priority[d])
    )

    # 取前 3 维度，结果完全确定
    top_dimensions = sorted_dims[:3]
    dominant_type = "".join(top_dimensions)

    total_questions = len(questions)
    answered_count = len(answered_ids)
    status = "completed" if answered_count >= total_questions else "incomplete"

    display_score = min(100, int((sum(scores.values()) / total_questions) * 100))

    # reportTextList：只含 top 3 维度的详情，字段名与前端契约一致（驼峰）
    # 分数展示走顶层 details，详情项不带 score，职责分离
    report_text_list = []
    for dim in top_dimensions:
        profile = DIMENSION_PROFILES.get(dim, {})
        report_text_list.append({
            "type": dim,
            "name": profile.get("name", dim),
            "commonFeatures": profile.get("commonFeatures", ""),
            "typicalOccupations": profile.get("typicalOccupations", "")
        })

    # details 按固定顺序 R, I, A, S, E, C 输出（规则 2）
    ordered_details = {d: scores.get(d, 0) for d in DIMENSIONS}

    result = {
        "assessment_id": "HOLLAND-60-001",
        "status": status,
        "score": display_score,
        "max_score": 100,
        "answered_count": answered_count,
        "total_questions": total_questions,
        "top_dimensions": top_dimensions,
        "dominant_type": dominant_type,
        "details": ordered_details,
        "reportTextList": report_text_list,
        "qrCodePath": "pages/hollander/index",
    }
    if status == "incomplete":
        missing_ids = [str(q.get("id")) for q in questions if str(q.get("id")) not in answered_ids]
        result["missing_questions"] = missing_ids
    return result


def main():
    parser = argparse.ArgumentParser(description="霍兰德职业兴趣测评 60 题版评分脚本")
    parser.add_argument(
        "--answers",
        required=True,
        help='作答内容：推荐紧凑序列（60 位 Y/N 字符串，如 "YYNNYY..."，约 60 字符，不会触发传输截断）；'
             '亦兼容旧 JSON 对象（如 \'{"1":"Y","2":"N"}\'，约 530 字符，不推荐）',
    )
    parser.add_argument(
        "--questions-path",
        default=str(Path(__file__).resolve().parent.parent / "references" / "questions.json"),
        help="题库 JSON 路径（默认为脚本同级 references/questions.json）",
    )
    args = parser.parse_args()

    raw = args.answers.strip()

    # 兼容两种格式：紧凑序列（Y/N 字符串）或 JSON 对象
    if raw.startswith("{"):
        # 旧 JSON 对象格式
        try:
            answers = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"答案格式错误：{exc}")
    else:
        # 紧凑序列格式：直接作为字符串传入 expand_answers
        answers = raw

    question_file = Path(args.questions_path)
    if not question_file.exists():
        raise SystemExit(f"题库文件不存在：{question_file}")

    questions = load_questions(str(question_file))
    result = calculate_scores(answers, questions)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
