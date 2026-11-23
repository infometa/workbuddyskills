#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""平台判定（Platform Detection）

用账单里的订单号反查 nexus MCP `queryOrderByReferenceNo`，由易仓系统返回的 platform
判定这份账单属于哪个平台；MCP 全部查不到时退回表头指纹判定。

用法:
    python detect_platform.py <账单文件>            # 人类可读摘要
    python detect_platform.py <账单文件> --json     # 输出 JSON（供 Agent 解析）

退出码:
    0  判定成功
    3  判断为歧义（账单混了多个平台 / 多候选并列）
    4  无法判定（MCP 全未命中且表头指纹不匹配）

依赖: Python 3.8+，openpyxl（仅 xlsx 需要），其余为 Python 标准库。
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter

DEFAULT_MCP_URL = "https://datacenter.eccang.com/nexus/mcp/stream"
PROTOCOL_VERSION = "2024-11-05"
TOOL_QUERY_ORDER = "queryOrderByReferenceNo"

# 表头指纹（多语言，覆盖英文 / 葡语导出）
HEADER_TOKENS = (
    "order number", "legacy order id", "order/adjustment id", "related order id",
    "id do pedido", "amazonorderid", "purchase order #", "customer order #",
    "transaction key", "transaction type", "amount type", "settlement amount",
    "total settlement amount", "net amount",
)

# 订单号候选列：先按高优先级列抽样（真正能被 MCP 命中的订单号），低优先级列少量兜底
ORDER_COL_HIGH = (
    "related order id", "order number", "id do pedido", "id de pedido",
    "purchase order #", "amazonorderid",
)
ORDER_COL_LOW = (
    "order/adjustment id", "customer order #", "legacy order id", "transaction key",
)
ORDER_COL_PATTERNS = ORDER_COL_HIGH + ORDER_COL_LOW

# 表头指纹 → 平台（MCP 全部未命中或票数不足时兜底）
PLATFORM_FINGERPRINTS = {
    "tiktok": (("related order id", "total settlement amount", "order/adjustment id"),
               ("order details",)),
    "walmart": (("purchase order #", "transaction key", "amount type", "customer order #"),
                ("结算单", "settlement")),
    "ebay": (("legacy order id", "net amount", "buyer username"),
             ("transaction report",)),
    "amazon": (("id do pedido", "amazonorderid", "id de liquidação", "settlement id",
                "tipo de conta", "marketplace"),
               ("transactions", "交易报告", "settlement")),
}

PLACEHOLDERS = {"", "-", "--", "/", "n/a", "none", "null"}


# ── MCP 客户端（JSON-RPC over Streamable HTTP）─────────────────────────────
class McpError(Exception):
    pass


