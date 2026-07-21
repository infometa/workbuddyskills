#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# save_node.py：批量保存脑图节点（创建/更新/删除）
# 调用 codebuddy server POST /node/batch-save 接口
#
# 用法：
#   python3 save_node.py [--namespace <ns>] --design_uid <uid> --file <file_path>
#
# file_path 为 .testbuddy/assets/{design_uid}-update.json 格式的文件，
# 包含 added/updated/deleted 三个字段（由 write_nodes.py 生成）
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
from get_session import _find_workspace_root, load_session  # noqa: E402

# 内网环境跳过 SSL 证书验证
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────
DEFAULT_SERVER = "http://testbuddy.woa.com"
WORKSPACE_ROOT = _find_workspace_root()
TESTBUDDY_DIR = os.path.join(WORKSPACE_ROOT, ".testbuddy", "assets")


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
        with urllib_request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
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
def cmd_save_node(args):
    token = get_token()
    if not token:
        return {
            "status": "error",
            "msg": "testbuddy skill缺少token无法执行，请先申请 testbuddy token，申请地址：https://testbuddy.woa.com/tencent/personal/account, 写入环境变量中，变量名：TESTBUDDY_TOKEN【export TESTBUDDY_TOKEN=****】",
        }

    # namespace 可选，为空时由服务端通过 token 自动获取用户名作为默认值
    namespace = args.namespace or ""

    # design_uid 可选，为空时由服务端自动创建
    design_uid = args.design_uid or ""

    # 确定文件路径：优先使用 --file 参数，否则使用默认路径
    if args.file:
        file_path = args.file
    else:
        filename = "{}-update.json".format(design_uid) if design_uid else "pending-update.json"
        file_path = os.path.join(TESTBUDDY_DIR, filename)

    if not os.path.exists(file_path):
        return {"status": "error", "msg": "文件不存在: {}, 请使用write_node工具进行文件创建".format(file_path)}

    # 读取 update 文件
    with open(file_path, "r", encoding="utf-8") as f:
        update_data = json.load(f)

    added = update_data.get("added", [])
    updated = update_data.get("updated", [])
    deleted = update_data.get("deleted", [])

    if not added and not updated and not deleted:
        return {"status": "error", "msg": "文件中没有任何待操作的节点（added/updated/deleted 均为空）"}

    # 通过 get_session 读取 env 字段，用于服务端判断节点来源（Source）
    session_data = _load_session_data()
    env = session_data.get("env", "other").strip() if session_data else "other"

    body = {
        "namespace": namespace,
        "env": env,
    }
    if design_uid:
        body["design_uid"] = design_uid
    if added:
        body["added"] = added
    if updated:
        body["updated"] = updated
    if deleted:
        body["deleted"] = deleted

    resp = _post("/api/tb/v1/cb-plugin/node/batch-save", token, body)

    if "error" in resp:
        return {"status": "error", "msg": resp["error"]}

    if not resp.get("success"):
        return {"status": "error", "msg": resp.get("error", str(resp))}

    # 保存成功后清空 update 文件
    if args.clear_after_save:
        empty = {"added": [], "updated": [], "deleted": []}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)

    # 从响应中获取最终的 design_uid 和 namespace（可能由服务端自动创建/解析）
    final_design_uid = resp.get("design_uid", design_uid)
    final_namespace = resp.get("namespace", namespace)

    # 拼接测试设计链接（域名根据环境变量 TESTBUDDY_SERVER 判断）
    design_url = ""
    if final_design_uid and final_namespace:
        design_url = "{}/tencent/tb/workbench#/testx/{}/design/{}".format(
            get_server(), final_namespace, final_design_uid
        )

    result = {
        "status": "success",
        "design_uid": final_design_uid,
        "namespace": final_namespace,
        "data": resp.get("data"),
        "stats": {
            "added": len(added),
            "updated": len(updated),
            "deleted": len(deleted),
        },
    }
    if design_url:
        result["url"] = design_url

    return result


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────
USAGE = """
用法：python3 save_node.py [options]

选项：
  --namespace NAMESPACE         命名空间（可选，不传则由服务端通过 token 自动获取）
  --design_uid DESIGN_UID       设计文件 UID（可选，不传则由服务端自动创建）
  --file FILE_PATH              update 文件路径（可选，默认 .testbuddy/assets/{design_uid}-update.json）
  --clear_after_save            保存成功后清空 update 文件（可选）

说明：
  update 文件格式（由 write_nodes.py 生成）：
  {
    "added":   [ { "uid": "...", "name": "...", "kind": "...", "parent_uid": "..." }, ... ],
    "updated": [ { "uid": "...", "name": "...", "kind": "...", "parent_uid": "..." }, ... ],
    "deleted": [ "uid1", "uid2", ... ]
  }

示例：
  python3 save_node.py --namespace my_ns --design_uid design-Az7SsiL3Ui
  python3 save_node.py --design_uid design-Az7SsiL3Ui --file /tmp/update.json --clear_after_save
"""

if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--namespace", default=None)
    parser.add_argument("--design_uid", default=None)
    parser.add_argument("--file", default=None)
    parser.add_argument("--clear_after_save", action="store_true", default=False)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(json.dumps({"status": "error", "msg": "参数解析失败，请检查参数格式"}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = cmd_save_node(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "success" else 1)
    except Exception as e:
        print(json.dumps({"status": "error", "msg": "脚本执行异常: {}".format(str(e))}, ensure_ascii=False, indent=2))
        sys.exit(1)
