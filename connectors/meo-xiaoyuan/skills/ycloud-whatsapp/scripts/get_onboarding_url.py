#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 DealClaw 拉取 WhatsApp onboardingUrl（纯标准库）。"""

from __future__ import print_function

import argparse
import json
import sys
import time

try:
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
except ImportError:  # pragma: no cover - Python 2 fallback not supported
    raise SystemExit("需要 Python 3.8+")

DEFAULT_BASE = "https://dealclaw.datathink.com/whatsapp/api/whatsapp/wabas"


def _ensure_utf8_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def fetch_wabas(customer_id, base_url, timeout):
    query = urlencode({"partnerCustomerId": customer_id})
    url = "%s?%s" % (base_url, query)
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "ycloud-whatsapp-skill/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def pick_onboarding(wabas, now_ms=None):
    """选取可交付给用户的 onboarding 记录。"""
    if now_ms is None:
        now_ms = int(time.time() * 1000)

    bound = []
    pending = []
    for item in wabas or []:
        if not isinstance(item, dict):
            continue
        if item.get("wabaId"):
            bound.append(item)
            continue
        url = item.get("onboardingUrl")
        if not url:
            continue
        expires = item.get("expiresAt")
        if expires is not None and int(expires) <= now_ms:
            continue
        pending.append(item)

    pending.sort(key=lambda x: int(x.get("expiresAt") or 0), reverse=True)
    return bound, pending


def main(argv=None):
    _ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description="获取 YCloud WhatsApp onboardingUrl")
    parser.add_argument("--customer-id", required=True, help="partnerCustomerId")
    parser.add_argument("--base-url", default=DEFAULT_BASE, help="wabas 接口地址")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP 超时秒数")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="打印完整 JSON 响应（含全部 wabas）",
    )
    args = parser.parse_args(argv)

    try:
        data = fetch_wabas(args.customer_id, args.base_url, args.timeout)
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(
            json.dumps(
                {"ok": False, "http": e.code, "error": err_body or str(e)},
                ensure_ascii=False,
            )
        )
        return 1
    except URLError as e:
        print(json.dumps({"ok": False, "error": str(e.reason)}, ensure_ascii=False))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1

    if args.raw:
        print(json.dumps({"ok": True, "data": data}, ensure_ascii=False, indent=2))
        return 0

    wabas = data.get("wabas") if isinstance(data, dict) else None
    if wabas is None and isinstance(data, list):
        wabas = data

    bound, pending = pick_onboarding(wabas)
    if bound and not pending:
        first = bound[0]
        print(
            json.dumps(
                {
                    "ok": True,
                    "already_connected": True,
                    "partnerCustomerId": data.get("partnerCustomerId")
                    if isinstance(data, dict)
                    else args.customer_id,
                    "wabaId": first.get("wabaId"),
                    "wabaName": first.get("wabaName"),
                    "phoneNumberId": first.get("phoneNumberId"),
                    "status": first.get("status"),
                    "paymentMethodAttached": first.get("paymentMethodAttached"),
                    "message": "已存在绑定的 WABA，无需再发 onboardingUrl",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not pending:
        print(
            json.dumps(
                {
                    "ok": False,
                    "partnerCustomerId": data.get("partnerCustomerId")
                    if isinstance(data, dict)
                    else args.customer_id,
                    "error": "未找到未过期的 onboardingUrl",
                    "waba_count": len(wabas or []),
                    "bound_count": len(bound),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    chosen = pending[0]
    print(
        json.dumps(
            {
                "ok": True,
                "already_connected": False,
                "partnerCustomerId": data.get("partnerCustomerId")
                if isinstance(data, dict)
                else args.customer_id,
                "onboardingUrl": chosen.get("onboardingUrl"),
                "expiresAt": chosen.get("expiresAt"),
                "expiresAtIso": chosen.get("expiresAtIso"),
                "status": chosen.get("status"),
                "locale": chosen.get("locale"),
                "onboardingType": chosen.get("onboardingType"),
                "id": chosen.get("id"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
