#!/usr/bin/env python3
"""使用 Seeyon 登录态查询单位、部门、人员、岗位、角色和职务级别。by AI.Coding"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Optional

DEFAULT_TIMEOUT = 20
DEFAULT_START_PAGE = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 1000

ENDPOINTS = {
    "accounts": {
        "manager_name": "accountManager",
        "nn": "showAccounts",
        "manager_method": "showAccounts",
    },
    "departments": {
        "manager_name": "departmentManager",
        "nn": None,
        "manager_method": "showDepartmentTree",
    },
    "members": {
        "manager_name": "memberManager",
        "nn": "showByAccount",
        "manager_method": "showByAccount",
    },
    "posts": {
        "manager_name": "postManager",
        "nn": "showPostList",
        "manager_method": "showPostList",
    },
    "roles": {
        "manager_name": "roleManager",
        "nn": "findRoles",
        "manager_method": "findRoles",
    },
    "job-levels": {
        "manager_name": "levelManager",
        "nn": "showLevelList",
        "manager_method": "showLevelList",
    },
}


def truncate(text: str, limit: int = 500) -> str:
    """截断过长文本，避免错误信息过大。"""
    return text if len(text) <= limit else text[:limit] + "..."


def optional_int(value: Any) -> Optional[int]:
    """尽可能把服务端数字字段转为 int。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def http_error_payload(exc: urllib.error.HTTPError) -> dict[str, Any]:
    """把 HTTPError 转成统一结构。"""
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return {
        "status": exc.code,
        "reason": exc.reason,
        "body_preview": truncate(body),
    }


def build_cookie_header(session_id: str, route: Optional[str]) -> str:
    """组装登录 Cookie。"""
    cookies = [f"JSESSIONID={session_id}"]
    if route:
        cookies.append(f"route={route}")
    return "; ".join(cookies)


def build_opener(session_id: str, route: Optional[str]) -> urllib.request.OpenerDirector:
    """创建携带登录 Cookie 的 opener。"""
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0"),
        ("Accept", "application/json,text/plain,*/*"),
        ("Cookie", build_cookie_header(session_id, route)),
    ]
    return opener


def build_business_url(base_url: str, entity: str) -> str:
    """按实体接口配置构造 ajax.do URL。"""
    endpoint = ENDPOINTS[entity]
    query: dict[str, str] = {
        "method": "ajaxAction",
        "managerName": endpoint["manager_name"],
    }
    if endpoint["nn"]:
        query["nn"] = endpoint["nn"]
    return f"{base_url.rstrip('/')}/ajax.do?{urllib.parse.urlencode(query)}"


def build_form_body(manager_method: str, arguments: list[dict[str, Any]]) -> bytes:
    """把 managerMethod 和 arguments 编码为 UTF-8 表单。"""
    arguments_json = json.dumps(arguments, ensure_ascii=False, separators=(",", ":"))
    return urllib.parse.urlencode(
        {
            "managerMethod": manager_method,
            "arguments": arguments_json,
        }
    ).encode("utf-8")


def post_form(
    opener: urllib.request.OpenerDirector,
    url: str,
    body: bytes,
) -> tuple[int, str, Any]:
    """发送 POST 表单并解析 JSON 响应。"""
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        method="POST",
    )
    with opener.open(request, timeout=DEFAULT_TIMEOUT) as response:
        text = response.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = text
        return response.getcode(), text, parsed


def build_accounts_arguments(page: int, size: int) -> list[dict[str, Any]]:
    """组装单位查询参数。"""
    return [{"page": page, "size": size}, {}]


def build_departments_arguments(account_id: str) -> list[dict[str, str]]:
    """组装部门树查询参数。"""
    return [{"accountId": account_id}]


def build_members_arguments(
    page: int,
    size: int,
    account_id: str,
    name: str = "",
    login_name: str = "",
    code: str = "",
    enable: str = "true",
) -> list[dict[str, Any]]:
    """组装人员查询参数。"""
    return [
        {"page": page, "size": size},
        {
            "advance_name": name,
            "advance_loginName": login_name,
            "advance_code": code,
            "advance_enable": enable,
            "accountId": account_id,
            "searchType": "advance",
            "newp": page,
        },
    ]


