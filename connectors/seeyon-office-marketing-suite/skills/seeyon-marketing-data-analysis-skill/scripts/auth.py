#!/usr/bin/env python3
"""使用环境变量登录 Java Web OA 认证地址。by AI.Coding

必需的环境变量：
    OA_BASE_URL       完整登录地址。
    OA_AUTH_USERNAME  登录用户名。
    OA_AUTH_PASSWORD  登录密码。

可以导入本模块以复用已经认证的 ``requests.Session``，也可以直接运行本模块执行脱敏的登录检查。
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import ssl
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Callable, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter

try:
    from Crypto.Cipher import DES
except ImportError:  # pragma: no cover - 仅影响可选的致远加密登录流程
    DES = None

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = (
    "OA_BASE_URL",
    "OA_AUTH_USERNAME",
    "OA_AUTH_PASSWORD",
)
SUPPORTED_SCHEMES = frozenset({"http", "https"})


class AuthConfigurationError(ValueError):
    """必需的环境配置无效时抛出。"""


class AuthenticationError(RuntimeError):
    """无法建立认证会话时抛出。"""


class _LoginFormParser(HTMLParser):
    """提取致远登录表单，不保留任何运行时凭据。"""

    def __init__(self) -> None:
        """初始化登录表单解析状态。"""
        super().__init__()
        self.action = ""
        self.fields: list[dict[str, Any]] = []
        self._in_login_form = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, Optional[str]]],
    ) -> None:
        """记录登录表单及其输入字段。"""
        attributes = dict(attrs)
        if tag == "form" and not self._in_login_form:
            action = attributes.get("action") or ""
            form_id = attributes.get("id") or ""
            if form_id == "login_form" or "method=login" in action.lower():
                self._in_login_form = True
                self.action = action
            return

        if tag != "input" or not self._in_login_form:
            return

        self.fields.append(
            {
                "name": attributes.get("name") or "",
                "type": (attributes.get("type") or "text").lower(),
                "value": attributes.get("value") or "",
                "disabled": "disabled" in attributes,
                "checked": "checked" in attributes,
            }
        )

    def handle_endtag(self, tag: str) -> None:
        """在表单结束标签处退出解析状态。"""
        if tag == "form" and self._in_login_form:
            self._in_login_form = False


def _evp_bytes_to_key(
    passphrase: bytes,
    salt: bytes,
    key_length: int,
    iv_length: int,
) -> tuple[bytes, bytes]:
    """实现 CryptoJS/OpenSSL 默认 PasswordBasedCipher 的 MD5 KDF。"""
    derived = b""
    previous = b""
    while len(derived) < key_length + iv_length:
        previous = hashlib.md5(previous + passphrase + salt).digest()
        derived += previous
    return derived[:key_length], derived[key_length : key_length + iv_length]


def _cryptojs_des_encrypt(
    plaintext: str,
    passphrase: str,
    salt: Optional[bytes] = None,
) -> str:
    """生成与 ``CryptoJS.DES.encrypt(text, passphrase)`` 兼容的密文。"""
    if DES is None:
        raise RuntimeError("致远加密登录需要 pycryptodome。")

    actual_salt = os.urandom(8) if salt is None else salt
    if len(actual_salt) != 8:
        raise ValueError("DES salt 必须为 8 字节。")

    key, iv = _evp_bytes_to_key(
        passphrase.encode("utf-8"),
        actual_salt,
        DES.block_size,
        DES.block_size,
    )
    clear_bytes = plaintext.encode("utf-8")
    padding_length = DES.block_size - len(clear_bytes) % DES.block_size
    padded = clear_bytes + bytes([padding_length]) * padding_length
    encrypted = DES.new(key, DES.MODE_CBC, iv).encrypt(padded)
    return base64.b64encode(b"Salted__" + actual_salt + encrypted).decode("ascii")


class SystemTrustHTTPAdapter(HTTPAdapter):
    """在不关闭 TLS 校验的情况下使用操作系统信任库。"""

    def __init__(self, *args: Any, **kwargs: Any):
        """创建使用系统信任库的 TLS 适配器。"""
        self._ssl_context = ssl.create_default_context()
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        """为直连连接池注入系统 TLS 上下文。"""
        kwargs["ssl_context"] = self._ssl_context
        super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: Any) -> Any:
        """为代理连接池注入系统 TLS 上下文。"""
        proxy_kwargs["ssl_context"] = self._ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


@dataclass(frozen=True)
class AuthConfig:
    """从环境变量加载并校验的认证配置。"""

    login_url: str
    username: str
    password: str
    timeout: float = 30.0
    verify_ssl: bool = True
    allow_insecure_tls_fallback: bool = True

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "AuthConfig":
        """从环境变量读取并校验认证配置。"""
        source = os.environ if environ is None else environ
        missing = [name for name in REQUIRED_ENV_VARS if not source.get(name, "").strip()]
        if missing:
            raise AuthConfigurationError(
                "以下必需环境变量缺失或为空：" + ", ".join(missing)
            )

        login_url = source["OA_BASE_URL"].strip()
        parsed = urlsplit(login_url)
        if parsed.scheme.lower() not in SUPPORTED_SCHEMES or not parsed.netloc:
            raise AuthConfigurationError(
                "OA_BASE_URL 必须是完整的 HTTP 或 HTTPS 登录地址。"
            )

        return cls(
            login_url=login_url,
            username=source["OA_AUTH_USERNAME"].strip(),
            password=source["OA_AUTH_PASSWORD"],
        )


class AuthManager:
    """管理登录过程和 requests 认证会话的生命周期。"""

    def __init__(self, config: AuthConfig, session_max_age: float = 1800.0):
        """创建认证管理器并初始化可复用 Session。"""
        self.config = config
        self.session = requests.Session()
        self.session.verify = config.verify_ssl
        if urlsplit(config.login_url).scheme.lower() == "https":
            self.session.mount("https://", SystemTrustHTTPAdapter())
        self.tls_verification_skipped = False
        self._authenticated = False
        self._auth_time: Optional[float] = None
        self._session_max_age = session_max_age

    @classmethod
    def from_env(
        cls,
        environ: Optional[Mapping[str, str]] = None,
        session_max_age: float = 1800.0,
    ) -> "AuthManager":
        """从环境变量构造认证管理器。"""
        return cls(AuthConfig.from_env(environ), session_max_age=session_max_age)

    def login(self) -> bool:
        """尝试支持的 OA 登录格式，并在成功后保留 Cookie 或 Token。"""
        self._authenticated = False
        self._auth_time = None
        self.tls_verification_skipped = False
        self.session.cookies.clear()
        self.session.headers.pop("Authorization", None)

        if urlsplit(self.config.login_url).scheme.lower() == "https":
            self.session.verify = self.config.verify_ssl
            self.session.mount("https://", SystemTrustHTTPAdapter())

        protocol = urlsplit(self.config.login_url).scheme.lower()
        logger.info("正在通过 %s 协议登录 OA", protocol.upper())

        payloads: list[dict[str, Any]] = []
        try:
            seeyon_payload = self._prepare_seeyon_login_payload()
        except requests.exceptions.SSLError:
            logger.warning("OA 登录页预取失败：HTTPS 证书校验错误")
            seeyon_payload = None
        except requests.exceptions.Timeout:
            logger.warning("OA 登录页预取失败：请求超时")
            seeyon_payload = None
        except requests.exceptions.ConnectionError:
            logger.warning("OA 登录页预取失败：连接错误")
            seeyon_payload = None
        except requests.RequestException:
            logger.warning("OA 登录页预取失败：HTTP 请求错误")
            seeyon_payload = None

        if seeyon_payload is not None:
            payloads.append(seeyon_payload)
        payloads.extend(self._login_payloads())

        for attempt, payload in enumerate(payloads, start=1):
            try:
                response = self._post_login_request(payload)
            except requests.exceptions.SSLError:
                logger.warning(
                    "第 %s 次 OA 登录尝试失败：HTTPS 证书校验错误",
                    attempt,
                )
                continue
            except requests.exceptions.Timeout:
                logger.warning("第 %s 次 OA 登录尝试失败：请求超时", attempt)
                continue
            except requests.exceptions.ConnectionError:
                logger.warning("第 %s 次 OA 登录尝试失败：连接错误", attempt)
                continue
            except requests.RequestException:
                logger.warning("第 %s 次 OA 登录尝试失败：HTTP 请求错误", attempt)
                continue

            logger.debug(
                "第 %s 次 OA 登录尝试返回 status=%s，cookie_names=%s",
                attempt,
                response.status_code,
                sorted(self.session.cookies.keys()),
            )

            if self._is_login_successful(response):
                self._authenticated = True
                self._auth_time = time.time()
                logger.info("OA 登录成功，使用第 %s 种登录格式", attempt)
                return True

            authoritative_rejection = payload.get("authoritative") and (
                response.headers.get("LoginError", "").strip()
                or response.status_code in {401, 403}
            )
            if authoritative_rejection:
                logger.warning("OA 服务端拒绝致远动态加密登录请求")
                break

        logger.error("OA 登录失败，请检查登录地址和认证环境变量。")
        return False

    def _post_login_request(self, payload: dict[str, Any]) -> requests.Response:
        """发送一次登录请求，仅在 HTTPS 证书校验失败后执行兜底。"""
        request_url = payload.get("url") or self.config.login_url
        return self._request_with_tls_fallback(
            lambda: self._send_login_request(payload),
            request_url,
        )

    def _request_with_tls_fallback(
        self,
        request: Callable[[], requests.Response],
        url: str,
    ) -> requests.Response:
        """执行请求，并仅对 HTTPS 证书校验错误进行一次不安全兜底。"""
        try:
            return request()
        except requests.exceptions.SSLError:
            is_https = urlsplit(url).scheme.lower() == "https"
            can_fallback = (
                is_https
                and self.config.verify_ssl
                and self.config.allow_insecure_tls_fallback
                and not self.tls_verification_skipped
            )
            if not can_fallback:
                raise

            logger.warning(
                "HTTPS 证书校验失败，正在按配置关闭 TLS 证书校验并重试"
            )
            self.session.mount("https://", HTTPAdapter())
            self.session.verify = False
            self.tls_verification_skipped = True
            return request()

    def _send_login_request(self, payload: dict[str, Any]) -> requests.Response:
        """按候选载荷发送一次登录请求。"""
        headers = self._headers(payload["content_type"])
        headers.update(payload.get("headers") or {})
        return self.session.post(
            payload.get("url") or self.config.login_url,
            data=payload.get("data"),
            json=payload.get("json"),
            headers=headers,
            timeout=self.config.timeout,
            allow_redirects=False,
        )

    def _prepare_seeyon_login_payload(self) -> Optional[dict[str, Any]]:
        """识别致远登录页并构造与浏览器一致的动态 DES 加密表单。"""
        if not self._is_seeyon_login_url():
            return None
        if DES is None:
            logger.warning("未安装 pycryptodome，跳过致远动态加密登录流程")
            return None

        page_url = self._seeyon_login_page_url()
        response = self._request_with_tls_fallback(
            lambda: self.session.get(
                page_url,
                headers=self._headers("text/html"),
                timeout=self.config.timeout,
                allow_redirects=True,
            ),
            page_url,
        )
        if response.status_code >= 400:
            return None

        body = response.text
        seed_match = re.search(
            r"\bvar\s+_SecuritySeed\s*=\s*(['\"])([^'\"]+)\1",
            body,
        )
        uses_signature = bool(
            re.search(
                r"signature\s*\(\s*clearPwd\s*,\s*_SecuritySeed",
                body,
            )
        )
        if seed_match is None or not uses_signature:
            return None

        parser = _LoginFormParser()
        parser.feed(body)
        if not parser.action:
            return None

        form_data: dict[str, str] = {}
        for field in parser.fields:
            name = field["name"]
            field_type = field["type"]
            if not name or field["disabled"]:
                continue
            if field_type in {"button", "submit", "reset", "file"}:
                continue
            if field_type in {"checkbox", "radio"} and not field["checked"]:
                continue
            if name in {"login_password", "login_password1"}:
                continue
            form_data[name] = field["value"]

        encrypted_password = _cryptojs_des_encrypt(
            self.config.password,
            seed_match.group(2),
        )
        form_data.update(
            {
                "login_username": self.config.username,
                "login_password": encrypted_password,
                "login_validatePwdStrength": (
                    form_data.get("login_validatePwdStrength") or "1"
                ),
                "fontSize": "12",
                "screenWidth": "1920",
                "screenHeight": "1080",
            }
        )

        final_page_url = response.url or page_url
        parsed_page_url = urlsplit(final_page_url)
        return {
            "content_type": "application/x-www-form-urlencoded",
            "data": form_data,
            "json": None,
            "url": urljoin(final_page_url, parser.action),
            "headers": {
                "Referer": final_page_url,
                "Origin": urlunsplit(
                    (
                        parsed_page_url.scheme,
                        parsed_page_url.netloc,
                        "",
                        "",
                        "",
                    )
                ),
            },
            "authoritative": True,
        }

    def _is_seeyon_login_url(self) -> bool:
        """判断配置地址是否为致远 main.do 登录入口。"""
        parsed = urlsplit(self.config.login_url)
        query = {
            key.lower(): value.lower()
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        }
        return parsed.path.lower().endswith("/main.do") and query.get(
            "method"
        ) == "login"

    def _seeyon_login_page_url(self) -> str:
        """生成用于提取动态登录参数的页面地址。"""
        parsed = urlsplit(self.config.login_url)
        query = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if not (key.lower() == "method" and value.lower() == "login")
        ]
        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(query, doseq=True),
                "",
            )
        )

    def ensure_authenticated(self) -> bool:
        """确保会话有效，本地会话过期后重新登录。"""
        if self._is_session_expired():
            return self.login()
        return True

    def get_session(self) -> requests.Session:
        """返回认证会话；认证失败时抛出异常。"""
        if not self.ensure_authenticated():
            raise AuthenticationError("无法建立有效的 OA 认证会话。")
        return self.session

    def invalidate(self) -> None:
        """清除本地认证状态及已保留的认证信息。"""
        self._authenticated = False
        self._auth_time = None
        self.session.cookies.clear()
        self.session.headers.pop("Authorization", None)

    def _is_session_expired(self) -> bool:
        """判断本地认证状态是否缺失或超过有效期。"""
        if not self._authenticated or self._auth_time is None:
            return True
        return time.time() - self._auth_time > self._session_max_age

    def _login_payloads(self) -> list[dict[str, Any]]:
        """生成通用 OA 登录格式的候选载荷。"""
        username = self.config.username
        password = self.config.password
        return [
            {
                "content_type": "application/x-www-form-urlencoded",
                "data": {
                    "login.timezone": "",
                    "authorization": "",
                    "fontSize": "",
                    "screenWidth": "1920",
                    "screenHeight": "1080",
                    "login_username": username,
                    "login_validatePwdStrength": "1",
                    "loginName": username,
                    "login_password": password,
                    "useClearPassword": "1",
                },
                "json": None,
            },
            {
                "content_type": "application/json",
                "data": None,
                "json": {"username": username, "password": password},
            },
            {
                "content_type": "application/x-www-form-urlencoded",
                "data": {"username": username, "password": password},
                "json": None,
            },
            {
                "content_type": "application/json",
                "data": None,
                "json": {"loginName": username, "loginPassword": password},
            },
            {
                "content_type": "application/json",
                "data": None,
                "json": {"account": username, "password": password},
            },
        ]

    @staticmethod
    def _headers(content_type: str) -> dict[str, str]:
        """生成登录请求使用的浏览器兼容请求头。"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if content_type == "application/json":
            headers["Content-Type"] = content_type
        return headers

    def _is_login_successful(self, response: requests.Response) -> bool:
        """综合响应头、JSON、Cookie 和重定向判断登录结果。"""
        login_error = response.headers.get("LoginError", "").strip()
        if login_error:
            logger.warning("OA 服务端返回 LoginError")
            return False

        if response.headers.get("LoginOK", "").strip().lower() == "ok":
            self._retain_jsessionid(response)
            return True

        body = self._json_body(response)
        if body is not None and self._json_indicates_success(body):
            self._extract_token(body)
            return True

        cookie_names = " ".join(name.lower() for name in self.session.cookies.keys())
        has_auth_cookie = any(
            marker in cookie_names
            for marker in ("jsessionid", "sessionid", "session", "token", "auth")
        )
        if has_auth_cookie and response.status_code < 400 and not self._body_indicates_failure(response):
            return True

        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location", "").lower()
            return bool(location) and not any(
                marker in location for marker in ("login", "signin", "authenticate")
            )

        return False

    @staticmethod
    def _json_body(response: requests.Response) -> Optional[dict[str, Any]]:
        """在响应为 JSON 对象时返回解析结果。"""
        try:
            body = response.json()
        except ValueError:
            return None
        return body if isinstance(body, dict) else None

    @staticmethod
    def _json_indicates_success(body: dict[str, Any]) -> bool:
        """判断 JSON 对象是否包含可靠登录成功标志。"""
        code = body.get("code")
        status = body.get("status")
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        return any(
            (
                code in (0, 200, "0", "200", "success", "ok"),
                body.get("success") is True,
                status in (200, "200", "success", "ok"),
                any(key in body for key in ("token", "accessToken", "access_token")),
                any(key in data for key in ("token", "accessToken", "access_token")),
            )
        )

    @staticmethod
    def _body_indicates_failure(response: requests.Response) -> bool:
        """判断文本响应是否明确表示认证失败。"""
        content_type = response.headers.get("Content-Type", "").lower()
        if "text" not in content_type and "html" not in content_type and "json" not in content_type:
            return False
        text = response.text[:8192].lower()
        return any(
            marker in text
            for marker in (
                "loginerror",
                "invalid password",
                "invalid username",
                "authentication failed",
                "登录失败",
                "用户名或密码错误",
            )
        )

    def _retain_jsessionid(self, response: requests.Response) -> None:
        """在 CookieJar 缺失时从响应头保留 JSESSIONID。"""
        if self.session.cookies.get("JSESSIONID"):
            return
        match = re.search(r"(?:^|[,;]\s*)JSESSIONID=([^;,]+)", response.headers.get("Set-Cookie", ""))
        if match:
            self.session.cookies.set("JSESSIONID", match.group(1))

    def _extract_token(self, body: dict[str, Any]) -> None:
        """从成功 JSON 中提取 Token 并设置认证请求头。"""
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        token = (
            body.get("token")
            or body.get("accessToken")
            or body.get("access_token")
            or data.get("token")
            or data.get("accessToken")
            or data.get("access_token")
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"


def main() -> int:
    """执行脱敏登录检查并返回稳定退出码。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        manager = AuthManager.from_env()
    except AuthConfigurationError as exc:
        logger.error("%s", exc)
        return 2

    if not manager.login():
        return 1

    cookie_names = sorted(manager.session.cookies.keys())
    token_present = "Authorization" in manager.session.headers
    print(
        "OA 认证成功；"
        f"protocol={urlsplit(manager.config.login_url).scheme.lower()}; "
        f"tls_verification_skipped={manager.tls_verification_skipped}; "
        f"cookie_names={cookie_names}; authorization_header_present={token_present}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
