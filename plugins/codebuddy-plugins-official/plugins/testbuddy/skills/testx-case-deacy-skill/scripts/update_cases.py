#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_cases.py：批量更新测试用例脚本
通过 testx case API 的 PatchCase 接口，逐个更新用例的关键字段。

【重要】PatchCase REST API（body: "case"）无法传递 Fields 参数，
服务端 UpdateCase 在 fields 为空时会全量更新 Name/Description/Priority 等所有字段，
即使请求中未传入某字段也会被覆盖为空值。

因此本脚本采用 read-merge-write 策略：
1. 先 GET 原始用例数据
2. 将输入的更新字段 merge 到原始数据上
3. 用合并后的完整数据调用 PatchCase
这样确保未指定更新的字段不会被覆盖。

请求方式参考: apps/fc/testx/srcs/mcp/tools/common.py

用法:
  echo '[{用例对象}]' | python update_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --token <token>
  python update_cases.py --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> --input <file.json> --token <token>

输入格式（JSON数组）:
  [
    {
      "uid": "用例UID（必填）",
      "name": "更新后的用例名称（可选，不传则保持原值）",
      "description": "更新后的描述（可选）",
      "pre_conditions": "更新后的前置条件（可选）",
      "priority": "P0/P1/P2/P3（可选）",
      "steps": [
        {"content": "步骤描述", "expected_result": "预期结果"}
      ]
    }
  ]

只需传入 uid + 需要变更的字段，脚本会自动获取原始数据并合并。
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
# 请求间隔（秒），避免限流
REQUEST_INTERVAL = 0.2

# 优先级映射
PRIORITY_MAP = {
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
    "p0": "P0",
    "p1": "P1",
    "p2": "P2",
    "p3": "P3",
    "0": "P0",
    "1": "P1",
    "2": "P2",
    "3": "P3",
}


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


def build_patch_url(base_url, namespace, repo_uid, repo_version_uid, case_uid):
    """
    构建PatchCase接口的URL
    proto定义: patch /v1/namespaces/{namespace}/repos/{repo_uid}/versions/{repo_version_uid}/cases/{case.uid}
    """
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/{uid}".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
        uid=case_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def build_get_url(base_url, namespace, repo_uid, repo_version_uid, case_uid):
    """
    构建GetCase接口的URL
    proto定义: get /v1/namespaces/{namespace}/repos/{repo_uid}/versions/{repo_version_uid}/cases/{uid}
    """
    path = "/testx/case/v1/namespaces/{ns}/repos/{repo}/versions/{ver}/cases/{uid}".format(
        ns=namespace,
        repo=repo_uid,
        ver=repo_version_uid,
        uid=case_uid,
    )
    return "{base}{path}".format(base=base_url.rstrip("/"), path=path)


def get_case(namespace, repo_uid, repo_version_uid, case_uid, token, base_url):
    """
    获取单个用例的完整数据（用于 read-merge-write 策略）。
    通过 GET 请求获取原始用例的所有字段，防止 PatchCase 全量更新时覆盖未指定的字段。
    """
    url = build_get_url(base_url, namespace, repo_uid, repo_version_uid, case_uid)
    req = Request(url)
    req.get_method = lambda: "GET"
    req.add_header("Content-Type", "application/json")
    req.add_header("token", token)
    if namespace:
        req.add_header("x-shipyard-ns", namespace)

    try:
        resp = urlopen(req, timeout=30)
        resp_data = resp.read().decode("utf-8")
        data = json.loads(resp_data)
        # 返回的结构为 {"Data": {Case对象}}
        case_data = data.get("Data") or data.get("data") or {}
        return case_data, None
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return None, "HTTP错误: {} {}".format(e.code, error_body[:500])
    except URLError as e:
        return None, "网络错误: {}".format(str(e))
    except Exception as e:
        return None, "请求异常: {}".format(str(e))


def make_request(url, body, token, namespace, method="PATCH"):
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


