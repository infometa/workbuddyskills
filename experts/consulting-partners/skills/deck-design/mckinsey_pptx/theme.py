from dataclasses import dataclass, field
from pptx.util import Pt, Inches, Emu
from pptx.dml.color import RGBColor


def rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


@dataclass(frozen=True)
class Palette:
    dark_navy: RGBColor = field(default_factory=lambda: rgb("0F2A4A"))
    deep_navy: RGBColor = field(default_factory=lambda: rgb("0A1F3D"))
    bright_blue: RGBColor = field(default_factory=lambda: rgb("2E9BD6"))
    mid_blue: RGBColor = field(default_factory=lambda: rgb("1F6FA8"))
    light_blue: RGBColor = field(default_factory=lambda: rgb("4FB2E5"))
    royal_blue: RGBColor = field(default_factory=lambda: rgb("2A2AE5"))
    black: RGBColor = field(default_factory=lambda: rgb("000000"))
    white: RGBColor = field(default_factory=lambda: rgb("FFFFFF"))
    text_dark: RGBColor = field(default_factory=lambda: rgb("1A1A1A"))
    rule_gray: RGBColor = field(default_factory=lambda: rgb("999999"))
    light_gray: RGBColor = field(default_factory=lambda: rgb("E8E8E8"))
    soft_gray: RGBColor = field(default_factory=lambda: rgb("F2F2F2"))
    grid_gray: RGBColor = field(default_factory=lambda: rgb("D0D0D0"))
    footer_gray: RGBColor = field(default_factory=lambda: rgb("888888"))
    placeholder_gray: RGBColor = field(default_factory=lambda: rgb("BFBFBF"))
    status_green: RGBColor = field(default_factory=lambda: rgb("4CAF50"))
    status_amber: RGBColor = field(default_factory=lambda: rgb("F4C57A"))
    status_red: RGBColor = field(default_factory=lambda: rgb("E04E5E"))


@dataclass(frozen=True)
class Typography:
    family: str = "Arial"
    title_size: int = 24
    section_title_size: int = 14
    body_size: int = 12
    small_size: int = 10
    footer_size: int = 9
    chart_label_size: int = 10
    chart_axis_size: int = 10


@dataclass(frozen=True)
class Layout:
    slide_width_in: float = 13.333
    slide_height_in: float = 7.5
    margin_left_in: float = 0.45
    margin_right_in: float = 0.45
    margin_top_in: float = 0.35
    margin_bottom_in: float = 0.3
    title_top_in: float = 0.45
    title_height_in: float = 0.7
    title_underline_top_in: float = 1.15
    body_top_in: float = 1.40
    footer_top_in: float = 7.05
    section_marker_w_in: float = 1.4
    section_marker_h_in: float = 0.3


@dataclass(frozen=True)
class Theme:
    palette: Palette = field(default_factory=Palette)
    typography: Typography = field(default_factory=Typography)
    layout: Layout = field(default_factory=Layout)
    copyright_text: str = "Copyright of mckinsey-AX"


DEFAULT_THEME = Theme()
