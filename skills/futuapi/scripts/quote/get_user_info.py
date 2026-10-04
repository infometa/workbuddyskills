#!/usr/bin/env python3
"""
获取用户信息（行情权限）

功能：查询当前用户的行情权限等级、订阅额度等信息
用法：python get_user_info.py

接口限制：
- 无特殊限频
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_quote_context,
    safe_close,
)


# 权限等级说明
QOT_RIGHT_DESC = {
    "N/A": "未知",
    "NO": "无权限",
    "BMP": "BMP（基础摘要）",
    "LV1": "LV1",
    "LV2": "LV2",
    "SF": "SF（已开通高级行情）",
}

# 权限字段 -> 显示名称
QOT_RIGHT_FIELDS = {
    "hk_qot_right": "港股",
    "us_qot_right": "美股",
    "cn_qot_right": "A股",
    "hk_option_qot_right": "港股期权",
    "hk_future_qot_right": "港股期货",
    "us_option_qot_right": "美股期权",
    "us_future_qot_right": "美股期货",
    "sg_future_qot_right": "新加坡期货",
    "jp_future_qot_right": "日本期货",
}


def get_user_info(output_json=False):
    ctx = None
    try:
        ctx = create_quote_context()
        ret, data = ctx.get_user_info()
        if ret != 0:
            raise RuntimeError(f"获取用户信息失败: {data}")

        if output_json:
            print(json.dumps(data, ensure_ascii=False))
        else:
            print("=" * 50)
            print("用户信息")
            print("=" * 50)
            print(f"  昵称:          {data.get('nick_name', 'N/A')}")
            print(f"  用户ID:        {data.get('user_id', 'N/A')}")
            print(f"  用户属性:      {data.get('user_attr', 'N/A')}")
            print(f"  订阅额度:      {data.get('sub_quota', 'N/A')}")
            print(f"  历史K线额度:   {data.get('history_kl_quota', 'N/A')}")
            print()
            print("  行情权限:")
            for field, label in QOT_RIGHT_FIELDS.items():
                level = data.get(field, "N/A")
                desc = QOT_RIGHT_DESC.get(level, level)
                print(f"    {label:<12} {desc}")
            print("=" * 50)

    except Exception as e:
        if output_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}")
        sys.exit(1)
    finally:
        safe_close(ctx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取用户信息（行情权限）")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    args = parser.parse_args()
    get_user_info(args.output_json)
