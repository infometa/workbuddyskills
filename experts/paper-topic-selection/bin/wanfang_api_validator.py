# -*- coding: utf-8 -*-
"""
万方API参数校验 + 结果相关性检查工具
=====================================
使用方式：
  from wanfang_api_validator import validate_params, check_relevance, print_report

  # 1. 调用前校验参数
  warnings = validate_params("read/paper", {"keyword": "帮信罪", "type": "HIGH"})
  if warnings:
      print(f"⚠️ 参数校验警告: {warnings}")

  # 2. 调用后检查结果相关性
  relevance_warnings = check_relevance("read/paper", "帮信罪", response_json)
  if relevance_warnings:
      print(f"⚠️ 结果相关性警告: {relevance_warnings}")

  # 3. 汇总报告
  print_report(all_warnings)
"""

import json
from typing import Dict, List, Any, Optional

# ============================================================
# 1. API参数Schema定义（与TEAM.md速查表同步）
# ============================================================

# POST接口的参数schema
POST_API_SCHEMA: Dict[str, Dict] = {
    # === 欧阳文献 read 系列 ===
    "read/paper": {
        "required": ["keyword"],
        "optional": ["page", "type"],
        "type_enum": ["HIGH", "NEW", "DEGREE", "REVIEW"],
        "wrong_param_warning": "read/paper的参数名为keyword，不是param！type枚举：HIGH/NEW/DEGREE/REVIEW",
    },
    "read/scholar": {
        "required": ["keyword"],
        "optional": ["page", "sort"],
        "sort_enum": ["RELATIVITY", "HINDEX", "ARTICLE", "CITED"],
        "wrong_param_warning": "read/scholar的参数名为keyword，不是param！sort枚举：RELATIVITY/HINDEX/ARTICLE/CITED",
    },
    # === 皇甫定题 assess 系列 ===
    "assess/NoveltyData": {
        "required": ["title", "keyword", "abstract"],
        "optional": [],
        "wrong_param_warning": "assess系列需要title+keyword+abstract三字段，不是单个param！",
    },
    "assess/NoveltyPaper": {
        "required": ["title", "keyword", "abstract", "type"],
        "optional": [],
        "type_enum": ["title", "keyword", "abstracts"],
        "wrong_param_warning": "assess系列需要title+keyword+abstract三字段，不是单个param！NoveltyPaper的type枚举：title/keyword/abstracts",
    },
    "assess/TopicExtendData": {
        "required": ["title", "keyword", "abstract"],
        "optional": [],
        "wrong_param_warning": "assess系列需要title+keyword+abstract三字段，不是单个param！",
    },
    "assess/TopicExtendPaper": {
        "required": ["title", "keyword", "abstract", "type", "key"],
        "optional": [],
        "type_enum": ["HIGH_CNT", "NEWS"],
        "wrong_param_warning": "assess系列需要title+keyword+abstract三字段，不是单个param！TopicExtendPaper的type枚举：HIGH_CNT/NEWS",
    },
    "assess/SubjectOsmosisData": {
        "required": ["title", "keyword", "abstract"],
        "optional": [],
        "wrong_param_warning": "assess系列需要title+keyword+abstract三字段，不是单个param！",
    },
    "assess/SubjectOsmosisPaper": {
        "required": ["title", "keyword", "abstract", "education_code"],
        "optional": [],
        "wrong_param_warning": "assess系列需要title+keyword+abstract三字段，不是单个param！SubjectOsmosisPaper需要education_code字段",
    },
    # === 上官选题 find Data 系列 ===
    "find/acadamicData": {
        "required": ["search", "param"],
        "optional": [],
        "search_enum": ["KEYWORD", "CODE"],
        "wrong_param_warning": "find Data系列需要search+param！search=KEYWORD/CODE，param=关键词（不是cluster！）",
    },
    "find/frontierData": {
        "required": ["search", "param"],
        "optional": [],
        "search_enum": ["KEYWORD", "CODE"],
        "wrong_param_warning": "find Data系列需要search+param！search=KEYWORD/CODE，param=关键词（不是cluster！）",
    },
    "find/acrossData": {
        "required": ["search", "param"],
        "optional": [],
        "search_enum": ["KEYWORD", "CODE"],
        "wrong_param_warning": "find Data系列需要search+param！search=KEYWORD/CODE，param=关键词（不是cluster！）",
    },
    "find/newthemeData": {
        "required": ["search", "param"],
        "optional": [],
        "search_enum": ["KEYWORD", "CODE"],
        "wrong_param_warning": "find Data系列需要search+param！search=KEYWORD/CODE，param=关键词（不是cluster！）",
    },
    "find/hotspot": {
        "required": ["param", "search"],
        "optional": [],
        "search_enum": ["HOTS", "NEWS"],
        "wrong_param_warning": "hotspot的param=学科号（如07），search=HOTS/NEWS！注意：与find Data系列的param含义不同",
    },
    "find/eduCodeList": {
        "required": [],
        "optional": [],
        "wrong_param_warning": "eduCodeList无必选参数",
    },
    # === 上官选题 find Paper 系列（两步联动） ===
    "find/acadamicPaper": {
        "required": ["paper", "param"],
        "optional": [],
        "paper_enum": ["HIGH", "NEW", "DEGREE", "REVIEW"],
        "wrong_param_warning": "find Paper系列的param=cluster值（不是关键词！），必须从Data接口返回获取！paper枚举：HIGH/NEW/DEGREE/REVIEW",
    },
    "find/frontierPaper": {
        "required": ["paper", "param"],
        "optional": [],
        "paper_enum": ["HIGH", "NEW", "DEGREE", "REVIEW"],
        "wrong_param_warning": "find Paper系列的param=cluster值（不是关键词！），必须从Data接口返回获取！paper枚举：HIGH/NEW/DEGREE/REVIEW",
    },
    "find/acrossPaper": {
        "required": ["paper", "param"],
        "optional": [],
        "paper_enum": ["HIGH", "NEW", "DEGREE", "REVIEW"],
        "wrong_param_warning": "find Paper系列的param=cluster值（不是关键词！），必须从Data接口返回获取！paper枚举：HIGH/NEW/DEGREE/REVIEW",
    },
    "find/newthemePaper": {
        "required": ["paper", "param"],
        "optional": [],
        "paper_enum": ["HIGH", "NEW", "DEGREE", "REVIEW"],
        "wrong_param_warning": "find Paper系列的param=cluster值（不是关键词！），必须从Data接口返回获取！paper枚举：HIGH/NEW/DEGREE/REVIEW",
    },
    # === 夏侯拟题 title 系列 ===
    "title/recommend": {
        "required": ["keyword"],
        "optional": [],
        "wrong_param_warning": "title系列的参数名为keyword，不是param！",
    },
    "title/synonyms": {
        "required": ["keyword"],
        "optional": ["page"],
        "wrong_param_warning": "title系列的参数名为keyword，不是param！",
    },
    # === 太史报告 report 系列 ===
    "report/reportNovelty": {
        "required": ["keyword"],
        "optional": [],
        "wrong_param_warning": "report系列的参数名为keyword，不是param！",
    },
    "report/reportSocial": {
        "required": ["keyword"],
        "optional": [],
        "wrong_param_warning": "report系列的参数名为keyword，不是param！",
    },
    "report/reportNatural": {
        "required": ["keyword"],
        "optional": [],
        "wrong_param_warning": "report系列的参数名为keyword，不是param！",
    },
    "report/reportPeriodical": {
        "required": ["keyword"],
        "optional": [],
        "wrong_param_warning": "report系列的参数名为keyword，不是param！",
    },
}

