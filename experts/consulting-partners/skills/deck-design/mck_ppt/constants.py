# Copyright 2024-2026 Kaku Li (https://github.com/likaku)
# Licensed under the Apache License, Version 2.0 — see LICENSE and NOTICE.
# Part of "Mck-ppt-design-skill" (McKinsey PPT Design Framework).
# NOTICE: This file must be retained in all copies or substantial portions.
#
"""McKinsey Design System — Color palette, typography, and layout constants."""
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# ═══════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════

# Primary colors
NAVY       = RGBColor(0x05, 0x1C, 0x2C)
BLACK      = RGBColor(0x00, 0x00, 0x00)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)

# Gray scale
DARK_GRAY  = RGBColor(0x33, 0x33, 0x33)
MED_GRAY   = RGBColor(0x66, 0x66, 0x66)
LINE_GRAY  = RGBColor(0xCC, 0xCC, 0xCC)
BG_GRAY    = RGBColor(0xF2, 0xF2, 0xF2)

# Accent colors (for 3+ parallel items)
ACCENT_BLUE   = RGBColor(0x00, 0x6B, 0xA6)
ACCENT_GREEN  = RGBColor(0x00, 0x7A, 0x53)
ACCENT_ORANGE = RGBColor(0xD4, 0x6A, 0x00)
ACCENT_RED    = RGBColor(0xC6, 0x28, 0x28)

# Light accent backgrounds
LIGHT_BLUE    = RGBColor(0xE3, 0xF2, 0xFD)
LIGHT_GREEN   = RGBColor(0xE8, 0xF5, 0xE9)
LIGHT_ORANGE  = RGBColor(0xFF, 0xF3, 0xE0)
LIGHT_RED     = RGBColor(0xFF, 0xEB, 0xEE)

# Paired accent sets: (accent, light_bg) for easy iteration
ACCENT_PAIRS = [
    (ACCENT_BLUE,   LIGHT_BLUE),
    (ACCENT_GREEN,  LIGHT_GREEN),
    (ACCENT_ORANGE, LIGHT_ORANGE),
    (ACCENT_RED,    LIGHT_RED),
]

# ═══════════════════════════════════════════
# SLIDE DIMENSIONS
# ═══════════════════════════════════════════

SW = Inches(13.333)  # Slide width (16:9)
SH = Inches(7.5)     # Slide height
LM = Inches(0.8)     # Left margin
RM = Inches(0.8)     # Right margin
CW = Inches(11.733)  # Content width = SW - LM - RM

# ═══════════════════════════════════════════
# VERTICAL GRID
# ═══════════════════════════════════════════

TITLE_TOP       = Inches(0.15)   # Action title top
TITLE_H         = Inches(0.9)    # Action title height
TITLE_LINE_Y    = Inches(1.05)   # Separator under title
CONTENT_TOP     = Inches(1.3)    # Content area start
SOURCE_Y        = Inches(7.05)   # Source attribution line
PAGE_NUM_X      = Inches(12.2)   # Page number left
BOTTOM_BAR_Y    = Inches(6.2)    # Default bottom summary bar
BOTTOM_BAR_H    = Inches(0.65)   # Bottom bar height

# ═══════════════════════════════════════════
# TYPOGRAPHY
# ═══════════════════════════════════════════

COVER_TITLE_SIZE   = Pt(44)
SECTION_TITLE_SIZE = Pt(28)
ACTION_TITLE_SIZE  = Pt(22)
SUB_HEADER_SIZE    = Pt(18)
EMPHASIS_SIZE      = Pt(16)
BODY_SIZE          = Pt(14)
SMALL_SIZE         = Pt(12)
FOOTNOTE_SIZE      = Pt(9)

FONT_HEADER = 'Georgia'
FONT_BODY   = 'Arial'
FONT_EA     = 'KaiTi'