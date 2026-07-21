# scripts/deal_watch/hkexnews_fetch.py
"""拉某港股代号的披露易公告。对齐现有 pipeline：urllib 不用 requests。

NOTE (2026-06-08 live-interface fix, see learnings.md):
披露易 titleSearchServlet.do 的真实响应/参数与 plan 初稿的猜测不同，已按实测校正：
  1. 响应顶层不是 {"app":[...]}，而是 {"result":"<JSON字符串>", "recordCnt":N, ...}；
     公告行在 result 这个【再次 json 编码的字符串】里，需二次 json.loads。
  2. 行内字段是大写：STOCK_CODE / TITLE / DATE_TIME / FILE_LINK / STOCK_NAME
     （plan 初稿猜的 stockId/title/date/fileLink/ststockName 不存在）。
  3. 检索不能用上市代号过滤，必须先把上市代号解析成披露易【内部 stockId】。
     解析源 = 静态 JSON activestock_sehk_e.json。
  4. 参数：searchType=0 + stockId=<内部id> + fromDate/toDate 都要给(YYYYMMDD)；
     选了个股后日期跨度可达 12 个月，未选个股则上限 1 个月（官方校验规则）。
parse_announcements 同时兼容 plan/test 的 {"app":[...]} 形态和真实的 {"result":...} 形态，
两套字段名都识别，因此 verbatim 单测照常通过，而 fetch() 走真实接口也能拿到数据。
"""
import datetime
import json, sys, urllib.request, urllib.parse

BASE = "https://www1.hkexnews.hk"
# 披露易 titleSearch JSON 接口（公告搜索）
SEARCH = BASE + "/search/titleSearchServlet.do"
# 在用证券 代号->内部stockId 映射（静态 JSON，行项 {"i":内部id,"c":"00700","n":名称,"s":排序}）
ACTIVE_STOCK = BASE + "/ncms/script/eds/activestock_sehk_e.json"


def default_from_date(today: datetime.date | None = None) -> str:
    """Return the default start date as YYYYMMDD for the recent 30-day window."""
    today = today or datetime.date.today()
    return (today - datetime.timedelta(days=30)).strftime("%Y%m%d")


def _row_to_record(a: dict) -> dict:
    """把一条公告行（兼容大写真实字段 / 小写初稿字段）归一成统一 record。"""
    # 代号：真实=STOCK_CODE，初稿=stockId
    raw_code = a.get("STOCK_CODE", a.get("stockId", ""))
    # 名称：真实=STOCK_NAME，初稿=ststockName/ststockname
    name = a.get("STOCK_NAME") or a.get("ststockName") or a.get("ststockname") or ""
    # 标题：真实=TITLE，初稿=title
    title = a.get("TITLE", a.get("title", ""))
    # 日期：真实=DATE_TIME（'DD/MM/YYYY HH:MM'），初稿=date（'YYYY-MM-DD'）
    date = a.get("DATE_TIME", a.get("date", ""))
    # 文件链接：真实=FILE_LINK，初稿=fileLink（均为以 / 开头的相对路径）
    link = a.get("FILE_LINK", a.get("fileLink", "")) or ""
    return {
        "code": str(raw_code).zfill(5),
        "name": name,
        "title": title,
        "date": date,
        "url": BASE + link if link.startswith("/") else link,
    }


def parse_announcements(raw: str) -> list[dict]:
    """解析披露易公告 JSON。

    兼容两种顶层形态：
      - 真实接口：{"result": "<再次json编码的公告数组字符串>", "recordCnt": N, ...}
      - plan/test：{"app": [ {...}, ... ]}
    """
    data = json.loads(raw)

    rows = data.get("app")
    if rows is None:
        # 真实接口：公告在 result（字符串）里，需二次解析；空结果时 result 可能是 "null"/""
        res = data.get("result")
        if isinstance(res, str) and res not in ("", "null"):
            try:
                rows = json.loads(res)
            except (ValueError, TypeError):
                rows = []
        elif isinstance(res, list):
            rows = res
        else:
            rows = []

    out = []
    for a in rows or []:
        if isinstance(a, dict):
            out.append(_row_to_record(a))
    return out


def _resolve_stock_id(stock_code: str) -> str:
    """把上市代号解析成披露易内部 stockId。解析失败返回 ''。"""
    code5 = stock_code.zfill(5)
    req = urllib.request.Request(ACTIVE_STOCK, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.loads(r.read().decode("utf-8"))
    for it in items:
        if str(it.get("c", "")).zfill(5) == code5:
            return str(it.get("i", ""))
    return ""


def fetch(stock_code: str, from_date: str, to_date: str = "") -> list[dict]:
    """from_date/to_date 格式 YYYYMMDD（to_date 缺省=今天）。返回该代号该区间的公告列表。

    披露易要求按内部 stockId 检索；本函数先解析代号->内部id，再查 titleSearchServlet。
    """
    if not to_date:
        to_date = datetime.date.today().strftime("%Y%m%d")

    internal_id = _resolve_stock_id(stock_code)
    if not internal_id:
        print(f"Unable to resolve HKEX ticker {stock_code}. Please check the ticker code.", file=sys.stderr)
        return []

    params = {
        "sortDir": "0", "sortByOptions": "DateTime",
        "category": "0", "market": "SEHK",
        "stockId": internal_id,
        "documentType": "-1", "fromDate": from_date,
        "toDate": to_date, "title": "",
        "searchType": "0", "t": "1", "lang": "E", "rowRange": "100",
    }
    url = SEARCH + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": BASE + "/search/titlesearch.xhtml"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return parse_announcements(r.read().decode("utf-8"))


if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "00700"
    frm = sys.argv[2] if len(sys.argv) > 2 else default_from_date()
    to = sys.argv[3] if len(sys.argv) > 3 else ""
    for a in fetch(code, frm, to):
        print(f'{a["date"]}  {a["title"]}  {a["url"]}')
