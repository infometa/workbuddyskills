"""行业分析外部数据获取脚本（fetch_external.py）

为 dd-industry-analysis 提供外部数据增强能力，用于 E1-E8 维度的数据补充。
遵循 stdin JSON → stdout JSON 标准模式。

支持的 action：
  - search: 搜索引擎检索（百度/搜狗/DuckDuckGo，中文财经优先）
  - structured_data: 结构化市场数据（宏观经济 GDP/CPI/PPI/PMI、期货、Shibor）
  - stock_realtime: 股票/基金实时行情（用于竞争对手市值对比）
  - sentiment: 行业舆情/竞争对手动态

用法：
    echo '{"action": "search", "query": "光伏行业 2025 市场规模"}' | python3 scripts/fetch_external.py
    echo '{"action": "structured_data", "data_type": "macro_gdp"}' | python3 scripts/fetch_external.py
    echo '{"action": "stock_realtime", "code": "601012"}' | python3 scripts/fetch_external.py
    echo '{"action": "sentiment", "target": "光伏行业", "days": 7}' | python3 scripts/fetch_external.py

输出 JSON（stdout）：
    {
      "success": true,
      "action": "structured_data",
      "results": [...],
      "fallback_needed": false,
      "error": null
    }

降级策略：
    脚本内部会尝试多种通道（akshare → 搜索引擎 → 直接爬取），全部失败时
    返回 fallback_needed=true，由 Agent 决定是否调用 web_search MCP 工具兜底。
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

# akshare 数据类型映射
AKSHARE_ROUTES = {
    "macro_gdp": {"func": "macro_china_gdp", "defaults": {"start_year": "2020"}},
    "macro_cpi": {"func": "macro_china_cpi", "defaults": {"start_year": "2020"}},
    "macro_ppi": {"func": "macro_china_ppi", "defaults": {"start_year": "2020"}},
    "macro_pmi": {"func": "macro_china_pmi", "defaults": {}},
    "futures_spot": {"func": "futures_zh_spot", "defaults": {"symbol": ""}},
    "shibor": {"func": "money_interest_shibor", "defaults": {}},
    "hk_spot": {"func": "stock_hk_spot_em", "defaults": {}},
    "us_spot": {"func": "stock_us_spot_em", "defaults": {}},
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
    """标题相似度（Jaccard）。"""
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
    matches = pattern.findall(html)
    for href, title_html in matches[:limit]:
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
    """获取结构化市场数据（通过 akshare）。

    akshare 未安装时返回 fallback_needed=true。
    """
    data_type = params.get("data_type", "")
    kwargs = params.get("kwargs", {})

    if not data_type:
        return {"success": False, "results": [], "fallback_needed": True, "error": "data_type 为空"}

    route = AKSHARE_ROUTES.get(data_type)
    if not route:
        available = list(AKSHARE_ROUTES.keys())
        return {"success": False, "results": [], "fallback_needed": True, "error": f"未知 data_type: {data_type}，可用: {available}"}

    # 尝试导入 akshare
    try:
        import akshare as ak
    except ImportError:
        return {
            "success": False,
            "results": [],
            "fallback_needed": True,
            "error": "akshare 未安装，建议降级为 web_search 获取宏观数据",
        }

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

        # DataFrame → JSON 序列化
        if hasattr(df, "to_dict"):
            records = df.head(50).to_dict(orient="records")  # 限制返回行数
            # 处理 NaN 和 Timestamp
            for row in records:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif v != v:  # NaN check
                        row[k] = None
            return {"success": True, "results": records, "fallback_needed": False, "error": None}
        else:
            return {"success": True, "results": [str(df)], "fallback_needed": False, "error": None}

    except Exception as e:
        return {"success": False, "results": [], "fallback_needed": True, "error": f"akshare 调用失败: {e}"}


# ============== 股票实时行情 ==============

def action_stock_realtime(params: Dict[str, Any]) -> Dict[str, Any]:
    """获取股票/基金实时行情（通过东方财富 API）。"""
    code = params.get("code", "")
    if not code:
        return {"success": False, "results": [], "fallback_needed": True, "error": "code 为空"}

    # 尝试 akshare
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            # 按代码筛选
            matched = df[df["代码"].str.contains(code)]
            if not matched.empty:
                records = matched.head(5).to_dict(orient="records")
                return {"success": True, "results": records, "fallback_needed": False, "error": None}
    except ImportError:
        pass
    except Exception:
        pass

    # 降级：东方财富 HTTP API
    try:
        # 判断市场（6开头=上海，其他=深圳）
        market = "1" if code.startswith("6") else "0"
        url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f170"
        html = _http_get(url)
        if html:
            data = json.loads(html)
            if data.get("data"):
                d = data["data"]
                result = {
                    "code": d.get("f57", code),
                    "name": d.get("f58", ""),
                    "price": d.get("f43", 0) / 100 if d.get("f43") else None,
                    "change_pct": d.get("f170", 0) / 100 if d.get("f170") else None,
                    "high": d.get("f44", 0) / 100 if d.get("f44") else None,
                    "low": d.get("f45", 0) / 100 if d.get("f45") else None,
                    "volume": d.get("f47"),
                    "amount": d.get("f48"),
                }
                return {"success": True, "results": [result], "fallback_needed": False, "error": None}
    except RateLimitError as e:
        return {"success": False, "results": [], "fallback_needed": True, "error": f"限流: {e}"}
    except Exception as e:
        return {"success": False, "results": [], "fallback_needed": True, "error": str(e)}

    return {"success": False, "results": [], "fallback_needed": True, "error": "行情获取失败，建议降级为 web_search"}


# ============== 行业舆情 ==============

def action_sentiment(params: Dict[str, Any]) -> Dict[str, Any]:
    """行业舆情/竞争对手动态获取。"""
    target = params.get("target", "")
    days = params.get("days", 7)
    limit = params.get("limit", 15)

    if not target:
        return {"success": False, "results": [], "fallback_needed": True, "error": "target 为空"}

    queries = [
        f"{target} 行业动态 最新",
        f"{target} 市场趋势 政策",
    ]

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
    return {"success": False, "results": [], "fallback_needed": True, "error": last_error or "行业舆情无结果，建议降级为 web_search"}


# ============== 主入口 ==============

ACTIONS = {
    "search": action_search,
    "structured_data": action_structured_data,
    "stock_realtime": action_stock_realtime,
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
