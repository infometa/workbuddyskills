#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
from typing import TypedDict

# 强制使用 Python 3
if sys.version_info[0] < 3:
    print("错误：此脚本需要 Python 3，请使用 python3 运行", file=sys.stderr)
    sys.exit(1)

DEFAULT_SERVER = "http://testbuddy.woa.com"


def _find_workspace_root() -> str:
    """查找工作区根目录。
    优先使用 os.getcwd()，如果当前目录下没有 .testbuddy 目录，
    则从当前目录向上逐级查找包含 .testbuddy 目录的祖先目录。
    如果都找不到，回退到 os.getcwd()。
    """
    cwd = os.getcwd()
    # 快速路径：当前目录就有 .testbuddy
    if os.path.isdir(os.path.join(cwd, ".testbuddy")):
        return cwd
    # 向上查找
    current = cwd
    while True:
        parent = os.path.dirname(current)
        if parent == current:
            # 已到根目录，回退到 cwd
            return cwd
        if os.path.isdir(os.path.join(parent, ".testbuddy")):
            return parent
        current = parent


# 动态查找工作区根目录，避免因 cd 到错误目录导致找不到 session.json
_WORKSPACE_ROOT = _find_workspace_root()
SESSION_FILE = os.path.join(_WORKSPACE_ROOT, ".testbuddy/env/session.json")


class Session(TypedDict):
    mode: str
    env: str
    session_id: str
    namespace: str
    design_uid: str
    select_node: dict
    story_node: dict
    story_info: dict
    knowledge_uids: list[str]
    domain: str
    token: str


def detect_env() -> str:
    if os.environ.get("CODEBUDDY_COPILOT_INTERNET_ENVIRONMENT"):
        return "codebuddy"
    return "other"


def load_session():
    """加载会话变量"""
    if not os.path.exists(SESSION_FILE):
        # 先尝试从环境变量中加载TESTBUDDY_TOKEN
        token = os.environ.get("TESTBUDDY_TOKEN", "").strip()
        if not token:
            # 如果不存在，提醒用户先申请token
            return {
                "status": "error",
                "msg": "testbuddy skill缺少token无法执行，请先申请 testbuddy token，申请地址：https://testbuddy.woa.com/tencent/personal/account, 写入环境变量中，变量名：TESTBUDDY_TOKEN【export TESTBUDDY_TOKEN=****】",
            }
        env = detect_env()
        mode = "chat"
        session = Session(mode=mode, env=env, token=token)
        save_session(session)
        return session

    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        # 检测token是否存在，如果不存在，提醒用户先申请token
        token = data.get("token", "").strip()
        if not token:
            token = os.environ.get("TESTBUDDY_TOKEN", "").strip()
            if not token:
                # 如果不存在，提醒用户先申请token
                return {
                    "status": "error",
                    "msg": "testbuddy skill缺少token无法执行，请先申请 testbuddy token，申请地址：https://testbuddy.woa.com/tencent/personal/account, 写入环境变量中，变量名：TESTBUDDY_TOKEN【export TESTBUDDY_TOKEN=****】",
                }
            data["token"] = token
            save_session(data)
        # 兜底补全：如果 session.json 中缺少 env 或 mode 字段（可能由外部写入），自动补全
        need_save = False
        if not data.get("env"):
            data["env"] = detect_env()
            need_save = True
        if not data.get("mode"):
            data["mode"] = "chat"
            need_save = True
        if need_save:
            save_session(data)
        # 如果存在文件，可能有几种情况：
        # 1.存在session id，判断session_id是否存活，如果不存活则转化为会话模式,否则保持脑图模式
        # 2.不存在session id, 是会话模式，检查数据后 直接返回
        session_id = data.get("session_id", "").strip()
        token = data.get("token", "")
        if session_id:
            # 情况1：存在 session_id，检查是否存活
            alive = _check_session_alive(session_id, token)
            if alive:
                return data
            else:
                # session 已失效，转为会话模式
                env = data.get("env", "other")
                mode = "chat"
                session = Session(mode=mode, env=env, token=data["token"])
                save_session(session)
                return session
        return data


def _get_testbuddy_origin() -> str:
    """根据 session.json 中的 env 字段返回 x-testbuddy-origin 值
    codebuddy -> cb-plugin，其他 -> openclaw
    """
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        env = data.get("env", "other").strip()
        if env == "codebuddy":
            return "cb-plugin"
    return "openclaw"


def _check_session_alive(session_id: str, token: str = None) -> bool:
    """通过 codebuddy server /session/check 接口检查 session_id 是否存活"""
    import ssl
    import urllib.request as urllib_request

    server = os.environ.get("TESTBUDDY_SERVER", DEFAULT_SERVER).rstrip("/")
    url = server + "/api/tb/v1/cb-plugin/session/check"
    body = json.dumps({"session_id": session_id}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-testbuddy-origin": _get_testbuddy_origin(),
    }
    # 添加 token 认证信息
    if token:
        headers["Authorization"] = f"token {token}"
    virtual_env = os.environ.get("TESTBUDDY_VIRTUAL_ENV")
    if virtual_env:
        headers["X-Virtual-Env"] = virtual_env

    # 内网环境跳过 SSL 证书验证
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    req = urllib_request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=5, context=ssl_ctx) as resp:
            status_code = resp.getcode()
            raw = resp.read().decode("utf-8")
            if status_code != 200:
                return False
            result = json.loads(raw)
            return result.get("alive", False)
    except Exception:
        # 无法连接 testbuddy server，保守认为 session 已失效
        return False


def save_session(data):
    """回写数据到 session.json"""
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_session(existing, new_data):
    """
    合并新数据到现有 session：
    - dict 类型字段：key 级别合并（有则更新，无则添加）
    - 其他类型字段：直接覆盖更新
    """
    for key, value in new_data.items():
        if isinstance(value, dict):
            # dict 字段做 key 级别合并
            if key not in existing or not isinstance(existing[key], dict):
                existing[key] = {}
            existing[key].update(value)
        else:
            existing[key] = value
    return existing


if __name__ == "__main__":
    # 支持两种用法：
    # 1. python3 get_session.py          → 读取并输出 session
    # 2. python3 get_session.py --write   → 从 stdin 读取 JSON 并回写到 session.json
    if len(sys.argv) > 1 and sys.argv[1] == "--write":
        try:
            input_data = json.loads(sys.stdin.read())
            # 加载现有数据并合并
            existing = load_session()
            merged = merge_session(existing, input_data)
            save_session(merged)
            print(json.dumps(merged, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"status": "error", "msg": str(e)}, ensure_ascii=False))
            sys.exit(1)
    else:
        data = load_session()
        print(json.dumps(data, ensure_ascii=False, indent=2))
