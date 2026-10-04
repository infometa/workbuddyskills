#!/usr/bin/env python3
"""run_full — listing-core 编排快捷入口，把多条 CLI 收敛成两条。

写作是语义步骤（listing-copy-suite-writer 由模型完成），无法端到端一键跑完，
所以这里只固化写作**前后**的确定性部分：

    start   run_manifest.py init + 建目录 + build_spec.py
      ↓  （模型写 listing-draft.json）
    finish  validate_fields.py → 可选 score_quality → finalize_listing.py

这样做的直接收益：调用方不必逐个脚本试参数、也不会漏掉 `--check-report`
（评分必须吃机检结果，否则超限字段照样能拿高分）。

用法：

    python3 run_full.py start --run-dir /abs/run --mode rewrite --profile standard \\
        --keywords /abs/02-insight/keywords-grouped.json \\
        --buyer-questions /abs/02-insight/buyer-questions.json \\
        --brands-owned Velmoriq --brands-competitor "BrandX,BrandY" \\
        --marketplace US --output-language en_US

    python3 run_full.py finish --run-dir /abs/run \\
        --draft /abs/03-write/listing-draft.json \\
        --facts /abs/01-facts/product-facts.md \\
        --deductions /abs/03-write/deductions.json

退出码：0 成功；2 表示字段安检未通过（stdout 打印失败字段与原因，供局部重写）。
本脚本只编排与校验，绝不修改任何 Listing 文案。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from build_spec import assemble_spec  # noqa: E402
from preflight import inspect_runtime  # noqa: E402
from run_manifest import init_manifest, parse_profile, update_stage  # noqa: E402
from validate_fields import check_fields  # noqa: E402

STAGE_DIRS = ("01-facts", "02-insight", "03-write")


def _require_runtime_contract() -> None:
    result = inspect_runtime()
    if result["ok"]:
        return
    parts = []
    if result["missing"]:
        parts.append("missing=" + ",".join(result["missing"]))
    if result["incompatible"]:
        details = ";".join(
            f"{script}:{','.join(flags)}"
            for script, flags in result["incompatible"].items()
        )
        parts.append("cli=" + details)
    raise RuntimeError("listing-core runtime contract failed: " + " | ".join(parts))


def _load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def _fresh_audit_insight_paths(
    handoff: dict, *, asin: str | None, marketplace: str,
) -> dict[str, str] | None:
    """返回可直接复用的 Audit S3 产物；契约不完整/过期时安全回退。"""
    if handoff.get("kind") != "listingAuditHandoff" or handoff.get("schema_version") != 1:
        return None
    target = handoff.get("target") or {}
    target_asin = str(target.get("asin") or "").strip().upper()
    target_marketplace = str(target.get("marketplace") or "").strip().upper()
    if asin and target_asin and target_asin != asin.strip().upper():
        return None
    if target_marketplace and target_marketplace != marketplace.strip().upper():
        return None

    freshness = handoff.get("data_freshness") or {}
    captured_at = freshness.get("captured_at")
    window_hours = freshness.get("cache_window_hours", 24)
    if not isinstance(captured_at, str) or not isinstance(window_hours, (int, float)):
        return None
    try:
        captured = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        if captured.tzinfo is None:
            captured = captured.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - captured.astimezone(timezone.utc)).total_seconds() / 3600
    except ValueError:
        return None
    if age_hours < 0 or age_hours > float(window_hours):
        return None

    evidence = handoff.get("evidence_paths") or {}
    required = ("keywords", "buyer_questions", "insight")
    paths = {key: str(evidence.get(key) or "") for key in required}
    if any(not os.path.isfile(path) for path in paths.values()):
        return None
    return paths


def cmd_start(args: argparse.Namespace) -> int:
    _require_runtime_contract()
    prepare_started = time.perf_counter()
    run_dir = Path(os.path.abspath(args.run_dir))
    profile = parse_profile(args.profile)
    if args.marketplace:
        profile["marketplace"] = args.marketplace
    if args.output_language:
        profile["output_language"] = args.output_language
    rewrite_handoff = _load_json(args.audit_handoff) if args.audit_handoff else None
    if (
        isinstance(rewrite_handoff, dict)
        and rewrite_handoff.get("kind") == "listingAuditReport"
        and isinstance(rewrite_handoff.get("auditHandoff"), dict)
    ):
        rewrite_handoff = rewrite_handoff["auditHandoff"]
    reused_paths = _fresh_audit_insight_paths(
        rewrite_handoff or {}, asin=args.asin, marketplace=args.marketplace or "US",
    )
    keywords_path = args.keywords or (reused_paths or {}).get("keywords")
    buyer_questions_path = args.buyer_questions or (reused_paths or {}).get("buyer_questions")
    evidence_mode = args.evidence_mode or (
        "facts_only" if args.mode == "rewrite" and not keywords_path else "external"
    )
    if evidence_mode == "external" and not args.keywords:
        if not keywords_path:
            raise ValueError("external evidence mode requires --keywords or a fresh audit insight bundle")
    keywords = _load_json(keywords_path) if keywords_path else {}

    spec = assemble_spec(
        mode=args.mode,
        brands_owned=_csv(args.brands_owned),
        brands_competitor=_csv(args.brands_competitor),
        keywords=keywords,
        category_flags=_csv(args.category_flags),
        user_spec=_load_json(args.spec) if args.spec else None,
        style_angle=args.style_angle,
        output_language=args.output_language,
        buyer_questions=_load_json(buyer_questions_path) if buyer_questions_path else None,
        marketplace=args.marketplace or "US",
        category=args.category,
        product_type=args.product_type,
        profile=str(profile.get("profile") or "standard"),
        rewrite_handoff=rewrite_handoff,
        evidence_mode=evidence_mode,
        banned_terms=_csv(args.banned_terms),
    )
    # 输入全部解析成功后再创建 run，避免坏 JSON 留下半初始化目录。
    manifest_path = init_manifest(str(run_dir), args.mode, profile)
    for name in STAGE_DIRS:
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    if reused_paths:
        canonical_paths = {
            "keywords": run_dir / "02-insight" / "keywords.json",
            "buyer_questions": run_dir / "02-insight" / "buyer-questions.json",
            "insight": run_dir / "02-insight" / "insight.md",
        }
        for key, destination in canonical_paths.items():
            source = Path(reused_paths[key]).resolve()
            if source != destination.resolve():
                shutil.copyfile(source, destination)
        update_stage(
            manifest_path, "insight", "complete",
            artifacts=[
                {"name": "keywords.json", "path": str(canonical_paths["keywords"]), "kind": "json"},
                {"name": "buyer-questions.json", "path": str(canonical_paths["buyer_questions"]), "kind": "json"},
                {"name": "insight.md", "path": str(canonical_paths["insight"]), "kind": "markdown"},
            ],
        )
    spec_path = run_dir / "03-write" / "spec.json"
    _write_json(spec_path, spec)
    update_stage(
        manifest_path, "write", "active",
        artifacts=[{"name": "spec", "path": str(spec_path), "kind": "json"}],
        metrics={"prepare_ms": round((time.perf_counter() - prepare_started) * 1000)},
    )
    # 一次 Bash 输出只允许一行 `Saved full response:`；spec 作为伴生产物走 JSON artifact 行。
    print(f"Saved full response: {manifest_path}")
    print(f"JSON artifact: {spec_path}")
    print(f"Draft target: {run_dir / '03-write' / 'listing-draft.json'}")
    print(f"Evidence mode: {evidence_mode}")
    print(f"Audit insight reused: {'true' if reused_paths else 'false'}")
    limits = spec["limits"]
    print(
        "Limits: title<={title_max} highlights<={item_highlights_max} "
        "bullet<={bullet_each_max}x{bullet_count} description<={description_max} "
        "search_terms<={search_terms_bytes_max}bytes".format(**limits)
    )
    return 0


def _failed_fields(report: dict) -> list[tuple[str, list[str]]]:
    failures: list[tuple[str, list[str]]] = []
    for name, field in (report.get("fields") or {}).items():
        if isinstance(field, dict) and field.get("status") == "fail":
            failures.append((
                name,
                [str(issue.get("detail") or "") for issue in (field.get("issues") or [])],
            ))
    return failures


def cmd_finish(args: argparse.Namespace) -> int:
    _require_runtime_contract()
    run_dir = Path(os.path.abspath(args.run_dir))
    manifest_path = str(run_dir / "run-manifest.json")
    spec_path = args.spec or str(run_dir / "03-write" / "spec.json")
    draft_path = args.draft or str(run_dir / "03-write" / "listing-draft.json")
    check_report_path = run_dir / "03-write" / "check-report.json"
    update_stage(manifest_path, "write", "active")

    draft = _load_json(draft_path)
    spec = _load_json(spec_path)
    facts_text = ""
    if args.facts and os.path.isfile(args.facts):
        facts_text = Path(args.facts).read_text(encoding="utf-8")

    validate_started = time.perf_counter()
    report = check_fields(draft, spec, facts_text=facts_text)
    validation_ms = round((time.perf_counter() - validate_started) * 1000)
    _write_json(check_report_path, report)
    # finish 后续会转发 finalize_listing.py 的 stdout，那里已经有唯一的 `Saved full response:`；
    # 机检报告在这里必须走 JSON artifact 行，否则会顶掉 listing-final.json 的主产物行。
    print(f"JSON artifact: {check_report_path}")

    failures = _failed_fields(report)
    if failures:
        update_stage(
            manifest_path, "write", "failed",
            artifacts=[{"name": "check-report", "path": str(check_report_path), "kind": "json"}],
            metrics={"validation_ms": validation_ms},
        )
        print("QA FAILED — 只重写下列字段，其余字段逐字保持不变：")
        for name, details in failures:
            print(f"  [{name}]")
            for detail in details:
                print(f"    - {detail}")
        return 2

    score_out: Path | None = None
    if args.deductions:
        scorer = Path(args.scorer or (
            SCRIPTS.parents[1] / "listing-quality-scorer" / "scripts" / "score_quality.py"
        ))
        if not scorer.is_file():
            print(f"ERROR: scorer not found: {scorer}", file=sys.stderr)
            return 1
        score_out = run_dir / "03-write" / "score-result.json"
        # --check-report 是必带的：评分必须吃机检结论，否则超限字段照样能拿高分。
        score_cmd = [
            sys.executable, str(scorer), args.deductions,
            "--out", str(score_out),
            "--check-report", str(check_report_path),
        ]
        score_started = time.perf_counter()
        score_result = subprocess.run(score_cmd, capture_output=True, text=True)
        score_ms = round((time.perf_counter() - score_started) * 1000)
        if score_result.returncode != 0:
            update_stage(
                manifest_path, "write", "failed",
                metrics={"validation_ms": validation_ms, "score_ms": score_ms},
            )
            sys.stderr.write(score_result.stderr)
            return score_result.returncode
        panel = _load_json(str(score_out))["scorePanel"]
        print(f"JSON artifact: {score_out}")
        print(f"Score: overall={panel['overall']} grade={panel['grade']}")

    finalize_cmd = [
        sys.executable, str(SCRIPTS / "finalize_listing.py"),
        "--manifest", manifest_path,
        "--draft", draft_path,
        "--spec", spec_path,
        "--check-report", str(check_report_path),
    ]
    if score_out:
        finalize_cmd += ["--score-result", str(score_out)]
    if args.brand_name:
        finalize_cmd += ["--brand-name", args.brand_name]
    if args.seller_sku:
        finalize_cmd += ["--seller-sku", args.seller_sku]
    finalize_started = time.perf_counter()
    result = subprocess.run(finalize_cmd, capture_output=True, text=True)
    finalize_ms = round((time.perf_counter() - finalize_started) * 1000)
    sys.stdout.write(result.stdout)
    if result.returncode != 0:
        update_stage(
            manifest_path, "write", "failed",
            metrics={"validation_ms": validation_ms, "finalize_ms": finalize_ms},
        )
        sys.stderr.write(result.stderr)
        return result.returncode

    metrics = {"validation_ms": validation_ms, "finalize_ms": finalize_ms}
    if args.deductions:
        metrics["score_ms"] = score_ms
    update_stage(manifest_path, "write", "complete", metrics=metrics)

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="listing-core 编排快捷入口")
    sub = parser.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("start", help="init manifest + 建目录 + 装配 spec")
    start.add_argument("--run-dir", required=True)
    start.add_argument("--mode", required=True, choices=("benchmark", "rewrite", "create"))
    start.add_argument("--profile", default="standard")
    start.add_argument("--keywords", default=None, help="四维分组关键词 JSON；facts_only 可省略")
    start.add_argument(
        "--evidence-mode", choices=("external", "facts_only"), default=None,
        help="省略时，rewrite 且无 keywords 自动使用 facts_only，其余使用 external",
    )
    start.add_argument("--buyer-questions", default=None)
    start.add_argument("--asin", default=None, help="目标 ASIN；用于校验 audit handoff 复用边界")
    start.add_argument("--brands-owned", default="")
    start.add_argument("--brands-competitor", default="")
    start.add_argument("--category-flags", default="")
    start.add_argument("--spec", default=None, help="user_spec JSON")
    start.add_argument("--style-angle", default=None)
    start.add_argument("--marketplace", default="US")
    start.add_argument("--output-language", default=None)
    start.add_argument("--category", default="")
    start.add_argument("--product-type", default="")
    start.add_argument("--audit-handoff", default=None)
    start.add_argument(
        "--banned-terms", default="",
        help="卖家避讳词，逗号分隔；与 keywords.json 的 banned 合流，validate 按违禁词判 fail",
    )

    finish = sub.add_parser("finish", help="validate → finalize（→ 可选评分）")
    finish.add_argument("--run-dir", required=True)
    finish.add_argument("--draft", default=None)
    finish.add_argument("--spec", default=None)
    finish.add_argument("--facts", default=None)
    finish.add_argument("--brand-name", default=None)
    finish.add_argument("--seller-sku", default=None)
    finish.add_argument("--deductions", default=None, help="传了才生成数字评分")
    finish.add_argument("--scorer", default=None, help="score_quality.py 路径（默认同级 skill）")

    args = parser.parse_args()
    raise SystemExit(cmd_start(args) if args.cmd == "start" else cmd_finish(args))


if __name__ == "__main__":
    main()
