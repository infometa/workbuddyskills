#!/usr/bin/env python3
"""
v7.9.5 批量为历史/地理课件注入 Leaflet 历史地图模块。

流程：
  1. 读 scripts/historical-maps-manifest.json
  2. 对每个课件：
     a. 复制所需 geojson 到 <course>/assets/maps/
     b. v7.9.5 新增：若 manifest 含 overlays，复制 details/*.geojson 到 <course>/assets/maps/details/
     c. 注入 Leaflet CDN + 标准地图模块 CSS/JS（幂等）
     d. 在 module-1 / intro 之后插入地图 section（幂等）
  3. 跳过标记 skip=true 的课件

幂等：检测 data-teachany-map 属性已存在则跳过 HTML 注入；geojson 已存在则跳过复制。
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/historical-maps-manifest.json"
SKILL_CHINA = ROOT / "skill/assets/historical-china"
SKILL_WORLD = ROOT / "skill/assets/historical-world"
# v7.9.5: CHGIS 细节数据目录（关隘/河流/古城/丝路）
SKILL_DETAILS = ROOT / "skill/assets/historical-china/details"
# v7.7.3: 全球彩色阴影地形底图（2k 版 205KB，满足地图容器显示需求）
HILLSHADE_SRC = ROOT / "skill/assets/hillshade/global-color-hillshade-2k.jpg"

LEAFLET_CSS = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
LEAFLET_JS = '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
MODULE_CSS = '<link rel="stylesheet" href="../../scripts/teachany-historical-map.css">'
MODULE_JS = '<script src="../../scripts/teachany-historical-map.js" defer></script>'

def copy_hillshade(course_dir: Path) -> int:
    """v7.7.3: 复制全球彩色阴影地形底图为课件本地 hillshade.jpg（统一默认底图）"""
    if not HILLSHADE_SRC.exists():
        return 0
    target = course_dir / "assets" / "maps" / "hillshade.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == HILLSHADE_SRC.stat().st_size:
        return 0  # 已是最新
    shutil.copy2(HILLSHADE_SRC, target)
    return 1

def copy_overlay_files(course_dir: Path, overlays: list) -> int:
    """v7.9.5: 把 overlays 中引用的 CHGIS 细节 geojson 从 skill/assets/historical-china/details/
    复制到 course/assets/maps/details/。overlay.file 可为纯文件名（'passes-ancient.geojson'）
    或含路径（'details/passes-ancient.geojson'），两种写法都支持。"""
    if not overlays:
        return 0
    target = course_dir / "assets" / "maps" / "details"
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for ov in overlays:
        raw = ov.get("file")
        if not raw:
            continue
        # 去掉可能的 details/ 前缀
        fname = raw.split("/")[-1]
        src = SKILL_DETAILS / fname
        if not src.exists():
            print(f"  ⚠ 缺失 overlay geojson：{fname}（期望在 {SKILL_DETAILS.relative_to(ROOT)}）")
            continue
        dst = target / fname
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            continue
        shutil.copy2(src, dst)
        copied += 1
    return copied

def copy_geojson_files(course_dir: Path, scope: str, eras: list):
    """把 eras 中引用的 geojson 从 skill/assets 复制到 course/assets/maps/
    优先在指定 scope 目录找，找不到则 fallback 另一个 scope（方便中国近现代史混用 world 时期文件）"""
    target = course_dir / "assets" / "maps"
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    search_dirs = []
    if scope == "china":
        search_dirs = [SKILL_CHINA, SKILL_WORLD]
    elif scope == "world":
        search_dirs = [SKILL_WORLD, SKILL_CHINA]
    else:
        search_dirs = [SKILL_CHINA, SKILL_WORLD]
    for era in eras:
        fname = era.get("file")
        if not fname: continue
        src = None
        for d in search_dirs:
            candidate = d / fname
            if candidate.exists():
                src = candidate
                break
        if not src:
            print(f"  ⚠ 缺失 geojson：{fname}（scope={scope}）")
            continue
        dst = target / fname
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            continue
        shutil.copy2(src, dst)
        copied += 1
    return copied

def inject_head(html: str) -> str:
    if "teachany-historical-map.js" in html:
        return html  # 已注入
    addition = ""
    if "leaflet.css" not in html:
        addition += "  " + LEAFLET_CSS + "\n"
    if "leaflet.js" not in html:
        addition += "  " + LEAFLET_JS + "\n"
    if "teachany-historical-map.css" not in html:
        addition += "  " + MODULE_CSS + "\n"
    if not addition:
        return html
    return html.replace("</head>", addition + "</head>", 1)

def inject_script_bottom(html: str) -> str:
    if MODULE_JS in html:
        return html
    # 放在 knowledge-graph js 之前或 </body> 之前
    kg_marker = '<script src="../../scripts/teachany-knowledge-graph.js"'
    if kg_marker in html:
        return html.replace(kg_marker, MODULE_JS + "\n" + kg_marker, 1)
    return html.replace("</body>", MODULE_JS + "\n</body>", 1)

def build_section(course_id: str, cfg: dict) -> str:
    """生成地图 section 的 HTML（v7.9.5 支持 overlays）"""
    config_dict = {
        "eras": cfg["eras"],
        "center": cfg.get("center", [34, 108]),
        "zoom": cfg.get("zoom", 4),
        "fitBounds": cfg.get("fitBounds"),
        "minZoom": cfg.get("minZoom", 2),
        "maxZoom": cfg.get("maxZoom", 8)
    }
    # v7.9.5: 透传 overlays 到前端
    if cfg.get("overlays"):
        config_dict["overlays"] = cfg["overlays"]
    config_json = json.dumps(config_dict, ensure_ascii=False, indent=2)
    map_id = "thm-" + re.sub(r"[^a-z0-9-]+", "-", course_id.lower())[:40]
    return f'''
<!-- ⭐ v7.9.5 标准 Leaflet 历史地图模块（CHGIS overlays 可用）-->
<section class="ta-standard-section" id="teachany-historical-map">
  <h2 style="text-align:center;margin-bottom:16px;">🗺️ {cfg["title"]}</h2>
  <p style="text-align:center;color:#64748b;margin-bottom:18px;">点击时代按钮切换疆域版图；悬停高亮边界；点击红色城市标记查看详情。</p>
  <div data-teachany-map="{map_id}"
       data-teachany-map-scope="{cfg.get('scope', 'china')}"
       data-teachany-map-title="{cfg['title']}">
    <script type="application/json" data-teachany-map-config>
{config_json}
    </script>
  </div>
</section>
'''

def inject_section(html: str, block: str) -> tuple:
    """把 map section 插入到合适位置；幂等"""
    if 'data-teachany-map=' in html:
        return html, False
    # 优先在 intro/module-1 section 之后插入
    for sec_id in ["module1", "module-1", "intro", "objectives", "pretest"]:
        pattern = r'<section[^>]*id=["\']' + sec_id + r'["\'][^>]*>'
        sm = re.search(pattern, html)
        if not sm:
            pattern = r'<div[^>]*class="section"[^>]*id=["\']' + sec_id + r'["\'][^>]*>'
            sm = re.search(pattern, html)
        if not sm: continue
        # 找对应的结束 </section> 或 </div>
        start = sm.end()
        depth = 1
        i = start
        open_tag = "<section" if sm.group(0).startswith("<section") else "<div"
        close_tag = "</section>" if open_tag == "<section" else "</div>"
        while i < len(html) and depth > 0:
            om = re.search(open_tag + r'[\s>]', html[i:])
            cm = re.search(close_tag, html[i:])
            if not cm: break
            if om and om.start() < cm.start():
                depth += 1
                i += om.end()
            else:
                depth -= 1
                i += cm.end()
        if depth == 0:
            return html[:i] + block + html[i:], True
    # 兜底：放在 tutor-card 之后
    if 'id="teachany-ai-tutor-card"' in html:
        pat = re.search(r'<section[^>]*id="teachany-ai-tutor-card"[^>]*>[\s\S]*?</section>', html)
        if pat:
            return html[:pat.end()] + block + html[pat.end():], True
    return html, False

def process(course_rel_path: str, cfg: dict):
    if cfg.get("skip"):
        return "skipped: " + cfg.get("reason", "")
    course_dir = ROOT / course_rel_path
    idx = course_dir / "index.html"
    if not idx.exists():
        return "no-index"

    # 1. 复制 geojson（即使 HTML 已注入也要补漏）
    copied = copy_geojson_files(course_dir, cfg.get("scope", "china"), cfg["eras"])
    # 1b. v7.7.3: 复制全球彩色阴影地形底图
    hill = copy_hillshade(course_dir)
    # 1c. v7.9.5: 复制 CHGIS 细节叠加层（关隘/河流/古城/丝路）
    overlay_copied = copy_overlay_files(course_dir, cfg.get("overlays", []))

    # 2. 注入 HTML
    html = idx.read_text(encoding="utf-8")
    orig = html
    html = inject_head(html)
    html = inject_script_bottom(html)
    html, inj_section = inject_section(html, build_section(course_rel_path, cfg))

    if html != orig:
        if DRY_RUN:
            print(f"    [dry-run] write {idx.relative_to(ROOT)} ({len(html)} chars)")
        else:
            idx.write_text(html, encoding="utf-8")
        return f"applied (geojson={copied}, overlays={overlay_copied}, hillshade={hill}, section={inj_section})"
    if copied > 0 or overlay_copied > 0 or hill > 0:
        return f"assets-only (geojson={copied}, overlays={overlay_copied}, hillshade={hill})"
    return "no-change"

DRY_RUN = False

def _real_copy2(src, dst):
    if DRY_RUN:
        print(f"    [dry-run] copy {Path(src).relative_to(ROOT)} → {Path(dst).relative_to(ROOT)}")
        return
    shutil.copy2(src, dst)

def _real_write_text(path: Path, content: str, encoding="utf-8"):
    if DRY_RUN:
        print(f"    [dry-run] write {path.relative_to(ROOT)} ({len(content)} chars)")
        return
    path.write_text(content, encoding=encoding)

def main():
    import sys
    global DRY_RUN
    if "--dry-run" in sys.argv:
        DRY_RUN = True
        # 拦截 shutil.copy2 与 Path.write_text：保留原方法，只在本脚本流程内替换
        shutil.copy2 = _real_copy2  # type: ignore
        # Path.write_text 是绑定方法，改装到模块级 helper 里，见下方 process 已经用 idx.write_text
        # 为避免破坏 Path 原生方法，改为在 process 内部判断 DRY_RUN
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print(f"处理 {len(manifest)} 个课件{' [DRY-RUN]' if DRY_RUN else ''}：\n")
    stats = {"applied": 0, "skipped": 0, "no-index": 0, "no-change": 0, "assets-only": 0}
    for course, cfg in manifest.items():
        result = process(course, cfg)
        if result.startswith("applied"):
            stats["applied"] += 1
        elif result.startswith("assets-only"):
            stats["assets-only"] += 1
        elif result.startswith("skipped"):
            stats["skipped"] += 1
        elif result == "no-index":
            stats["no-index"] += 1
        else:
            stats["no-change"] += 1
        print(f"  {course}: {result}")
    print(f"\n汇总：{stats}")

if __name__ == "__main__":
    main()
