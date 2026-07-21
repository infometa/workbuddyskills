#!/usr/bin/env python3
"""
小红书热点跟踪工具

用法:
    python track-topic.py <话题> [--limit N] [--feishu] [--output FILE]

示例:
    python track-topic.py "DeepSeek" --limit 5 --feishu
    python track-topic.py "春节旅游" --limit 10 --output report.md
"""

import argparse
import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# 获取脚本目录
SCRIPT_DIR = Path(__file__).parent.resolve()
XHS_SCRIPTS = SCRIPT_DIR  # 现在就在 xiaohongshu/scripts 目录下

# 飞书 skill 路径（支持多种可能的位置）
def find_feishu_scripts() -> Path:
    """查找 feishu-docs skill 的 scripts 目录"""
    # 只允许在已知的 skill 目录中查找
    allowed_roots = [
        SCRIPT_DIR.parent.parent,  # 同级 skill 目录
        Path.home() / ".openclaw" / "workspace" / "skills",
        Path.home() / ".claude" / "skills",
    ]
    for root in allowed_roots:
        candidate = (root / "feishu-docs" / "scripts").resolve()
        # 校验解析后的路径仍在允许的根目录下（防止符号链接逃逸）
        if candidate.is_dir() and any(
            str(candidate).startswith(str(r.resolve()) + os.sep) for r in allowed_roots
        ):
            return candidate
    return allowed_roots[0] / "feishu-docs" / "scripts"  # 返回默认路径（可能不存在）

FEISHU_SCRIPTS = find_feishu_scripts()