def build_posts_arguments(page: int, size: int, account_id: str) -> list[dict[str, Any]]:
    """组装岗位查询参数。"""
    return [{"page": page, "size": size}, {"accountId": account_id}]


def build_roles_arguments(page: int, size: int, account_id: str, bond: int = 1) -> list[dict[str, Any]]:
    """组装角色查询参数。"""
    return [
        {"page": page, "size": size},
        {"bond": bond, "accountId": account_id, "newp": page},
    ]


def build_job_levels_arguments(page: int, size: int, account_id: str) -> list[dict[str, Any]]:
    """组装职务级别查询参数。"""
    return [{"page": page, "size": size}, {"accountId": account_id}]


def request_entity(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    entity: str,
    arguments: list[dict[str, Any]],
) -> dict[str, Any]:
    """调用一个已配置的组织机构接口。"""
    endpoint = ENDPOINTS[entity]
    url = build_business_url(base_url, entity)
    try:
        status, text, response_body = post_form(
            opener,
            url,
            build_form_body(endpoint["manager_method"], arguments),
        )
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "failed_step": f"query_{entity}",
            "error": http_error_payload(exc),
            "requestUrl": url,
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "failed_step": f"query_{entity}",
            "error": {"reason": str(exc.reason)},
            "requestUrl": url,
        }

    if response_body == "__LOGOUT":
        return {
            "ok": False,
            "failed_step": "session_expired",
            "error": "Seeyon returned __LOGOUT; establish a new authenticated session.",
            "requestUrl": url,
        }
    if isinstance(response_body, str):
        return {
            "ok": False,
            "failed_step": "parse_response",
            "error": "Expected JSON from the organization endpoint.",
            "body_preview": truncate(text),
            "requestUrl": url,
        }
    return {
        "ok": True,
        "status": status,
        "body": response_body,
        "requestUrl": url,
    }


