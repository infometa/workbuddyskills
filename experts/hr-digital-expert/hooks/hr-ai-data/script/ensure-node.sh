#!/usr/bin/env bash
# =============================================================================
# ensure-node.sh — hook 转接脚本（macOS / Linux / Windows Git Bash）
# =============================================================================
# 用法：ensure-node.sh <event-type>
#   <event-type>：事件名，如 session-start / pre-tool / user-prompt 等
#
# 目的：
#   查找可用的 Node.js（>= v18），找到后用它执行对应的 handler 脚本。
#
# 查找顺序：
#   1) 系统 PATH 上 node >= v18                                    → 使用该 node
#   2) ~/.workbuddy/binaries/node/versions/ 按版本降序查找         → 使用该 node
#   3) ~/.page-deliver/bin/node-{PLATFORM_ARCH}/bin/node           → 使用该 node
#
# 退出码：始终 0，不阻塞主流程。
# =============================================================================

set -uo pipefail

MIN_MAJOR=18

PLUGIN_ROOT="${CODEBUDDY_PLUGIN_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}"

# 按事件类型分发不同 handler（与 ensure-node.ps1 保持一致）
EVENT_TYPE="${1:-session-start}"
case "$EVENT_TYPE" in
  pre-tool)       HANDLER_JS="$PLUGIN_ROOT/hooks/hr-ai-data/script/pre_tool_handler.js" ;;
  user-prompt)    HANDLER_JS="$PLUGIN_ROOT/hooks/hr-ai-data/script/user_prompt_handler.js" ;;
  session-start)  HANDLER_JS="$PLUGIN_ROOT/hooks/hr-ai-data/script/session_start_handler.js" ;;
  session-end)    HANDLER_JS="$PLUGIN_ROOT/hooks/hr-ai-data/script/session_end_handler.js" ;;
  *)              HANDLER_JS="$PLUGIN_ROOT/hooks/hr-ai-data/script/pre_tool_handler.js" ;;
esac

# ---- 读取 stdin，保存供后续转发 -------------------------------------------

RAW="$(cat 2>/dev/null || true)"

# ---- 辅助函数 ---------------------------------------------------------------

node_major() {
  local v="$1"
  v="${v#v}"
  echo "${v%%.*}"
}

test_node_bin() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  local ver
  ver="$("$bin" --version 2>/dev/null)" || return 1
  local maj
  maj="$(node_major "$ver")"
  [ "$maj" -ge "$MIN_MAJOR" ]
}

# 找到可用 node 后，用它执行对应的 handler，将原始 stdin 透传进去
run_handler() {
  local node_bin="$1"
  if [ -f "$HANDLER_JS" ]; then
    printf '%s' "$RAW" | "$node_bin" "$HANDLER_JS" "$EVENT_TYPE" 2>/dev/null || true
  fi
  exit 0
}

# ---- Step 1: 系统 PATH 中的 node -------------------------------------------

if command -v node >/dev/null 2>&1; then
  SYS_NODE="$(command -v node)"
  if test_node_bin "$SYS_NODE"; then
    SYS_VER="$("$SYS_NODE" --version 2>/dev/null || echo unknown)"
    echo "[ensure-node] system node found: $SYS_NODE ($SYS_VER)" >&2
    run_handler "$SYS_NODE"
  fi
fi

# ---- Step 2: workbuddy 管理的 node -----------------------------------------

WORKBUDDY_NODE_ROOT="$HOME/.workbuddy/binaries/node/versions"
if [ -d "$WORKBUDDY_NODE_ROOT" ]; then
  while IFS= read -r VER_DIR; do
    [ -n "$VER_DIR" ] || continue
    WB_NODE="$WORKBUDDY_NODE_ROOT/$VER_DIR/bin/node"
    if ! test_node_bin "$WB_NODE"; then
      WB_NODE="$WORKBUDDY_NODE_ROOT/$VER_DIR/node.exe"
    fi
    if test_node_bin "$WB_NODE"; then
      WB_VER="$("$WB_NODE" --version 2>/dev/null || echo unknown)"
      echo "[ensure-node] workbuddy node found: $WB_NODE ($WB_VER)" >&2
      run_handler "$WB_NODE"
    fi
  done < <(ls -1 "$WORKBUDDY_NODE_ROOT" 2>/dev/null | sort -rV)
fi

# ---- Step 3: preflight 安装的 page-deliver 缓存 node -----------------------

PAGE_DELIVER_CACHE="$HOME/.page-deliver/bin"
if [ -d "$PAGE_DELIVER_CACHE" ]; then
  OS_NAME="$(uname -s)"
  ARCH="$(uname -m)"
  case "${OS_NAME}/${ARCH}" in
    Darwin/arm64)  PD_PLATFORM_ARCH="darwin-arm64" ;;
    Darwin/x86_64) PD_PLATFORM_ARCH="darwin-x64"   ;;
    Linux/x86_64)  PD_PLATFORM_ARCH="linux-x64"    ;;
    Linux/aarch64) PD_PLATFORM_ARCH="linux-arm64"  ;;
    *)             PD_PLATFORM_ARCH=""              ;;
  esac
  if [ -n "$PD_PLATFORM_ARCH" ]; then
    PD_NODE="$PAGE_DELIVER_CACHE/node-${PD_PLATFORM_ARCH}/bin/node"
    if test_node_bin "$PD_NODE"; then
      PD_VER="$("$PD_NODE" --version 2>/dev/null || echo unknown)"
      echo "[ensure-node] page-deliver cached node found: $PD_NODE ($PD_VER)" >&2
      run_handler "$PD_NODE"
    fi
  fi
fi

echo "[ensure-node] no usable Node found, skipping handler" >&2
exit 0
