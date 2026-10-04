#!/usr/bin/env python3
"""Small Draft 2020-12 subset validator using only the Python standard library."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_instance(value: Any, schema: dict, label: str = "value") -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        choices = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, item) for item in choices):
            return [f"{label}: expected type {choices}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{label}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label}: invalid enum {value!r}")
    if isinstance(value, str):
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(f"{label}: pattern mismatch")
        if len(value) < int(schema.get("minLength", 0)):
            errors.append(f"{label}: shorter than minLength")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            errors.append(f"{label}: longer than maxLength")
        if schema.get("format") == "date-time" and value:
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{label}: invalid date-time")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{label}: below minimum")
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            errors.append(f"{label}: fewer than minItems")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{label}: array items are not unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_instance(item, item_schema, f"{label}[{index}]"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                errors.append(f"{label}: missing required field {field}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                errors.append(f"{label}: unknown fields {extra}")
        additional_schema = schema.get("additionalProperties") if isinstance(schema.get("additionalProperties"), dict) else None
        for field, item in value.items():
            field_schema = properties.get(field, additional_schema)
            if field_schema:
                errors.extend(validate_instance(item, field_schema, f"{label}.{field}"))
    return errors


def csv_row_to_instance(row: dict[str, str], schema: dict, label: str) -> tuple[dict[str, Any], list[str]]:
    instance: dict[str, Any] = {}
    errors: list[str] = []
    for field, spec in schema.get("properties", {}).items():
        raw = row.get(field, "")
        if spec.get("x-csvEncoding") == "json-array":
            if not raw:
                instance[field] = []
            else:
                try:
                    parsed = json.loads(raw)
                    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                        raise ValueError("not a string array")
                    instance[field] = raw
                except Exception as exc:
                    errors.append(f"{label}.{field}: invalid JSON string array: {exc}")
                    instance[field] = raw
        else:
            instance[field] = raw
    return instance, errors
