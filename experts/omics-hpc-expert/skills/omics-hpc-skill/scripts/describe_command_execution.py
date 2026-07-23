# -*- coding: utf-8 -*-
"""
组学平台 DescribeCommandExecution —— 用 InvocationId 查询 HPC 命令执行结果

用法：
  python3 describe_command_execution.py \
    --cluster-id <ClusterId> \
    --invocation-ids <id1,id2,...> \
    [--offset 0] [--limit 20] \
    [--region <REGION>] \
    [--poll] [--poll-interval 5] [--poll-timeout 300]

输出：
  JSON：{"region": "...", "response": {"ExecutionSet": [...], "TotalCount": N, "RequestId": "..."}}
  非终态且未启用 --poll 时，输出当前快照即返回。
  --poll 模式下持续轮询直至所有 InvocationId 进入终态或超时。
"""
import argparse
import json
import os
import sys
import time

from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

DEFAULT_REGION = "ap-guangzhou"
SERVICE = "omics"
VERSION = "2022-11-28"

# 统一接入点：腾讯云 omics 服务单一域名，由腾讯云就近接入。
# DescribeCommandExecution 本身不受地域限制，region 在这里仅作为 SDK 签名占位。
DEFAULT_ENDPOINT = "omics.tencentcloudapi.com"

# 终态状态关键字（大小写不敏感子串匹配）
# 已知样例：SUCCESS（命令成功），其他失败/超时态以关键字兜底
TERMINAL_KEYWORDS = (
    "success",
    "succeeded",
    "fail",       # FAILED / Failure
    "timeout",
    "terminated",
    "cancel",     # Cancelled / CANCELLED
    "error",
)


def resolve_endpoint(region: str) -> str:  # 保留名字，返回固定 endpoint
    return DEFAULT_ENDPOINT


def is_terminal_status(status: str) -> bool:
    """大小写不敏感的子串匹配兜底判定终态。"""
    if not status:
        return False
    s = status.lower()
    return any(k in s for k in TERMINAL_KEYWORDS)


def all_terminal(response: dict, expected_count: int) -> bool:
    """检查响应中所有 ExecutionSet 是否都已进入终态。

    expected_count: 预期的 InvocationId 数量；若 ExecutionSet 数量不足，视为还在生成中，继续轮询。
    """
    executions = response.get("ExecutionSet") or []
    if not executions or len(executions) < expected_count:
        return False
    return all(is_terminal_status(e.get("Status", "")) for e in executions)


def describe(invocation_ids: list, cluster_id: str, region: str,
             offset: int | None = None, limit: int | None = None) -> dict:
    """调一次 DescribeCommandExecution。"""
    secret_id = os.getenv("TENCENTCLOUD_SECRET_ID", "")
    secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY", "")
    if not secret_id or not secret_key:
        print(
            "[error] 未在环境变量中找到 TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY",
            file=sys.stderr,
        )
        sys.exit(2)

    cred = credential.Credential(secret_id, secret_key)
    http_profile = HttpProfile()
    http_profile.endpoint = resolve_endpoint(region)
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    common_client = CommonClient(SERVICE, VERSION, cred, region, profile=client_profile)
    params: dict = {"ClusterId": cluster_id, "InvocationIds": invocation_ids}
    if offset is not None:
        params["Offset"] = offset
    if limit is not None:
        params["Limit"] = limit
    return common_client.call_json("DescribeCommandExecution", params)


def main() -> None:
    parser = argparse.ArgumentParser(description="腾讯云组学平台 DescribeCommandExecution —— 查询 HPC 命令执行结果")
    parser.add_argument("--cluster-id", required=True, help="集群 ID")
    parser.add_argument("--invocation-ids", required=True, help="InvocationId 列表（英文逗号分隔）")
    parser.add_argument("--offset", type=int, default=None, help="分页起始位置（可选）")
    parser.add_argument("--limit", type=int, default=None, help="分页大小（可选）")
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help="SDK 签名用的 region（X-TC-Region）；DescribeCommandExecution 不受地域限制，默认 ap-guangzhou 即可",
    )
    parser.add_argument("--poll", action="store_true", help="是否轮询直至所有调用进入终态")
    parser.add_argument("--poll-interval", type=int, default=5, help="轮询间隔秒数（默认 5）")
    parser.add_argument("--poll-timeout", type=int, default=300, help="轮询超时秒数（默认 300）")
    args = parser.parse_args()

    invocation_ids = [i.strip() for i in args.invocation_ids.split(",") if i.strip()]
    if not invocation_ids:
        parser.error("--invocation-ids 解析为空")

    deadline = time.time() + args.poll_timeout if args.poll else None
    last_response: dict = {}

    while True:
        try:
            result = describe(invocation_ids, args.cluster_id, args.region,
                              offset=args.offset, limit=args.limit)
        except TencentCloudSDKException as err:
            print(
                f"[error] DescribeCommandExecution 调用失败（region={args.region}）：{err}",
                file=sys.stderr,
            )
            sys.exit(1)

        last_response = result.get("Response", {}) if isinstance(result, dict) else {}

        if not args.poll:
            break

        if all_terminal(last_response, len(invocation_ids)):
            break

        if deadline is not None and time.time() >= deadline:
            print(
                f"[warn] 轮询超时（{args.poll_timeout}s）未达终态，按当前快照返回",
                file=sys.stderr,
            )
            break

        time.sleep(args.poll_interval)

    print(
        json.dumps(
            {"region": args.region, "response": last_response},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
