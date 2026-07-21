#!/usr/bin/env python3
"""
inject.py · tencent-smart-page 注入器（COS 远端模板版）

结构：scenes/{scene}/{narrative}/template.html + _assets/skins/{skin}.css + _assets/motion/*
- **所有模板资源从 COS 拉取**（默认 https://artifact-page.gtimg.com/html_templates/），
  每次调用都直接联网，不做本地缓存；详见 `template_source.py`
- 注入 Agent 产出的 data.js（格式 `window.data = {...};`），替换 `<script src="./mock-data.js"></script>`
- 内联皮肤 CSS（<link id="skinCss" ...> → <style id="skinCss">）
- 内联 motion.css / motion.js（`../../../_assets/motion/*` → 内联）
- **腾讯系皮肤 @font-face 走 artifact-page.gtimg.com CDN + local() fallback + 全局强制覆盖**
- 移除皮肤切换器（.skin-sw）
- 产出单文件 HTML（离线自带样式 + 动效）

Usage:
    python3 inject.py --scene proposal --narrative pyramid --skin tencent-blue \
                      --data /tmp/data.js --output output/立项.html
"""

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import template_source  # noqa: E402

TENCENT_SKINS = {"tencent-blue"}  # 未来若加 tencent-gold 等也放这里


def fetch_template_resource(rel_path: str) -> str:
    """从 COS 拉取远端模板资源（无本地缓存；失败立刻退出非零）。"""
    try:
        return template_source.fetch_text(rel_path)
    except Exception as e:
        print(f"Error: fetch resource failed: {rel_path}: {e}", file=sys.stderr)
        sys.exit(1)


def inline_tencent_fonts(skin_css: str) -> str:
    """
    腾讯蓝皮肤字体方案：走模板同源 COS（artifact-page.gtimg.com），本地离线降级到系统中文字体。

    实现策略：
    - 在 Python 层「整段重写」CSS 中针对 TencentSans-W3/W7 的 @font-face 块：
      src 顺序为 local() → woff2 → ttf 兜底（woff2 体积约为 ttf 的 45%，加载快很多）
    - 不依赖 COS 上 tencent-blue.css 里 url(...) 的具体写法，正则只识别 @font-face 段落
    - 追加一段全局强制覆盖：所有 h1-h6 / body / .heading / .num 都走 TencentSans
    - 不再 base64 内联，避免单文件体积炸到几十 MB
    - 历史教训：曾用过 docs.gtimg.com/lib/fonts/，实际是 404；现统一走 artifact-page.gtimg.com
    """
    base = "https://artifact-page.gtimg.com/html_templates/_assets/fonts"

    def build_face(weight_tag: str, css_weight: str, local_names: list[str]) -> str:
        """生成单个 @font-face 块：local → woff2 → ttf。"""
        locals_part = ", ".join(f'local("{n}")' for n in local_names)
        return (
            "@font-face {\n"
            '  font-family: "TencentSans";\n'
            f"  src: {locals_part},\n"
            f'       url("{base}/TencentSans-{weight_tag}.woff2") format("woff2"),\n'
            f'       url("{base}/TencentSans-{weight_tag}.ttf") format("truetype");\n'
            f"  font-weight: {css_weight};\n"
            "  font-style: normal;\n"
            "  font-display: swap;\n"
            "}"
        )

    rewritten_faces = (
        build_face("W3", "400", ["TencentSans", "TencentSans-W3"])
        + "\n"
        + build_face("W7", "700", ["TencentSans Bold", "TencentSans-W7"])
    )

    # 整段替换 TencentSans-W3 / W7 的 @font-face 块。
    # 正则匹配：@font-face { ... TencentSans-W{3,7}... } 一整块（含外层大括号）。
    face_pattern = re.compile(
        r"@font-face\s*\{[^{}]*TencentSans-W[37][^{}]*\}",
        re.IGNORECASE | re.DOTALL,
    )
    matches = face_pattern.findall(skin_css)
    if matches:
        # 第一处替换为新的两段；其余原 @font-face 块（W3/W7）全部清掉，避免重复定义
        first_match = matches[0]
        skin_css = skin_css.replace(first_match, rewritten_faces, 1)
        for m in matches[1:]:
            skin_css = skin_css.replace(m, "", 1)
    else:
        # 没匹配到（理论上不应发生）：直接前置注入，保证字体可用
        print(
            "Warning: TencentSans @font-face not found in skin css; prepending fresh blocks",
            file=sys.stderr,
        )
        skin_css = rewritten_faces + "\n" + skin_css
    # 追加全局覆盖：把 template.html 里没绑 var(--font-body) 的节点也拉到 TencentSans
    override = """
/* === tencent-blue · 字体全局强制覆盖（由 inject.py 注入）=== */
html, body,
h1, h2, h3, h4, h5, h6,
.heading, .hero-title, .hero-subtitle,
.brand, .section-label,
button, input, textarea, select,
p, li, span:not(.mono):not([class*="mono"]),
[data-ai-count], [data-ai-stagger] > *,
.num, .label, .oneliner {
  font-family: "TencentSans", "PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif !important;
}
.mono, code, pre, [class*="mono"] {
  font-family: "JetBrains Mono", SFMono-Regular, Consolas, monospace !important;
}
"""
    return skin_css + "\n" + override


