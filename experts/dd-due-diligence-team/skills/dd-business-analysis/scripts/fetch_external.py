"""经营分析外部数据获取脚本（fetch_external.py）

为 dd-business-analysis 提供外部数据增强能力，用于行业对标和经营背景补充。
遵循 stdin JSON → stdout JSON 标准模式。

支持的 action：
  - search: 搜索引擎检索（百度/搜狗/DuckDuckGo，中文财经优先）
  - structured_data: 结构化市场数据（宏观经济指标作为行业背景）
  - sentiment: 企业经营相关新闻（供应链异常、客户纠纷等）

用法：
    echo '{"action": "search", "query": "某行业 经营指标 同行对标"}' | python3 scripts/fetch_external.py
    echo '{"action": "structured_data", "data_type": "macro_gdp"}' | python3 scripts/fetch_external.py
    echo '{"action": "sentiment", "target": "某公司", "days": 7, "keywords": "供应链 客户 纠纷"}' | python3 scripts/fetch_external.py

输出 JSON（stdout）：
    {
      "success": true,
      "action": "search",
      "results": [...],
      "fallback_needed": false,
      "error": null
    }

降级策略：
    脚本内部会尝试多种通道，全部失败时返回 fallback_needed=true，
    由 Agent 决定是否调用 web_search MCP 工具兜底。
"""

import json
import sys
import re
import time
import random
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


# ============== 配置 ==============

REQUEST_TIMEOUT = 10

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

RATE_LIMIT_CODES = {429, 403, 418, 503}

AKSHARE_ROUTES = {
    "macro_gdp": {"func": "macro_china_gdp", "defaults": {"start_year": "2020"}},
    "macro_cpi": {"func": "macro_china_cpi", "defaults": {"start_year": "2020"}},
    "macro_ppi": {"func": "macro_china_ppi", "defaults": {"start_year": "2020"}},
    "macro_pmi": {"func": "macro_china_pmi", "defaults": {}},
    "shibor": {"func": "money_interest_shibor", "defaults": {}},
}


# ============== 工具函数 ==============

