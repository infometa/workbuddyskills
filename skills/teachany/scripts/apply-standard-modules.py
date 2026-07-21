#!/usr/bin/env python3
"""TeachAny 标准模块统一注入器（v7.7.4）

为 `examples/*` + `community/*` 所有课件注入标准模块五件套：

  ① ai-tutor.{css,js}                      AI 学伴 FAB + 对话面板
  ② teachany-tutor-card.{css,js}           AI 学伴入口卡片
  ③ teachany-tts-narrator.{css,js}         Web Speech 悬浮朗读控制器
  ④ teachany-section-hints.{css,js}        滚动情境感知气泡
  ⑤ teachany-knowledge-graph.{css,js}      知识图谱（需 manifest.node_id）

设计原则：
  - 幂等：已存在的引用 / section 不重复插入
  - 最小侵入：只追加 `<link>` / `<script>` / tail-section，不动原业务
  - 兜底：没有 `manifest.node_id` 则跳过 KG 注入（日志标注）
  - 路径：community/* 下使用 ../../scripts/，examples/* 下同样 ../../scripts/

用法：
  python3 scripts/apply-standard-modules.py               # 全量
  python3 scripts/apply-standard-modules.py --only community/history-medieval-europe
  python3 scripts/apply-standard-modules.py --dry-run     # 只看 diff 统计
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------
# 资源片段定义
# --------------------------------------------------------------------

LINKS = [
    ('<link rel="stylesheet" href="../../scripts/ai-tutor.css">', "ai-tutor.css"),
    ('<link rel="stylesheet" href="../../scripts/teachany-tutor-card.css">', "teachany-tutor-card.css"),
    ('<link rel="stylesheet" href="../../scripts/teachany-tts-narrator.css">', "teachany-tts-narrator.css"),
    ('<link rel="stylesheet" href="../../scripts/teachany-section-hints.css">', "teachany-section-hints.css"),
    ('<link rel="stylesheet" href="../../scripts/teachany-knowledge-graph.css">', "teachany-knowledge-graph.css"),
]

SCRIPTS = [
    ('<script src="../../scripts/ai-tutor.js"></script>', "ai-tutor.js"),
    ('<script src="../../scripts/teachany-tutor-card.js" defer></script>', "teachany-tutor-card.js"),
    ('<script src="../../scripts/teachany-tts-narrator.js" defer></script>', "teachany-tts-narrator.js"),
    ('<script src="../../scripts/teachany-section-hints.js" defer></script>', "teachany-section-hints.js"),
    ('<script src="../../scripts/teachany-knowledge-graph.js" defer></script>', "teachany-knowledge-graph.js"),
]

TUTOR_CARD_SECTION_MARK = "teachany-ai-tutor-card"
KG_SECTION_MARK = 'id="knowledge-graph"'
KG_DATA_MARK = "data-teachany-kg"

# --------------------------------------------------------------------


def load_manifest(course_dir: Path) -> dict:
    p = course_dir / "manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


_REGISTRY_CACHE: dict | None = None


def load_registry_index() -> dict:
    """返回 {course_id: node_id, ...} 索引。"""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    _REGISTRY_CACHE = {}
    for rel in ("courseware-registry.json", "registry.json"):
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        courses = data.get("courses") or data.get("items") or []
        for c in courses:
            cid = c.get("id") or c.get("course_id")
            nid = c.get("node_id") or c.get("nodeId")
            if cid and nid:
                _REGISTRY_CACHE[cid] = nid
    return _REGISTRY_CACHE


def resolve_node_id(course_dir: Path, manifest: dict) -> tuple[str | None, str]:
    """返回 (node_id, source)。source ∈ {'manifest','registry','none'}。"""
    nid = manifest.get("node_id")
    if nid:
        return nid, "manifest"
    reg = load_registry_index()
    nid = reg.get(course_dir.name)
    if nid:
        return nid, "registry"
    return None, "none"



def ensure_head_links(html: str) -> tuple[str, list[str]]:
    """在 </head> 前插入所有缺失的 <link>，返回 (新 html, 新增列表)。"""
    added: list[str] = []
    if "</head>" not in html:
        return html, added
    insertion = []
    for tag, name in LINKS:
        if name in html:
            continue
        insertion.append(tag)
        added.append(name)
    if not insertion:
        return html, added
    block = "\n  " + "\n  ".join(insertion) + "\n"
    html = html.replace("</head>", block + "</head>", 1)
    return html, added


def ensure_tail_scripts(html: str) -> tuple[str, list[str]]:
    """在 </body> 前插入所有缺失的 <script>；若无 </body> 则追加文件末尾。"""
    added: list[str] = []
    insertion = []
    for tag, name in SCRIPTS:
        if name in html:
            continue
        insertion.append(tag)
        added.append(name)
    if not insertion:
        return html, added
    block = "\n" + "\n".join(insertion) + "\n"
    if "</body>" in html:
        html = html.replace("</body>", block + "</body>", 1)
    else:
        # 无 </body> 的老课件：追加到文件末尾
        html = html + block
    return html, added


def ensure_tutor_card_section(html: str) -> tuple[str, bool]:
    if TUTOR_CARD_SECTION_MARK in html or "data-teachany-tutor-card" in html:
        return html, False
    block = (
        '\n<!-- v7.7 标准 AI 学伴入口卡片 -->\n'
        '<section class="ta-standard-section" id="teachany-ai-tutor-card">\n'
        '  <div data-teachany-tutor-card></div>\n'
        '</section>\n'
    )
    if "</body>" in html:
        return html.replace("</body>", block + "</body>", 1), True
    return html + block, True


def find_kg_container_bounds(html: str) -> tuple[int, int] | None:
    """找到 `<section id="knowledge-graph"...>...</section>` 的起止。"""
    m = re.search(r'<section\b[^>]*\bid="knowledge-graph"[^>]*>', html, re.I)
    if not m:
        return None
    start = m.start()
    # 用 depth 找到对应的 </section>
    depth = 1
    open_re = re.compile(r"<section\b", re.I)
    close_re = re.compile(r"</section>", re.I)
    i = m.end()
    while i < len(html):
        om = open_re.search(html, i)
        cm = close_re.search(html, i)
        if not cm:
            return None
        if om and om.start() < cm.start():
            depth += 1
            i = om.end()
        else:
            depth -= 1
            if depth == 0:
                return start, cm.end()
            i = cm.end()
    return None


def ensure_kg_section(html: str, node_id: str, heading: str) -> tuple[str, str]:
    """确保 KG section 存在且使用标准 data-teachany-kg。

    返回 (新 html, 动作)：'added' | 'replaced' | 'unchanged'
    """
    block = (
        '\n<!-- v7.7.4 标准知识图谱模块 -->\n'
        f'<section class="section" id="knowledge-graph" style="max-width:1080px;margin:24px auto;padding:0 20px;">\n'
        f'  <h2 class="section-title">🗺️ 知识图谱：{heading}</h2>\n'
        f'  <div data-teachany-kg="{node_id}">\n'
        '    <canvas class="tkg-fallback-canvas" width="720" height="120" aria-label="知识图谱互动画布占位" style="display:block;width:100%;max-height:140px;border-radius:12px;"></canvas>\n'
        '  </div>\n'
        "</section>\n"
    )

    bounds = find_kg_container_bounds(html)
    if bounds:
        start, end = bounds
        existing = html[start:end]
        # 已经是标准模块 + 匹配 node_id 就不动
        if KG_DATA_MARK in existing and f'data-teachany-kg="{node_id}"' in existing:
            return html, "unchanged"
        return html[:start] + block.lstrip("\n") + html[end:], "replaced"

    # 没有 KG section：追加到 body 末尾，在 tutor-card 之后（若存在）
    if "</body>" in html:
        return html.replace("</body>", block + "</body>", 1), "added"
    return html + block, "added"


# --------------------------------------------------------------------


def process_course(course_dir: Path, dry: bool = False) -> dict:
    index = course_dir / "index.html"
    if not index.exists():
        return {"course": course_dir.name, "skipped": "no-index"}

    manifest = load_manifest(course_dir)
    original = index.read_text(encoding="utf-8")
    html = original
    report = {
        "course": str(course_dir.relative_to(ROOT)),
        "links_added": [],
        "scripts_added": [],
        "tutor_card": False,
        "kg": None,
    }

    html, la = ensure_head_links(html)
    report["links_added"] = la

    html, sa = ensure_tail_scripts(html)
    report["scripts_added"] = sa

    html, card_added = ensure_tutor_card_section(html)
    report["tutor_card"] = card_added

    node_id = manifest.get("node_id")
    heading = manifest.get("name") or course_dir.name
    if not node_id:
        node_id, _src = resolve_node_id(course_dir, manifest)
    if node_id:
        html, action = ensure_kg_section(html, node_id, heading)
        report["kg"] = action
    else:
        report["kg"] = "skipped-no-node-id"

    if html != original:
        if not dry:
            index.write_text(html, encoding="utf-8")
        report["changed"] = True
    else:
        report["changed"] = False
    return report


def iter_course_dirs(base: Path, only: str | None):
    if not base.exists():
        return
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        if only and str(d.relative_to(ROOT)) != only:
            continue
        yield d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default=None, help="相对路径（如 community/history-medieval-europe）")
    args = ap.parse_args()

    targets = []
    for base_name in ("examples", "community"):
        targets += list(iter_course_dirs(ROOT / base_name, args.only))

    if not targets:
        print("❌ 未找到任何课件")
        sys.exit(1)

    print(f"🔎 将处理 {len(targets)} 个课件 ({'dry-run' if args.dry_run else 'write'})")
    total_changed = 0
    kg_stats = {"added": 0, "replaced": 0, "unchanged": 0, "skipped-no-node-id": 0}
    for d in targets:
        r = process_course(d, dry=args.dry_run)
        if r.get("skipped"):
            print(f"  ⏭  {r['course']} → {r['skipped']}")
            continue
        flag = "✅" if r["changed"] else "   "
        total_changed += int(r["changed"])
        action_parts = []
        if r["links_added"]:
            action_parts.append(f"links+{len(r['links_added'])}")
        if r["scripts_added"]:
            action_parts.append(f"scripts+{len(r['scripts_added'])}")
        if r["tutor_card"]:
            action_parts.append("tutor-card")
        if r["kg"]:
            action_parts.append(f"kg={r['kg']}")
            kg_stats[r["kg"]] = kg_stats.get(r["kg"], 0) + 1
        print(f"  {flag} {r['course']} — {', '.join(action_parts) or 'no-op'}")

    print("\n📊 汇总")
    print(f"  - 变更课件：{total_changed}/{len(targets)}")
    print(f"  - KG 动作：{kg_stats}")
    if args.dry_run:
        print("  （dry-run 未落盘，去掉 --dry-run 真正执行）")


if __name__ == "__main__":
    main()
