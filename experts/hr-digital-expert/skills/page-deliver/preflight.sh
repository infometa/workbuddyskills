#!/usr/bin/env bash
# =============================================================================
# page-deliver preflight (macOS / Linux)
# =============================================================================
# 目的：保证有「同时可用」的 Node + npm（Node ≥ v18），
#       输出 NPM_BIN=... 与 NODE_BIN=... 两行供调用方 grep。
#
# 决策顺序（每一层都要求 node 与同目录下的 npm 同时可用）：
#   1) 系统 PATH 上 node ≥ v18  +  同目录 npm  → 直接用
#   1.5) ~/.workbuddy/binaries/node/ 下递归查找到的 node ≥ v18 + 同目录 npm  → 用
#   2) 缓存 ~/.page-deliver/bin/node-{darwin-arm64|darwin-x64|linux-x64}/bin/{node,npm} 已存在  → 用
#   3) 否则下载 Node v20.11.1 .tar.xz（官方包内置 npm）到缓存 + SHA256 校验
#
# PATH 持久化（仅 1.5 / 2 / 3 命中时）：
#   选中的 Node 所在目录会被写入用户 shell rc（zsh→~/.zshrc, bash→~/.bash_profile
#   或 ~/.bashrc）的 marker 块内，下次新开 shell 即可直接用 `node` / `npm`。
#   重复执行只会替换 marker 块，不会重复 append。Step 1 命中时不写（PATH 已有 node）。
#
# 退出码：
#   0 = 成功（最后两行：NPM_BIN=<path>、NODE_BIN=<path>，NODE_BIN 始终最后一行）
#   1 = 网络/下载失败
#   2 = SHA256 校验失败
#   3 = 解压失败 / 路径校验失败
#
# 用法：
#   bash preflight.sh
# 调用方拿 NODE_BIN（兼容旧契约）：
#   NODE_BIN=$(bash preflight.sh | tail -n 1 | sed 's/^NODE_BIN=//')
# 调用方拿 NPM_BIN：
#   NPM_BIN=$(bash preflight.sh | grep '^NPM_BIN=' | tail -n 1 | sed 's/^NPM_BIN=//')
# =============================================================================

set -euo pipefail

# ---- constants -------------------------------------------------------------
NODE_VERSION="v20.11.1"
MIN_MAJOR=18

OS_NAME="$(uname -s)"
ARCH="$(uname -m)"
case "${OS_NAME}/${ARCH}" in
  Darwin/arm64)  PLATFORM_ARCH="darwin-arm64" ;;
  Darwin/x86_64) PLATFORM_ARCH="darwin-x64" ;;
  Linux/x86_64)  PLATFORM_ARCH="linux-x64"   ;;
  Linux/aarch64) PLATFORM_ARCH="linux-arm64" ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "[preflight] detected Windows-style bash (${OS_NAME})" >&2
    echo "[preflight] please use preflight.ps1 on Windows instead" >&2
    exit 3
    ;;
  *)
    echo "[preflight] unsupported platform: ${OS_NAME}/${ARCH}" >&2
    exit 3
    ;;
esac

NODE_FILENAME="node-${NODE_VERSION}-${PLATFORM_ARCH}"
DOWNLOAD_URL="https://nodejs.org/dist/${NODE_VERSION}/${NODE_FILENAME}.tar.xz"
SHASUMS_URL="https://nodejs.org/dist/${NODE_VERSION}/SHASUMS256.txt"

CACHE_ROOT="$HOME/.page-deliver/bin"
CACHE_DIR="$CACHE_ROOT/node-${PLATFORM_ARCH}"
NODE_BIN="$CACHE_DIR/bin/node"

TMP_BASE="${TMPDIR:-/tmp}"
RAND="$(date +%s)$$"
TAR_PATH="$TMP_BASE/page-deliver-node-${NODE_VERSION}-${RAND}.tar.xz"
EXTRACT_TMP="$TMP_BASE/page-deliver-extract-${RAND}"

# ---- helpers ---------------------------------------------------------------

