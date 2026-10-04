"""
iOA 云规范接口签名（TC3-HMAC-SHA256）。

实现与 iOA 私有化后台一致的签名算法：
- 规范请求串 CanonicalRequest = Method + URI + Query + Headers + SignedHeaders + HashedBody
- 凭证范围 CredentialScope = Date / Service / tc3_request
- 默认 Service 取请求 path 第一段（私有化为 "capi"）；SaaS 场景可在配置里覆盖为 "ioa"

参考：references/api-docs/接口调用说明.md
"""

import hashlib
import hmac
import json
import time
import urllib.parse
import uuid
from typing import Any, Dict, Optional


ALGORITHM = "TC3-HMAC-SHA256"
DEFAULT_API_VERSION = "2022-06-01"


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def gen_nonce() -> str:
    return uuid.uuid4().hex


def _canonical_request(method: str, canonical_uri: str, query: str,
                       headers: Dict[str, str], body: Any) -> str:
    signed_headers = ""
    canonical_headers = ""
    for k in sorted(headers.keys()):
        signed_headers += ";" + k.strip()
        canonical_headers += "\n" + k.strip() + ":" + str(headers[k])
    signed_headers = signed_headers[1:].lower() if signed_headers else ""
    canonical_headers = canonical_headers.strip().lower() + "\n"

    body_str = body if isinstance(body, str) else json.dumps(body, separators=(",", ":"))
    hashed_body = hashlib.sha256(body_str.encode("utf-8")).hexdigest()
    req = (
        method + "\n"
        + canonical_uri + "\n"
        + query + "\n"
        + canonical_headers + "\n"
        + signed_headers + "\n"
        + hashed_body
    )
    return req, signed_headers


def build_authorization(secret_id: str, secret_key: str, method: str,
                        canonical_uri: str, sign_headers: Dict[str, str],
                        body: Any, service: Optional[str] = None,
                        timestamp_offset: int = 0):
    """生成 Authorization 头与时间戳。

    返回 (authorization, timestamp_str)
    """
    ts = time.time() + timestamp_offset
    timestamp = str(int(ts))

    canonical_request, signed_headers = _canonical_request(
        method, canonical_uri, "", sign_headers, body)
    hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()

    date = time.strftime("%Y-%m-%d", time.localtime(ts))
    if not service:
        uri_path = canonical_uri[1:] if canonical_uri.startswith("/") else canonical_uri
        service = uri_path.split("/", 1)[0] if "/" in uri_path else uri_path

    scope = f"{date}/{service}/tc3_request"
    string_to_sign = ALGORITHM + "\n" + timestamp + "\n" + scope + "\n" + hashed_canonical

    secret_date = _hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, service)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    authorization = (
        ALGORITHM
        + " Credential=" + secret_id + "/" + scope
        + ", SignedHeaders=" + signed_headers
        + ", Signature=" + signature
    )
    return authorization, timestamp


def build_signed_headers(config: Dict, canonical_uri: str, body: Any,
                         version: Optional[str] = DEFAULT_API_VERSION) -> Dict[str, str]:
    """构造一次调用所需的全部 HTTP 头（含签名）。"""
    nonce = gen_nonce()
    # 参与签名的最小头集合
    sign_headers = {"content-type": "application/json;charset=utf-8"}

    authorization, timestamp = build_authorization(
        secret_id=config["secret_id"],
        secret_key=config["secret_key"],
        method="POST",
        canonical_uri=canonical_uri,
        sign_headers=sign_headers,
        body=body,
        service=config.get("service") or None,
        timestamp_offset=int(config.get("timestamp_offset", 0)),
    )

    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "X-TC-Timestamp": timestamp,
        "X-TC-NONCE": nonce,
        "X-TC-RequestId": nonce,
        "X-TC-SecretId": config["secret_id"],
        "Authorization": authorization,
    }
    if version:
        headers["X-TC-Version"] = version
    return headers