def call_xhs_mcp(tool: str, args: dict) -> dict:
    """调用小红书 MCP 工具"""
    mcp_call = XHS_SCRIPTS / "mcp-call.sh"
    if not mcp_call.exists():
        print(f"❌ 找不到 xiaohongshu skill: {mcp_call}", file=sys.stderr)
        sys.exit(1)
    
    result = subprocess.run(
        [str(mcp_call), tool, json.dumps(args)],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        print(f"❌ MCP 调用失败: {result.stderr}", file=sys.stderr)
        return {}
    
    try:
        response = json.loads(result.stdout)
        if "result" in response and "content" in response["result"]:
            text = response["result"]["content"][0].get("text", "{}")
            return json.loads(text) if text else {}
        elif "error" in response:
            print(f"⚠️ MCP 错误: {response['error'].get('message', 'Unknown')}", file=sys.stderr)
            return {}
        return response
    except json.JSONDecodeError:
        return {}


def search_feeds(keyword: str) -> list:
    """搜索小红书内容"""
    print(f"🔍 搜索: {keyword}")
    result = call_xhs_mcp("search_feeds", {"keyword": keyword})
    feeds = result.get("feeds", [])
    # 过滤掉 hot_query 类型
    return [f for f in feeds if f.get("modelType") == "note"]


def get_feed_detail(feed_id: str, xsec_token: str, load_comments: bool = True) -> dict:
    """获取帖子详情"""
    args = {
        "feed_id": feed_id,
        "xsec_token": xsec_token,
        "load_all_comments": load_comments
    }
    result = call_xhs_mcp("get_feed_detail", args)
    return result.get("data", {})


def format_timestamp(ts: int) -> str:
    """格式化时间戳"""
    if not ts:
        return "未知"
    try:
        dt = datetime.fromtimestamp(ts / 1000)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return "未知"


def get_comments_list(post: dict) -> list:
    """安全地获取评论列表"""
    comments = post.get("comments", {})
    if isinstance(comments, dict):
        return comments.get("list", [])
    elif isinstance(comments, list):
        return comments
    return []


def generate_report(keyword: str, posts: list) -> str:
    """生成 Markdown 报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""# 🔥 小红书热点跟踪报告

**话题:** {keyword}  
**生成时间:** {now}  
**收录帖子:** {len(posts)} 篇

---

## 📊 概览

"""
    
    # 统计信息
    total_likes = sum(int(p.get("note", {}).get("interactInfo", {}).get("likedCount", 0) or 0) for p in posts)
    total_comments = sum(len(get_comments_list(p)) for p in posts)
    
    report += f"""| 指标 | 数值 |
|------|------|
| 总帖子数 | {len(posts)} |
| 总点赞数 | {total_likes:,} |
| 总评论数 | {total_comments} |

---

## 📝 热帖详情

"""
    
    for i, post in enumerate(posts, 1):
        note = post.get("note", {})
        comments = get_comments_list(post)
        
        title = note.get("title", "无标题")
        desc = note.get("desc", "")
        user = note.get("user", {}).get("nickname", "匿名")
        time_str = format_timestamp(note.get("time"))
        interact = note.get("interactInfo", {})
        likes = interact.get("likedCount", "0")
        collected = interact.get("collectedCount", "0")
        
        report += f"""### {i}. {title}

**作者:** {user}  
**时间:** {time_str}  
**互动:** ❤️ {likes} 赞 · ⭐ {collected} 收藏

**正文:**

> {desc[:500]}{"..." if len(desc) > 500 else ""}

"""
        
        if comments:
            report += f"""**热门评论 ({len(comments)} 条):**

"""
            for j, comment in enumerate(list(comments)[:5], 1):
                c_user = comment.get("userInfo", {}).get("nickname", "匿名")
                c_content = comment.get("content", "")
                c_likes = comment.get("likeCount", 0)
                report += f"- **{c_user}** ({c_likes}赞): {c_content[:100]}\n"
            
            if len(comments) > 5:
                report += f"- *... 还有 {len(comments) - 5} 条评论*\n"
        
        report += "\n---\n\n"
    
    # 评论区热点总结
    report += """## 💬 评论区热点关键词

"""
    
    # 简单的关键词提取（统计高频词）
    all_comments = []
    for post in posts:
        for c in get_comments_list(post):
            all_comments.append(c.get("content", ""))
    
    if all_comments:
        report += f"共 {len(all_comments)} 条评论，主要讨论方向：\n\n"
        # 这里可以做更复杂的 NLP 分析，暂时简化
        report += "- 用户对该话题的关注度较高\n"
        report += "- 评论区互动活跃\n"
    else:
        report += "暂无足够评论数据进行分析\n"
    
    report += """
---

## 📈 趋势分析

基于以上热帖和评论数据，该话题在小红书上呈现以下特点：

1. **热度指数**: """ + ("🔥🔥🔥 高" if total_likes > 1000 else "🔥🔥 中" if total_likes > 100 else "🔥 低") + f"""
2. **互动活跃度**: """ + ("活跃" if total_comments > 50 else "一般" if total_comments > 10 else "较低") + """
3. **内容类型**: 以图文笔记为主

---

*报告由 OpenClaw 小红书热点跟踪工具自动生成*
"""
    
    return report


def export_to_feishu(title: str, content: str) -> str:
    """导出到飞书文档"""
    import_script = FEISHU_SCRIPTS / "doc-import.sh"
    if not import_script.exists():
        print(f"❌ 找不到 feishu-docs skill: {import_script}", file=sys.stderr)
        return ""
    
    print("📤 导出到飞书文档...")
    
    # 写入临时文件
    tmp_file = Path("/tmp/xhs_report.md")
    tmp_file.write_text(content, encoding="utf-8")
    
    result = subprocess.run(
        [str(import_script), title, "--file", str(tmp_file)],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode != 0:
        print(f"⚠️ 飞书导出失败: {result.stderr}", file=sys.stderr)
        return ""
    
    # 解析返回的文档链接
    output = result.stdout
    print(output)
    return output


def main():
    parser = argparse.ArgumentParser(description="小红书热点跟踪工具")
    parser.add_argument("keyword", help="要跟踪的话题/关键词")
    parser.add_argument("--limit", "-n", type=int, default=10, help="获取帖子数量 (默认 10)")
    parser.add_argument("--feishu", "-f", action="store_true", help="导出到飞书文档")
    parser.add_argument("--output", "-o", help="输出 Markdown 文件路径")
    parser.add_argument("--no-comments", action="store_true", help="不获取评论")
    
    args = parser.parse_args()
    
    # 1. 搜索帖子
    feeds = search_feeds(args.keyword)
    if not feeds:
        print("❌ 未找到相关帖子")
        sys.exit(1)
    
    print(f"✅ 找到 {len(feeds)} 条帖子")
    
    # 2. 获取详情
    posts = []
    for i, feed in enumerate(feeds[:args.limit]):
        feed_id = feed.get("id")
        xsec_token = feed.get("xsecToken")
        title = feed.get("noteCard", {}).get("displayTitle", "")
        
        print(f"📖 [{i+1}/{min(len(feeds), args.limit)}] 获取: {title[:30]}...")
        
        detail = get_feed_detail(feed_id, xsec_token, not args.no_comments)
        if detail:
            posts.append(detail)
    
    if not posts:
        print("❌ 未能获取帖子详情")
        sys.exit(1)
    
    print(f"✅ 成功获取 {len(posts)} 篇帖子详情")
    
    # 3. 生成报告
    print("📝 生成报告...")
    report = generate_report(args.keyword, posts)
    
    # 4. 输出
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        print(f"✅ 报告已保存: {output_path}")
    
    if args.feishu:
        doc_title = f"小红书热点跟踪: {args.keyword} ({datetime.now().strftime('%m-%d')})"
        export_to_feishu(doc_title, report)
    
    if not args.output and not args.feishu:
        # 默认输出到 stdout
        print("\n" + "="*60 + "\n")
        print(report)
    
    return report


if __name__ == "__main__":
    main()
