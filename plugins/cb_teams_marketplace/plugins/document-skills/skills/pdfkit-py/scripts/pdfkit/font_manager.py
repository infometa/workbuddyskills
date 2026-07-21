#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdfkit 字体管理模块。

策略：
  1. 用户指定字体 → 直接使用
  2. 内置字体 NotoSansSC-Regular.ttf（setup 时从 CDN 下载到 <skill basedir>/fonts/）
     覆盖完整简体中文 + 常用 CJK，满足绝大多数场景
  3. 内置字体不存在时，自动搜索本机系统字体
  4. 搜索结果缓存，避免重复扫描

使用方式：
    from font_manager import resolve_font

    # 简单场景：直接拿内置字体
    font_path = resolve_font()

    # 带文本的场景（NotoSansSC 覆盖完整，通常直接命中内置字体）
    font_path = resolve_font(text="你好世界")

    # 用户指定字体：直接返回
    font_path = resolve_font(user_font="/path/to/font.ttf")
"""

import os
import sys
import platform

# ---------------------------------------------------------------------------
# 内置字体路径
# ---------------------------------------------------------------------------
# font_manager.py 位于 <skill basedir>/scripts/pdfkit/
# 内置字体位于      <skill basedir>/fonts/NotoSansSC-Regular.ttf

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_BASEDIR = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", ".."))

_BUNDLED_FONT_NAME = "NotoSansSC-Regular.ttf"
BUNDLED_FONT = os.path.join(_SKILL_BASEDIR, "fonts", _BUNDLED_FONT_NAME)


def _is_bundled_font_available():
    """检查内置字体是否已下载。"""
    return os.path.isfile(BUNDLED_FONT)


# ---------------------------------------------------------------------------
# 本机系统字体搜索
# ---------------------------------------------------------------------------

_system_cjk_font_cache = None  # 缓存搜索结果


# 各平台的 CJK 字体搜索路径
_SYSTEM_FONT_PATHS = {
    "Darwin": [
        # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/Supplemental/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        os.path.expanduser("~/Library/Fonts/NotoSansSC-Regular.ttf"),
        os.path.expanduser("~/Library/Fonts/NotoSansSC-Regular.otf"),
    ],
    "Linux": [
        # Linux 常见路径
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/droid/DroidSansFallback.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
        "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
        "/usr/share/fonts/google-droid/DroidSansFallback.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansFallback.ttf",
        "/usr/share/fonts/droid/DroidSansFallback.ttf",
        "/usr/share/fonts/truetype/DroidSansFallbackFull.ttf",
    ],
    "Windows": [
        # Windows
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyh.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyhbd.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simsun.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simhei.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simkai.ttf"),
    ],
}


def _detect_ttc_cjk_index(font_path):
    """检测 .ttc 字体集合中包含 CJK 字符的字体索引。

    PyMuPDF Shape.insert_text 对 .ttc 文件需要指定正确的 fontindex，
    否则可能加载到不含中文字形的子字体，导致渲染为方块。

    Args:
        font_path: .ttc 字体文件路径

    Returns:
        int: 包含 CJK 字符的字体索引，默认 0
    """
    if not font_path.lower().endswith('.ttc'):
        return 0

    try:
        from fontTools.ttLib import TTCollection
        ttc = TTCollection(font_path)
        # 用"中"字（U+4E2D）检测哪个子字体包含 CJK 字形
        test_cp = 0x4E2D
        for idx, font in enumerate(ttc.fonts):
            cmap = font.getBestCmap() or {}
            if test_cp in cmap:
                ttc.close()
                return idx
        ttc.close()
    except ImportError:
        pass
    except Exception:
        pass

    return 0


def find_system_cjk_font():
    """搜索本机系统中可用的 CJK 字体。

    Returns:
        str or None: 找到的字体路径，未找到返回 None
    """
    global _system_cjk_font_cache
    if _system_cjk_font_cache is not None:
        return _system_cjk_font_cache if _system_cjk_font_cache != "" else None

    system = platform.system()
    candidates = _SYSTEM_FONT_PATHS.get(system, [])

    # 也搜索其他平台的路径（跨平台兼容）
    for key, paths in _SYSTEM_FONT_PATHS.items():
        if key != system:
            candidates.extend(paths)

    # 优先选择 .ttf 文件（避免 .ttc 的 fontindex 问题）
    ttf_candidates = [p for p in candidates if p.lower().endswith('.ttf')]
    ttc_candidates = [p for p in candidates if not p.lower().endswith('.ttf')]

    for path in ttf_candidates + ttc_candidates:
        if os.path.exists(path):
            _system_cjk_font_cache = path
            return path

    # 深度搜索：遍历常见字体目录
    search_dirs = []
    if system == "Darwin":
        search_dirs = ["/System/Library/Fonts", "/Library/Fonts",
                       os.path.expanduser("~/Library/Fonts")]
    elif system == "Linux":
        search_dirs = ["/usr/share/fonts", "/usr/local/share/fonts",
                       os.path.expanduser("~/.fonts")]
    elif system == "Windows":
        search_dirs = [os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")]

    cjk_keywords = ["noto", "cjk", "droid", "wqy", "heiti", "songti",
                     "pingfang", "msyh", "simhei", "simsun", "simkai",
                     "hiragino", "gothic", "mincho"]

    # 深度搜索也优先 .ttf
    found_ttc = None
    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        try:
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if not f.lower().endswith(('.ttf', '.ttc', '.otf')):
                        continue
                    if any(kw in f.lower() for kw in cjk_keywords):
                        full_path = os.path.join(root, f)
                        if f.lower().endswith('.ttf'):
                            _system_cjk_font_cache = full_path
                            return full_path
                        elif found_ttc is None:
                            found_ttc = full_path
        except PermissionError:
            continue

    if found_ttc:
        _system_cjk_font_cache = found_ttc
        return found_ttc

    _system_cjk_font_cache = ""  # 标记已搜索过但未找到
    return None


def get_font_index(font_path):
    """获取字体文件的 CJK 字体索引。

    对于 .ttf/.otf 文件总是返回 0。
    对于 .ttc 集合文件，检测包含中文字形的子字体索引。

    Args:
        font_path: 字体文件路径

    Returns:
        int: 字体索引
    """
    if not font_path:
        return 0
    return _detect_ttc_cjk_index(font_path)


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------

def resolve_font(text=None, user_font=None, require_full_cjk=False):
    """智能选择字体路径。

    优先级：
      1. 用户指定字体 → 直接返回
      2. 内置 NotoSansSC-Regular.ttf（完整简体中文） → 直接返回
      3. 本机系统 CJK 字体 → 搜索并返回
      4. 均无 → 返回 None 并打印警告

    Args:
        text: 待渲染的文本（可选，保留参数兼容性）。
        user_font: 用户指定的字体路径（可选）。传入后直接返回。
        require_full_cjk: 强制要求完整 CJK 字体（保留参数兼容性，
                          NotoSansSC 本身即为完整字体，此参数不再影响选择逻辑）。

    Returns:
        str or None: 字体文件路径
    """
    # 1. 用户指定
    if user_font and os.path.exists(user_font):
        return user_font

    # 2. 内置 NotoSansSC（完整简体中文，无需 cmap 检测）
    if _is_bundled_font_available():
        return BUNDLED_FONT

    # 3. 搜索本机系统字体
    sys_font = find_system_cjk_font()
    if sys_font:
        return sys_font

    # 4. 均无可用字体
    print(
        "[font_manager] 警告: 未找到可用的中文字体。"
        "\n  内置字体不存在，本机也未找到 CJK 字体。"
        "\n  请运行 setup.sh (macOS/Linux) 或 setup.bat (Windows) 下载内置字体。",
        file=sys.stderr,
    )
    return None


def get_bundled_font():
    """直接获取内置字体路径（不做任何检测）。

    Returns:
        str or None: 内置字体路径
    """
    return BUNDLED_FONT if _is_bundled_font_available() else None


def text_covered_by_bundled(text):
    """检查文本是否被内置字体覆盖。

    NotoSansSC-Regular 覆盖完整简体中文，此函数保留以兼容外部调用。
    当内置字体存在时直接返回 True（NotoSansSC 覆盖范围极广）；
    当内置字体不存在时返回 False。

    Args:
        text: 待检查的文本字符串

    Returns:
        (bool, list[str]): (是否全覆盖, 未覆盖的字符列表)
    """
    if not text:
        return True, []
    if _is_bundled_font_available():
        return True, []
    # 内置字体不存在，保守返回 False
    return False, list(set(text))


# ---------------------------------------------------------------------------
# 跨引擎辅助函数
# ---------------------------------------------------------------------------

def make_fitz_font(font_path):
    """创建 fitz.Font 对象，正确处理 .ttc 字体集合。

    对 .ttc 文件自动检测包含 CJK 字形的子字体索引。
    对 .ttf/.otf 文件直接加载。

    Args:
        font_path: 字体文件路径

    Returns:
        fitz.Font 对象
    """
    import fitz
    if not font_path or not os.path.exists(font_path):
        return fitz.Font("helv")
    idx = _detect_ttc_cjk_index(font_path)
    return fitz.Font(fontfile=font_path, fontindex=idx)


def make_pil_font(font_path, font_size):
    """创建 PIL ImageFont 对象，正确处理 .ttc 字体集合。

    Args:
        font_path: 字体文件路径
        font_size: 字号（像素）

    Returns:
        PIL.ImageFont 对象
    """
    from PIL import ImageFont
    if not font_path or not os.path.exists(font_path):
        return ImageFont.load_default()
    idx = _detect_ttc_cjk_index(font_path)
    return ImageFont.truetype(font_path, font_size, index=idx)


def register_reportlab_font(font_name, font_path):
    """在 ReportLab 中注册字体，正确处理 .ttc 字体集合。

    Args:
        font_name: 注册的字体名称
        font_path: 字体文件路径

    Returns:
        bool: 注册是否成功
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if not font_path or not os.path.exists(font_path):
        return False

    try:
        if font_path.lower().endswith('.ttc'):
            idx = _detect_ttc_cjk_index(font_path)
            pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=idx))
        else:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        return True
    except Exception:
        # 对 .ttc 降级尝试遍历索引
        if font_path.lower().endswith('.ttc'):
            for i in range(10):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=i))
                    return True
                except Exception:
                    continue
        return False
