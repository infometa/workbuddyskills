#!/usr/bin/env python3
"""
AI生文 - LinkFox Skill (异步模式)
调用 aigc/textGenAsync 创建任务，然后轮询 aigc/textTaskQuery 获取结果。

Usage:
  python aigc_textgen.py '<JSON parameters>'                  # 自动：小结果全量；大结果写文件+摘要
  python aigc_textgen.py --stdin                              # 从 stdin 读取 JSON 参数
  python aigc_textgen.py '<JSON parameters>' --inline         # 强制全量打印到 stdout
  python aigc_textgen.py --stdin --content-only               # 只输出 content 文本（同样已是单行）

输出契约（面向被其他 agent 调用）：
  - stdout 只放机器数据：默认/--inline 为完整响应 JSON；大结果为 JSON 信封 {ok, truncated, savedPath, bytes, content}；
    --content-only 例外（stdout 为纯文本 content）。
  - 所有提示/摘要/诊断（CHAIN-HINT、Saved full response、summarize）一律走 stderr，stdout 始终可 json.loads。
  - 失败（网络错误 / errcode 非 200 / status==FAILED）时退出码非 0，agent 可凭退出码判错。

默认行为：
  - 响应体 <= SMALL_THRESHOLD 字节：完整响应 JSON 打印到 stdout
  - 响应体较大：写入 <cwd>/linkfox/<YYYY-MM-DD>/.../linkfox-aigc-textgen-<timestamp>.json，stdout 输出 JSON 信封

换行符压平（默认开启，无需任何 flag）：
  无论哪种输出模式，content 中的换行都会统一替换为单字符占位符 ⏎（U+23CE），
  同时覆盖两种形态：真实换行控制符（\r\n / \r / \n）与字面量两字符转义序列（\n / \r\n / \r）。
  该字符在 shell 单引号和 JSON 字符串中均无需转义，可安全捕获进变量并内联拼接进下游参数 JSON。
  下游脚本会自动把 ⏎ 还原为真实换行符（decode_nl），因此文本无损传递。
"""

import json
import os
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from linkfox_paths import decode_nl_in_obj, encode_nl, get_api_base, resolve_data_path


CREATE_PATH = "/aigc/textGenAsync"
QUERY_PATH = "/aigc/textTaskQuery"
SLUG = "linkfox-aigc-textgen"
POLL_INTERVAL_START = 10
POLL_INTERVAL_MIN = 5
POLL_INTERVAL_STEP = 1
MAX_POLL_TIME = 600
HTTP_TIMEOUT = 150
SMALL_THRESHOLD = 8000


def _encode_nl(text):
    """把 content 内真实换行符压平为单字符占位符 ⏎，供链式调用安全传递（复用共享实现）。"""
    return encode_nl(text)


def _decode_params(params):
    """入参解码：把上游 --content-only 注入的换行符占位符 ⏎ 还原为真实换行符。"""
    return decode_nl_in_obj(params)

def get_api_key():
    """
获取配置在环境变量的API Key。
如果获取不到，按 SKILL.md 的 **## 解决认证和积分问题** 处理。
"""
    key = os.environ.get("LINKFOX_AGENT_API_KEY") or os.environ.get("LINKFOXAGENT_API_KEY")
    if not key:
        print(
            "API Key 未配置",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def _post(url, params):
    api_key = get_api_key()
    data = json.dumps(params, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "User-Agent": "LinkFox-Skill/2.0",
        "SESSION_ID": os.environ.get("SESSION_ID", ""),
        "MESSAGE_ID": os.environ.get("MESSAGE_ID", ""),
        "MODE_ID": os.environ.get("MODE_ID", ""),
        "APP_NAME": os.environ.get("APP_NAME", ""),
    }
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            return json.loads(body) if body else {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception:
            return {"error": f"HTTP {e.code}: {e.reason}", "details": body}
    except URLError as e:
        return {"error": f"Connection failed: {e.reason}"}


def create_task(params):
    return _post(get_api_base() + CREATE_PATH, params)


def query_task(task_id, member_id):
    return _post(get_api_base() + QUERY_PATH, {"taskId": task_id, "memberId": member_id})


def poll_until_done(task_id, member_id):
    start = time.time()
    interval = POLL_INTERVAL_START
    while time.time() - start < MAX_POLL_TIME:
        time.sleep(interval)
        result = query_task(task_id, member_id)
        if result.get("error"):
            print(f"  Poll error: {result['error']}", file=sys.stderr)
            interval = max(interval - POLL_INTERVAL_STEP, POLL_INTERVAL_MIN)
            continue
        status = result.get("status")
        if status == "SUCCESS":
            return result
        if status == "FAILED":
            return result
        elapsed = int(time.time() - start)
        print(f"  Polling... status={status}, elapsed={elapsed}s, next in {interval}s", file=sys.stderr)
        interval = max(interval - POLL_INTERVAL_STEP, POLL_INTERVAL_MIN)
    return {"error": f"Polling timeout after {MAX_POLL_TIME}s", "taskId": task_id}


def _find_main_list(obj):
    best = (None, None, -1)

    def walk(node, path):
        nonlocal best
        if isinstance(node, list):
            if len(node) > best[2]:
                best = (path, node, len(node))
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)

    walk(obj, "")
    return best[0], best[1]


def summarize(result):
    """人类可读摘要——全部输出到 stderr，保持 stdout 干净可解析。"""
    if not isinstance(result, dict):
        print(f"Response type: {type(result).__name__}", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False)[:500], file=sys.stderr)
        return

    print(f"Top-level keys: {list(result.keys())}", file=sys.stderr)

    for k in ("errcode", "errorCode", "code", "errmsg", "msg",
              "total", "totalCount", "count", "costTime", "success", "status"):
        if k in result:
            v = result[k]
            if isinstance(v, (int, float, bool, str)):
                print(f"  {k}: {v}", file=sys.stderr)

    list_path, main_list = _find_main_list(result)
    if list_path is not None and main_list:
        print(f"\nMain list field: `{list_path}` (length={len(main_list)})", file=sys.stderr)
        sample = main_list[:3]
        print(f"Sample (first {len(sample)} of {len(main_list)}):", file=sys.stderr)
        print(json.dumps(sample, indent=2, ensure_ascii=False), file=sys.stderr)


