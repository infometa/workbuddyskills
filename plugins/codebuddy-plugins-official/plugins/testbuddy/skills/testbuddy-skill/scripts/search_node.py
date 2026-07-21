#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# search_node.py：查询脑图节点详细信息
# 支持按 UID 列表查询指定节点，或不传 uids 查询整个 design 下所有节点
# 优先从本地 .testbuddy/assets/{design_uid}.json 查询，本地文件不存在时调用远程接口
# 远程接口：POST /api/tb/v1/cb-plugin/node/search
#
# 用法：
#   python3 search_node.py --design_uid <uid> [--namespace <ns>] [--uids <uid1> [uid2 ...]] [--ancestor] [--no-descendant] [--kind CASE]
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


def get_mode():
    """通过 get_session 获取 mode（mindmap / chat）"""
    data = _load_session_data()
    if data:
        return data.get("mode", "").strip()
    return ""


# ──────────────────────────────────────────────
# 本地查询
# ──────────────────────────────────────────────
def flatten_nodes(data, result=None):
    """将树形节点结构展平为列表（兼容列表和树形两种格式）"""
    if result is None:
        result = []
    if isinstance(data, list):
        for item in data:
            flatten_nodes(item, result)
    elif isinstance(data, dict):
        if "uid" in data:
            node = {k: v for k, v in data.items() if k != "children"}
            result.append(node)
        children = data.get("children", [])
        if children:
            flatten_nodes(children, result)
    return result


def build_node_map(data):
    """构建 uid -> node 映射，同时保留 children 引用用于后代查询"""
    node_map = {}
    if isinstance(data, list):
        for item in data:
            _collect_node_map(item, node_map)
    elif isinstance(data, dict):
        _collect_node_map(data, node_map)
    return node_map


def _collect_node_map(node, node_map):
    if not isinstance(node, dict):
        return
    uid = node.get("uid")
    if uid:
        node_map[uid] = node
    for child in node.get("children", []):
        _collect_node_map(child, node_map)


def get_ancestors(uid, node_map, parent_map):
    """递归获取祖先节点列表"""
    ancestors = []
    current = uid
    while True:
        parent_uid = parent_map.get(current)
        if not parent_uid or parent_uid not in node_map:
            break
        parent_node = node_map[parent_uid]
        ancestors.append({k: v for k, v in parent_node.items() if k != "children"})
        current = parent_uid
    return ancestors


def get_descendants(uid, node_map):
    """递归获取后代节点列表"""
    node = node_map.get(uid)
    if not node:
        return []
    descendants = []
    for child in node.get("children", []):
        child_uid = child.get("uid")
        if child_uid:
            descendants.append({k: v for k, v in child.items() if k != "children"})
            descendants.extend(get_descendants(child_uid, node_map))
    return descendants


def build_parent_map(data, parent_map=None, parent_uid=None):
    """构建 uid -> parent_uid 映射"""
    if parent_map is None:
        parent_map = {}
    if isinstance(data, list):
        for item in data:
            build_parent_map(item, parent_map, parent_uid)
    elif isinstance(data, dict):
        uid = data.get("uid")
        if uid:
            parent_map[uid] = parent_uid
        for child in data.get("children", []):
            build_parent_map(child, parent_map, uid)
    return parent_map


