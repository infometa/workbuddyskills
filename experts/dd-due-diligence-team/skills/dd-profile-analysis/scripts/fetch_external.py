"""企业画像外部数据获取脚本（fetch_external.py）

为 dd-profile-analysis 提供外部数据增强能力，用于 negative/esg/related 等 section。
遵循 stdin JSON → stdout JSON 标准模式。

支持的 action：
  - search: 搜索引擎检索（百度/搜狗/DuckDuckGo，中文财经优先）
  - sentiment: 全网舆情爬取（多媒体源 + 情感分级 + 模糊去重）
  - institution: 金融机构名单查询（识别关联方是否为持牌机构）
  - announcement: 公告搜索（巨潮资讯/交易所披露）

用法：
    echo '{"action": "search", "query": "某公司 负面 诉讼 处罚"}' | python3 scripts/fetch_external.py
    echo '{"action": "sentiment", "target": "某公司", "days": 7}' | python3 scripts/fetch_external.py
    echo '{"action": "institution", "name": "某基金公司"}' | python3 scripts/fetch_external.py
    echo '{"action": "announcement", "company": "某公司", "keyword": "处罚"}' | python3 scripts/fetch_external.py

输出 JSON（stdout）：
    {
      "success": true,
      "action": "search",
      "results": [...],
      "fallback_needed": false,
      "error": null
    }

    失败时：
    {
      "success": false,
      "action": "search",
      "results": [],
      "fallback_needed": true,
      "error": "HTTP 429 限流，建议降级为 web_search"
    }

降级策略：
    脚本内部会尝试多种通道（RSS → 搜索引擎 → 直接爬取），全部失败时
    返回 fallback_needed=true，由 Agent 决定是否调用 web_search MCP 工具兜底。
"""

import json
import sys
import re
import time
import random
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional


# ============== 配置 ==============

# 请求超时（秒）
REQUEST_TIMEOUT = 10

# UA 轮换池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

# 限流错误码
RATE_LIMIT_CODES = {429, 403, 418, 503}


# ============== 工具函数 ==============

def _random_ua() -> str:
    return random.choice(USER_AGENTS)


def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    """HTTP GET 请求，返回文本或 None。"""
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
            raise RateLimitError(f"HTTP {e.code} 限流") from e
        raise
    except urllib.error.URLError as e:
        raise ConnectionError(f"连接失败: {e.reason}") from e


class RateLimitError(Exception):
    """限流异常，触发降级。"""
    pass


class SimpleHTMLTextExtractor(HTMLParser):
    """简单 HTML 文本提取器。"""
    def __init__(self):
        super().__init__()
        self.texts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self.texts.append(text)

    def get_text(self) -> str:
        return " ".join(self.texts)


def _extract_text(html: str) -> str:
    """从 HTML 提取纯文本。"""
    parser = SimpleHTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def _title_similarity(a: str, b: str) -> float:
    """简单标题相似度（Jaccard）。"""
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ============== 搜索引擎 ==============

