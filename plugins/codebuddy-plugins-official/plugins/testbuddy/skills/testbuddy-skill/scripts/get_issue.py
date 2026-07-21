#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# get_issue.py：获取需求/缺陷详情
# 调用 codebuddy server POST /issue 接口
#
# 用法：
#   python3 get_issue.py --workspace <workspace> --issue_id <id> [--issue_type STORY|BUG]
#   python3 get_issue.py --link <tapd_link>
#
# token 从 session.json 获取（参考 get_session.py load_session）
# server 地址从环境变量 TESTBUDDY_SERVER 获取（默认 https://testbuddy.woa.com）

import argparse
import json
import os
import re
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

# 工作区根目录（自动查找）
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
# 辅助工具
# ──────────────────────────────────────────────
def _parse_tapd_link(link):
    """从 TAPD 链接中解析 workspace、issue_id、issue_type。
    支持格式：
      https://tapd.woa.com/tapd_fe/{workspace}/story/detail/{issue_id}
      https://tapd.woa.com/tapd_fe/{workspace}/bug/detail/{issue_id}
      https://tapd.woa.com/prong/stories/view/{issue_id}
      https://tapd.woa.com/{workspace}/prong/stories/view/{issue_id}
    返回 (workspace, issue_id, issue_type) 或 (None, None, None)
    """
    if not link:
        return None, None, None

    # tapd_fe 格式：/tapd_fe/{workspace}/{story|bug}/detail/{issue_id}
    m = re.search(r"/tapd_fe/(\d+)/(story|bug)/detail/(\d+)", link)
    if m:
        workspace = m.group(1)
        issue_type = "STORY" if m.group(2) == "story" else "BUG"
        issue_id = m.group(3)
        return workspace, issue_id, issue_type

    # prong 格式带 workspace：/{workspace}/prong/stories/view/{issue_id}
    m = re.search(r"/(\d+)/prong/stories/view/(\d+)", link)
    if m:
        return m.group(1), m.group(2), "STORY"

    # prong 格式不带 workspace：/prong/stories/view/{issue_id}
    m = re.search(r"/prong/stories/view/(\d+)", link)
    if m:
        return None, m.group(1), "STORY"

    # prong bug 格式：/prong/bugs/view/{issue_id}
    m = re.search(r"/prong/bugs/view/(\d+)", link)
    if m:
        return None, m.group(1), "BUG"

    return None, None, None


def _save_story_info_to_session(workspace, issue_id, issue_type, issue_name, issue_url):
    """将需求/缺陷信息写入 session.json 的 story_info 字段，供后续 write_node 使用。
    格式：
    {
      "story_info": {
        "workspace": "12345678",
        "issue_id": "1001",
        "issue_type": "STORY",
        "issue_name": "需求名称",
        "issue_url": "https://tapd.woa.com/..."
      }
    }
    """
    from get_session import save_session

    session_data = _load_session_data() or {}
    session_data["story_info"] = {
        "workspace": workspace or "",
        "issue_id": issue_id or "",
        "issue_type": (issue_type or "STORY").upper(),
        "issue_name": issue_name or "",
        "issue_url": issue_url or "",
    }
    save_session(session_data)


# ──────────────────────────────────────────────
# 命令实现
# ──────────────────────────────────────────────
def cmd_get_issue(args):
    token = get_token()
    if not token:
        return {
            "status": "error",
            "msg": "testbuddy skill缺少token无法执行，请先申请 testbuddy token，申请地址：https://testbuddy.woa.com/tencent/personal/account, 写入环境变量中，变量名：TESTBUDDY_TOKEN【export TESTBUDDY_TOKEN=****】",
        }

    body = {}
    if args.link:
        body["link"] = args.link
    else:
        if not args.workspace or not args.issue_id:
            return {"status": "error", "msg": "需要 --workspace 和 --issue_id，或者使用 --link 参数"}
        body["workspace"] = args.workspace
        body["issue_id"] = args.issue_id
        if args.issue_type:
            body["issue_type"] = args.issue_type.upper()

    resp = _post("/api/tb/v1/cb-plugin/issue", token, body)

    if not isinstance(resp, dict):
        return {"status": "error", "msg": "服务端返回了非预期格式: {}".format(str(resp)[:500])}

    if "error" in resp:
        return {"status": "error", "msg": resp["error"]}

    if not resp.get("success"):
        return {"status": "error", "msg": resp.get("error", str(resp))}

    result = {
        "status": "success",
        "content": resp.get("content", ""),
    }

    # ── 将需求信息写入 session.json，供后续 write_node 自动创建需求节点 ──
    if args.link:
        workspace, issue_id, issue_type = _parse_tapd_link(args.link)
        # 如果链接解析失败，尝试从参数中获取
        if not workspace:
            workspace = args.workspace
        if not issue_id:
            issue_id = args.issue_id
        if not issue_type:
            issue_type = (args.issue_type or "STORY").upper()
    else:
        workspace = args.workspace
        issue_id = args.issue_id
        issue_type = (args.issue_type or "STORY").upper()

    issue_url = args.link or ""
    issue_name = resp.get("issue_name", "") or ""

    # 写入 session.json 的 story_info 字段
    try:
        _save_story_info_to_session(workspace, issue_id, issue_type, issue_name, issue_url)
        result["story_info_saved"] = True
    except Exception as e:
        result["story_info_saved"] = False
        result["story_info_error"] = str(e)

    return result


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────
USAGE = """
用法：python3 get_issue.py [options]

选项：
  --workspace WORKSPACE   TAPD 工作区 ID
  --issue_id ISSUE_ID     需求/缺陷 ID
  --issue_type TYPE       类型：STORY（默认）或 BUG
  --link LINK             TAPD 链接（支持 tapd_fe/prong 格式，与 workspace/issue_id 二选一）

示例：
  python3 get_issue.py --workspace 12345678 --issue_id 1001
  python3 get_issue.py --workspace 12345678 --issue_id 2001 --issue_type BUG
  python3 get_issue.py --link "https://tapd.woa.com/tapd_fe/12345678/story/detail/1001"
"""

if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--issue_id", default=None)
    parser.add_argument("--issue_type", default=None)
    parser.add_argument("--link", default=None)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(json.dumps({"status": "error", "msg": "参数解析失败，请检查参数格式"}, ensure_ascii=False))
        sys.exit(1)

    try:
        result = cmd_get_issue(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "success" else 1)
    except Exception as e:
        print(json.dumps({"status": "error", "msg": "脚本执行异常: {}".format(str(e))}, ensure_ascii=False, indent=2))
        sys.exit(1)