class RateLimitError(Exception):
    pass


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    """HTTP GET 请求。"""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", _random_ua())
    req.add_header("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            try:
                return raw.decode(charset, errors="replace")
            except (LookupError, TypeError):
                return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code in RATE_LIMIT_CODES:
            raise RateLimitError(f"HTTP {e.code}") from e
        raise
    except urllib.error.URLError as e:
        raise ConnectionError(f"连接失败: {e.reason}") from e


def _title_similarity(a: str, b: str) -> float:
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ============== 搜索引擎 ==============

def _search_duckduckgo(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """DuckDuckGo HTML 搜索。"""
    encoded = urllib.parse.urlencode({"q": query, "kl": "cn-zh"})
    url = f"https://html.duckduckgo.com/html/?{encoded}"
    html = _http_get(url)
    if not html:
        return []

    results = []
    link_pattern = re.compile(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    snippet_pattern = re.compile(r'class="result__snippet"[^>]*>(.*?)</(?:a|span|div)', re.DOTALL)
    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for i, (href, title_html) in enumerate(links[:limit]):
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        if href.startswith("//duckduckgo.com/l/"):
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                href = urllib.parse.unquote(m.group(1))
        results.append({"title": title, "url": href, "snippet": snippet, "source": "duckduckgo"})
    return results


def _search_baidu(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """百度搜索 HTML 解析。"""
    encoded = urllib.parse.urlencode({"wd": query, "rn": str(limit)})
    url = f"https://www.baidu.com/s?{encoded}"
    html = _http_get(url)
    if not html:
        return []

    results = []
    pattern = re.compile(
        r'<h3[^>]*class="[^"]*t[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    for href, title_html in pattern.findall(html)[:limit]:
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        if title:
            results.append({"title": title, "url": href, "snippet": "", "source": "baidu"})
    return results


def action_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """搜索引擎检索。"""
    query = params.get("query", "")
    limit = params.get("limit", 10)
    engines = params.get("engines", ["baidu", "duckduckgo"])

    if not query:
        return {"success": False, "results": [], "fallback_needed": True, "error": "query 为空"}

    all_results = []
    last_error = None

    for engine in engines:
        try:
            if engine == "baidu":
                results = _search_baidu(query, limit)
            elif engine == "duckduckgo":
                results = _search_duckduckgo(query, limit)
            else:
                continue
            if results:
                all_results.extend(results)
                break
            time.sleep(random.uniform(0.5, 1.5))
        except RateLimitError as e:
            last_error = str(e)
            time.sleep(random.uniform(1, 3))
            continue
        except Exception as e:
            last_error = str(e)
            continue

    if all_results:
        return {"success": True, "results": all_results[:limit], "fallback_needed": False, "error": None}
    return {"success": False, "results": [], "fallback_needed": True, "error": last_error or "搜索无结果，建议降级为 web_search"}


# ============== 结构化市场数据 ==============

def action_structured_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """获取结构化市场数据（通过 akshare）。"""
    data_type = params.get("data_type", "")
    kwargs = params.get("kwargs", {})

    if not data_type:
        return {"success": False, "results": [], "fallback_needed": True, "error": "data_type 为空"}

    route = AKSHARE_ROUTES.get(data_type)
    if not route:
        return {"success": False, "results": [], "fallback_needed": True, "error": f"未知 data_type: {data_type}，可用: {list(AKSHARE_ROUTES.keys())}"}

    try:
        import akshare as ak
    except ImportError:
        return {"success": False, "results": [], "fallback_needed": True, "error": "akshare 未安装，建议降级为 web_search"}

    func_name = route["func"]
    merged = dict(route["defaults"])
    merged.update(kwargs)

    try:
        func = getattr(ak, func_name, None)
        if func is None:
            return {"success": False, "results": [], "fallback_needed": True, "error": f"akshare 无此函数: {func_name}"}

        df = func(**merged) if merged else func()
        if df is None or (hasattr(df, "empty") and df.empty):
            return {"success": True, "results": [], "fallback_needed": False, "error": "返回空数据"}

        if hasattr(df, "to_dict"):
            records = df.head(50).to_dict(orient="records")
            for row in records:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif v != v:
                        row[k] = None
            return {"success": True, "results": records, "fallback_needed": False, "error": None}
        return {"success": True, "results": [str(df)], "fallback_needed": False, "error": None}
    except Exception as e:
        return {"success": False, "results": [], "fallback_needed": True, "error": f"akshare 调用失败: {e}"}


# ============== 经营舆情 ==============

def action_sentiment(params: Dict[str, Any]) -> Dict[str, Any]:
    """企业经营相关新闻获取。"""
    target = params.get("target", "")
    days = params.get("days", 7)
    keywords = params.get("keywords", "经营 供应链 客户 纠纷")
    limit = params.get("limit", 15)

    if not target:
        return {"success": False, "results": [], "fallback_needed": True, "error": "target 为空"}

    queries = [f"{target} {keywords}", f"{target} 最新动态"]
    all_news = []
    seen_titles = set()
    last_error = None

    for query in queries:
        try:
            search_result = action_search({"query": query, "limit": limit, "engines": ["baidu", "duckduckgo"]})
            if search_result["success"]:
                for item in search_result["results"]:
                    title = item.get("title", "")
                    is_dup = any(_title_similarity(title, seen) > 0.85 for seen in seen_titles)
                    if is_dup:
                        continue
                    seen_titles.add(title)
                    all_news.append({
                        "title": title,
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", ""),
                    })
            else:
                last_error = search_result.get("error")
        except Exception as e:
            last_error = str(e)
            continue
        time.sleep(random.uniform(1, 2))

    if all_news:
        return {"success": True, "results": all_news[:limit], "fallback_needed": False, "error": None}
    return {"success": False, "results": [], "fallback_needed": True, "error": last_error or "经营舆情无结果，建议降级为 web_search"}


# ============== 主入口 ==============

ACTIONS = {
    "search": action_search,
    "structured_data": action_structured_data,
    "sentiment": action_sentiment,
}


def main() -> None:
    """主入口：读 stdin JSON → 执行 action → 写 stdout JSON。"""
    try:
        raw = sys.stdin.read()
        params = json.loads(raw)
    except (json.JSONDecodeError, Exception) as e:
        result = {"success": False, "action": None, "results": [], "fallback_needed": True, "error": f"输入 JSON 解析失败: {e}"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    action = params.get("action", "")
    handler = ACTIONS.get(action)

    if not handler:
        result = {"success": False, "action": action, "results": [], "fallback_needed": True, "error": f"未知 action: {action}，可用: {list(ACTIONS.keys())}"}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    try:
        result = handler(params)
        result["action"] = action
    except RateLimitError as e:
        result = {"success": False, "action": action, "results": [], "fallback_needed": True, "error": f"限流: {e}"}
    except Exception as e:
        result = {"success": False, "action": action, "results": [], "fallback_needed": True, "error": f"执行异常: {e}"}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
