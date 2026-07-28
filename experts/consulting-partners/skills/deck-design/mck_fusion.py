#!/usr/bin/env python3
"""Strict two-engine adapter for the consulting deck pipeline."""
import inspect
import os
import sys
from dataclasses import replace

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from mck_ppt import MckEngine
from mck_ppt import constants as C
from mckinsey_pptx.theme import Palette, Typography, Layout, DEFAULT_THEME
from mckinsey_pptx import builder as _mck_builder


_ALIGNED_PALETTE = replace(
    Palette(),
    dark_navy=C.NAVY,
    deep_navy=C.NAVY,
    bright_blue=C.ACCENT_BLUE,
    mid_blue=C.ACCENT_BLUE,
    light_blue=C.LIGHT_BLUE,
    black=C.BLACK,
    white=C.WHITE,
    text_dark=C.DARK_GRAY,
    rule_gray=C.LINE_GRAY,
    light_gray=C.LINE_GRAY,
    soft_gray=C.BG_GRAY,
    grid_gray=C.LINE_GRAY,
    footer_gray=C.MED_GRAY,
    placeholder_gray=C.MED_GRAY,
    status_green=C.ACCENT_GREEN,
    status_amber=C.ACCENT_ORANGE,
    status_red=C.ACCENT_RED,
)
_ALIGNED_TYPO = replace(
    Typography(),
    family="Arial",
    title_size=22,
    section_title_size=14,
    body_size=14,
    small_size=12,
    footer_size=9,
    chart_label_size=12,
    chart_axis_size=10,
)
_ALIGNED_LAYOUT = replace(
    Layout(),
    slide_width_in=13.333,
    slide_height_in=7.5,
    margin_left_in=0.8,
    margin_right_in=0.8,
    margin_top_in=0.15,
    margin_bottom_in=0.3,
    title_top_in=0.15,
    title_height_in=0.9,
    title_underline_top_in=1.05,
    body_top_in=1.3,
    footer_top_in=7.05,
)
MCK_ALIGNED_THEME = replace(
    DEFAULT_THEME,
    palette=_ALIGNED_PALETTE,
    typography=_ALIGNED_TYPO,
    layout=_ALIGNED_LAYOUT,
    copyright_text="",
)

_ENGINE_ALIASES = {
    "main": "main",
    "mck_ppt": "main",
    "supplemental": "supplemental",
    "mckinsey_pptx": "supplemental",
}
_RESERVED_DATA_FIELDS = {"page_number", "theme", "prs", "presentation"}


def _format_sources(sources):
    if not sources:
        return ""
    if not isinstance(sources, list):
        raise ValueError("source must be a structured array")
    rendered = []
    for item in sources:
        if not isinstance(item, dict) or not str(item.get("label", "")).strip():
            raise ValueError("each source item must contain a non-empty label")
        label = str(item["label"]).strip()
        url = str(item.get("url", "")).strip()
        rendered.append(f"{label} ({url})" if url else label)
    return "; ".join(rendered)


def _accepts(parameter_name, fn):
    return parameter_name in inspect.signature(fn).parameters


