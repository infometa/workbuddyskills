"""
setup_chinese_pdf  –  CJK font bootstrap for reportlab
=======================================================

Import this module in **every** reportlab script that generates PDFs,
regardless of whether the content is Chinese or English:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
    from setup_chinese_pdf import setup_chinese_pdf

    cn_font, styles = setup_chinese_pdf()

`cn_font`  – registered font name; pass to canvas.setFont() and ParagraphStyle.
`styles`   – a pre-patched StyleSheet1 where every ParagraphStyle already uses
             the CJK font. Use styles['Title'], styles['Normal'], etc. directly.

Run standalone to verify font availability:

    python scripts/setup_chinese_pdf.py
"""

import os
import platform
import sys

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def setup_chinese_pdf():
    """
    Register a system CJK font and return (cn_font, styles).

    cn_font: the registered font name — pass to canvas.setFont() and any
             ParagraphStyle you create manually via fontName=cn_font.

    styles:  a StyleSheet1 where ALL default ParagraphStyles already use
             the CJK font. Use styles['Title'], styles['Normal'], etc.
             directly — Chinese will render correctly without extra args.

    Also works for child styles: ParagraphStyle('X', parent=styles['Title'])
    will inherit the CJK fontName because the parent was patched BEFORE the
    child was constructed (ParagraphStyle copies parent attrs at init time).
    """
    system = platform.system()

    if system == 'Darwin':  # macOS
        # PingFang.ttc does NOT exist on disk — it is a virtual system font.
        # STHeiti / Songti are real files present on all macOS versions.
        candidates = [
            ('/System/Library/Fonts/STHeiti Light.ttc',       'STHeiti',       0),
            ('/System/Library/Fonts/STHeiti Medium.ttc',      'STHeitiMedium', 0),
            ('/System/Library/Fonts/Supplemental/Songti.ttc', 'Songti',        0),
            ('/Library/Fonts/Arial Unicode MS.ttf',           'ArialUnicode',  0),
        ]
    elif system == 'Windows':
        candidates = []
        dirs = []
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        dirs.append(os.path.join(windir, 'Fonts'))
        local = os.environ.get('LOCALAPPDATA', '')
        if local:
            dirs.append(os.path.join(local, 'Microsoft', 'Windows', 'Fonts'))
        for d in dirs:
            for fname, name, idx in [
                ('msyh.ttc',   'MicrosoftYaHei', 0),   # 微软雅黑 — Win10/11
                ('msyhbd.ttc', 'MicrosoftYaHeiBold', 0),
                ('simhei.ttf', 'SimHei',          0),   # 黑体
                ('simsun.ttc', 'SimSun',          0),   # 宋体
                ('mingliu.ttc','MingLiU',         0),   # 細明體
            ]:
                candidates.append((os.path.join(d, fname), name, idx))
    else:  # Linux
        candidates = [
            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
            ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',           'WQYZenHei',   0),
            ('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf','DroidSans',  0),
        ]

    cn_font = None
    for font_path, font_name, idx in candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=idx))
                cn_font = font_name
                break
            except Exception:
                continue
    if cn_font is None:
        raise RuntimeError(
            f"No CJK font found on {system}.\n"
            "  macOS:   check /System/Library/Fonts/\n"
            "  Windows: ensure msyh.ttc or simhei.ttf in %WINDIR%\\Fonts\n"
            "  Linux:   sudo apt install fonts-noto-cjk"
        )

    # Build a stylesheet with ALL styles pre-patched to use the CJK font.
    # This eliminates garbling even if fontName= is accidentally omitted.
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        if isinstance(style, ParagraphStyle):
            style.fontName = cn_font

    return cn_font, styles


# ---------------------------------------------------------------------------
# Self-test: run  `python setup_chinese_pdf.py`  to verify font availability.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        font, _ = setup_chinese_pdf()
        print(f"OK — CJK font registered: {font}")
    except RuntimeError as exc:
        print(f"FAIL — {exc}", file=sys.stderr)
        sys.exit(1)
