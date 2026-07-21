#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯校招官网实时数据抓取工具
==========================================
直接调用 join.qq.com 公开 API，获取招聘公告、宣讲会、岗位类别等结构化信息。
所有接口均无需鉴权。公告/岗位类别用 GET，宣讲会用 POST。

用法:
    python fetch_recruit_info.py notices
    python fetch_recruit_info.py notice <id>
    python fetch_recruit_info.py flow "投递后多久有回复" --question-time "2026-05-10 11:24:00"
    python fetch_recruit_info.py talks
    python fetch_recruit_info.py families
    python fetch_recruit_info.py latest

输出: JSON 格式，便于 Skill 进一步处理
"""
import sys
import json
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from html import unescape
from typing import Any


BASE = "https://join.qq.com/api/v1"
NOTICE_LIST_URL = f"{BASE}/noticeDynamic/getNoticeDynamicList"
NOTICE_DETAIL_URL = f"{BASE}/noticeDynamic/getNoticeDynamicById"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://join.qq.com/notice.html",
    "Accept": "application/json, text/plain, */*",
}
FLOW_TERMS = [
    "招聘对象", "投递", "简历", "网申", "岗位", "修改", "志愿", "部门", "课题",
    "测评", "笔试", "面试", "通知", "进展", "流程", "截止", "时间", "内推", "伯乐码",
    "青云", "实习", "校招", "应届", "录用", "offer", "签约", "毁约", "转正", "材料",
]


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


def http_get(url: str, timeout: int = 15) -> dict[str, Any]:
    """统一 GET 请求，返回 JSON。失败返回 {error: ...}"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.URLError as e:
        return {"error": f"网络错误: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}"}
    except Exception as e:
        return {"error": f"未知错误: {e}"}


