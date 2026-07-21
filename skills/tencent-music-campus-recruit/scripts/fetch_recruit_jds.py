#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯校招官网岗位 JD 抓取与简历匹配兜底工具。

直接调用 join.qq.com 公开接口，不依赖 MCP / TRAG / requests。
用于 campus-recruit-jd-qa MCP 不可用时，仍能基于官网真实岗位名称、JD 描述、任职要求、招聘部门和工作地做推荐。
普通岗位详情使用 desc/request 字段；青云计划课题类岗位详情使用 topicDetail/topicRequirement 字段。
岗位详情页“招聘部门和工作地”来自 /resume/getBGAndDepartmentListByPostId?postId=<post_id>。

用法：
    python scripts/fetch_recruit_jds.py search --keyword 后台 --page-size 10
    python scripts/fetch_recruit_jds.py detail 1200791473415778304
    python scripts/fetch_recruit_jds.py all --max-pages 50 --page-size 100
    python scripts/fetch_recruit_jds.py match "Python 后台 分布式 MySQL Redis 深圳"
    python scripts/fetch_recruit_jds.py dicts
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Tuple


def configure_output_encoding() -> None:
    """Avoid UnicodeEncodeError on Windows terminals with legacy encodings."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


configure_output_encoding()

BASE = "https://join.qq.com/api/v1"
POST_PAGE = "https://join.qq.com/post.html"
ABOUT_PAGE = "https://join.qq.com/about.html"
DETAIL_PAGE = "https://join.qq.com/post_detail.html?postid={post_id}"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_PROJECT_IDS = [1, 2, 12, 14, 20, 21, 5, 15]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Referer": POST_PAGE,
    "Origin": "https://join.qq.com",
    "Accept": "application/json, text/plain, */*",
}

TECH_TERMS = [
    "Python", "Java", "Go", "Golang", "C++", "C/C++", "JavaScript", "TypeScript", "React", "Vue",
    "后台", "后端", "服务端", "前端", "客户端", "测试", "运维", "安全", "数据", "算法", "机器学习", "深度学习",
    "NLP", "自然语言", "多模态", "计算机视觉", "CV", "推荐", "搜索", "大模型", "LLM", "AIGC",
    "分布式", "高并发", "微服务", "数据库", "MySQL", "Redis", "NoSQL", "Kubernetes", "Docker", "Linux",
    "产品", "运营", "市场", "设计", "交互", "视觉", "游戏", "策划", "财务", "HR", "法务",
]
CITY_TERMS = ["深圳", "深圳总部", "北京", "上海", "广州", "成都", "武汉", "杭州", "合肥", "香港", "远程"]
PROJECT_KEYWORDS = {
    "实习": [2, 12, 20],
    "应届": [1, 14, 21],
    "校招": [1, 14, 21],
    "青云": [14, 20],
    "提前批": [21],
}


def _timestamp() -> int:
    return int(time.time() * 1000)


def _json_dumps(data: Any, pretty: bool = True) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)


def _request_json(method: str, path: str, body: Optional[Dict[str, Any]] = None, referer: str = POST_PAGE, timeout: int = 20) -> Dict[str, Any]:
    sep = "&" if "?" in path else "?"
    url = f"{BASE}{path}{sep}timestamp={_timestamp()}"
    headers = {**HEADERS, "Referer": referer}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json;charset=UTF-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        return {"status": -1, "message": f"HTTP {e.code}: {e.reason}", "data": None}
    except urllib.error.URLError as e:
        return {"status": -1, "message": f"网络错误: {e}", "data": None}
    except json.JSONDecodeError as e:
        return {"status": -1, "message": f"JSON 解析失败: {e}", "data": None}
    except Exception as e:
        return {"status": -1, "message": f"未知错误: {e}", "data": None}


def _as_int_list(value: Optional[str]) -> List[int]:
    if not value:
        return []
    out = []
    for part in re.split(r"[,，\s]+", value.strip()):
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            pass
    return out


def _normalize_page_size(value: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = DEFAULT_PAGE_SIZE
    return max(1, min(MAX_PAGE_SIZE, n))


def _flatten_project_ids(items: Iterable[Dict[str, Any]]) -> List[int]:
    ids = []
    for item in items or []:
        children = item.get("subDictionary") or []
        if children:
            ids.extend(_flatten_project_ids(children))
        else:
            code = item.get("code")
            if code is None:
                continue
            try:
                ids.append(int(code))
            except (TypeError, ValueError):
                pass
    return sorted(set(ids))


def get_all_project_ids() -> List[int]:
    data = _request_json("GET", "/position/getAllProject")
    ids = _flatten_project_ids(data.get("data") or []) if data.get("status") == 0 else []
    return ids or DEFAULT_PROJECT_IDS


def get_dicts() -> Dict[str, Any]:
    dictionary = _request_json("GET", "/dictionary/?types=RecruitType,BusinessGroup,RecruitProjectPostList")
    projects = _request_json("GET", "/position/getAllProject")
    families = _request_json("GET", "/position/getPositionFamily?lang=zh-cn")
    work_cities = _request_json("GET", "/position/getPositionWorkCities?lang=zh-cn")
    recruit_cities = _request_json("GET", "/position/getRecruitCity?lang=zh-cn")
    return {
        "success": all(x.get("status") == 0 for x in [dictionary, projects, families, work_cities, recruit_cities]),
        "source": "join.qq.com",
        "dictionary": dictionary.get("data"),
        "projects": projects.get("data"),
        "position_families": families.get("data"),
        "work_cities": work_cities.get("data"),
        "recruit_cities": recruit_cities.get("data"),
    }


def _build_search_body(
    keyword: str = "",
    project_ids: Optional[List[int]] = None,
    bg_ids: Optional[List[int]] = None,
    work_city_ids: Optional[List[int]] = None,
    recruit_city_ids: Optional[List[int]] = None,
    position_family_ids: Optional[List[int]] = None,
    page_index: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:
    return {
        "projectIdList": project_ids or get_all_project_ids(),
        "keyword": (keyword or "").strip()[:30],
        "bgList": bg_ids or [],
        "workCountryType": 0,
        "workCityList": work_city_ids or [],
        "recruitCityList": recruit_city_ids or [],
        "positionFidList": position_family_ids or [],
        "pageIndex": max(1, int(page_index or 1)),
        "pageSize": _normalize_page_size(page_size),
    }


def _first_text(data: Dict[str, Any], *keys: str) -> str:
    """按字段优先级取第一个非空文本；青云岗位会用 topicDetail/topicRequirement 承载 JD。"""
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _field_source(data: Dict[str, Any], *keys: str) -> str:
    """返回第一个非空文本字段名，便于排查官网字段来源。"""
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return key
    return ""


def _format_department_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "department_id": item.get("id"),
        "department_name": item.get("name") or "",
        "bg_id": item.get("bgid"),
        "introduction": item.get("comment") or "",
        "work_cities": item.get("workCityList") or [],
        "work_city_codes": item.get("workCity") or "",
    }


def get_departments_by_post_id(post_id: str) -> Dict[str, Any]:
    """获取岗位详情页“招聘部门和工作地”模块数据。

    页面结构来自独立接口：
    /resume/getBGAndDepartmentListByPostId?postId=<post_id>
    返回 BG 分组及其 departmentList，每个部门包含 name/comment/workCityList。
    """
    post_id = (post_id or "").strip()
    if not post_id:
        return {"success": False, "message": "postId 不能为空", "departments_by_bg": [], "department_names": []}
    referer = DETAIL_PAGE.format(post_id=urllib.parse.quote(post_id))
    data = _request_json("GET", f"/resume/getBGAndDepartmentListByPostId?postId={urllib.parse.quote(post_id)}", referer=referer)
    if data.get("status") != 0:
        return {
            "success": False,
            "source": "join.qq.com",
            "message": data.get("message") or "未获取到招聘部门信息",
            "departments_by_bg": [],
            "department_names": [],
        }

    groups = []
    department_names: List[str] = []
    bg_names: List[str] = []
    for group in data.get("data") or []:
        departments = [_format_department_item(x) for x in (group.get("departmentList") or [])]
        if not departments:
            continue
        bg_name = group.get("showTitle") or group.get("title") or ""
        if bg_name:
            bg_names.append(bg_name)
        for dep in departments:
            name = dep.get("department_name") or ""
            if name:
                department_names.append(name)
        groups.append({
            "bg_id": group.get("id"),
            "bg_name": bg_name,
            "departments": departments,
        })

    return {
        "success": True,
        "source": "join.qq.com",
        "department_source_api": "/resume/getBGAndDepartmentListByPostId",
        "departments_by_bg": groups,
        "department_names": list(dict.fromkeys(department_names)),
        "bg_names": list(dict.fromkeys(bg_names)),
    }


def _format_intro_department_item(item: Dict[str, Any], bg_name: str = "") -> Dict[str, Any]:
    return {
        "department_id": item.get("id"),
        "department_name": item.get("name") or "",
        "bg_id": item.get("bgid"),
        "bg_name": bg_name,
        "introduction": item.get("comment") or "",
    }


def get_department_introductions() -> Dict[str, Any]:
    """获取 about.html 组织架构中的 BG 与部门介绍。

    页面数据来自独立接口：
    /resume/getBGAndDepartmentIntroduction
    返回 BG 分组及其 departmentList，每个部门包含 name/comment。
    """
    data = _request_json("GET", "/resume/getBGAndDepartmentIntroduction", referer=ABOUT_PAGE)
    if data.get("status") != 0:
        return {
            "success": False,
            "source": "join.qq.com",
            "source_page": ABOUT_PAGE,
            "source_api": "/resume/getBGAndDepartmentIntroduction",
            "message": data.get("message") or "未获取到官网组织架构/部门介绍信息",
            "orgs": [],
            "departments": [],
        }

    orgs = []
    departments: List[Dict[str, Any]] = []
    for group in data.get("data") or []:
        bg_name = group.get("title") or group.get("showTitle") or ""
        dept_items = [_format_intro_department_item(x, bg_name=bg_name) for x in (group.get("departmentList") or [])]
        orgs.append({
            "bg_id": group.get("id"),
            "bg_name": bg_name,
            "departments": dept_items,
            "department_count": len(dept_items),
        })
        departments.extend(dept_items)

    return {
        "success": True,
        "source": "join.qq.com",
        "source_page": ABOUT_PAGE,
        "source_api": "/resume/getBGAndDepartmentIntroduction",
        "count": len(orgs),
        "department_count": len(departments),
        "orgs": orgs,
        "departments": departments,
    }


def _contains_keyword(*values: str, keyword: str) -> bool:
    keyword = (keyword or "").strip().lower()
    if not keyword:
        return True
    return any(keyword in (value or "").lower() for value in values)


def search_departments(keyword: str = "", bg_keyword: str = "", limit: int = 20) -> Dict[str, Any]:
    """按 BG 名、部门名或简介关键词搜索 about 页面部门介绍。"""
    org_data = get_department_introductions()
    if not org_data.get("success"):
        return org_data

    keyword = (keyword or "").strip()
    bg_keyword = (bg_keyword or "").strip()
    limit = max(1, int(limit or 20))
    matches = []
    for dep in org_data.get("departments") or []:
        if bg_keyword and not _contains_keyword(dep.get("bg_name", ""), keyword=bg_keyword):
            continue
        if keyword and not _contains_keyword(dep.get("department_name", ""), dep.get("introduction", ""), dep.get("bg_name", ""), keyword=keyword):
            continue
        matches.append(dep)

    return {
        "success": True,
        "source": org_data.get("source"),
        "source_page": org_data.get("source_page"),
        "source_api": org_data.get("source_api"),
        "keyword": keyword,
        "bg_keyword": bg_keyword,
        "count": len(matches),
        "matches": matches[:limit],
        "message": "ok" if matches else "未在官网组织架构数据中匹配到相关 BG 或部门介绍",
    }


def _format_list_item(item: Dict[str, Any]) -> Dict[str, Any]:
    post_id = str(item.get("postId") or "")
    return {
        "post_id": post_id,
        "position_id": item.get("id"),
        "position_code": item.get("position"),
        "title": item.get("positionTitle") or "",
        "direction_id": item.get("positionFamily"),
        "project_id": item.get("projectId"),
        "project_name": item.get("projectName") or "",
        "recruit_label": item.get("recruitLabelName") or "",
        "bgs": (item.get("bgs") or "").strip(),
        "work_cities": (item.get("workCities") or "").strip(),
        "source": item.get("positionSource") or "join.qq.com",
        "apply_url": DETAIL_PAGE.format(post_id=urllib.parse.quote(post_id)) if post_id else POST_PAGE,
    }


def _search_positions_api(
    keyword: str = "",
    project_ids: Optional[List[int]] = None,
    bg_ids: Optional[List[int]] = None,
    work_city_ids: Optional[List[int]] = None,
    recruit_city_ids: Optional[List[int]] = None,
    position_family_ids: Optional[List[int]] = None,
    page_index: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:
    body = _build_search_body(
        keyword=keyword,
        project_ids=project_ids,
        bg_ids=bg_ids,
        work_city_ids=work_city_ids,
        recruit_city_ids=recruit_city_ids,
        position_family_ids=position_family_ids,
        page_index=page_index,
        page_size=page_size,
    )
    data = _request_json("POST", "/position/searchPosition", body=body)
    payload = data.get("data") or {}
    raw_items = payload.get("positionList") or []
    items = [_format_list_item(x) for x in raw_items]
    return {
        "success": data.get("status") == 0,
        "source": "join.qq.com",
        "query": body,
        "count": payload.get("count", len(items)),
        "page_index": body["pageIndex"],
        "page_size": body["pageSize"],
        "positions": items,
        "message": data.get("message") or ("ok" if data.get("status") == 0 else "接口返回异常"),
    }


def _keyword_terms(keyword: str) -> List[str]:
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    lower_keyword = keyword.lower()
    terms: List[str] = []
    known_terms = list(PROJECT_KEYWORDS.keys()) + TECH_TERMS + CITY_TERMS + ["青云", "青云计划", "qingyun"]
    for term in known_terms:
        if term.lower() in lower_keyword:
            terms.append("青云" if term.lower() == "qingyun" else term)
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,20}", keyword):
        terms.append(token)
    if not terms:
        terms.extend(x for x in re.split(r"[\s,，/、|]+", keyword) if x)
    return list(dict.fromkeys(x.lower() for x in terms if x.strip()))



def _matches_keyword_locally(item: Dict[str, Any], keyword: str) -> bool:
    terms = _keyword_terms(keyword)
    if not terms:
        return True
    haystack = " ".join(str(item.get(k) or "") for k in [
        "title", "project_name", "recruit_label", "bgs", "work_cities", "position_code"
    ]).lower()
    return all(term in haystack for term in terms)


def _merge_positions(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen = set()
    for group in groups:
        for item in group or []:
            key = item.get("post_id") or item.get("position_id") or item.get("title")
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def search_positions(
    keyword: str = "",
    project_ids: Optional[List[int]] = None,
    bg_ids: Optional[List[int]] = None,
    work_city_ids: Optional[List[int]] = None,
    recruit_city_ids: Optional[List[int]] = None,
    position_family_ids: Optional[List[int]] = None,
    page_index: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:
    api_result = _search_positions_api(
        keyword=keyword,
        project_ids=project_ids,
        bg_ids=bg_ids,
        work_city_ids=work_city_ids,
        recruit_city_ids=recruit_city_ids,
        position_family_ids=position_family_ids,
        page_index=page_index,
        page_size=page_size,
    )
    keyword = (keyword or "").strip()
    if not keyword or not api_result.get("success"):
        return api_result

    all_result = fetch_all_positions(
        max_pages=50,
        page_size=100,
        keyword=keyword,
        project_ids=project_ids,
        bg_ids=bg_ids,
        work_city_ids=work_city_ids,
        recruit_city_ids=recruit_city_ids,
        position_family_ids=position_family_ids,
    )
    local_matches = (all_result.get("positions") or []) if all_result.get("success") else []
    api_items = api_result.get("positions") or []
    merged = _merge_positions(api_items, local_matches)
    api_result["positions"] = merged
    api_result["count"] = max(int(api_result.get("count") or 0), len(merged))
    api_result["api_title_match_count"] = len(api_items)
    api_result["local_field_match_count"] = len(local_matches)
    if local_matches:
        api_result["note"] = "官网 keyword 搜索可能只匹配岗位标题；已补充全量岗位中的招聘标签、项目名称等字段本地匹配，避免青云等岗位漏召回。"
    return api_result


def get_jd_detail(post_id: str) -> Dict[str, Any]:
    post_id = (post_id or "").strip()
    if not post_id:
        return {"success": False, "message": "postId 不能为空", "data": None}
    referer = DETAIL_PAGE.format(post_id=urllib.parse.quote(post_id))
    data = _request_json("GET", f"/jobDetails/getJobDetailsByPostId?postId={urllib.parse.quote(post_id)}", referer=referer)
    d = data.get("data") or {}
    if data.get("status") != 0 or not d:
        return {"success": False, "source": "join.qq.com", "message": data.get("message") or "未获取到岗位详情", "post_id": post_id}
    description_keys = ("desc", "topicDetail", "introduction")
    requirement_keys = ("request", "topicRequirement")
    departments = get_departments_by_post_id(post_id)
    detail = {
        "post_id": str(d.get("postId") or post_id),
        "title": d.get("title") or "",
        "direction": d.get("tidName") or "",
        "project_name": d.get("projectName") or "",
        "recruit_label": d.get("recruitLabelName") or "",
        "description": _first_text(d, *description_keys),
        "requirements": _first_text(d, *requirement_keys),
        "description_source_field": _field_source(d, *description_keys),
        "requirements_source_field": _field_source(d, *requirement_keys),
        "graduate_bonus": d.get("graduateBonus") or "",
        "intern_bonus": d.get("internBonus") or "",
        "introduction": d.get("introduction") or "",
        "departments": departments.get("department_names") or [],
        "department_groups": departments.get("departments_by_bg") or [],
        "department_bg_names": departments.get("bg_names") or [],
        "department_source_api": departments.get("department_source_api") or "",
        "department_fetch_success": bool(departments.get("success")),
        "work_cities": d.get("workCityList") or [],
        "recruit_cities": d.get("recruitCityList") or [],
        "is_qingyun": bool(d.get("isQingyun")),
        "apply_url": DETAIL_PAGE.format(post_id=urllib.parse.quote(str(d.get("postId") or post_id))),
    }
    return {"success": True, "source": "join.qq.com", "jd": detail}


def fetch_all_positions(
    max_pages: int = 50,
    page_size: int = 100,
    keyword: str = "",
    project_ids: Optional[List[int]] = None,
    bg_ids: Optional[List[int]] = None,
    work_city_ids: Optional[List[int]] = None,
    recruit_city_ids: Optional[List[int]] = None,
    position_family_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    max_pages = max(1, int(max_pages or 1))
    page_size = _normalize_page_size(page_size)
    all_items = []
    total = None
    for page in range(1, max_pages + 1):
        result = _search_positions_api(
            keyword="",
            project_ids=project_ids,
            bg_ids=bg_ids,
            work_city_ids=work_city_ids,
            recruit_city_ids=recruit_city_ids,
            position_family_ids=position_family_ids,
            page_index=page,
            page_size=page_size,
        )
        if not result.get("success"):
            return {"success": False, "source": "join.qq.com", "message": result.get("message"), "positions": all_items}
        if total is None:
            total = result.get("count")
        items = result.get("positions") or []
        if not items:
            break
        all_items.extend(items)
        if total is not None and len(all_items) >= int(total):
            break
    matched_items = [x for x in all_items if _matches_keyword_locally(x, keyword)] if keyword else all_items
    return {
        "success": True,
        "source": "join.qq.com",
        "count": len(matched_items) if keyword else (total or len(all_items)),
        "fetched": len(all_items),
        "positions": matched_items,
        "keyword": keyword or "",
        "note": "已全量抓取后按岗位标题、招聘标签、项目名称、BG、工作地等字段本地匹配。" if keyword else "已全量抓取官网岗位摘要。",
    }



def _extract_terms(text: str) -> Tuple[List[str], List[str], List[int]]:
    text = text or ""
    lower_text = text.lower()
    terms = []
    for term in TECH_TERMS:
        if term.lower() in lower_text:
            terms.append(term)
    cities = [city for city in CITY_TERMS if city in text]
    project_ids = []
    for key, ids in PROJECT_KEYWORDS.items():
        if key in text:
            project_ids.extend(ids)
    english_words = re.findall(r"[A-Za-z][A-Za-z0-9+#.]{1,20}", text)
    for word in english_words:
        if word not in terms and len(terms) < 20:
            terms.append(word)
    return list(dict.fromkeys(terms))[:20], list(dict.fromkeys(cities))[:8], sorted(set(project_ids))


def _score_text(haystack: str, terms: List[str], cities: List[str]) -> Tuple[int, List[str]]:
    haystack_lower = haystack.lower()
    score = 0
    reasons = []
    for term in terms:
        if term and term.lower() in haystack_lower:
            score += 3 if len(term) > 2 else 1
            if len(reasons) < 4:
                reasons.append(f"技能/经历关键词匹配：{term}")
    for city in cities:
        if city and city in haystack:
            score += 2
            if len(reasons) < 4:
                reasons.append(f"工作地偏好匹配：{city}")
    return score, reasons


def match_resume(text: str, top_n: int = 5, detail_candidates: int = 30, max_pages: int = 8) -> Dict[str, Any]:
    terms, cities, project_ids = _extract_terms(text)
    keyword = " ".join(terms[:3]) if terms else ""
    project_filter = project_ids or None
    first = search_positions(keyword=keyword, project_ids=project_filter, page_index=1, page_size=100)
    candidates = first.get("positions") or []
    if len(candidates) < 10:
        candidates = fetch_all_positions(max_pages=max_pages, page_size=100).get("positions") or candidates

    scored = []
    for item in candidates:
        text_for_score = " ".join([
            item.get("title", ""), item.get("project_name", ""), item.get("recruit_label", ""),
            item.get("bgs", ""), item.get("work_cities", ""),
        ])
        score, reasons = _score_text(text_for_score, terms, cities)
        if score > 0:
            scored.append((score, item, reasons))
    scored.sort(key=lambda x: x[0], reverse=True)
    shortlist = scored[: max(top_n, detail_candidates)] or [(0, x, []) for x in candidates[:detail_candidates]]

    enriched = []
    for base_score, item, base_reasons in shortlist[:detail_candidates]:
        detail = get_jd_detail(item.get("post_id", ""))
        jd = detail.get("jd") or {}
        jd_text = " ".join([
            jd.get("title", ""), jd.get("direction", ""), " ".join(jd.get("departments") or []),
            " ".join(jd.get("department_bg_names") or []), jd.get("description", ""), jd.get("requirements", ""),
            jd.get("graduate_bonus", ""), jd.get("intern_bonus", ""), " ".join(jd.get("work_cities") or []),
        ])
        extra_score, extra_reasons = _score_text(jd_text, terms, cities)
        reasons = list(dict.fromkeys(base_reasons + extra_reasons))[:4]
        if not reasons:
            reasons = ["岗位信息来自腾讯校招官网，可进一步结合简历细节判断"]
        enriched.append((base_score + extra_score, {**item, "jd": jd, "match_reasons": reasons}))
    enriched.sort(key=lambda x: x[0], reverse=True)
    matches = [x[1] for x in enriched[:top_n]]

    return {
        "success": True,
        "source": "join.qq.com",
        "extracted_terms": terms,
        "city_preferences": cities,
        "project_filter": project_filter or "all",
        "matches": matches,
        "note": "岗位与 JD 均来自腾讯校招官网公开接口；对用户展示时不要输出分数或匹配百分比。",
    }


def main() -> int:
    compact_output = "--compact" in sys.argv[1:]
    argv = [arg for arg in sys.argv[1:] if arg != "--compact"]

    parser = argparse.ArgumentParser(description="腾讯校招官网岗位 JD 抓取与匹配兜底工具")
    parser.add_argument("--compact", action="store_true", help="输出紧凑 JSON，可放在子命令前或后")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="搜索官网岗位列表")
    p_search.add_argument("--keyword", default="", help="搜索关键词，最多取前 30 字")
    p_search.add_argument("--project-ids", default="", help="招聘项目 ID，逗号分隔；为空时自动取官网全部项目")
    p_search.add_argument("--bg-ids", default="", help="BG code，逗号分隔")
    p_search.add_argument("--work-city-ids", default="", help="工作城市 code，逗号分隔")
    p_search.add_argument("--recruit-city-ids", default="", help="面试城市 code，逗号分隔")
    p_search.add_argument("--position-family-ids", default="", help="岗位类别 code，逗号分隔，如技术=2、产品=3")
    p_search.add_argument("--page-index", type=int, default=1)
    p_search.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)

    p_detail = sub.add_parser("detail", help="按 postId 获取完整 JD")
    p_detail.add_argument("post_id")

    p_all = sub.add_parser("all", help="分页拉取岗位摘要")
    p_all.add_argument("--keyword", default="")
    p_all.add_argument("--max-pages", type=int, default=50)
    p_all.add_argument("--page-size", type=int, default=100)

    p_match = sub.add_parser("match", help="根据简历/背景文本匹配官网岗位")
    p_match.add_argument("text", help="简历或背景文本")
    p_match.add_argument("--top-n", type=int, default=5)
    p_match.add_argument("--detail-candidates", type=int, default=30)
    p_match.add_argument("--max-pages", type=int, default=8)

    sub.add_parser("orgs", help="获取 about.html 组织架构 BG 与部门介绍")

    p_department = sub.add_parser("department", help="按 BG/部门/关键词搜索官网部门介绍")
    p_department.add_argument("--keyword", default="", help="部门名称或简介关键词")
    p_department.add_argument("--bg", default="", help="BG/事业群关键词，如 CDG、IEG、微信")
    p_department.add_argument("--limit", type=int, default=20, help="最多返回部门数量")

    sub.add_parser("dicts", help="获取官网筛选字典")

    args = parser.parse_args(argv)
    args.compact = compact_output or bool(getattr(args, "compact", False))
    if args.cmd == "search":
        has_filters = any([
            (args.keyword or "").strip(),
            (args.project_ids or "").strip(),
            (args.bg_ids or "").strip(),
            (args.work_city_ids or "").strip(),
            (args.recruit_city_ids or "").strip(),
            (args.position_family_ids or "").strip(),
        ])
        if not has_filters and args.page_index == 1 and args.page_size == DEFAULT_PAGE_SIZE:
            result = fetch_all_positions(max_pages=50, page_size=100)
            result["note"] = "未提供筛选条件，已自动改为全量抓取，避免只返回第一页岗位。"
        else:
            result = search_positions(
                keyword=args.keyword,
                project_ids=_as_int_list(args.project_ids),
                bg_ids=_as_int_list(args.bg_ids),
                work_city_ids=_as_int_list(args.work_city_ids),
                recruit_city_ids=_as_int_list(args.recruit_city_ids),
                position_family_ids=_as_int_list(args.position_family_ids),
                page_index=args.page_index,
                page_size=args.page_size,
            )
    elif args.cmd == "detail":
        result = get_jd_detail(args.post_id)
    elif args.cmd == "all":
        result = fetch_all_positions(max_pages=args.max_pages, page_size=args.page_size, keyword=args.keyword)
    elif args.cmd == "match":
        result = match_resume(args.text, top_n=args.top_n, detail_candidates=args.detail_candidates, max_pages=args.max_pages)
    elif args.cmd == "orgs":
        result = get_department_introductions()
    elif args.cmd == "department":
        result = search_departments(keyword=args.keyword, bg_keyword=args.bg, limit=args.limit)
    elif args.cmd == "dicts":
        result = get_dicts()
    else:
        parser.print_help()
        return 1

    print(_json_dumps(result, pretty=not args.compact))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
