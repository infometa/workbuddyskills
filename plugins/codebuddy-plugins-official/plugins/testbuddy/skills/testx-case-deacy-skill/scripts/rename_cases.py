#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rename_cases.py：批量重命名测试用例/目录脚本
- 目录重命名: 使用 UpdateFolder 接口 (PUT .../folders/{uid})，这是目录的专用更新接口
- 用例重命名: 使用 PatchCase 接口 (PATCH .../cases/{uid})

参考实际API源码:
  - apps/fc/testx/srcs/case/core/api/case.go → UpdateFolder / PatchCase
  - protocols/fc/testx/case/case_api.proto → HTTP路由映射

请求方式参考: apps/fc/testx/srcs/mcp/tools/common.py

用法:
  # 通过 --uids 和 --name-prefix/--name-map 重命名
  python rename_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --token <token> --uids uid1,uid2 --name-prefix "[空-待删除]"
  # 通过 --input 文件批量重命名（文件中需包含 uid + new_name 字段，可选 is_folder 字段）
  python rename_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --token <token> --input <file.json>
  # 通过 stdin 传入
  echo '[{"uid":"uid1","new_name":"新名称","is_folder":true}]' | python rename_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --token <token>

参数说明:
  --uids          逗号分隔的UID列表（配合 --name-prefix 使用）
  --name-prefix   重命名前缀，将在原名称前添加该前缀（配合 --uids 使用）
  --input         输入JSON文件路径（需包含 uid + new_name 字段，可选 is_folder）
  --is-folder     当使用 --uids 时指定这些UID都是目录（默认是目录）
  --dry-run       仅预览，不执行