def search_local(design_uid, uids, ancestor=False, descendant=False, kind=None):
    """从本地 assets/{design_uid}.json 按 uid 查询节点，返回 (nodes, found) 元组
    uids 为空时返回整个 design 下所有节点"""
    local_file = os.path.join(TESTBUDDY_DIR, "{}.json".format(design_uid))
    if not os.path.exists(local_file):
        return None, False

    with open(local_file, "r", encoding="utf-8") as f:
        raw = json.load(f)

    node_map = build_node_map(raw)
    parent_map = build_parent_map(raw)
    kind_upper = kind.upper() if kind else None

    # uids 为空时，返回整个 design 下所有节点
    if not uids:
        all_nodes = flatten_nodes(raw)
        if kind_upper:
            all_nodes = [n for n in all_nodes if n.get("kind", "").upper() == kind_upper]
        return all_nodes, True

    result = []
    seen_uids = set()

    for uid in uids:
        node = node_map.get(uid)
        if not node:
            continue
        base = {k: v for k, v in node.items() if k != "children"}

        # kind 过滤
        if kind_upper and base.get("kind", "").upper() != kind_upper:
            continue

        if uid not in seen_uids:
            result.append(base)
            seen_uids.add(uid)

        # 祖先节点
        if ancestor:
            for anc in get_ancestors(uid, node_map, parent_map):
                if anc.get("uid") not in seen_uids:
                    result.append(anc)
                    seen_uids.add(anc["uid"])

        # 后代节点
        if descendant:
            for desc in get_descendants(uid, node_map):
                desc_uid = desc.get("uid")
                if desc_uid and desc_uid not in seen_uids:
                    if kind_upper and desc.get("kind", "").upper() != kind_upper:
                        continue
                    result.append(desc)
                    seen_uids.add(desc_uid)

    return result, True


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
def cmd_search_node(args):
    if not args.design_uid:
        return {"status": "error", "msg": "缺少 --design_uid 参数"}
    # namespace 非必填，后端会从 token 中获取
    # uids 非必填，不填时默认查询整个 design
    uids = args.uids or []

    token = get_token()
    if not token:
        return {
            "status": "error",
            "msg": "testbuddy skill缺少token无法执行，请先申请 testbuddy token，申请地址：https://testbuddy.woa.com/tencent/personal/account, 写入环境变量中，变量名：TESTBUDDY_TOKEN【export TESTBUDDY_TOKEN=****】",
        }

    # ── mindmap 模式：优先从本地文件查询（uids 为空时默认查询整个 design）──
    mode = get_mode()
    if mode == "mindmap":
        matched, found = search_local(args.design_uid, uids, args.ancestor, args.descendant, args.kind)
        if found:
            return {
                "status": "success",
                "source": "local",
                "design_uid": args.design_uid,
                "total": len(matched),
                "data": matched,
            }

    # ── chat 模式或本地文件不存在，走远程接口 ──
    fields = []
    if args.ancestor:
        fields.append("Ancestor")
    if args.descendant:
        fields.append("Descendant")

    body = {
        "design_uid": args.design_uid,
        "uids": uids,
        "fields": fields,
    }
    if args.namespace:
        body["namespace"] = args.namespace
    if args.kind:
        body["kind"] = args.kind.upper()

    resp = _post("/api/tb/v1/cb-plugin/node/search", token, body)

    if "error" in resp:
        return {"status": "error", "msg": resp["error"]}

    if not resp.get("success"):
        return {"status": "error", "msg": resp.get("error", str(resp))}

    return {
        "status": "success",
        "source": "remote",
        "design_uid": resp.get("design_uid", args.design_uid),
        "total": resp.get("total", 0),
        "data": resp.get("data", []),
    }


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────
USAGE = """
用法：python3 search_node.py [options]

选项：
  --namespace NAMESPACE         命名空间（可选，不填时后端从 token 中获取）
  --design_uid DESIGN_UID       设计文件 UID（必填）
  --uids UID [UID ...]          节点 UID 列表（可选，不填时查询整个 design 下所有节点）
  --ancestor                    同时返回祖先节点（可选，默认不返回）
  --no-descendant               不返回后代节点（可选，默认返回后代节点）
  --kind KIND                   节点类型过滤（可选，如 CASE/FEATURE/STORY/TEST_POINT）

查询策略：
  1. mindmap 模式：指定 uids 时优先从本地 .testbuddy/assets/{design_uid}.json 查询（速度快）
  2. chat 模式或本地文件不存在时，调用远程接口（需要 token）

示例：
  python3 search_node.py --design_uid design-Az7SsiL3Ui                                          # 查询整个 design
  python3 search_node.py --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2                    # 查询指定节点
  python3 search_node.py --design_uid design-Az7SsiL3Ui --uids uid1 uid2 uid3 --ancestor          # 同时返回祖先
  python3 search_node.py --design_uid design-Az7SsiL3Ui --uids feature-Kx9Yz8Wv7U --kind CASE     # 按类型过滤
  python3 search_node.py --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2 --no-descendant    # 不返回后代
  python3 search_node.py --namespace my_ns --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2  # 指定 namespace
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
    parser.add_argument("--uids", nargs="+", default=None)
    parser.add_argument("--ancestor", action="store_true", default=False)
    parser.add_argument("--descendant", action="store_true", default=True)
    parser.add_argument("--no-descendant", dest="descendant", action="store_false")
    parser.add_argument("--kind", default=None)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(json.dumps({"status": "error", "msg": "参数解析失败，请检查参数格式"}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = cmd_search_node(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "success" else 1)
    except Exception as e:
        print(json.dumps({"status": "error", "msg": "脚本执行异常: {}".format(str(e))}, ensure_ascii=False, indent=2))
        sys.exit(1)
