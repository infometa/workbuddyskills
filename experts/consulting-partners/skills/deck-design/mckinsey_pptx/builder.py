"""High-level builder + adaptive slide selector.

The user supplies a list of slide-spec dicts. Each spec has a `type`
(or none — in which case we auto-pick) plus payload. The builder
applies the matching template while keeping the McKinsey design intact.

Spec example:
    {"type": "executive_summary", "paragraphs": [...] }
    {"type": "column_chart", "categories": [...], "values": [...]}

If `type` is missing, `infer_slide_type` chooses based on the payload shape.
"""
from __future__ import annotations
from typing import Sequence, Optional, Dict, Any, Iterable, List

from .base import init_presentation
from .theme import Theme, DEFAULT_THEME
from .slides import (
    executive_summary, assessment_table, bubble_chart, column_chart,
    trends_slides, org_charts, timeline_slides, summary_slide,
    structure_slides, comparison_slides, extra_charts, process_extras,
)


# Routing table: type -> (callable, default kwargs override)
_REGISTRY = {
    # Executive summary
    "executive_summary": executive_summary.add_paragraph_summary,
    "executive_summary_paragraph": executive_summary.add_paragraph_summary,
    "executive_summary_takeaways": executive_summary.add_keytakeaway_summary,

    # Assessment
    "assessment_table": assessment_table.add_assessment_table,
    "status_overview": assessment_table.add_assessment_table,

    # Bubble / scatter
    "bubble_chart": bubble_chart.add_bubble_chart,
    "bubble_chart_takeaways": bubble_chart.add_bubble_chart_with_takeaways,
    "growth_share": bubble_chart.add_growth_share_matrix,
    "bcg_matrix": bubble_chart.add_growth_share_matrix,
    "prioritization_matrix": bubble_chart.add_prioritization_matrix,
    "assessment_matrix": bubble_chart.add_prioritization_matrix,

    # Column charts
    "column_comparison": column_chart.add_column_comparison,
    "column_simple_growth": column_chart.add_column_simple_growth,
    "column_split_growth": column_chart.add_column_split_growth,
    "column_historic_forecast": column_chart.add_column_historic_forecast,

    # Trends / areas
    "three_trends_icons": trends_slides.add_three_trends_icons,
    "three_trends_table": trends_slides.add_three_trends_table,
    "three_trends_numbered": trends_slides.add_three_trends_numbered,
    "five_key_areas": trends_slides.add_five_key_areas,

    # Org / team / hierarchy
    "issue_tree": org_charts.add_issue_tree,
    "org_chart": org_charts.add_org_chart,
    "project_team_circles": org_charts.add_project_team_circles,
    "team_chart": org_charts.add_team_chart,

    # Timeline / roadmap / process
    "phases_chevron_3": timeline_slides.add_phases_chevron_3,
    "phases_table_4": timeline_slides.add_phases_table_4,
    "waves_timeline_4": timeline_slides.add_waves_timeline_4,
    "gantt_timeline": timeline_slides.add_gantt_timeline,
    "overview_areas": timeline_slides.add_overview_areas,
    "process_activities": timeline_slides.add_process_activities,

    # Summary
    "dark_navy_summary": summary_slide.add_dark_navy_summary,

    # Structural slides
    "cover_slide": structure_slides.add_cover_slide,
    "cover": structure_slides.add_cover_slide,
    "section_divider": structure_slides.add_section_divider,
    "agenda": structure_slides.add_agenda,
    "stat_hero": structure_slides.add_stat_hero,
    "big_number": structure_slides.add_stat_hero,
    "quote_slide": structure_slides.add_quote_slide,
    "quote": structure_slides.add_quote_slide,

    # Comparison
    "comparison_table": comparison_slides.add_comparison_table,
    "option_compare": comparison_slides.add_comparison_table,
    "pros_cons": comparison_slides.add_pros_cons,
    "two_column_compare": comparison_slides.add_two_column_compare,
    "before_after": comparison_slides.add_two_column_compare,

    # Extra charts
    "stacked_column_chart": extra_charts.add_stacked_column_chart,
    "stacked_column": extra_charts.add_stacked_column_chart,
    "grouped_column_chart": extra_charts.add_grouped_column_chart,
    "grouped_column": extra_charts.add_grouped_column_chart,
    "line_chart": extra_charts.add_line_chart,

    # Process / metric overview
    "process_flow_horizontal": process_extras.add_process_flow_horizontal,
    "process_flow": process_extras.add_process_flow_horizontal,
    "funnel": process_extras.add_funnel,
    "kpi_dashboard": process_extras.add_kpi_dashboard,
}


