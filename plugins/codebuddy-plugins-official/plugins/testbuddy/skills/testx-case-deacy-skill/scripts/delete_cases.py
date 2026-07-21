#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
delete_cases.py：批量删除测试用例/目录脚本
通过 testx case API 的 BatchDeleteCases 接口，批量删除指定用例或空目录。

功能特点：
  - 支持删除用例和空目录（均通过 batch-delete 接口）
  - 非空目录安全检查：删除目录前可自动检查是否为空（--check-empty）
  - 优雅降级：非空目录删除失败时自动回退为重命名（添加"[空-待删除]"前缀）
  - 批量分批：数量过多时自动按 BATCH_SIZE 分批处理
  - 三种返回状态：success / fallback / error

请求方式参考: apps/fc/testx/srcs/mcp/tools/common.py

用法:
  echo '["uid1","uid2"]' | python delete_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --token <token>
  python delete_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --uids uid1,uid2 --token <token>
  python delete_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --input <file.json> --token <token>
  # 删除目录并进行非空检查，失败时降级为重命名
  python delete_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --uids dir1,dir2 --token <token> --check-empty --fallback-rename
"""

import argparse
import json
import os
import re
import sys
import time

try:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import HTTPError, Request, URLError, urlopen


# API配置
DEFAULT_BASE_URL = "http://openapi.zhiyan.woa.com"
# 单次批量删除上限
BATCH_SIZE = 50
# 请求间隔（秒），避免限流
REQUEST_INTERVAL = 0.2
# 降级重命名前缀
FALLBACK_RENAME_PREFIX = "[空-待删除]"


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


def build_delete_url(base_url, namespace, repo_uid, repo_version_uid):
    """构建批量删除用例的URL"""
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/batch-delete".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def build_search_url(base_url, namespace, repo_uid, repo_version_uid):
    """构建搜索用例的URL（用于非空检查）"""
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/search".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def build_patch_url(base_url, namespace, repo_uid, repo_version_uid, case_uid):
    """构建PatchCase接口的URL（用于降级重命名）"""
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/{uid}".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
        uid=case_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def make_request(url, body, token, namespace, method="POST"):
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


def check_folder_empty(namespace, repo_uid, repo_version_uid, folder_uid, token, base_url):
    """
    安全检查：检查目录是否为空。
    通过 SearchCases 接口查询该目录下是否有子节点。

    参考 case.go → SearchCases():
      - FolderUid: 指定目录UID
      - IncludeDescendants=False: 只查直接子节点
      - 返回结构: Data.Folders + Data.Cases
      - TotalCount 可能只计算用例（不含子目录），所以需要同时检查返回的 Folders 和 Cases

    返回:
      True  - 目录为空（可安全删除）
      False - 目录非空（不应直接删除）
    """
    url = build_search_url(base_url, namespace, repo_uid, repo_version_uid)
    body = {
        "PageInfo": {"Limit": 1, "Offset": 0},
        "FolderUid": folder_uid,
        "IncludeDescendants": False,
    }

    resp = make_request(url, body, token, namespace, method="POST")

    error = resp.get("error") or resp.get("Error")
    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            # 查询出错时保守返回 False（不删除）
            return False

    # 检查返回的 Data 中是否有子节点
    data = resp.get("Data") or resp.get("data") or {}
    folders = data.get("Folders") or data.get("folders") or []
    cases = data.get("Cases") or data.get("cases") or []

    # 同时检查 TotalCount 作为补充
    total_count = resp.get("TotalCount") or resp.get("total_count") or 0

    return len(folders) == 0 and len(cases) == 0 and total_count == 0


def build_update_folder_url(base_url, namespace, repo_uid, repo_version_uid, folder_uid):
    """构建 UpdateFolder 接口的URL（用于降级重命名目录）"""
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/folders/{uid}".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
        uid=folder_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def try_rename_as_deleted(namespace, repo_uid, repo_version_uid, uid, token, base_url, original_name=""):
    """
    优雅降级：将删除失败的目录重命名为 "[空-待删除]xxx" 格式。
    使用 UpdateFolder 接口 (PUT .../folders/{uid})，这是目录的专用更新接口。
    参考 case.go → UpdateFolder()

    返回:
      {"status": "fallback", "uid": ..., "new_name": ...}
      {"status": "error", "uid": ..., "msg": ...}
    """
    new_name = "{}{}".format(FALLBACK_RENAME_PREFIX, original_name or uid)

    url = build_update_folder_url(base_url, namespace, repo_uid, repo_version_uid, uid)
    # UpdateFolder 的 body 是 Folder 对象
    body = {
        "Uid": uid,
        "Name": new_name,
        "RepoUid": repo_uid,
        "RepoVersionUid": repo_version_uid,
    }

    resp = make_request(url, body, token, namespace, method="PUT")

    error = resp.get("error") or resp.get("Error")
    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            return {"status": "error", "uid": uid, "msg": "重命名降级也失败: {}".format(msg)}

    return {"status": "fallback", "uid": uid, "new_name": new_name, "msg": "删除失败，已降级为重命名"}


def batch_delete_request(namespace, repo_uid, repo_version_uid, uids, token, base_url):
    """
    单次批量删除请求（不超过 BATCH_SIZE）。
    参考 case_api.proto: POST .../cases/batch-delete
      - Namespace/RepoUid/RepoVersionUid 是 URL 路径参数
      - body 只需传 Uids（Namespace等为URL path中自动解析）

    返回 (success_uids, failed_uids, error_msg)
    """
    url = build_delete_url(base_url, namespace, repo_uid, repo_version_uid)
    # proto定义: body = "*"，所有非path字段都在body中
    # BatchDeleteCasesRequest { namespace, repo_uid, repo_version_uid, uids }
    # 但 namespace/repo_uid/repo_version_uid 已在URL路径中，body主要传 Uids
    body = {
        "Uids": uids,
    }

    resp = make_request(url, body, token, namespace)
    error = resp.get("error") or resp.get("Error")

    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            return [], uids, msg

    return uids, [], None


def batch_delete(
    namespace,
    repo_uid,
    repo_version_uid,
    uids,
    base_url=DEFAULT_BASE_URL,
    token_arg=None,
    check_empty=False,
    fallback_rename=False,
    uid_names=None,
):
    """
    分批执行批量删除。

    参数:
      uids: 待删除的UID列表
      check_empty: 是否对每个UID进行非空检查（用于目录删除场景）
      fallback_rename: 删除失败时是否降级为重命名
      uid_names: UID到名称的映射字典（用于降级重命名时保留原名称）

    返回三种状态的结果:
      - success: 删除成功
      - fallback: 删除失败但降级重命名成功
      - error: 完全失败
    """
    if not uids:
        return {"status": "error", "msg": "用例UID列表为空"}

    token = get_token(token_arg)
    uid_names = uid_names or {}

    # 阶段1: 非空检查（如果启用）
    safe_uids = []
    non_empty_uids = []

    if check_empty:
        for uid in uids:
            is_empty = check_folder_empty(namespace, repo_uid, repo_version_uid, uid, token, base_url)
            if is_empty:
                safe_uids.append(uid)
            else:
                non_empty_uids.append(uid)
            time.sleep(REQUEST_INTERVAL)
    else:
        safe_uids = list(uids)

    # 阶段2: 分批批量删除
    results = []
    total_deleted = 0
    total_failed = 0
    total_fallback = 0

    for i in range(0, len(safe_uids), BATCH_SIZE):
        batch = safe_uids[i : i + BATCH_SIZE]
        success_list, failed_list, error_msg = batch_delete_request(
            namespace, repo_uid, repo_version_uid, batch, token, base_url
        )

        for uid in success_list:
            results.append({"status": "success", "uid": uid})
            total_deleted += 1

        for uid in failed_list:
            if fallback_rename:
                original_name = uid_names.get(uid, "")
                fallback_result = try_rename_as_deleted(
                    namespace, repo_uid, repo_version_uid, uid, token, base_url, original_name
                )
                results.append(fallback_result)
                if fallback_result["status"] == "fallback":
                    total_fallback += 1
                else:
                    total_failed += 1
                time.sleep(REQUEST_INTERVAL)
            else:
                results.append({"status": "error", "uid": uid, "msg": error_msg or "批量删除失败"})
                total_failed += 1

        # 批次间间隔
        if i + BATCH_SIZE < len(safe_uids):
            time.sleep(REQUEST_INTERVAL)

    # 阶段3: 处理非空目录（如果有）
    for uid in non_empty_uids:
        if fallback_rename:
            original_name = uid_names.get(uid, "")
            fallback_result = try_rename_as_deleted(
                namespace, repo_uid, repo_version_uid, uid, token, base_url, original_name
            )
            results.append(fallback_result)
            if fallback_result["status"] == "fallback":
                total_fallback += 1
            else:
                total_failed += 1
            time.sleep(REQUEST_INTERVAL)
        else:
            results.append({"status": "error", "uid": uid, "msg": "目录非空，跳过删除"})
            total_failed += 1

    # 确定整体状态
    if total_failed == 0 and total_fallback == 0:
        overall_status = "success"
    elif total_failed == 0 and total_fallback > 0:
        overall_status = "partial"
    elif total_deleted > 0 or total_fallback > 0:
        overall_status = "partial"
    else:
        overall_status = "error"

    return {
        "status": overall_status,
        "total_requested": len(uids),
        "total_deleted": total_deleted,
        "total_fallback": total_fallback,
        "total_failed": total_failed,
        "check_empty_enabled": check_empty,
        "fallback_rename_enabled": fallback_rename,
        "non_empty_skipped": len(non_empty_uids) if not fallback_rename else 0,
        "results": results,
    }


def load_uids(args):
    """从各种来源加载待删除的UID列表，同时返回名称映射"""
    uids = []
    uid_names = {}

    # 优先从--uids参数获取
    if args.uids:
        uids = [u.strip() for u in args.uids.split(",") if u.strip()]
        return uids, uid_names

    # 从--input文件获取
    if args.input:
        if not os.path.exists(args.input):
            print(
                json.dumps(
                    {"status": "error", "msg": "输入文件不存在: {}".format(args.input)}, ensure_ascii=False, indent=2
                )
            )
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    uids.append(item)
                elif isinstance(item, dict):
                    uid_val = item.get("uid") or item.get("Uid") or ""
                    name_val = item.get("name") or item.get("Name") or ""
                    if uid_val:
                        uids.append(uid_val)
                        if name_val:
                            uid_names[uid_val] = name_val
        return uids, uid_names

    # 从stdin获取
    if not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()
        if input_data:
            input_data = sanitize_json_string(input_data)
            data = json.loads(input_data)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        uids.append(item)
                    elif isinstance(item, dict):
                        uid_val = item.get("uid") or item.get("Uid") or ""
                        name_val = item.get("name") or item.get("Name") or ""
                        if uid_val:
                            uids.append(uid_val)
                            if name_val:
                                uid_names[uid_val] = name_val

    return uids, uid_names


def main():
    parser = argparse.ArgumentParser(description="批量删除测试用例/目录")
    parser.add_argument("--namespace", required=True, help="项目命名空间")
    parser.add_argument("--repo-uid", required=True, help="用例库UID")
    parser.add_argument("--repo-version-uid", required=True, help="用例库版本UID")
    parser.add_argument("--uids", default="", help="逗号分隔的用例UID列表")
    parser.add_argument("--input", default="", help="输入JSON文件路径")
    parser.add_argument("--token", required=True, help="访问令牌（access_token）")
    parser.add_argument("--dry-run", action="store_true", help="仅显示待删除列表，不执行删除")
    parser.add_argument(
        "--check-empty",
        action="store_true",
        help="删除目录前检查是否为空（仅删除空目录，非空目录跳过或降级）",
    )
    parser.add_argument(
        "--fallback-rename",
        action="store_true",
        help="删除失败时降级为重命名（添加'[空-待删除]'前缀）",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API基础地址，默认 {}".format(DEFAULT_BASE_URL))
    args = parser.parse_args()

    uids, uid_names = load_uids(args)

    if not uids:
        print(json.dumps({"status": "error", "msg": "未提供任何用例UID"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "msg": "以下用例/目录将被删除（dry-run模式，未实际执行）",
                    "total_count": len(uids),
                    "check_empty": args.check_empty,
                    "fallback_rename": args.fallback_rename,
                    "uids": uids,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = batch_delete(
        namespace=args.namespace,
        repo_uid=args.repo_uid,
        repo_version_uid=args.repo_version_uid,
        uids=uids,
        base_url=args.base_url,
        token_arg=args.token,
        check_empty=args.check_empty,
        fallback_rename=args.fallback_rename,
        uid_names=uid_names,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