def inject(scene: str, narrative: str, skin: str, data_file: str, output_path: str,
           keep_switcher: bool = False, keep_mock_fallback: bool = False):
    # === 资源定位（相对 COS 根路径）===
    template_rel = f"scenes/{scene}/{narrative}/template.html"
    skin_rel = f"_assets/skins/{skin}.css"
    motion_css_rel = "_assets/motion/motion.css"
    motion_js_rel = "_assets/motion/motion.js"

    html = fetch_template_resource(template_rel)
    skin_css = fetch_template_resource(skin_rel)
    motion_css = fetch_template_resource(motion_css_rel)
    motion_js = fetch_template_resource(motion_js_rel)

    # 腾讯系皮肤：字体 CDN 化 + 全局强制覆盖
    if skin in TENCENT_SKINS:
        skin_css = inline_tencent_fonts(skin_css)

    # --- 1) 读 data ---
    data_path = Path(data_file)
    if not data_path.is_file():
        print(f"Error: data file not found: {data_file}", file=sys.stderr)
        sys.exit(1)
    data_js = data_path.read_text(encoding="utf-8").strip()
    # 兼容两种写法：`const data = {...}` 和 `window.data = {...}`
    if "window.data" not in data_js:
        # 把 `const data = ` 改成 `window.data = `
        data_js = re.sub(r"^\s*(/\*\*[\s\S]*?\*/\s*)?const\s+data\s*=", "window.data =", data_js, count=1)

    # 注意：re.sub 的 repl 字符串会解析 \1 等反引用；replacement 里可能含 JS/CSS 的反斜杠字符，
    # 因此一律用 lambda 返回静态字符串，绕过模板解析。

    # --- 2) 替换 <script src="./mock-data.js"></script> ---
    mock_pattern = re.compile(r'<script[^>]*src="\./mock-data\.js"[^>]*></script>', re.IGNORECASE)
    inline_data = f'<script id="inlineData">\n{data_js}\n</script>'
    if mock_pattern.search(html):
        html = mock_pattern.sub(lambda m: inline_data, html, count=1)
    else:
        print("Warning: mock-data.js link not found; prepending data before first <script>", file=sys.stderr)
        html = re.sub(r'<script(?!.*src=)', lambda m: inline_data + '\n<script', html, count=1)

    # --- 3) 内联皮肤 CSS ---
    skin_link_pattern = re.compile(
        r'<link\s+id="skinCss"\s+rel="stylesheet"\s+href="[^"]+"\s*/?>',
        re.IGNORECASE,
    )
    inline_skin = f'<style id="skinCss" data-skin="{skin}">\n{skin_css}\n</style>'
    if skin_link_pattern.search(html):
        html = skin_link_pattern.sub(lambda m: inline_skin, html)
    else:
        fallback = re.compile(r'<link[^>]*href="[^"]*_assets/skins/[^"]+\.css"[^>]*/?>', re.IGNORECASE)
        html = fallback.sub(lambda m: inline_skin, html, count=1)

    # --- 4) 内联 motion.css ---
    motion_css_pattern = re.compile(r'<link[^>]*href="[^"]*_assets/motion/motion\.css"[^>]*/?>', re.IGNORECASE)
    inline_motion_css = f'<style id="motionCss">\n{motion_css}\n</style>'
    html = motion_css_pattern.sub(lambda m: inline_motion_css, html)

    # --- 5) 内联 motion.js ---
    motion_js_pattern = re.compile(r'<script[^>]*src="[^"]*_assets/motion/motion\.js"[^>]*></script>', re.IGNORECASE)
    inline_motion_js = f'<script id="motionJs" defer>\n{motion_js}\n</script>'
    html = motion_js_pattern.sub(lambda m: inline_motion_js, html)

    # --- 6) 移除皮肤切换器 ---
    if not keep_switcher:
        # 先尝试有注释标记的版本
        sw_pattern = re.compile(r'<!--\s*皮肤切换\s*-->[\s\S]*?<!--\s*/皮肤切换\s*-->', re.IGNORECASE)
        if sw_pattern.search(html):
            html = sw_pattern.sub("", html)
        else:
            # fallback：删除 class="skin-sw" 的 div（仅匹配不含嵌套 div 的简单情况）
            html = re.sub(r'<div\s+class="skin-sw">[^<]*(?:<(?!/div>)[^<]*)*</div>', "", html)

    # --- 7) 输出 ---
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    size_kb = len(html.encode("utf-8")) / 1024
    print(f"OK scene={scene} narrative={narrative} skin={skin} output={output_path} ({size_kb:.0f}KB)")


def main():
    p = argparse.ArgumentParser(description="Inject data + skin into template (COS-backed)")
    p.add_argument("--scene", required=True, help="scene id (proposal/sync/insight/share)")
    p.add_argument("--narrative", required=True, help="narrative id (pyramid/scqa/blm/...)")
    p.add_argument("--skin", required=True, help="skin id (stillwater/tencent-blue/...)")
    p.add_argument("--data", required=True, help="path to data.js file")
    p.add_argument("--output", required=True, help="output HTML path")
    p.add_argument("--keep-switcher", action="store_true")
    args = p.parse_args()
    inject(args.scene, args.narrative, args.skin, args.data, args.output, args.keep_switcher)


if __name__ == "__main__":
    main()