class Mcp:
    def __init__(self, url=None, timeout=20):
        self.url = (url or os.environ.get("NEXUS_MCP_URL") or DEFAULT_MCP_URL).rstrip("/")
        self.timeout = timeout
        self.session_id = None
        self._ready = False
        self._id = 0

    def _post(self, payload, expect_body=True):
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(
            self.url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    self.session_id = sid
                ctype = (resp.headers.get("Content-Type") or "").lower()
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raise McpError("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:200]))
        except urllib.error.URLError as e:
            raise McpError("MCP 服务不可达（%s）: %s" % (self.url, e.reason))
        if not expect_body or not raw.strip():
            return None
        if "text/event-stream" in ctype or raw.lstrip().startswith(("event:", "data:", "id:", ":")):
            return self._parse_sse(raw)
        return json.loads(raw)

    @staticmethod
    def _parse_sse(text):
        chunks, buf = [], []
        for line in text.splitlines():
            if line.startswith("data:"):
                buf.append(line[5:].lstrip())
            elif not line.strip() and buf:
                chunks.append("\n".join(buf))
                buf = []
        if buf:
            chunks.append("\n".join(buf))
        fallback = None
        for c in chunks:
            c = c.strip()
            if not c:
                continue
            try:
                msg = json.loads(c)
            except ValueError:
                continue
            if "result" in msg or "error" in msg:
                return msg
            fallback = fallback or msg
        if fallback is not None:
            return fallback
        raise McpError("MCP 响应无法解析: %s" % text[:160])

    def _request(self, method, params=None):
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        msg = self._post(payload)
        if msg is None:
            raise McpError("MCP %s 无响应" % method)
        if "error" in msg:
            raise McpError("MCP %s 失败: %s" % (method, msg["error"]))
        return msg.get("result")

    def initialize(self):
        self._request("initialize", {"protocolVersion": PROTOCOL_VERSION,
                                     "capabilities": {},
                                     "clientInfo": {"name": "eccang-detect", "version": "1.0"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_body=False)
        self._ready = True

    def query_order(self, order_id):
        if not self._ready:
            self.initialize()
        result = self._request("tools/call", {"name": TOOL_QUERY_ORDER,
                                              "arguments": {"orderId": str(order_id)}})
        if (result or {}).get("isError"):
            return []
        text = "".join(i.get("text", "") for i in (result or {}).get("content", [])
                       if i.get("type") == "text")
        if not text.strip():
            return []
        try:
            data = json.loads(text)
        except ValueError:
            return []
        if isinstance(data, dict):
            data = data.get("data")
        return data if isinstance(data, list) else []


# ── 读表 ──────────────────────────────────────────────────────────────────
def _decode(raw):
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8/replace"


def _score_header(cells):
    low = [str(c).strip().lower() for c in cells if c and str(c).strip()]
    return sum(1 for t in HEADER_TOKENS if any(t in c for c in low))


def load_table(path):
    """返回 (headers, rows, sheets, encoding)。rows 为表头之后的数据行。"""
    if not os.path.exists(path):
        raise SystemExit("文件不存在: %s" % path)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            best = None
            for sn in wb.sheetnames:
                ws = wb[sn]
                sample = []
                for i, row in enumerate(ws.iter_rows(values_only=True)):
                    sample.append(list(row))
                    if i >= 40:
                        break
                if not sample:
                    continue
                hi = max(range(len(sample)), key=lambda k: _score_header(sample[k]))
                score = _score_header(sample[hi])
                prefer = 1 if "order details" in sn.lower() else 0
                cand = (score + prefer, sn, sample, hi)
                if best is None or cand[0] > best[0]:
                    best = cand
            if best is None:
                raise SystemExit("Excel 无可用 sheet: %s" % path)
            _, sheet, sample, hi = best
            rows = sample[hi + 1:]
            for row in ws_rows_rest(path, sheet, max(hi + 1, len(sample))):
                rows.append(row)
            return list(sample[hi]), rows, wb.sheetnames, "xlsx:" + sheet
        finally:
            wb.close()
    raw = open(path, "rb").read()
    text, enc = _decode(raw)
    sample = text[:8000]
    delim = "," if sample.count(",") >= sample.count("\t") else "\t"
    table = list(csv.reader(io.StringIO(text), delimiter=delim))
    if not table:
        raise SystemExit("文件为空: %s" % path)
    hi = max(range(min(len(table), 40)), key=lambda k: _score_header(table[k]))
    return table[hi], table[hi + 1:], ["csv"], enc + ":" + ("comma" if delim == "," else "tab")


def ws_rows_rest(path, sheet, start):
    """read_only 模式下取剩余行（大文件安全）"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for i, row in enumerate(wb[sheet].iter_rows(values_only=True)):
            if i >= start:
                yield list(row)
    finally:
        wb.close()


# ── 订单号抽取 ─────────────────────────────────────────────────────────────
def clean_id(value):
    s = str(value).strip().strip('"').strip()
    if not s or s.lower() in PLACEHOLDERS:
        return None
    if s.startswith("/") or len(s) < 6:
        return None
    return s


def order_columns(headers):
    """返回 [(优先级, 列下标)]，0 为高优先级"""
    cols = []
    for idx, h in enumerate(headers):
        if not h:
            continue
        low = str(h).strip().lower()
        if any(p in low for p in ORDER_COL_HIGH):
            cols.append((0, idx))
        elif any(p in low for p in ORDER_COL_LOW):
            cols.append((1, idx))
    cols.sort(key=lambda x: x[0])
    return cols


def stratified(ids, per_col=9):
    """每列取分散样本：首 3 + 中 3 + 尾 3，避免只抽到未同步的时段"""
    n = len(ids)
    if n <= per_col:
        return list(ids)
    picks = [0, 1, 2, n // 2 - 1, n // 2, n // 2 + 1, n - 3, n - 2, n - 1]
    out = []
    for i in picks:
        if 0 <= i < n and ids[i] not in out:
            out.append(ids[i])
    return out


def extract_samples(headers, rows):
    """返回 (候选订单号池, 订单号列名)。池按列优先级排列，供分批抽样。"""
    cols = order_columns(headers)
    if not cols:
        return [], []
    buckets = {}
    for prio, idx in cols:
        vals = []
        for r in rows:
            if idx < len(r):
                v = clean_id(r[idx])
                if v and v not in vals:
                    vals.append(v)
        if vals:
            buckets[idx] = (prio, str(headers[idx]).strip(), vals)
    samples = []
    for idx, (prio, _name, vals) in sorted(buckets.items(), key=lambda kv: kv[1][0]):
        for v in stratified(vals, 9 if prio == 0 else 3):
            if v not in samples:
                samples.append(v)
    names = [b[1] for b in sorted(buckets.values(), key=lambda x: x[0])]
    return samples, names


def fingerprint(headers, sheets, path):
    low = " | ".join(str(h).strip().lower() for h in headers if h)
    sheet_low = " | ".join(s.lower() for s in sheets)
    hits = []
    for platform, (cols, sheet_keys) in PLATFORM_FINGERPRINTS.items():
        col_hit = sum(1 for c in cols if c in low)
        sheet_hit = any(k in sheet_low for k in sheet_keys)
        if col_hit >= 2 or (col_hit >= 1 and sheet_hit):
            hits.append((platform, col_hit + (1 if sheet_hit else 0)))
    hits.sort(key=lambda x: -x[1])
    return hits


# ── 主流程 ────────────────────────────────────────────────────────────────
def detect(path, max_sample=36, mcp_url=None, verbose=True):
    headers, rows, sheets, meta = load_table(path)
    pool, cols = extract_samples(headers, rows)
    if len(pool) > max_sample:
        pool = pool[:max_sample]
    result = {
        "file": os.path.basename(path),
        "orders_total": len(rows),
        "order_columns": cols,
        "sampled": 0,
        "method": None,
        "confidence": None,
        "platform": None,
        "companyCode": None,
        "userAccount": None,
        "votes": {},
        "hit": 0,
        "miss": 0,
    }
    if verbose:
        print("[detect] %s | 数据行 %d | 订单号列 %s | 候选样本 %d"
              % (result["file"], len(rows), cols, len(pool)))

    votes = Counter()
    shops = Counter()
    miss = 0
    used = 0
    if pool:
        client = Mcp(mcp_url)
        pos, batch = 0, 12
        while pos < len(pool):
            for oid in pool[pos:pos + batch]:
                used += 1
                try:
                    data = client.query_order(oid)
                except McpError as e:
                    if verbose:
                        print("[detect] MCP 调用中断: %s" % e)
                    pos = len(pool)
                    break
                if not data:
                    miss += 1
                    continue
                top = data[0]
                plat = str(top.get("platform") or "").strip().lower()
                if plat:
                    votes[plat] += 1
                    shops[(top.get("companyCode"), top.get("userAccount"), plat)] += 1
            pos += batch
            total = sum(votes.values())
            if total >= 3 and votes.most_common(1)[0][1] / total >= 0.8:
                break  # 早停

    result["sampled"] = used
    result["votes"] = dict(votes)
    result["hit"] = sum(votes.values())
    result["miss"] = miss

    fp = fingerprint(headers, sheets, path)
    fp_top = fp[0][0] if fp else None

    if votes:
        top_plat, top_n = votes.most_common(1)[0]
        total = sum(votes.values())
        if len(votes) > 1 and top_n / total < 0.8:
            result.update(method="mcp_vote", platform="AMBIGUOUS",
                          candidates=dict(votes), confidence="none")
            if verbose:
                print("[detect] 多平台并列 %s → 需用户确认" % dict(votes))
            return result, 3
        shop = max(shops.items(), key=lambda kv: kv[1])[0]
        if top_n >= 3:
            method, conf = "mcp_vote", "high"
        elif fp_top == top_plat:
            method, conf = "mcp_vote+header_fingerprint", "medium"
        else:
            method, conf = "mcp_vote_low_sample", "low"
        result.update(method=method, platform=top_plat, confidence=conf,
                      companyCode=shop[0], userAccount=shop[1])
        if verbose:
            print("[detect] 判定: %s（%s，MCP %d/%d 票）| 店铺 %s / %s"
                  % (top_plat, conf, top_n, total, shop[0], shop[1]))
        if conf == "low":
            print("[detect] 提示：命中票数偏少（%d 票），建议向用户确认平台后再对账" % top_n)
        return result, 0

    if fp_top:
        result.update(method="header_fingerprint", platform=fp_top, confidence="low",
                      candidates={p: s for p, s in fp})
        if verbose:
            print("[detect] 判定: %s（表头指纹，MCP 无命中 → 置信度低）" % fp_top)
        return result, 0

    result.update(method="none", platform="UNKNOWN", confidence="none")
    if verbose:
        print("[detect] 无法判定：MCP 无命中，表头指纹无匹配")
        print("[detect] 支持格式：TikTok Shop(Order details) / Walmart(结算单/Purchase Order #) "
              "/ eBay(Transaction Report) / Amazon(Settlement/交易报告)")
    return result, 4


def main():
    ap = argparse.ArgumentParser(description="按订单号反查 nexus MCP 判定账单所属平台")
    ap.add_argument("file", help="账单文件路径（xlsx/xls/csv）")
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    ap.add_argument("--max-sample", type=int, default=36, help="最多抽样订单号数量（默认 36）")
    ap.add_argument("--mcp-url", default=None, help="nexus MCP 地址（默认读 NEXUS_MCP_URL 或内置地址）")
    args = ap.parse_args()

    result, code = detect(args.file, args.max_sample, args.mcp_url, verbose=not args.json)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
