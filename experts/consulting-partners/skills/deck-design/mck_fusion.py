#!/usr/bin/env python3
"""
mck_fusion —— 双引擎融合适配层（consulting-partners / deck-design）

背景：本 skill 融合两套麦肯锡风 PPT 引擎——
  - 主引擎 mck_ppt（源自 likaku/Mck-ppt-design-skill, Apache-2.0）：67 种版式 + 中文楷体 + 机读门禁，做骨架。
  - 补充版式 mckinsey_pptx（源自 seulee26/mckinsey-pptx, MIT）：甘特图/BCG矩阵/气泡图等 mck_ppt 相对弱或缺的版式。

风格统一是融合成败关键：两套原生配色/边距/字号不同，直接混用会视觉跳变。
本模块把 mckinsey_pptx 的 Theme **覆写成 mck_ppt 的设计令牌**（MCK_ALIGNED_THEME），
再让 mckinsey_pptx 的版式函数在 **同一个 MckEngine.prs** 上作画——做到"两套引擎、一套皮肤"。

用法：
    from mck_ppt import MckEngine
    from mck_fusion import FusionDeck
    d = FusionDeck(total_slides=8)
    d.eng.cover(title='...', subtitle='...')          # 直接用 mck_ppt 原生版式
    d.eng.executive_summary(...)                       # 同上
    d.mck('gantt_timeline', title='...', ...)          # 用 mckinsey_pptx 补充版式(自动套对齐皮肤)
    d.mck('growth_share', title='...', ...)            # BCG 矩阵
    d.save('output/deck.pptx')

依赖：python-pptx, lxml（核心）。中文默认楷体（mck_ppt 已内置注入）。
"""
import os
import sys
from dataclasses import replace

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from mck_ppt import MckEngine
from mck_ppt import constants as C

from mckinsey_pptx.theme import Theme, Palette, Typography, Layout, DEFAULT_THEME
from mckinsey_pptx.base import blank_slide
from mckinsey_pptx import builder as _mck_builder


def _rgb_to_hexobj(c):
    """mck_ppt 用 RGBColor，mckinsey_pptx 的 Palette 字段也用 RGBColor，直接透传。"""
    return c


# ── 把 mckinsey_pptx 的令牌覆写为 mck_ppt 的设计令牌（同色/同网格/同字号）──
_ALIGNED_PALETTE = replace(
    Palette(),
    dark_navy=C.NAVY, deep_navy=C.NAVY,
    bright_blue=C.ACCENT_BLUE, mid_blue=C.ACCENT_BLUE, light_blue=C.LIGHT_BLUE,
    black=C.BLACK, white=C.WHITE, text_dark=C.DARK_GRAY,
    rule_gray=C.LINE_GRAY, light_gray=C.LINE_GRAY, soft_gray=C.BG_GRAY,
    grid_gray=C.LINE_GRAY, footer_gray=C.MED_GRAY, placeholder_gray=C.MED_GRAY,
    status_green=C.ACCENT_GREEN, status_amber=C.ACCENT_ORANGE, status_red=C.ACCENT_RED,
)
_ALIGNED_TYPO = replace(
    Typography(),
    family='Arial',
    title_size=22,          # 对齐 mck ACTION_TITLE_SIZE
    section_title_size=14,
    body_size=14,           # 对齐 mck BODY_SIZE(原 mckinsey 是 12)
    small_size=12,
    footer_size=9,
    chart_label_size=12, chart_axis_size=10,
)
_ALIGNED_LAYOUT = replace(
    Layout(),
    slide_width_in=13.333, slide_height_in=7.5,
    margin_left_in=0.8, margin_right_in=0.8,     # 对齐 mck LM/RM
    margin_top_in=0.15, margin_bottom_in=0.3,
    title_top_in=0.15, title_height_in=0.9,
    title_underline_top_in=1.05,                  # 对齐 mck TITLE_LINE_Y
    body_top_in=1.3,                              # 对齐 mck CONTENT_TOP
    footer_top_in=7.05,
)
MCK_ALIGNED_THEME = replace(
    DEFAULT_THEME,
    palette=_ALIGNED_PALETTE, typography=_ALIGNED_TYPO, layout=_ALIGNED_LAYOUT,
    copyright_text='',
)


class FusionDeck:
    """持有一个 MckEngine，既能用 mck_ppt 原生 67 版式，也能用 mckinsey_pptx 的补充版式，
    两者画到同一个 presentation、同一套 MCK_ALIGNED_THEME 皮肤。"""

    def __init__(self, total_slides):
        self.eng = MckEngine(total_slides=total_slides)
        self.prs = self.eng.prs
        self.theme = MCK_ALIGNED_THEME

    def mck(self, slide_type, **kwargs):
        """用 mckinsey_pptx 的某个补充版式加一页（自动套对齐皮肤）。
        slide_type 见 mckinsey_pptx.builder._REGISTRY（gantt_timeline / growth_share /
        bubble_chart / column_historic_forecast / waves_timeline_4 / three_trends_* 等）。

        注意：mckinsey_pptx 的版式函数签名为 add_xxx(prs, *, ..., theme=...)，
        它内部自己 blank_slide(prs) 建页并 add_chrome。我们只需把 self.prs + 对齐 theme 传进去，
        它就会把这一页加进 MckEngine 的同一个 presentation，且套用 MCK_ALIGNED_THEME 皮肤。"""
        fn = _mck_builder._REGISTRY.get(slide_type)
        if fn is None:
            raise ValueError(
                f"未知补充版式: {slide_type}。可用: {sorted(_mck_builder._REGISTRY.keys())}")
        kwargs.setdefault('theme', self.theme)
        return fn(self.prs, **kwargs)

    @staticmethod
    def available_fusion_layouts():
        return sorted(_mck_builder._REGISTRY.keys())

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.eng.save(path)
        # MckEngine.save 的打印只统计它自己经手的页,融合进来的 mckinsey 页不计入 →
        # 这里按 prs 真实页数覆盖报告,避免"少报页数"误导(真实页数以 prs 为准)。
        real_n = len(self.prs.slides._sldIdLst)
        print(f"[fusion] 实际总页数(含两套引擎): {real_n} 页 → {path}")
        return path
