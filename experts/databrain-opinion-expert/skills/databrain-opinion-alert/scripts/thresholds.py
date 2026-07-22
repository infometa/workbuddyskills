#!/usr/bin/env python3
"""
thresholds.py — 加载 thresholds.yaml + 按 game_id 深合并 overrides。

仅做配置加载与合并，不涉及任何取数 / 告警判定逻辑。

用法（CLI 调试）：
    python scripts/thresholds.py --game_id e7f672beaa5fddd166df98bc046ba4bd4 \
                                 --channel steam --scope all_reviews

调用方典型用法：
    from thresholds import (
        load_thresholds, get_channel_thresholds,
        get_silence_seconds, get_slicing_config,
    )
    merged = load_thresholds("thresholds.yaml", game_id="...")
    levels = get_channel_thresholds(merged, channel="steam", scope="all_reviews")
    # → {"P0": {"absolute_pp": 60, ...}, "P1": {...}, "P2": {...}}
    sl = get_slicing_config(merged, channel="steam")
    # → {"enabled": True, "exclude": [...], "language_priority": ["EN", ...], ...}
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LEVELS = ("P0", "P1", "P2")

# 各 channel 必须存在的字段；缺失时温和告警 + 该维度跳过（不抛异常）
_REQUIRED_TOP_KEYS = ("defaults", "silence_seconds", "slicing")

# 各 (channel, level) 至少包含的字段（任一即可，并不要求全有；只要 baseline 有就允许该等级）
# 这里只做最小保证：必须能算出"是否触发"，否则该等级形同虚设
_LEVEL_MIN_FIELDS = ("baseline", "min_sample")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def load_thresholds(yaml_path: str | Path, game_id: str = "") -> dict:
    """
    加载 yaml + 应用 overrides[game_id] 深合并。

    [Why] 温和校验：缺关键字段不抛异常，仅在 stderr 输出 [WARN]，运行期再按维度跳过。
    这样即便 yaml 配置不全也能尽量评估出可用维度，避免单个字段拼写错误导致整个告警失效。
    """
    path = Path(yaml_path)
    if not path.is_file():
        raise FileNotFoundError(f"thresholds.yaml not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    for k in _REQUIRED_TOP_KEYS:
        if k not in raw:
            print(f"[WARN] thresholds.yaml 缺少顶层键 '{k}'，相关维度将被跳过", file=sys.stderr)

    merged = copy.deepcopy(raw)
    overrides = (raw.get("overrides") or {}).get(game_id) if game_id else None
    if overrides:
        merged["defaults"] = _deep_merge(merged.get("defaults", {}), overrides)

    _validate_levels(merged.get("defaults", {}))
    return merged


def get_channel_thresholds(
    merged: dict, channel: str, scope: str | None = None
) -> dict[str, dict]:
    """
    取指定渠道（+ Steam scope）的 P0/P1/P2 三档阈值。

    channel: steam / google_play / app_store
    scope:   仅 channel='steam' 时必填，all_reviews / recent_reviews
    """
    defaults = merged.get("defaults", {})
    node = defaults.get(channel)
    if node is None:
        raise KeyError(f"defaults 中缺少渠道 '{channel}'")

    if channel == "steam":
        if not scope:
            raise ValueError("channel='steam' 必须指定 scope=all_reviews 或 recent_reviews")
        node = node.get(scope)
        if node is None:
            raise KeyError(f"defaults.steam 中缺少 scope '{scope}'")

    return {lvl: dict(node.get(lvl) or {}) for lvl in LEVELS}


def get_silence_seconds(merged: dict, level: str) -> int:
    """取静默期秒数；缺失时返回 0（视为不静默）。"""
    cfg = merged.get("silence_seconds") or {}
    val = cfg.get(level)
    if val is None:
        print(f"[WARN] silence_seconds 缺少 '{level}'，默认返回 0", file=sys.stderr)
        return 0
    return int(val)


def get_slicing_config(merged: dict, channel: str) -> dict:
    """
    取该渠道的切片评估配置。

    返回：
      enabled  是否启用切片评估（False 时仅评估全球聚合）
      exclude  排除清单（Steam: 语种代码/key；GP/App Store: area 值）
      language_priority/custom_languages/include_unlisted_languages 仅 Steam 使用

    Steam 必须按语言切片：全球聚合 + 官方支持语种优先 + 自定义语种 + 其余语种。
    """
    cfg = (merged.get("slicing") or {}).get(channel) or {}
    if channel == "steam":
        return {
            "enabled": bool(cfg.get("by_language", True)),
            "exclude": list(cfg.get("exclude_languages") or []),
            "language_priority": list(cfg.get("language_priority") or []),
            "custom_languages": list(cfg.get("custom_languages") or []),
            "include_unlisted_languages": bool(cfg.get("include_unlisted_languages", True)),
        }
    return {
        "enabled": bool(cfg.get("by_country", True)),
        "exclude": list(cfg.get("exclude_areas") or []),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并 dict：override 中的值覆盖 base 同 key；非 dict 直接替换。"""
    if not isinstance(base, dict) or not isinstance(override, dict):
        return copy.deepcopy(override)
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _validate_levels(defaults: dict) -> None:
    """
    遍历 defaults.<channel>.[scope.]<level>，对每个 level 做最小字段校验。
    [Why] 缺 baseline / min_sample 这两个字段会让该等级"永远不触发"或"永远触发"，
    必须告警出来；其余字段（如 absolute_pp / drop_xx）按维度配置即可。
    """
    for channel, node in (defaults or {}).items():
        if not isinstance(node, dict):
            continue
        if channel == "steam":
            for scope, scope_node in node.items():
                _validate_scope_levels(f"steam.{scope}", scope_node or {})
        else:
            _validate_scope_levels(channel, node)


