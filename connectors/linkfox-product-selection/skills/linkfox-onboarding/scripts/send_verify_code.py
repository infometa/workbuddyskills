#!/usr/bin/env python3
"""发送 LinkFox 注册/登录验证码。

用法：
    python scripts/send_verify_code.py <phone>

输出 JSON：
    成功：{"sent": true, "phone": "188****1234", "agreements": {...}}
    失败：{"sent": false, "phone": "188****1234", "errmsg": "..."}

调 POST https://api.linkfox.com/user/v1/web/login，method=getVerifyCode。
手机号在输出时脱敏（保留前 3 后 4），脚本内部仍用完整手机号调接口。
"""
from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])

from setup_common import _stderr_tag


AGREEMENTS = {
    "user_agreement": "https://agent.linkfox.com/agreement/term",
    "service_agreement": "https://agent.linkfox.com/agreement/service",
    "privacy_policy": "https://agent.linkfox.com/agreement/privacy",
}


def _mask_phone(phone: str) -> str:
    """脱敏：188****1234。"""
    if len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone


def send_verify_code(phone: str, area_code: str = "+86") -> dict:
    # 基础格式校验：国内手机号 11 位数字
    if not re.fullmatch(r"\d{11}", phone):
        return {"sent": False, "phone": _mask_phone(phone), "errmsg": f"手机号格式不正确（需 11 位数字）: {phone}"}
    body = {
        "type": "sms",
        "method": "getVerifyCode",
        "data": {"authPhone": phone, "areaCode": area_code},
    }
    from setup_common import login_post
    resp = login_post("/user/v1/web/login", body, with_uid=True)
    masked = _mask_phone(phone)
    if "_http_error" in resp or "_error" in resp:
        return {"sent": False, "phone": masked, "errmsg": resp.get("_body") or resp.get("_error", "未知错误")}
    # 响应信封：{"code":"OK","message":"成功","data":{},"success":true}
    if resp.get("success") or resp.get("code") == "OK":
        return {
            "sent": True,
            "phone": masked,
            "area_code": area_code,
            "agreements": AGREEMENTS,
        }
    return {"sent": False, "phone": masked, "errmsg": resp.get("message") or json.dumps(resp, ensure_ascii=False)}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(json.dumps({"sent": False, "errmsg": "用法: python send_verify_code.py <phone>"}, ensure_ascii=False))
        return 2
    phone = argv[1].strip()
    result = send_verify_code(phone)
    print(json.dumps(result, ensure_ascii=False))
    # stderr 仍保留协议链接，供不读 stdout JSON 的旧宿主兜底
    if result.get("sent"):
        print(
            f"{_stderr_tag()} 验证码已发送到 {result['phone']}。协议链接见 stdout JSON 的 agreements 字段。",
            file=sys.stderr,
        )
    return 0 if result.get("sent") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