cleanup() {
  rm -f "$TAR_PATH" 2>/dev/null || true
  rm -rf "$EXTRACT_TMP" 2>/dev/null || true
}
trap cleanup EXIT

node_major() {
  # 输入 "v20.11.1" → 输出 20
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

# 给定一个 node 二进制，返回与之配套的 npm 路径（stdout）。找不到则返回非 0。
# Node 官方 tarball 里 npm 与 node 同放在 <prefix>/bin/ 下。
#
# 注意：npm 是个 shell 脚本，shebang 写的是 `#!/usr/bin/env node`，env 走 PATH 找 node。
# 如果用户 PATH 上没 node（典型场景：workbuddy 自己管理的 Node 不会污染 shell PATH），
# 直接 `"$candidate" --version` 会以 `env: node: No such file or directory` 失败，
# 导致这层 Node 被误判为不可用。所以探测时必须把 node 所在目录临时塞进 PATH。
find_npm_for_node() {
  local node_bin="$1"
  local node_dir
  node_dir="$(dirname "$node_bin")"
  local candidate="$node_dir/npm"
  if [ -x "$candidate" ]; then
    # 进一步验证 --version 能跑出来；某些包里 npm 是死链或缺依赖
    if PATH="$node_dir:$PATH" "$candidate" --version >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  fi
  return 1
}

# 把选中的 Node 所在目录写入用户 shell rc，让后续新开的 shell 自动 PATH 可见
# `node` / `npm`。用 marker 块包裹，重复执行只会替换块内容，不会重复 append。
#
# 参数：$1 = node_dir（不能为空）
# 行为：
#   - 选 rc 文件（按 $SHELL 优先选 zsh→.zshrc / bash→.bash_profile|.bashrc / 其他→输出 warn 不写）
#   - 不存在则创建（touch）
#   - 用 awk 删掉旧 marker 块，append 新 marker 块，原子 mv
#   - 失败一律仅 warn 到 stderr，不影响主流程退出码
persist_node_dir_to_rc() {
  local node_dir="$1"
  [ -n "$node_dir" ] || return 0
  [ -d "$node_dir" ] || return 0

  # 决定 rc 文件
  local user_shell rc_file
  user_shell="$(basename "${SHELL:-}")"
  case "$user_shell" in
    zsh)
      rc_file="$HOME/.zshrc"
      ;;
    bash)
      # macOS 登录 shell 读 .bash_profile，Linux 交互 shell 读 .bashrc
      if [ "$(uname -s)" = "Darwin" ]; then
        rc_file="$HOME/.bash_profile"
      else
        rc_file="$HOME/.bashrc"
      fi
      ;;
    *)
      echo "[preflight] unknown shell '$user_shell', skip rc persistence; you may need to add '$node_dir' to PATH manually" >&2
      return 0
      ;;
  esac

  # marker 必须独占两行，便于 awk 精确匹配
  local marker_begin="# >>> page-deliver node path >>>"
  local marker_end="# <<< page-deliver node path <<<"

  # 文件不存在则创建
  if [ ! -e "$rc_file" ]; then
    if ! : > "$rc_file" 2>/dev/null; then
      echo "[preflight] cannot create $rc_file, skip rc persistence" >&2
      return 0
    fi
  fi

  # 如果已经存在内容完全一致 *且* 格式正确的 marker 块，直接跳过
  # （避免无谓写盘 + mtime 抖动）。
  # 注意：必须显式校验 `*)` 那行格式正确 —— 历史版本在 bash 3.2 下踩过
  # heredoc-in-$()-bug，把 `*":...:"*) ;;` 写坏成 `*":...:"* ;;`，且尾部
  # 多出一行裸 `EOF`。这种损坏块如果只匹配 marker + export 行，会被误判
  # 为「已是最新」而永远不重写。所以必须把 case 那一行也算进指纹。
  if grep -qF "$marker_begin" "$rc_file" 2>/dev/null \
     && grep -qF "export PAGE_DELIVER_NODE_DIR=\"$node_dir\"" "$rc_file" 2>/dev/null \
     && grep -qF '*":$PAGE_DELIVER_NODE_DIR:"*) ;;' "$rc_file" 2>/dev/null; then
    return 0
  fi

  # awk 删掉旧 marker 块（如果有），写到 tmp，再 append 新块，最后原子 mv
  local tmp_rc
  tmp_rc="$(mktemp "${rc_file}.preflight.XXXXXX" 2>/dev/null)" || {
    echo "[preflight] cannot create tmp file next to $rc_file, skip rc persistence" >&2
    return 0
  }

  # awk 规则：
  #   1. 遇到 marker_begin，进入 skip 模式，丢弃直到 marker_end（含）
  #   2. 离开 marker_end 后，再额外清理紧跟其后的「历史 bash 3.2 bug 残骸」：
  #      具体是裸 `EOF` 行、`  )` 行、`  )"` 行 —— 这些是旧版脚本在 macOS
  #      bash 3.2 下被 heredoc-in-$() 解析 bug 注入到 rc 文件末尾的垃圾。
  #      最多吃掉连续 5 行以容错，遇到非垃圾行立即停止。
  awk -v B="$marker_begin" -v E="$marker_end" '
    BEGIN { skip = 0; mop = 0 }
    {
      if (skip) {
        if ($0 == E) { skip = 0; mop = 5 }
        next
      }
      if ($0 == B) { skip = 1; next }
      if (mop > 0) {
        mop--
        if ($0 == "EOF" || $0 == "  )" || $0 == "  )\"" || $0 == ")" || $0 == ")\"") next
        mop = 0
      }
      print
    }
  ' "$rc_file" > "$tmp_rc" || {
    rm -f "$tmp_rc"
    echo "[preflight] failed to rewrite $rc_file, skip rc persistence" >&2
    return 0
  }

  # 确保文件末尾有换行再 append（否则旧文件最后一行可能粘到 marker_begin）
  if [ -s "$tmp_rc" ]; then
    # 取最后一字节
    local last_byte
    last_byte="$(tail -c 1 "$tmp_rc" 2>/dev/null || true)"
    if [ "$last_byte" != "" ] && [ "$last_byte" != $'\n' ]; then
      printf '\n' >> "$tmp_rc"
    fi
  fi

  # 把新 block 直接 append 到 tmp_rc。
  #
  # 注意：不能用 `new_block="$(cat <<EOF ... EOF)"` 这种「heredoc 套在 $(...) 命令
  # 替换里」的写法 —— macOS 系统自带的 bash 3.2 在解析阶段会把 heredoc 内容里
  # 出现的 `)` 误当成命令替换的关闭括号，从而吃掉脚本里的 `*)` 并把 `EOF` 直接
  # 写进 .zshrc，造成语法损坏。详见 bash bug：
  #   https://lists.gnu.org/archive/html/bug-bash/2010-04/msg00073.html
  # 直接 heredoc 到文件没有这个限制。
  cat >> "$tmp_rc" <<EOF