# GET接口的参数schema（pool系列）
GET_API_SCHEMA: Dict[str, Dict] = {
    "pool/listTopics": {
        "method": "GET",
        "query_params": ["page", "size"],
        "wrong_param_warning": "pool系列使用GET方法，参数通过URL query传递",
    },
    "pool/listNaturals": {
        "method": "GET",
        "query_params": ["page", "size"],
        "wrong_param_warning": "pool系列使用GET方法，参数通过URL query传递",
    },
    "pool/listSubjectTypes": {
        "method": "GET",
        "query_params": [],
        "wrong_param_warning": "pool系列使用GET方法，无参数",
    },
    "pool/listPapers": {
        "method": "GET",
        "query_params": ["page", "size", "classCode"],
        "wrong_param_warning": "pool系列使用GET方法！listPapers用classCode参数（不是param）！",
    },
    "pool/listSocialCategorys": {
        "method": "GET",
        "query_params": [],
        "wrong_param_warning": "pool系列使用GET方法，无参数",
    },
    "pool/listSocials": {
        "method": "GET",
        "query_params": ["socialId"],
        "wrong_param_warning": "pool系列使用GET方法！listSocials用socialId参数（不是param）！",
    },
}

# 合并所有schema
ALL_API_SCHEMA = {**POST_API_SCHEMA, **GET_API_SCHEMA}

