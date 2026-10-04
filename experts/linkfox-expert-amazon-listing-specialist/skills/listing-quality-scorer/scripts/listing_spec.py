#!/usr/bin/env python3
"""listing_spec — 双层规格模型的公共实现。

Layer A（platform）：亚马逊平台真实硬限制，任何 spec 都不能放宽，超出即阻断。
Layer B（authoring）：写作规格（字符区间/条数/结构），脚本内置常量只是缺省值，
用户 spec（--spec spec.json）可在平台底线内自由覆盖。

所有 saver 校验脚本共用本模块：
    from listing_spec import extract_spec_arg, load_spec, resolve_limit, tag

用法（saver 侧）：
    argv, spec = extract_spec_arg(sys.argv[1:])          # 剥离 --spec，其余参数不变
    limit, layer = resolve_limit(spec, "title", "max", default=75)
    # layer ∈ {"user_spec", "default"}；错误信息用 tag(layer) 前缀标注来源

spec.json 结构（全部可选，缺省即为脚本原有行为）：
{
  "title":           {"max": 190, "min": 0},
  "item_highlights": {"max": 125, "enabled": true},
  "bullets":         {"count": 5, "each_max": 400, "each_min": 200,
                       "total_max": 2000, "total_min": 0},
  "description":     {"max": 2500, "min": 1000},
  "search_terms":    {"bytes_max": 250}
}

原则：本模块只提供限值解析，永不修改文案；spec 超出平台底线在加载时即报错
（layer=platform），不允许带病执行。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Layer A：平台真实硬限制（不可被 spec 放宽）。
# 依据：Amazon 商品页真实截断/抑制阈值与后台字段上限，非本产品最佳实践。
# ---------------------------------------------------------------------------
PLATFORM_LIMITS: dict[str, dict[str, int]] = {
    "title": {"max": 200},                # >200 字符 Amazon 抑制展示
    "item_highlights": {"max": 500},      # 后台字段宽限；产品默认 125 是 Layer B
    "bullets": {"each_max": 500, "total_max": 2500, "count_max": 10, "count_min": 1},
    "description": {"max": 2000},         # 普通描述字段上限（A+ 另计）
    "search_terms": {"bytes_max": 250},   # 超限整个字段不被索引
}

# Layer B：产品缺省值（与历史脚本常量一致，保证不传 spec 时零回归）。
DEFAULTS: dict[str, dict[str, int]] = {
    "title": {"max": 75},
    "item_highlights": {"max": 125},
    "bullets": {"count": 5, "each_max": 255, "each_min": 0, "total_max": 1275, "total_min": 0},
    "description": {"max": 1000, "min": 0},
    "search_terms": {"bytes_max": 250},
}

_MIN_KEYS = {"min", "each_min", "total_min", "count_min"}


def tag(layer: str) -> str:
    """错误信息前缀，让重写方/用户分清「平台不让」与「你自己设的」。"""
    return {"platform": "[平台硬限制]", "user_spec": "[用户规格]", "default": "[默认规格]"}.get(layer, f"[{layer}]")


def _platform_cap(field: str, key: str) -> int | None:
    caps = PLATFORM_LIMITS.get(field) or {}
    if key in caps:
        return caps[key]
    # min 类键没有平台上界约束
    return None


def validate_spec(spec: dict[str, Any]) -> list[str]:
    """校验用户 spec 不越过平台底线；返回错误列表（layer=platform）。"""
    errors: list[str] = []
    if not isinstance(spec, dict):
        return [f"{tag('platform')} spec 顶层必须是 JSON 对象"]
    for field, rules in spec.items():
        if not isinstance(rules, dict):
            continue
        for key, value in rules.items():
            if isinstance(value, bool) or not isinstance(value, int):
                continue
            if key in _MIN_KEYS:
                continue
            cap = _platform_cap(field, key)
            if cap is not None and value > cap:
                errors.append(
                    f"{tag('platform')} spec.{field}.{key}={value} 超出平台硬限制 {cap}，"
                    f"平台底线不可放宽"
                )
            if key == "count":
                cmin = PLATFORM_LIMITS["bullets"]["count_min"]
                cmax = PLATFORM_LIMITS["bullets"]["count_max"]
                if not (cmin <= value <= cmax):
                    errors.append(
                        f"{tag('platform')} spec.bullets.count={value} 必须在 [{cmin}, {cmax}] 内"
                    )
    return errors


def load_spec(path: str) -> dict[str, Any]:
    """读取并校验 spec 文件；平台越线直接抛 SystemExit(2)。"""
    if not os.path.isfile(path):
        print(f"{tag('platform')} spec 文件不存在: {path}", file=sys.stderr)
        raise SystemExit(2)
    try:
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"{tag('platform')} spec 不是合法 JSON: {exc}", file=sys.stderr)
        raise SystemExit(2)
    errors = validate_spec(spec)
    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        raise SystemExit(2)
    return spec


def extract_spec_arg(argv: list[str]) -> tuple[list[str], dict[str, Any] | None]:
    """从 argv 中剥离 --spec <path> / --spec=<path>，返回 (剩余 argv, spec|None)。

    额外支持环境变量 LISTING_SPEC_PATH（编排层透传时不必改每条命令行）。
    """
    remaining: list[str] = []
    spec_path: str | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--spec":
            if i + 1 >= len(argv):
                print(f"{tag('platform')} --spec 缺少路径参数", file=sys.stderr)
                raise SystemExit(2)
            spec_path = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--spec="):
            spec_path = arg.split("=", 1)[1]
            i += 1
            continue
        remaining.append(arg)
        i += 1
    if spec_path is None:
        spec_path = os.environ.get("LISTING_SPEC_PATH") or None
    return remaining, (load_spec(spec_path) if spec_path else None)


def resolve_limit(
    spec: dict[str, Any] | None,
    field: str,
    key: str,
    default: int | None = None,
) -> tuple[int | None, str]:
    """解析某字段某限值：用户 spec 优先，否则缺省值。返回 (值, layer)。

    返回的 layer 用于错误标注：user_spec / default。
    值为 None 表示该项不校验。
    """
    if spec and isinstance(spec.get(field), dict) and key in spec[field]:
        value = spec[field][key]
        if isinstance(value, int) and not isinstance(value, bool):
            return value, "user_spec"
    if default is not None:
        return default, "default"
    fallback = DEFAULTS.get(field, {}).get(key)
    return fallback, "default"


def field_enabled(spec: dict[str, Any] | None, field: str) -> bool:
    """字段是否启用（如用户流程不要 item_highlights）。缺省启用。"""
    if spec and isinstance(spec.get(field), dict):
        enabled = spec[field].get("enabled")
        if enabled is False:
            return False
        # max=0 等价于禁用
        if spec[field].get("max") == 0:
            return False
    return True


def check_range(
    value_len: int,
    *,
    field: str,
    label: str,
    spec: dict[str, Any] | None,
    max_key: str,
    min_key: str | None = None,
    default_max: int | None = None,
    default_min: int | None = None,
) -> list[str]:
    """通用区间校验，返回带 layer 标注的错误列表（不修改任何内容）。"""
    errors: list[str] = []
    max_v, max_layer = resolve_limit(spec, field, max_key, default_max)
    if max_v is not None and value_len > max_v:
        errors.append(f"{tag(max_layer)} {label} 超长：{value_len} > {max_v}")
    # 平台底线独立再验一次（防止 default 被外部改大）
    cap = _platform_cap(field, max_key)
    if cap is not None and value_len > cap:
        msg = f"{tag('platform')} {label} 超出平台硬限制：{value_len} > {cap}"
        if msg not in errors:
            errors.append(msg)
    if min_key:
        min_v, min_layer = resolve_limit(spec, field, min_key, default_min)
        if min_v not in (None, 0) and value_len < min_v:
            errors.append(f"{tag(min_layer)} {label} 低于下限：{value_len} < {min_v}")
    return errors