$marker_begin
# Managed by page-deliver preflight. Do not edit between markers.
# To remove: delete this entire block (between the two marker lines).
export PAGE_DELIVER_NODE_DIR="$node_dir"
case ":\$PATH:" in
  *":\$PAGE_DELIVER_NODE_DIR:"*) ;;
  *) export PATH="\$PAGE_DELIVER_NODE_DIR:\$PATH" ;;
esac
$marker_end
EOF

  if ! mv "$tmp_rc" "$rc_file"; then
    rm -f "$tmp_rc"
    echo "[preflight] failed to atomically replace $rc_file, skip rc persistence" >&2
    return 0
  fi

  echo "[preflight] persisted Node path to $rc_file (open a new shell to take effect)"
}

# ---- step 1: system Node ---------------------------------------------------

if command -v node >/dev/null 2>&1; then
  SYS_NODE="$(command -v node)"
  SYS_VER="$("$SYS_NODE" --version 2>/dev/null || echo unknown)"
  if test_node_bin "$SYS_NODE"; then
    # 优先用与 node 同目录的 npm；找不到再回退到 PATH 上的 npm
    SYS_NPM="$(find_npm_for_node "$SYS_NODE" 2>/dev/null || true)"
    if [ -z "$SYS_NPM" ] && command -v npm >/dev/null 2>&1; then
      CAND="$(command -v npm)"
      if "$CAND" --version >/dev/null 2>&1; then
        SYS_NPM="$CAND"
      fi
    fi
    if [ -n "$SYS_NPM" ]; then
      NPM_VER="$("$SYS_NPM" --version 2>/dev/null || echo unknown)"
      echo "[preflight] using system Node: $SYS_NODE ($SYS_VER) + npm: $SYS_NPM ($NPM_VER)"
      echo "NPM_BIN=$SYS_NPM"
      echo "NODE_BIN=$SYS_NODE"
      exit 0
    fi
    echo "[preflight] system Node $SYS_VER OK but npm not found, falling back to managed"
  else
    echo "[preflight] system Node $SYS_VER < v$MIN_MAJOR, falling back to managed"
  fi