# 已知的"万方API静默容错"特征：参数名错误时仍返回HTTP 200
SILENT_FAILURE_NOTE = (
    "⚠️ 万方API在参数名错误时返回HTTP 200而非400（静默忽略未知参数），"
    "不会报错，但返回的数据不相关。必须靠参数名正确+结果相关性检查来发现。"
)


# ============================================================
# 2. 参数校验函数
# ============================================================

def validate_params(endpoint: str, params: Dict[str, Any]) -> List[str]:
    """
    校验API请求参数是否正确。

    Args:
        endpoint: API路径（如 "read/paper", "assess/NoveltyData"）
        params: 请求参数字典

    Returns:
        警告列表（空列表=无问题）
    """
    warnings = []

    # 标准化endpoint：去掉/topic/前缀
    ep = endpoint.replace("/topic/", "").lstrip("/")

    schema = ALL_API_SCHEMA.get(ep)
    if schema is None:
        # 尝试模糊匹配
        for key in ALL_API_SCHEMA:
            if ep.endswith(key) or key in ep:
                schema = ALL_API_SCHEMA[key]
                ep = key
                break
        if schema is None:
            warnings.append(f"❓ 未知接口: {endpoint}，无法校验参数")
            return warnings

    # 检查是否使用了被禁止的通用参数名
    if "param" in params and ep not in (
        "find/acadamicData", "find/frontierData", "find/acrossData",
        "find/newthemeData", "find/hotspot",
        "find/acadamicPaper", "find/frontierPaper",
        "find/acrossPaper", "find/newthemePaper",
    ):
        # find Data系列和find Paper系列的param是合法的
        warnings.append(
            f"❌ 接口 {ep} 使用了通用参数名 'param'，这是错误用法！"
            f" 正确做法: {schema.get('wrong_param_warning', '请查看TEAM.md速查表')}"
        )

    # 检查必选参数
    required = schema.get("required", [])
    for r in required:
        if r not in params:
            warnings.append(
                f"❌ 接口 {ep} 缺少必选参数 '{r}'。"
                f" 必选参数: {required}"
            )

    # 检查枚举值
    if "type_enum" in schema and "type" in params:
        if params["type"] not in schema["type_enum"]:
            warnings.append(
                f"❌ 接口 {ep} 的type值 '{params['type']}' 不在合法枚举中。"
                f" 合法值: {schema['type_enum']}"
            )

    if "sort_enum" in schema and "sort" in params:
        if params["sort"] not in schema["sort_enum"]:
            warnings.append(
                f"❌ 接口 {ep} 的sort值 '{params['sort']}' 不在合法枚举中。"
                f" 合法值: {schema['sort_enum']}"
            )

    if "paper_enum" in schema and "paper" in params:
        if params["paper"] not in schema["paper_enum"]:
            warnings.append(
                f"❌ 接口 {ep} 的paper值 '{params['paper']}' 不在合法枚举中。"
                f" 合法值: {schema['paper_enum']}"
            )

    if "search_enum" in schema and "search" in params:
        if params["search"] not in schema["search_enum"]:
            warnings.append(
                f"❌ 接口 {ep} 的search值 '{params['search']}' 不在合法枚举中。"
                f" 合法值: {schema['search_enum']}"
            )

    # 检查assess系列是否有title+keyword+abstract三字段（已在required检查中覆盖，此处仅补充说明）
    if ep.startswith("assess/") and not any("title" in w and "keyword" in w for w in warnings):
        pass  # required检查已处理，不重复

    return warnings