def query_paginated(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    entity: str,
    arguments_builder: Callable[[int, int], list[dict[str, Any]]],
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询并汇总分页组织机构接口。"""
    items: list[Any] = []
    summaries: list[dict[str, Any]] = []
    reported_total: Optional[int] = None
    page = start_page

    for _ in range(max_pages):
        response = request_entity(opener, base_url, entity, arguments_builder(page, page_size))
        if not response.get("ok"):
            return {
                **response,
                "entity": entity,
                "partialItems": items,
                "fetched": len(items),
                "pagesFetched": len(summaries),
            }
        body = response["body"]
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            return {
                "ok": False,
                "failed_step": "parse_response",
                "entity": entity,
                "error": "Expected response.data to be an array for a paginated endpoint.",
                "body_preview": truncate(json.dumps(body, ensure_ascii=False)),
                "partialItems": items,
                "fetched": len(items),
                "pagesFetched": len(summaries),
            }

        page_items = body["data"]
        items.extend(page_items)
        current_total = optional_int(body.get("total"))
        if current_total is not None:
            reported_total = current_total
        reported_pages = optional_int(body.get("pages"))
        summaries.append(
            {
                "requestPage": page,
                "responsePage": optional_int(body.get("page")),
                "responseSize": optional_int(body.get("size")),
                "count": len(page_items),
                "total": current_total,
                "pages": reported_pages,
                "status": response["status"],
            }
        )

        if single_page or not page_items:
            break
        if reported_total is not None and len(items) >= reported_total:
            break
        if reported_pages is not None and reported_pages > 0 and page >= reported_pages:
            break
        if len(page_items) < page_size:
            break
        page += 1
    else:
        return {
            "ok": False,
            "failed_step": "pagination_limit",
            "entity": entity,
            "error": f"Reached max_pages={max_pages} before the last page was detected.",
            "partialItems": items,
            "fetched": len(items),
            "pagesFetched": len(summaries),
            "pageSummaries": summaries,
        }

    return {
        "ok": True,
        "entity": entity,
        "items": items,
        "fetched": len(items),
        "total": reported_total if reported_total is not None else len(items),
        "pagesFetched": len(summaries),
        "pageSummaries": summaries,
    }


def query_accounts(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询全部单位。"""
    return query_paginated(
        opener,
        base_url,
        "accounts",
        build_accounts_arguments,
        start_page,
        page_size,
        max_pages,
        single_page,
    )


def query_departments(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_id: str,
) -> dict[str, Any]:
    """查询指定单位的部门树。"""
    response = request_entity(opener, base_url, "departments", build_departments_arguments(account_id))
    if not response.get("ok"):
        return {**response, "entity": "departments", "accountId": account_id}
    return {
        "ok": True,
        "entity": "departments",
        "accountId": account_id,
        "departmentTree": response["body"],
        "requestUrl": response["requestUrl"],
    }


def query_members(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_id: str,
    name: str = "",
    login_name: str = "",
    code: str = "",
    enable: str = "true",
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询指定单位的人员。"""
    builder = lambda page, size: build_members_arguments(
        page, size, account_id, name, login_name, code, enable
    )
    result = query_paginated(
        opener, base_url, "members", builder, start_page, page_size, max_pages, single_page
    )
    return {**result, "accountId": account_id}


def query_posts(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_id: str,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询指定单位的岗位。"""
    builder = lambda page, size: build_posts_arguments(page, size, account_id)
    result = query_paginated(
        opener, base_url, "posts", builder, start_page, page_size, max_pages, single_page
    )
    return {**result, "accountId": account_id}


def query_collaboration_snapshot(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_id: str,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> dict[str, Any]:
    """查询自由协同人员解析所需的部门、人员和岗位快照。"""
    organization = {
        "departments": query_departments(opener, base_url, account_id),
        "members": query_members(
            opener,
            base_url,
            account_id,
            start_page=start_page,
            page_size=page_size,
            max_pages=max_pages,
        ),
        "posts": query_posts(
            opener,
            base_url,
            account_id,
            start_page,
            page_size,
            max_pages,
        ),
    }
    failed_entities = [
        entity for entity, result in organization.items() if not result.get("ok")
    ]
    if failed_entities:
        # 任何组织实体不完整都会使人员 ID关联不可靠，因此整体失败。
        return {
            "ok": False,
            "complete": False,
            "failed_step": "query_organization",
            "failedEntities": failed_entities,
            "accountIds": [account_id],
            "organizations": {account_id: organization},
        }
    return {
        "ok": True,
        "complete": True,
        "accountIds": [account_id],
        "organizations": {account_id: organization},
    }


def query_roles(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_id: str,
    bond: int = 1,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询指定单位的角色。"""
    builder = lambda page, size: build_roles_arguments(page, size, account_id, bond)
    result = query_paginated(
        opener, base_url, "roles", builder, start_page, page_size, max_pages, single_page
    )
    return {**result, "accountId": account_id}


def query_job_levels(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_id: str,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询指定单位的职务级别。"""
    builder = lambda page, size: build_job_levels_arguments(page, size, account_id)
    result = query_paginated(
        opener, base_url, "job-levels", builder, start_page, page_size, max_pages, single_page
    )
    return {**result, "accountId": account_id}


def extract_account_ids(items: list[Any]) -> list[str]:
    """从单位列表中提取 id 或 accountId，并保持原顺序去重。"""
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get("id") or item.get("accountId")
        if value is None:
            continue
        account_id = str(value)
        if account_id not in seen:
            seen.add(account_id)
            result.append(account_id)
    return result


def query_all(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    account_ids: list[str],
    name: str = "",
    login_name: str = "",
    code: str = "",
    enable: str = "true",
    bond: int = 1,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    single_page: bool = False,
) -> dict[str, Any]:
    """查询单位，并逐单位汇总部门、人员、岗位、角色和职务级别。"""
    accounts = query_accounts(opener, base_url, start_page, page_size, max_pages, single_page)
    if not accounts.get("ok"):
        return {"ok": False, "failed_step": "query_accounts", "accounts": accounts}

    targets = account_ids or extract_account_ids(accounts["items"])
    if not targets:
        return {
            "ok": False,
            "failed_step": "resolve_account_ids",
            "error": "No account ID was provided or found in account records (id/accountId).",
            "accounts": accounts,
        }

    organizations: dict[str, dict[str, Any]] = {}
    for account_id in targets:
        organizations[account_id] = {
            "departments": query_departments(opener, base_url, account_id),
            "members": query_members(
                opener,
                base_url,
                account_id,
                name,
                login_name,
                code,
                enable,
                start_page,
                page_size,
                max_pages,
                single_page,
            ),
            "posts": query_posts(
                opener, base_url, account_id, start_page, page_size, max_pages, single_page
            ),
            "roles": query_roles(
                opener,
                base_url,
                account_id,
                bond,
                start_page,
                page_size,
                max_pages,
                single_page,
            ),
            "jobLevels": query_job_levels(
                opener, base_url, account_id, start_page, page_size, max_pages, single_page
            ),
        }

    ok = all(
        result.get("ok")
        for organization in organizations.values()
        for result in organization.values()
    )
    return {
        "ok": ok,
        "complete": ok,
        "accounts": accounts,
        "accountIds": targets,
        "organizations": organizations,
    }


def validate_common_args(start_page: int, page_size: int, max_pages: int) -> Optional[dict[str, Any]]:
    """校验分页参数。"""
    if start_page < 1:
        return {"ok": False, "failed_step": "validate_args", "error": "start_page must be >= 1"}
    if page_size < 1:
        return {"ok": False, "failed_step": "validate_args", "error": "page_size must be >= 1"}
    if max_pages < 1:
        return {"ok": False, "failed_step": "validate_args", "error": "max_pages must be >= 1"}
    return None


def main() -> int:
    """读取参数并执行对应组织机构查询。"""
    parser = argparse.ArgumentParser(description="Query Seeyon organization information")
    parser.add_argument(
        "entity",
        choices=("accounts", "departments", "members", "posts", "roles", "job-levels", "all"),
    )
    parser.add_argument("--base-url", default=os.getenv("SEIYON_BASE_URL"), help="Seeyon base URL")
    parser.add_argument("--session-id", default=os.getenv("SEIYON_SESSION_ID"), help="登录 skill 返回的 sessionId")
    parser.add_argument("--jsessionid", dest="session_id_alias", help="兼容旧参数")
    parser.add_argument("--route", default=os.getenv("SEIYON_ROUTE"), help="登录 skill 返回的 route，可为空")
    parser.add_argument("--account-id", action="append", default=[], help="单位 ID；all 模式可重复传入")
    parser.add_argument("--name", default="", help="人员姓名筛选")
    parser.add_argument("--login-name", default="", help="人员登录名筛选")
    parser.add_argument("--code", default="", help="人员编码筛选")
    parser.add_argument("--enable", choices=("true", "false"), default="true", help="人员启用状态")
    parser.add_argument("--bond", type=int, default=1, help="角色 bond 参数，默认 1")
    parser.add_argument("--start-page", type=int, default=DEFAULT_START_PAGE)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--single-page", action="store_true")
    args = parser.parse_args()

    session_id = args.session_id or args.session_id_alias
    missing = [
        name
        for name, value in {"base_url": args.base_url, "session_id": session_id}.items()
        if not value
    ]
    if missing:
        output = {
            "ok": False,
            "failed_step": "validate_args",
            "error": f"Missing required values: {', '.join(missing)}",
        }
    elif (validation_error := validate_common_args(args.start_page, args.page_size, args.max_pages)):
        output = validation_error
    elif args.entity in {"departments", "members", "posts", "roles", "job-levels"} and len(args.account_id) != 1:
        output = {
            "ok": False,
            "failed_step": "validate_args",
            "error": f"{args.entity} requires exactly one --account-id.",
        }
    else:
        opener = build_opener(session_id, args.route)
        common = (args.start_page, args.page_size, args.max_pages, args.single_page)
        if args.entity == "accounts":
            output = query_accounts(opener, args.base_url, *common)
        elif args.entity == "departments":
            output = query_departments(opener, args.base_url, args.account_id[0])
        elif args.entity == "members":
            output = query_members(
                opener,
                args.base_url,
                args.account_id[0],
                args.name,
                args.login_name,
                args.code,
                args.enable,
                *common,
            )
        elif args.entity == "posts":
            output = query_posts(opener, args.base_url, args.account_id[0], *common)
        elif args.entity == "roles":
            output = query_roles(opener, args.base_url, args.account_id[0], args.bond, *common)
        elif args.entity == "job-levels":
            output = query_job_levels(opener, args.base_url, args.account_id[0], *common)
        else:
            output = query_all(
                opener,
                args.base_url,
                args.account_id,
                args.name,
                args.login_name,
                args.code,
                args.enable,
                args.bond,
                *common,
            )

        output = {**output, "sessionId": session_id, "route": args.route}

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