def infer_slide_type(spec: Dict[str, Any]) -> str:
    """Adaptive picker — choose a template by what payload shape was supplied."""
    # Structural / single-purpose
    if "stat" in spec and "stat_label" in spec:
        return "stat_hero"
    if "quote" in spec and "author" in spec:
        return "quote_slide"
    if "section_number" in spec and "section_title" in spec:
        return "section_divider"
    if "client" in spec and "title" in spec and "items" not in spec:
        return "cover_slide"
    if "items" in spec and isinstance(spec.get("items"), list) \
            and spec["items"] and isinstance(spec["items"][0], str):
        return "agenda"

    # Comparison
    if "options" in spec and "criteria" in spec:
        return "comparison_table"
    if "pros" in spec and "cons" in spec:
        return "pros_cons"
    if "left_items" in spec and "right_items" in spec:
        return "two_column_compare"

    # KPIs / funnels / process flow
    if "kpis" in spec:
        return "kpi_dashboard"
    if "stages" in spec:
        return "funnel"

    # Extra charts (series-shaped data)
    if "series" in spec and "categories" in spec:
        first = spec["series"][0] if spec["series"] else {}
        if spec.get("chart") == "line" or "values" in first \
                and spec.get("kind") == "line":
            return "line_chart"
        if spec.get("chart") == "stacked":
            return "stacked_column_chart"
        if spec.get("chart") == "grouped":
            return "grouped_column_chart"
        # default for series + categories: stacked
        return "stacked_column_chart"

    if "body" in spec and len(spec) <= 4:
        return "dark_navy_summary"
    if "paragraphs" in spec and "sections" not in spec:
        return "executive_summary_paragraph"
    if "sections" in spec:
        return "executive_summary_takeaways"
    if "categories" in spec and isinstance(spec["categories"], list) \
            and spec["categories"] and isinstance(spec["categories"][0], dict) \
            and "rows" in spec["categories"][0]:
        return "assessment_table"
    if "main_drivers" in spec:
        return "issue_tree"
    if "branches" in spec:
        return "org_chart"
    if "leader" in spec and "members" in spec:
        return "project_team_circles"
    if "functions" in spec:
        return "team_chart"
    if "weeks" in spec and "workstreams" in spec:
        return "gantt_timeline"
    if "waves" in spec:
        return "waves_timeline_4"
    if "phases" in spec:
        first = spec["phases"][0] if spec["phases"] else {}
        if "outcomes" in first or "activities" in first:
            return "phases_table_4"
        return "phases_chevron_3"
    if "steps" in spec:
        return "process_activities"
    if "areas" in spec:
        first = spec["areas"][0] if spec["areas"] else {}
        if "bullets" in first:
            return "overview_areas"
        return "five_key_areas"
    if "trends" in spec:
        first = spec["trends"][0] if spec["trends"] else {}
        if "examples" in first:
            return "three_trends_table"
        if spec.get("numbered"):
            return "three_trends_numbered"
        return "three_trends_icons"
    if "bus" in spec:
        return "growth_share"
    if "items" in spec and spec["items"] and "x_band" in spec["items"][0]:
        return "prioritization_matrix"
    if "bubbles" in spec:
        return ("bubble_chart_takeaways" if spec.get("takeaways")
                else "bubble_chart")
    if "values" in spec and "categories" in spec:
        if "forecast_from_index" in spec:
            return "column_historic_forecast"
        if "split_index" in spec:
            return "column_split_growth"
        if spec.get("growth_pct"):
            return "column_simple_growth"
        return "column_comparison"
    raise ValueError(f"Cannot infer slide type from spec keys: {list(spec.keys())}")


class PresentationBuilder:
    """Compose a full deck of McKinsey-style slides."""

    def __init__(self, theme: Theme = DEFAULT_THEME, *,
                 auto_page_numbers: bool = True,
                 default_section_marker: Optional[str] = None):
        self.theme = theme
        self.auto_page_numbers = auto_page_numbers
        self.default_section_marker = default_section_marker
        self.prs = init_presentation(theme)
        self._page = 0

    # Direct add by type
    def add(self, slide_type: str, **kwargs):
        fn = _REGISTRY.get(slide_type)
        if fn is None:
            raise ValueError(f"Unknown slide type: {slide_type}. "
                             f"Available: {sorted(_REGISTRY)}")
        if self.auto_page_numbers:
            self._page += 1
            kwargs.setdefault("page_number", self._page)
        if (self.default_section_marker is not None
                and "section_marker" not in kwargs):
            kwargs["section_marker"] = self.default_section_marker
        kwargs.setdefault("theme", self.theme)
        return fn(self.prs, **kwargs)

    # Adaptive add (type optional)
    def add_spec(self, spec: Dict[str, Any]):
        spec = dict(spec)  # copy
        slide_type = spec.pop("type", None) or infer_slide_type(spec)
        return self.add(slide_type, **spec)

    def add_specs(self, specs: Iterable[Dict[str, Any]]):
        return [self.add_spec(s) for s in specs]

    def save(self, path: str):
        self.prs.save(path)
        return path


def build_from_spec(specs: Sequence[Dict[str, Any]], output_path: str, *,
                    theme: Theme = DEFAULT_THEME,
                    auto_page_numbers: bool = True,
                    default_section_marker: Optional[str] = None) -> str:
    """Convenience function: spec list in, .pptx out."""
    b = PresentationBuilder(theme=theme,
                            auto_page_numbers=auto_page_numbers,
                            default_section_marker=default_section_marker)
    b.add_specs(specs)
    return b.save(output_path)
