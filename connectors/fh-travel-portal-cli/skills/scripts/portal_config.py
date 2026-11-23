"""从 skill 根目录 config.json 读取服务端地址与本机工作区。

发布换环境时改：config.json 的 baseUrl、credentialsFile、cli.json 的 authUrlDomain、workbuddy.json。
工作区取 config.json 的 `workspaceRoot`；未配置时用 ~/.fh-travel-workspace：
  fh-travel-runs  查询产物
业务调用经 fh CLI（scripts/mcp_proxy.py 兼容层）；本模块只负责地址与工作区解析。
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse


def _skill_dir() -> Path:
    # 本文件在 scripts/，上一级就是 skill 根；不依赖启动时的当前工作目录。
    return Path(__file__).resolve().parent.parent


def _read_config_json() -> dict[str, Any]:
    path = _skill_dir() / "config.json"
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RuntimeError(f"config.json 格式错误: {path}")
    return data


def _join_forward(mcp_base: str) -> str:
    return mcp_base.rstrip("/") + "/oauth2/forward"


@lru_cache(maxsize=1)
def portal() -> dict[str, str]:
    """返回 scheme/host/mcpPath/mcpBase/forwardPath/forwardBase。"""
    cfg = _read_config_json()
    base = (os.environ.get("FH_TRAVEL_MCP_URL") or "").strip() or str(cfg.get("baseUrl") or "").strip()
    if not base:
        raise RuntimeError(
            f"未配置服务端地址：请在 {_skill_dir() / 'config.json'} 设置 baseUrl，"
            "或设置环境变量 FH_TRAVEL_MCP_URL。"
        )

    parsed = urlparse(base)
    scheme = (os.environ.get("FH_PORTAL_SCHEME") or "").strip() or (parsed.scheme or "https")
    host = (os.environ.get("FH_PORTAL_HOST") or "").strip() or (parsed.netloc or "")
    mcp_path = (os.environ.get("FH_MCP_PATH") or "").strip() or (parsed.path or "/api/portal/mcp")
    if not mcp_path.startswith("/"):
        mcp_path = "/" + mcp_path

    mcp_base = urlunparse((scheme, host, mcp_path, "", "", "")).rstrip("/")
    env_forward = (os.environ.get("FH_FORWARD_PATH") or "").strip()
    if env_forward:
        if not env_forward.startswith("/"):
            env_forward = "/" + env_forward
        forward_path = env_forward
        forward_base = urlunparse((scheme, host, forward_path, "", "", "")).rstrip("/")
    else:
        forward_base = _join_forward(mcp_base)
        forward_path = urlparse(forward_base).path or (mcp_path.rstrip("/") + "/forward")

    if not host:
        raise RuntimeError(f"服务端地址无法解析 host：{base!r}（文件: {_skill_dir() / 'config.json'}）")

    return {
        "scheme": scheme,
        "host": host,
        "mcpPath": mcp_path,
        "mcpBase": mcp_base,
        "forwardPath": forward_path,
        "forwardBase": forward_base,
    }


def mcp_base() -> str:
    return portal()["mcpBase"]


def domestic_rule_url() -> str:
    """页内退改补查：GET .../busi/air/domestic/rule，请求头 X-Auth-Code = infoCode。"""
    return mcp_base().rstrip("/") + "/busi/air/domestic/rule"


def intl_shop_url() -> str:
    """页内查舱位：GET .../busi/air/intl/intlShop，请求头 X-Auth-Code = infoCode。"""
    return mcp_base().rstrip("/") + "/busi/air/intl/intlShop"


def fh_base_url() -> str:
    """fh --base-url 用的 portal 基址（config.json baseUrl 去掉末尾 /mcp）。"""
    mcp = mcp_base()
    return mcp[: -len("/mcp")] if mcp.endswith("/mcp") else mcp


_CRED_FILE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
DEFAULT_CREDENTIALS_FILE = "credentials"


def credentials_file() -> str:
    """fh --credentials-file 用的文件名（只允许 basename，落在 ~/.fh/）。"""
    raw = str(_read_config_json().get("credentialsFile") or DEFAULT_CREDENTIALS_FILE).strip()
    if not _CRED_FILE_RE.fullmatch(raw):
        raise RuntimeError(
            f"config.json credentialsFile 只能是文件名（字母数字 . _ -），收到: {raw!r}"
        )
    return raw


def portal_host() -> str:
    return portal()["host"]


def forward_path() -> str:
    return portal()["forwardPath"]


def forward_base() -> str:
    return portal()["forwardBase"]


def clear_cache() -> None:
    portal.cache_clear()


DEFAULT_WORKSPACE = "~/.fh-travel-workspace"
_RUN_ID_RE = re.compile(r"^[0-9]{14}-[0-9a-fA-F-]+$")


def workspace_root() -> Path:
    raw = str(_read_config_json().get("workspaceRoot") or DEFAULT_WORKSPACE).strip()
    if not raw:
        raw = DEFAULT_WORKSPACE
    return Path(raw).expanduser().resolve()


def runs_root() -> Path:
    """查询产物根：workspaceRoot/fh-travel-runs。"""
    return workspace_root() / "fh-travel-runs"


def last_task_id_path() -> Path:
    return workspace_root() / "fh-last-task-id.txt"


def new_run_id() -> str:
    return f"{_dt.datetime.now():%Y%m%d%H%M%S}-{uuid.uuid4().hex[:8]}"


def write_last_task_id(run_id: str) -> Path:
    path = last_task_id_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(run_id.strip().lower() + "\n", encoding="utf-8")
    return path


def normalize_run_id(run_id: str) -> str:
    rid = (run_id or "").strip().lower()
    if not _RUN_ID_RE.fullmatch(rid):
        raise SystemExit(
            "[失败] --run-id 必须是 <YYYYMMDDHHMMSS>-<id>，例如 20260915165300-a1b2c3d4"
        )
    return rid


def adopt_run_id(run_id: str = "") -> str:
    """有传入则校验并登记；否则新发一个。stdout 打一行，同时写 fh-last-task-id.txt。"""
    rid = normalize_run_id(run_id) if (run_id or "").strip() else new_run_id()
    write_last_task_id(rid)
    print(rid, flush=True)
    return rid


def task_dir(run_id: str) -> Path:
    """读 config.json，拼出 <workspaceRoot>/fh-travel-runs/<run-id> 并建好目录。"""
    path = runs_root() / normalize_run_id(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def task_summary_path(run_id: str) -> Path:
    """传入 run_id，拼出该轮 run_summary.json 路径。不写文件。"""
    return task_dir(run_id) / "run_summary.json"


def task_log(run_id: str, msg: str, *, to_stderr: bool = False) -> None:
    """print 一行。摘要是一条龙成功后自己写的 run_summary.json，不往这里堆日志。"""
    print(str(msg).rstrip("\n"), file=sys.stderr if to_stderr else sys.stdout, flush=True)


def main() -> int:
    adopt_run_id()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
