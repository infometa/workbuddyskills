# -*- coding: utf-8 -*-
"""
weight_engine.py — Layer 3 信号处理（权仲校）

景气度：仅后序信号净汇总
  w_sig     = 距离折扣 × 命中率
  chain_net = Σ 后序信号 (w_sig × effective_sign)        # 按链归因
  景气度(净) = Σ chain_net
  方向      = sign(景气度)

置信度：C × R × S（三因子连乘，无 link_strength）
  C = 跨链收敛 = 同向链数 ÷ 总链数(3，含静默链，文档 Layer3 置信度表)
  R = 命中率可靠度 = f(累计期数)  <8→0.3 / 8–24→0.6 / 24+→0.9
  S = 来源可信度 = 专业1.0 / 部分0.8 / 纯网0.6
  >0.66 高 / >0.33 中 / 否则 低

用法：
  python weight_engine.py --resolved resolved.json --mode 专业 --run-count 1 [--calibration calibration.json]
  python weight_engine.py --self-test
"""
from __future__ import annotations
import json
import argparse
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from signals_config import (DISTANCE_DISCOUNT, MODE_FACTOR, r_from_periods,
                            CONF_HIGH, CONF_MID)

DEFAULT_HIT_RATE = 0.5


def load_calibration(path):
    if path and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("signals", {})
        except Exception:
            return {}
    return {}


def get_hit_rate(calib, name, min_samples=3):
    rec = calib.get(name)
    if rec and isinstance(rec, dict) and rec.get("samples", 0) >= min_samples:
        return float(rec.get("hit_rate", DEFAULT_HIT_RATE))
    return DEFAULT_HIT_RATE


def classify_confidence(raw):
    if raw > CONF_HIGH:
        return "高"
    if raw > CONF_MID:
        return "中"
    return "低"


def _next_quarter_end(d):
    q = (d.month - 1) // 3
    m = (q + 1) * 3 + 1
    y = d.year
    if m > 12:
        m = 1
        y += 1
    first = date(y, m, 1)
    return (first - timedelta(days=1)).isoformat()


def build_meta(mode, active_signals, calib):
    """构造 rater.py 所需的 meta 字段，使 weight_engine → rater 管道可直接串联。"""
    src = {"专业": "万得 ✅ + 通达信 ✅",
           "部分": "专业数据源缺一项（部分精度）",
           "纯网": "纯互联网公开数据（精度下降）"}.get(mode, mode)
    return {"run_date": date.today().isoformat(), "mode": mode,
            "data_source": src, "triggered_count": len(active_signals or [])}


def build_evolution(run_count, R, calib):
    cal = sum(1 for rec in (calib or {}).values()
              if isinstance(rec, dict) and rec.get("samples", 0) >= 3)
    return {"run_count": run_count, "R": R, "calibrated_signals": cal,
            "next_calibration": _next_quarter_end(date.today())}


def compute(active_signals, mode="专业", run_count=1, calib=None):
    """active_signals: Layer2 输出（含 chain/chain_index/effective_sign/distance/is_successor）。"""
    if calib is None:
        calib = {}
    mode_factor = MODE_FACTOR.get(mode, 1.0)
    R = r_from_periods(run_count)

    rows = []
    by_chain = {}

    for a in active_signals:
        name = a["name"]
        distance = a.get("distance", "浅")
        eff = int(a.get("effective_sign", 0))
        is_succ = a.get("is_successor", False)
        discount = DISTANCE_DISCOUNT.get(distance, 1.0)
        hit = get_hit_rate(calib, name)
        w = discount * hit
        signed = w * eff if is_succ else 0.0   # 前序不进景气度

        if is_succ:
            by_chain.setdefault(a["chain"], 0.0)
            by_chain[a["chain"]] += signed

        rows.append({
            "name": name, "chain": a["chain"],
            "chain_index": a.get("chain_index", -1),
            "distance": distance, "effective_sign": eff,
            "is_successor": is_succ,
            "distance_discount": discount, "hit_rate": round(hit, 3),
            "weight": round(w, 4), "signed": round(signed, 4),
        })

    # ── 景气度：后序净汇总 ──
    prosperity_signed = round(sum(r["signed"] for r in rows if r["is_successor"]), 4)
    by_chain = {k: round(v, 4) for k, v in by_chain.items()}
    direction = "扩张" if prosperity_signed > 0 else ("收缩" if prosperity_signed < 0 else "持平")

    # ── 置信度 C：跨链收敛 ──
    # 文档 Layer3 置信度表：C = 同向链数 ÷ 总链数（总链数=3，含静默链）
    TOTAL_CHAINS = 3
    effective = {c: v for c, v in by_chain.items() if v != 0}
    if not effective:
        C = 1.0                       # 无有效链 → 视为无分歧
    elif prosperity_signed == 0:
        C = 0.0                       # 方向相反相消 → 最大分歧
    else:
        overall_sign = 1 if prosperity_signed > 0 else -1
        agree = sum(1 for v in effective.values() if (v > 0) == (overall_sign > 0))
        C = round(agree / TOTAL_CHAINS, 3)

    confidence_raw = round(C * R * mode_factor, 4)
    conf_label = classify_confidence(confidence_raw)

    # 多链收敛卡
    convergence_card = []
    for c in ["供给", "需求", "技术"]:
        net = by_chain.get(c)
        if net is None:
            convergence_card.append({"chain": c, "net": None, "direction": "无信号", "agree": None})
        else:
            d = "扩张" if net > 0 else ("收缩" if net < 0 else "持平")
            agree = (net > 0) == (prosperity_signed > 0) if prosperity_signed != 0 else None
            convergence_card.append({"chain": c, "net": net,
                                     "direction": d, "agree": agree})

    return {
        "weights": rows,
        "summary": {
            "prosperity_signed": prosperity_signed,
            "by_chain": by_chain,
            "prosperity_direction": direction,
            "confidence_C": C,
            "confidence_R": R,
            "confidence_S": mode_factor,
            "confidence_raw": confidence_raw,
            "confidence_label": conf_label,
            "convergence_card": convergence_card,
        },
    }