fi

# ---- step 1.5: workbuddy Node ----------------------------------------------
# workbuddy 在 ~/.workbuddy/binaries/node 下安装 Node，但内部布局不固定，
# 见过的形式包括：
#   versions/<ver>/bin/node
#   versions/<ver>.installing.<n>.__extract_temp__/node-v<ver>-<arch>/bin/node
# 因此采用有限深度的递归查找，命中第一个可用的 node 即用。

WORKBUDDY_NODE_ROOT="$HOME/.workbuddy/binaries/node"

if [ -d "$WORKBUDDY_NODE_ROOT" ]; then
  # -maxdepth 5 足以覆盖 node/versions/<dir>/<inner>/bin/node 这类布局
  # 限制最多检查 20 个能启动的 node。
  while IFS= read -r WORKBUDDY_NODE; do
    [ -n "$WORKBUDDY_NODE" ] || continue
    if ! test_node_bin "$WORKBUDDY_NODE"; then continue; fi
    # 必须找到同目录下的 npm 才算这一层通过；否则继续找下一个 node
    WB_NPM="$(find_npm_for_node "$WORKBUDDY_NODE" 2>/dev/null || true)"
    if [ -z "$WB_NPM" ]; then
      echo "[preflight] workbuddy Node $WORKBUDDY_NODE has no usable npm sibling, skipping"
      continue
    fi
    WB_VER="$("$WORKBUDDY_NODE" --version)"
    NPM_VER="$(PATH="$(dirname "$WORKBUDDY_NODE"):$PATH" "$WB_NPM" --version 2>/dev/null || echo unknown)"
    echo "[preflight] using workbuddy Node: $WORKBUDDY_NODE ($WB_VER) + npm: $WB_NPM ($NPM_VER)"
    persist_node_dir_to_rc "$(dirname "$WORKBUDDY_NODE")"
    echo "NPM_BIN=$WB_NPM"
    echo "NODE_BIN=$WORKBUDDY_NODE"
    exit 0
  done < <(find "$WORKBUDDY_NODE_ROOT" -maxdepth 5 -type f -name node -perm -u+x 2>/dev/null | head -n 20)
fi

# ---- step 2: cached managed Node ------------------------------------------

if test_node_bin "$NODE_BIN"; then
  CACHED_NPM="$(find_npm_for_node "$NODE_BIN" 2>/dev/null || true)"
  if [ -n "$CACHED_NPM" ]; then
    CACHED_VER="$("$NODE_BIN" --version)"
    NPM_VER="$(PATH="$(dirname "$NODE_BIN"):$PATH" "$CACHED_NPM" --version 2>/dev/null || echo unknown)"
    echo "[preflight] using cached Node: $NODE_BIN ($CACHED_VER) + npm: $CACHED_NPM ($NPM_VER)"
    persist_node_dir_to_rc "$(dirname "$NODE_BIN")"
    echo "NPM_BIN=$CACHED_NPM"
    echo "NODE_BIN=$NODE_BIN"
    exit 0
  fi
  echo "[preflight] cached Node found at $NODE_BIN but npm sibling missing, will re-download"
fi

# ---- step 3: download + verify + extract ----------------------------------

