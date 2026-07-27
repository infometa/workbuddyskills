#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_assessment_into_profile.py
把测评结果（DNA 解析后的 JSON）写入 ~/.workbuddy/career-broker/<rtx>/assessment.json
并在 profile.json 顶层加 assessment 字段（C 互补方案）。

调用：
    python merge_assessment_into_profile.py --rtx <your-rtx> --result-json '<DNA 解析后的 json>'
"""
import argparse, json, sys
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtx", required=True)
    ap.add_argument("--result-json", required=True, help="parse_result_code.py 输出的 result 字段 JSON 字符串")
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else (
        Path.home() / ".workbuddy" / "career-broker" / args.rtx
    )
    base.mkdir(parents=True, exist_ok=True)

    try:
        result = json.loads(args.result_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"result-json 解析失败: {e}"}, ensure_ascii=False))
        sys.exit(2)

    # 1. 写独立 assessment.json（完整版，含解析细节）
    assessment_full = {
        "schema_version": "1.0",
        "rtx": args.rtx,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        **result,
    }
    (base / "assessment.json").write_text(
        json.dumps(assessment_full, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 2. 更新 profile.json 顶层 assessment 字段（精简版，给下游 skill 用）
    profile_path = base / "profile.json"
    if profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["assessment"] = {
            "result_code": result.get("raw_code"),
            "main_code": result.get("main_code"),
            "anchors_top3": result.get("anchors_top3", []),
            "styles_top2": result.get("styles_top2", []),
            "psy_state_summary": {
                k: v.get("score") for k, v in (result.get("psy_state") or {}).items()
            },
            "burnout_alert": result.get("psy_burnout_alert", False),
            "captured_at": assessment_full["captured_at"],
        }
        profile["schema_version"] = "2.1"  # 升 schema 版本号
        profile_path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        merged = True
    else:
        merged = False

    print(json.dumps({
        "ok": True,
        "assessment_file": str(base / "assessment.json"),
        "profile_merged": merged,
        "profile_file": str(profile_path) if merged else None,
        "burnout_alert": result.get("psy_burnout_alert", False),
        "next_step": ("M3 教练（B 倦怠指数 ≥3.5）" if result.get("psy_burnout_alert")
                      else "M2 方向建议"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