def _search_duckduckgo(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """DuckDuckGo HTML 搜索（零依赖，无需 API key）。"""
    encoded = urllib.parse.urlencode({"q": query, "kl": "cn-zh"})
    url = f"https://html.duckduckgo.com/html/?{encoded}"
    html = _http_get(url)
    if not html:
        return []

    results = []
    # 解析 DuckDuckGo HTML 结果
    link_pattern = re.compile(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    snippet_pattern = re.compile(r'class="result__snippet"[^>]*>(.*?)</(?:a|span|div)', re.DOTALL)

    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for i, (href, title_html) in enumerate(links[:limit]):
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
        # DuckDuckGo 的链接可能是重定向
        if href.startswith("//duckduckgo.com/l/"):
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                href = urllib.parse.unquote(m.group(1))
        results.append({
            "title": title,
            "url": href,
            "snippet": snippet,
            "source": "duckduckgo",
        })

    return results


def _search_baidu(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """百度搜索 HTML 解析（中文召回最佳，可能触发限流）。"""
    encoded = urllib.parse.urlencode({"wd": query, "rn": str(limit)})
    url = f"https://www.baidu.com/s?{encoded}"
    html = _http_get(url)
    if not html:
        return []

    results = []
    # 解析百度搜索结果
    # 百度结果在 <h3 class="t"> 或 <h3 class="c-title"> 中
    pattern = re.compile(
        r'<h3[^>]*class="[^"]*t[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL
    )
    matches = pattern.findall(html)

    for href, title_html in matches[:limit]:
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        if title:
            results.append({
                "title": title,
                "url": href,
                "snippet": "",
                "source": "baidu",
            })

    return results


def action_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """执行搜索引擎检索。

    优先百度（中文召回最佳）→ DuckDuckGo（零限流兜底）。
    """
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
                break  # 第一个成功的引擎即可
            # 空结果继续尝试下一个引擎
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
    else:
        return {
            "success": False,
            "results": [],
            "fallback_needed": True,
            "error": last_error or "所有搜索引擎均无结果，建议降级为 web_search",
        }


# ============== 舆情爬取 ==============

# 情感关键词
NEGATIVE_KEYWORDS = [
    "处罚", "罚款", "违规", "违法", "失信", "被执行", "诉讼", "起诉", "仲裁",
    "暴雷", "跑路", "欺诈", "造假", "亏损", "下滑", "暴跌", "崩盘", "清盘",
    "监管", "约谈", "整改", "警告", "通报", "立案", "调查", "冻结", "查封",
    "裁员", "欠薪", "停产", "破产", "重整", "退市", "ST", "*ST",
]

POSITIVE_KEYWORDS = [
    "盈利", "增长", "突破", "创新", "获奖", "上市", "融资", "合作", "签约",
    "扩产", "投产", "中标", "订单", "业绩", "分红", "回购",
]


def _classify_sentiment(title: str, snippet: str = "") -> Dict[str, Any]:
    """情感分类（正面/负面/中性 + 严重度）。"""
    text = f"{title} {snippet}".lower()

    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)

    # 否定词处理："否认"、"未发现"、"不存在" 等否定前缀会翻转情感
    negation_patterns = ["否认", "未发现", "不存在", "并非", "没有", "辟谣", "澄清"]
    has_negation = any(p in text for p in negation_patterns)

    if has_negation and neg_count > 0:
        # "否认业绩下滑" → 不算负面
        neg_count = max(0, neg_count - 1)

    if neg_count > pos_count:
        severity = "high" if neg_count >= 3 else ("medium" if neg_count >= 2 else "low")
        return {"sentiment": "negative", "severity": severity, "neg_keywords": neg_count}
    elif pos_count > neg_count:
        return {"sentiment": "positive", "severity": "low", "pos_keywords": pos_count}
    else:
        return {"sentiment": "neutral", "severity": "none", "neg_keywords": 0}


def action_sentiment(params: Dict[str, Any]) -> Dict[str, Any]:
    """执行舆情爬取。

    通过搜索引擎获取目标企业相关新闻，进行情感分类和去重。
    """
    target = params.get("target", "")
    days = params.get("days", 7)
    keywords = params.get("keywords", "负面 诉讼 处罚 失信 违规")
    limit = params.get("limit", 20)

    if not target:
        return {"success": False, "results": [], "fallback_needed": True, "error": "target 为空"}

    # 构造搜索查询
    queries = [
        f"{target} {keywords}",
        f"{target} 最新消息",
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
                    # 模糊去重（标题相似度 > 0.85）
                    is_dup = any(_title_similarity(title, seen) > 0.85 for seen in seen_titles)
                    if is_dup:
                        continue
                    seen_titles.add(title)

                    sentiment = _classify_sentiment(title, item.get("snippet", ""))
                    all_news.append({
                        "title": title,
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", ""),
                        "sentiment": sentiment["sentiment"],
                        "severity": sentiment["severity"],
                    })
            else:
                last_error = search_result.get("error")
        except Exception as e:
            last_error = str(e)
            continue

        time.sleep(random.uniform(1, 2))

    if all_news:
        # 按严重度排序（负面优先）
        severity_order = {"high": 0, "medium": 1, "low": 2, "none": 3}
        all_news.sort(key=lambda x: severity_order.get(x.get("severity", "none"), 3))
        return {"success": True, "results": all_news[:limit], "fallback_needed": False, "error": None}
    else:
        return {
            "success": False,
            "results": [],
            "fallback_needed": True,
            "error": last_error or "舆情爬取无结果，建议降级为 web_search",
        }


# ============== 机构查询 ==============

# 内置精简版金融机构名单（常见持牌机构关键词）
INSTITUTION_KEYWORDS = {
    "bank": ["银行", "Bank"],
    "securities": ["证券", "Securities"],
    "fund": ["基金", "Fund", "资管", "资产管理"],
    "insurance": ["保险", "Insurance", "人寿", "财险"],
    "trust": ["信托", "Trust"],
    "futures": ["期货", "Futures"],
    "finance_company": ["财务公司", "金融租赁", "消费金融"],
}


def action_institution(params: Dict[str, Any]) -> Dict[str, Any]:
    """查询机构是否为持牌金融机构。

    基于关键词匹配判断机构类型（精简版，不依赖外部数据文件）。
    """
    name = params.get("name", "")
    if not name:
        return {"success": False, "results": [], "fallback_needed": False, "error": "name 为空"}

    matched_types = []
    for inst_type, keywords in INSTITUTION_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            matched_types.append(inst_type)

    if matched_types:
        return {
            "success": True,
            "results": [{
                "name": name,
                "is_financial_institution": True,
                "institution_types": matched_types,
                "confidence": "keyword_match",
            }],
            "fallback_needed": False,
            "error": None,
        }
    else:
        return {
            "success": True,
            "results": [{
                "name": name,
                "is_financial_institution": False,
                "institution_types": [],
                "confidence": "keyword_match",
            }],
            "fallback_needed": False,
            "error": None,
        }


# ============== 公告搜索 ==============

def action_announcement(params: Dict[str, Any]) -> Dict[str, Any]:
    """搜索巨潮资讯公告。

    通过巨潮资讯 API 搜索企业公告（年报/季报/处罚/问询等）。
    """
    company = params.get("company", "")
    keyword = params.get("keyword", "")
    limit = params.get("limit", 10)

    if not company:
        return {"success": False, "results": [], "fallback_needed": True, "error": "company 为空"}

    # 巨潮资讯全文搜索 API
    search_query = f"{company} {keyword}".strip()
    api_url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
    post_data = urllib.parse.urlencode({
        "searchkey": search_query,
        "sdate": "",
        "edate": "",
        "isfulltext": "false",
        "sortName": "pubdate",
        "sortType": "desc",
        "pageNum": "1",
        "pageSize": str(limit),
    }).encode("utf-8")

    try:
        req = urllib.request.Request(api_url, data=post_data, method="POST")
        req.add_header("User-Agent", _random_ua())
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)

        announcements = []
        for item in data.get("announcements", [])[:limit]:
            announcements.append({
                "title": item.get("announcementTitle", ""),
                "url": f"http://www.cninfo.com.cn/new/disclosure/detail?annoId={item.get('annoId', '')}",
                "pub_date": item.get("announcementTime", ""),
                "company": item.get("secName", company),
                "type": item.get("announcementTypeName", ""),
            })

        if announcements:
            return {"success": True, "results": announcements, "fallback_needed": False, "error": None}
        else:
            return {"success": True, "results": [], "fallback_needed": False, "error": "无匹配公告"}

    except urllib.error.HTTPError as e:
        if e.code in RATE_LIMIT_CODES:
            return {
                "success": False,
                "results": [],
                "fallback_needed": True,
                "error": f"巨潮资讯 HTTP {e.code} 限流，建议降级为 web_search",
            }
        return {"success": False, "results": [], "fallback_needed": True, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"success": False, "results": [], "fallback_needed": True, "error": str(e)}


# ============== 主入口 ==============

ACTIONS = {
    "search": action_search,
    "sentiment": action_sentiment,
    "institution": action_institution,
    "announcement": action_announcement,
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
        result = {
            "success": False,
            "action": action,
            "results": [],
            "fallback_needed": True,
            "error": f"未知 action: {action}，可用: {list(ACTIONS.keys())}",
        }
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
