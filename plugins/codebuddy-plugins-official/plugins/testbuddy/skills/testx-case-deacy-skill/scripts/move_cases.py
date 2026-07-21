#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
move_cases.py：批量移动测试用例到指定目录脚本
通过 testx case API 的 BatchMoveCases 接口，批量将用例移动到目标目录下。

参考实际API源码:
  - apps/fc/testx/srcs/case/core/api/case.go → BatchMoveCases()
  - protocols/fc/testx/case/case_api.proto → POST .../cases/batch-move
  - protocols/fc/testx/case/case.proto → BatchCopyOrMoveCasesRequest

接口说明:
  BatchMoveCases 接口接收 BatchCopyOrMoveCasesRequest，一次请求可移动多个用例到目标目录。
  比逐个调用 MoveCase 接口效率更高，且无需指定 Direction 参数。

请求方式参考: apps/fc/testx/srcs/mcp/tools/common.py

用法:
  python move_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --target-uid <folder_uid> --uids uid1,uid2 --token <token>
  python move_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --target-uid <folder_uid> --input <file.json> --token <token>
  echo '["uid1","uid2"]' | python move_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --target-uid <folder_uid> --token <token>

参数说明:
  --target-uid    目标目录的UID（用例将移动到该目录下）
  --uids          逗号分隔的用例UID列表
  --input         输入JSON文件路径（支持UID数组或对象数组）
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
    from urllib2 import HTTPError, Request, URLError, urlopen


# API配置
DEFAULT_BASE_URL = "http://openapi.zhiyan.woa.com"
# 单次批量移动上限
BATCH_SIZE = 50
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


def build_batch_move_url(base_url, namespace, repo_uid, repo_version_uid):
    """
    构建批量移动用例接口的URL
    proto定义: POST /v1/namespaces/{namespace}/repos/{repo_uid}/versions/{repo_version_uid}/cases/batch-move
    实际API: case.go → BatchMoveCases()
    """
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/batch-move".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
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


def batch_move_request(namespace, repo_uid, repo_version_uid, uids, target_uid, token, base_url):
    """
    单次批量移动请求（不超过 BATCH_SIZE）。
    参考 case_api.proto: POST .../cases/batch-move
      - Namespace/RepoUid/RepoVersionUid 是 URL 路径参数
      - body 中传 CaseUids + TargetFolderUid（body: "*"）

    参考 case.go → BatchMoveCases():
      - 从 req.CaseUids 提取待移动用例
      - 从 req.TargetFolderUid 提取目标目录
      - 调用 logic.Case.BatchMove() 执行批量移动

    返回 (success_uids, failed_uids, error_msg)
    """
    url = build_batch_move_url(base_url, namespace, repo_uid, repo_version_uid)
    # proto定义: body = "*"，所有非path字段都在body中
    # BatchCopyOrMoveCasesRequest { namespace, repo_uid, repo_version_uid, case_uids, target_folder_uid, ... }
    # namespace/repo_uid/repo_version_uid 已在URL路径中，body主要传 CaseUids + TargetFolderUid
    body = {
        "CaseUids": uids,
        "TargetFolderUid": target_uid,
    }

    resp = make_request(url, body, token, namespace, method="POST")
    error = resp.get("error") or resp.get("Error")

    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            return [], uids, msg

    return uids, [], None


def batch_move(
    namespace,
    repo_uid,
    repo_version_uid,
    uids,
    target_uid,
    base_url=DEFAULT_BASE_URL,
    token_arg=None,
):
    """
    分批执行批量移动。
    使用 BatchMoveCases 接口（POST .../cases/batch-move），一次请求可移动多个用例。
    数量超过 BATCH_SIZE 时自动分批处理。

    参数:
      uids: 待移动的用例/目录UID列表
      target_uid: 目标目录UID

    返回汇总结果。
    """
    if not uids:
        return {"status": "error", "msg": "用例UID列表为空"}
    if not target_uid:
        return {"status": "error", "msg": "目标目录UID为空"}

    token = get_token(token_arg)

    results = []
    total_moved = 0
    total_failed = 0

    for i in range(0, len(uids), BATCH_SIZE):
        batch = uids[i : i + BATCH_SIZE]
        success_list, failed_list, error_msg = batch_move_request(
            namespace, repo_uid, repo_version_uid, batch, target_uid, token, base_url
        )

        for uid in success_list:
            results.append({"status": "success", "uid": uid, "target_uid": target_uid})
            total_moved += 1

        for uid in failed_list:
            results.append({"status": "error", "uid": uid, "msg": error_msg or "批量移动失败"})
            total_failed += 1

        # 批次间间隔
        if i + BATCH_SIZE < len(uids):
            time.sleep(REQUEST_INTERVAL)

    return {
        "status": "success" if total_failed == 0 else "partial",
        "total_requested": len(uids),
        "total_moved": total_moved,
        "total_failed": total_failed,
        "target_uid": target_uid,
        "results": results,
    }


def load_uids(args):
    """从各种来源加载待移动的UID列表"""
    uids = []

    # 优先从--uids参数获取
    if args.uids:
        uids = [u.strip() for u in args.uids.split(",") if u.strip()]
        return uids

    # 从--input文件获取
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
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    uids.append(item)
                elif isinstance(item, dict):
                    uid_val = item.get("uid") or item.get("Uid") or ""
                    if uid_val:
                        uids.append(str(uid_val))
        return uids

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
                        if uid_val:
                            uids.append(str(uid_val))

    return uids


def main():
    parser = argparse.ArgumentParser(description="批量移动测试用例到指定目录")
    parser.add_argument("--namespace", required=True, help="项目命名空间")
    parser.add_argument("--repo-uid", required=True, help="用例库UID")
    parser.add_argument("--repo-version-uid", required=True, help="用例库版本UID")
    parser.add_argument("--target-uid", required=True, help="目标目录的UID")
    parser.add_argument("--uids", default="", help="逗号分隔的用例UID列表")
    parser.add_argument("--input", default="", help="输入JSON文件路径")
    parser.add_argument("--token", required=True, help="访问令牌（access_token）")
    parser.add_argument("--dry-run", action="store_true", help="仅显示待移动列表，不执行移动")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API基础地址，默认 {}".format(DEFAULT_BASE_URL))
    args = parser.parse_args()

    uids = load_uids(args)

    if not uids:
        print(json.dumps({"status": "error", "msg": "未提供任何用例UID"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "msg": "以下用例将被移动到目录 {} 下（dry-run模式，未实际执行）".format(args.target_uid),
                    "total_count": len(uids),
                    "target_uid": args.target_uid,
                    "uids": uids,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = batch_move(
        namespace=args.namespace,
        repo_uid=args.repo_uid,
        repo_version_uid=args.repo_version_uid,
        uids=uids,
        target_uid=args.target_uid,
        base_url=args.base_url,
        token_arg=args.token,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
