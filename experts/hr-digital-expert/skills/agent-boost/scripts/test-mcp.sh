#!/usr/bin/env bash
# ============================================================
# agent-boost test-mcp — MCP 工具质量 + 权限测试（§5 验证）
#
# 三层：L1 连通(tools/list) → L2 可调用(只读 GET) → L3 权限(预期用例)
#
# 用法:
#   MCP_LOCAL_URL="http://127.0.0.1:8932/mcp" \
#   AUTHZ_MANIFEST="/abs/.agent/authz/api-authz.json" \
#   REPORT_OUT="/abs/.agent/mcp-test-report.json" \
#   ADMIN_STAFF="zhangsan" \
#   NONADMIN_STAFF="agent-boost-probe-nonadmin" \
#   bash test-mcp.sh
#
# 环境变量:
#   MCP_LOCAL_URL  (必填) Bridge 的 /mcp 可达地址（本机或容器内）
#   AUTHZ_MANIFEST (可选) 授权清单路径；无则只跑 L1+L2（不测权限）
#   REPORT_OUT     (可选) 报告落盘路径，默认 {cwd}/.agent/mcp-test-report.json
#   ADMIN_STAFF    (可选) 管理员样例工号（L3 admin 身份）
#   NONADMIN_STAFF (可选) 非管理员合成名，默认 agent-boost-probe-nonadmin
#
# 说明：通过 JSON-RPC 调 Bridge，请求头带 X-Staff-Name/X-Staff-Id 模拟真实身份链路。
#       denial 判定依据应用侧授权中间件返回的 forbidden/unauthenticated 标记或 _http_status。
# ============================================================
set -euo pipefail
source "$(dirname "$0")/_env.sh"

: "${MCP_LOCAL_URL:?MCP_LOCAL_URL is required}"
export MCP_LOCAL_URL
export AUTHZ_MANIFEST="${AUTHZ_MANIFEST:-}"
export REPORT_OUT="${REPORT_OUT:-}"
export ADMIN_STAFF="${ADMIN_STAFF:-}"
export NONADMIN_STAFF="${NONADMIN_STAFF:-agent-boost-probe-nonadmin}"

python3 << 'PYEOF'
import json, os, sys, time, urllib.request

URL = os.environ["MCP_LOCAL_URL"]
MANIFEST_PATH = os.environ.get("AUTHZ_MANIFEST") or ""
ADMIN = os.environ.get("ADMIN_STAFF") or ""
NONADMIN = os.environ.get("NONADMIN_STAFF") or "agent-boost-probe-nonadmin"

report = {"url": URL, "l1": {}, "l2": [], "l3": [], "summary": {}}


def _rpc(method, params=None, staff=None):
    """发一个 JSON-RPC 请求到 Bridge，返回 (ok, result_or_error, latency_ms)。"""
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if staff:
        req.add_header("X-Staff-Name", staff)
        req.add_header("X-Staff-Id", staff)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except Exception as e:
        return False, {"error": str(e)}, int((time.time() - t0) * 1000)
    lat = int((time.time() - t0) * 1000)
    # 兼容 SSE：抽取 data: 行里的 JSON
    payload = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            try:
                payload = json.loads(line)
                break
            except Exception:
                continue
    if payload is None:
        try:
            payload = json.loads(raw)
        except Exception:
            return False, {"error": "unparseable response", "raw": raw[:300]}, lat
    if "error" in payload:
        return False, payload["error"], lat
    return True, payload.get("result", payload), lat


def _tool_text(result):
    """从 tools/call 结果里抽出文本内容。"""
    try:
        c = result.get("content") or []
        for item in c:
            if item.get("type") == "text":
                return item.get("text", "")
    except Exception:
        pass
    return json.dumps(result, ensure_ascii=False)


def _is_denied(text):
    low = text.lower()
    return ('"forbidden"' in low or '"unauthenticated"' in low
            or '"_http_status": 401' in low or '"_http_status": 403' in low
            or '_http_status": 403' in low or '_http_status": 401' in low)


def call_api_tool(method, path, staff, params=None):
    args = {"method": method, "path": path}
    if params:
        args["params"] = params
    return _rpc("tools/call", {"name": "call_api_tool", "arguments": args}, staff=staff)