def self_test():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from signals_config import SIGNALS
    from causal_verifier import verify

    # ── 场景A：全信号触发（动态分界：每链最远触发信号=后序）──
    # 供给→VCSEL(+1,中), 需求→旭创(+1,浅), 技术→云厂口径(-1,中)
    triggered = [s["name"] for s in SIGNALS]
    active = verify(triggered)["active_signals"]

    r1 = compute(active, mode="专业", run_count=1, calib={})
    s1 = r1["summary"]
    print("=== 权重引擎 self-test (全信号 / 专业) ===")
    assert s1["prosperity_direction"] == "扩张", s1   # 需求+供给(+0.8) > 技术(-0.3)
    # 供给(+0.3)+需求(+0.5)同向 → agree=2；技术(-0.3)背离 → C=2/3
    assert abs(s1["confidence_C"] - round(2 / 3, 3)) < 1e-6, s1["confidence_C"]
    assert s1["confidence_R"] == 0.3                       # 第1期
    assert s1["confidence_label"] == "低"                  # 2/3*0.3*1.0=0.20
    print(f"  [A 分歧] 景气度={s1['prosperity_signed']:+.3f}({s1['prosperity_direction']}) "
          f"C={s1['confidence_C']} → 置信度={s1['confidence_raw']}({s1['confidence_label']})")

    # R 升档 → C=2/3 不变，置信度从低→中
    r1b = compute(active, mode="专业", run_count=10, calib={})
    s1b = r1b["summary"]
    assert s1b["confidence_R"] == 0.6
    assert s1b["confidence_label"] == "中"                 # 2/3*0.6*1.0=0.40

    # ── 场景B：仅需求+供给 base_sign>0（两链同向 +）→ C=2/3 ──
    conv = [s["name"] for s in SIGNALS
            if s["chain"] in ("需求", "供给") and s["base_sign"] > 0]
    active_b = verify(conv)["active_signals"]
    rb1 = compute(active_b, mode="专业", run_count=1, calib={})
    rb2 = compute(active_b, mode="专业", run_count=12, calib={})
    sb1, sb2 = rb1["summary"], rb2["summary"]
    assert abs(sb1["confidence_C"] - round(2/3, 3)) < 1e-6, sb1["confidence_C"]  # 两链均+，但÷总链数3
    assert sb1["confidence_label"] == "低"                 # 2/3*0.3*1.0=0.20
    assert sb2["confidence_label"] == "中"                 # 2/3*0.6*1.0=0.40
    print(f"  [B 收敛] C={sb2['confidence_C']} 第1期={sb1['confidence_raw']}({sb1['confidence_label']}) "
          f"→ 第12期={sb2['confidence_raw']}({sb2['confidence_label']})  [R 升档生效]")

    # ── 场景C：纯网降档 S=0.6 拉低置信度（对比 B 的中 → 退回低）──
    rc = compute(active_b, mode="纯网", run_count=12, calib={})
    sc = rc["summary"]
    assert sc["confidence_label"] == "低"                  # 2/3*0.6*0.6=0.24 <0.33
    print(f"  [C 纯网] 置信度={sc['confidence_raw']}({sc['confidence_label']})  [S 降档生效，对比 B=中]")

    # 前序不进景气度
    pred = [r for r in r1["weights"] if not r["is_successor"]]
    assert all(r["signed"] == 0.0 for r in pred), "前序不应计入景气度"
    # 每条链恰好1个后序
    for c in ["供给", "需求", "技术"]:
        succ = [r for r in r1["weights"] if r["chain"] == c and r["is_successor"]]
        assert len(succ) == 1, f"链{c}后序数={len(succ)}，应为1"

    print("\n[test] ✅ 动态分界：每链最远触发信号=后序(仅1个)；前序不进；"
          "C=2/3(两链同向÷3)；R升档/S降档生效")


def main():
    ap = argparse.ArgumentParser(description="Layer3 信号处理（权仲校）")
    ap.add_argument("--resolved", help="Layer2 产物 JSON (含 active_signals)")
    ap.add_argument("--mode", default="专业", help="专业/部分/纯网")
    ap.add_argument("--run-count", type=int, default=1, help="累计运行期数（R）")
    ap.add_argument("--calibration", help="calibration.json 路径")
    ap.add_argument("--out", help="输出权重 JSON")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.resolved:
        print("错误: 需提供 --resolved 或 --self-test")
        sys.exit(1)
    with open(args.resolved, encoding="utf-8") as f:
        spec = json.load(f)
    active = spec.get("active_signals", spec.get("signals", []))
    calib = load_calibration(args.calibration)
    result = compute(active, mode=args.mode, run_count=args.run_count, calib=calib)
    result["meta"] = build_meta(args.mode, active, calib)
    result["evolution"] = build_evolution(args.run_count, result["summary"]["confidence_R"], calib)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[weight] 已写 {args.out}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
