#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 iOA 全部终端，并附带「内置终端分组（组织架构分组）」与「自定义分组」信息。

数据来源（均为只读云规范接口）：
  1) Assets/DescribeDevices           —— 终端列表详情（分页），每条自带 GroupId/GroupName/GroupNamePath（内置分组）
  2) Assets/DescribeDeviceGroups      —— 内置终端分组树（Id/Name/NamePath/ParentId/Count 等）
  3) Assets/DescribeDeviceVirtualGroups —— 自定义分组列表（Id/DeviceVirtualGroupName/DeviceCount 等）

用法：
  # 方式一：用技能里的客户配置
  python fetch_devices_with_groups.py --config ../configs/<customer>.json

  # 方式二：用环境变量 IOA_BASE_URL / IOA_SECRET_ID / IOA_SECRET_KEY
  python fetch_devices_with_groups.py

  # 可选参数
  --os-type 0系统类型 0:win 1:linux 2:mac 4:android 5:ios（默认 0）
  --page-size 200        每页数量（默认 200）
  --out devices.json     结果落盘为 JSON（默认只打印摘要）
  --path8私有化 8.0 以后版本用新path（Assets/Device/Describe...）

说明：
  - 终端「所属分组」= 内置分组（组织架构），字段 GroupName / GroupNamePath 已在设备详情里返回。
  - 「自定义分组」是另一套虚拟分组，一台终端可属于 0..N 个自定义分组；
    云规范的设备详情接口不直接吐出自定义分组归属，因此本脚本用
    Assets/DescribeDeviceVirtualGroups 拉出所有自定义分组清单一并给出（含每组终端数）。
