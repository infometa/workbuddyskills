#!/usr/bin/env python3
"""
TAPD Wiki 同步与搜索工具

用法:
  python3 search_wiki.py sync               # 下载全部 Wiki 到本地缓存
  python3 search_wiki.py search <关键词>     # 搜索 Wiki 内容（支持多个关键词，空格分隔取交集）
  python3 search_wiki.py search <关键词> --title-only  # 仅搜索标题
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

# ============================================================
# 配置
# ============================================================

API_ENDPOINT = os.environ.get("TAPD_API_ENDPOINT", "")
TOKEN = os.environ.get("TAPD_TOKEN", "")
WORKSPACE_IDS_STR = os.environ.get("TAPD_WORKSPACE_IDS", "") or os.environ.get("TAPD_WORKSPACE_ID", "")
TAPD_SITE_URL = os.environ.get("TAPD_SITE_URL", "") or API_ENDPOINT.replace("://api.", "://", 1)

CACHE_DIR = os.path.join(os.environ.get("HOME", "/tmp"), ".tapd-wiki-cache")
PAGE_SIZE = 200  # ListWikis 最大每页 200
MAX_WIKIS = 5000
CONTEXT_CHARS = 150  # 搜索结果上下文字符数

# ============================================================
# API 请求
# ============================================================


def api_get(path, params=None):
    """发送 GET 请求到 TAPD API，返回 JSON 数据"""
    url = f"{API_ENDPOINT}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") != 1:
                print(f"  API 错误: {data.get('info', '未知')}", file=sys.stderr)
                return None
            return data.get("data")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  请求失败: {e}", file=sys.stderr)
        return None


# ============================================================
# Wiki 同步
# ============================================================


def get_workspace_ids():
    return [ws.strip() for ws in WORKSPACE_IDS_STR.split(",") if ws.strip()]


def fetch_wiki_count(workspace_id):
    data = api_get("tapd_wikis/count", {"workspace_id": workspace_id})
    if data and "count" in data:
        return int(data["count"])
    return 0


def fetch_wikis_page(workspace_id, page):
    data = api_get("tapd_wikis", {
        "workspace_id": workspace_id,
        "limit": PAGE_SIZE,
        "page": page,
        "order": "modified desc",
        "fields": "id,name,workspace_id,description,markdown_description,parent_wiki_id,creator,modifier,created,modified",
    })
    if not data:
        return []
    return [item.get("Wiki", item) for item in data if isinstance(item, dict)]


def wiki_url(workspace_id, wiki_id):
    return f"{TAPD_SITE_URL}/{workspace_id}/markdown_wikis/show/#{wiki_id}"


def save_wiki(workspace_id, wiki):
    ws_dir = os.path.join(CACHE_DIR, str(workspace_id))
    os.makedirs(ws_dir, exist_ok=True)

    wiki_id = wiki.get("id", "unknown")
    name = wiki.get("name", "")
    content = wiki.get("markdown_description") or wiki.get("description") or ""
    url = wiki_url(workspace_id, wiki_id)

    header = (
        f"---\n"
        f"id: {wiki_id}\n"
        f"name: {name}\n"
        f"workspace_id: {workspace_id}\n"
        f"parent_wiki_id: {wiki.get('parent_wiki_id', '')}\n"
        f"creator: {wiki.get('creator', '')}\n"
        f"modifier: {wiki.get('modifier', '')}\n"
        f"created: {wiki.get('created', '')}\n"
        f"modified: {wiki.get('modified', '')}\n"
        f"url: {url}\n"
        f"---\n\n"
    )
    filepath = os.path.join(ws_dir, f"{wiki_id}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content)
    return filepath


def cmd_sync():
    """下载全部 Wiki 到本地缓存"""
    workspace_ids = get_workspace_ids()
    if not workspace_ids:
        print("错误: 未配置 TAPD_WORKSPACE_IDS 或 TAPD_WORKSPACE_ID", file=sys.stderr)
        sys.exit(1)
    if not API_ENDPOINT:
        print("错误: 未配置 TAPD_API_ENDPOINT，请设置环境变量 TAPD_API_ENDPOINT", file=sys.stderr)
        sys.exit(1)
    if not TOKEN:
        print("错误: 未配置 TAPD_TOKEN，请设置环境变量 TAPD_TOKEN", file=sys.stderr)
        sys.exit(1)

    os.makedirs(CACHE_DIR, exist_ok=True)
    total_saved = 0

    for ws_id in workspace_ids:
        count = fetch_wiki_count(ws_id)
        remaining = MAX_WIKIS - total_saved
        if remaining <= 0:
            print(f"[workspace {ws_id}] 已达最大拉取数量 {MAX_WIKIS}，跳过")
            break
        effective = min(count, remaining)
        print(f"[workspace {ws_id}] 共 {count} 篇 Wiki，本次拉取 {effective} 篇（上限 {MAX_WIKIS}）")

        if count == 0:
            continue

        pages = (effective + PAGE_SIZE - 1) // PAGE_SIZE
        ws_saved = 0
        for page in range(1, pages + 1):
            wikis = fetch_wikis_page(ws_id, page)
            if not wikis:
                break
            for wiki in wikis:
                save_wiki(ws_id, wiki)
                ws_saved += 1
                if total_saved + ws_saved >= MAX_WIKIS:
                    break
            print(f"  已同步 {ws_saved}/{effective}")
            if len(wikis) < PAGE_SIZE or total_saved + ws_saved >= MAX_WIKIS:
                break
            time.sleep(0.2)

        total_saved += ws_saved

    meta = {"synced_at": time.strftime("%Y-%m-%d %H:%M:%S"), "workspace_ids": workspace_ids, "total": total_saved}
    with open(os.path.join(CACHE_DIR, "meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n同步完成: {total_saved} 篇 Wiki -> {CACHE_DIR}")


# ============================================================
# Wiki 搜索
# ============================================================


def parse_front_matter(text):
    """解析 YAML front matter，返回 (metadata_dict, body)"""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    header = text[4:end]
    body = text[end + 5:]
    meta = {}
    for line in header.split("\n"):
        idx = line.find(": ")
        if idx > 0:
            meta[line[:idx].strip()] = line[idx + 2:].strip()
    return meta, body


def _split_sentences(text):
    """按中英文句末标点或换行拆分句子，保留非空句子"""
    parts = re.split(r'(?<=[。！？!?\n])', text)
    return [s.strip() for s in parts if s.strip()]


def extract_context(text, keyword, chars=CONTEXT_CHARS):
    """提取关键词所在句子及前后各一句，并加粗关键词"""
    lower_kw = keyword.lower()
    if lower_kw not in text.lower():
        return None

    sentences = _split_sentences(text)
    if not sentences:
        return None

    matched_indices = set()
    for i, sent in enumerate(sentences):
        if lower_kw in sent.lower():
            matched_indices.add(i)

    if not matched_indices:
        return None

    indices = set()
    for idx in matched_indices:
        indices.update(range(max(0, idx - 1), min(len(sentences), idx + 2)))

    selected = [sentences[i] for i in sorted(indices)]
    snippet = " ".join(selected)

    bold_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    snippet = bold_pattern.sub(lambda m: f"**{m.group()}**", snippet)

    return snippet


def search_wikis(keywords, title_only=False):
    """搜索本地缓存的 Wiki，返回匹配结果列表"""
    if not os.path.isdir(CACHE_DIR):
        print(f"缓存目录不存在，请先执行 sync: {CACHE_DIR}", file=sys.stderr)
        sys.exit(1)

    lower_keywords = [kw.lower() for kw in keywords]
    results = []

    for ws_dir_name in os.listdir(CACHE_DIR):
        ws_path = os.path.join(CACHE_DIR, ws_dir_name)
        if not os.path.isdir(ws_path):
            continue
        for fname in os.listdir(ws_path):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(ws_path, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            meta, body = parse_front_matter(content)
            name = meta.get("name", "")

            search_text = name if title_only else f"{name}\n{body}"
            lower_search = search_text.lower()

            if not all(kw in lower_search for kw in lower_keywords):
                continue

            snippets = []
            for kw in keywords:
                ctx = extract_context(search_text, kw)
                if ctx:
                    snippets.append(ctx)

            results.append({
                "name": name,
                "url": meta.get("url", ""),
                "workspace_id": meta.get("workspace_id", ""),
                "modifier": meta.get("modifier", ""),
                "modified": meta.get("modified", ""),
                "snippets": snippets,
            })

    results.sort(key=lambda r: r.get("modified", ""), reverse=True)
    return results


def cmd_search(keywords, title_only=False):
    """搜索 Wiki 并输出结果"""
    results = search_wikis(keywords, title_only)
    if not results:
        print(f"未找到匹配的 Wiki（关键词: {', '.join(keywords)}）")
        return

    print(f"找到 {len(results)} 篇匹配的 Wiki（关键词: {', '.join(keywords)}）\n")
    for i, r in enumerate(results, 1):
        print(f"### {i}. {r['name']}")
        print(f"- 链接: {r['url']}")
        print(f"- 最后修改: {r['modified']} by {r['modifier']}")
        if r["snippets"]:
            print(f"- 匹配片段:")
            for s in r["snippets"]:
                print(f"  > {s}")
        print()


# ============================================================
# 入口
# ============================================================


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "sync":
        cmd_sync()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("用法: search_wiki.py search <关键词> [--title-only]", file=sys.stderr)
            sys.exit(1)
        title_only = "--title-only" in sys.argv
        keywords = [a for a in sys.argv[2:] if not a.startswith("--")]
        cmd_search(keywords, title_only)
    else:
        print(f"未知命令: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
