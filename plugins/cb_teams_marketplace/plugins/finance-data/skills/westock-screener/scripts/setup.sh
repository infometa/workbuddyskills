#!/usr/bin/env bash
set -uo pipefail

BIN_NAME="westock"

CLI_BASE_DEFAULT="https://stockbuddy.gtimg.com/release/workbuddy/cli"

# 「SHA256.txt 清单文件」自身的预期哈希，作为独立于发布源的信任根。
PINNED_MANIFEST_SHA256="31c98307558da497b2077a796aebf6ae6864e75b7b38f173897c60a9bb35affd"

# 本包对应的发布版本 tag（与该版本 SHA256.txt 信任根配套）。
PINNED_VERSION="v0.0.2"

CHANNEL="workbuddy"

WESTOCK_ROOT="${WESTOCK_HOME:-${HOME}/.westock}"

CHANNEL_DIR="${WESTOCK_CHANNEL_DIR:-${WESTOCK_ROOT}/channels/${CHANNEL}/bin}"

NO_SWITCH="${WESTOCK_NO_SWITCH:-0}"
DO_SWITCH="${WESTOCK_SWITCH:-0}"
FORCE="${WESTOCK_FORCE:-0}"

SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
fi

BASE_ARG="${WESTOCK_BASE:-}"
INSTALL_DIR="${WESTOCK_INSTALL_DIR:-${HOME}/.local/bin}"
VERSION="${WESTOCK_VERSION:-}"
DRY_RUN=0
# 注意：该开关只放宽下载来源，不影响 SHA256 校验（校验始终强制）。
ALLOW_UNOFFICIAL_BASE="${WESTOCK_ALLOW_UNOFFICIAL_BASE:-0}"
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

lower() { printf '%s' "$1" | tr 'A-Z' 'a-z'; }

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

用法（agent 直接零参数执行即可）:
  ./setup.sh                           # 安装到 ~/.local/bin
  ./setup.sh -n                        # 预演：只打印计划，不下载、不落盘
  ./setup.sh --help

参数（全部可选）:
  -n, --dry-run        只打印计划，不下载、不落盘
  -h, --help           显示帮助

环境变量（供部署方 / 平台注入，agent 无需设置）:
  WESTOCK_BASE                    发布基址（默认官方发布源，其次脚本所在目录）
  WESTOCK_ALLOW_UNOFFICIAL_BASE   允许 WESTOCK_BASE 指向非官方域名（危险；SHA256 仍强制）
  WESTOCK_VERSION                 指定版本（默认包内固定版本，其次 latest.txt）
  WESTOCK_INSTALL_DIR             安装目录（默认 ~/.local/bin）
  WESTOCK_HOME                    数据根目录（默认 ~/.westock）
  WESTOCK_CHANNEL_DIR             覆盖实际文件的落盘目录
  WESTOCK_SWITCH                  设为默认入口
  WESTOCK_NO_SWITCH               绝不改动入口（含首次安装）
  WESTOCK_FORCE                   忽略「已安装」判断，强制重新下载

固定约束（无开关可绕过）:
  * SHA256 校验强制执行：清单拿不到、无哈希工具、条目缺失 / 重复 / 畸形、哈希不匹配，
    一律拒绝安装，不存在跳过校验的选项。
  * 二进制只从本脚本认定的官方发布源下载，其它域名一律拒绝
    （需 WESTOCK_ALLOW_UNOFFICIAL_BASE=1 才放行，且校验照旧强制）。
  * 只把二进制写入安装目录，不修改 shell 配置、PATH 或任何环境变量。
    安装目录不在 PATH 中时，直接用绝对路径调用即可。
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run)  DRY_RUN=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *) err "未知参数: $1（本脚本零参数执行；可调项见 --help 中的环境变量表）"; usage; exit 1 ;;
  esac
done

if [[ -n "$BASE_ARG" ]]; then
  BASE="$BASE_ARG"
elif [[ "$CLI_BASE_DEFAULT" == http* ]]; then
  BASE="$CLI_BASE_DEFAULT"
elif [[ -n "$SCRIPT_DIR" ]]; then
  BASE="$SCRIPT_DIR"
else
  err "无法确定发布基址，请设置 WESTOCK_BASE"; exit 1
fi