def _extract_content(result):
    """从响应中提取 content 字段，支持 data.content 和顶层 content 两种路径。"""
    if not isinstance(result, dict):
        return None
    data = result.get("data") or result.get("result")
    if isinstance(data, dict) and "content" in data:
        return data["content"]
    return result.get("content")


def _is_failure(result):
    """判定本次调用是否失败，供退出码使用。"""
    if not isinstance(result, dict):
        return True
    if "error" in result:
        return True
    for code_key in ("errcode", "errorCode", "code"):
        if code_key in result and result[code_key] not in (200, "200", None):
            return True
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    if result.get("status") in (4, "FAILED") or data.get("status") in (4, "FAILED"):
        return True
    return False


def _encode_content_in_result(result):
    """默认在原地把 result 里的 content 换行压平成单字符 ⏎。"""
    if not isinstance(result, dict):
        return result
    data = result.get("data") or result.get("result")
    if isinstance(data, dict) and "content" in data:
        data["content"] = _encode_nl(data["content"])
    elif "content" in result:
        result["content"] = _encode_nl(result["content"])
    return result


def _resolve_output_path(ts):
    return resolve_data_path(SLUG, ts)


def _read_params(argv):
    if "--stdin" in argv:
        raw = sys.stdin.read()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    remaining = [a for a in argv if a not in ("--inline", "--content-only")]
    if not remaining:
        print(
            "Usage: aigc_textgen.py '<JSON>' [--inline]\n"
            "       aigc_textgen.py --stdin [--inline]",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        return json.loads(remaining[0])
    except json.JSONDecodeError as e:
        print(f"Invalid parameter format: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    argv = sys.argv[1:]
    inline = "--inline" in argv
    content_only = "--content-only" in argv

    params = _decode_params(_read_params(argv))
    member_id = params.get("memberId", "")

    create_result = create_task(params)
    if create_result.get("error"):
        print(json.dumps(create_result, ensure_ascii=False))
        sys.exit(1)

    task_id = create_result.get("taskId")
    if not task_id:
        print(json.dumps(create_result, ensure_ascii=False))
        sys.exit(1)

    print(f"Task created: taskId={task_id}", file=sys.stderr)

    result = poll_until_done(task_id, member_id)

    _encode_content_in_result(result)
    failed = _is_failure(result)

    if content_only:
        content = _extract_content(result)
        if content is None:
            print("ERROR: content field not found in response", file=sys.stderr)
            print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
            sys.exit(1)
        sys.stdout.write(content)
        sys.stdout.write("\n")
        sys.exit(1 if failed else 0)

    if inline:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1 if failed else 0)

    serialized = json.dumps(result, ensure_ascii=False, indent=2)

    if len(serialized.encode("utf-8")) <= SMALL_THRESHOLD:
        print(serialized)
        if _extract_content(result) is not None:
            print(
                "# CHAIN-HINT: content 已压平为单行（换行=⏎），可直接提取后内联拼接进下游参数 JSON；"
                "也可用 --content-only 只取文本。下游脚本接收后会自动把 ⏎ 还原为换行符。",
                file=sys.stderr,
            )
        sys.exit(1 if failed else 0)

    ts = int(time.time())
    out_path = _resolve_output_path(ts)
    saved_path = None
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(serialized)
        saved_path = out_path
        print(f"Saved full response: {out_path} ({len(serialized)} bytes)", file=sys.stderr)
    except OSError as e:
        print(f"Failed to save to {out_path}: {e}", file=sys.stderr)

    envelope = {
        "ok": not failed,
        "truncated": True,
        "savedPath": saved_path,
        "bytes": len(serialized),
        "content": _extract_content(result),
    }
    print(json.dumps(envelope, ensure_ascii=False))
    summarize(result)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
