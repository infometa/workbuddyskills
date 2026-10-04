#!/usr/bin/env bash
set -uo pipefail

BIN_NAME="westock"

# CLI 官方发布源（默认下载基址，形如 https://<host>/release/<channel>/cli）。
# 占位符未被替换时（本地直接运行源码）视为空，回退到脚本所在目录。
CLI_BASE_DEFAULT="https://stockbuddy.qq.com/release/workbuddy/cli"

# 发布时注入的「SHA256.txt 清单文件」自身哈希（信任根，独立于 CDN）。
# 校验链：脚本内固定哈希 → 校验 SHA256.txt 未被篡改 → SHA256.txt 校验二进制。
# 占位符未被替换（本地源码运行）时为空，退回仅校验二进制（兼容本地开发）。
PINNED_MANIFEST_SHA256="f2b3fc21beddb82604c3c8e355e6201de9bb281fcf340758c5aaccf01a7b6724"

# 发布时注入的「发布版本 tag」（与该版本 SHA256.txt 信任根配套）。
# 安装时优先用它确定版本（而非 CDN 上的 latest.txt），保证清单哈希信任根
# 始终对应该版本，不被后续发版破坏；追新交给 CLI 运行时自检升级。
# 占位符未被替换（本地源码运行）时为空，退回读 latest.txt / 本地枚举。
PINNED_VERSION="v0.0.4"

# 解析脚本所在目录（管道模式 BASH_SOURCE 为空，需判空兜底，避免 set -u 报错）
SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
fi

# ---- 默认值 ----
BASE_ARG=""
INSTALL_DIR="${WESTOCK_INSTALL_DIR:-${HOME}/.local/bin}"
VERSION=""
DRY_RUN=0
ASSUME_YES=0

# 颜色（非 TTY 时关闭）
if [[ -t 1 ]]; then
  C_GREEN=$'\033[0;32m'
  C_YELLOW=$'\033[0;33m'
  C_RED=$'\033[0;31m'
  C_RESET=$'\033[0m'
else
  C_GREEN=""; C_YELLOW=""; C_RED=""; C_RESET=""
fi

log()  { printf '%s%s%s\n' "$C_GREEN"  "$*" "$C_RESET"; }
warn() { printf '%s%s%s\n' "$C_YELLOW" "$*" "$C_RESET" >&2; }
err()  { printf '%s%s%s\n' "$C_RED"    "$*" "$C_RESET" >&2; }

# ---- 下载工具（定义提前，供版本解析与二进制下载共用） ----
download_file() {
  local url="$1" out="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$out"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$out" "$url"
  else
    err "需要 curl 或 wget 才能下载安装包"; return 1
  fi
}

# ---- 本地版本枚举（本地模式缺 latest.txt 时的通用兜底）----
# 返回 $1 目录下语义化版本最大的 vX.Y.Z 目录名（无则空）
latest_local_tag() {
  local dir="$1" best='' tag
  [[ -d "$dir" ]] || return 0
  for entry in "$dir"/v*; do
    [[ -d "$entry" ]] || continue
    tag="$(basename "$entry")"
    if [[ -z "$best" ]] || version_gt "$tag" "$best"; then
      best="$tag"
    fi
  done
  printf '%s' "$best"
}

