#!/usr/bin/env bash
# ============================================================
# agent-boost gen-authz — 渲染授权中间件 + 落盘授权清单
#
# 用法:
#   FRAMEWORK="express" \
#   MANIFEST_PATH=".agent/authz/api-authz.json" \
#   MANIFEST_FILE="/abs/path/.agent/authz/api-authz.json" \
#   MANIFEST_JSON='{"schemaVersion":1,...}' \
#   ROLE_RESOLVER='<db/custom 型 resolver 代码，static/env 留空用默认>' \
#   bash gen-authz.sh /abs/path/middleware/agent-authz.js
#
# 环境变量:
#   FRAMEWORK     (必填) express | fastapi | flask
#   MANIFEST_PATH (可选) 中间件运行期读取清单的相对路径，默认 .agent/authz/api-authz.json
#   MANIFEST_FILE (可选) 授权清单落盘的绝对路径（配合 MANIFEST_JSON）
#   MANIFEST_JSON (可选) 授权清单内容；提供则校验 JSON 后写入 MANIFEST_FILE
#   ROLE_RESOLVER (可选) db/custom 型 Role Resolver 代码片段；留空则用模板内置默认（static/env）
#   $1            (必填) 中间件输出文件绝对路径
#
# 原理：读取对应框架 .template，替换 ${ROLE_RESOLVER} 与 ${MANIFEST_PATH}，写出并做语法检查。
# ============================================================
set -euo pipefail
source "$(dirname "$0")/_env.sh"   # 保持与其他脚本一致（本脚本不直接使用地址）

OUTPUT="${1:?Usage: gen-authz.sh <output_path>}"
: "${FRAMEWORK:?FRAMEWORK is required (express|fastapi|flask)}"
MANIFEST_PATH="${MANIFEST_PATH:-.agent/authz/api-authz.json}"
TPL_DIR="$(dirname "$0")/../assets/templates/authz"

case "$FRAMEWORK" in
  express) TEMPLATE_FILE="$TPL_DIR/express-agent-authz.js.template"; LANG_KIND="js" ;;
  fastapi) TEMPLATE_FILE="$TPL_DIR/fastapi_agent_authz.py.template"; LANG_KIND="py" ;;
  flask)   TEMPLATE_FILE="$TPL_DIR/flask_agent_authz.py.template";   LANG_KIND="py" ;;
  *) echo "ERROR: unsupported FRAMEWORK: $FRAMEWORK" >&2; exit 1 ;;
esac

[ -f "$TEMPLATE_FILE" ] || { echo "ERROR: template not found: $TEMPLATE_FILE" >&2; exit 1; }

# ── 默认 Role Resolver（static/env 场景，未显式传 ROLE_RESOLVER 时）──
if [ -z "${ROLE_RESOLVER:-}" ]; then
  if [ "$LANG_KIND" = "js" ]; then
    ROLE_RESOLVER=$'async function resolveRole(staffName, staffId) {\n  return defaultResolveRole(staffName, staffId);\n}'
  else
    ROLE_RESOLVER=$'def resolve_role(staff_name, staff_id):\n    return default_resolve_role(staff_name, staff_id)'
  fi
fi

# ── 落盘授权清单（可选）──
if [ -n "${MANIFEST_JSON:-}" ]; then
  : "${MANIFEST_FILE:?MANIFEST_FILE is required when MANIFEST_JSON is set}"
  MANIFEST_FILE="$MANIFEST_FILE" MANIFEST_JSON="$MANIFEST_JSON" python3 << 'PYEOF'
import json, os
data = json.loads(os.environ["MANIFEST_JSON"])  # 校验合法性
p = os.environ["MANIFEST_FILE"]
os.makedirs(os.path.dirname(p), exist_ok=True)
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"authz manifest written → {p}")
PYEOF
fi

# ── 渲染中间件 ──
TEMPLATE_FILE="$TEMPLATE_FILE" OUTPUT="$OUTPUT" \
MANIFEST_PATH="$MANIFEST_PATH" ROLE_RESOLVER="$ROLE_RESOLVER" python3 << 'PYEOF'
import os
tpl = open(os.environ["TEMPLATE_FILE"], encoding="utf-8").read()
tpl = tpl.replace("${MANIFEST_PATH}", os.environ["MANIFEST_PATH"])
tpl = tpl.replace("${ROLE_RESOLVER}", os.environ["ROLE_RESOLVER"])
out = os.environ["OUTPUT"]
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write(tpl)
print(f"agent-authz written → {out}")
PYEOF

# ── 语法检查 ──
if [ "$LANG_KIND" = "js" ]; then
  if command -v node >/dev/null 2>&1; then
    node --check "$OUTPUT" 2>&1 || { echo "ERROR: JS syntax check failed for $OUTPUT" >&2; exit 1; }
    echo "✅ syntax check passed (node --check)"
  else
    echo "⚠️ node 不可用，跳过 JS 语法检查"
  fi
else
  python3 -m py_compile "$OUTPUT" 2>&1 || { echo "ERROR: py syntax check failed for $OUTPUT" >&2; exit 1; }
  echo "✅ syntax check passed (py_compile)"
fi
