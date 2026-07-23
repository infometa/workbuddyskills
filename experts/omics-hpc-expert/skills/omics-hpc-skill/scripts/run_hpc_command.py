# -*- coding: utf-8 -*-
"""
组学平台 RunCommand —— HPC 集群命令下发脚本

用法：
  python3 run_hpc_command.py \
    --cluster-id <ClusterId> \
    --command '<shell command>' \
    [--command-file <path>] \
    [--node-id <NodeId>] \
    [--timeout <seconds>] \
    [--client-token <token>] \
    [--extra-params '<json>'] \
    [--run-as-user <username>] \
    [--region <REGION>]

输出：
  JSON：{"region": "...", "response": {"InvocationId": "...", "RequestId": "..."}}
  失败时 stderr 打印错误信息，exit 1。

--run-as-user：
  指定后，原始命令会被自动包装为 `su - <username> -c '<原始命令>'`，
  使得命令以指定用户身份而非 root 执行。
  典型场景：提交 SLURM (sbatch) 或 SGE (qsub) 作业时，需要以普通用户身份提交。
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

# 统一接入点：腾讯云 omics 服务单一域名，由腾讯云就近接入。
# RunCommand 本身不受地域限制，region 在这里仅作为 SDK 签名占位。
DEFAULT_ENDPOINT = "omics.tencentcloudapi.com"

def resolve_endpoint(region: str) -> str:  # 保留函数名以免外部调用者依赖；返回固定 endpoint
    return DEFAULT_ENDPOINT


def load_command(args) -> str:
    """从 --command 或 --command-file 加载命令内容。两者同传时以 --command-file 为准。"""
    if args.command_file:
        with open(args.command_file, "r", encoding="utf-8") as f:
            return f.read()
    return args.command or ""


def wrap_command_as_user(command: str, username: str) -> str:
    """将原始命令包装为以指定用户身份执行。

    使用 `su - <username> -c '<command>'` 实现用户切换。
    原始命令中的单引号会被转义，确保命令字符串安全嵌套。

    参数：
        command:  原始 shell 命令字符串
        username: 目标用户名

    返回：
        包装后的命令字符串，形如 `su - alice -c 'sbatch job.sh'`
    """
    # 转义原始命令中的单引号：' -> '\''（即先关闭引号、转义单引号、再重新开启引号）
    escaped = command.replace("'", "'\\''")
    return f"su - {username} -c '{escaped}'"


def build_params(args) -> dict:
    """根据命令行参数拼接 RunCommand 入参。

    真实字段（按样例验证）：
      ClusterId / Command / NodeId / Timeout / ClientToken
    其余字段通过 --extra-params 透传，避免脚本与 SDK 字段集合写死。
    """
    params: dict = {
        "ClusterId": args.cluster_id,
        "Command": load_command(args),
    }
    # 如果指定了 --run-as-user，将命令包装为以该用户身份执行
    if args.run_as_user:
        params["Command"] = wrap_command_as_user(params["Command"], args.run_as_user)
    if args.node_id:
        params["NodeId"] = args.node_id
    if args.timeout is not None:
        params["Timeout"] = args.timeout
    if args.client_token:
        params["ClientToken"] = args.client_token

    if args.extra_params:
        try:
            extra = json.loads(args.extra_params)
        except json.JSONDecodeError as e:
            print(f"[error] --extra-params 不是合法 JSON：{e}", file=sys.stderr)
            sys.exit(2)
        if not isinstance(extra, dict):
            print("[error] --extra-params 必须是一个 JSON 对象", file=sys.stderr)
            sys.exit(2)
        params.update(extra)

    return params


def run_command(params: dict, region: str) -> dict:
    """调用 RunCommand，返回原始 dict。"""
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
    return common_client.call_json("RunCommand", params)


def main() -> None:
    parser = argparse.ArgumentParser(description="腾讯云组学平台 RunCommand —— 在 HPC 集群上下发 Shell 命令")
    parser.add_argument("--cluster-id", required=True, help="集群 ID（如 hpc-9jragud9）")
    group = parser.add_argument_group("命令内容（二选一）")
    group.add_argument("--command", default="", help="命令内容（shell 字符串）")
    group.add_argument("--command-file", default="", help="命令内容文件路径（与 --command 同传时优先）")

    parser.add_argument("--node-id", default="", help="目标节点 ID（不传则按服务端默认调度，通常落在 manager 节点）")
    parser.add_argument("--timeout", type=int, default=None, help="命令超时（秒）")
    parser.add_argument("--client-token", default="", help="幂等 Token（可选，用于避免重试时重复下发）")
    parser.add_argument("--extra-params", default="", help="额外透传给 RunCommand 的 JSON 参数")
    parser.add_argument(
        "--run-as-user",
        default="",
        help="以指定用户身份执行命令（自动包装为 su - <user> -c '...'）；典型场景：以普通用户而非 root 提交 SLURM/SGE 作业",
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help="SDK 签名用的 region（X-TC-Region）；RunCommand 不受地域限制，默认 ap-guangzhou 即可",
    )

    args = parser.parse_args()

    if not args.command and not args.command_file:
        parser.error("--command 与 --command-file 至少要传一个")

    params = build_params(args)

    try:
        result = run_command(params, args.region)
    except TencentCloudSDKException as err:
        print(f"[error] RunCommand 调用失败（region={args.region}）：{err}", file=sys.stderr)
        sys.exit(1)

    response = result.get("Response", {}) if isinstance(result, dict) else {}
    if not response.get("InvocationId"):
        # 没拿到 InvocationId 视为失败（即便服务端没抛异常）
        print(
            json.dumps(
                {"region": args.region, "response": response, "warning": "未返回 InvocationId"},
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    print(
        json.dumps(
            {"region": args.region, "response": response},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
