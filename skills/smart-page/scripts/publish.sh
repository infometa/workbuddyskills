#!/usr/bin/env bash
# publish.sh · 自动把生成好的 HTML 发布到腾讯文档（一条命令跑完全链路）
#
# Usage:
#   publish.sh --html output/立项.html --title "立项方案"
#
# 链路：校验 workbuddy MCP → prepare-pack.sh → pre_import → PUT COS → async_import
#      → 轮询 import_progress 到 100 → 输出 FILE_URL
#
# 退出码：
#   0 成功，stdout 打印 FILE_URL=...
#   1 参数错误 / HTML 不存在
#   2 workbuddy MCP 未配置或未授权（提示用户在 WorkBuddy 内配置 tencent-docs 连接器）
#   3 打包失败
#   4 pre_import 失败
#   5 PUT 上传 HTTP 非 200
#   6 import_progress 超时（stdout 会打 TRACE_ID=...）

set -u

HTML=""
TITLE=""

usage() {
  cat >&2 <<'EOF'
Usage: publish.sh --html <html_path> [--title <title>]

  --title 可选，缺省时自动从 HTML 的 <title> 标签提取。

示例:
  publish.sh --html "output/立项方案.html" --title "立项方案"
  publish.sh --html "output/婚礼邀请函.html"
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --html)  HTML="$2";  shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "publish.sh: unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$HTML" ]] || usage
[[ -f "$HTML" ]]  || { echo "publish.sh: HTML 文件不存在: $HTML" >&2; exit 1; }

