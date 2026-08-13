#!/usr/bin/env python3
"""统一建立并封装 Seeyon OA 认证上下文。by AI.Coding"""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit

import requests
from Crypto.Cipher import AES

from auth import AuthManager

REQUIRED_ENV_VARS = ("OA_BASE_URL", "OA_AUTH_USERNAME", "OA_AUTH_PASSWORD")


class SessionContextError(RuntimeError):
    """认证上下文无法安全建立时抛出。by AI.Coding"""


def derive_service_base_url(value: str) -> str:
    """从登录地址或业务地址推导不带尾斜杠的服务根地址。"""
    raw_value = (value or "").strip()
    parsed = urlsplit(raw_value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise SessionContextError("OA 服务地址必须是完整的 HTTP 或 HTTPS 地址")

    path = parsed.path.rstrip("/")
    segments = [segment for segment in path.split("/") if segment]
    if "seeyon" in segments:
        # 业务接口固定挂载在 seeyon 上下文，忽略登录页面和查询参数。
        index = segments.index("seeyon")
        service_path = "/" + "/".join(segments[: index + 1])
    elif path.lower().endswith(".do"):
        service_path = path.rsplit("/", 1)[0]
    else:
        service_path = path

    return urlunsplit((parsed.scheme, parsed.netloc, service_path, "", "")).rstrip("/")


def extract_cookie_value(session: Any, name: str) -> Optional[str]:
    """从 Session CookieJar 中安全提取指定 Cookie 的最后一个非空值。"""
    cookies = getattr(session, "cookies", None)
    if cookies is None:
        return None

    values: list[str] = []
    try:
        # CookieJar 可能包含同名不同域 Cookie，迭代可避免 get() 冲突。
        for cookie in cookies:
            if getattr(cookie, "name", None) == name:
                value = str(getattr(cookie, "value", "") or "").strip()
                if value:
                    values.append(value)
    except TypeError:
        value = cookies.get(name)
        if value:
            values.append(str(value).strip())

    if not values and hasattr(cookies, "get"):
        try:
            value = cookies.get(name)
        except Exception:  # pragma: no cover - 兼容第三方 CookieJar 的同名冲突行为
            value = None
        if value:
            values.append(str(value).strip())
    return values[-1] if values else None


def load_connector_session() -> Mapping[str, Any]:
    """直接解密读取本地浏览器会话，避免通过标准输出传递 Cookie。"""
    state_dir = Path.home() / ".workbuddy" / "seeyon-connector"
    key_path = state_dir / "session.key"
    session_path = state_dir / "session.enc.json"
    try:
        key = key_path.read_bytes()
        encrypted = json.loads(session_path.read_text(encoding="utf-8"))
        cipher = AES.new(key, AES.MODE_GCM, nonce=base64.b64decode(encrypted["iv"]))
        plaintext = cipher.decrypt_and_verify(
            base64.b64decode(encrypted["ciphertext"]),
            base64.b64decode(encrypted["tag"]),
        )
        payload = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        # 不传播底层异常文本，避免意外泄漏 Cookie 或本机路径。
        raise SessionContextError(f"OA 浏览器会话不可用：{type(exc).__name__}") from exc
    if not isinstance(payload, Mapping):
        raise SessionContextError("OA 浏览器会话格式无效")
    if time.time() * 1000 - float(payload.get("savedAt", 0)) > 12 * 60 * 60 * 1000:
        raise SessionContextError("OA 浏览器会话已过期，请重新连接")
    return payload


def build_session_from_connector(payload: Mapping[str, Any]) -> tuple[Any, str, str, Optional[str], str]:
    """将连接器会话装入 requests.Session 并返回内部认证字段。"""
    service_base_url = derive_service_base_url(str(payload.get("serviceUrl", "")))
    session_id = str(payload.get("JSESSIONID", "") or "").strip()
    username = str(payload.get("username", "") or "").strip()
    route = str(payload.get("route", "") or "").strip() or None
    if not session_id or not username:
        raise SessionContextError("OA 浏览器会话缺少必要认证信息")

    session = requests.Session()
    hostname = urlsplit(service_base_url).hostname
    session.cookies.set("JSESSIONID", session_id, domain=hostname, path="/")
    if route:
        session.cookies.set("route", route, domain=hostname, path="/")
    return session, service_base_url, session_id, route, username


@dataclass(frozen=True)
class SessionContext:
    """保存单次命令共享的认证会话和内部业务上下文。by AI.Coding"""

    session: Any
    service_base_url: str
    session_id: str
    route: Optional[str]
    username: str

    @classmethod
    def from_env(
        cls,
        base_url_override: Optional[str] = None,
        environ: Optional[Mapping[str, str]] = None,
        auth_manager_factory: Callable[[Mapping[str, str]], Any] = AuthManager.from_env,
        connector_session_loader: Callable[[], Mapping[str, Any]] = load_connector_session,
    ) -> "SessionContext":
        """优先账号密码登录，缺少账号或密码时复用连接器浏览器会话。"""
        source = os.environ if environ is None else environ
        has_credentials = all(str(source.get(name, "")).strip() for name in REQUIRED_ENV_VARS)

        if has_credentials:
            try:
                manager = auth_manager_factory(source)
                session = manager.get_session()
            except Exception as exc:
                # 认证异常只保留类型，避免第三方错误文本携带凭据或 Cookie。
                raise SessionContextError(f"OA 认证失败：{type(exc).__name__}") from exc

            session_id = extract_cookie_value(session, "JSESSIONID")
            if not session_id:
                raise SessionContextError("OA 认证会话缺少 JSESSIONID")
            address_source = base_url_override or str(source["OA_BASE_URL"])
            return cls(
                session=session,
                service_base_url=derive_service_base_url(address_source),
                session_id=session_id,
                route=extract_cookie_value(session, "route"),
                username=str(source["OA_AUTH_USERNAME"]).strip(),
            )

        try:
            session, stored_url, session_id, route, username = build_session_from_connector(
                connector_session_loader()
            )
        except SessionContextError:
            raise
        except Exception as exc:
            raise SessionContextError(f"OA 浏览器会话加载失败：{type(exc).__name__}") from exc

        service_base_url = derive_service_base_url(base_url_override) if base_url_override else stored_url
        return cls(
            session=session,
            service_base_url=service_base_url,
            session_id=session_id,
            route=route,
            username=username,
        )
