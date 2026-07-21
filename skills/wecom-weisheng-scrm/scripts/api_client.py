#!/usr/bin/env python3
"""SCRM 开放平台 API Client。"""
from __future__ import annotations

import json
import os
import ssl
from typing import Any, Optional
from urllib import error, parse, request

from utils import ApiError, ConfigError

DEFAULT_BASE_URL = "https://open.wshoto.com"

def _get_ssl_context() -> ssl.SSLContext:
    """获取 SSL 上下文，支持通过环境变量跳过验证。"""
    if os.getenv("SCRM_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_personal_access_token(app_key: str, *, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """通过 personal app_key 获取 Access Token 及当前用户身份。"""
    query = parse.urlencode({"app_key": app_key})
    url = f"{base_url.rstrip('/')}/openapi/personal_access_token?{query}"
    ssl_context = _get_ssl_context()

    try:
        with request.urlopen(url, timeout=30, context=ssl_context) as response:
            status = response.status
            raw_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            raise ApiError(f"接口请求失败，HTTP {exc.code}", status=exc.code, response_body=raw_body) from exc
        raise ApiError(
            payload.get("msg") or f"接口请求失败，HTTP {exc.code}",
            code=payload.get("code"),
            status=exc.code,
            response_body=payload,
        ) from exc
    except error.URLError as exc:
        raise ApiError(f"接口请求失败：{exc.reason}") from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ApiError("接口返回了非 JSON 内容", status=status, response_body=raw_body) from exc

    if payload.get("code") != 0:
        raise ApiError(
            payload.get("msg") or "接口返回失败",
            code=payload.get("code"),
            status=status,
            response_body=payload,
        )
    return payload.get("data", {})


class SCRMClient:
    """封装开放平台接口调用。"""

    def __init__(self, access_token: str, *, base_url: str = DEFAULT_BASE_URL, timeout: int = 30, user_id: Optional[str] = None) -> None:
        if not access_token.strip():
            raise ConfigError("缺少 Access Token，请检查 APP_KEY 配置")
        self.access_token = access_token.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_id = user_id

    def build_url(self, path: str) -> str:
        """拼接完整请求地址并追加 access_token。"""
        clean_path = path if path.startswith("/") else f"/{path}"
        query = parse.urlencode({"access_token": self.access_token})
        return f"{self.base_url}{clean_path}?{query}"

    def get_json(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """发送 GET 请求，params 中的参数会追加到查询字符串。"""
        url = self.build_url(path)
        if params:
            extra = parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}&{extra}"
        req = request.Request(url, method="GET")
        return self._execute(req)

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """发送 JSON POST 请求。"""
        url = self.build_url(path)
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        return self._execute(req)

    def post_multipart(self, path: str, body: bytes, *, content_type: str) -> dict[str, Any]:
        """发送 multipart/form-data POST 请求。"""
        url = self.build_url(path)
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )
        return self._execute(req)

    def _execute(self, req: request.Request) -> dict[str, Any]:
        ssl_context = _get_ssl_context()
        try:
            with request.urlopen(req, timeout=self.timeout, context=ssl_context) as response:
                status = response.status
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            raise self._build_http_error(exc.code, raw_body) from exc
        except error.URLError as exc:
            raise ApiError(f"接口请求失败：{exc.reason}") from exc

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ApiError("接口返回了非 JSON 内容", status=status, response_body=raw_body) from exc

        if payload.get("code") != 0:
            raise ApiError(
                payload.get("msg") or "接口返回失败",
                code=payload.get("code"),
                status=status,
                response_body=payload,
            )
        return payload

    def _build_http_error(self, status: int, raw_body: str) -> ApiError:
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return ApiError(
                f"接口请求失败，HTTP {status}",
                status=status,
                response_body=raw_body,
            )

        return ApiError(
            payload.get("msg") or f"接口请求失败，HTTP {status}",
            code=payload.get("code"),
            status=status,
            response_body=payload,
        )
