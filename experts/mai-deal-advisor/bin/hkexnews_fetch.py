#!/usr/bin/env python3
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
import json, re, sys, urllib.request, urllib.parse

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
    if not isinstance(data, dict):
        raise ValueError("HKEX 响应结构异常：顶层不是对象")

    if "app" in data:
        rows = data["app"]
    elif "result" in data:
        # 真实接口：公告在 result（字符串）里，需二次解析；空结果时 result 可能是 "null"/""
        res = data.get("result")
        if isinstance(res, str) and res not in ("", "null"):
            try:
                rows = json.loads(res)
            except (ValueError, TypeError) as exc:
                raise ValueError("HKEX result 字段无法解析") from exc
        elif isinstance(res, list):
            rows = res
        else:
            rows = []
        try:
            record_count = int(data["recordCnt"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("HKEX 响应结构异常：缺少有效 recordCnt") from exc
        if record_count > 0 and not rows:
            raise ValueError("HKEX recordCnt 大于零但未解析到公告行")
    else:
        raise ValueError("HKEX 响应结构异常：缺少 app 或 result")

    if not isinstance(rows, list):
        raise ValueError("HKEX 响应结构异常：公告列表不是数组")

    out = []
    for a in rows or []:
        if not isinstance(a, dict):
            raise ValueError("HKEX 响应结构异常：公告行不是对象")
        record = _row_to_record(a)
        if not record["title"] or not record["date"] or not record["url"]:
            raise ValueError("HKEX 响应结构异常：公告行缺少标题、日期或链接")
        out.append(record)
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
        raise LookupError(f"无法在披露易证券列表中解析代码 {stock_code}")

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


def _parse_date(value: str) -> datetime.date:
    return datetime.datetime.strptime(value, "%Y%m%d").date()


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    code = args[0] if args else "00700"
    frm = args[1] if len(args) > 1 else default_from_date()
    to = args[2] if len(args) > 2 else datetime.date.today().strftime("%Y%m%d")

    if not re.fullmatch(r"\d{1,5}", code) or not (1 <= int(code) <= 9999):
        print(f"无效港股代码: {code}。请输入 00001 至 09999 的上市公司代码。", file=sys.stderr)
        return 2
    try:
        start = _parse_date(frm)
        end = _parse_date(to)
    except ValueError:
        print("无效日期区间：日期必须使用 YYYYMMDD。", file=sys.stderr)
        return 2
    if start > end or (end - start).days > 366:
        print("无效日期区间：开始日期不得晚于结束日期，跨度不得超过 366 天。", file=sys.stderr)
        return 2

    try:
        announcements = fetch(code.zfill(5), frm, to)
    except Exception as exc:
        print(f"查询未完成: {exc}", file=sys.stderr)
        return 2

    for a in announcements:
        print(f'{a["date"]}  {a["title"]}  {a["url"]}')
    if not announcements:
        print("[OK] 查询完成，0 条公告")
    elif len(announcements) >= 100:
        print("[UNVERIFIED] 返回达到 100 条上限，结果可能被截断。", file=sys.stderr)
        return 2
    else:
        print(f"[OK] 查询完成，{len(announcements)} 条公告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
