#!/usr/bin/env python3
"""
万方选题 API 统一调用脚本 (Wanfang Topic CLI)

功能：
1. 封装 find Data → cluster → Paper 两步联动为一键调用
2. 内置参数校验（调用前）+ 相关性检查（调用后）
3. 支持单接口调用和多维度批量调用

用法：
  export APP_KEY="你的万方AppKey"
  python bin/wanfang_topic_cli.py --keyword "帮信罪" --action find_all
  python bin/wanfang_topic_cli.py --keyword "帮信罪" --action read_paper --type HIGH
  python bin/wanfang_topic_cli.py --keyword "帮信罪" --action assess --title "标题" --abstract "摘要"
  python bin/wanfang_topic_cli.py --keyword "帮信罪" --action title_recommend
  python bin/wanfang_topic_cli.py --keyword "帮信罪" --action report_novelty
  python bin/wanfang_topic_cli.py --keyword "帮信罪" --action pool_listpapers --classCode B
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import time
from typing import Any

# ============================================================
# 配置（唯一来源，与 references/api.md 保持一致）
# ============================================================

BASE_URL = "https://api.wfdata.com"
APP_KEY = os.environ.get("APP_KEY", "")
CONTENT_TYPE = "application/json"

if not APP_KEY:
    print("⚠️ 未检测到 APP_KEY 环境变量。请先设置：", file=sys.stderr)
    print("  Linux/macOS:  export APP_KEY=\"你的万方AppKey\"", file=sys.stderr)
    print("  Windows:      $env:APP_KEY=\"你的万方AppKey\"", file=sys.stderr)
    sys.exit(1)

# ============================================================
# 参数 Schema（用于调用前校验）
# ============================================================

PARAM_SCHEMA = {
    # read 系列
    "read/paper": {"required": ["keyword", "page", "type"], "valid": {"type": ["HIGH", "NEW", "DEGREE", "REVIEW"]}},
    "read/scholar": {"required": ["keyword", "page", "sort"], "valid": {"sort": ["RELATIVITY", "HINDEX", "ARTICLE", "CITED"]}},

    # assess 系列
    "assess/NoveltyData": {"required": ["title", "keyword", "abstract"]},
    "assess/NoveltyPaper": {"required": ["title", "keyword", "abstract", "type"], "valid": {"type": ["title", "keyword", "abstracts"]}},
    "assess/TopicExtendData": {"required": ["title", "keyword", "abstract"]},
    "assess/TopicExtendPaper": {"required": ["title", "keyword", "abstract", "type"], "valid": {"type": ["HIGH_CNT", "NEWS"]}},
    "assess/SubjectOsmosisData": {"required": ["title", "keyword", "abstract"]},
    "assess/SubjectOsmosisPaper": {"required": ["title", "keyword", "abstract", "education_code"]},

    # find Data 系列
    "find/acadamicData": {"required": ["search", "param"], "valid": {"search": ["KEYWORD", "CODE"]}},
    "find/frontierData": {"required": ["search", "param"], "valid": {"search": ["KEYWORD", "CODE"]}},
    "find/acrossData": {"required": ["search", "param"], "valid": {"search": ["KEYWORD", "CODE"]}},
    "find/newthemeData": {"required": ["search", "param"], "valid": {"search": ["KEYWORD", "CODE"]}},
    "find/hotspot": {"required": ["param", "search"], "valid": {"search": ["HOTS", "NEWS"]}},

    # find Paper 系列
    "find/acadamicPaper": {"required": ["paper", "param"], "valid": {"paper": ["HIGH", "NEW", "DEGREE", "REVIEW"]}},
    "find/frontierPaper": {"required": ["paper", "param"], "valid": {"paper": ["HIGH", "NEW", "DEGREE", "REVIEW"]}},
    "find/acrossPaper": {"required": ["paper", "param"], "valid": {"paper": ["HIGH", "NEW", "DEGREE", "REVIEW"]}},
    "find/newthemePaper": {"required": ["paper", "param"], "valid": {"paper": ["HIGH", "NEW", "DEGREE", "REVIEW"]}},

    # title 系列
    "title/recommend": {"required": ["keyword"]},
    "title/synonyms": {"required": ["keyword", "page"]},

    # report 系列
    "report/reportNovelty": {"required": ["keyword"]},
    "report/reportSocial": {"required": ["keyword"]},
    "report/reportNatural": {"required": ["keyword"]},
    "report/reportPeriodical": {"required": ["keyword"]},
}

# Data → Paper 两步联动映射
DATA_PAPER_MAP = {
    "acadamic": {"data": "find/acadamicData", "paper": "find/acadamicPaper", "data_key": "knowledge", "cluster_field": "cluster"},
    "frontier": {"data": "find/frontierData", "paper": "find/frontierPaper", "data_key": "frontier", "cluster_field": "cluster"},
    "across": {"data": "find/acrossData", "paper": "find/acrossPaper", "data_key": "across", "cluster_field": "cluster"},
    "newtheme": {"data": "find/newthemeData", "paper": "find/newthemePaper", "data_key": "newTheme", "cluster_field": "cluster"},
}


# ============================================================
# 核心函数
# ============================================================

def validate_params(endpoint: str, params: dict) -> list[str]:
    """校验参数名和枚举值，返回错误列表（空列表=通过）"""
    errors = []
    schema = PARAM_SCHEMA.get(endpoint)
    if not schema:
        errors.append(f"未知接口: {endpoint}")
        return errors

    # 检查必选参数
    for req in schema["required"]:
        if req not in params:
            errors.append(f"缺少必选参数: {req}（接口 {endpoint} 需要 {schema['required']}）")

    # 检查枚举值
    for field, valid_values in schema.get("valid", {}).items():
        if field in params and params[field] not in valid_values:
            errors.append(f"参数 {field}={params[field]} 不合法，合法值: {valid_values}")

    # 检查是否误用了通用 param（assess/title/report 系列不应有单独的 param）
    if endpoint.startswith(("read/", "assess/", "title/", "report/")) and "param" in params and endpoint not in PARAM_SCHEMA:
        errors.append(f"接口 {endpoint} 不应使用 param 参数，请检查参数名")

    return errors


def call_api(endpoint: str, params: dict | None = None, method: str = "POST") -> dict:
    """调用万方 API，返回 JSON dict"""
    url = f"{BASE_URL}/topic/{endpoint}"
    headers = {
        "X-Ca-AppKey": APP_KEY,
        "Content-Type": CONTENT_TYPE,
    }

    if method == "GET":
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        data = None
    else:
        data = json.dumps(params or {}).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")}
    except Exception as e:
        return {"error": str(e)}


def find_data_to_paper(keyword: str, dimension: str, paper_type: str = "HIGH") -> dict:
    """
    两步联动：Data → 提取 cluster → Paper
    dimension: acadamic / frontier / across / newtheme
    """
    mapping = DATA_PAPER_MAP.get(dimension)
    if not mapping:
        return {"error": f"未知维度: {dimension}，合法值: {list(DATA_PAPER_MAP.keys())}"}

    # Step 1: 调用 Data 接口
    data_endpoint = mapping["data"]
    data_params = {"search": "KEYWORD", "param": keyword}
    errors = validate_params(data_endpoint, data_params)
    if errors:
        return {"error": "参数校验失败", "details": errors}

    data_result = call_api(data_endpoint, data_params)

    # 提取 cluster 列表
    data_key = mapping["data_key"]
    cluster_field = mapping["cluster_field"]
    nodes = data_result.get(data_key, {}).get("nodes", [])
    if not nodes:
        return {
            "dimension": dimension,
            "keyword": keyword,
            "data_result": data_result,
            "papers": [],
            "message": f"该关键词无{dimension}知识脉络数据（正常返回）"
        }

    # Step 2: 对每个 cluster 调用 Paper 接口
    paper_endpoint = mapping["paper"]
    all_papers = []
    for node in nodes[:5]:  # 限制前5个 cluster，避免过多调用
        cluster = node.get(cluster_field, "")
        if not cluster:
            continue
        paper_params = {"paper": paper_type, "param": cluster}
        errors = validate_params(paper_endpoint, paper_params)
        if errors:
            all_papers.append({"cluster": cluster, "error": errors})
            continue
        paper_result = call_api(paper_endpoint, paper_params)
        papers = paper_result.get("pageInfo", {}).get("pageDatas", [])
        all_papers.append({"cluster": cluster, "count": len(papers), "papers": papers[:3]})  # 每 cluster 取前3篇

    return {
        "dimension": dimension,
        "keyword": keyword,
        "data_nodes": len(nodes),
        "paper_results": all_papers
    }


def check_relevance(endpoint: str, keyword: str, result: dict) -> str:
    """检查返回数据与查询关键词的相关性"""
    if result.get("error"):
        return "ERROR"

    code = result.get("Code", "")
    if code not in ("success", "成功"):
        return f"API_ERROR: Code={code}"

    # 文本类
    if endpoint.startswith(("read/paper", "title/recommend")):
        if endpoint == "read/paper":
            datas = result.get("pageInfo", {}).get("pageDatas", [])
        elif endpoint == "title/recommend":
            datas = result.get("template", {}).get("nodes", [])
        else:
            datas = []
        if not datas:
            return "EMPTY"
        # 检查前3条是否包含关键词
        relevant = 0
        for item in datas[:3]:
            text = json.dumps(item, ensure_ascii=False)
            if keyword in text:
                relevant += 1
        ratio = relevant / min(3, len(datas))
        if ratio >= 0.5:
            return "OK"
        elif ratio > 0:
            return "PARTIAL"
        else:
            return "SUSPICIOUS"

    # 统计类
    if endpoint.startswith("assess/"):
        if "innovation" in result:
            inn = result["innovation"]
            counts = [inn.get("titleCount", "0"), inn.get("keywordCount", "0"), inn.get("abstractCount", "0")]
            if all(c == "0" for c in counts):
                return "ALL_ZERO"
        return "OK"

    # 其他类型默认 OK
    return "OK"


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="万方选题 API 统一调用脚本")
    parser.add_argument("--keyword", "-k", required=True, help="检索关键词")
    parser.add_argument("--action", "-a", required=True, help="操作类型", choices=[
        "read_paper", "read_scholar", "assess", "title_recommend", "title_synonyms",
        "report_novelty", "report_social", "report_natural", "report_periodical",
        "find_acadamic", "find_frontier", "find_across", "find_newtheme",
        "find_all", "assess_all", "report_all",
        "pool_listpapers", "pool_listsubjecttypes", "pool_listtopics", "pool_listnaturals"
    ])
    parser.add_argument("--type", default="HIGH", help="论文类型: HIGH/NEW/DEGREE/REVIEW")
    parser.add_argument("--sort", default="HINDEX", help="学者排序: RELATIVITY/HINDEX/ARTICLE/CITED")
    parser.add_argument("--title", default="", help="选题标题（assess系列需要）")
    parser.add_argument("--abstract", default="", help="选题摘要（assess系列需要）")
    parser.add_argument("--classCode", default="ALL", help="学科分类码（pool/listPapers）")
    parser.add_argument("--page", type=int, default=1, help="页码")

    args = parser.parse_args()
    keyword = args.keyword
    results = {}

    # read 系列
    if args.action == "read_paper":
        params = {"keyword": keyword, "page": args.page, "type": args.type}
        results = call_api("read/paper", params)
        results["_relevance"] = check_relevance("read/paper", keyword, results)

    elif args.action == "read_scholar":
        params = {"keyword": keyword, "page": args.page, "sort": args.sort}
        results = call_api("read/scholar", params)
        results["_relevance"] = check_relevance("read/scholar", keyword, results)

    # assess 系列
    elif args.action == "assess":
        title = args.title or keyword
        abstract = args.abstract or f"本文研究{keyword}的相关问题"
        params = {"title": title, "keyword": keyword, "abstract": abstract}
        results = {"novelty": call_api("assess/NoveltyData", params),
                   "extend": call_api("assess/TopicExtendData", params),
                   "osmosis": call_api("assess/SubjectOsmosisData", params)}

    elif args.action == "assess_all":
        title = args.title or keyword
        abstract = args.abstract or f"本文研究{keyword}的相关问题"
        params = {"title": title, "keyword": keyword, "abstract": abstract}
        results = {
            "NoveltyData": call_api("assess/NoveltyData", params),
            "TopicExtendData": call_api("assess/TopicExtendData", params),
            "SubjectOsmosisData": call_api("assess/SubjectOsmosisData", params),
        }

    # find 系列
    elif args.action.startswith("find_") and args.action != "find_all":
        dim = args.action.replace("find_", "")
        results = find_data_to_paper(keyword, dim, args.type)

    elif args.action == "find_all":
        results = {}
        for dim in ["acadamic", "frontier", "across", "newtheme"]:
            results[dim] = find_data_to_paper(keyword, dim, args.type)

    # title 系列
    elif args.action == "title_recommend":
        params = {"keyword": keyword}
        results = call_api("title/recommend", params)
        results["_relevance"] = check_relevance("title/recommend", keyword, results)

    elif args.action == "title_synonyms":
        params = {"keyword": keyword, "page": args.page}
        results = call_api("title/synonyms", params)

    # report 系列
    elif args.action == "report_novelty":
        results = call_api("report/reportNovelty", {"keyword": keyword})

    elif args.action == "report_social":
        results = call_api("report/reportSocial", {"keyword": keyword})

    elif args.action == "report_natural":
        results = call_api("report/reportNatural", {"keyword": keyword})

    elif args.action == "report_periodical":
        results = call_api("report/reportPeriodical", {"keyword": keyword})

    elif args.action == "report_all":
        results = {
            "reportNovelty": call_api("report/reportNovelty", {"keyword": keyword}),
            "reportSocial": call_api("report/reportSocial", {"keyword": keyword}),
            "reportNatural": call_api("report/reportNatural", {"keyword": keyword}),
            "reportPeriodical": call_api("report/reportPeriodical", {"keyword": keyword}),
        }

    # pool 系列
    elif args.action == "pool_listpapers":
        results = call_api("pool/listPapers", {"page": args.page, "size": 10, "classCode": args.classCode}, method="GET")

    elif args.action == "pool_listsubjecttypes":
        results = call_api("pool/listSubjectTypes", method="GET")

    elif args.action == "pool_listtopics":
        results = call_api("pool/listTopics", {"page": args.page, "size": 10}, method="GET")

    elif args.action == "pool_listnaturals":
        results = call_api("pool/listNaturals", {"page": args.page, "size": 10}, method="GET")

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