# ============================================================
# 3. 结果相关性检查函数
# ============================================================

def check_relevance(endpoint: str, keyword: str, response_data: Dict) -> List[str]:
    """
    检查API返回数据是否与查询关键词相关。

    Args:
        endpoint: API路径
        keyword: 查询关键词
        response_data: API返回的JSON数据（已解析为dict）

    Returns:
        警告列表（空列表=无问题）
    """
    warnings = []

    # 标准化endpoint
    ep = endpoint.replace("/topic/", "").lstrip("/")
    for key in ALL_API_SCHEMA:
        if ep.endswith(key) or key in ep:
            ep = key
            break

    code = response_data.get("Code", "")

    # 检查HTTP层面的成功
    if code and code != "success" and code != 200 and code != "200":
        warnings.append(f"⚠️ 接口 {ep} 返回非成功状态: Code={code}, Msg={response_data.get('Msg', '')}")
        return warnings  # 如果API本身就报错了，不需要做相关性检查

    # --- 文本类API：检查返回内容是否包含关键词 ---
    if ep in ("read/paper",):
        _check_paper_relevance(ep, keyword, response_data, warnings)
    elif ep in ("read/scholar",):
        _check_scholar_relevance(ep, keyword, response_data, warnings)
    elif ep in ("title/recommend",):
        _check_title_relevance(ep, keyword, response_data, warnings)
    elif ep in ("title/synonyms",):
        _check_synonyms_relevance(ep, keyword, response_data, warnings)

    # --- 统计类API：检查数据是否为空 ---
    elif ep.startswith("assess/"):
        _check_assess_relevance(ep, keyword, response_data, warnings)
    elif ep.startswith("report/"):
        _check_report_relevance(ep, keyword, response_data, warnings)

    # --- 图谱类API：检查nodes是否为空 ---
    elif ep in ("find/acadamicData", "find/frontierData", "find/acrossData", "find/newthemeData"):
        _check_graph_relevance(ep, keyword, response_data, warnings)

    # --- 列表类API：检查pageDatas是否为空 ---
    elif ep in ("pool/listTopics", "pool/listNaturals", "pool/listPapers"):
        _check_list_relevance(ep, keyword, response_data, warnings)

    return warnings


def _check_paper_relevance(ep, keyword, data, warnings):
    """检查read/paper返回的论文是否与关键词相关"""
    pi = data.get("pageInfo", {})
    total = pi.get("totalCount", 0)
    papers = pi.get("pageDatas", [])

    if total == 0 or len(papers) == 0:
        warnings.append(f"⚠️ {ep} 返回0篇论文，可能关键词太冷门或参数错误")
        return

    # 检查前5篇论文的标题/关键词是否与查询关键词相关
    kw_lower = keyword.lower()
    relevant_count = 0
    for p in papers[:5]:
        per = p.get("periodical", p.get("thesis", {}))
        title = per.get("title", "").lower()
        keywords_list = per.get("keywords", [])
        keywords_str = " ".join(keywords_list).lower() if isinstance(keywords_list, list) else str(keywords_list).lower()

        # 检查关键词是否出现在标题或关键词列表中
        # 支持分号分隔的多关键词（如"帮助信息网络犯罪活动罪;帮信罪"）
        kw_parts = [k.strip().lower() for k in keyword.replace(";", ",").replace("，", ",").split(",")]
        for kp in kw_parts:
            if kp and (kp in title or kp in keywords_str):
                relevant_count += 1
                break

    if relevant_count == 0:
        warnings.append(
            f"🔴 高风险: {ep} 返回了{total}篇论文，但前{min(5, len(papers))}篇均与关键词'{keyword}'不相关。"
            f" 极可能参数名错误（API静默容错）！请检查是否使用了正确的参数名'keyword'。"
        )
    else:
        # 按比例判断：如果相关论文占比<50%且论文数>=3，标记为中风险
        checked = min(5, len(papers))
        ratio = relevant_count / checked if checked > 0 else 0
        if ratio < 0.5 and checked >= 3:
            warnings.append(
                f"⚠️ 中风险: {ep} 前{checked}篇论文中仅{relevant_count}篇与关键词'{keyword}'相关（{ratio:.0%}），"
                f" 可能参数不完全正确或关键词太宽泛"
            )


