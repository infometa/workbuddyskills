#!/usr/bin/env python3
"""
alert_state.py — 静默期状态管理（JSON 文件持久化）。

设计要点
========
1. 状态 key 格式：``{game_id}:{channel}:{scope}:{slice_key}``
   - scope 仅对 steam 有意义（all_reviews / recent_reviews）；其他渠道用 "_" 占位
   - slice_key 全局用 "__global__"，切片用 "lang_<语种>" / "country_<area>"
2. 升级判定：当前等级序号 < 上次（P0=0/P1=1/P2=2/OK=99）→ 立刻打破静默
3. 降级判定：当前等级序号 > 上次 + 还在静默期 → 不重复推（更弱告警）
4. 同级判定：序号相等 + 静默期内 → 不重复
5. 静默到期：时间差 ≥ silence_seconds → 重新触发
6. clear_state(state, key)：当前 OK 时调用，删掉历史记录，下次再触发视为首次

CLI（自带 smoke test）
======================
    python scripts/alert_state.py --self_test
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LEVEL_RANK = {"P0": 0, "P1": 1, "P2": 2, "OK": 99}
DEFAULT_STATE_PATH = "/tmp/databrain_alert_state.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def make_key(game_id: str, channel: str, scope: Optional[str], slice_key: str) -> str:
    """组装状态 key，scope 为空时用 '_' 占位。"""
    return f"{game_id}:{channel}:{scope or '_'}:{slice_key}"


def load_state(path: str | Path = DEFAULT_STATE_PATH) -> dict:
    """加载状态文件；不存在或损坏时返回空 dict。"""
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        # [Why] 状态文件损坏不应阻塞告警；视作空状态，下次自动重建
        print(f"[WARN] state file 损坏，重置为空：{p}", file=sys.stderr)
        return {}


def save_state(path: str | Path, state: dict) -> None:
    """原子写入（先写临时文件再 rename，避免半写状态）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp.replace(p)


def should_trigger(
    state: dict,
    key: str,
    level: str,
    now: datetime,
    silence_seconds: int,
) -> tuple[bool, str]:
    """
    判定是否应触发告警。

    返回 (should: bool, reason: str)：
      reason 取值：first_trigger / upgraded_from_<lvl> / silence_expired /
                   silenced_until_<iso> / downgrade_silenced
    """
    if level == "OK":
        return False, "level_is_ok"

    rec = state.get(key)
    if rec is None:
        return True, "first_trigger"

    last_level = rec.get("last_level", "OK")
    silence_until = _parse_dt(rec.get("silence_until"))

    cur_rank = LEVEL_RANK.get(level, 99)
    last_rank = LEVEL_RANK.get(last_level, 99)

    if cur_rank < last_rank:
        return True, f"upgraded_from_{last_level}"

    if silence_until is None or now >= silence_until:
        return True, "silence_expired"

    if cur_rank > last_rank:
        return False, "downgrade_silenced"

    return False, f"silenced_until_{silence_until.isoformat()}"


def record_trigger(
    state: dict,
    key: str,
    level: str,
    silence_seconds: int,
    now: datetime,
) -> None:
    """将本次触发写入状态字典（不落盘）。"""
    state[key] = {
        "last_triggered_at": now.isoformat(),
        "last_level": level,
        "silence_until": (now + timedelta(seconds=silence_seconds)).isoformat(),
    }


def clear_state(state: dict, key: str) -> None:
    """清除某 key 的历史记录（用于该切片当前评估为 OK 时）。"""
    state.pop(key, None)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Self test (smoke test)
# ---------------------------------------------------------------------------
def _self_test() -> int:
    """
    覆盖 6 个核心场景：
      1) 首次触发
      2) 同级别立即重复 → 静默
      3) P1→P0 升级 → 打破静默
      4) P0→P1 降级 → 静默
      5) 静默期到期 → 重新触发
      6) clear_state 后再触发 → 视为首次
    """
    failures = []
    state: dict = {}
    key = make_key("e7f6test", "steam", "all_reviews", "__global__")
    t0 = datetime(2026, 5, 7, 10, 0, 0, tzinfo=timezone.utc)

    def _check(name: str, ok: bool, detail: str = "") -> None:
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            failures.append(name)

    # 场景 1：首次触发
    s, r = should_trigger(state, key, "P1", t0, 7200)
    _check("1) 首次触发应 trigger", s and r == "first_trigger", f"got s={s}, r={r}")
    record_trigger(state, key, "P1", 7200, t0)

    # 场景 2：同级别立即重复 → 静默
    t1 = t0 + timedelta(minutes=10)
    s, r = should_trigger(state, key, "P1", t1, 7200)
    _check("2) 同级 10min 后应静默", (not s) and r.startswith("silenced_until_"),
           f"got s={s}, r={r}")

    # 场景 3：升级 P1→P0 打破静默
    s, r = should_trigger(state, key, "P0", t1, 3600)
    _check("3) P1→P0 升级应 trigger", s and r == "upgraded_from_P1", f"got s={s}, r={r}")
    record_trigger(state, key, "P0", 3600, t1)

    # 场景 4：降级 P0→P1 → 静默
    t2 = t1 + timedelta(minutes=20)
    s, r = should_trigger(state, key, "P1", t2, 7200)
    _check("4) P0→P1 降级应静默", (not s) and r == "downgrade_silenced",
           f"got s={s}, r={r}")

    # 场景 5：静默期到期重新触发
    t3 = t1 + timedelta(seconds=3600 + 1)  # 超过 P0 的 1h 静默
    s, r = should_trigger(state, key, "P0", t3, 3600)
    _check("5) 静默期到期应 trigger", s and r == "silence_expired", f"got s={s}, r={r}")

    # 场景 6：clear_state 后再触发视为首次
    clear_state(state, key)
    s, r = should_trigger(state, key, "P2", t3, 21600)
    _check("6) clear_state 后再触发应视为首次", s and r == "first_trigger",
           f"got s={s}, r={r}")

    # 场景 7：load/save 往返一致性
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        tf_path = tf.name
    try:
        record_trigger(state, key, "P0", 3600, t3)
        save_state(tf_path, state)
        loaded = load_state(tf_path)
        _check("7) save/load 往返一致", loaded == state, f"got {loaded!r}")
    finally:
        Path(tf_path).unlink(missing_ok=True)

    # 场景 8：OK 等级永不触发
    s, r = should_trigger(state, key, "OK", t3, 0)
    _check("8) OK 等级不应 trigger", (not s) and r == "level_is_ok", f"got s={s}, r={r}")

    print(f"\n{'-' * 40}")
    if failures:
        print(f"FAIL: {len(failures)} / 8 — {failures}")
        return 1
    print("PASS: 8 / 8")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="静默期状态管理（CLI 仅作 self-test）")
    parser.add_argument("--self_test", action="store_true", help="运行内置 smoke test")
    parser.add_argument("--show", default="", help="展示指定状态文件内容（默认 /tmp/databrain_alert_state.json）")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    path = args.show or DEFAULT_STATE_PATH
    state = load_state(path)
    print(f"State file: {path}")
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
