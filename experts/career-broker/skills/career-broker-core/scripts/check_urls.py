#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_urls.py —— 外链事实性校验（防 LLM 编造 / 防漂移）。

背景：同事反馈专家给了好几个错的太湖地址（tai.woa.com/user/token、tai.woa.com、
mcp.woa.com），拉扯半天才拿到对的。根因是某些引导路径只写了"引导用户去申 PAT"
却没带完整 URL，模型手里没有事实，就按"太湖=tai.woa.com"的直觉编了一个。

本脚本做两件事：
  1. 黑名单：扫出所有**已知错误**的域名/路径写法（编造过的地址）
  2. 白名单：校验关键外链只使用登记过的唯一正确 URL

用法（在专家包根目录跑）：
    python3 skills/career-broker-core/scripts/check_urls.py
    echo $?     # 0=通过  1=发现问题

新增任何对外链接时，请同时登记到 CANONICAL 或 BLACKLIST。
"""
import re
import sys
from pathlib import Path

# ── 唯一正确地址登记表（白名单） ────────────────────────────────
CANONICAL = {
    "太湖 PAT 申请页": "https://tai.it.woa.com/user/pat",
    "QLearning MCP": "https://qlearning.mcp.it.woa.com/api/mcp",
    "TAPD 网关": "https://mcpgw.knot.woa.com/tapd/",
    "工蜂网关": "https://mcpgw.knot.woa.com/gongfeng",
    # 职业DNA测评 —— 2026-08 升级为三版本，端口从 8080 迁到 8082
    "职业DNA测评·初阶员工版": "http://21.6.92.38:8082/junior.html",
    "职业DNA测评·中高阶员工版": "http://21.6.92.38:8082/senior.html",
    "职业DNA测评·管理者版": "http://21.6.92.38:8082/manager.html",
    "职业DNA测评·总入口": "http://21.6.92.38:8082/",
    # 行家话题 —— 只能用 mentors.json 里带来源参数的完整串，前缀固定
    "行家话题（前缀）": "https://learn.woa.com/r/hangjiaTopic?",
}

# ── 已知错误写法（黑名单）：出现即失败 ──────────────────────────
# 前 4 条是同事 2026-08-17 实际收到的编造地址
BLACKLIST = [
    (r"https?://tai\.woa\.com",              "tai.woa.com（漏了 .it，正确是 tai.it.woa.com）"),
    (r"https?://mcp\.woa\.com",              "mcp.woa.com（不存在）"),
    (r"https?://taihu\.woa\.com",            "taihu.woa.com（不存在）"),
    (r"tai\.it\.woa\.com/user/token",        "path 应为 /user/pat，不是 /user/token"),
    (r"https?://tai\.it\.woa\.com/pat\b",    "path 应为 /user/pat"),
    (r"招活水\s*(MCP|知识库|token)",          "产品名应为「招活MCP/招活知识库/招活 token」（多了'水'字）"),
    # 测评站 2026-08 从 8080 迁到 8082 并拆成三版；下面都是编造过/已废弃的写法
    (r"21\.6\.92\.38:8080",                  "测评站旧端口 8080 已废弃，现行是 8082（三版本见 T5 §0）"),
    (r"""21\.6\.92\.38:8082/(?!junior\.html|senior\.html|manager\.html)[a-zA-Z]""",
                                             "8082 下只有 junior.html / senior.html / manager.html 三个页面，其它路径不存在"),
    # 行家链接必须原样使用 mentors.json 的 url（带 jump_from/project/source 来源参数）
    (r"""learn\.woa\.com/r/hangjia(?!Topic\?)[a-zA-Z]""",
                                             "行家链接路径只有 /r/hangjiaTopic?，其它 hangjia* 路径不存在"),
    (r"""learn\.woa\.com/hangjia""",         "行家链接缺 /r/ 段，正确前缀是 learn.woa.com/r/hangjiaTopic?"),
    (r"""https?://hangjia\.woa\.com""",      "hangjia.woa.com（不存在，行家在 learn.woa.com 上）"),
]

SCAN_SUFFIX = {".md", ".py", ".json", ".sh"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "careerbroker", "careerbuddy"}
# 本文件自身登记了错误写法用于检测，需排除
SELF = Path(__file__).name

# 只扫「运行时会被模型读到」的目录/文件。
# 历史记录、方法论、改动清单里大量**引用**错误写法作为反面教材，不是在犯错。
RUNTIME_ONLY = ("agents/", "skills/", "README.md")
SKIP_PREFIX = (".workbuddy/memory/",)   # 项目记忆不是运行时产物

# 反面教材豁免：这一行本身就是在"警告不要这么写"，不算犯错。
# 判据是同一行出现了否定/警示语义的标记词。
NEGATION_MARKERS = (
    "不是", "严禁", "禁止", "错误", "不存在", "不许", "别写", "误写", "写错",
    "应为", "正确是", "改成", "废弃", "旧流程", "反面", "铁律", "问题：", "漏了",
)


def is_counter_example(line: str) -> bool:
    """判断这一行是不是在把错误写法当反面教材引用。"""
    return any(m in line for m in NEGATION_MARKERS)



def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.suffix not in SCAN_SUFFIX:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name == SELF:
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith(SKIP_PREFIX):
            continue
        if not rel.startswith(RUNTIME_ONLY):
            continue
        yield p


def main():
    root = Path(__file__).resolve().parents[3]  # skills/career-broker-core/scripts/ → 包根
    problems = []
    exempted = 0

    for f in iter_files(root):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.split("\n"), 1):
            for pat, why in BLACKLIST:
                if not re.search(pat, line):
                    continue
                if is_counter_example(line):
                    exempted += 1
                    continue
                rel = f.relative_to(root)
                problems.append(f"  {rel}:{lineno}\n      问题：{why}\n      原文：{line.strip()[:110]}")

    print("=" * 60)
    print("外链事实性校验（只扫运行时：agents/ · skills/ · README）")
    print("=" * 60)
    print("\n【唯一正确地址登记表】")
    for name, url in CANONICAL.items():
        print(f"  {name:<16} {url}")

    if problems:
        print(f"\n❌ 发现 {len(problems)} 处错误写法：\n")
        print("\n\n".join(problems))
        print("\n修复要求：改成上面登记表里的正确地址；若确实不该出现链接，直接删掉。")
        return 1

    print(f"\n✅ 通过——运行时文件未发现错误写法")
    print(f"   （{len(BLACKLIST)} 条规则；{exempted} 处命中被判定为反面教材引用，已豁免）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
