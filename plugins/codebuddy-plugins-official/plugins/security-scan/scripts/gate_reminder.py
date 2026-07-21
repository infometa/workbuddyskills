#!/usr/bin/env python3
"""
门禁通知脚本 — 通过企业微信 Webhook 发送门禁告警通知

跨平台：Python3 内置模块 + _common.py，零外部依赖。

子命令：
  1. notify   — 读取 gate-result.json + config.json，发送门禁告警
  2. test     — 发送测试消息，验证 Webhook 配置

设计原则：
  - 发送失败不阻塞流程（best effort）
  - 所有输出为 JSON（stdout），日志到 stderr
  - Webhook URL 仅从 config.json 读取，不硬编码
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    make_logger,
    load_json_file,
    load_merged_config,
    get_git_branch,
    get_git_project_name,
    get_git_project_root,
    resolve_project_root_from_batch_dir,
    stdout_json,
    BEIJING_TZ,
)


# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------

log_info, log_ok, log_warn, log_error = make_logger("gate-notify")

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

SEND_TIMEOUT_SECONDS = 8
SEND_MAX_RETRIES = 2

CONFIG_FILENAME = "config.json"
CONFIG_DIR = ".codebuddy/security-scan"


# ---------------------------------------------------------------------------
# 配置加载
# ---------------------------------------------------------------------------

def _project_root_from_batch_dir(batch_dir=None):
    """从批次目录推断项目根目录，兼容 .codebuddy 新路径和旧 security-scan-output。"""
    if not batch_dir:
        return ""

    candidate = resolve_project_root_from_batch_dir(Path(batch_dir))

    # 校验：必须是 git 仓库，否则回退为空（由调用方使用 cwd）
    git_root = get_git_project_root(candidate)
    return git_root if git_root else ""


def _source_matches_trigger(trigger, source):
    """判断通知触发时机是否匹配当前来源。"""
    allowed_sources = {
        "on_scan": {"scan", "hook-auto"},
        "on_push": {"push"},
        "both": {"scan", "push", "hook-auto"},
    }
    normalized_trigger = trigger if trigger in allowed_sources else "on_scan"
    return source in allowed_sources[normalized_trigger]


def _load_gate_config(config_path=None, project_root=""):
    """加载门禁通知配置（分层合并：项目级 > 用户级）。

    查找顺序:
    1. 指定的 config_path（直接使用，不合并）
    2. 分层合并: 项目级 .codebuddy/security-scan/config.json > 用户级 ~/.codebuddy/security-scan/config.json

    Returns:
        dict: 配置数据，或 None
    """
    if config_path:
        data = load_json_file(config_path)
        if data:
            return data

    # 分层合并
    merged = load_merged_config(project_root)
    return merged if merged else None


def _load_gate_result(batch_dir):
    """加载门禁评估结果。"""
    if not batch_dir:
        return None
    path = Path(batch_dir) / "gate-result.json"
    return load_json_file(str(path))


# ---------------------------------------------------------------------------
# 企业微信 Webhook
# ---------------------------------------------------------------------------

def _build_wecom_markdown(gate_result, project_name="", branch="", source="scan"):
    """构建企业微信 Markdown 消息内容。

    Args:
        gate_result: 门禁评估结果 dict
        project_name: Git 项目名
        branch: Git 分支名
        source: 触发来源 (scan / hook-auto / push)
    """
    status = gate_result.get("gateStatus", "unknown")
    summary = gate_result.get("summary", {})
    violations = gate_result.get("violations", [])
    batch_id = gate_result.get("batchId", "")

    total = summary.get("totalFindings", 0)
    critical = summary.get("criticalRisk", 0)
    high = summary.get("highRisk", 0)
    medium = summary.get("mediumRisk", 0)
    low = summary.get("lowRisk", 0)
    high_conf = summary.get("highConfidenceCount", 0)

    # 状态映射
    status_map = {
        "pass": '<font color="info">通过</font>',
        "warn": '<font color="warning">告警</font>',
        "soft-block": '<font color="warning">未通过</font>',
    }
    status_display = status_map.get(status, status)

    # 触发方式标记
    source_map = {
        "hook-auto": '[自动]',
        "scan": '[手动]',
        "push": '[推送]',
    }
    source_tag = source_map.get(source, '')

    # 构建消息
    lines = [
        f"## Security-Scan 门禁通知 {source_tag}".rstrip(),
        "",
    ]

    if project_name:
        lines.append(f"> 项目: **{project_name}**")
    if branch:
        lines.append(f"> 分支: **{branch}**")
    if batch_id:
        lines.append(f"> 批次: {batch_id}")

    lines.extend([
        "",
        f"**门禁状态**: {status_display}",
        f"**漏洞统计**: {total} 个 (严重:{critical} 高:{high} 中:{medium} 低:{low})",
        f"**高置信度**: {high_conf} 个",
    ])

    if violations:
        lines.append("")
        lines.append("**违规项**:")
        for v in violations[:5]:
            rule = v.get("rule", "?")
            details = v.get("details", "")
            lines.append(f"- [{rule}] {details}")
        if len(violations) > 5:
            lines.append(f"- ... 及其他 {len(violations) - 5} 项")

    # 格式化评估时间为 YYYY-MM-DD HH:MM:SS
    from _common import format_beijing_time
    evaluated_at_raw = gate_result.get("evaluatedAt", "")
    evaluated_at_display = format_beijing_time(evaluated_at_raw) or evaluated_at_raw

    lines.extend([
        "",
        f"**评估时间**: {evaluated_at_display}",
    ])

    return "\n".join(lines)


def _build_wecom_test_message():
    """构建企业微信测试消息。"""
    now = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"## Security-Scan 门禁通知测试\n"
        f"\n"
        f"这是一条测试消息，用于验证企业微信 Webhook 配置是否正确。\n"
        f"\n"
        f"发送时间: {now}\n"
        f"\n"
        f"如果您收到此消息，说明配置正确。"
    )


def _send_wecom(webhook_url, markdown_content):
    """发送企业微信 Webhook 消息。

    Args:
        webhook_url: 企业微信 Webhook URL
        markdown_content: Markdown 格式的消息内容

    Returns:
        tuple: (success: bool, error: str or None)
    """
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content,
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(1, SEND_MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                webhook_url, data=data, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=SEND_TIMEOUT_SECONDS) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                result = json.loads(body)
                errcode = result.get("errcode", 0)
                if errcode != 0:
                    errmsg = result.get("errmsg", "unknown error")
                    return False, f"企业微信返回错误: errcode={errcode}, errmsg={errmsg}"
                return True, None
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}"
            try:
                last_error += f": {e.read().decode('utf-8', errors='ignore')[:200]}"
            except Exception:
                pass
        except urllib.error.URLError as e:
            last_error = f"网络错误: {e.reason}"
        except TimeoutError:
            last_error = "请求超时"
        except Exception as e:
            return False, str(e)

        if attempt < SEND_MAX_RETRIES:
            import time
            time.sleep(1)

    return False, last_error or "发送失败"


# ---------------------------------------------------------------------------
# Git 信息获取
# ---------------------------------------------------------------------------

def _get_git_info(project_root=""):
    """获取当前 Git 项目名和分支名。"""
    return get_git_project_name(project_root) or "", get_git_branch(project_root) or ""


# ---------------------------------------------------------------------------
# 子命令: notify
# ---------------------------------------------------------------------------

def cmd_notify(args):
    """发送门禁告警通知。"""
    project_root = getattr(args, "project_root", None) or _project_root_from_batch_dir(args.batch_dir)

    # 加载配置
    config = _load_gate_config(args.config, project_root)
    if not config:
        log_warn("未找到门禁通知配置 (.codebuddy/security-scan/config.json)，跳过通知")
        stdout_json({"sent": False, "reason": "no_config"})
        return

    notification = config.get("notification", {})
    if not notification.get("enabled", False):
        log_info("通知已禁用，跳过")
        stdout_json({"sent": False, "reason": "disabled"})
        return

    # 检查触发时机
    trigger = notification.get("trigger", "on_scan")
    source = args.source or "scan"
    if not _source_matches_trigger(trigger, source):
        log_info(f"触发时机不匹配 (config={trigger}, source={source})，跳过")
        stdout_json({"sent": False, "reason": "trigger_mismatch"})
        return

    # 加载门禁结果
    gate_result = _load_gate_result(args.batch_dir)
    if not gate_result:
        log_warn("未找到 gate-result.json，跳过通知")
        stdout_json({"sent": False, "reason": "no_gate_result"})
        return

    gate_status = gate_result.get("gateStatus", "unknown")
    if gate_status == "pass":
        log_info("门禁状态为 pass，无需通知")
        stdout_json({"sent": False, "reason": "gate_passed"})
        return

    # 获取项目信息
    project_name, branch = _get_git_info(project_root)

    # 发送通知
    channel = notification.get("channel", "")
    webhook_url = notification.get("webhook_url", "")

    if channel == "wecom" and webhook_url:
        markdown = _build_wecom_markdown(gate_result, project_name, branch, source=source)
        sent, error = _send_wecom(webhook_url, markdown)

        if sent:
            log_ok("企业微信通知发送成功")
            stdout_json({"sent": True, "channel": "wecom"})
        else:
            log_error(f"企业微信通知发送失败: {error}")
            stdout_json({"sent": False, "channel": "wecom", "error": error})
    else:
        log_warn(f"不支持的通知渠道或缺少 webhook_url: channel={channel}")
        stdout_json({"sent": False, "reason": "unsupported_channel"})


# ---------------------------------------------------------------------------
# 子命令: test
# ---------------------------------------------------------------------------

def cmd_test(args):
    """发送测试消息。"""
    webhook_url = args.webhook_url

    if not webhook_url:
        # 尝试从配置中读取
        config = _load_gate_config(args.config)
        if config:
            webhook_url = config.get("notification", {}).get("webhook_url", "")

    if not webhook_url:
        log_error("未指定 Webhook URL，请使用 --webhook-url 参数或先完成配置")
        stdout_json({"sent": False, "reason": "no_webhook_url"})
        return

    log_info(f"发送测试消息到: {webhook_url[:60]}...")
    markdown = _build_wecom_test_message()
    sent, error = _send_wecom(webhook_url, markdown)

    if sent:
        log_ok("测试消息发送成功")
        stdout_json({"sent": True, "channel": "wecom"})
    else:
        log_error(f"测试消息发送失败: {error}")
        stdout_json({"sent": False, "channel": "wecom", "error": error})


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="门禁通知脚本 — 通过企业微信 Webhook 发送门禁告警",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 发送门禁告警通知
  %(prog)s notify --batch-dir .codebuddy/security-scan/runs/project-deep-xxx

  # 发送测试消息
  %(prog)s test --webhook-url "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

  # 从配置文件读取 URL 发送测试
  %(prog)s test
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # notify
    p_notify = subparsers.add_parser("notify", help="发送门禁告警通知")
    p_notify.add_argument("--batch-dir", default=None,
                          help="扫描批次目录路径")
    p_notify.add_argument("--config", default=None,
                          help="config.json 路径")
    p_notify.add_argument("--source", default="scan",
                          choices=["scan", "push", "hook-auto"],
                          help="触发来源: scan（扫描完成）或 push（git push 前）")
    p_notify.add_argument("--project-root", default=None,
                          help="项目根目录（自定义输出位置时显式传入；未传则从批次目录反推 + git 兜底）")
    p_notify.set_defaults(func=cmd_notify)

    # test
    p_test = subparsers.add_parser("test", help="发送测试消息")
    p_test.add_argument("--webhook-url", default=None,
                        help="企业微信 Webhook URL")
    p_test.add_argument("--config", default=None,
                        help="config.json 路径")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        log_error(f"未预期的错误: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
