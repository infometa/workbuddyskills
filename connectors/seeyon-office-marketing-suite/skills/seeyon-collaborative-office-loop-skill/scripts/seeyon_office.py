#!/usr/bin/env python3
"""提供 Seeyon 协同办公的统一安全命令入口。by AI.Coding"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import query_meetings
import query_organization
import send_collaboration
import send_meeting
from session_context import SessionContext

WRITE_COMMANDS = frozenset({"meeting-create", "collaboration-send"})
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
    """把 argparse 退出行为转换为可序列化异常。by AI.Coding"""

    def error(self, message: str) -> None:
        """抛出参数异常，确保最终输出仍是单个 JSON。"""
        raise CommandInputError(message)


def add_service_base_argument(parser: argparse.ArgumentParser) -> None:
    """为子命令增加可选业务服务地址覆盖参数。"""
    parser.add_argument("--base-url", help="覆盖从 OA_BASE_URL 推导的 Seeyon 服务根地址")


def add_write_mode_arguments(parser: argparse.ArgumentParser) -> None:
    """为写命令增加可选预览模式，未指定时直接执行写入。"""
    parser.add_argument("--dry-run", action="store_true", help="只执行必要只读校验并输出预览")


def add_meeting_create_arguments(parser: argparse.ArgumentParser) -> None:
    """注册会议创建业务参数。"""
    add_service_base_argument(parser)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file", type=Path)
    parser.add_argument("--begin-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--emcee")
    parser.add_argument("--recorder")
    parser.add_argument("--conferee", action="append", default=[])
    parser.add_argument("--impart", action="append", default=[])
    parser.add_argument("--meeting-place", default="")
    parser.add_argument("--attachment", action="append", default=[], type=Path)
    parser.add_argument("--current-page-id")
    parser.add_argument("--before-time", type=int, default=10)
    parser.add_argument("--meeting-type-id")
    parser.add_argument("--meeting-type-name", default="普通会议")
    parser.add_argument("--meeting-type")
    parser.add_argument("--project-id", default="-1")
    parser.add_argument("--project-name", default="无")
    parser.add_argument("--send-text-messages", type=int, choices=(0, 1), default=0)
    parser.add_argument("--qr-code-sign", type=int, choices=(0, 1), default=0)
    parser.add_argument("--public", dest="is_public", type=int, choices=(0, 1), default=0)
    parser.add_argument("--sync-to-schedule", type=int, choices=(0, 1), default=0)
    add_write_mode_arguments(parser)


def add_collaboration_arguments(parser: argparse.ArgumentParser) -> None:
    """注册自由协同业务参数。"""
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
    add_write_mode_arguments(parser)


def build_parser() -> JsonArgumentParser:
    """创建包含五个业务子命令的统一参数解析器。"""
    parser = JsonArgumentParser(description="Seeyon 协同办公")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=JsonArgumentParser,
    )

    meeting_list = subparsers.add_parser("meeting-list", help="查询会议列表")
    add_service_base_argument(meeting_list)
    meeting_list.add_argument("--title")
    meeting_list.add_argument("--begin-date")
    meeting_list.add_argument("--end-date")
    meeting_list.add_argument("--list-type", default=query_meetings.DEFAULT_LIST_TYPE)
    meeting_list.add_argument("--page", type=int, default=query_meetings.DEFAULT_PAGE)
    meeting_list.add_argument("--size", type=int, default=query_meetings.DEFAULT_SIZE)

    meeting_detail = subparsers.add_parser("meeting-detail", help="查询会议详情")
    add_service_base_argument(meeting_detail)
    meeting_detail.add_argument("--meeting-id", required=True)
    meeting_detail.add_argument("--proxy-id", default="-1")
    meeting_detail.add_argument("--show-tab", default="true")
    meeting_detail.add_argument(
        "--recommend-menu-id",
        default=query_meetings.DEFAULT_MEETING_VIEW_ARGUMENTS["recommendMenuId"],
    )
    meeting_detail.add_argument("--menu-summary", default="add")
    meeting_detail.add_argument("--portal-id", default="12345678910")

    organization = subparsers.add_parser("organization", help="查询组织机构")
    add_service_base_argument(organization)
    organization.add_argument(
        "entity",
        choices=("accounts", "departments", "members", "posts", "roles", "job-levels", "all"),
    )
    organization.add_argument("--account-id", action="append", default=[])
    organization.add_argument("--name", default="")
    organization.add_argument("--login-name", default="")
    organization.add_argument("--code", default="")
    organization.add_argument("--enable", choices=("true", "false"), default="true")
    organization.add_argument("--bond", type=int, default=1)
    organization.add_argument("--start-page", type=int, default=query_organization.DEFAULT_START_PAGE)
    organization.add_argument("--page-size", type=int, default=query_organization.DEFAULT_PAGE_SIZE)
    organization.add_argument("--max-pages", type=int, default=query_organization.DEFAULT_MAX_PAGES)
    organization.add_argument("--single-page", action="store_true")

    meeting_create = subparsers.add_parser("meeting-create", help="预览或发起会议")
    add_meeting_create_arguments(meeting_create)

    collaboration = subparsers.add_parser("collaboration-send", help="预览或发送自由协同")
    add_collaboration_arguments(collaboration)
    return parser


def validate_pre_auth_args(args: argparse.Namespace) -> Optional[dict[str, Any]]:
    """在认证前校验会导致不必要请求的业务必填参数。"""
    errors: list[str] = []
    if args.command in WRITE_COMMANDS:
        content_count = int(bool(getattr(args, "content", None))) + int(
            bool(getattr(args, "content_file", None))
        )
        if content_count != 1:
            errors.append("--content 与 --content-file 必须且只能提供一个")
    if args.command == "meeting-create" and not args.conferee:
        errors.append("meeting-create 至少需要一个 --conferee")
    if args.command == "collaboration-send":
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
    """递归脱敏认证字段、Cookie 文本和已知秘密值。"""
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
            if isinstance(secret, str) and secret:
                sanitized_text = sanitized_text.replace(secret, "[REDACTED]")
        return sanitized_text
    return value


def normalize_command_result(command: str, result: Any) -> dict[str, Any]:
    """为来源模块结果补齐统一公共字段。"""
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


def dispatch_meeting_list(args: argparse.Namespace, context: SessionContext) -> dict[str, Any]:
    """执行会议列表查询。"""
    return query_meetings.query_meetings(
        session=context.session,
        base_url=context.service_base_url,
        title=args.title,
        begin_date=args.begin_date,
        end_date=args.end_date,
        list_type=args.list_type,
        page=args.page,
        size=args.size,
    )


def dispatch_meeting_detail(args: argparse.Namespace, context: SessionContext) -> dict[str, Any]:
    """执行会议详情查询。"""
    return query_meetings.query_meeting_detail(
        session=context.session,
        base_url=context.service_base_url,
        meeting_id=args.meeting_id,
        proxy_id=args.proxy_id,
        show_tab=args.show_tab,
        recommend_menu_id=args.recommend_menu_id,
        menu_summary=args.menu_summary,
        portal_id=args.portal_id,
    )


def require_account_id(args: argparse.Namespace) -> str:
    """为非单位列表组织查询取得唯一目标单位 ID。"""
    account_ids = list(getattr(args, "account_id", []) or [])
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
        return query_organization.query_posts(
            opener, context.service_base_url, account_id, **common
        )
    if args.entity == "roles":
        return query_organization.query_roles(
            opener, context.service_base_url, account_id, bond=args.bond, **common
        )
    return query_organization.query_job_levels(
        opener, context.service_base_url, account_id, **common
    )


def dispatch_meeting_create(args: argparse.Namespace, context: SessionContext) -> dict[str, Any]:
    """构造会议配置并执行预览或直接写入。"""
    html_content = send_meeting.load_text(args.content, args.content_file)
    config = send_meeting.MeetingConfig(
        base_url=context.service_base_url,
        session_id=context.session_id,
        route=context.route,
        account_id=args.account_id,
        current_username=context.username,
        title=args.title,
        html_content=html_content,
        begin_date=args.begin_date,
        end_date=args.end_date,
        emcee_input=args.emcee,
        recorder_input=args.recorder,
        conferee_inputs=args.conferee,
        impart_inputs=args.impart,
        meeting_place=args.meeting_place,
        attachment_paths=args.attachment,
        current_page_id=args.current_page_id,
        dry_run=args.dry_run,
        before_time=args.before_time,
        meeting_type_id=args.meeting_type_id,
        meeting_type_name=args.meeting_type_name,
        meeting_type=args.meeting_type,
        project_id=args.project_id,
        project_name=args.project_name,
        is_send_text_messages=args.send_text_messages,
        qr_code_sign=args.qr_code_sign,
        is_public=args.is_public,
        sync_to_schedule=args.sync_to_schedule,
    )
    return send_meeting.send_meeting(config)


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
    """构造自由协同配置并执行预览或直接写入。"""
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
    # 默认发送人来自认证账号，因此未提供全精确人员时统一查询组织快照。
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
    """解析、门控、认证并分发一个统一命令。"""
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
        "meeting-list": dispatch_meeting_list,
        "meeting-detail": dispatch_meeting_detail,
        "organization": dispatch_organization,
        "meeting-create": dispatch_meeting_create,
        "collaboration-send": dispatch_collaboration,
    }
    try:
        business_result = handlers[args.command](args, context)
        result = normalize_command_result(args.command, business_result)
    except Exception as exc:
        # 业务模块已提供结构化失败时直接返回；入口只兜底未捕获异常。
        result = {
            "ok": False,
            "command": args.command,
            "completedStages": [],
            "failed_step": "dispatch",
            "error": f"{type(exc).__name__}: {exc}",
        }

    secrets = (context.session_id, context.route or "")
    return sanitize_result(result, secrets)


def main(argv: Optional[list[str]] = None) -> int:
    """输出单个 JSON 文档并返回与业务成功状态对应的退出码。"""
    result = dispatch(argv)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
