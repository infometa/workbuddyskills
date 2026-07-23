# -*- coding: utf-8 -*-
"""
组学平台 DescribeHPCClusters —— 列出 / 筛选 omics-hpc 集群

用法：
  python3 describe_hpc_clusters.py \
    [--cluster-id <id1,id2,...>] \
    [--name <name1,name2,...>] \
    [--status <RUNNING,...>] \
    [--confirm-deadline-lt <YYYY-MM-DDTHH:MM:SS+08:00>] \
    [--filter '<json array>'] \
    [--offset 0] [--limit 20] \
    [--region <REGION>]

输出：
  JSON：{"region": "...", "response": {"Clusters": [...], "TotalCount": N, "RequestId": "..."}}

说明：
  Filters 元素结构：{"Name": "ClusterId|Name|Status|ConfirmDeadlineLt", "Values": [...]}。
  --filter 直接透传一个 JSON 数组用于覆盖未列举过滤器；与 --cluster-id/--name/--status/
  --confirm-deadline-lt 等便捷参数会按"同名以 --filter 为准"的规则合并。
"""
import argparse
import json
import os
import sys

from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

DEFAULT_REGION = "ap-guangzhou"
SERVICE = "omics"
VERSION = "2022-11-28"

# 统一接入点：腾讯云 omics 服务使用单一域名，由腾讯云就近接入；
# 业务地域通过 X-TC-Region（SDK CommonClient 的 region 形参）传递。
DEFAULT_ENDPOINT = "omics.tencentcloudapi.com"


def split_csv(value: str) -> list:
    """英文逗号分隔的字符串 → 去空白的列表。"""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def build_filters(args) -> list:
    """组合 --cluster-id / --name / --status / --confirm-deadline-lt 与 --filter 到 Filters。"""
    filters_by_name: dict = {}

    def put(name: str, values: list) -> None:
        if values:
            filters_by_name[name] = {"Name": name, "Values": values}

    put("ClusterId", split_csv(args.cluster_id))
    put("Name", split_csv(args.name))
    put("Status", split_csv(args.status))
    if args.confirm_deadline_lt:
        put("ConfirmDeadlineLt", [args.confirm_deadline_lt])

    if args.filter:
        try:
            extra = json.loads(args.filter)
        except json.JSONDecodeError as e:
            print(f"[error] --filter 不是合法 JSON：{e}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(extra, list):
            print("[error] --filter 必须是一个 JSON 数组", file=sys.stderr)
            sys.exit(2)
        for item in extra:
            if not isinstance(item, dict) or "Name" not in item:
                print("[error] --filter 元素必须是 {Name, Values} 对象", file=sys.stderr)
                sys.exit(2)
            filters_by_name[item["Name"]] = item  # 同名以 --filter 为准

    return list(filters_by_name.values())


def build_params(args) -> dict:
    params: dict = {}
    filters = build_filters(args)
    if filters:
        params["Filters"] = filters
    if args.offset is not None:
        params["Offset"] = args.offset
    if args.limit is not None:
        params["Limit"] = args.limit
    return params


def describe(params: dict, region: str) -> dict:
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
    http_profile.endpoint = DEFAULT_ENDPOINT
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    # region 这里是真正的「业务地域」——决定查哪一片地域下的集群（X-TC-Region 头）。
    common_client = CommonClient(SERVICE, VERSION, cred, region, profile=client_profile)
    return common_client.call_json("DescribeHPCClusters", params)


def main() -> None:
    parser = argparse.ArgumentParser(description="腾讯云组学平台 DescribeHPCClusters —— 列出 omics-hpc 集群")
    parser.add_argument("--cluster-id", default="", help="按 ClusterId 过滤（多个用英文逗号分隔）")
    parser.add_argument("--name", default="", help="按 Name 过滤（多个用英文逗号分隔）")
    parser.add_argument("--status", default="", help="按 Status 过滤（多个用英文逗号分隔，如 RUNNING,UPGRADING）")
    parser.add_argument(
        "--confirm-deadline-lt",
        default="",
        help="按 ConfirmDeadlineLt 过滤（如 2026-01-13T16:00:00+08:00）",
    )
    parser.add_argument(
        "--filter",
        default="",
        help='直接透传 Filters 的 JSON 数组（如 \'[{"Name":"Status","Values":["RUNNING"]}]\'）',
    )
    parser.add_argument("--offset", type=int, default=None, help="分页起始位置（可选）")
    parser.add_argument("--limit", type=int, default=None, help="分页大小（可选）")
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help="业务地域（X-TC-Region），决定查哪个地域下的集群，集群是按地域隔离的；默认 ap-guangzhou",
    )

    args = parser.parse_args()
    params = build_params(args)

    try:
        result = describe(params, args.region)
    except TencentCloudSDKException as err:
        print(
            f"[error] DescribeHPCClusters 调用失败（region={args.region}）：{err}",
            file=sys.stderr,
        )
        sys.exit(1)

    response = result.get("Response", {}) if isinstance(result, dict) else {}
    print(
        json.dumps(
            {"region": args.region, "response": response},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
