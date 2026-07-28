#!/usr/bin/env python3
"""
发票查验脚本
通过汇联易查验服务进行发票真伪查验（标准 JSON-RPC over SSE 协议）。

用法：
  python3 verify_invoice.py --invoiceTypeNo 113 --invoiceNo ... --billingDate 20251203 --invoiceFee 75.87

API Key 读取优先级（从高到低）：
  1. --apikey 命令行参数
  2. 脚本同目录下的 .apikey 文件
  3. HELIOS_KEY 环境变量

参数说明见 references/parameters.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request

MCP_URL = "https://hlymcp.huilianyi.com:8443/mcp"
MCP_TOOL_NAME = "huilianyi_verify_invoice"

# SSE data line pattern
SSE_DATA_RE = re.compile(r"^data:\s*(.+)$", re.MULTILINE)


def build_params(args: argparse.Namespace) -> dict:
    """Build tool arguments dict from CLI args."""
    arguments = {
        "invoiceTypeNo": args.invoiceTypeNo,
        "invoiceNo": args.invoiceNo,
        "billingDate": args.billingDate,
    }

    if args.invoiceCode is not None:
        arguments["invoiceCode"] = args.invoiceCode
    if args.invoiceAmount is not None:
        arguments["invoiceAmount"] = args.invoiceAmount
    if args.checkCode is not None:
        arguments["checkCode"] = args.checkCode
    if args.invoiceFee is not None:
        arguments["invoiceFee"] = args.invoiceFee
    if args.totalAmount is not None:
        arguments["totalAmount"] = args.totalAmount

    return arguments


def call_mcp(api_key: str, arguments: dict) -> dict:
    """Call the MCP endpoint via standard tools/call protocol and return parsed result."""
    # Standard MCP tools/call payload
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": MCP_TOOL_NAME,
            "arguments": arguments,
        },
        "id": 1,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP_KEY": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"}
    except urllib.error.URLError as e:
        return {"_error": f"网络错误: {e.reason}"}
    except Exception as e:
        return {"_error": f"未知错误: {e}"}

    # Parse SSE response: extract last "data:" line's JSON
    matches = SSE_DATA_RE.findall(raw_body)
    if not matches:
        return {"_error": f"无法解析 SSE 响应: {raw_body[:200]}"}

    try:
        result = json.loads(matches[-1])
    except json.JSONDecodeError as e:
        return {"_error": f"JSON 解析失败: {e}\n原始数据: {matches[-1][:500]}"}

    # Unwrap MCP tool result
    if "result" in result:
        mcp_result = result["result"]
        if isinstance(mcp_result, dict) and "content" in mcp_result:
            content_list = mcp_result["content"]
            if content_list and isinstance(content_list, list):
                text = content_list[0].get("text", "")
                try:
                    inner = json.loads(text)
                except json.JSONDecodeError:
                    inner = {"message": text}
                inner["_isError"] = mcp_result.get("isError", False)
                return inner
        return mcp_result

    if "error" in result and result["error"]:
        return {"_error": f"MCP error {result['error'].get('code','')}: {result['error'].get('message','')}"}

    return result


def format_result(data: dict) -> str:
    """Format the verification result into human-readable output."""
    if "_error" in data:
        return f"❌ 查验失败：{data['_error']}"

    # Code 121800 = "查验成功，发票一致" — treated as success
    code = data.get("code", "")
    message = data.get("message", "")

    if code == "121800" or "查验成功" in message:
        # Extract invoice details from nested data
        details = data.get("details", {})
        invoice_data = details.get("data", {}) or data

        fee_yuan = (invoice_data.get("fee", 0) or 0) / 100
        fee_without_tax = (invoice_data.get("feeWithoutTax", 0) or 0) / 100
        tax = invoice_data.get("tax", "")
        tax_yuan = float(tax) / 100 if tax else 0

        lines = [
            "✅ 发票查验通过 — 该发票真实有效，与税务系统一致",
            "=" * 56,
            f"发票类型:    {invoice_data.get('type', 'N/A')}",
            f"发票号码:    {invoice_data.get('invoiceNo', 'N/A')}",
            f"发票代码:    {invoice_data.get('invoiceCode') or '(电子发票无发票代码)'}",
            f"开票日期:    {invoice_data.get('billingDate', 'N/A')}",
            f"购买方:      {invoice_data.get('title', 'N/A')}",
            f"购买方税号:  {invoice_data.get('draweeNo', 'N/A')}",
            f"销售方:      {invoice_data.get('payee', 'N/A')}",
            f"销售方税号:  {invoice_data.get('payeeNo', 'N/A')}",
            f"价税合计:    ¥{fee_yuan:.2f}",
            f"不含税金额:  ¥{fee_without_tax:.2f}",
            f"税额:        ¥{tax_yuan:.2f}",
            f"税率:        {invoice_data.get('invoiceGoods', [{}])[0].get('taxRate', 'N/A')}%",
            f"货物/服务:   {invoice_data.get('invoiceGoods', [{}])[0].get('goodsName', 'N/A')}",
            f"发票状态:    {invoice_data.get('receiptStatus', 'N/A')}",
            f"是否作废:    {'否' if invoice_data.get('invalidStatus') == 'N' else '是'}",
            "=" * 56,
            f"查验结果码:  {code} ({message})",
        ]
        lines.append("")
        lines.append("提示：查验返回的发票信息与您提供的一致。")
        return "\n".join(lines)

    # Other codes — likely failure
    lines = [
        f"❌ 发票查验未通过",
        "=" * 40,
        f"结果码: {code}",
        f"消息:   {message}",
    ]
    if "details" in data:
        dtl_msg = data["details"].get("message", "")
        if dtl_msg and dtl_msg != message:
            lines.append(f"详情:   {dtl_msg}")
    return "\n".join(lines)


def get_api_key(cli_key=None):
    """Read API key from multiple sources, ordered by priority.

    Priority: CLI arg > .apikey file > HELIOS_KEY env var.
    """
    # 1. CLI --apikey argument (highest priority)
    if cli_key:
        return cli_key

    # 2. .apikey file in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apikey_file = os.path.join(script_dir, "..", ".apikey")
    if os.path.isfile(apikey_file):
        try:
            with open(apikey_file, "r") as f:
                key = f.read().strip()
                if key:
                    return key
        except OSError:
            pass

    # 3. HELIOS_KEY environment variable (fallback)
    return os.environ.get("HELIOS_KEY")


def main():
    parser = argparse.ArgumentParser(description="发票查验")
    parser.add_argument("--apikey", default=None, help="汇联易查验 API Key (优先级最高)")
    parser.add_argument("--invoiceTypeNo", required=True, help="发票类型 (必填)")
    parser.add_argument("--invoiceCode", default=None, help="发票代码 (条件必填)")
    parser.add_argument("--invoiceNo", required=True, help="发票号码 (必填)")
    parser.add_argument("--billingDate", required=True, help="开票日期，格式：20220419 (必填)")
    parser.add_argument("--invoiceAmount", type=float, default=None, help="发票不含税金额，以元为单位 (条件必填)")
    parser.add_argument("--checkCode", default=None, help="校验码后六位 (条件必填)")
    parser.add_argument("--invoiceFee", type=float, default=None, help="发票价税合计，以元为单位 (条件必填)")
    parser.add_argument("--totalAmount", type=float, default=None, help="总金额，以元为单位 (条件必填)")

    args = parser.parse_args()

    # Get API key (priority: --apikey > .apikey file > HELIOS_KEY env var)
    api_key = get_api_key(args.apikey)
    if not api_key:
        print("❌ 错误：未找到 API Key")
        print("请通过以下任一方式提供 API Key：")
        print("  1. 命令行参数：--apikey YOUR_KEY")
        print("  2. 在脚本上级目录创建 .apikey 文件，写入 Key")
        print("  3. 设置环境变量：export HELIOS_KEY=your_api_key")
        sys.exit(1)

    # Build arguments and call
    arguments = build_params(args)
    data = call_mcp(api_key, arguments)

    # Output result
    print(format_result(data))

    # Exit with error code if verification failed
    if "_error" in data:
        sys.exit(1)


if __name__ == "__main__":
    main()
