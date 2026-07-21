#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_cases.py：批量获取测试用例脚本
通过 testx case API 的 search 接口，获取指定目录下的所有用例（服务端分页，返回完整字段）。

请求方式参考: apps/fc/testx/docs/openAPI/case/case.md

用法:
  # FLAT模式（默认，返回平铺列表，自动分页）
  python search_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --folder-uid <folder> --token <token> [--page-size 100] [--output <file>]

  # TREE模式（返回服务端组装的树形结构，用于HTML报告生成）
  python search_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --folder-uid <folder> --token <token> --show-mode TREE [--output <file>]

输出字段（FLAT模式）: uid, name, pre_conditions, description, steps, priority, step_type, folder_uid, item_type
输出字段（TREE模式）: 嵌套树结构，每个folder节点含 children（子目录+子用例），参考 SearchCases API showMode=TREE
"""

import argparse
import io
import json
import os
import sys

try:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import HTTPError, Request, URLError, urlopen


# API配置
DEFAULT_BASE_URL = "http://openapi.zhiyan.woa.com"
DEFAULT_PAGE_SIZE = 100


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


def build_search_url(base_url, namespace, repo_uid, repo_version_uid):
    """构建搜索用例的URL - 使用 search 接口（返回完整字段）"""
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/search".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def build_request_body(
    namespace,
    repo_uid,
    repo_version_uid,
    folder_uid,
    name=None,
    uids=None,
    item_type=None,
    include_descendants=True,
    include_ancestors=False,
    show_mode="FLAT",
    with_full_path=False,
    page_size=DEFAULT_PAGE_SIZE,
    offset=0,
):
    """
    构建请求体 - 使用 cases/search 接口，需要 PageInfo 分页参数

    item_type: 过滤类型，可选值: "CASE"（仅用例）, "FOLDER"（仅目录）, None/""（不过滤，返回全部）
    show_mode: 展示模式，"FLAT"（平铺，默认）或 "TREE"（树形）
    include_ancestors: 是否返回父目录层级（TREE模式下建议开启）
    with_full_path: 是否返回完整目录路径

    参考源码: apps/fc/testx/srcs/case/core/api/case.go → SearchCases()
    - ShowMode=TREE + IncludeAncestors=true 时，API通过 ComposeItems() 构建完整树形结构
    - 返回的 Folders 中每个 Folder 包含嵌套的 Folders（子目录）和 Cases（子用例）
    """
    filter_obj = {"Name": name or ""}
    if item_type:
        filter_obj["ItemType"] = item_type

    body = {
        "PageInfo": {
            "Limit": page_size,
            "Offset": offset,
        },
        "Namespace": namespace,
        "RepoUid": repo_uid,
        "RepoVersionUid": repo_version_uid,
        "FolderUid": folder_uid or "0",
        "Filter": filter_obj,
        "IncludeDescendants": include_descendants,
        "IncludeAncestors": include_ancestors,
        "ShowMode": show_mode,
        "WithFullPath": with_full_path,
        "ExtendFields": [
            "STEP",
        ],
    }
    if uids:
        body["CaseUids"] = uids
    return body


def make_request(url, body, token, namespace):
    """
    执行HTTP请求 - 对齐MCP tools/common.py 中 make_request 的header格式
    认证方式: token header + x-shipyard-ns
    """
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data)
    req.get_method = lambda: "POST"
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


def extract_case_info(case_data):
    """从API返回的case数据中提取所需字段，同时保留 item_type 以区分用例和目录"""
    item_type = case_data.get("ItemType") or case_data.get("itemType") or case_data.get("item_type") or "CASE"

    steps = []
    raw_steps = case_data.get("Steps") or case_data.get("steps") or []
    for step in raw_steps:
        steps.append(
            {
                "content": step.get("Content", "") or step.get("content", ""),
                "expected_result": step.get("ExpectedResult", "") or step.get("expected_result", ""),
            }
        )

    # 处理文本步骤类型
    step_text = case_data.get("StepText") or case_data.get("step_text")
    step_type = case_data.get("StepType") or case_data.get("stepType") or case_data.get("step_type") or "STEP"

    result = {
        "uid": case_data.get("Uid") or case_data.get("uid") or "",
        "name": case_data.get("Name") or case_data.get("name") or "",
        "item_type": item_type,
        "description": case_data.get("Description") or case_data.get("description") or "",
        "pre_conditions": case_data.get("PreConditions") or case_data.get("pre_conditions") or "",
        "priority": case_data.get("Priority") or case_data.get("priority") or "",
        "step_type": step_type,
        "steps": steps,
        "folder_uid": case_data.get("FolderUid") or case_data.get("folder_uid") or "",
        "full_path": case_data.get("FullPath") or case_data.get("full_path") or "",
    }

    # 如果是TEXT类型步骤，额外填充step_text
    if step_text and step_type == "TEXT":
        result["step_text"] = {
            "content": step_text.get("Content")
            or step_text.get("content")
            or step_text.get("StepText")
            or step_text.get("step_text")
            or "",
            "expected_result": step_text.get("ExpectedResult") or step_text.get("expected_result") or "",
        }

    return result


def extract_case_node(case_data):
    """
    从TREE模式返回的Case对象中提取用例节点信息。
    返回统一的树节点格式，用于HTML报告的tree数据结构。

    参考proto: case.proto → message Case
    """
    info = extract_case_info(case_data)
    node = {
        "uid": info["uid"],
        "name": info["name"],
        "type": "case",
        "item_type": "CASE",
        "description": info.get("description", ""),
        "pre_conditions": info.get("pre_conditions", ""),
        "priority": info.get("priority", ""),
        "step_type": info.get("step_type", "STEP"),
        "steps": info.get("steps", []),
        "folder_uid": info.get("folder_uid", ""),
        "full_path": info.get("full_path", ""),
    }
    if "step_text" in info:
        node["step_text"] = info["step_text"]
    return node


def extract_folder_tree(folder_data):
    """
    递归解析TREE模式返回的Folder对象，构建嵌套树结构。

    参考proto: case.proto → message Folder
    - Folder.Folders (json: "Folders"): 直接子目录
    - Folder.Cases (json: "Cases"): 直接子用例
    - 服务端通过 ComposeItems() 已构建好嵌套关系

    返回树节点，children中先放子目录（递归），再放子用例。
    """
    uid = folder_data.get("Uid") or folder_data.get("uid") or ""
    name = folder_data.get("Name") or folder_data.get("name") or ""
    folder_uid = folder_data.get("FolderUid") or folder_data.get("folder_uid") or ""
    full_path = folder_data.get("FullPath") or folder_data.get("full_path") or ""
    case_count = folder_data.get("CaseCount") or folder_data.get("case_count") or 0

    node = {
        "uid": uid,
        "name": name,
        "type": "folder",
        "item_type": "FOLDER",
        "folder_uid": folder_uid,
        "full_path": full_path,
        "case_count": case_count,
        "children": [],
    }

    # 递归处理子目录
    sub_folders = folder_data.get("Folders") or folder_data.get("folders") or []
    for sf in sub_folders:
        node["children"].append(extract_folder_tree(sf))

    # 处理直接子用例
    sub_cases = folder_data.get("Cases") or folder_data.get("cases") or []
    for sc in sub_cases:
        node["children"].append(extract_case_node(sc))

    return node


def _count_tree_nodes(node):
    """统计树中的目录数和用例数"""
    folders = 0
    cases = 0
    if node.get("type") == "folder":
        folders = 1
    else:
        cases = 1
    for child in node.get("children", []):
        cf, cc = _count_tree_nodes(child)
        folders += cf
        cases += cc
    return folders, cases


def search_tree(
    namespace,
    repo_uid,
    repo_version_uid,
    folder_uid,
    name=None,
    uids=None,
    item_type=None,
    include_descendants=True,
    page_size=DEFAULT_PAGE_SIZE,
    base_url=DEFAULT_BASE_URL,
    token_arg=None,
):
    """
    使用 TREE 模式获取目录树结构。

    通过 ShowMode=TREE + IncludeAncestors=true + IncludeDescendants=true，
    让服务端直接返回通过 ComposeItems() 组装好的嵌套树形结构。

    参考源码: apps/fc/testx/srcs/case/core/api/case.go → SearchCases()
    - showMode=true 时调用 ComposeItems(pbFolders, pbCases, folderUid, ...)
    - ComposeItems() 将 Folders 和 Cases 按 FolderUid 关系组装为嵌套结构
    - 返回的 Folders 中 FolderUid==folderUid 的为根节点，其内部嵌套子目录和子用例

    注意: TREE模式下，分页参数设置较大值以一次获取全量数据。

    返回:
    {
        "status": "success",
        "tree": { ... },           # 嵌套树结构根节点
        "total_count": N,
        "folder_count": N,
        "case_count": N,
        "flat_cases": [...]        # 同时提供平铺的用例列表（兼容原有逻辑）
    }
    """
    token = get_token(token_arg)
    url = build_search_url(base_url, namespace, repo_uid, repo_version_uid)

    body = build_request_body(
        namespace=namespace,
        repo_uid=repo_uid,
        repo_version_uid=repo_version_uid,
        folder_uid=folder_uid,
        name=name,
        uids=uids,
        item_type=item_type,
        include_descendants=include_descendants,
        include_ancestors=True,
        show_mode="TREE",
        with_full_path=True,
        page_size=max(page_size, 500),  # TREE模式尽量一次获取全量
        offset=0,
    )

    resp = make_request(url, body, token, namespace)

    # 检查错误
    error = resp.get("error") or resp.get("Error")
    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            return {"status": "error", "msg": msg, "tree": None, "flat_cases": []}

    data = resp.get("Data") or resp.get("data") or {}
    total_count = resp.get("TotalCount") or resp.get("total_count") or 0

    # TREE模式下: Folders 为已组装好的根级目录列表（含嵌套子目录和子用例）
    folders_raw = data.get("Folders") or data.get("folders") or []
    # 根级 Cases（不在任何子目录下的用例）
    root_cases_raw = data.get("Cases") or data.get("cases") or []

    # 构建树根节点
    if len(folders_raw) == 1:
        # 通常 IncludeAncestors=true 时，根节点就是 folder_uid 对应的目录
        tree_root = extract_folder_tree(folders_raw[0])
    elif len(folders_raw) > 1:
        # 多个根级目录，创建虚拟根节点
        tree_root = {
            "uid": folder_uid or "root",
            "name": "根目录",
            "type": "folder",
            "item_type": "FOLDER",
            "folder_uid": "",
            "full_path": "",
            "case_count": 0,
            "children": [],
        }
        for f in folders_raw:
            tree_root["children"].append(extract_folder_tree(f))
    else:
        # 没有目录，创建虚拟根节点
        tree_root = {
            "uid": folder_uid or "root",
            "name": "根目录",
            "type": "folder",
            "item_type": "FOLDER",
            "folder_uid": "",
            "full_path": "",
            "case_count": 0,
            "children": [],
        }

    # 根级用例也加入根节点
    for rc in root_cases_raw:
        tree_root["children"].append(extract_case_node(rc))

    # 同时收集平铺用例列表（兼容原有逻辑）
    flat_cases = []

    def _collect_flat_cases(node):
        if node.get("type") == "case":
            flat_cases.append(
                {
                    "uid": node["uid"],
                    "name": node["name"],
                    "item_type": "CASE",
                    "description": node.get("description", ""),
                    "pre_conditions": node.get("pre_conditions", ""),
                    "priority": node.get("priority", ""),
                    "step_type": node.get("step_type", "STEP"),
                    "steps": node.get("steps", []),
                    "folder_uid": node.get("folder_uid", ""),
                    "full_path": node.get("full_path", ""),
                }
            )
            if "step_text" in node:
                flat_cases[-1]["step_text"] = node["step_text"]
        for child in node.get("children", []):
            _collect_flat_cases(child)

    _collect_flat_cases(tree_root)

    folder_count, case_count = _count_tree_nodes(tree_root)

    return {
        "status": "success",
        "total_count": total_count,
        "folder_count": folder_count,
        "case_count": case_count,
        "namespace": namespace,
        "repo_uid": repo_uid,
        "repo_version_uid": repo_version_uid,
        "folder_uid": folder_uid,
        "tree": tree_root,
        "flat_cases": flat_cases,
    }


def search_all_cases(
    namespace,
    repo_uid,
    repo_version_uid,
    folder_uid,
    name=None,
    uids=None,
    item_type=None,
    include_descendants=True,
    page_size=DEFAULT_PAGE_SIZE,
    base_url=DEFAULT_BASE_URL,
    token_arg=None,
):
    """
    通过服务端分页获取所有用例（FLAT模式）

    使用 cases/search 接口，每次请求 page_size 条，
    根据 TotalCount 判断是否还有下一页，循环获取全量数据。

    item_type: 过滤类型，"CASE"（仅用例）, "FOLDER"（仅目录）, None（不过滤，返回全部含目录）
    """
    token = get_token(token_arg)
    url = build_search_url(base_url, namespace, repo_uid, repo_version_uid)

    all_cases = []
    offset = 0
    total_count = None

    while True:
        body = build_request_body(
            namespace=namespace,
            repo_uid=repo_uid,
            repo_version_uid=repo_version_uid,
            folder_uid=folder_uid,
            name=name,
            uids=uids,
            item_type=item_type,
            include_descendants=include_descendants,
            page_size=page_size,
            offset=offset,
        )

        resp = make_request(url, body, token, namespace)

        # 检查错误
        error = resp.get("error") or resp.get("Error")
        if error:
            msg = error.get("message") or error.get("Message") or str(error)
            if msg and msg != "null":
                return {"status": "error", "msg": msg, "cases": []}

        # 解析数据 - 响应格式: {"Data": {"Cases": [...]}, "TotalCount": N}
        data = resp.get("Data") or resp.get("data") or {}
        cases_raw = data.get("Cases") or data.get("cases") or []

        if total_count is None:
            total_count = resp.get("TotalCount") or resp.get("total_count") or 0

        for c in cases_raw:
            all_cases.append(extract_case_info(c))

        # 没有更多数据或已获取全部
        if not cases_raw or len(all_cases) >= total_count:
            break

        offset += len(cases_raw)

    return {
        "status": "success",
        "total_count": total_count or len(all_cases),
        "fetched_count": len(all_cases),
        "namespace": namespace,
        "repo_uid": repo_uid,
        "repo_version_uid": repo_version_uid,
        "folder_uid": folder_uid,
        "cases": all_cases,
    }


def main():
    parser = argparse.ArgumentParser(description="批量获取测试用例")
    parser.add_argument("--namespace", required=True, help="项目命名空间")
    parser.add_argument("--repo-uid", required=True, help="用例库UID")
    parser.add_argument("--repo-version-uid", required=True, help="用例库版本UID")
    parser.add_argument("--folder-uid", required=True, help="目录UID")
    parser.add_argument("--name", default="", help="用例名称（模糊匹配）")
    parser.add_argument(
        "--item-type",
        default="",
        choices=["", "CASE", "FOLDER"],
        help="过滤类型: CASE（仅用例）、FOLDER（仅目录）、空（不过滤，返回全部含目录，默认）",
    )
    parser.add_argument(
        "--show-mode",
        default="FLAT",
        choices=["FLAT", "TREE"],
        help="展示模式: FLAT（平铺列表，默认）、TREE（树形结构，用于HTML报告生成）",
    )
    parser.add_argument(
        "--include-descendants", action="store_true", default=True, help="是否包含子目录用例（默认包含）"
    )
    parser.add_argument(
        "--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="每页数量，默认{}".format(DEFAULT_PAGE_SIZE)
    )
    parser.add_argument("--token", required=True, help="访问令牌（access_token）")
    parser.add_argument("--output", default="", help="输出文件路径，不指定则输出到stdout")
    args = parser.parse_args()

    if args.show_mode == "TREE":
        result = search_tree(
            namespace=args.namespace,
            repo_uid=args.repo_uid,
            repo_version_uid=args.repo_version_uid,
            folder_uid=args.folder_uid,
            name=args.name if args.name else None,
            item_type=args.item_type if args.item_type else None,
            include_descendants=args.include_descendants,
            page_size=args.page_size,
            token_arg=args.token,
        )
    else:
        result = search_all_cases(
            namespace=args.namespace,
            repo_uid=args.repo_uid,
            repo_version_uid=args.repo_version_uid,
            folder_uid=args.folder_uid,
            name=args.name if args.name else None,
            item_type=args.item_type if args.item_type else None,
            include_descendants=args.include_descendants,
            page_size=args.page_size,
            token_arg=args.token,
        )

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with io.open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)

        summary = {
            "status": result["status"],
            "total_count": result.get("total_count", 0),
            "output_file": args.output,
            "show_mode": args.show_mode,
        }
        if args.show_mode == "TREE":
            summary["folder_count"] = result.get("folder_count", 0)
            summary["case_count"] = result.get("case_count", 0)
        else:
            summary["fetched_count"] = result.get("fetched_count", 0)

        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(output_json)


if __name__ == "__main__":
    main()
