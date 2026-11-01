import argparse
import json
from typing import Any

from resources import recommend_resources
from scnet_job_client import SCNetJobClient
from skill_auth import SkillAuthError, get_skill_auth


def build_client(args: argparse.Namespace) -> SCNetJobClient:
    explicit = (args.access_key, args.secret_key, args.user)
    if any(value is not None for value in explicit):
        if not all(isinstance(value, str) and value.strip() for value in explicit):
            raise SkillAuthError("INCOMPLETE_CREDENTIALS", "手动认证时必须同时提供 --access-key、--secret-key 和 --user。")
        return SCNetJobClient(*explicit)
    credentials = get_skill_auth()
    return SCNetJobClient(credentials["SCNET_AK"], credentials["SCNET_SK"], credentials["SCNET_USER"])


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def render_markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, separator, *body])


def run_clusters_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.get_clusters()
    if not result.get("success"):
        print_json(result)
        return 1

    print_json(result.get("clusters", []))
    return 0


def run_queues_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.get_available_queues(args.cluster_id)
    if not result.get("success"):
        print_json(result)
        return 1

    queues = result.get("queues", [])
    if not queues:
        print(f"队列查询成功，当前集群 {args.cluster_id} 下没有可用队列。")
        return 0

    print(render_markdown_table(queues, ["queueName", "queNodes", "queFreeNodes", "queFreeNcpus"]))
    return 0


def run_job_info_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.get_job_info(args.cluster_id, args.job_id)
    print_json(result)
    return 0 if result.get("success") else 1


def run_monitor_job_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.monitor_job(args.cluster_id, args.job_id)
    print_json(result)
    return 0 if result.get("success") else 1


def run_cancel_job_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.cancel_job(args.cluster_id, args.job_id)
    print_json(result)
    return 0 if result.get("success") else 1


def run_submit_job_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.submit_job(args.cluster_id, args.workdir, args.filename)
    print_json(result)
    return 0 if result.get("success") else 1


def run_upload_file_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.upload_file(
        args.cluster_id,
        args.local_file,
        args.remote_path,
        args.cover,
    )
    print_json(result)
    return 0 if result.get("success") else 1


def run_download_file_flow(args: argparse.Namespace) -> int:
    client = build_client(args)
    result = client.download_file(
        args.cluster_id,
        args.remote_path,
        args.local_path,
        args.byte_range,
    )
    print_json(result)
    return 0 if result.get("success") else 1


def run_recommend_resources_flow(args: argparse.Namespace) -> int:
    result = recommend_resources(
        keyWords=args.keywords,
        region=args.region,
    )
    print_json(result)
    return 0


def add_common_auth_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--access-key", help="可选：手动认证时与 --secret-key、--user 同时提供；默认使用 WorkBuddy OAuth")
    parser.add_argument("--secret-key", help="手动认证的 SCNet secret_key")
    parser.add_argument("--user", help="手动认证的 SCNet 平台用户名")


def main() -> int:
    parser = argparse.ArgumentParser(description="SCNet Job Manager CLI")
    subparsers = parser.add_subparsers(dest="flow", required=True)

    clusters_parser = subparsers.add_parser("clusters", help="查询可用集群")
    add_common_auth_args(clusters_parser)
    clusters_parser.set_defaults(handler=run_clusters_flow)

    queues_parser = subparsers.add_parser("queues", help="查询指定集群的队列")
    add_common_auth_args(queues_parser)
    queues_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    queues_parser.set_defaults(handler=run_queues_flow)

    job_info_parser = subparsers.add_parser("job-info", help="查询作业详情")
    add_common_auth_args(job_info_parser)
    job_info_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    job_info_parser.add_argument("--job-id", required=True, help="作业 ID")
    job_info_parser.set_defaults(handler=run_job_info_flow)

    monitor_parser = subparsers.add_parser("monitor-job", help="监控作业状态")
    add_common_auth_args(monitor_parser)
    monitor_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    monitor_parser.add_argument("--job-id", required=True, help="作业 ID")
    monitor_parser.set_defaults(handler=run_monitor_job_flow)

    cancel_parser = subparsers.add_parser("cancel-job", help="取消作业")
    add_common_auth_args(cancel_parser)
    cancel_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    cancel_parser.add_argument("--job-id", required=True, help="作业 ID")
    cancel_parser.set_defaults(handler=run_cancel_job_flow)

    submit_parser = subparsers.add_parser("submit-job", help="提交作业")
    add_common_auth_args(submit_parser)
    submit_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    submit_parser.add_argument("--workdir", required=True, help="作业工作目录")
    submit_parser.add_argument("--filename", required=True, help="slurm 脚本文件名")
    submit_parser.add_argument("--appname", required=False, default="BASE", help="应用名称，默认 BASE")
    submit_parser.set_defaults(handler=run_submit_job_flow)

    upload_parser = subparsers.add_parser("upload-file", help="上传文件到 SCNet 远端路径")
    add_common_auth_args(upload_parser)
    upload_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    upload_parser.add_argument("--local-file", required=True, help="本地文件路径")
    upload_parser.add_argument("--remote-path", required=True, help="SCNet 远端目录路径")
    upload_parser.add_argument(
        "--cover",
        required=False,
        default="cover",
        choices=["cover", "uncover"],
        help="是否覆盖同名文件，默认 cover",
    )
    upload_parser.set_defaults(handler=run_upload_file_flow)

    download_parser = subparsers.add_parser("download-file", help="下载 SCNet 远端文件或文件夹")
    add_common_auth_args(download_parser)
    download_parser.add_argument("--cluster-id", required=True, help="集群 ID")
    download_parser.add_argument("--remote-path", required=True, help="SCNet 远端文件或文件夹路径")
    download_parser.add_argument(
        "--local-path",
        required=False,
        default=None,
        help="本地保存路径。可指定文件路径或目录；默认使用远端文件名",
    )
    download_parser.add_argument(
        "--byte-range",
        required=False,
        default=None,
        help="断点下载 Range 头，例如 bytes=0-2000",
    )
    download_parser.set_defaults(handler=run_download_file_flow)

    resources_parser = subparsers.add_parser("recommend-resources", help="查询推荐的 CPU 资源")
    resources_parser.add_argument(
        "--keywords",
        required=False,
        default="",
        help="资源搜索关键词，默认为空",
    )
    resources_parser.add_argument(
        "--region",
        required=False,
        nargs="*",
        default=None,
        help="区域/集群 ID，可传入多个",
    )
    resources_parser.set_defaults(handler=run_recommend_resources_flow)

    args = parser.parse_args()
    try:
        return args.handler(args)
    except SkillAuthError as exc:
        print_json({"success": False, "error": {"stage": "get_skill_auth", "code": exc.code, "message": str(exc)}})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
