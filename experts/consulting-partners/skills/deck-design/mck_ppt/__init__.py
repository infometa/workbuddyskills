# Copyright 2024-2026 Kaku Li (https://github.com/likaku)
# Licensed under the Apache License, Version 2.0 — see LICENSE and NOTICE.
# Part of "Mck-ppt-design-skill" (McKinsey PPT Design Framework).
# NOTICE: This file must be retained in all copies or substantial portions.
#
"""McKinsey PPT Design Framework — High-level Layout Function Library.

Usage:
    from mck_ppt import MckEngine
    eng = MckEngine(total_slides=30)
    eng.cover(title='My Title', subtitle='Subtitle')
    eng.toc(items=[('1','Topic','Description'), ...])
    eng.save('output/my_deck.pptx')
"""
from .engine import MckEngine
from .constants import *
from .review import SlideReviewer, AutoFixPipeline, review, autofix


def generate_cover_image(*args, **kwargs):
    from .cover_image import generate_cover_image as _generate_cover_image
    return _generate_cover_image(*args, **kwargs)

__version__ = '2.3.0'