echo "[preflight] no usable Node found, downloading $NODE_VERSION ..."
mkdir -p "$CACHE_ROOT"

# Download
echo "[preflight] GET $DOWNLOAD_URL"
START=$(date +%s)
if ! curl -fsSL --proto '=https' --tlsv1.2 -o "$TAR_PATH" "$DOWNLOAD_URL"; then
  echo "[preflight] download failed" >&2
  exit 1
fi
ELAPSED=$(($(date +%s) - START))
SIZE=$(du -h "$TAR_PATH" 2>/dev/null | cut -f1 || echo "?")
echo "[preflight] downloaded $SIZE in ${ELAPSED}s"

# SHA256 verify
echo "[preflight] verifying SHA256 ..."
SHASUMS="$(curl -fsSL --proto '=https' --tlsv1.2 "$SHASUMS_URL" 2>/dev/null || true)"
if [ -z "$SHASUMS" ]; then
  echo "[preflight] cannot fetch SHASUMS256.txt" >&2
  exit 2
fi
EXPECTED="$(echo "$SHASUMS" | awk -v f="${NODE_FILENAME}.tar.xz" '$2 == f {print $1; exit}')"
if [ -z "$EXPECTED" ]; then
  echo "[preflight] cannot find ${NODE_FILENAME}.tar.xz in SHASUMS256.txt" >&2
  exit 2
fi

if command -v shasum >/dev/null 2>&1; then
  ACTUAL="$(shasum -a 256 "$TAR_PATH" | awk '{print $1}')"
elif command -v sha256sum >/dev/null 2>&1; then
  ACTUAL="$(sha256sum "$TAR_PATH" | awk '{print $1}')"
else
  echo "[preflight] no shasum/sha256sum tool available" >&2
  exit 2
fi

if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "[preflight] SHA256 mismatch: expected=$EXPECTED actual=$ACTUAL" >&2
  exit 2
fi
echo "[preflight] SHA256 OK"

# Extract
echo "[preflight] extracting ..."
mkdir -p "$EXTRACT_TMP"
if ! tar -xJf "$TAR_PATH" -C "$EXTRACT_TMP"; then
  echo "[preflight] extract failed" >&2
  exit 3
fi

# tar.xz 内目录形如 node-v20.11.1-darwin-arm64/
INNER="$(ls -d "$EXTRACT_TMP"/*/ 2>/dev/null | head -n 1)"
if [ -z "$INNER" ] || [ ! -d "$INNER" ]; then
  echo "[preflight] tar layout unexpected" >&2
  exit 3
fi
INNER="${INNER%/}"

CACHE_NEW="${CACHE_DIR}.new"
rm -rf "$CACHE_NEW"
mv "$INNER" "$CACHE_NEW"

# 验证产物可执行
NEW_NODE="$CACHE_NEW/bin/node"
if ! test_node_bin "$NEW_NODE"; then
  rm -rf "$CACHE_NEW"
  echo "[preflight] extracted node failed self-check" >&2
  exit 3
fi
# 官方 tarball 必带 npm，缺了就是包损坏
NEW_NPM="$(find_npm_for_node "$NEW_NODE" 2>/dev/null || true)"
if [ -z "$NEW_NPM" ]; then
  rm -rf "$CACHE_NEW"
  echo "[preflight] extracted package missing npm at $CACHE_NEW/bin/npm" >&2
  exit 3
fi

# 原子替换旧缓存（如有）
rm -rf "$CACHE_DIR"
mv "$CACHE_NEW" "$CACHE_DIR"

NPM_BIN="$CACHE_DIR/bin/npm"
VER="$("$NODE_BIN" --version)"
NPM_VER="$(PATH="$CACHE_DIR/bin:$PATH" "$NPM_BIN" --version 2>/dev/null || echo unknown)"
echo "[preflight] managed Node ready: $NODE_BIN ($VER) + npm: $NPM_BIN ($NPM_VER)"
persist_node_dir_to_rc "$CACHE_DIR/bin"
echo "NPM_BIN=$NPM_BIN"
echo "NODE_BIN=$NODE_BIN"
exit 0
