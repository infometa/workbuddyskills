#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国国航 B2C 移动应用对外服务接口客户端
基于《中国国航B2C移动应用对外服务接口规范 v1.0.0》封装

协议底座：accessToken 鉴权 + MD5 签名 + AES/ECB/PKCS5 加密 + adapter/procedure 分发
业务接口：send_sms_code（短信验证码）、claim_coupon（领券）
"""

import os
import sys
import json
import time
import hashlib
import argparse
import base64
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    sys.stderr.write("缺少依赖 requests，请先执行：pip install requests\n")
    sys.exit(2)

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError:
    sys.stderr.write("缺少依赖 pycryptodome，请先执行：pip install pycryptodome\n")
    sys.exit(2)


# -----------------------------------------------------------------------------
# 硬编码配置（全部内置，无需任何外部环境变量）
# -----------------------------------------------------------------------------
# 国航签发给腾讯 WorkBuddy 的【生产】凭证
APP_ID = "2NhdoyHXf41wWutaM5kULzAD"
SECRET_KEY = "gXcWi1qzGUuo4KFOIASdCrE7"
# 渠道：国航分配给腾讯 WorkBuddy 的固定值
CHANNEL = "TENCENT"
SUB_CHANNEL = "OTA"
# 接口版本：文档 v1.0.0 的当前版本
SERVICE_VERSION = "10100"
# 网关地址：测试 9066 端口，生产 443 端口
GATEWAY = {
    "test": "https://m.airchina.com.cn:9066",
    "prod": "https://m.airchina.com.cn",
}
# 路径
AUTH_PATH = "/airchina/gateway/ota/v2.0/auth/getAccessToken"
SERVICE_PATH = "/airchina/gateway/ota/v2.0/api/services/"

# accessToken 本地缓存时长（文档规定 2 小时，留 10 分钟缓冲）
TOKEN_TTL_SECONDS = 110 * 60


# -----------------------------------------------------------------------------
# 异常定义
# -----------------------------------------------------------------------------
class AirChinaError(Exception):
    """国航接口调用异常基类"""


class AuthError(AirChinaError):
    """获取 accessToken 失败"""


class GatewayError(AirChinaError):
    """网关层 securityCode != 0000"""


class BusinessError(AirChinaError):
    """业务层 code 非成功码"""


# -----------------------------------------------------------------------------
# 客户端
# -----------------------------------------------------------------------------
class AirChinaClient:
    def __init__(
        self,
        env: Optional[str] = None,
        timeout: int = 15,
    ):
        # 所有凭证和渠道都硬编码在模块顶部常量里
        self.app_id = APP_ID
        self.secret_key = SECRET_KEY
        self.channel = CHANNEL
        self.sub_channel = SUB_CHANNEL
        self.service_version = SERVICE_VERSION
        # 环境切换：默认 prod，可传 "test" 或 AIRCHINA_ENV=test 临时覆盖
        self.env = env or os.environ.get("AIRCHINA_ENV", "prod")
        self.timeout = timeout

        if self.env not in GATEWAY:
            raise AirChinaError(f"未知环境：{self.env}，可选 test | prod")

        self._token: Optional[str] = None
        self._token_expire_at: float = 0.0

    # ---------- 协议底座 ----------
    @property
    def gateway(self) -> str:
        return GATEWAY[self.env]

    def get_access_token(self, force_refresh: bool = False) -> str:
        """获取 accessToken，内存缓存，过期自动刷新"""
        now = time.time()
        if not force_refresh and self._token and now < self._token_expire_at:
            return self._token

        url = self.gateway + AUTH_PATH
        params = {
            "appId": self.app_id,
            "secretKey": self.secret_key,
            "channel": self.channel,
            "subChannel": self.sub_channel,
        }
        resp = requests.post(url, params=params, data="{}",
                             headers={"Content-Type": "application/json"},
                             timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("securityCode") != "0000":
            raise AuthError(f"获取 accessToken 失败：{data}")
        token = data.get("accessToken")
        if not token:
            raise AuthError(f"响应缺少 accessToken：{data}")
        self._token = token
        self._token_expire_at = now + TOKEN_TTL_SECONDS
        return token

    @staticmethod
    def _sign(params: Dict[str, str]) -> str:
        """按文档 3.3.2：所有键值升序排序，拼成 k1=v1&k2=v2&...，整串 MD5
        注意：国航 MD5Util.Md5 返回**大写 hex**，必须大写，否则 securityCode=1000"""
        pairs = sorted(params.items(), key=lambda x: x[0])
        raw = "&".join(f"{k}={v}" for k, v in pairs)
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()

    @staticmethod
    def _aes_key(access_token: str) -> bytes:
        """文档 3.3.3：密钥 = accessToken 第 8~24 位（16 字节）"""
        key = access_token[8:24]
        if len(key) != 16:
            raise AirChinaError(f"accessToken 长度异常，无法截取 8~24 位生成密钥：len={len(access_token)}")
        return key.encode("utf-8")

    @classmethod
    def _encrypt(cls, access_token: str, plaintext: str) -> str:
        """AES/ECB/PKCS5Padding 加密，Base64 输出"""
        cipher = AES.new(cls._aes_key(access_token), AES.MODE_ECB)
        ct = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
        return base64.b64encode(ct).decode("utf-8")

    @classmethod
    def _decrypt(cls, access_token: str, ciphertext: str) -> str:
        """AES/ECB/PKCS5Padding 解密"""
        cipher = AES.new(cls._aes_key(access_token), AES.MODE_ECB)
        pt = unpad(cipher.decrypt(base64.b64decode(ciphertext)), AES.block_size)
        return pt.decode("utf-8")

    def invoke_service(
        self,
        adapter: str,
        procedure: str,
        req_payload: Dict[str, Any],
        lang: str = "zh_CN",
        raw: bool = False,
    ) -> Dict[str, Any]:
        """
        通用业务调用器：负责组 body → 签名 → 加密 → 组 header → 发请求 → 解密响应
        返回已解密的响应 JSON（含外层 securityCode/msg/resp）
        raw=True 时返回原始网关响应（resp 仍为密文），用于调试加密链路
        """
        token = self.get_access_token()
        url = self.gateway + SERVICE_PATH

        body_params = {
            "lang": lang,
            "timestamp": str(int(time.time() * 1000)),
            "req": json.dumps(req_payload, ensure_ascii=False, separators=(",", ":")),
        }

        # 文档 3.3.2：签名对 query+body 的所有键值做，本接口没有 query，只对 body 签
        sign_string = self._sign(body_params)

        # 组装明文 body（form-urlencoded 形式，但签名和加密都在这串上做）
        plaintext_body = "&".join(f"{k}={v}" for k, v in sorted(body_params.items()))
        encrypted_body = self._encrypt(token, plaintext_body)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "channel": self.channel,
            "subChannel": self.sub_channel,
            "appId": self.app_id,
            "accessToken": token,
            "signString": sign_string,
            "adapter": adapter,
            "procedure": procedure,
            "serviceVersion": self.service_version,
        }

        http_resp = requests.post(url, data=encrypted_body, headers=headers, timeout=self.timeout)
        http_resp.raise_for_status()
        envelope = http_resp.json()

        if envelope.get("securityCode") != "0000":
            raise GatewayError(f"网关返回错误：securityCode={envelope.get('securityCode')} msg={envelope.get('msg')}")

        if raw:
            return envelope

        enc_resp = envelope.get("resp") or ""
        if not enc_resp:
            return envelope
        try:
            decrypted = self._decrypt(token, enc_resp)
            # 国航响应解密后是 URL-encoded JSON（如 %7B%22msg%22%3A%22ok%22%7D），需再 URL-decode
            from urllib.parse import unquote
            decrypted = unquote(decrypted)
            envelope["resp"] = json.loads(decrypted)
        except Exception as e:
            raise AirChinaError(f"响应解密/解析失败：{e}；密文={enc_resp[:80]}...")
        return envelope

    # ---------- 业务接口 ----------
    def send_sms_code(self, phone: str, area_code: str = "86") -> Dict[str, Any]:
        """
        短信验证码接口
        adapter=ACOTADigitalProducts procedure=sendSMSVeriCodeActivity
        成功码：resp.code == "0"
        """
        envelope = self.invoke_service(
            adapter="ACOTADigitalProducts",
            procedure="sendSMSVeriCodeActivity",
            req_payload={"phone": phone, "areaCode": area_code},
        )
        resp = envelope.get("resp", {})
        if resp.get("code") != "0":
            raise BusinessError(f"发送短信失败：code={resp.get('code')} msg={resp.get('msg')}")
        return resp

    def claim_coupon(self, phone: str, veri_code: str, area_code: str = "86") -> Dict[str, Any]:
        """
        领券接口
        adapter=ACOTADigitalProducts procedure=tencentClaimCoupon
        成功码：resp.code == "00000000"
        返回的 resp 包含 couponList: [{couponCardCode, couponAmount, couponName, couponTypeCode}, ...]
        """
        envelope = self.invoke_service(
            adapter="ACOTADigitalProducts",
            procedure="tencentClaimCoupon",
            req_payload={
                "mobileNo": phone,
                "areaCode": area_code,
                "veriCode": veri_code,
            },
        )
        resp = envelope.get("resp", {})
        if resp.get("code") != "00000000":
            raise BusinessError(f"领券失败：code={resp.get('code')} msg={resp.get('msg')}")
        return resp


# -----------------------------------------------------------------------------
# CLI 入口
# -----------------------------------------------------------------------------
def _print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="中国国航 B2C 接口调用工具（基于规范 v1.0.0）",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check-env", help="检查环境变量是否齐备")

    p_token = sub.add_parser("get-token", help="获取 accessToken")
    p_token.add_argument("--force", action="store_true", help="强制刷新，忽略缓存")

    p_sms = sub.add_parser("send_sms_code", help="发送短信验证码")
    p_sms.add_argument("--phone", required=True)
    p_sms.add_argument("--area-code", default="86")

    p_coupon = sub.add_parser("claim_coupon", help="领券")
    p_coupon.add_argument("--phone", required=True)
    p_coupon.add_argument("--area-code", default="86")
    p_coupon.add_argument("--veri-code", required=True)

    p_inv = sub.add_parser("invoke", help="通用 adapter/procedure 调用器")
    p_inv.add_argument("--adapter", required=True)
    p_inv.add_argument("--procedure", required=True)
    p_inv.add_argument("--req", required=True, help="JSON 字符串，对应 body 的 req 字段")
    p_inv.add_argument("--lang", default="zh_CN")
    p_inv.add_argument("--raw", action="store_true", help="返回原始响应（resp 仍为密文）")

    args = parser.parse_args()

    if args.cmd == "check-env":
        env_mode = os.environ.get("AIRCHINA_ENV", "prod")
        out = {
            "—— 硬编码配置（全部内置，无需任何环境变量）——": "",
            "appId": APP_ID,
            "secretKey": f"{SECRET_KEY[:8]}... (长度 {len(SECRET_KEY)})",
            "channel": CHANNEL,
            "subChannel": SUB_CHANNEL,
            "serviceVersion": SERVICE_VERSION,
            "gateway": GATEWAY.get(env_mode, "unknown"),
            "运行环境": env_mode,
            "—— 可临时覆盖的环境变量 ——": "",
            "AIRCHINA_ENV=prod": "切换到生产环境",
        }
        _print_json(out)
        return

    client = AirChinaClient()

    if args.cmd == "get-token":
        _print_json({"accessToken": client.get_access_token(force_refresh=args.force)})
    elif args.cmd == "send_sms_code":
        _print_json(client.send_sms_code(phone=args.phone, area_code=args.area_code))
    elif args.cmd == "claim_coupon":
        _print_json(client.claim_coupon(
            phone=args.phone, area_code=args.area_code, veri_code=args.veri_code))
    elif args.cmd == "invoke":
        try:
            req_payload = json.loads(args.req)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"--req 不是合法 JSON：{e}\n")
            sys.exit(2)
        _print_json(client.invoke_service(
            adapter=args.adapter,
            procedure=args.procedure,
            req_payload=req_payload,
            lang=args.lang,
            raw=args.raw,
        ))


if __name__ == "__main__":
    try:
        main()
    except AirChinaError as e:
        sys.stderr.write(f"[国航接口错误] {e}\n")
        sys.exit(1)