# ── L1 连通 ──
ok, res, lat = _rpc("tools/list")
tools = res.get("tools", []) if ok else []
report["l1"] = {"ok": ok and len(tools) > 0, "toolCount": len(tools), "latencyMs": lat}
if not report["l1"]["ok"]:
    report["l1"]["error"] = res
    print("❌ L1 连通失败：", json.dumps(res, ensure_ascii=False)[:200])
    print(json.dumps(report, ensure_ascii=False))
    # L1 失败无需继续
    if os.environ.get("REPORT_OUT"):
        p = os.environ["REPORT_OUT"]
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(report, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    sys.exit(1)
print(f"✅ L1 连通：{len(tools)} 个工具，{lat}ms")

# ── 加载清单（authz 能力启用时传入，L3 权限测试需要）──
manifest = None
if MANIFEST_PATH and os.path.exists(MANIFEST_PATH):
    try:
        manifest = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ 授权清单解析失败，跳过 L3：{e}")

# ── 获取 API 端点列表（L2 核心测试不依赖 authz）──
# 端点来源：authz 启用时优先 manifest.apis；否则调 list_endpoints 工具获取
if manifest:
    api_list = manifest.get("apis", [])
else:
    ok_le, res_le, _ = _rpc("tools/call", {"name": "list_endpoints", "arguments": {}})
    eps_text = _tool_text(res_le) if ok_le else "[]"
    try:
        api_list = json.loads(eps_text)
    except Exception:
        api_list = []
    print(f"📋 未提供授权清单，从 list_endpoints 获取 {len(api_list)} 个端点用于 L2")

# ── L2 可调用（只读 GET，核心测试，所有应用执行）──
admin_for_l2 = (ADMIN or (manifest.get("test", {}) or {}).get("adminStaff")) if manifest else ""
for a in api_list:
    if (a.get("method", "GET")).upper() != "GET":
        continue
    if manifest and a.get("requiredRole") not in (None, "public", "user"):
        continue  # 受限接口在 L3 测（仅 authz 启用时）
    ok, res, lat = call_api_tool("GET", a["path"], staff=admin_for_l2)
    text = _tool_text(res) if ok else json.dumps(res, ensure_ascii=False)
    passed = ok and not _is_denied(text) and '"error"' not in text[:120].lower()
    report["l2"].append({"path": a["path"], "ok": passed, "latencyMs": lat,
                         "sample": text[:160]})
    print(f"{'✅' if passed else '⚠️'} L2 {a['path']} ({lat}ms)")

# ── L3 权限（预期用例）──
if manifest:
    cases = (manifest.get("test", {}) or {}).get("cases", [])
    admin = ADMIN or (manifest.get("test", {}) or {}).get("adminStaff") or ""
    nonadmin = (manifest.get("test", {}) or {}).get("nonadminStaff") or NONADMIN
    for c in cases:
        who = admin if c.get("as") == "admin" else nonadmin
        expect = c.get("expect")
        if expect == "allow-readonly-skip":
            report["l3"].append({**c, "result": "skip", "note": "写操作，跳过破坏性验证"})
            print(f"⏭️  L3 {c['method']} {c['path']} as {c['as']} → 跳过(写操作)")
            continue
        if c.get("as") == "admin" and not admin:
            report["l3"].append({**c, "result": "skip", "note": "无 admin 样例工号"})
            print(f"⏭️  L3 {c['method']} {c['path']} → 跳过(缺 admin 样例)")
            continue
        ok, res, lat = call_api_tool(c["method"], c["path"], staff=who)
        text = _tool_text(res) if ok else json.dumps(res, ensure_ascii=False)
        denied = _is_denied(text)
        if expect == "deny":
            passed = denied
        else:  # allow
            passed = not denied
        report["l3"].append({**c, "result": "pass" if passed else "fail",
                             "denied": denied, "latencyMs": lat, "sample": text[:160]})
        print(f"{'✅' if passed else '❌'} L3 {c['method']} {c['path']} as {c['as']} "
              f"期望={expect} 实际={'拒绝' if denied else '放行'}")

# ── 汇总 ──
l2_pass = sum(1 for x in report["l2"] if x["ok"])
l3_fail = [x for x in report["l3"] if x.get("result") == "fail"]
report["summary"] = {
    "l1": report["l1"]["ok"],
    "l2Pass": l2_pass, "l2Total": len(report["l2"]),
    "l3Fail": len(l3_fail), "l3Total": len(report["l3"]),
    "gate": bool(report["l1"]["ok"] and l2_pass == len(report["l2"]) and not l3_fail),
}
print("\n📋 汇总:", json.dumps(report["summary"], ensure_ascii=False))

out = os.environ.get("REPORT_OUT")
if not out:
    # 核心报告统一在 .agent/mcp-test-report.json（不依赖 manifest 路径）
    out = os.path.join(os.getcwd(), ".agent", "mcp-test-report.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"📄 报告已写入 → {out}")
PYEOF
