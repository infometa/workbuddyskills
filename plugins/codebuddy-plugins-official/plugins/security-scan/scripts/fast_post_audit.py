#!/usr/bin/env python3
"""Fast 模式后处理一键管线（v3.5.5 性能优化）

将 merge-scan → merge-verify → audit_end_time → generate_report → gate_evaluator → gate_reminder
合并为单次 Bash 调用，减少 LLM 往返次数。

用法：
  python3 fast_post_audit.py --batch-dir security-scan-output/diff-fast-xxx

等价于依次执行：
  merge_findings.py merge-scan --batch-dir ... --extra-agents light-inline
  merge_findings.py merge-verify --batch-dir ...
  (写入 .audit_end_time)
  generate_report.py --input ... --format html --output .../report.html
  gate_evaluator.py evaluate --batch-dir ...
  gate_reminder.py notify --batch-dir ... --source scan
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _run_step(name, cmd, timeout=60):
    """执行单个子步骤，返回 (ok, result_dict)。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        # 尝试从 stdout 最后一行解析 JSON（脚本可能在 stdout 输出多行日志 + 最终 JSON）
        stdout_lines = r.stdout.strip().splitlines()
        last_json = None
        for line in reversed(stdout_lines):
            line = line.strip()
            if line.startswith('{'):
                try:
                    last_json = json.loads(line)
                    break
                except (json.JSONDecodeError, ValueError):
                    continue
        return r.returncode == 0, {
            "exit_code": r.returncode,
            "ok": r.returncode == 0,
            "json": last_json,
        }
    except subprocess.TimeoutExpired:
        return False, {"exit_code": -1, "error": f"timeout after {timeout}s"}
    except Exception as e:
        return False, {"exit_code": -1, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Fast 模式后处理一键管线：merge → report → gate → notify"
    )
    parser.add_argument("--batch-dir", required=True,
                        help="扫描批次目录路径")
    parser.add_argument("--extra-agents", default="light-inline",
                        help="merge-scan 额外 agent 名（默认 light-inline）")
    parser.add_argument("--notify-source", default="scan",
                        choices=["scan", "push", "hook-auto"],
                        help="门禁通知来源标记（默认 scan）")
    parser.add_argument("--enforce-language", default="zh",
                        choices=["zh", "none"],
                        help="报告语言校验（默认 zh）")
    args = parser.parse_args()

    batch_dir = args.batch_dir
    batch_path = Path(batch_dir)
    batch_id = batch_path.name
    scripts_dir = Path(__file__).resolve().parent

    if not batch_path.is_dir():
        print(json.dumps({"status": "error", "message": f"batch dir not found: {batch_dir}"}))
        sys.exit(1)

    results = {}
    all_ok = True

    # Step 1: merge-scan
    ok, res = _run_step("merge-scan", [
        sys.executable, str(scripts_dir / "merge_findings.py"),
        "merge-scan", "--batch-dir", batch_dir,
        "--extra-agents", args.extra_agents,
    ])
    results["merge-scan"] = res
    if not ok:
        all_ok = False

    # Step 2: merge-verify
    ok, res = _run_step("merge-verify", [
        sys.executable, str(scripts_dir / "merge_findings.py"),
        "merge-verify", "--batch-dir", batch_dir,
    ])
    results["merge-verify"] = res
    if not ok:
        all_ok = False

    # Step 3: 写入 .audit_end_time
    try:
        end_time = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
        (batch_path / ".audit_end_time").write_text(end_time + "\n")
        results["audit-end-time"] = {"ok": True, "time": end_time}
    except Exception as e:
        results["audit-end-time"] = {"ok": False, "error": str(e)}

    # Step 4: generate_report (HTML)
    report_path = str(batch_path / "report.html")
    ok, res = _run_step("generate-report", [
        sys.executable, str(scripts_dir / "generate_report.py"),
        "--input", batch_dir,
        "--audit-batch-id", batch_id,
        "--format", "html",
        "--output", report_path,
        "--enforce-language", args.enforce_language,
    ])
    results["generate-report"] = res
    # 语言校验失败（exit code 2）不视为致命错误，记录但继续
    if not ok and res.get("exit_code") != 2:
        all_ok = False

    # Step 5: gate_evaluator
    ok, res = _run_step("gate-evaluate", [
        sys.executable, str(scripts_dir / "gate_evaluator.py"),
        "evaluate", "--batch-dir", batch_dir,
    ])
    results["gate-evaluate"] = res

    # Step 6: gate_reminder (best-effort, 不影响 all_ok)
    ok, res = _run_step("gate-notify", [
        sys.executable, str(scripts_dir / "gate_reminder.py"),
        "notify", "--batch-dir", batch_dir,
        "--source", args.notify_source,
    ], timeout=15)
    results["gate-notify"] = res

    output = {
        "status": "completed" if all_ok else "completed_with_errors",
        "steps": results,
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