def _check_scholar_relevance(ep, keyword, data, warnings):
    """检查read/scholar返回的学者是否与关键词相关"""
    pi = data.get("pageInfo", {})
    total = pi.get("totalCount", 0)
    scholars = pi.get("pageDatas", [])

    if total == 0 or len(scholars) == 0:
        warnings.append(f"⚠️ {ep} 返回0位学者，可能关键词太冷门或参数错误")
        return

    # 检查前3位学者的研究方向关键词是否与查询关键词相关
    kw_lower = keyword.lower()
    relevant_count = 0
    for s in scholars[:3]:
        sch = s.get("scholar", {})
        keywords_list = sch.get("keywords", [])
        keywords_str = " ".join(keywords_list).lower() if isinstance(keywords_list, list) else str(keywords_list).lower()
        kw_parts = [k.strip().lower() for k in keyword.replace(";", ",").replace("，", ",").split(",")]
        for kp in kw_parts:
            if kp and kp in keywords_str:
                relevant_count += 1
                break

    if relevant_count == 0:
        warnings.append(
            f"⚠️ {ep} 返回了{total}位学者，但前3位的研究方向均不含关键词'{keyword}'。"
            f" 这可能是正常的（学者研究范围广），但也可能是参数错误。"
        )


def _check_title_relevance(ep, keyword, data, warnings):
    """检查title/recommend返回的标题是否与关键词相关"""
    tmpl = data.get("template", {})
    nodes = tmpl.get("nodes", [])

    if len(nodes) == 0:
        warnings.append(f"⚠️ {ep} 返回0条推荐标题，可能关键词太冷门或参数错误")
        return

    # 检查前5条标题是否包含关键词
    kw_lower = keyword.lower()
    kw_parts = [k.strip().lower() for k in keyword.replace(";", ",").replace("，", ",").split(",")]
    relevant_count = 0
    for n in nodes[:5]:
        title = n.get("templateTitle", "").lower()
        for kp in kw_parts:
            if kp and kp in title:
                relevant_count += 1
                break

    if relevant_count == 0:
        warnings.append(
            f"🔴 高风险: {ep} 返回了{len(nodes)}条推荐标题，但前5条均不含关键词'{keyword}'。"
            f" 极可能参数名错误！请检查是否使用了正确的参数名'keyword'。"
        )


def _check_synonyms_relevance(ep, keyword, data, warnings):
    """检查title/synonyms返回的关联主题"""
    pi = data.get("pageInfo", {})
    total = pi.get("totalCount", 0)
    if total == 0:
        warnings.append(f"⚠️ {ep} 返回0条关联主题，可能关键词太冷门")


def _check_assess_relevance(ep, keyword, data, warnings):
    """检查assess系列返回的数据是否合理"""
    if "NoveltyData" in ep:
        inn = data.get("innovation", {})
        title_count = inn.get("titleCount", 0)
        kw_count = inn.get("keywordCount", 0)
        if title_count == 0 and kw_count == 0:
            warnings.append(
                f"⚠️ {ep} 返回titleCount=0且keywordCount=0。"
                f" 可能是关键词太新颖（正常），也可能是参数未传递（异常）。"
                f" 请确认请求体包含title+keyword+abstract三字段。"
            )
    elif "TopicExtendData" in ep:
        kw = data.get("keyword", {})
        nodes = kw.get("nodes", [])
        if len(nodes) == 0:
            warnings.append(
                f"⚠️ {ep} 返回0个关联主题。"
                f" 可能是关键词太冷门（正常），也可能是参数未传递（异常）。"
            )
    elif "SubjectOsmosisData" in ep:
        sub = data.get("subject", {})
        nodes = sub.get("nodes", [])
        if len(nodes) == 0:
            warnings.append(
                f"⚠️ {ep} 返回0个渗透学科。"
                f" 可能是关键词太冷门（正常），也可能是参数未传递（异常）。"
            )


