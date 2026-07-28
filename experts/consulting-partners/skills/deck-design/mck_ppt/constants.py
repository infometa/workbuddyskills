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

# Primary colors — warm deep charcoal with subtle brown undertone
NAVY       = RGBColor(0x2C, 0x2C, 0x34)   # Warm charcoal (not blue-cold)
BLACK      = RGBColor(0x00, 0x00, 0x00)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)

# Gray scale — warm undertones throughout
DARK_GRAY  = RGBColor(0x3D, 0x3D, 0x42)   # Warm near-black for body text
MED_GRAY   = RGBColor(0x7A, 0x77, 0x72)   # Warm taupe gray for secondary
LINE_GRAY  = RGBColor(0xE2, 0xDD, 0xD8)   # Warm sand divider
BG_GRAY    = RGBColor(0xFA, 0xF8, 0xF5)   # Warm off-white / cream tint

# Accent colors — warm-leaning palette
ACCENT_BLUE   = RGBColor(0xC4, 0x7A, 0x2B)  # Warm copper/amber (primary accent)
ACCENT_GREEN  = RGBColor(0x5E, 0x8C, 0x6A)  # Sage green (muted, warm)
ACCENT_ORANGE = RGBColor(0xD9, 0x7B, 0x2D)  # Burnt sienna
ACCENT_RED    = RGBColor(0xB5, 0x4C, 0x4C)  # Dusty rose-red
SLATE_BLUE    = RGBColor(0x3A, 0x38, 0x3F)  # Warm dark panel (charcoal-purple tint)
PALE_BLUE     = RGBColor(0xF5, 0xF0, 0xE8)  # Warm cream highlight

# Light accent backgrounds — warm harmonized
LIGHT_BLUE    = RGBColor(0xFB, 0xF5, 0xEB)  # Light warm gold
LIGHT_GREEN   = RGBColor(0xEF, 0xF5, 0xF0)  # Pale sage
LIGHT_ORANGE  = RGBColor(0xFD, 0xF3, 0xE7)  # Light apricot
LIGHT_RED     = RGBColor(0xFA, 0xED, 0xED)  # Blush pink

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

# Use a restrained modern sans-serif system. East Asian text explicitly
# selects Microsoft YaHei for broad Office compatibility instead of a
# calligraphic font that weakens the executive-consulting tone.
FONT_HEADER = 'Arial'
FONT_BODY   = 'Arial'
FONT_EA     = 'Microsoft YaHei'