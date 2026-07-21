#!/usr/bin/env bash
# NeoData 金融数据查询 - curl 封装（通过代理 API）
#
# Usage:
#   bash query.sh "腾讯最新财报"
#   bash query.sh --token "<credential>" "贵州茅台股价"
#   bash query.sh --save-token "<credential>"
#
# 凭证优先级: --token 参数 > ~/.workbuddy/.neodata_token 缓存文件（12 小时有效期）
#
# 环境变量 (可选):
#   NEODATA_ENDPOINT  - 代理 URL (可选，默认 https://copilot.tencent.com/agenttool/v1/neodata)
#   NEODATA_DATA_TYPE - 数据类型 all/api/doc (可选，默认不传由代理填充)

set -euo pipefail

DEFAULT_ENDPOINT="https://copilot.tencent.com/agenttool/v1/neodata"
TOKEN_FILE="$HOME/.workbuddy/.neodata_token"
TOKEN_TTL=43200  # 12 小时 = 43200 秒

CLI_TOKEN=""
SAVE_TOKEN=""
QUERY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --token)
            CLI_TOKEN="$2"
            shift 2
            ;;
        --save-token)
            SAVE_TOKEN="$2"
            shift 2
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done

if [[ -n "$SAVE_TOKEN" ]]; then
    mkdir -p "$(dirname "$TOKEN_FILE")"
    NOW=$(date +%s)
    TOKEN_VALUE="$SAVE_TOKEN" SAVED_AT="$NOW" /usr/bin/env python3 - <<'PY' > "$TOKEN_FILE"
import json
import os
print(json.dumps({"token": os.environ["TOKEN_VALUE"], "saved_at": int(os.environ["SAVED_AT"])}))
PY
    chmod 600 "$TOKEN_FILE"
    echo "凭证已保存到 $TOKEN_FILE（有效期 12 小时）"
    exit 0
fi

if [[ -z "$QUERY" ]]; then
    echo "用法: bash query.sh [--token <credential>] <query>" >&2
    echo "      bash query.sh --save-token <credential>" >&2
    exit 1
fi

ENDPOINT="${NEODATA_ENDPOINT:-$DEFAULT_ENDPOINT}"
DATA_TYPE="${NEODATA_DATA_TYPE:-}"

TOKEN="$CLI_TOKEN"
if [[ -z "$TOKEN" ]]; then
    if [[ ! -f "$TOKEN_FILE" ]]; then
        echo "TOKEN_MISSING: 未找到本地缓存凭证，需要获取凭证" >&2
        exit 1
    fi

    CACHE_RESULT=$(TOKEN_FILE="$TOKEN_FILE" TOKEN_TTL="$TOKEN_TTL" /usr/bin/env python3 - <<'PY'
import json
import os
import time
from pathlib import Path

p = Path(os.environ["TOKEN_FILE"])
try:
    raw = p.read_text(encoding="utf-8").strip()
except PermissionError:
    print("TOKEN_MISSING: 无法读取本地缓存凭证，需要获取凭证")
    raise SystemExit(1)

if not raw:
    print("TOKEN_MISSING: 本地缓存凭证为空，需要获取凭证")
    raise SystemExit(1)

try:
    data = json.loads(raw)
except Exception:
    print("TOKEN_EXPIRED: 本地缓存为旧格式或格式异常，需要重新获取凭证")
    raise SystemExit(1)

credential = data.get("token", "")
saved_at = data.get("saved_at", 0)
if not credential:
    print("TOKEN_MISSING: 本地缓存缺少凭证内容，需要获取凭证")
    raise SystemExit(1)
if time.time() - saved_at > int(os.environ["TOKEN_TTL"]):
    print("TOKEN_EXPIRED: 本地缓存凭证已超过 12 小时，需要重新获取凭证")
    raise SystemExit(1)
print(credential)
PY
) || {
        echo "$CACHE_RESULT" >&2
        exit 1
    }
    TOKEN="$CACHE_RESULT"
fi

BODY=$(QUERY="$QUERY" DATA_TYPE="$DATA_TYPE" /usr/bin/env python3 - <<'PY'
import json
import os
payload = {
    "query": os.environ["QUERY"],
    "channel": "neodata",
    "sub_channel": "workbuddy",
}
data_type = os.environ.get("DATA_TYPE", "")
if data_type:
    payload["data_type"] = data_type
print(json.dumps(payload, ensure_ascii=False))
PY
)

RESPONSE=$(curl --silent --show-error --location --max-time 30 --connect-timeout 10 \
    --write-out "\n%{http_code}" \
    "${ENDPOINT}" \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer ${TOKEN}" \
    --data "$BODY")

HTTP_CODE=$(printf "%s" "$RESPONSE" | tail -1)
BODY_RESP=$(printf "%s" "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "403" ]]; then
    echo "AUTH_ERROR: HTTP ${HTTP_CODE}，凭证已失效或无权限" >&2
    exit 2
fi

if [[ "$HTTP_CODE" -ne 200 ]]; then
    echo "REQUEST_FAILED: HTTP ${HTTP_CODE}" >&2
    [[ -n "$BODY_RESP" ]] && echo "$BODY_RESP" >&2
    exit 1
fi

AUTH_CHECK=$(BODY_RESP="$BODY_RESP" /usr/bin/env python3 - <<'PY'
import json
import os
body = os.environ.get("BODY_RESP", "")
try:
    data = json.loads(body)
except Exception:
    print("")
    raise SystemExit(0)
code = str(data.get("code", ""))
msg = str(data.get("msg", "")).lower()
keywords = ("token", "认证", "鉴权", "凭证", "unauthorized", "forbidden")
if code == "40101" or any(keyword in msg for keyword in keywords):
    print("AUTH_ERROR: 服务返回鉴权错误，需要重新获取凭证")
PY
)

if [[ -n "$AUTH_CHECK" ]]; then
    echo "$AUTH_CHECK" >&2
    exit 2
fi

printf "%s" "$BODY_RESP" | /usr/bin/env python3 -m json.tool 2>/dev/null || printf "%s\n" "$BODY_RESP"
