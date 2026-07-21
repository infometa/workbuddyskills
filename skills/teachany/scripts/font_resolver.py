#!/usr/bin/env python3
"""TeachAny CJK/STEM font resolver.

Use this module whenever Pillow generates images containing Chinese text,
chemical formulas, math symbols, arrows, superscripts, or subscripts.

Python usage:
    from font_resolver import get_pillow_font, resolve_font_path
    title_font = get_pillow_font(56, require_stem=True)

CLI usage:
    python3 scripts/font_resolver.py --check
    python3 scripts/font_resolver.py --print-path
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Characters that commonly break in local Pillow-generated STEM images.
CJK_SAMPLE = "原电池化学能电能盐桥阳极阴极"
STEM_SAMPLE = "Zn²⁺ Cu²⁺ NO₃⁻ e⁻ H₂O ΔG° E° → ⇌ −"

FONT_CANDIDATES = [
    # Explicit override always wins.
    os.environ.get("TEACHANY_CJK_FONT", ""),

    # macOS: best coverage for CJK + chemical/math superscripts/subscripts.
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",

    # User-installed Source Han / Noto fonts.
    str(Path.home() / "Library/Fonts/SourceHanSansCN-VF-2.otf"),
    str(Path.home() / "Library/Fonts/SourceHanSansSC-Regular.otf"),
    str(Path.home() / "Library/Fonts/NotoSansCJKsc-Regular.otf"),

    # Linux common packages.
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Regular.otf",

    # Windows common CJK fonts. Use only as last resort; STEM coverage varies.
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]


def _font_cmap_has(path: Path, sample: str) -> bool:
    """Return True when font cmap contains all chars in sample.

    Uses fontTools when available. For TTC collections, any face passing is OK.
    If fontTools is unavailable, fall back to Pillow-load-only check.
    """
    try:
        from fontTools.ttLib import TTCollection, TTFont  # type: ignore
    except Exception:
        # Still better than silently falling back to ImageFont.load_default().
        try:
            from PIL import ImageFont
            ImageFont.truetype(str(path), 24)
            return True
        except Exception:
            return False

    codepoints = {ord(ch) for ch in sample if not ch.isspace()}

    def ttfont_ok(font) -> bool:
        cmap = set()
        for table in font["cmap"].tables:
            cmap.update(table.cmap.keys())
        return codepoints.issubset(cmap)

    try:
        if path.suffix.lower() == ".ttc":
            collection = TTCollection(str(path))
            return any(ttfont_ok(font) for font in collection.fonts)
        font = TTFont(str(path), lazy=True)
        return ttfont_ok(font)
    except Exception:
        return False


def resolve_font_path(require_stem: bool = True) -> str:
    """Resolve a font path with CJK and optional STEM-symbol coverage.

    Raises RuntimeError instead of silently using Pillow's default bitmap font.
    """
    sample = CJK_SAMPLE + (STEM_SAMPLE if require_stem else "")
    tried: list[str] = []
    for raw in FONT_CANDIDATES:
        if not raw:
            continue
        path = Path(raw).expanduser()
        tried.append(str(path))
        if path.exists() and _font_cmap_has(path, sample):
            return str(path)

    raise RuntimeError(
        "未找到可安全渲染中文与理科符号的字体。\n"
        "请安装 Arial Unicode MS / Noto Sans CJK / Source Han Sans，"
        "或设置环境变量 TEACHANY_CJK_FONT=/absolute/path/to/font.ttf。\n"
        "已尝试：\n- " + "\n- ".join(tried)
    )


def get_pillow_font(size: int = 36, require_stem: bool = True):
    """Return PIL.ImageFont.FreeTypeFont using the resolved safe font."""
    from PIL import ImageFont

    return ImageFont.truetype(resolve_font_path(require_stem=require_stem), size)


def main() -> int:
    parser = argparse.ArgumentParser(description="TeachAny CJK/STEM font resolver")
    parser.add_argument("--print-path", action="store_true", help="print resolved font path")
    parser.add_argument("--check", action="store_true", help="validate current environment")
    parser.add_argument("--no-stem", action="store_true", help="only require CJK coverage")
    args = parser.parse_args()

    try:
        path = resolve_font_path(require_stem=not args.no_stem)
    except RuntimeError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    if args.print_path:
        print(path)
    if args.check or not args.print_path:
        print(f"✅ TeachAny 字体可用: {path}")
        print(f"   sample: {CJK_SAMPLE} {STEM_SAMPLE if not args.no_stem else ''}".rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
