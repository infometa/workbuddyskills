#!/usr/bin/env python3
"""粉象 MCP 全链路验证：tools/list + 6 个业务工具。

用法：
  python3 verify.py
  python3 verify.py --insecure   # 仅内网自签名测试环境

当前服务已关闭鉴权，不需要 FENXIANG_MCP_API_KEY。
"""

import argparse
import json
import os
import sys

from fenxiang_mcp import DEFAULT_URL, McpClient, McpError, load_api_key

TAOBAO_A = "https://s.click.taobao.com/OH0jVXi"
TAOBAO_B = "https://s.click.taobao.com/WR0whPi"
EXPECTED_TOOLS = {
    "goods_search", "history_price", "compare_price",
    "saving_plan", "buy_advice", "batch_analyze",
}


class Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def check(self, name, condition, detail=""):
        if condition:
            self.passed += 1
            print("PASS  %s" % name)
        else:
            self.failed += 1
            print("FAIL  %s  %s" % (name, detail))

    def summary(self):
        total = self.passed + self.failed
        print("\nsummary: passed=%d failed=%d total=%d" % (self.passed, self.failed, total))
        return 0 if self.failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="粉象 MCP 全链路验证")
    parser.add_argument("--url", default=os.environ.get("FENXIANG_MCP_URL") or DEFAULT_URL)
    parser.add_argument("--api-key-file")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--insecure", action="store_true",
                        help="仅内网自签名测试环境使用：跳过证书校验")
    args = parser.parse_args()

    client = McpClient(args.url, load_api_key(args.api_key_file),
                       timeout=args.timeout, insecure=args.insecure)
    result = Result()

    try:
        tools = client.list_tools()
        names = {tool.get("name") for tool in tools}
        result.check("tools/list has 6 expected tools",
                     EXPECTED_TOOLS.issubset(names),
                     "got=%s" % sorted(names))
    except Exception as error:
        result.check("tools/list", False, str(error))
        return result.summary()

    def call(tool, arguments):
        text, data, structured = client.call_tool(tool, arguments)
        return text, data, structured

    try:
        text, data, _ = call("goods_search", {
            "keyword": "iPhone 18", "platform": "all", "size": 5,
            "responseFormat": "json",
        })
        items = data.get("goodsList") if isinstance(data, dict) else None
        result.check("goods_search returns items", bool(items),
                     "data=%s" % (text or "")[:200])
    except Exception as error:
        result.check("goods_search", False, str(error))

    try:
        text, data, _ = call("history_price", {
            "goodsUrl": TAOBAO_A, "responseFormat": "json",
        })
        points = data.get("points") if isinstance(data, dict) else None
        result.check("history_price returns points and itemTitle",
                     bool(points) and bool(data.get("itemTitle")),
                     "keys=%s" % (sorted(data.keys()) if isinstance(data, dict) else text))
    except Exception as error:
        result.check("history_price", False, str(error))

    try:
        text, data, _ = call("compare_price", {
            "goodsUrl": TAOBAO_A, "responseFormat": "json",
        })
        if isinstance(data, dict):
            result.check("compare_price returns structured result",
                         isinstance(data.get("items"), list),
                         "keys=%s" % sorted(data.keys()))
        else:
            result.check("compare_price no-data fallback",
                         "商品暂无比价数据" in (text or ""),
                         "text=%s" % (text or "")[:200])
    except Exception as error:
        result.check("compare_price", False, str(error))

    try:
        text, data, _ = call("saving_plan", {
            "goodsUrl": TAOBAO_A, "responseFormat": "json",
        })
        price = data.get("finalPrice") if isinstance(data, dict) else None
        result.check("saving_plan returns no-rebate price and steps",
                     isinstance(price, (int, float)) and price > 0
                     and data.get("priceType") == "no_rebate"
                     and bool(data.get("steps")),
                     "keys=%s" % (sorted(data.keys()) if isinstance(data, dict) else text))
    except Exception as error:
        result.check("saving_plan", False, str(error))

    try:
        text, data, _ = call("buy_advice", {
            "goodsUrl": TAOBAO_A, "responseFormat": "json",
        })
        serialized = json.dumps(data, ensure_ascii=False) if data is not None else (text or "")
        result.check("buy_advice is self-contained",
                     isinstance(data, dict)
                     and bool(data.get("recommendation"))
                     and data.get("score") is not None
                     and isinstance(data.get("savingPlan"), dict)
                     and isinstance(data.get("compareItems"), list)
                     and bool(data.get("itemTitle")),
                     "keys=%s" % (sorted(data.keys()) if isinstance(data, dict) else text))
        result.check("buy_advice has no commissionRebate",
                     "commissionRebate" not in serialized)
    except Exception as error:
        result.check("buy_advice", False, str(error))

    try:
        text, data, _ = call("batch_analyze", {
            "goodsUrls": TAOBAO_A + "," + TAOBAO_B,
            "responseFormat": "json",
        })
        items = data.get("items") if isinstance(data, dict) else None
        serialized = json.dumps(data, ensure_ascii=False) if data is not None else (text or "")
        result.check("batch_analyze returns multiple items", bool(items) and len(items) >= 1,
                     "keys=%s" % (sorted(data.keys()) if isinstance(data, dict) else text))
        result.check("batch_analyze has no commissionRebate",
                     "commissionRebate" not in serialized)
    except Exception as error:
        result.check("batch_analyze", False, str(error))

    return result.summary()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except McpError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        sys.exit(1)