IS_REMOTE=0
[[ "$BASE" == http://* || "$BASE" == https://* ]] && IS_REMOTE=1

host_of() { printf '%s' "${1#*://}" | cut -d/ -f1; }
if [[ "$IS_REMOTE" -eq 1 && "$CLI_BASE_DEFAULT" == http* ]]; then
  OFFICIAL_HOST="$(host_of "$CLI_BASE_DEFAULT")"
  BASE_HOST="$(host_of "$BASE")"
  if [[ -n "$OFFICIAL_HOST" && "$BASE_HOST" != "$OFFICIAL_HOST" ]]; then
    if [[ "$ALLOW_UNOFFICIAL_BASE" -eq 0 ]]; then
      err "拒绝从非官方域名下载: ${BASE_HOST}（官方发布源: ${OFFICIAL_HOST}）"
      err "确需自建源请设置 WESTOCK_ALLOW_UNOFFICIAL_BASE=1"
      exit 1
    fi
    warn "正在使用非官方基址 ${BASE_HOST}（WESTOCK_ALLOW_UNOFFICIAL_BASE）；SHA256 校验仍会强制执行"
  fi
fi

# 是否已配置 pinned 信任根（值为真实哈希而非未填形态）。
has_pinned() {
  local sentinel="__PINNED_""MANIFEST_SHA256__"
  [[ -n "$PINNED_MANIFEST_SHA256" && "$PINNED_MANIFEST_SHA256" != "$sentinel" ]]
}

has_pinned_version() {
  local sentinel="__PINNED_""VERSION__"
  [[ -n "$PINNED_VERSION" && "$PINNED_VERSION" != "$sentinel" ]]
}

# 有固定版本时优先使用，避免与包内固定的清单校验值失配。
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
    VERSION="$(latest_local_tag "$BASE")"
    if [[ -z "$VERSION" ]]; then
      err "未找到 latest.txt，且 scripts/ 下无可用 v* 版本目录，请用 -v 指定版本"; exit 1
    fi
  fi
fi
[[ "$VERSION" != v* ]] && VERSION="v${VERSION#v}"

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
    *) err "不支持的操作系统: ${os}（Windows 请用 setup.ps1）"; exit 1 ;;
  esac
  PLATFORM_OS="$os"
  PLATFORM_ARCH="$arch"
}
detect_platform
ARTIFACT="westock-${PLATFORM_OS}-${PLATFORM_ARCH}"

has_channel() {
  local sentinel="__""CHANNEL__"
  [[ -n "$CHANNEL" && "$CHANNEL" != "$sentinel" ]]
}

bin_version() {
  local bin="$1" out
  [[ -x "$bin" ]] || return 1
  out="$(WESTOCK_NO_AUTO_UPGRADE=1 "$bin" version --json 2>/dev/null)" || return 1
  printf '%s' "$out" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p'
}

# 提示如何调用（本脚本不改 PATH / shell 配置）。
path_hint() {
  if echo ":$PATH:" | grep -q ":$INSTALL_DIR:"; then
    log "PATH 已包含 ${INSTALL_DIR}，可直接用 $BIN_NAME 调用"
  else
    log "$INSTALL_DIR 不在 PATH 中（本脚本不修改 shell 配置与 PATH）"
    log "  请用绝对路径调用: $DEST <子命令>"
  fi
}

SRC="$BASE/$VERSION/$ARTIFACT"
DEST="$INSTALL_DIR/$BIN_NAME"
if has_channel; then
  REAL_BIN="$CHANNEL_DIR/$BIN_NAME"
else
  REAL_BIN="$DEST"
fi

log "将安装: $BIN_NAME $VERSION"
log "  源: $SRC"
if has_channel; then
  log "  落盘: $REAL_BIN"
  log "  入口: $DEST"
  [[ "$NO_SWITCH" -eq 1 ]] && log "  WESTOCK_NO_SWITCH=1: 不改动入口"
  [[ "$DO_SWITCH" -eq 1 ]] && log "  WESTOCK_SWITCH=1: 设为入口"
else
  log "  目标: $DEST"
fi
log "  shell 配置 / PATH: 不修改"
if [[ "$DRY_RUN" -eq 1 ]]; then
  log "(dry-run) 未做任何改动"; exit 0
fi

# 用给定的二进制执行自行安装（既能用刚下载的临时文件，也能用已装的副本）
run_install_self() {
  local bin="$1" out rc
  # 未注入标识（旧包）时不具备自行安装所需的参数，直接走回退
  has_channel || return 1
  local args=(install-self --channel "$CHANNEL" --bindir "$INSTALL_DIR" --version "$VERSION")
  [[ "$DO_SWITCH" -eq 1 ]] && args+=(--switch)
  [[ "$NO_SWITCH" -eq 1 ]] && args+=(--no-switch)
  [[ "$FORCE" -eq 1 ]] && args+=(--force)
  [[ "$DRY_RUN" -eq 1 ]] && args+=(--dry-run)
  out="$("$bin" "${args[@]}" 2>&1)"; rc=$?
  if [[ $rc -eq 0 ]]; then
    printf '%s\n' "$out" | while IFS= read -r line; do log "  $line"; done
    log "✅ 安装由程序自身完成"
    return 0
  fi
  if [[ "$out" == *"unknown command"* || "$out" == *"unknown flag"* ]]; then
    log "   当前产物不支持自行安装，回退到脚本直接写入"
  else
    log "   CLI 安装未成功（rc=${rc}），回退到脚本内置安装逻辑"
    fi
  return 1
}
# 用本次下载的临时文件执行自行安装
try_install_self() {
  has_channel || return 1
  [[ -n "${TMP_BIN:-}" && -f "$TMP_BIN" ]] || return 1
  chmod 755 "$TMP_BIN" 2>/dev/null
  if run_install_self "$TMP_BIN"; then
    TMP_BIN=""   # CLI 已自行落盘，避免 EXIT trap 误删
    return 0
  fi
  return 1
}

