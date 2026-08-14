#!/usr/bin/env bash
# ============================================================
# agent-boost gen-bridge — 生成 mcp_server/ 目录（mcp_bridge.py + requirements.txt）
#
# 用法:
#   PROJECT_NAME="my-app" \
#   PROJECT_ID="my-app-20260101" \
#   APP_PORT="3456" \
#   BRIDGE_PORT="8932" \
#   KNOWN_ENDPOINTS_JSON='[{"method":"GET","path":"/api/health","summary":"健康检查"}]' \
#   PROJECT_TOOLS='# no project-specific tools' \
#   bash gen-bridge.sh /path/to/project/mcp_server
#
# 环境变量:
#   PROJECT_NAME         (必填) 项目显示名
#   PROJECT_ID           (必填) 项目唯一标识
#   APP_PORT             (可选) 应用端口，默认 3000
#   BRIDGE_PORT          (可选) Bridge 起始探测端口，默认 8932
#   KNOWN_ENDPOINTS_JSON (可选) 已知 API 端点 JSON 数组，默认 []
#   PROJECT_TOOLS        (可选) 项目特有 MCP 工具 Python 代码，默认注释占位
#   $1                   (必填) 输出目录路径（mcp_server/）
#
# 原理：读取 .template 文件，做 6 个 ${...} 占位符的纯文本替换，写入目标目录；
#       同时复制静态资产 requirements.txt 到同一目录。
# 避免 python3 -c "..." 内联渲染导致的转义地狱和 env 变量丢失问题。
# ============================================================
set -euo pipefail
source "$(dirname "$0")/_env.sh"   # 复用地址默认值（本脚本不直接使用，保持一致性）

OUTPUT_DIR="${1:?Usage: gen-bridge.sh <output_dir>}"
OUTPUT="${OUTPUT_DIR}/mcp_bridge.py"
TEMPLATE_FILE="$(dirname "$0")/../assets/templates/mcp_bridge.py.template"
REQ_TEMPLATE="$(dirname "$0")/../assets/templates/requirements.txt"

# 参数校验
: "${PROJECT_NAME:?PROJECT_NAME is required}"
: "${PROJECT_ID:?PROJECT_ID is required}"
APP_PORT="${APP_PORT:-3000}"
BRIDGE_PORT="${BRIDGE_PORT:-8932}"
KNOWN_ENDPOINTS_JSON="${KNOWN_ENDPOINTS_JSON:-[]}"
PROJECT_TOOLS="${PROJECT_TOOLS:-# no project-specific tools}"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "ERROR: template file not found: $TEMPLATE_FILE" >&2
    exit 1
fi

if [ ! -f "$REQ_TEMPLATE" ]; then
    echo "ERROR: requirements template not found: $REQ_TEMPLATE" >&2
    exit 1
fi

# 用 Python 做纯文本替换（env 传递，无转义问题）
TEMPLATE_FILE="$TEMPLATE_FILE" OUTPUT="$OUTPUT" \
PROJECT_NAME="$PROJECT_NAME" PROJECT_ID="$PROJECT_ID" APP_PORT="$APP_PORT" \
BRIDGE_PORT="$BRIDGE_PORT" KNOWN_ENDPOINTS_JSON="$KNOWN_ENDPOINTS_JSON" \
PROJECT_TOOLS="$PROJECT_TOOLS" python3 << 'PYEOF'
import os

tpl = open(os.environ["TEMPLATE_FILE"]).read()
tpl = tpl.replace("${PROJECT_NAME}", os.environ["PROJECT_NAME"])
tpl = tpl.replace("${PROJECT_ID}", os.environ["PROJECT_ID"])
tpl = tpl.replace("${APP_PORT}", os.environ["APP_PORT"])
tpl = tpl.replace("${BRIDGE_PORT}", os.environ["BRIDGE_PORT"])
tpl = tpl.replace("${KNOWN_ENDPOINTS_JSON}", os.environ["KNOWN_ENDPOINTS_JSON"])
tpl = tpl.replace("${PROJECT_TOOLS}", os.environ["PROJECT_TOOLS"])

out = os.environ["OUTPUT"]
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    f.write(tpl)
print(f"mcp_bridge.py written → {out}")
PYEOF

# 语法检查：渲染后立即验证 Python 语法正确性
python3 -m py_compile "$OUTPUT" 2>&1 || {
    echo "ERROR: syntax check failed for $OUTPUT" >&2
    exit 1
}
echo "✅ syntax check passed"

# 复制 requirements.txt（静态资产，无占位符）
cp "$REQ_TEMPLATE" "${OUTPUT_DIR}/requirements.txt"
echo "requirements.txt copied → ${OUTPUT_DIR}/requirements.txt"