"""

import argparse
import json
import sys

# 复用技能自带的签名客户端与配置加载
try:
    from config import load_config
    from ioa_client import IOAOpenApiClient
except ImportError:
    # 允许从其它目录运行
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import load_config
    from ioa_client import IOAOpenApiClient


def _items(data):
    """从已解析的 Response 里取分页 Items。"""
    if isinstance(data, dict):
        d = data.get("Data")
        if isinstance(d, dict):
            return d.get("Items") or []
        if isinstance(d, list):
            return d
    return []


def _paging_total(data):
    if isinstance(data, dict):
        d = data.get("Data") or {}
        page = d.get("Paging") or d.get("Page") or {}
        return int(page.get("Total") or 0)
    return 0


def fetch_all_devices(client, action, os_type=0, page_size=200):
    """分页拉取全部终端。"""
    all_items = []
    page = 1
    while True:
        body = {
            "Condition": {"PageNum": page, "PageSize": page_size},
            "OsType": os_type,
        }
        ok, msg, data = client.call(action, body)
        if not ok:
            raise RuntimeError(f"查询终端失败(page={page}): {msg}")
        items = _items(data)
        all_items.extend(items)
        total = _paging_total(data)
        if not items or len(all_items) >= total or len(items) < page_size:
            break
        page += 1
    return all_items


def fetch_device_groups(client, action, os_type=0):
    """拉取内置终端分组树（组织架构分组）。返回 Id -> 分组信息 的映射。"""
    ok, msg, data = client.call(action, {"OsType": os_type, "ParentId": 0})
    if not ok:
        # 分组信息取不到不致命，返回空
        print(f"[warn] 查询内置终端分组失败: {msg}", file=sys.stderr)
        return {}
    groups = {}
    for g in _items(data):
        groups[g.get("Id")] = {
            "Id": g.get("Id"),
            "Name": g.get("Name"),
            "NamePath": g.get("NamePath"),
            "ParentId": g.get("ParentId"),
            "Count": g.get("Count"),
            "IsLeaf": g.get("IsLeaf"),
        }
    return groups


def fetch_virtual_groups(client, action, os_type=0):
    """拉取自定义分组（虚拟分组）列表。VirtualGroupType=0 含普通+内置。"""
    ok, msg, data = client.call(action, {"OsType": os_type, "VirtualGroupType": 0})
    if not ok:
        print(f"[warn] 查询自定义分组失败: {msg}", file=sys.stderr)
        return []
    result = []
    for v in _items(data):
        result.append({
            "Id": v.get("Id"),
            "Name": v.get("DeviceVirtualGroupName"),
            "EnName": v.get("EnDeviceVirtualGroupName"),
            "DeviceCount": v.get("DeviceCount"),
            "Description": v.get("Description"),
            "Status": v.get("Status"),
            "InsideId": v.get("InsideId"),
        })
    return result


def simplify_device(d, group_map):
    """抽取终端关键字段 + 补齐内置分组信息。"""
    gid = d.get("GroupId")
    g = group_map.get(gid, {})
    return {
        "DeviceId": d.get("DeviceId") or d.get("Id"),
        "Mid": d.get("Mid"),
        "Name": d.get("Name") or d.get("ComputerName"),
        "ComputerName": d.get("ComputerName"),
        "Ip": d.get("Ip"),
        "LocalIpList": d.get("LocalIpList"),
        "MacAddr": d.get("MacAddr"),
        "Os": d.get("Os"),
        "OsType": d.get("OsType"),
        "OnlineStatus": d.get("OnlineStatus"),        # 1/2 在线，0 离线
        "IOAUserName": d.get("IOAUserName"),
        "UserName": d.get("UserName"),
        # ---- 内置分组（组织架构分组）----
        "GroupId": gid,
        "GroupName": d.get("GroupName") or g.get("Name"),
        "GroupNamePath": d.get("GroupNamePath") or g.get("NamePath"),
    }


def main():
    parser = argparse.ArgumentParser(description="获取 iOA 终端及分组信息")
    parser.add_argument("--config", help="客户配置 JSON 路径（不传则读环境变量）")
    parser.add_argument("--os-type", type=int, default=0,
                        help="系统类型 0:win 1:linux 2:mac 4:android 5:ios")
    parser.add_argument("--page-size", type=int, default=200, help="每页数量")
    parser.add_argument("--out", help="结果落盘 JSON 路径")
    parser.add_argument("--path8", action="store_true",
                        help="私有化 8.0+ 使用新 path（Assets/Device/Describe...）")
    args = parser.parse_args()

    cfg = load_config(args.config)
    client = IOAOpenApiClient(cfg)

    # 8.0 前后 path 不同
    if args.path8:
        act_devices = "Assets/Device/DescribeDevices"
        act_groups = "Assets/Device/DescribeDeviceGroups"
        act_vgroups = "Assets/Device/DescribeDeviceVirtualGroups"
    else:
        act_devices = "Assets/DescribeDevices"
        act_groups = "Assets/DescribeDeviceGroups"
        act_vgroups = "Assets/DescribeDeviceVirtualGroups"

    # 1) 内置分组树 -> 映射
    group_map = fetch_device_groups(client, act_groups, args.os_type)

    # 2) 自定义分组清单
    virtual_groups = fetch_virtual_groups(client, act_vgroups, args.os_type)

    # 3) 全部终端
    raw_devices = fetch_all_devices(client, act_devices, args.os_type, args.page_size)
    devices = [simplify_device(d, group_map) for d in raw_devices]

    result = {
        "device_count": len(devices),
        "devices": devices,
        "builtin_groups": list(group_map.values()),   # 内置/组织架构分组
        "virtual_groups": virtual_groups,             # 自定义分组
    }

    # 摘要打印
    print(f"共获取终端 {len(devices)} 台；"
          f"内置分组 {len(group_map)} 个；自定义分组 {len(virtual_groups)} 个。")
    for d in devices[:20]:
        print(f"  - {d['Name'] or d['DeviceId']:<24} "
              f"IP={d['Ip'] or '-':<16} "
              f"分组={d['GroupNamePath'] or d['GroupName'] or '-'}")
    if len(devices) > 20:
        print(f"  ... 其余 {len(devices) - 20} 台省略")

    if virtual_groups:
        print("\n自定义分组：")
        for v in virtual_groups:
            print(f"  - {v['Name']}（Id={v['Id']}, 终端数={v['DeviceCount']}）")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n已写入 {args.out}")

    return result


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
