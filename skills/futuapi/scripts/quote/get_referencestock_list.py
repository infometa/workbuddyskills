#!/usr/bin/env python3
"""
获取关联数据

功能：获取正股关联的窝轮、期货等数据
用法：python get_referencestock_list.py HK.00700 WARRANT

接口限制：
- 每 30 秒内最多请求 60 次

参数说明：
- reference_type: WARRANT(窝轮), FUTURE(期货)
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
    SecurityReferenceType,
)


def get_referencestock_list(code, reference_type, output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        type_map = {
            "WARRANT": SecurityReferenceType.WARRANT,
            "FUTURE": SecurityReferenceType.FUTURE,
        }
        sec_type = type_map.get(reference_type.upper())
        if sec_type is None:
            raise ValueError(f"不支持的关联类型: {reference_type}，可选: {list(type_map.keys())}")

        ret, data = ctx.get_referencestock_list(code, sec_type)
        check_ret(ret, data, ctx, "获取关联数据")

        if is_empty(data):
            if output_json:
                print(json.dumps({"code": code, "reference_type": reference_type, "data": []}))
            else:
                print("无关联数据")
            return

        if output_json:
            print(json.dumps({"code": code, "reference_type": reference_type, "data": df_to_records(data)}, ensure_ascii=False))
        else:
            print("=" * 70)
            print(f"关联数据 - {code} ({reference_type})")
            print("=" * 70)
            print(data.to_string(index=False))
            print(f"\n共 {len(data)} 条记录")
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
    parser = argparse.ArgumentParser(description="获取关联数据（窝轮/期货等）")
    parser.add_argument("code", help="正股代码，如 HK.00700")
    parser.add_argument("reference_type", choices=["WARRANT", "FUTURE"], help="关联类型")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_referencestock_list(args.code, args.reference_type, args.output_json)