if has_channel && [[ "$FORCE" -eq 0 && -x "$REAL_BIN" ]]; then
  installed_ver="$(bin_version "$REAL_BIN")"
  if [[ -n "$installed_ver" ]] && ! version_gt "$VERSION" "$installed_ver"; then
    log "   已安装 ${installed_ver}（不低于 ${VERSION}），跳过下载"
    # 已装副本本身就是可用的 CLI：用它完成入口决策（此时没有下载 TMP_BIN）
# 落盘与入口设置由程序自身完成；脚本只负责下载与校验。

    run_install_self "$REAL_BIN" || log "✅ 已安装 → $REAL_BIN"
    path_hint
    exit 0
  fi
fi

TMP_BIN="$(mktemp)"
TMP_MANIFEST=""
cleanup() {
  [[ -n "${TMP_BIN:-}" ]] && rm -f "$TMP_BIN"
  [[ -n "${TMP_MANIFEST:-}" ]] && rm -f "$TMP_MANIFEST"
  return 0
}
trap cleanup EXIT

if [[ "$IS_REMOTE" -eq 1 ]]; then
  if ! download_file "$SRC" "$TMP_BIN"; then
    err "下载失败: $SRC"; exit 1
  fi
else
  if [[ ! -f "$SRC" ]]; then
    err "找不到二进制: $SRC"; exit 1
  fi
  cp "$SRC" "$TMP_BIN"
fi

# ---- 校验 SHA256 ----
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
  local checksum_file expected actual manifest_actual count

  # SHA256 校验对任何包无条件强制，不存在跳过分支。
  if [[ "$IS_REMOTE" -eq 1 ]]; then
    TMP_MANIFEST="$(mktemp)"
    if ! download_file "$BASE/$VERSION/SHA256.txt" "$TMP_MANIFEST"; then
      err "无法获取校验清单 $BASE/$VERSION/SHA256.txt，拒绝安装"
      exit 1
    fi
    checksum_file="$TMP_MANIFEST"
  else
    checksum_file="$BASE/$VERSION/SHA256.txt"
    if [[ ! -f "$checksum_file" ]]; then
      err "未找到校验清单 ${checksum_file}，拒绝安装"
      exit 1
    fi
  fi

  manifest_actual="$(lower "$(sha256_of "$checksum_file")")"
  if [[ -z "$manifest_actual" ]]; then
    err "缺少 shasum/sha256sum，无法校验完整性，拒绝安装"
    exit 1
  fi

  # 信任根校验：用固定哈希确认清单本身未被篡改（独立于发布源）。
  if has_pinned && [[ "$manifest_actual" != "$(lower "$PINNED_MANIFEST_SHA256")" ]]; then
    err "SHA256.txt 清单校验失败（疑似发布源被篡改），拒绝安装"
    err "  期望: $PINNED_MANIFEST_SHA256"
    err "  实际: $manifest_actual"
    exit 1
  fi

  # 取出目标平台在 SHA256.txt 中的哈希条目
  local expected="" h f cnt=0
  while read -r h f _; do
    [[ "$f" == "$ARTIFACT" ]] || continue
    [[ "$h" == *[!0-9a-fA-F]* ]] && continue
    [[ ${#h} -eq 64 ]] || continue
    cnt=$((cnt + 1))
    expected="$h"
  done < "$checksum_file"
  if [[ "$cnt" -eq 0 ]]; then
    err "SHA256.txt 中未找到 $ARTIFACT 的合法校验条目，拒绝安装"
    err "  清单共 $(wc -l < "$checksum_file" | tr -d ' ') 行，前 5 行如下："
    head -n 5 "$checksum_file" | while IFS= read -r l; do err "    $l"; done
    exit 1
  fi
  if [[ "$cnt" -gt 1 ]]; then
    err "SHA256.txt 中 $ARTIFACT 存在 $cnt 条校验条目（清单歧义），拒绝安装"; exit 1
  fi
  expected="$(lower "$expected")"

  actual="$(lower "$(sha256_of "$TMP_BIN")")"
  if [[ "$actual" != "$expected" ]]; then
    err "SHA256 校验失败: $ARTIFACT"
    err "  期望: $expected"
    err "  实际: $actual"
    exit 1
  fi
  log "SHA256 校验通过: $ARTIFACT"
}
verify_checksum

if try_install_self; then
  :   # CLI 已完成副本落盘与入口决策
else
  # 每一步都必须校验：否则写入失败时会打印「已安装」并以 0 退出，
  # 让调用方（agent / CI）误以为装好了，实际入口根本不存在。
  mkdir -p "$INSTALL_DIR" || { err "无法创建安装目录: ${INSTALL_DIR}（权限不足？）"; exit 1; }
  mv "$TMP_BIN" "$DEST" || { err "无法写入: ${DEST}（目录无写权限？）"; exit 1; }
  TMP_BIN=""   # 已移动，避免 EXIT trap 误删刚安装的文件
  chmod 755 "$DEST" || true
  log "✅ 已安装 → ${DEST}（直接安装）"
fi

# ---- PATH ----
path_hint