def http_post(url: str, body: dict[str, Any] | None = None, timeout: int = 15) -> dict[str, Any]:
    """统一 POST 请求（JSON body），返回 JSON。失败返回 {error: ...}"""
    try:
        payload = json.dumps(body or {}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.URLError as e:
        return {"error": f"网络错误: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON 解析失败: {e}"}
    except Exception as e:
        return {"error": f"未知错误: {e}"}


def html_to_text(html: str) -> str:
    """简易 HTML 转纯文本，保留段落结构"""
    if not html:
        return ""
    html = re.sub(r"</(p|div|li|h[1-6]|tr|br)>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<li[^>]*>", "- ", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    text = unescape(html)
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def parse_time(value: Any, default: datetime | None = None) -> datetime | None:
    """解析官网时间或用户提问时间。"""
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = text.replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[: len(fmt.replace('%', '')) + 8] if fmt == "%Y-%m-%d %H:%M:%S" else text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return default


def truncate_text(text: str, max_chars: int = 1200) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def extract_terms(query: str) -> list[str]:
    query = (query or "").strip().lower()
    terms: list[str] = []
    for term in FLOW_TERMS:
        if term.lower() in query and term not in terms:
            terms.append(term)
    if "投" in query and "投递" not in terms:
        terms.append("投递")
    if "几个" in query and "几个" not in terms:
        terms.append("几个")
    if "同时" in query and "同时" not in terms:
        terms.append("同时")
    for token in re.findall(r"[a-zA-Z0-9]{2,}", query):
        if token not in terms:
            terms.append(token)
    for chunk in re.findall(r"[\u4e00-\u9fa5]{2,}", query):
        if chunk not in terms and len(chunk) <= 12:
            terms.append(chunk)
        for size in (4, 3, 2):
            for i in range(0, max(len(chunk) - size + 1, 0)):
                token = chunk[i : i + size]
                if token not in terms:
                    terms.append(token)
    return terms[:40]



def score_notice(query: str, notice: dict[str, Any], content: str = "") -> tuple[int, list[str]]:
    terms = extract_terms(query)
    title = str(notice.get("title") or "")
    tag = str(notice.get("tag") or "")
    corpus_title = title.lower()
    corpus_tag = tag.lower()
    corpus_content = content.lower()
    score = 0
    matched: list[str] = []

    if query and query.lower() in (corpus_title + " " + corpus_content):
        score += 40
        matched.append(query[:30])

    for term in terms:
        t = term.lower()
        term_score = 0
        if t in corpus_title:
            term_score += 10
        if t in corpus_tag:
            term_score += 6
        if corpus_content and t in corpus_content:
            term_score += 3
        if term_score:
            score += term_score
            matched.append(term)

    if "青云" in query and "青云" in (title + tag + content):
        score += 25
    if "实习" in query and "实习" in (title + tag + content):
        score += 15
    if "faq" in title.lower() or "FAQ" in title:
        score += 5
    return score, sorted(set(matched), key=matched.index)


def recency_score(publish_time: Any, question_time: datetime) -> int:
    publish_dt = parse_time(publish_time)
    if not publish_dt:
        return -1000
    diff_days = abs((question_time - publish_dt).days)
    score = 365 - min(diff_days, 365)
    if publish_dt > question_time:
        score -= 500
    return score


def best_excerpt(content: str, terms: list[str], max_chars: int = 900) -> str:
    if not content:
        return ""
    compact = re.sub(r"\s+", " ", content).strip()
    lower = compact.lower()
    positions = [lower.find(term.lower()) for term in terms if term and lower.find(term.lower()) >= 0]
    if positions:
        start = max(min(positions) - 260, 0)
        end = min(start + max_chars, len(compact))
        return compact[start:end].strip()
    return truncate_text(compact, max_chars)



def get_notices() -> dict[str, Any]:
    """招聘公告列表"""
    data = http_get(NOTICE_LIST_URL)
    if "error" in data:
        return data
    items = ((data.get("data") or {}).get("list") or [])
    simplified = [
        {
            "id": x.get("id"),
            "title": x.get("title"),
            "tag": x.get("noticeTag"),
            "publish_time": x.get("publisheTimeTxt"),
            "type": "视频" if x.get("newsType") == 2 else "公告",
            "detail_url": f"https://join.qq.com/detail.html?id={x.get('id')}",
        }
        for x in items
    ]
    return {"count": len(simplified), "notices": simplified, "source_url": "https://join.qq.com/notice.html"}


def get_notice_detail(notice_id: str) -> dict[str, Any]:
    """单条公告全文"""
    notice_id = str(notice_id or "").strip()
    if not notice_id or len(notice_id) > 80 or not re.fullmatch(r"[A-Za-z0-9_-]+", notice_id):
        return {"error": "无效 notice id"}
    query = urllib.parse.urlencode({"id": notice_id})
    data = http_get(f"{NOTICE_DETAIL_URL}?{query}")
    if "error" in data:
        return data
    d = data.get("data") or {}
    return {
        "id": d.get("id"),
        "title": d.get("title"),
        "tag": d.get("noticeTag"),
        "publish_time": d.get("publisheTimeTxt"),
        "detail_url": f"https://join.qq.com/detail.html?id={d.get('id') or notice_id}",
        "content_text": html_to_text(d.get("cont") or ""),
    }


def match_flow_notices(query: str, question_time: str = "", top_k: int = 3, max_detail: int = 12) -> dict[str, Any]:
    """按问题文本和提问时间动态选择最匹配的官网公告。"""
    query = (query or "").strip()
    if not query:
        return {"success": False, "message": "缺少 query，无法匹配通用流程公告"}

    question_dt = parse_time(question_time, datetime.now()) or datetime.now()
    notices_result = get_notices()
    if "error" in notices_result:
        return {"success": False, "message": notices_result.get("error"), "source_url": "https://join.qq.com/notice.html"}

    notices = notices_result.get("notices") or []
    if not notices:
        return {"success": False, "message": "官网公告列表为空", "source_url": "https://join.qq.com/notice.html"}

    pre_scored = []
    for notice in notices:
        text_score, matched = score_notice(query, notice)
        time_score = recency_score(notice.get("publish_time"), question_dt)
        final_score = text_score * 1000 + time_score
        pre_scored.append((final_score, text_score, notice, matched))
    pre_scored.sort(key=lambda x: x[0], reverse=True)

    detail_candidates = pre_scored[: max(1, min(max_detail, len(pre_scored)))]
    enriched = []
    for _, _, notice, _ in detail_candidates:
        detail = get_notice_detail(str(notice.get("id") or ""))
        if "error" in detail:
            continue
        content = str(detail.get("content_text") or "")
        text_score, matched = score_notice(query, detail, content)
        time_score = recency_score(detail.get("publish_time"), question_dt)
        final_score = text_score * 1000 + time_score
        enriched.append((final_score, text_score, time_score, detail, matched))

    if not enriched:
        return {"success": False, "message": "未能获取公告详情", "source_url": "https://join.qq.com/notice.html"}

    enriched.sort(key=lambda x: x[0], reverse=True)
    selected = []
    for final_score, text_score, time_score, detail, matched in enriched[: max(1, top_k)]:
        selected.append(
            {
                "id": detail.get("id"),
                "title": detail.get("title"),
                "tag": detail.get("tag"),
                "publish_time": detail.get("publish_time"),
                "detail_url": detail.get("detail_url"),
                "match_score": final_score,
                "text_score": text_score,
                "time_score": time_score,
                "matched_terms": matched,
                "excerpt": best_excerpt(str(detail.get("content_text") or ""), matched or extract_terms(query)),
            }
        )

    return {
        "success": True,
        "source": "join.qq.com notice API",
        "source_url": "https://join.qq.com/notice.html",
        "query": query,
        "question_time": question_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "selection_rule": "先按问题与公告标题/标签/正文的相关度打分，再对比提问时间与公告发布时间；同等相关度下优先采用不晚于提问时间且发布时间更近的公告。",
        "selected_notices": selected,
    }


def get_talks() -> dict[str, Any]:
    """宣讲会/直播日程（POST 接口）"""
    data = http_post(f"{BASE}/jointalk/getTalkList")
    if "error" in data:
        return data
    items = ((data.get("data") or {}).get("list") or [])
    simplified = [
        {
            "id": x.get("id"),
            "session": x.get("session"),
            "content": x.get("content"),
            "date": x.get("dateTxt"),
            "time": x.get("timeTxt"),
            "type": "线上直播" if x.get("talkType") == 2 else "线下专场",
            "live_qr": x.get("liveQRCodeUrl"),
            "playback_url": x.get("playUrl") or "",
        }
        for x in items
    ]
    return {"count": len(simplified), "talks": simplified}


def get_position_families() -> dict[str, Any]:
    """岗位类别"""
    data = http_get(f"{BASE}/position/getPositionFamily")
    if "error" in data:
        return data
    raw = data.get("data") or {}
    families = []
    for fid, lst in raw.items():
        for item in lst or []:
            families.append(
                {
                    "id": item.get("id"),
                    "fid": fid,
                    "title": item.get("title"),
                    "is_qingyun": bool(item.get("isQingyun")),
                }
            )
    return {"count": len(families), "families": families}


def get_latest_overview() -> dict[str, Any]:
    """一站式概览：最新3条公告 + 近期5场宣讲会"""
    notices = get_notices()
    talks = get_talks()
    return {
        "latest_notices": (notices.get("notices") or [])[:3] if "notices" in notices else [],
        "upcoming_talks": (talks.get("talks") or [])[:5] if "talks" in talks else [],
        "tip": "通用流程问题使用: python scripts/fetch_recruit_info.py flow \"<问题>\" --question-time \"<提问时间>\"",
    }


def parse_flow_args(args: list[str]) -> dict[str, Any]:
    query_parts: list[str] = []
    question_time = ""
    top_k = 3
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--question-time", "--time"} and i + 1 < len(args):
            question_time = args[i + 1]
            i += 2
        elif arg == "--top-k" and i + 1 < len(args):
            try:
                top_k = max(1, min(int(args[i + 1]), 5))
            except ValueError:
                top_k = 3
            i += 2
        elif arg == "--query" and i + 1 < len(args):
            query_parts.append(args[i + 1])
            i += 2
        else:
            query_parts.append(arg)
            i += 1
    return {"query": " ".join(query_parts).strip(), "question_time": question_time, "top_k": top_k}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1].lower()
    if cmd == "flow":
        flow_args = parse_flow_args(sys.argv[2:])
        result = match_flow_notices(flow_args["query"], flow_args["question_time"], flow_args["top_k"])
    elif cmd == "notices":
        result = get_notices()
    elif cmd == "notice":
        result = get_notice_detail(sys.argv[2]) if len(sys.argv) >= 3 else {"error": "缺少 notice id"}
    elif cmd == "talks":
        result = get_talks()
    elif cmd == "families":
        result = get_position_families()
    elif cmd == "latest":
        result = get_latest_overview()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
