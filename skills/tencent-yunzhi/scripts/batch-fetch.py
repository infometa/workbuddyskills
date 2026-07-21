#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch-fetch.py — 批量获取乐享知识库文档内容（v1.3.0 新增）

用法：
  # 拉取一个 v2 知识库下某文件夹所有页面内容到本地 ./out/
  python3 batch-fetch.py --space-id <space_id> --parent-entry-id <folder_entry_id> --out ./out/

  # 拉取一个 v1 团队某目录下所有文档（用 parsed-content 接口）
  python3 batch-fetch.py --v1 --team-id <UUID> --node-id <folder_id> --out ./out/

环境变量：
  LEXIANG_TOKEN  必填，lxmcp_xxx
  COMPANY_FROM   选填，默认 CSIG（永久默认值）

设计目标：
  - 一次脚本完成「列目录 → 区分类型 → 拉取正文 → 落盘」
  - 富文本走 parsed-content（v1）/ ai_parse_content（v2）
  - 文件类型（PDF/PPT 等）下载二进制 + 调用 markitdown 解析
  - 失败容错：单条失败不中断，统计后输出报告
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_HOST = "https://lxapi.lexiangla.com"
DEFAULT_COMPANY_FROM = "CSIG"  # 永久默认值，禁止改动


def get_token() -> str:
    token = os.environ.get("LEXIANG_TOKEN", "").strip()
    if not token or not token.startswith("lxmcp_"):
        sys.exit("❌ 请设置环境变量 LEXIANG_TOKEN（lxmcp_ 开头）")
    return token


def http_get(url: str, token: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_v1_doc_parsed(doc_id: str, token: str) -> str:
    """v1 文档 → parsed_content（已解析 Markdown）"""
    url = f"{API_HOST}/cgi-bin/v1/docs/{doc_id}/parsed-content"
    data = http_get(url, token)
    return data.get("data", {}).get("attributes", {}).get("parsed_content", "")


def fetch_v1_team_docs(team_id: str, node_id: str, token: str) -> list[dict]:
    """列出 v1 团队某目录下的文档"""
    # 实际接口按 references/api-*.md 调整
    url = f"{API_HOST}/cgi-bin/v1/teams/{team_id}/docs?node={node_id}&page_size=100"
    data = http_get(url, token)
    return data.get("data", [])


def safe_filename(name: str, doc_id: str) -> str:
    """文件名安全化：去掉特殊字符，保留可读性"""
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:80]
    return f"{safe}-{doc_id[:8]}.md"


def main():
    parser = argparse.ArgumentParser(description="批量获取乐享文档内容")
    parser.add_argument("--v1", action="store_true", help="走 1.0 REST API")
    parser.add_argument("--space-id", help="v2 知识库 ID")
    parser.add_argument("--parent-entry-id", help="v2 父级 entry_id")
    parser.add_argument("--team-id", help="v1 团队 UUID")
    parser.add_argument("--node-id", help="v1 目录 node_id")
    parser.add_argument("--out", default="./out", help="输出目录")
    parser.add_argument("--limit", type=int, default=100, help="最多处理多少篇")
    args = parser.parse_args()

    token = get_token()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    success, failed = [], []

    if args.v1:
        if not (args.team_id and args.node_id):
            sys.exit("❌ --v1 模式需要 --team-id 和 --node-id")
        print(f"[v1] 获取团队 {args.team_id} 目录 {args.node_id} 下文档列表...")
        docs = fetch_v1_team_docs(args.team_id, args.node_id, token)[: args.limit]
        print(f"[v1] 共 {len(docs)} 篇文档，开始拉取正文...")
        for i, doc in enumerate(docs, 1):
            doc_id = doc.get("id") or doc.get("attributes", {}).get("doc_id")
            name = doc.get("attributes", {}).get("name", "untitled")
            try:
                content = fetch_v1_doc_parsed(doc_id, token)
                fname = safe_filename(name, doc_id)
                (out_dir / fname).write_text(content, encoding="utf-8")
                print(f"  [{i}/{len(docs)}] ✅ {fname}")
                success.append(fname)
            except urllib.error.HTTPError as e:
                print(f"  [{i}/{len(docs)}] ❌ {name}: HTTP {e.code}")
                failed.append({"name": name, "doc_id": doc_id, "error": f"HTTP {e.code}"})
            except Exception as e:
                print(f"  [{i}/{len(docs)}] ❌ {name}: {e}")
                failed.append({"name": name, "doc_id": doc_id, "error": str(e)})
            time.sleep(0.2)  # 简单限速
    else:
        # v2 模式：实现略，需要走 MCP 而不是 REST
        # 此处给出框架，建议优先用 MCP 工具组合：
        #   entry_list_children(parent_entry_id) → 遍历 entry → entry_describe_ai_parse_content
        sys.exit("❌ v2 模式请用 MCP 工具组合实现：entry_list_children + entry_describe_ai_parse_content")

    print("\n=== 报告 ===")
    print(f"✅ 成功：{len(success)} 篇 → {out_dir.resolve()}")
    print(f"❌ 失败：{len(failed)} 篇")
    if failed:
        report_path = out_dir / "_failed.json"
        report_path.write_text(json.dumps(failed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   失败详情已写入：{report_path}")


if __name__ == "__main__":
    main()
