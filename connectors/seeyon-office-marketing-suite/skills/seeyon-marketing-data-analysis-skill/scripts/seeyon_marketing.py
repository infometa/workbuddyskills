#!/usr/bin/env python3
"""提供 Seeyon 营销数据分析的统一安全命令入口。by AI.Coding"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import query_organization
import query_sales_orders
import send_collaboration
from session_context import SessionContext

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "cookies",
        "jsessionid",
        "password",
        "route",
        "sessionid",
        "session_id",
        "token",
        "username",
    }
)
SECRET_TEXT_PATTERN = re.compile(
    r"(?i)(authorization|cookie|jsessionid|password|route|sessionid|token)\s*[:=]\s*[^;,\s]+"
)


class CommandInputError(ValueError):
    """统一 CLI 参数无法解析时抛出。by AI.Coding"""


class JsonArgumentParser(argparse.ArgumentParser):
    """把 argparse 的进程退出转换为 JSON 可表达的异常。by AI.Coding"""

    def error(self, message: str) -> None:
        """抛出参数异常，确保入口始终输出单个 JSON。"""
        raise CommandInputError(message)


def add_service_base_argument(parser: argparse.ArgumentParser) -> None:
    """为子命令增加可选业务服务地址覆盖参数。"""
    parser.add_argument("--base-url", help="覆盖从 OA_BASE_URL 推导的 Seeyon 服务根地址")


def add_organization_arguments(parser: argparse.ArgumentParser) -> None:
    """注册组织机构查询参数。"""
    add_service_base_argument(parser)
    parser.add_argument(
        "entity",
        choices=("accounts", "departments", "members", "posts", "roles", "job-levels", "all"),
    )
    parser.add_argument("--account-id", action="append", default=[])
    parser.add_argument("--name", default="")
    parser.add_argument("--login-name", default="")
    parser.add_argument("--code", default="")
    parser.add_argument("--enable", choices=("true", "false"), default="true")
    parser.add_argument("--bond", type=int, default=1)
    parser.add_argument("--start-page", type=int, default=query_organization.DEFAULT_START_PAGE)
    parser.add_argument("--page-size", type=int, default=query_organization.DEFAULT_PAGE_SIZE)
    parser.add_argument("--max-pages", type=int, default=query_organization.DEFAULT_MAX_PAGES)
    parser.add_argument("--single-page", action="store_true")


def add_collaboration_arguments(parser: argparse.ArgumentParser) -> None:
    """注册营销分析自由协同参数。"""
    add_service_base_argument(parser)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file", type=Path)
    parser.add_argument("--sender-json")
    parser.add_argument("--sender-login-name")
    parser.add_argument("--recipient-json", action="append", default=[])
    parser.add_argument("--recipient-login-name", action="append", default=[])
    parser.add_argument("--organization-data", type=Path)
    parser.add_argument("--process-xml-file", type=Path)
    parser.add_argument("--attachment", action="append", default=[], type=Path)
    parser.add_argument("--current-page-id")
    parser.add_argument("--dry-run", action="store_true", help="只校验并预览，不执行 OA 写入")


def build_parser() -> JsonArgumentParser:
    """创建包含三个业务子命令的统一参数解析器。"""
    parser = JsonArgumentParser(description="Seeyon 营销数据分析")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=JsonArgumentParser,
    )

    order_query = subparsers.add_parser("order-query", help="查询销售订单报表")
    add_service_base_argument(order_query)
    order_query.add_argument(
        "--report-name",
        default=query_sales_orders.DEFAULT_REPORT_NAME,
        help="销售订单报表名称",
    )

    organization = subparsers.add_parser("organization", help="查询组织机构")
    add_organization_arguments(organization)

    collaboration = subparsers.add_parser("collaboration-send", help="预览或发送营销分析协同")
    add_collaboration_arguments(collaboration)
    return parser


def validate_pre_auth_args(args: argparse.Namespace) -> Optional[dict[str, Any]]:
    """在认证前校验会导致不必要 OA 请求的业务参数。"""
    errors: list[str] = []
    if args.command == "collaboration-send":
        content_count = int(bool(args.content)) + int(bool(args.content_file))
        if content_count != 1:
            errors.append("--content 与 --content-file 必须且只能提供一个")
        if not args.recipient_json and not args.recipient_login_name:
            errors.append("collaboration-send 至少需要一个接收人")
    if args.command == "organization" and args.entity not in {"accounts", "all"}:
        if len(args.account_id) != 1:
            errors.append("该组织查询必须且只能提供一个 --account-id")
    if not errors:
        return None
    return {
        "ok": False,
        "command": args.command,
        "completedStages": [],
        "failed_step": "validate_args",
        "error": "；".join(errors),
    }


def sanitize_result(value: Any, secret_values: tuple[str, ...] = ()) -> Any:
    """递归脱敏认证字段、Cookie 文本和当前命令的已知秘密值。"""
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_result(item, secret_values)
        return sanitized
    if isinstance(value, list):
        return [sanitize_result(item, secret_values) for item in value]
    if isinstance(value, tuple):
        return [sanitize_result(item, secret_values) for item in value]
    if isinstance(value, str):
        sanitized_text = SECRET_TEXT_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        for secret in secret_values:
            if secret:
                sanitized_text = sanitized_text.replace(secret, "[REDACTED]")
        return sanitized_text
    return value


def normalize_command_result(command: str, result: Any) -> dict[str, Any]:
    """为业务模块结果补齐统一公共字段。"""
    if not isinstance(result, dict):
        result = {
            "ok": False,
            "failed_step": "parse_business_response",
            "error": "业务模块未返回 JSON 对象",
        }
    normalized = dict(result)
    normalized["command"] = command
    normalized.setdefault("completedStages", ["query"] if normalized.get("ok") else [])
    if not normalized.get("ok"):
        normalized.setdefault("failed_step", "business")
        normalized.setdefault("error", "业务命令未取得明确成功证据")
    return normalized


def dispatch_order_query(args: argparse.Namespace, context: SessionContext) -> dict[str, Any]:
    """使用统一认证上下文查询销售订单报表。"""
    return query_sales_orders.query_sales_orders(
        base_url=context.service_base_url,
        session_id=context.session_id,
        route=context.route,
        report_name=args.report_name,
    )


def require_account_id(args: argparse.Namespace) -> str:
    """为非单位列表组织查询取得唯一目标单位 ID。"""
    account_ids = list(args.account_id or [])
    if len(account_ids) != 1:
        raise CommandInputError("该组织查询必须且只能提供一个 --account-id")
    return account_ids[0]


def dispatch_organization(args: argparse.Namespace, context: SessionContext) -> dict[str, Any]:
    """按实体类型执行组织查询。"""
    opener = query_organization.build_opener(context.session_id, context.route)
    common = {
        "start_page": args.start_page,
        "page_size": args.page_size,
        "max_pages": args.max_pages,
        "single_page": args.single_page,
    }
    if args.entity == "accounts":
        return query_organization.query_accounts(opener, context.service_base_url, **common)
    if args.entity == "all":
        return query_organization.query_all(
            opener,
            context.service_base_url,
            account_ids=args.account_id,
            name=args.name,
            login_name=args.login_name,
            code=args.code,
            enable=args.enable,
            bond=args.bond,
            **common,
        )

    account_id = require_account_id(args)
    if args.entity == "departments":
        return query_organization.query_departments(opener, context.service_base_url, account_id)
    if args.entity == "members":
        return query_organization.query_members(
            opener,
            context.service_base_url,
            account_id,
            name=args.name,
            login_name=args.login_name,
            code=args.code,
            enable=args.enable,
            **common,
        )
    if args.entity == "posts":
        return query_organization.query_posts(opener, context.service_base_url, account_id, **common)
    if args.entity == "roles":
        return query_organization.query_roles(
            opener,
            context.service_base_url,
            account_id,
            bond=args.bond,
            **common,
        )
    return query_organization.query_job_levels(
        opener,
        context.service_base_url,
        account_id,
        **common,
    )


def load_collaboration_snapshot(
    args: argparse.Namespace,
    context: SessionContext,
) -> dict[str, Any]:
    """读取显式快照或使用当前登录态查询协同人员快照。"""
    if args.organization_data:
        return send_collaboration.load_organization_snapshot(args.organization_data)
    opener = query_organization.build_opener(context.session_id, context.route)
    result = query_organization.query_collaboration_snapshot(
        opener,
        context.service_base_url,
        args.account_id,
    )
    if not result.get("ok"):
        raise CommandInputError("自由协同参与者所需的组织快照查询失败")
    return result


def dispatch_collaboration(args: argparse.Namespace, context: SessionContext) -> dict[str, Any]:
    """构造营销分析自由协同配置并执行预览或直接写入。"""
    html_content = send_collaboration.load_text(args.content, args.content_file, "HTML 正文")
    sender_exact = (
        send_collaboration.parse_json_argument(args.sender_json, "--sender-json")
        if args.sender_json
        else None
    )
    recipient_exact_values = [
        send_collaboration.parse_json_argument(value, "--recipient-json")
        for value in args.recipient_json
    ]
    process_xml = (
        send_collaboration.load_text(None, args.process_xml_file, "流程 XML")
        if args.process_xml_file
        else None
    )
    # 登录名解析需要完整组织快照；全精确 JSON 路径无需额外组织查询。
    needs_snapshot = sender_exact is None or bool(args.recipient_login_name)
    organization_snapshot = load_collaboration_snapshot(args, context) if needs_snapshot else None
    config = send_collaboration.CollaborationConfig(
        base_url=context.service_base_url,
        session_id=context.session_id,
        route=context.route,
        subject=args.subject,
        html_content=html_content,
        sender_exact=sender_exact,
        sender_login_name=args.sender_login_name or context.username,
        recipient_exact_values=recipient_exact_values,
        recipient_login_names=args.recipient_login_name,
        account_id=args.account_id,
        organization_snapshot=organization_snapshot,
        process_xml=process_xml,
        attachment_paths=args.attachment,
        current_page_id=args.current_page_id,
        dry_run=args.dry_run,
    )
    return send_collaboration.send_collaboration(config)


def dispatch(
    argv: Optional[list[str]] = None,
    context_factory: Callable[..., SessionContext] = SessionContext.from_env,
) -> dict[str, Any]:
    """解析、认证并分发一个营销数据分析命令。"""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except CommandInputError as exc:
        return sanitize_result(
            {
                "ok": False,
                "command": None,
                "completedStages": [],
                "failed_step": "validate_args",
                "error": str(exc),
            }
        )

    argument_error = validate_pre_auth_args(args)
    if argument_error is not None:
        return argument_error

    try:
        context = context_factory(base_url_override=getattr(args, "base_url", None))
    except Exception as exc:
        # 认证异常统一脱敏，禁止透传可能包含凭据的第三方错误文本。
        return sanitize_result(
            {
                "ok": False,
                "command": args.command,
                "completedStages": [],
                "failed_step": "authenticate",
                "error": str(exc),
            }
        )

    handlers = {
        "order-query": dispatch_order_query,
        "organization": dispatch_organization,
        "collaboration-send": dispatch_collaboration,
    }
    try:
        business_result = handlers[args.command](args, context)
        result = normalize_command_result(args.command, business_result)
    except Exception as exc:
        # 业务模块未捕获异常在统一边界内转换，不中断 JSON 输出。
        result = {
            "ok": False,
            "command": args.command,
            "completedStages": [],
            "failed_step": "dispatch",
            "error": f"{type(exc).__name__}: {exc}",
        }

    return sanitize_result(result, (context.session_id, context.route or ""))


def main(argv: Optional[list[str]] = None) -> int:
    """输出单个 JSON 文档并返回与业务成功状态对应的退出码。"""
    result = dispatch(argv)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
