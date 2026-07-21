#!/usr/bin/env python3
"""SCRM Skill 公共工具。"""
from __future__ import annotations

import json
import logging
import os
import platform
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

SKILL_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = SKILL_ROOT / "logs"
DOWNLOAD_DIR = SKILL_ROOT / "downloads"


class SCRMError(Exception):
    """SCRM Skill 基础异常。"""

    def __init__(self, message: str, *, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.details = details or {}


def force_utf8_output() -> None:
    """强制将 stdout/stderr 编码设置为 UTF-8，解决 Windows 下中文输出乱码问题。"""
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception as e:
        import warnings
        warnings.warn(f"设置 UTF-8 编码失败: {e}")


class ConfigError(SCRMError):
    """配置错误。"""


class ValidationError(SCRMError):
    """输入参数错误。"""


class ApiError(SCRMError):
    """开放平台接口错误。"""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[int] = None,
        status: Optional[int] = None,
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.response_body = response_body
        self.details = {
            key: value
            for key, value in {
                "code": code,
                "status": status,
                "response_body": response_body,
            }.items()
            if value is not None
        }


class UploadError(SCRMError):
    """图床上传错误。"""


class DownloadError(SCRMError):
    """文件下载错误。"""


def ensure_dir(path: Path) -> Path:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


_LOGGING_READY = False


def setup_logging() -> logging.Logger:
    """初始化日志记录器。"""
    global _LOGGING_READY
    ensure_dir(LOG_DIR)
    logger = logging.getLogger("scrm-skills")
    if _LOGGING_READY:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_DIR / "scrm.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    _LOGGING_READY = True
    return logger


LOGGER = setup_logging()


def get_platform() -> str:
    """返回当前平台名称。"""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    if system == "Windows":
        return "windows"
    return system.lower()


def output_json(payload: dict[str, Any], *, exit_code: int = 0) -> None:
    """输出 JSON 并按需要退出。"""
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


def output_success(action: str, data: Optional[dict[str, Any]] = None, message: str = "") -> None:
    """输出成功结果。"""
    payload = {
        "success": True,
        "action": action,
        "message": message,
        "data": data or {},
    }
    output_json(payload, exit_code=0)


def output_error(
    action: str,
    error: str,
    message: str,
    *,
    details: Optional[dict[str, Any]] = None,
    exit_code: int = 1,
) -> None:
    """输出失败结果。"""
    payload = {
        "success": False,
        "action": action,
        "error": error,
        "message": message,
    }
    if details:
        payload["details"] = details
    output_json(payload, exit_code=exit_code)


def parse_csv_list(raw: Optional[str], *, cast=str) -> list[Any]:
    """解析逗号分隔列表。"""
    if not raw:
        return []
    result = []
    for item in raw.split(","):
        value = item.strip()
        if not value:
            continue
        result.append(cast(value))
    return result


def first_non_empty(values: Iterable[Optional[str]]) -> Optional[str]:
    """返回首个非空字符串。"""
    for value in values:
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def is_truthy_env(name: str) -> bool:
    """解析布尔型环境变量。"""
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


# ISO 8601 时间格式正则，如 2026-04-13T07:09:32.000+00:00
_ISO8601_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(\.\d+)?([+-]\d{2}:\d{2}|Z)$"
)

_BEIJING_TZ = timezone(timedelta(hours=8))


def convert_iso8601_to_beijing(value: str) -> str:
    """将 ISO 8601 时间字符串转换为北京时间（+08:00）。

    Args:
        value: ISO 8601 格式的时间字符串，如 "2026-04-13T07:09:32.000+00:00"。

    Returns:
        北京时间字符串，如 "2026-04-13T15:09:32.000+08:00"。
        非 ISO 8601 格式的字符串原样返回。
    """
    match = _ISO8601_RE.match(value)
    if not match:
        return value

    date_part, time_part, micro_part, tz_part = match.groups()
    micro_part = micro_part or ""

    if tz_part == "Z":
        tz_offset = timezone.utc
    else:
        sign = 1 if tz_part[0] == "+" else -1
        hours, minutes = int(tz_part[1:3]), int(tz_part[4:6])
        tz_offset = timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

    dt = datetime(
        int(date_part[:4]), int(date_part[5:7]), int(date_part[8:10]),
        int(time_part[0:2]), int(time_part[3:5]), int(time_part[6:8]),
        tzinfo=tz_offset,
    )
    dt_beijing = dt.astimezone(_BEIJING_TZ)
    return dt_beijing.strftime(f"%Y-%m-%dT%H:%M:%S{micro_part}+08:00")


def normalize_datetimes(data: Any) -> Any:
    """递归遍历 dict/list，将所有 ISO 8601 时间字符串转换为北京时间。

    Args:
        data: 待处理的数据，可以是 dict、list 或其他类型。

    Returns:
        转换后的数据。
    """
    if isinstance(data, dict):
        return {k: normalize_datetimes(v) for k, v in data.items()}
    if isinstance(data, list):
        return [normalize_datetimes(item) for item in data]
    if isinstance(data, str) and _ISO8601_RE.match(data):
        return convert_iso8601_to_beijing(data)
    return data
