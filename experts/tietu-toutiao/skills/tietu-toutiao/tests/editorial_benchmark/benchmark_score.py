#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编辑基准集跑分脚本（benchmark_score.py）

对 tests/editorial_benchmark/cases/ 下每个注册 case，比较模型产出的
content-state（state.json）与人工标注（expected.json），按三个维度评分：

  - headline_agree : 主标题逐字一致（规范化空白/全半角后）
  - item_agree     : 条目标题集合重合率 >= 0.5
  - bbox_fidelity  : 主图 bbox IoU >= 0.8

诚实原则：case 数不足 --min-cases 时 exit 3（防冒充门禁）；任何 case 文件
缺失/损坏按结构错误 exit 2，不跳过、不降门槛、不伪造指标。

退出码：0 全部通过；1 agree_rate 低于阈值；2 结构错误；3 case 数不足。

用法：
  python benchmark_score.py --benchmark-dir <...>/editorial_benchmark \
      --min-cases 10 --min-agree 0.8 [--report report.json]
"""

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- utilities

def _norm_text(text):
    """规范化文本：全角转半角、去空白差异，仅用于比较不用于展示。"""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", "", text).strip().lower()


def _headline(item):
    """条目标题，兼容 items[] 里 headline/title 两种命名。"""
    if not isinstance(item, dict):
        return ""
    return _norm_text(item.get("headline") or item.get("title") or "")


def _bbox(val):
    """bbox 归一化为 (x, y, w, h) 浮点元组；失败返回 None。"""
    if not isinstance(val, (list, tuple, dict)):
        return None
    try:
        if isinstance(val, dict):
            keys = ("x", "y", "w", "h") if "w" in val else ("x", "y", "width", "height")
            x, y, w, h = (float(val[k]) for k in keys)
        else:
            if len(val) == 4:
                x, y, w, h = (float(v) for v in val)
            elif len(val) == 2:  # 两点式 [x1,y1,x2,y2] 会被 len==4 覆盖；这里不支持
                return None
            else:
                return None
    except (TypeError, ValueError, KeyError):
        return None
    if w <= 0 or h <= 0:
        return None
    return (x, y, w, h)


def _iou(a, b):
    """两个 (x,y,w,h) 的 IoU；无效输入返回 0.0。"""
    if not a or not b:
        return 0.0
    ax1, ay1, ax2, ay2 = a[0], a[1], a[0] + a[2], a[1] + a[3]
    bx1, by1, bx2, by2 = b[0], b[1], b[0] + b[2], b[1] + b[3]
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def _headline_text(state):
    """从 content-state 提取主标题文本（契约形式 headline.original + 常见变体）。"""
    h = state.get("headline")
    if isinstance(h, dict):
        for k in ("original", "text", "final"):
            v = h.get(k)
            if isinstance(v, str) and v.strip():
                return v
    elif isinstance(h, str) and h.strip():
        return h
    for key in ("headline_text", "title"):
        v = state.get(key)
        if isinstance(v, str) and v.strip():
            return v
    cover = state.get("cover") or {}
    if isinstance(cover, dict):
        v = cover.get("headline_text") or cover.get("title")
        if isinstance(v, str) and v.strip():
            return v
    return ""


def _state_bboxes(state):
    """收集 state 中所有候选图片 bbox（版面坐标：layout_analysis.photo_regions 优先）。"""
    out = []
    la = state.get("layout_analysis")
    if isinstance(la, dict):
        for pr in (la.get("photo_regions") or []):
            if isinstance(pr, dict):
                b = _bbox(pr.get("bbox"))
                if b:
                    out.append(b)
    v = state.get("photo_bbox")
    b = _bbox(v)
    if b:
        out.append(b)
    cover = state.get("cover") or {}
    if isinstance(cover, dict):
        b = _bbox(cover.get("photo_bbox") or cover.get("image_bbox"))
        if b:
            out.append(b)
    items = state.get("items") or []
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                b = _bbox(it.get("bbox") or it.get("photo_bbox"))
                if b:
                    out.append(b)
    return out


def _main_photo_bbox(state):
    """取主图 bbox：优先 photo_bbox，否则 items 里权重最高条目的 bbox。"""
    bboxes = _state_bboxes(state)
    if not bboxes:
        return None
    return bboxes[0]

# ---------------------------------------------------------------- scoring

def score_case(case_dir):
    """评单个 case，返回 (dict 明细, error_or_None)。结构错误时 error 非 None。"""
    exp_path = case_dir / "expected.json"
    state_path = case_dir / "state.json"
    if not exp_path.exists() or not state_path.exists():
        return None, "missing expected.json / state.json in %s" % case_dir.name
    try:
        expected = json.loads(exp_path.read_text(encoding="utf-8"))
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, "bad JSON in %s: %s" % (case_dir.name, exc)

    # --- headline
    exp_hl = _norm_text(expected.get("expected_headline_text"))
    got_hl = _norm_text(_headline_text(state))
    headline_ok = bool(exp_hl) and exp_hl == got_hl

    # --- item agree: 集合重合率（以 expected 为分母）
    exp_set = {_headline(it) for it in (expected.get("expected_items") or [])}
    exp_set.discard("")
    got_set = {_headline(it) for it in (state.get("items") or [])}
    got_set.discard("")
    if exp_set:
        item_agree = len(exp_set & got_set) / len(exp_set)
    else:
        item_agree = 0.0

    # --- bbox fidelity: state 中最佳 bbox 与 expected 主图 bbox 的 IoU
    exp_bbox = _bbox(expected.get("expected_photo_bbox"))
    got_bboxes = _state_bboxes(state)
    best_iou = max((_iou(exp_bbox, g) for g in got_bboxes), default=0.0) if exp_bbox else 0.0

    detail = {
        "case_id": expected.get("case_id") or case_dir.name,
        "headline_agree": headline_ok,
        "item_agree": round(item_agree, 4),
        "bbox_fidelity": round(best_iou, 4),
    }
    passed = headline_ok and item_agree >= 0.5 and best_iou >= 0.8
    detail["passed"] = passed
    return detail, None

# ---------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description="Editorial benchmark scorer")
    parser.add_argument("--benchmark-dir", required=True,
                        help="editorial_benchmark 目录（含 cases/）")
    parser.add_argument("--min-cases", type=int, default=10,
                        help="最小 case 数门禁（v1 目标 10）")
    parser.add_argument("--min-agree", type=float, default=0.8,
                        help="case 通过率阈值")
    parser.add_argument("--report", default=None,
                        help="把逐 case 明细写入该 JSON 文件；'-' 表示 stdout")
    args = parser.parse_args(argv)

    bench = Path(args.benchmark_dir)
    cases_dir = bench / "cases"
    manifest = cases_dir / "cases_manifest.json"
    if not manifest.exists():
        print("[BENCH][ERROR] cases_manifest.json 不存在：%s" % manifest, file=sys.stderr)
        print("[BENCH] 基准集尚未建集。按 README 的 expected.json 结构逐份人工标注后注册。",
              file=sys.stderr)
        return 2
    try:
        reg = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print("[BENCH][ERROR] cases_manifest.json 坏 JSON：%s" % exc, file=sys.stderr)
        return 2
    case_ids = [c for c in (reg.get("cases") or []) if isinstance(c, str) and c]

    if len(case_ids) < args.min_cases:
        print("[BENCH][GATE] case 数不足：注册 %d 份 < 门槛 %d 份。"
              % (len(case_ids), args.min_cases), file=sys.stderr)
        print("[BENCH] 拒绝用 %d 份样本冒充达标率（诚实原则）。缺 %d 份，"
              "按 README 建集计划灌入真实标注后再跑。"
              % (len(case_ids), args.min_cases - len(case_ids)), file=sys.stderr)
        return 3

    details, structural_errors = [], []
    for cid in case_ids:
        cdir = cases_dir / cid
        if not cdir.is_dir():
            structural_errors.append("case 目录不存在：%s" % cid)
            continue
        detail, err = score_case(cdir)
        if err:
            structural_errors.append(err)
        else:
            details.append(detail)

    if structural_errors:
        for e in structural_errors:
            print("[BENCH][ERROR] %s" % e, file=sys.stderr)
        print("[BENCH] 存在结构错误，拒绝给出聚合指标（坏 case 不跳过）。", file=sys.stderr)
        return 2

    passed_n = sum(1 for d in details if d["passed"])
    agree_rate = passed_n / len(details) if details else 0.0

    print("[BENCH] case=%d passed=%d agree_rate=%.3f (threshold=%.2f)"
          % (len(details), passed_n, agree_rate, args.min_agree))
    for d in details:
        flag = "PASS" if d["passed"] else "FAIL"
        print("[BENCH][%s] %s headline=%s item_agree=%.3f bbox_iou=%.3f"
              % (flag, d["case_id"], "ok" if d["headline_agree"] else "MISMATCH",
                 d["item_agree"], d["bbox_fidelity"]))
        if not d["passed"]:
            print("         -> 差异点：标题需逐字一致；条目重合率>=0.5；主图 IoU>=0.8")

    if args.report:
        payload = json.dumps({
            "min_cases": args.min_cases, "min_agree": args.min_agree,
            "cases": len(details), "passed": passed_n,
            "agree_rate": round(agree_rate, 4), "details": details,
        }, ensure_ascii=False, indent=2)
        if args.report == "-":
            print(payload)
        else:
            Path(args.report).write_text(payload, encoding="utf-8")
            print("[BENCH] 明细已写入 %s" % args.report)

    return 0 if agree_rate >= args.min_agree else 1


if __name__ == "__main__":
    sys.exit(main())
