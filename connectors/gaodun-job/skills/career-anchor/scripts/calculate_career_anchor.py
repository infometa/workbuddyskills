import json
import sys
from typing import Dict, List
from pathlib import Path


def _load_data(path) -> List[Dict]:
    """
    通用数据加载（单一数据源 = references 下的 markdown 文档）：
    优先按纯 JSON 解析；若失败（如 markdown 包裹格式），则提取 ```json 代码块内容。
    支持 .json（纯 JSON 数组）与 .md（markdown 包裹 JSON）两种数据文件。
    """
    path = Path(path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 先尝试直接按 JSON 解析（兼容纯 JSON 文件）
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 解析失败则从 markdown 的 ```json 代码块中提取
    marker = '```json'
    start = content.find(marker)
    if start == -1:
        raise ValueError(f"文件 {path} 既不是合法 JSON，也不包含 ```json 代码块")
    start += len(marker)
    end = content.find('```', start)
    if end == -1:
        raise ValueError(f"文件 {path} 中的 ```json 代码块缺少结束标记 ```")
    try:
        return json.loads(content[start:end].strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"文件 {path} 中 ```json 代码块内容解析失败: {e}") from e


def load_questions(questions_path: str = None) -> List[Dict]:
    """
    加载题库数据
    默认从 references/questions.md 的 ```json 代码块读取（单一数据源）
    """
    if questions_path is None:
        # 默认路径为 skill 根目录下 references/questions.md
        root_dir = Path(__file__).parent.parent
        questions_path = root_dir / "references" / "questions.md"

    return _load_data(questions_path)


def load_dimensions(dimensions_path: str = None) -> Dict[str, Dict]:
    """
    加载维度详情数据
    默认从 references/dimensions.md 的 ```json 代码块读取（单一数据源）
    返回以维度代码为 key 的字典
    """
    if dimensions_path is None:
        # 默认路径为 skill 根目录下 references/dimensions.md
        root_dir = Path(__file__).parent.parent
        dimensions_path = root_dir / "references" / "dimensions.md"

    dimensions_list = _load_data(dimensions_path)

    # 转换为以 code 为 key 的字典
    dimensions = {}
    for dim in dimensions_list:
        dimensions[dim['code']] = dim

    return dimensions


def calculate_scores(answers: Dict[str, int], questions: List[Dict] = None,
                     dimensions_path: str = None) -> Dict:
    """
    计算八个维度的得分

    Args:
        answers: 用户答案，key 为题目编号（字符串），value 为评分（1-6）
        questions: 题库数据，如果为 None 则从默认路径加载
        dimensions_path: 维度详情文件路径，如果为 None 则从默认路径加载

    Returns:
        包含得分和职业锚类型的完整结果字典
    """
    if questions is None:
        questions = load_questions()

    # 归一化答案 key 为字符串（兼容 int / str 两种 key 类型），
    # 无法解析为整数的值视为"未作答"（计入缺失题号）
    normalized = {}
    for k, v in answers.items():
        try:
            normalized[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    answers = normalized

    # 初始化八个维度得分
    dimension_scores = {
        'TF': 0,
        'GM': 0,
        'AU': 0,
        'SE': 0,
        'EC': 0,
        'SV': 0,
        'CH': 0,
        'LS': 0
    }

    # 统计已答题数（仅统计值在 1-6 范围内的有效答案）
    answered_count = 0
    answered_indexes = set()

    # 计算各维度得分
    for question in questions:
        question_index = str(question['questionIndex'])
        score = answers.get(question_index)
        if score is not None and 1 <= score <= 6:
            dimension_code = question['dimensionCode']
            dimension_scores[dimension_code] += score
            answered_count += 1
            answered_indexes.add(question_index)

    # 排序规则：先按得分降序，分数相同时按固定维度顺序
    dimension_order = ['TF', 'GM', 'AU', 'SE', 'EC', 'SV', 'CH', 'LS']
    sorted_dimensions = sorted(
        dimension_scores.items(),
        key=lambda x: (-x[1], dimension_order.index(x[0]))
    )

    # 取前三个维度
    top_three = sorted_dimensions[:3]
    anchor_type = '+'.join([dim[0] for dim in top_three])

    # 加载维度详情
    dimensions = load_dimensions(dimensions_path)

    # 构建前三个维度的详情列表
    top_three_details = []
    for code, score in top_three:
        dim_info = dimensions.get(code, {})
        top_three_details.append({
            'code': code,
            'name': dim_info.get('name', ''),
            'score': score,
            'description': dim_info.get('description', '')
        })

    # 生成总结
    summary = f"您的职业锚类型为 {anchor_type}（{'+'.join([d['name'] for d in top_three_details])}），得分最高的三个维度分别为：{top_three_details[0]['name']}（{top_three_details[0]['score']}分）、{top_three_details[1]['name']}（{top_three_details[1]['score']}分）、{top_three_details[2]['name']}（{top_three_details[2]['score']}分）。"

    # 生成职业建议（基于前三个维度）
    recommendations = generate_recommendations(top_three_details)

    # 构建完整结果
    result = {
        'assessment_id': 'CAREER-ANCHOR-40-001',
        'assessment_name': '职业锚测评',
        'status': 'completed' if answered_count == 40 else 'incomplete',
        'answered_count': answered_count,
        'total_questions': 40,
        'anchor_type': anchor_type,
        'dimension_scores': dimension_scores,
        'top_three_dimensions': top_three_details,
        'analysis': {
            'summary': summary,
            'recommendations': recommendations
        }
    }

    # 如果未完成，添加缺失题号（基于"无有效答案"判断，而非 key 是否存在，
    # 避免非法答案值导致 status=incomplete 却 missing_questions 为空）
    if answered_count < 40:
        missing = [str(i) for i in range(1, 41) if str(i) not in answered_indexes]
        result['missing_questions'] = missing

    return result


def generate_recommendations(top_three_details: List[Dict]) -> List[str]:
    """
    基于前三个维度生成职业建议
    """
    # 这里可以根据维度组合生成更精准的建议
    # 目前采用通用的推荐逻辑

    recommendations_map = {
        'TF': ['技术研发岗位', '技术专家岗位', '技术培训师', '技术顾问'],
        'GM': ['管理岗位', '项目经理', '部门主管', '运营总监'],
        'AU': ['自由职业', '创业', '独立顾问', '远程工作'],
        'SE': ['体制内工作', '大型企业', '公务员', '教师'],
        'EC': ['创业', '产品创新', '风险投资', '商业模式设计'],
        'SV': ['公益组织', '教育培训', '医疗健康', '社会工作'],
        'CH': ['技术攻关', '项目管理', '战略咨询', '创业'],
        'LS': ['远程工作', '弹性工作制', '自由职业', '工作生活平衡岗位']
    }

    recommendations = []
    for detail in top_three_details:
        code = detail['code']
        if code in recommendations_map:
            recommendations.extend(recommendations_map[code][:2])

    # 去重并限制数量
    recommendations = list(dict.fromkeys(recommendations))[:5]

    return recommendations


def main():
    """
    命令行入口
    """
    import argparse

    parser = argparse.ArgumentParser(description='职业锚测评评分脚本')
    parser.add_argument('--answers', type=str, required=True, help='用户答案 JSON 字符串')
    parser.add_argument('--questions-path', type=str, help='题库文件路径（可选）')
    parser.add_argument('--dimensions-path', type=str, help='维度详情文件路径（可选）')

    args = parser.parse_args()

    # 解析答案
    try:
        answers = json.loads(args.answers)
    except json.JSONDecodeError as e:
        print(f"答案 JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 加载题库（如果指定了路径）
    questions = None
    if args.questions_path:
        questions = load_questions(args.questions_path)

    # 计算得分
    result = calculate_scores(answers, questions, args.dimensions_path)

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()