def _check_report_relevance(ep, keyword, data, warnings):
    """检查report系列返回的数据"""
    if "reportNovelty" in ep:
        ri = data.get("reportInnovation", {})
        if not ri:
            warnings.append(f"⚠️ {ep} 返回的reportInnovation为空，可能参数错误")
            return
        years = ri.get("years", [])
        if len(years) == 0:
            warnings.append(f"⚠️ {ep} 返回0年趋势数据，可能关键词太冷门或参数错误")
    elif "reportSocial" in ep:
        rsi = data.get("reportSocialGuideInfo", {})
        if not rsi:
            warnings.append(f"⚠️ {ep} 返回的reportSocialGuideInfo为空")
    elif "reportNatural" in ep:
        rng = data.get("reportNaturalGuide", {})
        if not rng:
            warnings.append(f"⚠️ {ep} 返回的reportNaturalGuide为空")
    elif "reportPeriodical" in ep:
        rpg = data.get("reportPeriodicalGuide", {})
        if not rpg:
            warnings.append(f"⚠️ {ep} 返回的reportPeriodicalGuide为空")


def _check_graph_relevance(ep, keyword, data, warnings):
    """检查find/*Data系列返回的图谱节点"""
    # 确定数据路径
    root_key_map = {
        "find/acadamicData": "knowledge",
        "find/frontierData": "frontier",
        "find/acrossData": "across",
        "find/newthemeData": "newTheme",
    }
    root_key = root_key_map.get(ep, "")
    if not root_key:
        return

    root = data.get(root_key, {})
    nodes = root.get("nodes", [])

    if len(nodes) == 0:
        # 空节点可能是正常的（关键词无对应数据），也可能是参数错误
        code = data.get("Code", "")
        if code == 2 or code == "2":
            warnings.append(
                f"ℹ️ {ep} 返回Code=2，表示该关键词无知识脉络数据（正常返回，非错误）"
            )
        else:
            warnings.append(
                f"⚠️ {ep} 返回0个{root_key}节点。"
                f" 可能是关键词无对应聚类数据（正常），也可能是参数错误。"
                f" 请确认请求体格式为 {{\"search\":\"KEYWORD\",\"param\":\"{keyword}\"}}。"
            )


def _check_list_relevance(ep, keyword, data, warnings):
    """检查pool系列返回的列表数据"""
    pi = data.get("pageInfo", {})
    total = pi.get("totalCount", 0)
    if total == 0:
        warnings.append(f"ℹ️ {ep} 返回0条记录，可能是数据尚未录入（正常）")


# ============================================================
# 4. 报告输出函数
# ============================================================

def print_report(all_warnings: List[Dict]) -> str:
    """
    汇总输出所有校验和相关性检查结果。

    Args:
        all_warnings: [{"endpoint": ..., "type": "param"/"relevance", "warnings": [...]}, ...]

    Returns:
        格式化的报告字符串
    """
    if not all_warnings:
        return "✅ 全部API参数校验和结果相关性检查通过，无警告。"

    lines = ["=" * 60]
    lines.append("API参数校验 + 结果相关性检查报告")
    lines.append("=" * 60)
    lines.append("")

    high_risk = []
    medium_risk = []
    info = []

    for item in all_warnings:
        for w in item.get("warnings", []):
            entry = {"endpoint": item["endpoint"], "type": item["type"], "message": w}
            if "🔴" in w or "❌" in w:
                high_risk.append(entry)
            elif "⚠️" in w:
                medium_risk.append(entry)
            else:
                info.append(entry)

    if high_risk:
        lines.append("🔴 高风险问题（必须修复）:")
        for e in high_risk:
            lines.append(f"  [{e['endpoint']}] {e['message']}")
        lines.append("")

    if medium_risk:
        lines.append("⚠️ 中等风险（建议关注）:")
        for e in medium_risk:
            lines.append(f"  [{e['endpoint']}] {e['message']}")
        lines.append("")

    if info:
        lines.append("ℹ️ 提示信息:")
        for e in info:
            lines.append(f"  [{e['endpoint']}] {e['message']}")
        lines.append("")

    lines.append("-" * 60)
    lines.append(f"总计: {len(high_risk)} 高风险, {len(medium_risk)} 中等风险, {len(info)} 提示")

    report = "\n".join(lines)
    print(report)
    return report


# ============================================================
# 5. 快捷函数：一键校验整个测试结果
# ============================================================