def build_case_body(case_input, original_case=None):
    """
    将输入的用例数据转换为API所需的Case对象格式。

    采用 read-merge-write 策略：
    - 如果提供了 original_case（原始用例数据），则以原始数据为基础，
      只覆盖 case_input 中显式指定的字段
    - 如果没有 original_case，则只包含 case_input 中提供的字段（向后兼容）

    这样确保 PatchCase 全量更新时不会把未指定的字段覆盖为空值。
    """
    case_obj = {}

    # UID（必填）
    uid = case_input.get("uid") or case_input.get("Uid") or ""
    if not uid:
        return None, "用例缺少uid字段"
    case_obj["Uid"] = uid

    # 需要 merge 的字段列表及其映射
    # (输入字段名小写, 输入字段名大写, API字段名, 原始数据字段名)
    text_fields = [
        ("name", "Name", "Name", "Name"),
        ("description", "Description", "Description", "Description"),
        ("pre_conditions", "PreConditions", "PreConditions", "PreConditions"),
    ]

    for lower_key, upper_key, api_key, orig_key in text_fields:
        # 检查输入中是否显式提供了该字段
        if lower_key in case_input or upper_key in case_input:
            val = case_input.get(lower_key) or case_input.get(upper_key) or ""
            case_obj[api_key] = val
        elif original_case:
            # 输入中没有该字段，但有原始数据，使用原始值保持不变
            orig_val = original_case.get(orig_key) or original_case.get(lower_key) or ""
            case_obj[api_key] = orig_val

    # 优先级
    if "priority" in case_input or "Priority" in case_input:
        priority = case_input.get("priority") or case_input.get("Priority") or ""
        if priority:
            mapped = PRIORITY_MAP.get(str(priority), priority)
            case_obj["Priority"] = mapped
    elif original_case:
        orig_priority = original_case.get("Priority") or original_case.get("priority") or ""
        if orig_priority:
            case_obj["Priority"] = orig_priority

    # 步骤
    if "steps" in case_input or "Steps" in case_input:
        steps = case_input.get("steps") or case_input.get("Steps") or []
        case_steps = []
        for step in steps:
            case_steps.append(
                {
                    "Content": step.get("content") or step.get("Content") or "",
                    "ExpectedResult": step.get("expected_result") or step.get("ExpectedResult") or "",
                }
            )
        case_obj["Steps"] = case_steps
        case_obj["StepType"] = "STEP"
    elif original_case:
        orig_steps = original_case.get("Steps") or original_case.get("steps") or []
        if orig_steps:
            case_obj["Steps"] = orig_steps
        orig_step_type = original_case.get("StepType") or original_case.get("step_type") or ""
        if orig_step_type:
            case_obj["StepType"] = orig_step_type

    # 文本步骤类型
    if "step_text" in case_input or "StepText" in case_input:
        step_text = case_input.get("step_text") or case_input.get("StepText")
        if step_text is not None:
            case_obj["StepText"] = {
                "StepText": step_text.get("content") or step_text.get("Content") or "",
                "ExpectedResult": step_text.get("expected_result") or step_text.get("ExpectedResult") or "",
            }
            case_obj["StepType"] = "TEXT"
    elif original_case:
        orig_step_text = original_case.get("StepText") or original_case.get("step_text")
        orig_step_type = original_case.get("StepType") or original_case.get("step_type") or ""
        if orig_step_text and orig_step_type == "TEXT":
            case_obj["StepText"] = orig_step_text
            case_obj["StepType"] = "TEXT"

    return case_obj, None


