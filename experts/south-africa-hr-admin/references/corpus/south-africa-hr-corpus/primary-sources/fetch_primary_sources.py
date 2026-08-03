# -*- coding: utf-8 -*-
"""
核心法源一键下载脚本（Primary Sources Fetcher）— 含官源镜像兜底
==================================================================
尝试从 SAFLII 及官方镜像（legislation.gov.za / gov.za）归档 5 部核心
法案的官方法文，保存到 primary-sources/raw/。

设计要点：
  - SAFLII 对自动化抓取有反爬限制（常返回 403）。本脚本按
    SAFLII → legislation.gov.za → gov.za 顺序尝试多个官源镜像，
    任一返回「像法文全文」的内容即采用，提高在你本机（正常网络）的成功率。
  - 下载后做「是否像法文全文」的启发式校验：
        [OK 全文]   内容像法文全文，已保存；
        [UNCERTAIN] 只拿到检索/落地页，已保存但需人工确认补全；
        [FAIL]      所有官源均不可达，打印人工下载步骤。
  - 受限网络（如本沙箱）下仍可能失败 —— 失败时会打印「人工下载」步骤，不影响其他流程。

用法：
  python fetch_primary_sources.py
  python fetch_primary_sources.py --act bcea        # 只下某一部
  python fetch_primary_sources.py --out raw         # 指定输出目录
"""

import argparse
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "raw")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-ZA,en;q=0.9",
}

# 每部法案：简称 + 文件名 + 检索短语（脚本会用其尝试定位法文页）
ACTS = {
    "bcea": {
        "name": "Basic Conditions of Employment Act 75 of 1997",
        "file": "bcea-75-of-1997.txt",
        "q": "Basic Conditions of Employment Act 75 of 1997",
    },
    "lra": {
        "name": "Labour Relations Act 66 of 1995",
        "file": "lra-66-of-1995.txt",
        "q": "Labour Relations Act 66 of 1995",
    },
    "eea": {
        "name": "Employment Equity Act 55 of 1998",
        "file": "eea-55-of-1998.txt",
        "q": "Employment Equity Act 55 of 1998",
    },
    "bbbee": {
        "name": "Broad-Based Black Economic Empowerment Act 53 of 2003",
        "file": "bbbee-53-of-2003.txt",
        "q": "Broad-Based Black Economic Empowerment Act 53 of 2003",
    },
    "coida": {
        "name": "Compensation for Occupational Injuries and Diseases Act 130 of 1993",
        "file": "coida-130-of-1993.txt",
        "q": "Compensation for Occupational Injuries and Diseases Act 130 of 1993",
    },
}

# 官源镜像（顺序即优先级）；{q} 在运行时被 URL 编码后的短语替换
MIRRORS = [
    ("SAFLII", "https://www.saflii.org/cgi-bin/sinodisp/za/search?query={q}"),
    ("legislation.gov.za", "https://www.legislation.gov.za/search?query={q}"),
    ("gov.za", "https://www.gov.za/search?query={q}"),
]


def _looks_like_act_text(text):
    """启发式：下载内容是否像法文全文（而非检索页/错误页/首页）。"""
    if not text or len(text) < 6000:
        return False
    low = text.lower()
    # 典型检索/错误页信号 → 不算法文全文
    if any(k in low for k in ("no results", "did not match", "search results", "0 results", "page not found")):
        return False
    has_act = "act" in low
    has_struct = ("section" in low) or ("s." in low) or ("chapter" in low)
    has_enact = any(k in low for k in ("enacted", "parliament", "whereas", "republic of south africa"))
    return has_act and (has_struct or has_enact)


def _fetch_url(url, timeout=25):
    import urllib.request
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _save(dest, text):
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)


def _print_manual(meta, dest):
    print(f"    人工下载步骤：")
    print(f"      1. 打开 SAFLII 法源库浏览：https://www.saflii.org/za/legis/num_act/")
    print(f"         或在 Google 搜：\"{meta['name']} PDF\"")
    print(f"      2. 复制全文或点 Download，保存为：{dest}")
    print(f"      3. 记录 Government Gazette 编号与日期以便溯源")


def _fetch_one(key, meta, out_dir):
    """按镜像顺序尝试下载单部法案；返回 True 表示已拿到像全文的内容。"""
    dest = os.path.join(out_dir, meta["file"])
    print(f"\n=== {key.upper()} — {meta['name']} ===")

    q = urllib.parse.quote_plus(meta["q"])
    landed = []  # (label, html) 拿到但非全文的页面，留作兜底
    for label, tpl in MIRRORS:
        url = tpl.format(q=q)
        print(f"    → 试 {label}: {url[:78]}...")
        try:
            html = _fetch_url(url)
        except Exception as e:  # noqa: BLE001
            print(f"    [SKIP] {label} 不可达：{e}")
            continue

        if _looks_like_act_text(html):
            _save(dest, html)
            print(f"    [OK 全文] 已保存 {dest} ({len(html) // 1024} KB) — 来源 {label}")
            return True

        landed.append((label, html))
        print(f"    [·] {label} 返回内容不像法文全文，继续试下一个镜像")
        time.sleep(0.5)

    # 没有一个像全文：保存最后一个能拿到的（多半是检索/落地页），标注需人工确认
    if landed:
        label, html = landed[-1]
        _save(dest, html)
        print(f"    [UNCERTAIN] 已保存 {label} 返回页到 {dest} ({len(html) // 1024} KB)")
        print(f"    注意：该文件可能不是法文全文（更像检索/落地页），请人工打开确认并补全。")
        _print_manual(meta, dest)
        return False

    # 全部连接失败
    print(f"    [FAIL] 所有官源镜像均不可达。")
    _print_manual(meta, dest)
    return False


def main():
    p = argparse.ArgumentParser(description="下载南非核心劳动法原文（SAFLII + 官源镜像兜底）")
    p.add_argument("--act", type=str, default=None, help="只下载指定法案：bcea/lra/eea/bbbee/coida")
    p.add_argument("--out", type=str, default="raw", help="输出子目录（默认 raw）")
    args = p.parse_args()

    out_dir = os.path.join(HERE, args.out)
    os.makedirs(out_dir, exist_ok=True)

    targets = {args.act: ACTS[args.act]} if args.act else ACTS

    ok, uncertain, fail = 0, 0, 0
    for key, meta in targets.items():
        r = _fetch_one(key, meta, out_dir)
        if r:
            ok += 1
        else:
            # 区分「拿到检索页」与「全失败」
            dest = os.path.join(out_dir, meta["file"])
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                uncertain += 1
            else:
                fail += 1
        time.sleep(1.0)  # 降低被封风险

    print("\n" + "=" * 60)
    print(f"  完成：全文 {ok} / 检索页(需人工) {uncertain} / 全失败 {fail}（共 {len(targets)}）")
    if uncertain or fail:
        print("  部分未拿到全文属正常（SAFLII 反爬 / 受限网络）。")
        print("  凡标 [UNCERTAIN] 或 [FAIL] 的，请按上方人工步骤补全 raw/ 下文件。")
    print("=" * 60)


if __name__ == "__main__":
    main()