def validate_all_results(results: Dict[str, Dict], keyword_map: Dict[str, str]) -> str:
    """
    一键校验整个测试的所有API调用结果。

    Args:
        results: {call_name: {"endpoint": ..., "params": ..., "data": ...}, ...}
        keyword_map: {call_name: keyword, ...} 每个调用对应的查询关键词

    Returns:
        报告字符串
    """
    all_warnings = []

    for call_name, call_data in results.items():
        endpoint = call_data.get("endpoint", "")
        params = call_data.get("params", {})
        data = call_data.get("data", {})
        keyword = keyword_map.get(call_name, "")

        # 参数校验
        param_warnings = validate_params(endpoint, params)
        if param_warnings:
            all_warnings.append({
                "endpoint": f"{call_name} ({endpoint})",
                "type": "param",
                "warnings": param_warnings,
            })

        # 结果相关性检查
        if keyword and data:
            relevance_warnings = check_relevance(endpoint, keyword, data)
            if relevance_warnings:
                all_warnings.append({
                    "endpoint": f"{call_name} ({endpoint})",
                    "type": "relevance",
                    "warnings": relevance_warnings,
                })

    return print_report(all_warnings)


# ============================================================
# 6. 单元测试（自检）
# ============================================================

if __name__ == "__main__":
    print("=== 万方API参数校验工具自检 ===\n")

    # 测试1：正确的read/paper参数
    w = validate_params("read/paper", {"keyword": "帮信罪", "type": "HIGH"})
    print(f"测试1 read/paper正确参数: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试2：错误的read/paper参数（用了param）
    w = validate_params("read/paper", {"param": "帮信罪", "type": "HIGH"})
    print(f"测试2 read/paper错误参数(param): {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试3：缺少keyword的read/paper
    w = validate_params("read/paper", {"type": "HIGH"})
    print(f"测试3 read/paper缺少keyword: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试4：正确的assess参数
    w = validate_params("assess/NoveltyData", {"title": "帮信罪研究", "keyword": "帮信罪", "abstract": "摘要"})
    print(f"测试4 assess/NoveltyData正确参数: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试5：错误的assess参数（只有param）
    w = validate_params("assess/NoveltyData", {"param": "帮信罪"})
    print(f"测试5 assess/NoveltyData错误参数(param): {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试6：正确的find/acadamicData参数
    w = validate_params("find/acadamicData", {"search": "KEYWORD", "param": "帮信罪"})
    print(f"测试6 find/acadamicData正确参数: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试7：错误的type枚举
    w = validate_params("read/paper", {"keyword": "帮信罪", "type": "WRONG"})
    print(f"测试7 read/paper错误type枚举: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试8：相关性检查 - 返回不相关论文
    fake_data = {
        "Code": "success",
        "pageInfo": {
            "totalCount": 50,
            "pageDatas": [
                {"periodical": {"title": "新质生产力发展研究", "keywords": ["新质生产力", "数字经济"]}},
                {"periodical": {"title": "数字经济时代创新", "keywords": ["数字经济"]}},
            ]
        }
    }
    w = check_relevance("read/paper", "帮信罪", fake_data)
    print(f"测试8 相关性检查-不相关论文: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试9：相关性检查 - 返回相关论文
    fake_data2 = {
        "Code": "success",
        "pageInfo": {
            "totalCount": 50,
            "pageDatas": [
                {"periodical": {"title": "帮信罪的司法适用研究", "keywords": ["帮信罪", "帮助信息网络犯罪活动罪"]}},
                {"periodical": {"title": "帮助信息网络犯罪活动罪处罚界限", "keywords": ["帮信罪"]}},
            ]
        }
    }
    w = check_relevance("read/paper", "帮信罪", fake_data2)
    print(f"测试9 相关性检查-相关论文: {'✅ 通过' if not w else f'❌ {w}'}")

    # 测试10：空结果检查
    fake_empty = {"Code": "success", "pageInfo": {"totalCount": 0, "pageDatas": []}}
    w = check_relevance("read/paper", "帮信罪", fake_empty)
    print(f"测试10 相关性检查-空结果: {'✅ 通过' if not w else f'❌ {w}'}")

    print("\n=== 自检完成 ===")