def update_single_case(namespace, repo_uid, repo_version_uid, case_input, token, base_url):
    """
    更新单个用例（read-merge-write 策略）。

    1. 先 GET 原始用例数据
    2. 将输入的更新字段 merge 到原始数据上
    3. 用合并后的完整数据调用 PatchCase

    这样确保 PatchCase 全量更新时不会把未指定的字段覆盖为空值。
    """
    case_uid = case_input.get("uid") or case_input.get("Uid") or ""
    if not case_uid:
        return {"status": "error", "uid": "", "msg": "用例缺少uid字段"}

    # Step 1: GET 原始用例数据
    original_case, get_err = get_case(namespace, repo_uid, repo_version_uid, case_uid, token, base_url)
    if get_err:
        return {"status": "error", "uid": case_uid, "msg": "获取原始数据失败: {}".format(get_err)}

    # Step 2: Merge - 以原始数据为基础，覆盖需要更新的字段
    case_obj, err = build_case_body(case_input, original_case)
    if err:
        return {"status": "error", "uid": case_uid, "msg": err}

    # Step 3: Write - 用合并后的完整数据调用 PatchCase
    url = build_patch_url(base_url, namespace, repo_uid, repo_version_uid, case_uid)
    resp = make_request(url, case_obj, token, namespace, method="PATCH")

    error = resp.get("error") or resp.get("Error")
    if error:
        msg = error.get("message") or error.get("Message") or str(error)
        if msg and msg != "null":
            return {"status": "error", "uid": case_uid, "msg": msg}

    return {"status": "success", "uid": case_uid}


def batch_update(namespace, repo_uid, repo_version_uid, cases, base_url=DEFAULT_BASE_URL, token_arg=None):
    """
    批量更新用例。

    每个用例更新需要两次API调用（GET获取原始数据 + PATCH合并更新），
    因此处理速度约为原来的一半，但确保不会意外覆盖未指定的字段。
    """
    if not cases:
        return {"status": "error", "msg": "用例列表为空"}

    token = get_token(token_arg)

    results = []
    success_count = 0
    fail_count = 0

    for idx, case_input in enumerate(cases):
        result = update_single_case(
            namespace,
            repo_uid,
            repo_version_uid,
            case_input,
            token,
            base_url,
        )
        result["index"] = idx
        results.append(result)

        if result["status"] == "success":
            success_count += 1
        else:
            fail_count += 1

        # 请求间隔，避免限流
        if idx < len(cases) - 1:
            time.sleep(REQUEST_INTERVAL)

    return {
        "status": "success" if fail_count == 0 else "partial",
        "total_requested": len(cases),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
    }


def load_cases(args):
    """从各种来源加载待更新的用例列表"""
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
            return data
        elif isinstance(data, dict) and "cases" in data:
            return data["cases"]
        return [data]

    # 从stdin获取
    if not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()
        if input_data:
            input_data = sanitize_json_string(input_data)
            data = json.loads(input_data)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "cases" in data:
                return data["cases"]
            return [data]

    return []


def main():
    parser = argparse.ArgumentParser(description="批量更新测试用例")
    parser.add_argument("--namespace", required=True, help="项目命名空间")
    parser.add_argument("--repo-uid", required=True, help="用例库UID")
    parser.add_argument("--repo-version-uid", required=True, help="用例库版本UID")
    parser.add_argument("--input", default="", help="输入JSON文件路径")
    parser.add_argument("--token", required=True, help="访问令牌（access_token）")
    parser.add_argument("--dry-run", action="store_true", help="仅显示待更新列表，不执行更新")
    args = parser.parse_args()

    cases = load_cases(args)

    if not cases:
        print(json.dumps({"status": "error", "msg": "未提供任何用例数据"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 校验每个用例都有uid
    for idx, c in enumerate(cases):
        uid_val = c.get("uid") or c.get("Uid") or ""
        if not uid_val:
            print(
                json.dumps({"status": "error", "msg": "用例[{}]缺少uid字段".format(idx)}, ensure_ascii=False, indent=2)
            )
            sys.exit(1)

    if args.dry_run:
        summary = []
        for c in cases:
            summary.append(
                {
                    "uid": c.get("uid") or c.get("Uid"),
                    "name": c.get("name") or c.get("Name") or "(未修改)",
                    "fields_to_update": [k for k in c.keys() if k.lower() != "uid"],
                }
            )
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "msg": "以下用例将被更新（dry-run模式，未实际执行）",
                    "total_count": len(cases),
                    "cases": summary,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = batch_update(
        namespace=args.namespace,
        repo_uid=args.repo_uid,
        repo_version_uid=args.repo_version_uid,
        cases=cases,
        token_arg=args.token,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
