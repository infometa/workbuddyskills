#!/usr/bin/env python3
"""Check a service-provided normalized lead-field contract without changing data."""
import argparse
import json
import sys

TYPES = {"text", "long_text", "number", "checkbox", "person",
         "datetime", "single_select", "multi_select"}


def fields_by_name(values, label):
    if not isinstance(values, list):
        raise ValueError(label + " must be an array")
    result = {}
    for value in values:
        if not isinstance(value, dict):
            raise ValueError(label + " contains a non-object")
        name, kind = value.get("name"), value.get("type")
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            raise ValueError(label + " contains an invalid field name")
        if name in result or kind not in TYPES:
            raise ValueError(label + " contains a duplicate field or invalid type: " + name)
        if kind in ("single_select", "multi_select"):
            options = value.get("options")
            if not isinstance(options, list) or not all(isinstance(o, str) for o in options):
                raise ValueError(name + " requires string options")
            if len(options) != len(set(options)):
                raise ValueError(name + " has duplicate options")
        result[name] = dict(value)
    return result


def plan(payload):
    if not isinstance(payload, dict) or set(payload) != {"expected_fields", "fields"}:
        raise ValueError("expected_fields and fields are required")
    expected = fields_by_name(payload["expected_fields"], "expected_fields")
    live = fields_by_name(payload["fields"], "fields")
    primary = [f for f in expected.values() if f.get("primary") is True]
    if len(primary) != 1 or primary[0]["type"] != "text":
        raise ValueError("approved contract must contain exactly one text primary field")
    primary_name = primary[0]["name"]
    missing, incompatible = [], []
    for name, spec in expected.items():
        actual = live.get(name)
        if actual is None:
            missing.append(spec)
        elif actual["type"] != spec["type"]:
            incompatible.append({"name": name, "reason": "type_mismatch",
                                 "expected_type": spec["type"], "actual_type": actual["type"]})
        elif spec["type"] in ("single_select", "multi_select"):
            absent = [o for o in spec["options"] if o not in actual["options"]]
            if absent:
                incompatible.append({"name": name, "reason": "missing_options",
                                     "missing_options": absent})
    live_primary = [f for f in live.values() if f.get("primary") is True]
    primary_ok = (primary_name in live and live[primary_name]["type"] == "text"
                  and live[primary_name].get("primary") is True and len(live_primary) == 1)
    return {"ok": not missing and not incompatible and primary_ok,
            "primary_field": primary_name, "primary_field_ok": primary_ok,
            "missing_fields": missing,
            "add_plan": [] if incompatible or not primary_ok else missing,
            "incompatible_fields": incompatible,
            "requires_manual_resolution": bool(incompatible or not primary_ok),
            "reconciliation_policy": "add_only"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan"])
    parser.parse_args()
    try:
        result = plan(json.load(sys.stdin))
    except (ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
