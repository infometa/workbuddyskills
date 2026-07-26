# -*- coding: utf-8 -*-
"""
causal_verifier.py — Layer 2 信号筛选（阴果验）

职责：把 Layer1 采集到的「触发信号名」映射到三条因果链，给出 effective_sign
（方向，唯一权威在 Layer2）。

动态前序/后序判定（非固定字段）：
  · 每条链上，触发的信号中 chain_index 最大者（最靠近结局）= 后序 → 进景气度
  · 之前的触发信号 = 前序 → 不进景气度
  · 链上无触发 → 静默
  · 输出 active_signals + chain_health，交 Layer3

用法：
  python causal_verifier.py --triggered triggered.json [--out resolved.json]
  python causal_verifier.py --self-test
  # triggered.json: {"triggered": ["旭创/新易盛营收增速", "EML缺口(200G)", ...]}
"""
from __future__ import annotations
import json
import argparse
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signals_config import (SIGNALS, SIGNAL_INDEX, CHAINS, chain_index)


def verify(triggered_names: list[str]) -> dict:
    """输入触发信号名列表 → 输出 Layer2 产物。"""
    active = []
    unknown = []
    for name in triggered_names:
        s = SIGNAL_INDEX.get(name)
        if not s:
            unknown.append(name)
            continue
        ci = chain_index(name)
        active.append({
            "name": name,
            "end": s["end"],
            "chain": s["chain"],
            "chain_index": ci,
            "distance": s["distance"],
            "effective_sign": s["base_sign"],   # 方向唯一权威：Layer2 解析
            "is_successor": False,              # 下方动态判定
            "interpretation": s["interpretation"],
        })

    # ── 动态分界：每条链找触发信号中 chain_index 最大者 = 后序 ──
    chain_health = {}
    for c in CHAINS:
        chain_signals = [a for a in active if a["chain"] == c]
        if not chain_signals:
            chain_health[c] = "静默"
            continue
        max_idx = max(a["chain_index"] for a in chain_signals)
        for a in chain_signals:
            a["is_successor"] = (a["chain_index"] == max_idx)
        chain_health[c] = "确认"

    return {
        "active_signals": active,
        "unknown_signals": unknown,
        "chain_health": chain_health,
    }


def self_test():
    # ── 场景1：全信号触发 → 每条链只有 chain_index 最大的信号是后序 ──
    triggered = [s["name"] for s in SIGNALS]
    out = verify(triggered)
    print("=== 阴果验 self-test (全信号触发) ===")
    print(json.dumps(out, ensure_ascii=False, indent=2))

    # 每条链恰好 1 个后序
    for c in CHAINS:
        succ = [a for a in out["active_signals"]
                if a["chain"] == c and a["is_successor"]]
        assert len(succ) == 1, f"链{c}后序数={len(succ)}，应为1"
        # 后序的 chain_index 应为该链最大值
        chain_signals = [a for a in out["active_signals"] if a["chain"] == c]
        max_idx = max(a["chain_index"] for a in chain_signals)
        assert succ[0]["chain_index"] == max_idx

    # 链健康度：三链全确认
    assert out["chain_health"] == {"供给": "确认", "需求": "确认", "技术": "确认"}

    # ── 场景2：仅供给链前两个信号触发 → 第二个为后序 ──
    out2 = verify(["MOCVD设备订单", "InP衬底价格/供给"])
    s2 = out2["active_signals"]
    assert s2[0]["is_successor"] is False   # MOCVD (index 0)
    assert s2[1]["is_successor"] is True    # InP (index 1)
    assert out2["chain_health"]["供给"] == "确认"
    assert out2["chain_health"]["需求"] == "静默"
    assert out2["chain_health"]["技术"] == "静默"

    # ── 场景3：单信号触发 → 该信号即后序 ──
    out3 = verify(["MOCVD设备订单"])
    assert out3["active_signals"][0]["is_successor"] is True
    assert out3["chain_health"]["供给"] == "确认"

    print("\n[test] ✅ 动态分界：每链最远触发信号=后序；之前的=前序；单信号触发=后序")


def main():
    ap = argparse.ArgumentParser(description="Layer2 信号筛选（阴果验）")
    ap.add_argument("--triggered", help="触发信号名 JSON ({'triggered':[...]})")
    ap.add_argument("--out", help="输出 resolved JSON")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.triggered:
        print("错误: 需提供 --triggered 或 --self-test")
        sys.exit(1)
    with open(args.triggered, encoding="utf-8") as f:
        spec = json.load(f)
    out = verify(spec.get("triggered", []))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[verify] 已写 {args.out}")
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