class FusionDeck:
    """Build one presentation through a strict, fail-fast two-engine API."""

    def __init__(self, total_slides):
        if not isinstance(total_slides, int) or isinstance(total_slides, bool) or total_slides <= 0:
            raise ValueError("total_slides must be a positive integer")
        self.total_slides = total_slides
        self.eng = MckEngine(total_slides=total_slides)
        self.prs = self.eng.prs
        self.theme = MCK_ALIGNED_THEME

    @staticmethod
    def available_primary_layouts():
        excluded = {"save"}
        return sorted(
            name
            for name, fn in inspect.getmembers(MckEngine, predicate=inspect.isfunction)
            if not name.startswith("_") and name not in excluded
        )

    @staticmethod
    def available_fusion_layouts():
        return sorted(_mck_builder._REGISTRY.keys())

    def _add_primary(self, layout, kwargs):
        if layout not in self.available_primary_layouts():
            raise ValueError(
                f"Unknown primary layout: {layout}. Available: {self.available_primary_layouts()}"
            )
        fn = getattr(self.eng, layout)
        before = len(self.prs.slides)
        self.eng._page = before
        try:
            slide = fn(**kwargs)
        except Exception as exc:
            raise RuntimeError(f"Primary layout {layout} failed: {exc}") from exc
        after = len(self.prs.slides)
        if after != before + 1 or self.eng._page != after:
            raise RuntimeError(
                f"Primary layout {layout} must add exactly one slide; before={before}, after={after}, page={self.eng._page}"
            )
        return slide

    def mck(self, slide_type, **kwargs):
        if slide_type not in self.available_fusion_layouts():
            raise ValueError(
                f"Unknown supplemental layout: {slide_type}. Available: {self.available_fusion_layouts()}"
            )
        fn = _mck_builder._REGISTRY[slide_type]
        before = len(self.prs.slides)
        next_page = before + 1
        self.eng._page = before
        kwargs = dict(kwargs)
        if _accepts("page_number", fn):
            kwargs.setdefault("page_number", f"{next_page}/{self.total_slides}")
        if _accepts("theme", fn):
            kwargs.setdefault("theme", self.theme)
        try:
            slide = fn(self.prs, **kwargs)
        except Exception as exc:
            raise RuntimeError(f"Supplemental layout {slide_type} failed: {exc}") from exc
        after = len(self.prs.slides)
        if after != before + 1:
            raise RuntimeError(
                f"Supplemental layout {slide_type} must add exactly one slide; before={before}, after={after}"
            )
        self.eng._page = after
        return slide

    def add_spec(self, spec):
        if not isinstance(spec, dict):
            raise TypeError("slide spec must be an object")
        expected_idx = len(self.prs.slides) + 1
        idx = spec.get("idx")
        if idx != expected_idx:
            raise ValueError(f"slide idx must be {expected_idx}, got {idx}")

        layout = str(spec.get("layout", "")).strip()
        if not layout:
            raise ValueError(f"slide {idx} is missing layout")
        engine_raw = str(spec.get("engine", "main")).strip()
        engine = _ENGINE_ALIASES.get(engine_raw)
        if engine is None:
            raise ValueError(f"slide {idx} has unknown engine: {engine_raw}")

        data = spec.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"slide {idx} data must be an object")
        forbidden = sorted(_RESERVED_DATA_FIELDS.intersection(data))
        if forbidden:
            raise ValueError(f"slide {idx} data contains reserved fields: {forbidden}")
        kwargs = dict(data)
        source_text = _format_sources(spec.get("source", []))
        title = spec.get("title")

        if engine == "main":
            if layout not in self.available_primary_layouts():
                raise ValueError(f"slide {idx} uses unknown primary layout: {layout}")
            fn = getattr(self.eng, layout)
            if _accepts("title", fn):
                kwargs.setdefault("title", title)
            if source_text and _accepts("source", fn):
                kwargs.setdefault("source", source_text)
            return self._add_primary(layout, kwargs)

        fn = _mck_builder._REGISTRY.get(layout)
        if fn is None:
            raise ValueError(f"slide {idx} uses unknown supplemental layout: {layout}")
        if _accepts("title", fn):
            kwargs.setdefault("title", title)
        if source_text and _accepts("source", fn):
            kwargs.setdefault("source", source_text)
        return self.mck(layout, **kwargs)

    def build_specs(self, specs):
        if not isinstance(specs, list) or not specs:
            raise ValueError("specs must be a non-empty array")
        if len(specs) != self.total_slides:
            raise ValueError(
                f"spec count {len(specs)} does not match total_slides {self.total_slides}"
            )
        slides = []
        for spec in specs:
            idx = spec.get("idx", "?") if isinstance(spec, dict) else "?"
            try:
                slides.append(self.add_spec(spec))
            except Exception as exc:
                raise RuntimeError(f"Failed to build slide {idx}: {exc}") from exc
        return slides

    add_specs = build_specs

    def save(self, path):
        real_count = len(self.prs.slides)
        if real_count != self.total_slides:
            raise RuntimeError(
                f"Refusing to save: actual slides {real_count} != declared total {self.total_slides}"
            )
        if self.eng._page != self.total_slides:
            raise RuntimeError(
                f"Refusing to save: page counter {self.eng._page} != declared total {self.total_slides}"
            )
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.eng.save(path)
        return path
