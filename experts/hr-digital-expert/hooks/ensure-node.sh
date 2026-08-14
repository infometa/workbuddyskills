#!/usr/bin/env bash
# =============================================================================
# ensure-node.sh — hook 转接脚本（WorkBuddy 专家专用，macOS / Linux / GitBash）
# =============================================================================
# 用法：ensure-node.sh <event-type>
#   <event-type>：传给 hook-handler.js 的事件名，如 session-start / pre-tool 等
#
# 目的：
#   定位 WorkBuddy 自带的 Node.js（>= v18），用它执行 hook-handler.js <event-type>。
#
#   WorkBuddy 客户端安装时会自带 node（保证 >= v18），但该 node 不注册到系统 PATH，
#   故不能直接 `node ...`，必须主动到 ~/.workbuddy/binaries/node/versions/ 下查找。
#   存在多版本时取版本号最大的目录。
#
# 退出码：始终 0，不阻塞主流程。
# =============================================================================

set -uo pipefail

# ---- 常量 ------------------------------------------------------------------

# 最低 Node 大版本要求 = 18。
# 原因：上报用的 page-deliver-cli bundle（由 mcporter-taihu 编译）通过 MCP HTTP transport
#       调用 globalThis.fetch 上报指标，fetch 在 Node 18+ 才内置（实验性，Node 18.17+ 稳定），
#       Node 16 会在调用时抛 `ReferenceError: fetch is not defined` 导致上报静默失败。
MIN_MAJOR=18

PLUGIN_ROOT="${CODEBUDDY_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
HANDLER_JS="$PLUGIN_ROOT/hooks/hook-handler.js"

# 第一个参数为事件名，默认 session-start
EVENT_TYPE="${1:-session-start}"

# ---- 读取 stdin，保存供后续转发 -------------------------------------------

RAW="$(cat 2>/dev/null || true)"

# ---- 辅助函数 -------------------------------------------------------------

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

# 找到可用 node 后，用它执行 hook-handler.js，将原始 stdin 透传进去
run_handler() {
  local node_bin="$1"
  if [ -f "$HANDLER_JS" ]; then
    printf '%s' "$RAW" | "$node_bin" "$HANDLER_JS" "$EVENT_TYPE" 2>/dev/null || true
  fi
  exit 0
}

# ---- 定位 WorkBuddy 自带 node（取 versions 下版本号最大的目录）-------------
#
# 目录形态：
#   macOS/Linux : ~/.workbuddy/binaries/node/versions/<ver>/bin/node
#   Windows/Git Bash: ~/.workbuddy/binaries/node/versions/<ver>/node.exe
# 多版本并存时按版本号降序取第一个 >= MIN_MAJOR 的；都不可用则放弃。
WORKBUDDY_NODE_ROOT="$HOME/.workbuddy/binaries/node/versions"
if [ -d "$WORKBUDDY_NODE_ROOT" ]; then
  # 列出 versions 下的目录名，按版本号降序排列
  while IFS= read -r VER_DIR; do
    [ -n "$VER_DIR" ] || continue
    # 优先 macOS/Linux 路径，再尝试 Windows 路径
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

echo "[ensure-node] no usable WorkBuddy Node found, skipping handler" >&2
exit 0