"""

import argparse
import io
import json
import os
import re
import sys
import time

try:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import HTTPError, Request, URLError, urlopen  # type: ignore[import-not-found]


# API配置
DEFAULT_BASE_URL = "http://openapi.zhiyan.woa.com"
# 请求间隔（秒），避免限流
REQUEST_INTERVAL = 0.2


def get_token(token_arg):
    """获取访问令牌"""
    if not token_arg:
        print(
            json.dumps(
                {"status": "error", "msg": "未找到访问令牌，请通过 --token 参数传入"}, ensure_ascii=False, indent=2
            )
        )
        sys.exit(1)
    return token_arg


def sanitize_json_string(input_str):
    """预处理JSON字符串"""
    input_str = input_str.strip()
    input_str = re.sub(r"^```json\s*", "", input_str)
    input_str = re.sub(r"^```\s*", "", input_str)
    input_str = re.sub(r"\s*```$", "", input_str)
    input_str = re.sub(r"//.*?$", "", input_str, flags=re.MULTILINE)
    return input_str.strip()


def build_update_folder_url(base_url, namespace, repo_uid, repo_version_uid, folder_uid):
    """
    构建 UpdateFolder 接口的URL（用于重命名目录）
    proto定义: PUT /v1/namespaces/{namespace}/repos/{folder.repo_uid}/versions/{folder.repo_version_uid}/folders/{folder.uid}
    实际API: case.go → UpdateFolder()
    """
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/folders/{uid}".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
        uid=folder_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def build_patch_case_url(base_url, namespace, repo_uid, repo_version_uid, case_uid):
    """
    构建 PatchCase 接口的URL（用于重命名用例）
    proto定义: PATCH /v1/namespaces/{namespace}/repos/{repo_uid}/versions/{repo_version_uid}/cases/{case.uid}
    实际API: case.go → PatchCase()
    """
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/{uid}".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
        uid=case_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def make_request(url, body, token, namespace, method="PUT"):
    """
    执行HTTP请求 - 对齐MCP tools/common.py 中 make_request 的header格式
    认证方式: token header + x-shipyard-ns
    """
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data)
    req.get_method = lambda: method
    req.add_header("Content-Type", "application/json")
    req.add_header("token", token)
    if namespace:
        req.add_header("x-shipyard-ns", namespace)

    try:
        resp = urlopen(req, timeout=30)
        resp_data = resp.read().decode("utf-8")
        return json.loads(resp_data)
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {"error": {"code": e.code, "message": "HTTP错误: {} {}".format(e.code, error_body[:500])}}
    except URLError as e:
        return {"error": {"message": "网络错误: {}".format(str(e))}}
    except Exception as e:
        return {"error": {"message": "请求异常: {}".format(str(e))}}


def rename_single_item(namespace, repo_uid, repo_version_uid, uid, new_name, is_folder, token, base_url):
    """
    重命名单个目录/用例的核心函数。

    目录: 使用 UpdateFolder 接口 (PUT .../folders/{uid})
      - body 为 Folder 对象：{"Uid": ..., "Name": ..., "RepoUid": ..., "RepoVersionUid": ...}
      - 参考 case.go → UpdateFolder(): 接收 FolderRequest{Folder}，更新目录名称
    用例: 使用 PatchCase 接口 (PATCH .../cases/{uid})
      - body 为 Case 对象：{"Uid": ..., "Name": ...}
      - 参考 case.go → PatchCase(): 按 fields 列表部分更新用例

    返回:
      {"status": "success", "uid": ..., "new_name": ..., "is_folder": ...}
      {"status": "error", "uid": ..., "msg": ...}
    """
    if is_folder:
        url = build_update_folder_url(base_url, namespace, repo_uid, repo_version_uid, uid)
        # UpdateFolder 的 body 是 Folder 对象（proto: FolderRequest.folder）
        # 参考 valid.go → validInFolder(): 只保存 Name, Description, Owners, ParentID 等特定字段
        body = {
            "Uid": uid,
            "Name": new_name,
            "RepoUid": repo_uid,
            "RepoVersionUid": repo_version_uid,
        }
        method = "PUT"
    else:
        url = build_patch_case_url(base_url, namespace, repo_uid, repo_version_uid, uid)
        body = {
            "Uid": uid,
            "Name": new_name,
        }
        method = "PATCH"

    resp = make_request(url, body, token, namespace, method=method)

    error = resp.get("error") or resp.get("Error")
    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            return {"status": "error", "uid": uid, "new_name": new_name, "is_folder": is_folder, "msg": msg}

    return {"status": "success", "uid": uid, "new_name": new_name, "is_folder": is_folder}


def batch_rename(
    namespace,
    repo_uid,
    repo_version_uid,
    rename_items,
    base_url=DEFAULT_BASE_URL,
    token_arg=None,
):
    """
    批量重命名：循环编排，逐个调用 rename_single_item()。
    每次请求间隔 REQUEST_INTERVAL 秒，避免限流。

    rename_items: [{"uid": "xxx", "new_name": "yyy", "is_folder": true/false}, ...]
    - is_folder=True: 使用 UpdateFolder (PUT) 接口
    - is_folder=False: 使用 PatchCase (PATCH) 接口

    返回汇总结果。
    """
    if not rename_items:
        return {"status": "error", "msg": "重命名列表为空"}

    token = get_token(token_arg)

    results = []
    success_count = 0
    fail_count = 0

    for idx, item in enumerate(rename_items):
        uid = item.get("uid") or item.get("Uid") or ""
        new_name = item.get("new_name") or item.get("NewName") or ""
        is_folder = item.get("is_folder", True)  # 默认为目录

        if not uid:
            results.append({"status": "error", "uid": "", "index": idx, "msg": "缺少uid字段"})
            fail_count += 1
            continue

        if not new_name:
            results.append({"status": "error", "uid": uid, "index": idx, "msg": "缺少new_name字段"})
            fail_count += 1
            continue

        result = rename_single_item(namespace, repo_uid, repo_version_uid, uid, new_name, is_folder, token, base_url)
        result["index"] = idx
        results.append(result)

        if result["status"] == "success":
            success_count += 1
        else:
            fail_count += 1

        # 请求间隔，避免限流
        if idx < len(rename_items) - 1:
            time.sleep(REQUEST_INTERVAL)

    return {
        "status": "success" if fail_count == 0 else "partial",
        "total_requested": len(rename_items),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
    }


def load_rename_items(args):
    """
    从各种来源加载重命名列表。
    支持三种输入方式：
      1. --uids + --name-prefix: 对指定UID添加前缀重命名
      2. --input 文件: 包含 uid + new_name 的JSON数组
      3. stdin: 同 --input 格式

    返回: [{"uid": "xxx", "new_name": "yyy", "is_folder": true/false}, ...]
    """
    items = []
    default_is_folder = getattr(args, "is_folder", True)

    # 方式1: --uids + --name-prefix（仅前缀模式，new_name 在外部由 dry-run 或执行时拼接）
    if args.uids:
        uids = [u.strip() for u in args.uids.split(",") if u.strip()]
        if args.name_prefix:
            # 前缀模式：new_name 先留空，由调用方补充
            for uid in uids:
                items.append({"uid": uid, "name_prefix": args.name_prefix, "is_folder": default_is_folder})
        else:
            # 无前缀，需要从其他途径获取 new_name
            for uid in uids:
                items.append({"uid": uid, "is_folder": default_is_folder})
        return items

    # 方式2: --input 文件
    if args.input:
        if not os.path.exists(args.input):
            print(
                json.dumps(
                    {"status": "error", "msg": "输入文件不存在: {}".format(args.input)}, ensure_ascii=False, indent=2
                )
            )
            sys.exit(1)
        with io.open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _parse_rename_data(data, default_is_folder)

    # 方式3: stdin
    if not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()
        if input_data:
            input_data = sanitize_json_string(input_data)
            data = json.loads(input_data)
            return _parse_rename_data(data, default_is_folder)

    return items


def _parse_rename_data(data, default_is_folder=True):
    """解析输入数据为重命名列表"""
    items = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                uid = item.get("uid") or item.get("Uid") or ""
                new_name = item.get("new_name") or item.get("NewName") or item.get("name") or item.get("Name") or ""
                name_prefix = item.get("name_prefix") or item.get("NamePrefix") or ""
                # 支持通过 is_folder 字段区分目录/用例
                is_folder = item.get("is_folder", item.get("IsFolder", default_is_folder))
                if uid:
                    entry = {"uid": uid, "is_folder": is_folder}
                    if new_name:
                        entry["new_name"] = new_name
                    if name_prefix:
                        entry["name_prefix"] = name_prefix
                    items.append(entry)
    elif isinstance(data, dict):
        if "items" in data:
            return _parse_rename_data(data["items"], default_is_folder)
        uid = data.get("uid") or data.get("Uid") or ""
        new_name = data.get("new_name") or data.get("NewName") or ""
        is_folder = data.get("is_folder", data.get("IsFolder", default_is_folder))
        if uid:
            items.append({"uid": uid, "new_name": new_name, "is_folder": is_folder})
    return items


def resolve_new_names(items, search_func=None):
    """
    解析最终的 new_name：
    - 如果 item 已有 new_name，直接使用
    - 如果 item 有 name_prefix 但无 new_name，需要查原名称后拼接前缀
    - search_func: 可选的回调函数，用于根据uid查询原名称

    注意：在 name_prefix 模式下，如果没有提供 search_func，
    则 new_name 将为 "{prefix}{uid}"（uid作为占位符）
    """
    resolved = []
    for item in items:
        uid = item.get("uid", "")
        new_name = item.get("new_name", "")
        name_prefix = item.get("name_prefix", "")
        original_name = item.get("original_name", "")
        is_folder = item.get("is_folder", True)

        if new_name:
            resolved.append({"uid": uid, "new_name": new_name, "is_folder": is_folder})
        elif name_prefix:
            if original_name:
                resolved.append(
                    {"uid": uid, "new_name": "{}{}".format(name_prefix, original_name), "is_folder": is_folder}
                )
            elif search_func:
                orig = search_func(uid)
                resolved.append(
                    {"uid": uid, "new_name": "{}{}".format(name_prefix, orig or uid), "is_folder": is_folder}
                )
            else:
                # 无法获取原名称，使用uid作为占位
                resolved.append({"uid": uid, "new_name": "{}{}".format(name_prefix, uid), "is_folder": is_folder})
        else:
            resolved.append({"uid": uid, "new_name": "", "is_folder": is_folder})

    return resolved


def main():
    parser = argparse.ArgumentParser(description="批量重命名测试用例/目录")
    parser.add_argument("--namespace", required=True, help="项目命名空间")
    parser.add_argument("--repo-uid", required=True, help="用例库UID")
    parser.add_argument("--repo-version-uid", required=True, help="用例库版本UID")
    parser.add_argument("--uids", default="", help="逗号分隔的UID列表")
    parser.add_argument("--name-prefix", default="", help="重命名前缀（配合 --uids 使用，在原名称前添加前缀）")
    parser.add_argument("--input", default="", help="输入JSON文件路径（包含 uid + new_name 字段，可选 is_folder）")
    parser.add_argument("--token", required=True, help="访问令牌（access_token）")
    parser.add_argument("--dry-run", action="store_true", help="仅显示待重命名列表，不执行")
    parser.add_argument(
        "--is-folder",
        action="store_true",
        default=True,
        help="当使用 --uids 时指定这些UID都是目录（默认True，将使用 UpdateFolder 接口）",
    )
    parser.add_argument(
        "--is-case",
        action="store_true",
        default=False,
        help="当使用 --uids 时指定这些UID都是用例（将使用 PatchCase 接口）",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API基础地址，默认 {}".format(DEFAULT_BASE_URL))
    args = parser.parse_args()

    # --is-case 覆盖 --is-folder
    if args.is_case:
        args.is_folder = False
    args = parser.parse_args()

    items = load_rename_items(args)

    if not items:
        print(json.dumps({"status": "error", "msg": "未提供任何重命名数据"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 解析最终的 new_name
    resolved = resolve_new_names(items)

    # 检查是否所有项都有 new_name
    missing = [r for r in resolved if not r.get("new_name")]
    if missing:
        print(
            json.dumps(
                {
                    "status": "error",
                    "msg": "以下UID缺少 new_name（使用 --name-prefix 时请通过 --input 提供 original_name 或 new_name）",
                    "missing_uids": [m["uid"] for m in missing],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "msg": "以下目录/用例将被重命名（dry-run模式，未实际执行）",
                    "total_count": len(resolved),
                    "items": resolved,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = batch_rename(
        namespace=args.namespace,
        repo_uid=args.repo_uid,
        repo_version_uid=args.repo_version_uid,
        rename_items=resolved,
        base_url=args.base_url,
        token_arg=args.token,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
