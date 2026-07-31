"""Shared helpers for TideRider / Databrain query scripts.

- get_token / require_token: 读取 API token（环境变量 DATABRAIN_TOKEN）
- get_host:                  读取 API host（环境变量 DATABRAIN_HOST），三级优先级 CLI > env > 默认值
                             非受信任域名会回退到默认值并打印 stderr 警告
- get_display_host:          读取回答展示链接 host（可选 DATABRAIN_DISPLAY_HOST）
- check_http_auth:           统一处理 401/403 并给出友好提示
- _load_dotenv:              在 import 期自动加载 skill 根目录下的 .env
- _is_trusted_host:          域名白名单校验（databrain.intlgame.com / databrain.woa.com /
                             databrain.mcp.it.woa.com / databrain-*.intlgame.com）

Token 获取地址（DataBrain 用户中心 - 个人令牌中心）：
  内网: https://databrain.woa.com/v2/user-center/personal-tokens-center
  外网: https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center
选"授权访问应用-全部应用"，复制原始值（不含 Bearer 前缀）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

TOKEN_ENV = "DATABRAIN_TOKEN"
HOST_ENV = "DATABRAIN_HOST"
DISPLAY_HOST_ENV = "DATABRAIN_DISPLAY_HOST"

DEFAULT_HOST = "https://databrain-global.intlgame.com"
_TRUSTED_HOSTS = (
    "databrain.intlgame.com",
    "databrain.woa.com",
    "databrain.mcp.it.woa.com",
)
_TRUSTED_WILDCARD_SUFFIX = ".intlgame.com"
_TRUSTED_WILDCARD_PREFIX = "databrain-"

TOKEN_HELP = (
    "请设置 DataBrain Token（DATABRAIN_TOKEN，原始值，不含 Bearer 前缀）。\n"
    "请先设置系统环境变量：export DATABRAIN_TOKEN=<token>\n"
    "或在 skill 根目录创建 .env 文件，内容形如：DATABRAIN_TOKEN=<token>\n"
    "Token 获取地址（DataBrain 用户中心 - 个人令牌中心）：\n"
    "  内网: https://databrain.woa.com/v2/user-center/personal-tokens-center\n"
    "  外网: https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center\n"
    "（选\"授权访问应用-全部应用\"）"
)


# ---- .env auto-load ---------------------------------------------------------
def _load_dotenv() -> None:
    """加载 skill 根目录下的 .env（脚本上一级目录），仅在环境变量未设置时填充。

    与 databrain-game-content-trend-intel/scripts/report_log.py 行为一致：
    `os.environ.setdefault(k, v)`，已存在的环境变量优先于 .env。
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    os.environ.setdefault(k, v)
    except OSError:
        # .env 读取失败不应阻塞脚本本身
        pass


# import 期立刻加载，确保后续 get_token/get_host 拿得到值
_load_dotenv()


def _is_trusted_host(host: str) -> bool:
    """域名白名单校验。允许 databrain.intlgame.com / databrain.woa.com /
    databrain.mcp.it.woa.com，以及 databrain-*.intlgame.com 通配模式。"""
    from urllib.parse import urlparse

    hostname = (urlparse(host).hostname or "").lower()
    if not hostname:
        return False
    if hostname in _TRUSTED_HOSTS:
        return True
    if hostname.endswith(_TRUSTED_WILDCARD_SUFFIX):
        prefix = hostname[: -len(_TRUSTED_WILDCARD_SUFFIX)]
        return prefix.startswith(_TRUSTED_WILDCARD_PREFIX) and len(prefix) > len(_TRUSTED_WILDCARD_PREFIX)
    return False


def get_token(cli_token: str | None = None) -> str:
    """读取 API token，优先级: 命令行参数 > DATABRAIN_TOKEN。"""
    if cli_token:
        return cli_token.strip()
    return os.environ.get(TOKEN_ENV, "").strip()


def get_host(cli_host: str | None = None, default: str = DEFAULT_HOST) -> str:
    """读取 API host，优先级: 命令行参数 > 系统环境变量 DATABRAIN_HOST > 默认值。

    非受信任域名会回退到默认值并在 stderr 打印警告（与 query_trending.py 严格抛错相比，
    本 skill 选择软回退，因为 execute_sql / game_search 是高频 CLI，避免因 host 字符串
    误配（如带 trailing slash 的旧值）导致整路阻塞）。
    """
    raw = cli_host if cli_host else os.environ.get(HOST_ENV, "")
    target = (raw or default).strip().rstrip("/")
    if not target:
        return default
    if not _is_trusted_host(target):
        print(
            f"⚠ DATABRAIN_HOST '{target}' 不在受信任域名列表 {_TRUSTED_HOSTS}，"
            f"已回退到默认值 {default}",
            file=sys.stderr,
        )
        return default
    return target


def get_display_host(default: str = "") -> str:
    """读取回答中展示链接的 host，优先使用 DATABRAIN_DISPLAY_HOST。"""
    return os.environ.get(DISPLAY_HOST_ENV, default).strip()


def require_token(cli_token: str | None = None) -> str:
    """读取 token；为空则打印提示并退出。"""
    token = get_token(cli_token)
    if not token:
        print(f"\n❌ 未找到 API Token (环境变量 {TOKEN_ENV})。\n{TOKEN_HELP}\n", file=sys.stderr)
        sys.exit(1)
    return token


def check_http_auth(resp) -> None:
    """在 raise_for_status 之前拦截 401/403，给出友好提示。"""
    if resp.status_code == 401:
        print(f"\n❌ 认证失败 (HTTP 401): Token 无效或已过期。\n{TOKEN_HELP}\n", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 403:
        print(
            "\n❌ 无权限 (HTTP 403): 当前用户没有该数据的访问权限。\n"
            "请联系数据管理员申请对应 game_code / 数据表的权限。\n",
            file=sys.stderr,
        )
        sys.exit(1)
