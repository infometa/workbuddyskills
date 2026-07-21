#!/usr/bin/env python3
"""AlarmVid 计算工具 - 用于 cwp DescribeAlarmIncidentNodes 入参

⭐ 不同告警类型的 AlarmVid 计算方式不同：
- 高危命令: md5(uuid + pid + bashcmd)
- 恶意请求: md5(uuid + domain)
- 木马:     md5(uuid + filepath)  — filepath 是木马文件的完整路径（FilePath 字段）

注意：不是每个告警都能查到事件图谱数据（需要有足够的进程链支撑），
查不到是正常情况，不影响其他溯源流程。

两种使用方式：
- 命令行：python3 alarm_vid.py {bash|malreq|trojan|raw} <参数...>
- 模块：  from alarm_vid import compute_alarm_vid
"""

import sys
import json
import argparse
import hashlib


def _md5(raw):
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def compute_alarm_vid(machine_uuid, alert_type, event):
    """根据告警类型计算 AlarmVid。

    Args:
        machine_uuid: 机器 Uuid
        alert_type:   告警类型名称（"高危命令"/"恶意请求"/"木马"）
        event:        告警事件原始数据 dict

    Returns:
        AlarmVid（md5 hex string）；字段缺失或类型未识别时返回空串。
    """
    raw = ""
    if alert_type == "高危命令":
        pid = str(event.get("Pid", ""))
        bash_cmd = event.get("BashCmd", "")
        if pid and bash_cmd:
            raw = f"{machine_uuid}{pid}{bash_cmd}"
    elif alert_type == "恶意请求":
        domain = event.get("Domain", "")
        if domain:
            raw = f"{machine_uuid}{domain}"
    elif alert_type == "木马":
        filepath = event.get("FilePath", "")
        if filepath:
            raw = f"{machine_uuid}{filepath}"
    return _md5(raw) if raw else ""


def main():
    parser = argparse.ArgumentParser(description="AlarmVid 计算工具 (cwp DescribeAlarmIncidentNodes)")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("bash", help="高危命令: md5(uuid + pid + bashcmd)")
    p.add_argument("uuid")
    p.add_argument("pid")
    p.add_argument("bashcmd")

    p = sub.add_parser("malreq", help="恶意请求: md5(uuid + domain)")
    p.add_argument("uuid")
    p.add_argument("domain")

    p = sub.add_parser("trojan", help="木马: md5(uuid + filepath)")
    p.add_argument("uuid")
    p.add_argument("filepath")

    p = sub.add_parser("raw", help="通用: md5(拼接所有参数)")
    p.add_argument("parts", nargs="+")

    p = sub.add_parser("event", help="从告警事件 JSON 计算: --uuid <uuid> --type <alert_type> --event <json>")
    p.add_argument("--uuid", required=True)
    p.add_argument("--type", dest="alert_type", required=True, choices=["高危命令", "恶意请求", "木马"])
    p.add_argument("--event", required=True, help="告警事件 JSON 字符串")

    args = parser.parse_args()

    if args.cmd == "bash":
        print(_md5(f"{args.uuid}{args.pid}{args.bashcmd}"))
    elif args.cmd == "malreq":
        print(_md5(f"{args.uuid}{args.domain}"))
    elif args.cmd == "trojan":
        print(_md5(f"{args.uuid}{args.filepath}"))
    elif args.cmd == "raw":
        print(_md5("".join(args.parts)))
    elif args.cmd == "event":
        try:
            event = json.loads(args.event)
        except json.JSONDecodeError as e:
            print(f"Error: invalid --event JSON: {e}", file=sys.stderr)
            sys.exit(1)
        print(compute_alarm_vid(args.uuid, args.alert_type, event))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
