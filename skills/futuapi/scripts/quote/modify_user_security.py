#!/usr/bin/env python3
"""
修改自选股

功能：添加或删除自选股
用法：python modify_user_security.py "我的自选" ADD HK.00700 US.AAPL
      python modify_user_security.py "我的自选" DEL HK.00700

接口限制：
- 每 30 秒内最多请求 60 次

参数说明：
- op: ADD(添加), DEL(删除)
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
    RET_OK,
)


def modify_user_security(group_name, op, codes, output_json=False):
    ctx = None
    try:
        from futu import ModifyUserSecurityOp
        op_map = {
            "ADD": ModifyUserSecurityOp.ADD,
            "DEL": ModifyUserSecurityOp.DEL,
        }
        op_enum = op_map.get(op.upper())
        if op_enum is None:
            raise ValueError(f"不支持的操作: {op}，可选: ADD, DEL")

        ctx = create_quote_context()
        ret, data = ctx.modify_user_security(group_name, op_enum, codes)
        check_ret(ret, data, ctx, "修改自选股")

        if output_json:
            print(json.dumps({"result": "ok", "group_name": group_name, "op": op, "codes": codes}, ensure_ascii=False))
        else:
            action = "添加" if op.upper() == "ADD" else "删除"
            print(f"成功{action}自选股: {', '.join(codes)} -> 分组 \"{group_name}\"")

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修改自选股")
    parser.add_argument("group_name", help="自选股分组名称")
    parser.add_argument("op", choices=["ADD", "DEL"], help="操作类型")
    parser.add_argument("codes", nargs="+", help="股票代码列表")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    modify_user_security(args.group_name, args.op, args.codes, args.output_json)