# 语义化版本比较：$1 > $2 返回 0，否则 1（忽略前缀 v 与预发布后缀）
version_gt() {
  local a="${1#v}" b="${2#v}" IFS='.'
  local a1 a2 a3 b1 b2 b3
  read -r a1 a2 a3 <<< "$a"
  read -r b1 b2 b3 <<< "$b"
  a1="${a1%%[-+]*}"; a2="${a2%%[-+]*}"; a3="${a3%%[-+]*}"
  a1="${a1:-0}"; a2="${a2:-0}"; a3="${a3:-0}"
  b1="${b1:-0}"; b2="${b2:-0}"; b3="${b3:-0}"
  (( 10#$a1 > 10#$b1 )) && return 0
  (( 10#$a1 < 10#$b1 )) && return 1
  (( 10#$a2 > 10#$b2 )) && return 0
  (( 10#$a2 < 10#$b2 )) && return 1
  (( 10#$a3 > 10#$b3 )) && return 0
  return 1
}

usage() {
  cat <<'EOF'
westock 安装脚本（Mac / Linux，随技能包提供）

用法:
  ./setup.sh                           # 本地安装到 ~/.local/bin
  ./setup.sh -d /usr/local/bin -v v1.2.3
  ./setup.sh --help

参数（全部可选）:
  -b, --base URL     远程发布基址 (默认: 官方发布源，或脚本所在目录)
  -d, --bindir DIR   安装目录 (默认 ~/.local/bin 或 WESTOCK_INSTALL_DIR)
  -v, --version VER  指定版本 (默认 latest.txt)
  -n, --dry-run      只打印不执行
  -y, --yes          跳过确认
  -h, --help         显示帮助
EOF
}

# ---- 参数解析 ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--base)     BASE_ARG="$2"; shift 2 ;;
    -d|--bindir)   INSTALL_DIR="$2"; shift 2 ;;
    -v|--version)  VERSION="$2"; shift 2 ;;
    -n|--dry-run)  DRY_RUN=1; shift ;;
    -y|--yes)      ASSUME_YES=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *) err "未知参数: $1"; usage; exit 1 ;;
  esac
done

# ---- 解析发布基址 BASE ----
# 优先级: -b/--base > 注入的 CDN 基址（管道模式）> 脚本所在目录（本地模式）
if [[ -n "$BASE_ARG" ]]; then
  BASE="$BASE_ARG"
elif [[ "$CLI_BASE_DEFAULT" == http* ]]; then
  BASE="$CLI_BASE_DEFAULT"
elif [[ -n "$SCRIPT_DIR" ]]; then
  BASE="$SCRIPT_DIR"
else
  err "无法确定发布基址，请用 -b 指定远程基址"; exit 1
fi

IS_REMOTE=0
[[ "$BASE" == http://* || "$BASE" == https://* ]] && IS_REMOTE=1

# 是否配置了 pinned 信任根（占位符已被发布流程替换为真实哈希）。
# 哨兵用拼接构造，避免发布期字符串替换把这里的比较基准也一并替换。
has_pinned() {
  local sentinel="__PINNED_""MANIFEST_SHA256__"
  [[ -n "$PINNED_MANIFEST_SHA256" && "$PINNED_MANIFEST_SHA256" != "$sentinel" ]]
}

# 是否注入了固定发布版本（占位符已被发布流程替换为真实 tag）。
has_pinned_version() {
  local sentinel="__PINNED_""VERSION__"
  [[ -n "$PINNED_VERSION" && "$PINNED_VERSION" != "$sentinel" ]]
}

# ---- 版本解析 ----
# 发布产物注入了固定版本时优先使用，避免读 CDN 的 latest.txt 导致旧包指向新版本、
# 与包内固定的 SHA256.txt 清单信任根失配（版本 tag 由构建期注入）。
if [[ -z "$VERSION" ]]; then
  if has_pinned_version; then
    VERSION="$PINNED_VERSION"
  elif [[ "$IS_REMOTE" -eq 1 ]]; then
    tmp="$(mktemp)"
    if ! download_file "$BASE/latest.txt" "$tmp"; then
      err "无法获取 latest.txt: $BASE/latest.txt"; exit 1
    fi
    VERSION="$(tr -d '[:space:]' < "$tmp")"
    rm -f "$tmp"
  elif [[ -f "$BASE/latest.txt" ]]; then
    VERSION="$(tr -d '[:space:]' < "$BASE/latest.txt")"
  else
    # 本地模式（缺 latest.txt）：枚举 scripts/ 下 v* 目录取最新 tag 作为兜底
    VERSION="$(latest_local_tag "$BASE")"
    if [[ -z "$VERSION" ]]; then
      err "未找到 latest.txt，且 scripts/ 下无可用 v* 版本目录，请用 -v 指定版本"; exit 1
    fi
  fi
fi
[[ "$VERSION" != v* ]] && VERSION="v${VERSION#v}"

# ---- 平台检测 ----
detect_platform() {
  local os arch
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *) err "不支持的架构: $arch"; exit 1 ;;
  esac
  case "$os" in
    darwin) os="darwin" ;;
    linux) os="linux" ;;
    *) err "不支持的操作系统: $os（Windows 请用 setup.ps1）"; exit 1 ;;
  esac
  PLATFORM_OS="$os"
  PLATFORM_ARCH="$arch"
}
detect_platform
ARTIFACT="westock-${PLATFORM_OS}-${PLATFORM_ARCH}"

# ---- 准备二进制到 TMP_BIN（远程下载 / 本地拷贝） ----
TMP_BIN="$(mktemp)"
if [[ "$IS_REMOTE" -eq 1 ]]; then
  SRC="$BASE/$VERSION/$ARTIFACT"
  if ! download_file "$SRC" "$TMP_BIN"; then
    err "下载失败: $SRC"; exit 1
  fi
else
  SRC="$BASE/$VERSION/$ARTIFACT"
  if [[ ! -f "$SRC" ]]; then
    err "找不到二进制: $SRC"; exit 1
  fi
  cp "$SRC" "$TMP_BIN"
fi
chmod +x "$TMP_BIN"

# ---- 校验 SHA256 ----
# 计算文件 sha256（小写十六进制），无可用工具时返回空串。
sha256_of() {
  local f="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  else
    printf ''
  fi
}

verify_checksum() {
  local checksum_file expected actual tmpc
  if [[ "$IS_REMOTE" -eq 1 ]]; then
    tmpc="$(mktemp)"
    if ! download_file "$BASE/$VERSION/SHA256.txt" "$tmpc"; then
      if has_pinned; then
        err "无法下载 SHA256.txt，且已配置固定校验值，拒绝安装"; rm -f "$tmpc"; exit 1
      fi
      warn "未找到 SHA256.txt，跳过校验"; rm -f "$tmpc"; return 0
    fi
    checksum_file="$tmpc"
  else
    checksum_file="$BASE/$VERSION/SHA256.txt"
    if [[ ! -f "$checksum_file" ]]; then
      if has_pinned; then
        err "未找到 SHA256.txt，且已配置固定校验值，拒绝安装"; exit 1
      fi
      warn "未找到 SHA256.txt，跳过校验"; return 0
    fi
  fi

  # 信任根校验：先确认 SHA256.txt 清单本身未被篡改（独立于 CDN 的固定哈希）。
  if has_pinned; then
    local manifest_actual
    manifest_actual="$(sha256_of "$checksum_file")"
    if [[ -z "$manifest_actual" ]]; then
      err "无 shasum/sha256sum 工具，无法校验清单完整性，拒绝安装"
      [[ "$IS_REMOTE" -eq 1 ]] && rm -f "$checksum_file"
      exit 1
    fi
    if [[ "$(printf '%s' "$manifest_actual" | tr 'A-Z' 'a-z')" != "$(printf '%s' "$PINNED_MANIFEST_SHA256" | tr 'A-Z' 'a-z')" ]]; then
      err "SHA256.txt 清单校验失败（疑似 CDN 被篡改），拒绝安装"
      err "  期望: $PINNED_MANIFEST_SHA256"
      err "  实际: $manifest_actual"
      [[ "$IS_REMOTE" -eq 1 ]] && rm -f "$checksum_file"
      exit 1
    fi
  fi

  expected="$(awk -v art="$ARTIFACT" '$2 == art { print $1; exit }' "$checksum_file")"
  if [[ -z "$expected" ]]; then
    err "SHA256.txt 中未找到 $ARTIFACT"; exit 1
  fi
  actual="$(sha256_of "$TMP_BIN")"
  if [[ -z "$actual" ]]; then
    if has_pinned; then
      err "无 shasum/sha256sum 工具，无法校验二进制，拒绝安装"; exit 1
    fi
    warn "无 shasum/sha256sum，跳过校验"; return 0
  fi
  if [[ "$actual" != "$expected" ]]; then
    err "SHA256 校验失败: $ARTIFACT"
    err "  期望: $expected"
    err "  实际: $actual"
    exit 1
  fi
  [[ "$IS_REMOTE" -eq 1 ]] && rm -f "$checksum_file"
}
verify_checksum

DEST="$INSTALL_DIR/$BIN_NAME"

# ---- 预览 ----
log "将安装: $BIN_NAME $VERSION"
log "  源: $SRC"
log "  目标: $DEST"
if [[ "$DRY_RUN" -eq 1 ]]; then
  rm -f "$TMP_BIN"
  log "(dry-run) 未做任何改动"; exit 0
fi

# ---- 安装（默认自动，无需确认；-n 仅预览） ----
mkdir -p "$INSTALL_DIR"
mv "$TMP_BIN" "$DEST"
log "✅ 已安装 → $DEST"

# ---- PATH / shell profile ----
if echo ":$PATH:" | grep -q ":$INSTALL_DIR:"; then
  log "PATH 已包含 $INSTALL_DIR"
else
  PROFILE=""
  case "$(basename "${SHELL:-}")" in
    zsh)  PROFILE="${ZDOTDIR:-$HOME}/.zshrc" ;;
    bash) PROFILE="$HOME/.bashrc" ;;
    *)    PROFILE="$HOME/.profile" ;;
  esac
  LINE="export PATH=\"$INSTALL_DIR:\$PATH\""
  # 注意: bash 3.2 的 set -u 对 case 内赋值的变量在函数参数中展开会误报 unbound，
  # 统一用 ${PROFILE:-} 兜底避免误报（PROFILE 恒已被赋值，等价）。
  if [[ -n "${PROFILE:-}" ]] && ! grep -qF "$INSTALL_DIR" "$PROFILE" 2>/dev/null; then
    printf '\n# westock\n%s\n' "$LINE" >> "$PROFILE"
    log "已写入 PATH 到 ${PROFILE:-}，执行: source ${PROFILE:-}"
  else
    warn "请将 $INSTALL_DIR 加入 PATH:"
    warn "  $LINE"
  fi
fi
