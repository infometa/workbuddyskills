#!/usr/bin/env python3
"""
获取交易账户列表

功能：查询当前登录用户的所有交易账户
用法：python get_accounts.py

接口限制：
- 无特殊限频

返回字段说明：
- card_num: 综合账户下包含一个或多个业务账户（综合证券、综合期货等），与交易品种有关
- trdmarket_auth: 账户可交易的市场列表
- acc_role: MASTER=主账户，NORMAL=普通账户
"""
import argparse
import json
import sys
import os as _os
sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
from common import (
    create_trade_context,
    check_ret,
    safe_close,
    is_empty,
    safe_get,
    safe_int,
    format_enum,
)

from futu import SecurityFirm


# All SecurityFirm enum values to try
_ALL_SECURITY_FIRMS = [
    SecurityFirm.NONE,
    SecurityFirm.FUTUSECURITIES,
    SecurityFirm.FUTUINC,
    SecurityFirm.FUTUSG,
    SecurityFirm.FUTUAU,
    SecurityFirm.FUTUCA,
    SecurityFirm.FUTUJP,
    SecurityFirm.FUTUMY,
]


def _parse_account_row(row):
    """Parse a single account row into a dict."""
    trdmarket_auth_raw = safe_get(row, "trdmarket_auth", default=[])
    if isinstance(trdmarket_auth_raw, str):
        trdmarket_auth = [s.strip() for s in trdmarket_auth_raw.strip("[]").split(",") if s.strip()]
    elif isinstance(trdmarket_auth_raw, list):
        trdmarket_auth = [format_enum(m) for m in trdmarket_auth_raw]
    else:
        trdmarket_auth = []
    return {
        "acc_id": safe_int(safe_get(row, "acc_id", default=0)),
        "acc_type": format_enum(safe_get(row, "acc_type", default="")),
        "acc_role": format_enum(safe_get(row, "acc_role", default="")),
        "trd_env": format_enum(safe_get(row, "trd_env", default="")),
        "card_num": safe_get(row, "card_num", default=""),
        "security_firm": format_enum(safe_get(row, "security_firm", default="")),
        "trdmarket_auth": trdmarket_auth,
        "acc_status": format_enum(safe_get(row, "acc_status", default="")),
    }


def get_accounts(output_json=False, show_disabled=False):
    seen_acc_ids = set()
    accounts = []

    for firm in _ALL_SECURITY_FIRMS:
        ctx = None
        try:
            ctx = create_trade_context(market="NONE", security_firm=firm)
            ret, data = ctx.get_acc_list()
            if ret != 0 or is_empty(data):
                continue
            for i in range(len(data)):
                row = data.iloc[i] if hasattr(data, "iloc") else data[i]
                acc = _parse_account_row(row)
                if acc["acc_id"] not in seen_acc_ids:
                    if not show_disabled and acc["acc_status"] == "DISABLED":
                        continue
                    seen_acc_ids.add(acc["acc_id"])
                    accounts.append(acc)
        except Exception:
            pass
        finally:
            safe_close(ctx)

    if not accounts:
        if output_json:
            print(json.dumps({"accounts": []}))
        else:
            print("无账户数据")
        return

    if output_json:
        print(json.dumps({"accounts": accounts}, ensure_ascii=False))
    else:
        print("=" * 70)
        print("交易账户列表")
        print("=" * 70)
        for a in accounts:
            print(f"\n  账户 ID: {a['acc_id']}")
            print(f"    类型: {a['acc_type']}  角色: {a['acc_role']}  环境: {a['trd_env']}  券商: {a['security_firm']}")
            print(f"    交易市场权限: {', '.join(a['trdmarket_auth']) if a['trdmarket_auth'] else 'N/A'}")
        print("\n" + "=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取交易账户列表")
    parser.add_argument("--json", action="store_true", dest="output_json", help="输出 JSON 格式")
    parser.add_argument("--show-disabled", action="store_true", help="显示 DISABLED 状态的账户")
    args = parser.parse_args()
    get_accounts(args.output_json, show_disabled=args.show_disabled)
