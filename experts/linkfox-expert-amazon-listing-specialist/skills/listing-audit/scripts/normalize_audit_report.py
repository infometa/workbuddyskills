#!/usr/bin/env python3
"""Normalize and validate a semantic listing audit before it becomes an artifact.

The audit model is allowed to explain findings, but the Audit -> Core interface is
not free-form.  This module converts the small legacy variants that have existed in
production into the canonical ``listingAuditHandoff`` shape, resolves evidence paths,
and fails closed when the rewrite cannot be reproduced from real local artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_KIND = "listingAuditReport"
HANDOFF_KIND = "listingAuditHandoff"
REWRITE_FIELDS = {
    "title", "item_highlights", "bullets", "description", "search_terms",
    "structured_attributes", "subject_matter",
}
GLOBAL_REWRITE_GUARDS = (
    "只使用 source_listing_path 与 evidence_paths 中可追溯的本品事实，不得从评论、竞品或示例补造规格、时长、认证、安全或效果声明",
    "改写并生成后台字段后必须重新扫描 title、item_highlights、bullets、description、search_terms、subject_matter；存在 block 不得交付",
)
SEARCH_TERM_GUARD = (
    "只使用与本品事实一致的通用相关词；禁止自有或他牌品牌名、ASIN、无关词及与适用年龄冲突的词"
)
EVIDENCE_ALIASES = {
    "compliance_report": "compliance",
    "normalized_listing": "normalized_listing",
    "sif_keywords": "sif_keywords",
}


def _required_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _target(report: dict[str, Any], handoff: dict[str, Any]) -> dict[str, str]:
    outer = _required_dict(report.get("target"), "target")
    inner = handoff.get("target") if isinstance(handoff.get("target"), dict) else {}
    asin = str(inner.get("asin") or handoff.get("target_asin") or outer.get("asin") or "").strip().upper()
    marketplace = str(
        inner.get("marketplace") or handoff.get("marketplace") or outer.get("marketplace") or ""
    ).strip().upper()
    if not asin or not marketplace:
        raise ValueError("audit handoff requires target.asin and target.marketplace")
    if outer.get("asin") and str(outer["asin"]).strip().upper() != asin:
        raise ValueError("audit target ASIN does not match handoff target")
    if outer.get("marketplace") and str(outer["marketplace"]).strip().upper() != marketplace:
        raise ValueError("audit target marketplace does not match handoff target")
    return {"asin": asin, "marketplace": marketplace}


def _absolute_existing_path(value: Any, workspace_root: Path, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    path = Path(text)
    if not path.is_absolute():
        path = workspace_root / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")
    return str(path)


def _evidence_paths(
    handoff: dict[str, Any], workspace_root: Path,
) -> tuple[dict[str, str], str]:
    raw = handoff.get("evidence_paths") or {}
    if not isinstance(raw, dict):
        raise ValueError("auditHandoff.evidence_paths must be an object")
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        canonical_key = EVIDENCE_ALIASES.get(str(key), str(key))
        resolved = _absolute_existing_path(value, workspace_root, f"evidence_paths.{key}")
        if resolved:
            normalized[canonical_key] = resolved
    source = _absolute_existing_path(
        handoff.get("source_listing_path") or normalized.get("normalized_listing"),
        workspace_root,
        "source_listing_path",
    )
    if not source:
        raise ValueError("audit handoff requires an existing source_listing_path")
    normalized.setdefault("normalized_listing", source)
    return normalized, source


def _actions(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    raw = handoff.get("field_actions")
    if not isinstance(raw, list) or not raw:
        raise ValueError("auditHandoff.field_actions must be a non-empty array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"field_actions[{index}] must be an object")
        field = str(item.get("field") or "").strip()
        if field not in REWRITE_FIELDS:
            raise ValueError(f"invalid field_actions[{index}].field: {field!r}")
        if field in seen:
            raise ValueError(f"duplicate field action: {field}")
        seen.add(field)
        constraints = [str(value).strip() for value in item.get("constraints") or [] if str(value).strip()]
        for guard in GLOBAL_REWRITE_GUARDS:
            if guard not in constraints:
                constraints.append(guard)
        if field in {"search_terms", "subject_matter"} and SEARCH_TERM_GUARD not in constraints:
            constraints.append(SEARCH_TERM_GUARD)
        result.append({
            "field": field,
            "priority": str(item.get("priority") or "medium"),
            "problem": str(item.get("problem") or item.get("reason") or "").strip(),
            "evidence": list(item.get("evidence") or []),
            "objective": str(item.get("objective") or item.get("expected_direction") or "").strip(),
            "constraints": constraints,
            "expected_direction": str(item.get("expected_direction") or "").strip(),
            "confidence": str(item.get("confidence") or "partial"),
        })
    return result


def normalize_report(payload: Any, workspace_root: str | os.PathLike[str]) -> dict[str, Any]:
    report = _required_dict(payload, "report")
    if report.get("kind") != REPORT_KIND or report.get("schema_version") != 2:
        raise ValueError("report must be listingAuditReport schema_version=2")
    raw_handoff = _required_dict(report.get("auditHandoff"), "auditHandoff")
    root = Path(workspace_root).resolve()
    target = _target(report, raw_handoff)
    evidence_paths, source_listing_path = _evidence_paths(raw_handoff, root)
    actions = _actions(raw_handoff)
    locked = raw_handoff.get("locked_fields") or []
    if not isinstance(locked, list) or any(field not in REWRITE_FIELDS for field in locked):
        raise ValueError("auditHandoff.locked_fields contains an invalid field")
    if set(locked) & {action["field"] for action in actions}:
        raise ValueError("a field cannot be both locked and targeted for rewrite")

    freshness = raw_handoff.get("data_freshness") or {}
    if not isinstance(freshness, dict):
        raise ValueError("auditHandoff.data_freshness must be an object")
    freshness = {
        "captured_at": str(freshness.get("captured_at") or datetime.now(timezone.utc).isoformat()),
        "cache_window_hours": freshness.get("cache_window_hours", 24),
    }
    report = dict(report)
    report["target"] = target
    report["auditHandoff"] = {
        "kind": HANDOFF_KIND,
        "schema_version": 1,
        "target": target,
        "source_listing_path": source_listing_path,
        "evidence_paths": evidence_paths,
        "score_panel_path": _absolute_existing_path(
            raw_handoff.get("score_panel_path") or evidence_paths.get("score_result"),
            root,
            "score_panel_path",
        ),
        "field_actions": actions,
        "operational_actions": list(raw_handoff.get("operational_actions") or []),
        "locked_fields": list(locked),
        "data_freshness": freshness,
    }
    report["rewrite_ready"] = True
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and validate listingAuditReport")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--workspace-root", default=os.getcwd())
    args = parser.parse_args()
    payload = json.loads(args.source.read_text(encoding="utf-8"))
    report = normalize_report(payload, args.workspace_root)
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"JSON artifact: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
