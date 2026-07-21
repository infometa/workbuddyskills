#!/usr/bin/env python3
"""
获取自选股分组

功能：获取用户的自选股分组列表
用法：python get_user_security_group.py

接口限制：
- 每 30 秒内最多请求 60 次

返回字段说明：
- group_id: 分组 ID
- group_name: 分组名称
- group_type: 分组类型
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_quote_context,
    check_ret,
    safe_close,
    is_empty,
    df_to_records,
)


def get_user_security_group(group_type=None, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        kwargs = {}
        if group_type is not None:
            from futu import UserSecurityGroupType
            type_map = {
                "ALL": UserSecurityGroupType.ALL,
                "CUSTOM": UserSecurityGroupType.CUSTOM,
                "SYSTEM": UserSecurityGroupType.SYSTEM,
            }
            t = type_map.get(group_type.upper())
            if t is not None:
                kwargs["group_type"] = t

        ret, data = ctx.get_user_security_group(**kwargs)
        check_ret(ret, data, ctx, "获取自选股分组")

        if is_empty(data):
            if output_json:
                print(json.dumps({"data": []}))
            else:
                print("无自选股分组")
            return

        if output_json:
            print(json.dumps({"data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print("自选股分组")
            print("=" * 70)
            print(data.to_string(index=False))
            print("=" * 70)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取自选股分组")
    parser.add_argument("--group-type", choices=["ALL", "CUSTOM", "SYSTEM"], default=None, help="分组类型")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_user_security_group(args.group_type, args.output_json)