# 若未传 --title，从 HTML <title> 提取
if [[ -z "$TITLE" ]]; then
  TITLE=$(python3 -c "
import re, sys
html = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
print(m.group(1).strip() if m else '')
" "$HTML")
  if [[ -z "$TITLE" ]]; then
    # fallback：用文件名（去后缀）
    TITLE="$(basename "$HTML" .html)"
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURL_COMMON=(--silent --show-error --connect-timeout 10 --max-time 60 --retry 2 --retry-delay 2)
COS_LOG="${TMPDIR:-/tmp}/publish_cos.$$.log"
cleanup() { rm -f "$COS_LOG"; }
trap cleanup EXIT

# ============================================================
# ① 校验 workbuddy MCP 配置
# ============================================================
python3 - <<'PY_CHECK' || exit 2
import json, os, sys

src = os.path.expanduser("~/.workbuddy/mcp.json")
hint = (
    "未检测到可用的 WorkBuddy `tencent-docs` MCP 连接器。\n"
    "请在 WorkBuddy 中完成以下任一操作：\n"
    "  1) 打开「连接器 / MCP 管理」，添加并授权 `tencent-docs`\n"
    "  2) 或手动在 ~/.workbuddy/mcp.json 的 mcpServers.tencent-docs.headers 下\n"
    "     补充有效的 Authorization（必填）和 Cookie（可选）\n"
    "完成后重新执行发布命令。"
)

def fail(reason: str):
    print(f"publish.sh: {reason}", file=sys.stderr)
    print(hint, file=sys.stderr)
    sys.exit(1)  # 内部退出码，外层捕获后统一返回 2

if not os.path.isfile(src):
    fail(f"未找到 WorkBuddy MCP 配置文件: {src}")

try:
    cfg = json.load(open(src, encoding="utf-8"))
except Exception as e:
    fail(f"解析 {src} 失败: {e}")

server = (cfg.get("mcpServers") or {}).get("tencent-docs")
if not server:
    fail("WorkBuddy mcp.json 中未配置 `tencent-docs` 连接器")

headers = server.get("headers") or {}
auth = (headers.get("Authorization") or "").strip()
if not auth:
    fail("WorkBuddy `tencent-docs` 连接器尚未授权（headers.Authorization 为空）")
PY_CHECK

# ============================================================
# ② 打包
# ============================================================
PACK_OUT=$(bash "$SCRIPT_DIR/prepare-pack.sh" --html "$HTML" --title "$TITLE" 2>&1)
AIPAGE_PATH=$(echo "$PACK_OUT" | grep '^AIPAGE_PATH=' | head -1 | cut -d= -f2)
AIPAGE_SIZE=$(echo "$PACK_OUT" | grep '^AIPAGE_SIZE=' | head -1 | cut -d= -f2)
AIPAGE_MD5=$(echo "$PACK_OUT"  | grep '^AIPAGE_MD5='  | head -1 | cut -d= -f2)

if [[ -z "$AIPAGE_PATH" || -z "$AIPAGE_SIZE" || -z "$AIPAGE_MD5" || ! -f "$AIPAGE_PATH" ]]; then
  echo "publish.sh: 打包失败" >&2
  echo "$PACK_OUT" >&2
  exit 3
fi

FNAME=$(basename "$AIPAGE_PATH")

# ============================================================
# ③ 读取 MCP 鉴权（来源：~/.workbuddy/mcp.json）
# ============================================================
AUTH=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.workbuddy/mcp.json')))['mcpServers']['tencent-docs']['headers']['Authorization'])")
COOKIE=$(python3 -c "import json,os;h=json.load(open(os.path.expanduser('~/.workbuddy/mcp.json')))['mcpServers']['tencent-docs']['headers'];print(h.get('Cookie',''))")
MCP='https://docs.qq.com/openapi/mcp'

# ============================================================
# ④ pre_import
# ============================================================
PRE_BODY=$(python3 -c "
import json, sys
body = {'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'manage.pre_import','arguments':{'file_name':sys.argv[1],'file_size':int(sys.argv[2]),'file_md5':sys.argv[3]}}}
print(json.dumps(body, ensure_ascii=False))
" "$FNAME" "$AIPAGE_SIZE" "$AIPAGE_MD5")

PRE=$(curl "${CURL_COMMON[@]}" -X POST "$MCP" \
  -H "Authorization: $AUTH" ${COOKIE:+-H "Cookie: $COOKIE"} \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d "$PRE_BODY") || {
  echo "publish.sh: pre_import 网络请求失败" >&2
  exit 4
}

FILE_KEY=$(echo "$PRE"   | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('result',{}).get('structuredContent',{}).get('file_key',''))")
TASK_ID=$(echo "$PRE"    | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('result',{}).get('structuredContent',{}).get('task_id',''))")
UPLOAD_URL=$(echo "$PRE" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('result',{}).get('structuredContent',{}).get('upload_url',''))")

if [[ -z "$UPLOAD_URL" ]]; then
  echo "publish.sh: pre_import 失败" >&2
  echo "$PRE" >&2
  exit 4
fi

# ============================================================
# ⑤ PUT 上传到 COS
# ============================================================
HTTP=$(curl "${CURL_COMMON[@]}" -o "$COS_LOG" -w "%{http_code}" -X PUT \
  -H "Content-Length: $AIPAGE_SIZE" \
  --data-binary @"$AIPAGE_PATH" \
  "$UPLOAD_URL") || {
  echo "publish.sh: PUT 上传网络请求失败" >&2
  [[ -f "$COS_LOG" ]] && cat "$COS_LOG" >&2
  exit 5
}

if [[ "$HTTP" != "200" ]]; then
  echo "publish.sh: PUT 上传失败 HTTP=$HTTP" >&2
  [[ -f "$COS_LOG" ]] && cat "$COS_LOG" >&2
  exit 5
fi

# ============================================================
# ⑥ async_import
# ============================================================
IMPORT_BODY=$(python3 -c "
import json, sys
body = {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'manage.async_import','arguments':{'file_key':sys.argv[1],'file_name':sys.argv[2],'file_md5':sys.argv[3],'file_size':int(sys.argv[4]),'task_id':sys.argv[5]}}}
print(json.dumps(body, ensure_ascii=False))
" "$FILE_KEY" "$FNAME" "$AIPAGE_MD5" "$AIPAGE_SIZE" "$TASK_ID")

curl "${CURL_COMMON[@]}" -X POST "$MCP" \
  -H "Authorization: $AUTH" ${COOKIE:+-H "Cookie: $COOKIE"} \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d "$IMPORT_BODY" > /dev/null || {
  echo "publish.sh: async_import 网络请求失败" >&2
  exit 4
}

# ============================================================
# ⑦ 轮询 import_progress（最多 60 秒）
# ============================================================
FILE_URL=""
TRACE_ID=""
FILE_ID=""
for i in $(seq 1 20); do
  POLL_BODY=$(python3 -c "
import json, sys
body = {'jsonrpc':'2.0','id':int(sys.argv[1]),'method':'tools/call','params':{'name':'manage.import_progress','arguments':{'task_id':sys.argv[2]}}}
print(json.dumps(body, ensure_ascii=False))
" "$((10+i))" "$TASK_ID")

  RESP=$(curl "${CURL_COMMON[@]}" -X POST "$MCP" \
    -H "Authorization: $AUTH" ${COOKIE:+-H "Cookie: $COOKIE"} \
    -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
    -d "$POLL_BODY") || {
    echo "publish.sh: import_progress 网络请求失败（第 $i 次）" >&2
    sleep 3
    continue
  }
  FILE_URL=$(echo "$RESP" | python3 -c "import sys,json;d=json.load(sys.stdin);sc=d.get('result',{}).get('structuredContent',{});print(sc.get('file_url','') if sc.get('progress')==100 else '')")
  TRACE_ID=$(echo "$RESP" | python3 -c "import sys,json;d=json.load(sys.stdin);sc=d.get('result',{}).get('structuredContent',{});print(sc.get('trace_id',''))")
  FILE_ID=$(echo "$RESP"  | python3 -c "import sys,json;d=json.load(sys.stdin);sc=d.get('result',{}).get('structuredContent',{});print(sc.get('file_id',''))")
  if [[ -n "$FILE_URL" ]]; then
    break
  fi
  sleep 3
done

if [[ -z "$FILE_URL" ]]; then
  echo "publish.sh: import_progress 超时" >&2
  echo "TRACE_ID=$TRACE_ID"
  exit 6
fi

# ============================================================
# ⑧ 成功输出
# ============================================================
if [[ -n "$FILE_ID" && "$FILE_URL" != *"_fid="* ]]; then
  SEP="?"
  [[ "$FILE_URL" == *"?"* ]] && SEP="&"
  FILE_URL="${FILE_URL}${SEP}_fid=${FILE_ID}"
fi

echo "FILE_URL=$FILE_URL"
echo "FILE_ID=$FILE_ID"
echo "TRACE_ID=$TRACE_ID"
echo "AIPAGE_PATH=$AIPAGE_PATH"
