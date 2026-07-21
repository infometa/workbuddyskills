#!/usr/bin/env python3
"""
Stop Hook: 静默上报未报告的审计/修复批次。

触发方式: hooks/hooks.json > Stop Hook (与 git_commit_detector.py 并行)
输入: stdin JSON (包含 cwd 等)
输出: 无 stdout 输出 (日志写 stderr)

本脚本始终 exit 0，绝不阻止 Agent 停止。
上报通过 CodeBuddy 代理通道发送（环境变量 CODEBUDDY_SERVICE_PROXY_URL），
由网关注入认证信息。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _common import BATCH_PREFIXES, get_scan_output_dirs

_PREFIX = "report-hook"


def _log(msg: str) -> None:
    print(f"[{_PREFIX}] {msg}", file=sys.stderr)


def _find_unreported_batches(cwd: str) -> list[Path]:
    """查找未上报的审计批次目录（按修改时间倒序，最新在前）。"""
    search_dirs = get_scan_output_dirs(cwd)

    seen = set()
    candidates = []

    for scan_dir in search_dirs:
        if not scan_dir.is_dir():
            continue
        for d in scan_dir.iterdir():
            if not d.is_dir():
                continue
            if not d.name.startswith(BATCH_PREFIXES):
                continue
            # 子目录级去重：get_scan_output_dirs 已做目录级去重，
            # 但符号链接可能导致不同路径指向同一批次目录
            real = d.resolve()
            if real in seen:
                continue
            seen.add(real)

            # 检查 report-sent.json
            sent_file = d / "report-sent.json"
            if sent_file.exists():
                try:
                    data = json.loads(sent_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and data.get("sent") is True:
                        continue  # 已成功上报，跳过
                except Exception:
                    pass  # 文件损坏或无法解析，视为未上报

            # 需要有 summary.json 或 result-*.json 或 merged-scan.json 才值得上报
            has_data = (
                (d / "summary.json").exists()
                or any(d.glob("result-*.json"))
                or (d / "merged-scan.json").exists()
            )
            if has_data:
                candidates.append(d)

    # 按修改时间倒序
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates


def _needs_fix_upload(batch_dir: Path) -> bool:
    """检查批次是否有未上报的修复结果。"""
    fix_report = batch_dir / "fix-report.json"
    if not fix_report.exists():
        return False

    fix_sent = batch_dir / "fix-report-sent.json"
    if fix_sent.exists():
        try:
            data = json.loads(fix_sent.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("sent") is True:
                return False
        except Exception:
            pass
    return True


def main() -> None:
    # 解析 stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        _log("无法解析 stdin JSON，跳过")
        sys.exit(0)

    cwd = hook_input.get("cwd", "")

    # 导入上报模块（延迟导入，减少 Hook 启动时间）
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        from report_upload import upload_report, upload_fix_report
    except ImportError as e:
        _log(f"导入 report_upload 失败: {e}")
        sys.exit(0)

    # 查找未上报批次
    batches = _find_unreported_batches(cwd)
    if not batches:
        _log("无未上报批次，跳过")
        sys.exit(0)

    # 只处理最新的一个批次（效率优先，Stop Hook 有 25s 超时）
    batch_dir = batches[0]
    batch_id = batch_dir.name

    _log(f"发现未上报批次: {batch_id}")

    # 审计上报（Hook 路径仅重试 1 次，超时由 Hook timeout=25s 兜底）
    try:
        ok = upload_report(
            input_path=str(batch_dir),
            audit_batch_id=batch_id,
            cwd=cwd,
            quiet=True,
            max_retries=1,
        )
        if ok:
            _log(f"审计上报成功: {batch_id}")
        else:
            _log(f"审计上报失败: {batch_id}")
    except Exception as e:
        _log(f"审计上报异常: {e}")

    # 修复上报（如果有未上报的 fix-report.json）
    if _needs_fix_upload(batch_dir):
        try:
            ok = upload_fix_report(
                input_path=str(batch_dir),
                audit_batch_id=batch_id,
                cwd=cwd,
                quiet=True,
                max_retries=1,
            )
            if ok:
                _log(f"修复上报成功: {batch_id}")
            else:
                _log(f"修复上报失败: {batch_id}")
        except Exception as e:
            _log(f"修复上报异常: {e}")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log(f"未预期错误: {e}")
        sys.exit(0)  # 始终 exit 0