def _validate_scope_levels(scope_label: str, scope_node: dict) -> None:
    for lvl in LEVELS:
        cfg = scope_node.get(lvl)
        if cfg is None:
            print(f"[WARN] {scope_label}.{lvl} 配置缺失", file=sys.stderr)
            continue
        for f in _LEVEL_MIN_FIELDS:
            if f not in cfg:
                print(f"[WARN] {scope_label}.{lvl} 缺字段 '{f}'，该等级判定可能失效",
                      file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI（调试用）
# ---------------------------------------------------------------------------
def _default_yaml_path() -> Path:
    return Path(__file__).resolve().parent.parent / "thresholds.yaml"


def _self_test() -> int:
    """smoke test：yaml 加载 / deep merge / 必填字段 / silence 解析。"""
    import tempfile
    failures: list[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            failures.append(name)

    print("=== thresholds self test ===")

    base = load_thresholds(str(_default_yaml_path()), game_id="")
    _check("加载默认 yaml 不报错", isinstance(base, dict) and "defaults" in base)

    gp_p0 = get_channel_thresholds(base, "google_play", None).get("P0", {})
    _check("GP P0 含 absolute_score", "absolute_score" in gp_p0,
           f"got keys={list(gp_p0)}")

    steam_p0 = get_channel_thresholds(base, "steam", "all_reviews").get("P0", {})
    _check("Steam all_reviews P0 含 absolute_pp", "absolute_pp" in steam_p0,
           f"got keys={list(steam_p0)}")

    sl = get_slicing_config(base, "google_play")
    _check("slicing 转换出 enabled/exclude", "enabled" in sl and "exclude" in sl, f"{sl}")
    sl_steam = get_slicing_config(base, "steam")
    _check("Steam slicing 含官方语种优先级", "EN" in sl_steam.get("language_priority", []), f"{sl_steam}")

    s_p0 = get_silence_seconds(base, "P0")
    _check("silence_seconds.P0 是正整数", isinstance(s_p0, int) and s_p0 > 0, f"{s_p0}")

    yaml_text = """
slicing:
  steam:
    by_language: true
    language_priority: [EN, JA, KO, ZH-CN, DE, FR, RU, ES, PT-BR]
    custom_languages: []
    include_unlisted_languages: true
    exclude_languages: []
  google_play:  { by_country:  true, exclude_areas: [] }
  app_store:    { by_country:  true, exclude_areas: [] }
silence_seconds: { P0: 100, P1: 200, P2: 300 }
defaults:
  steam:
    all_reviews:
      P0: { absolute_pp: 60, baseline: p5, min_sample: 100 }
      P1: { absolute_pp: 75, baseline: p25, min_sample: 50 }
      P2: { absolute_pp: 80, baseline: median_7d, min_sample: 20 }
    recent_reviews:
      P0: { absolute_pp: 65, baseline: p5, min_sample: 80 }
      P1: { absolute_pp: 80, baseline: p25, min_sample: 40 }
      P2: { absolute_pp: 85, baseline: median_7d, min_sample: 20 }
  google_play:
    P0: { absolute_score: 3.0, baseline: p5, min_sample: 200 }
    P1: { absolute_score: 3.5, baseline: p25, min_sample: 100 }
    P2: { absolute_score: 4.0, baseline: median_7d, min_sample: 50 }
  app_store:
    P0: { absolute_score: 3.0, baseline: p5, min_sample: 100 }
    P1: { absolute_score: 3.5, baseline: p25, min_sample: 50 }
    P2: { absolute_score: 4.0, baseline: median_7d, min_sample: 20 }
overrides:
  efeedface:
    steam:
      all_reviews:
        P0: { absolute_pp: 55 }
"""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
        tf.write(yaml_text)
        tmp_path = tf.name
    try:
        merged = load_thresholds(tmp_path, game_id="efeedface")
        p0 = get_channel_thresholds(merged, "steam", "all_reviews")["P0"]
        _check("深合并：override 字段被替换", p0["absolute_pp"] == 55, f"got {p0}")
        _check("深合并：未覆盖字段保留 baseline=p5", p0.get("baseline") == "p5", f"got {p0}")
        _check("深合并：未覆盖字段保留 min_sample=100", p0.get("min_sample") == 100, f"got {p0}")
        p1 = get_channel_thresholds(merged, "steam", "all_reviews")["P1"]
        _check("深合并：未覆盖等级保持原值", p1["absolute_pp"] == 75, f"got {p1}")
        merged2 = load_thresholds(tmp_path, game_id="other")
        p0b = get_channel_thresholds(merged2, "steam", "all_reviews")["P0"]
        _check("无 override 时 game_id 不影响 defaults",
               p0b["absolute_pp"] == 60, f"got {p0b}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    try:
        get_channel_thresholds(base, "steam", None)
        failures.append("steam 缺 scope 没报错")
        print("  ❌ steam 缺 scope 应报错但没报")
    except (ValueError, KeyError):
        print("  ✅ steam 缺 scope 报错")

    print("\n" + "-" * 40)
    print(f"FAIL: {len(failures)}" if failures else f"PASS: {12 - len(failures)} thresholds tests")
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="加载 thresholds.yaml 并打印合并后的结果")
    parser.add_argument("--game_id", default="", help="按此 game_id 应用 overrides")
    parser.add_argument("--channel", choices=["steam", "google_play", "app_store"],
                        help="只看指定渠道的阈值")
    parser.add_argument("--scope", choices=["all_reviews", "recent_reviews"],
                        help="仅 channel=steam 时必填")
    parser.add_argument("--config", default=str(_default_yaml_path()),
                        help="thresholds.yaml 路径")
    parser.add_argument("--self_test", action="store_true", help="跑内置 smoke test")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    merged = load_thresholds(args.config, args.game_id)

    if args.channel:
        scope = args.scope if args.channel == "steam" else None
        if args.channel == "steam" and not scope:
            print("[ERROR] --channel steam 必须同时指定 --scope", file=sys.stderr)
            sys.exit(1)
        out = {
            "channel": args.channel,
            "scope": scope,
            "thresholds": get_channel_thresholds(merged, args.channel, scope),
            "slicing": get_slicing_config(merged, args.channel),
            "silence_seconds": {lvl: get_silence_seconds(merged, lvl) for lvl in LEVELS},
        }
    else:
        out = merged

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
