#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# retrieve_knowledge.py：召回知识库
# 调用 codebuddy server POST /knowledge/retrieve 接口
#
# 用法：
#   python3 retrieve_knowledge.py --query <query> --knowledge_uids <uid1> [uid2 ...] [--top_k 5] [--score_threshold 0.6]
#
# token 从 session.json 获取，优先读文件，再读环境变量 TESTBUDDY_TOKEN
# server 地址从环境变量 TESTBUDDY_SERVER 获取（默认 https://testbuddy.woa.com）

import argparse
import json
import os
import sys

if sys.version_info[0] < 3:
    print("错误：此脚本需要 Python 3，请使用 python3 运行", file=sys.stderr)
    sys.exit(1)

try:
    import ssl
    import urllib.error as urllib_error
    import urllib.request as urllib_request
except ImportError:
    print(json.dumps({"status": "error", "msg": "urllib 不可用，请使用 Python 3"}))
    sys.exit(1)

# 确保脚本所在目录在 sys.path 中，以便正确导入同目录模块
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# 导入 get_session 模块，复用 session 加载逻辑
from get_session import load_session  # noqa: E402

# 内网环境跳过 SSL 证书验证
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────
DEFAULT_SERVER = "http://testbuddy.woa.com"


def get_server():
    return os.environ.get("TESTBUDDY_SERVER", DEFAULT_SERVER).rstrip("/")


def _load_session_data():
    """通过 get_session.load_session 加载 session 数据，返回 session dict 或 None（加载失败）"""
    data = load_session()
    if isinstance(data, dict) and data.get("status") == "error":
        return None
    return data


def get_token():
    """通过 get_session 获取 token"""
    data = _load_session_data()
    if data:
        return data.get("token", "").strip()
    return ""


# ──────────────────────────────────────────────
# HTTP 工具
# ──────────────────────────────────────────────
def _get_testbuddy_origin():
    """根据 session 中的 env 字段返回 x-testbuddy-origin 值
    codebuddy -> cb-plugin，其他 -> openclaw
    """
    data = _load_session_data()
    if data:
        env = data.get("env", "other").strip()
        if env == "codebuddy":
            return "cb-plugin"
    return "openclaw"


def _post(path, token, body):
    """发送 POST 请求，返回解析后的 JSON 响应。校验状态码必须为200，否则返回错误。"""
    url = get_server() + path
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-testbuddy-origin": _get_testbuddy_origin(),
    }
    if token:
        headers["Authorization"] = "token {}".format(token)
    virtual_env = os.environ.get("TESTBUDDY_VIRTUAL_ENV")
    if virtual_env:
        headers["X-Virtual-Env"] = virtual_env
    req = urllib_request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=30, context=SSL_CONTEXT) as resp:
            status_code = resp.getcode()
            raw = resp.read().decode("utf-8")
            if status_code != 200:
                return {"error": "请求失败(HTTP {}): {}".format(status_code, raw[:500])}
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return {"error": "服务端返回了非预期格式: {}".format(raw[:500])}
            return parsed
    except urllib_error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        return {"error": "请求失败(HTTP {}): {}".format(e.code, raw[:500])}
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────
# 命令实现
# ──────────────────────────────────────────────
def cmd_retrieve_knowledge(args):
    token = get_token()
    if not token:
        return {
            "status": "error",
            "msg": "testbuddy skill缺少token无法执行，请先申请 testbuddy token，申请地址：https://testbuddy.woa.com/tencent/personal/account, 写入环境变量中，变量名：TESTBUDDY_TOKEN【export TESTBUDDY_TOKEN=****】",
        }

    if not args.query:
        return {"status": "error", "msg": "缺少 --query 参数"}
    if not args.knowledge_uids:
        return {"status": "error", "msg": "缺少 --knowledge_uids 参数"}

    body = {
        "query": args.query,
        "knowledge_uids": args.knowledge_uids,
        "top_k": args.top_k,
        "score_threshold": args.score_threshold,
    }

    resp = _post("/api/tb/v1/cb-plugin/knowledge/retrieve", token, body)

    if "error" in resp:
        return {"status": "error", "msg": resp["error"]}

    if not resp.get("success"):
        return {"status": "error", "msg": resp.get("error", str(resp))}

    return {
        "status": "success",
        "query": resp.get("query", args.query),
        "knowledge_uids": resp.get("knowledge_uids", args.knowledge_uids),
        "results_count": resp.get("results_count", 0),
        "results": resp.get("results", []),
    }


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────
USAGE = """
用法：python3 retrieve_knowledge.py [options]

选项：
  --query QUERY                   检索关键词（必填）
  --knowledge_uids UID [UID ...]   知识库 UID 列表（必填，可多个）
  --top_k N                       返回结果数量（默认 5）
  --score_threshold FLOAT         相似度阈值（默认 0.6）

示例：
  python3 retrieve_knowledge.py --query "登录功能" --knowledge_uids kb-abc123
  python3 retrieve_knowledge.py --query "支付流程" --knowledge_uids kb-abc123 kb-def456 --top_k 10
"""

if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--query", default=None)
    parser.add_argument("--knowledge_uids", nargs="+", default=None)
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--score_threshold", type=float, default=0.6)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(json.dumps({"status": "error", "msg": "参数解析失败，请检查参数格式"}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = cmd_retrieve_knowledge(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "success" else 1)
    except Exception as e:
        print(json.dumps({"status": "error", "msg": "脚本执行异常: {}".format(str(e))}, ensure_ascii=False, indent=2))
        sys.exit(1)
