"""Minimal Redis reader shipped with the WorkBuddy renderer.

The MCP tool writes through ``tools.utils.redis_utils``.  WorkBuddy's local
Python does not necessarily install redis-py, so this reader also supports the
small RESP subset required for a bounded GET.
"""

from __future__ import annotations

import json
import socket
from typing import Any


REDIS_HOST_PROD = "10.221.0.35"
REDIS_PORT_PROD = 6379
REDIS_HOST_FAT = "10.200.5.212"
REDIS_PORT_FAT = 6379
REDIS_TIMEOUT_SECONDS = 2
MAX_REDIS_VALUE_BYTES = 512 * 1024


def _target(env: str) -> tuple[str, int]:
    if env == "prod":
        return REDIS_HOST_PROD, REDIS_PORT_PROD
    return REDIS_HOST_FAT, REDIS_PORT_FAT


def _resp_get(host: str, port: int, cache_key: str) -> str | None:
    key = cache_key.encode("utf-8")
    request = b"*2\r\n$3\r\nGET\r\n$" + str(len(key)).encode("ascii") + b"\r\n" + key + b"\r\n"
    with socket.create_connection((host, port), timeout=REDIS_TIMEOUT_SECONDS) as connection:
        connection.settimeout(REDIS_TIMEOUT_SECONDS)
        connection.sendall(request)
        with connection.makefile("rb") as stream:
            header = stream.readline(128)
            if header == b"$-1\r\n":
                return None
            if not header.startswith(b"$") or not header.endswith(b"\r\n"):
                raise ValueError("Redis 返回类型异常")
            length = int(header[1:-2])
            if length < 0:
                return None
            if length > MAX_REDIS_VALUE_BYTES:
                raise ValueError("Redis 行程预览超过 512 KiB 限制")
            raw = stream.read(length)
            trailer = stream.read(2)
            if len(raw) != length or trailer != b"\r\n":
                raise ValueError("Redis 行程预览读取不完整")
            return raw.decode("utf-8")


def get_req_data_from_redis_dict(env: str, cache_key: str) -> dict[str, Any] | None:
    try:
        host, port = _target(env)
        raw = _resp_get(host, port, cache_key)
        if raw is None:
            return None
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except Exception:
        return None
