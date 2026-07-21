#!/usr/bin/env python3
"""
GitHub Trending — 获取今日/本周/本月热门项目（真实 GitHub API）
无需第三方依赖，仅使用 Python stdlib
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}
PERIOD_LABELS = {"daily": "今日热门", "weekly": "本周热门", "monthly": "本月热门"}
PERIOD_EMOJI = {"daily": "🔥", "weekly": "📊", "monthly": "📈"}

# 按语言分批搜索，覆盖多个主流语言
LANGUAGES = [
    "", "python", "javascript", "typescript", "go", "rust",
    "java", "cpp", "c", "swift", "kotlin", "ruby", "php",
]


def gh_search(query: str, per_page: int = 30, token: str = None) -> list:
    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    })
    url = f"https://api.github.com/search/repositories?{params}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-trending-cn/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data.get("items", [])
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[WARN] GitHub API HTTP {e.code}: {body[:200]}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[WARN] GitHub API error: {e}", file=sys.stderr)
        return []


def fetch_trending(period: str = "weekly", limit: int = 25,
                   language: str = "", token: str = None) -> list:
    days = PERIOD_DAYS.get(period, 7)
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    seen: set = set()
    results: list = []

    # 构建语言过滤词
    lang_filter = f" language:{language}" if language else ""

    # 第一批：直接按 pushed + stars 排序，捞最活跃的仓库
    query = f"pushed:>={since} stars:>=10{lang_filter}"
    for item in gh_search(query, per_page=min(limit * 2, 100), token=token):
        if item["full_name"] not in seen:
            seen.add(item["full_name"])
            results.append(item)

    # 如果语言未指定，再按主流语言补充，避免单语言垄断
    if not language and len(results) < limit * 2:
        for lang in LANGUAGES[1:6]:  # top 5 语言补充
            if len(results) >= limit * 3:
                break
            q = f"pushed:>={since} stars:>=50 language:{lang}"
            for item in gh_search(q, per_page=20, token=token):
                if item["full_name"] not in seen:
                    seen.add(item["full_name"])
                    results.append(item)

    # 按 stars 降序排列，取 top N
    results.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    return results[:limit]


def fmt_num(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def format_output(repos: list, period: str, language: str = "") -> str:
    label = PERIOD_LABELS.get(period, period)
    emoji = PERIOD_EMOJI.get(period, "📊")
    tz_cst = timezone(timedelta(hours=8))
    now = datetime.now(tz_cst).strftime("%Y-%m-%d %H:%M CST")
    lang_tag = f" · {language}" if language else ""

    lines = [
        f"{emoji} **GitHub Trending — {label}{lang_tag}**",
        f"数据时间：{now}  |  共 {len(repos)} 个项目",
        "",
    ]

    for i, r in enumerate(repos, 1):
        stars = fmt_num(r.get("stargazers_count", 0))
        forks = fmt_num(r.get("forks_count", 0))
        lang = r.get("language") or "N/A"
        desc = r.get("description") or ""
        if len(desc) > 100:
            desc = desc[:97] + "..."
        name = r["full_name"]
        url = r["html_url"]
        topics = r.get("topics", [])[:3]
        topic_str = "  `" + "` `".join(topics) + "`" if topics else ""

        lines.append(f"**#{i}** [{name}]({url})")
        lines.append(f"⭐ {stars}  🍴 {forks}  🔤 {lang}{topic_str}")
        if desc:
            lines.append(f"> {desc}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Trending — 获取真实热门项目数据"
    )
    parser.add_argument(
        "--period", "-p",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="时间范围：daily/weekly/monthly（默认 daily）",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=20,
        help="返回数量（默认 20）",
    )
    parser.add_argument(
        "--language", "-l",
        default="",
        help="编程语言过滤，例如 python、javascript、go（默认不过滤）",
    )
    parser.add_argument(
        "--token", "-t",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="GitHub Personal Access Token（或设置 GITHUB_TOKEN 环境变量）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出原始 JSON",
    )
    args = parser.parse_args()

    print(f"[INFO] 正在获取 GitHub {args.period} trending...", file=sys.stderr)
    repos = fetch_trending(args.period, args.limit, args.language, args.token)

    if not repos:
        print("[ERROR] 未获取到数据，请检查网络或 GitHub API 限额", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 获取到 {len(repos)} 个项目", file=sys.stderr)

    if args.json:
        output = [
            {
                "rank": i,
                "name": r["full_name"],
                "url": r["html_url"],
                "description": r.get("description"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language"),
                "topics": r.get("topics", []),
            }
            for i, r in enumerate(repos, 1)
        ]
        json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    else:
        print(format_output(repos, args.period, args.language))


if __name__ == "__main__":
    main()
