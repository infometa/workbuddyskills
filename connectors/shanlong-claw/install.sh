#!/usr/bin/env bash
set -euo pipefail

MIN_NODE_VERSION=18
SL_HOME="${SL_CLI_HOME:-$HOME/.slclaw}"
INSTALL_DIR="$SL_HOME/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL_CONF="$SCRIPT_DIR/install-url.conf"
ENSURE_LATEST=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "$@" >&2; }
log_ok() { log "${GREEN}✓ $*${NC}"; }
log_err() { log "${RED}✗ $*${NC}"; }
log_warn() { log "${YELLOW}→ $*${NC}"; }

usage() {
  echo "用法: bash install.sh [选项]"
  echo ""
  echo "选项:"
  echo "  --ensure-latest  对比 OSS 版本，有更新则覆盖安装；stdout 仅输出当前版本号"
  echo "  --uninstall      完全卸载（删除程序、配置、Token）"
  echo "  --reset          重置安装（清除所有数据后重新安装）"
  echo "  (无参数)         从 OSS/CDN 下载 CLI tgz 并安装（保留已有配置和 Token）"
  exit 0
}

do_uninstall() {
  log_warn "卸载商龙 CLI ..."
  rm -rf "$SL_HOME"
  log_ok "卸载完成"
  log ""
  log "提示：如果之前手动将 ~/.slclaw/bin 添加到 PATH，请自行移除。"
  exit 0
}

load_tgz_url() {
  if [ -n "${SL_CLI_TGZ_URL:-}" ]; then
    :
  elif [ -f "$URL_CONF" ]; then
    # shellcheck disable=SC1090
    source "$URL_CONF"
  elif [ -f "$SL_HOME/install-url.conf" ]; then
    # shellcheck disable=SC1090
    source "$SL_HOME/install-url.conf"
  else
    log_err "缺少 install-url.conf，无法确定 CLI 下载地址"
    exit 1
  fi
  if [ -z "${SL_CLI_TGZ_URL:-}" ]; then
    log_err "未设置 SL_CLI_TGZ_URL"
    exit 1
  fi
}

resolve_version_url() {
  if [ -n "${SL_CLI_VERSION_URL:-}" ]; then
    return 0
  fi
  if [[ "$SL_CLI_TGZ_URL" == *.tgz ]]; then
    SL_CLI_VERSION_URL="${SL_CLI_TGZ_URL%.tgz}.version"
  else
    SL_CLI_VERSION_URL="${SL_CLI_TGZ_URL}.version"
  fi
}

check_tgz_url() {
  if [[ "$SL_CLI_TGZ_URL" == *REPLACE_WITH_YOUR_OSS_HOST* ]]; then
    log_err "尚未配置真实 OSS/CDN 地址"
    log "  请编辑: $URL_CONF"
    log "  或导出环境变量 SL_CLI_TGZ_URL 后重试"
    exit 1
  fi
}

check_node() {
  if ! command -v node &>/dev/null; then
    log_err "未检测到 Node.js，请先安装 Node.js >= ${MIN_NODE_VERSION}"
    exit 1
  fi
  local node_version
  node_version=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$node_version" -lt "$MIN_NODE_VERSION" ]; then
    log_err "Node.js 版本过低: $(node -v)，需要 >= ${MIN_NODE_VERSION}"
    exit 1
  fi
  if [ "$ENSURE_LATEST" -eq 0 ]; then
    log_ok "Node.js $(node -v)"
  fi
}

fetch_to_file() {
  local url="$1"
  local dest="$2"
  if command -v curl &>/dev/null; then
    curl -fsSL --connect-timeout 5 --max-time 60 "$url" -o "$dest"
  elif command -v wget &>/dev/null; then
    wget -q --timeout=60 -O "$dest" "$url"
  else
    log_err "未找到 curl 或 wget，无法下载"
    exit 1
  fi
}

fetch_text() {
  local url="$1"
  if command -v curl &>/dev/null; then
    curl -fsSL --connect-timeout 5 --max-time 30 "$url"
  elif command -v wget &>/dev/null; then
    wget -q --timeout=30 -O- "$url"
  else
    log_err "未找到 curl 或 wget，无法下载"
    exit 1
  fi
}

read_local_version() {
  local pkg="$INSTALL_DIR/package.json"
  if [ -f "$pkg" ]; then
    node -e "const p=require(process.argv[1]); process.stdout.write(String(p.version||''))" "$pkg" 2>/dev/null || true
  fi
}

# 若 $1 > $2 返回 0
version_gt() {
  local a="$1" b="$2"
  [ -z "$b" ] && return 0
  [ -z "$a" ] && return 1
  [ "$a" = "$b" ] && return 1
  local first
  first="$(printf '%s\n%s\n' "$a" "$b" | sort -V | head -1)"
  [ "$first" = "$b" ]
}

download_tgz() {
  local dest="$1"
  log_warn "下载 CLI 包 ..."
  log "  $SL_CLI_TGZ_URL"
  fetch_to_file "$SL_CLI_TGZ_URL" "$dest"
  if [ ! -s "$dest" ]; then
    log_err "下载失败或文件为空"
    exit 1
  fi
  log_ok "下载完成"
}

install_from_tgz() {
  local tgz_path="$1"
  local tmp_dir
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/slclaw-install.XXXXXX")"

  log_warn "解压并安装到 ${INSTALL_DIR} ..."
  tar -xzf "$tgz_path" -C "$tmp_dir"

  local pkg_dir
  pkg_dir="$(find "$tmp_dir" -maxdepth 2 -type f -name package.json | head -1 | xargs dirname)"
  if [ -z "$pkg_dir" ] || [ ! -d "$pkg_dir/dist" ]; then
    rm -rf "$tmp_dir"
    log_err "tgz 内容无效：未找到 package.json 或 dist/"
    exit 1
  fi

  rm -rf "$INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
  mkdir -p "$SL_HOME"
  # 全量安装已写入最新 bin，丢弃陈旧 pending/锁，避免下次启动降级
  rm -rf "$SL_HOME/pending-update" "$SL_HOME/update-stage.lock"
  rm -rf "$SL_HOME"/tmp-update-* "$SL_HOME"/pending-update.staging-* 2>/dev/null || true

  cp -r "$pkg_dir/dist" "$INSTALL_DIR/dist"
  cp "$pkg_dir/package.json" "$INSTALL_DIR/package.json"
  if [ -f "$SCRIPT_DIR/default.env" ]; then
    cp "$SCRIPT_DIR/default.env" "$INSTALL_DIR/default.env"
    cp "$SCRIPT_DIR/default.env" "$SL_HOME/default.env"
  fi
  if [ -f "$URL_CONF" ]; then
    cp "$URL_CONF" "$SL_HOME/install-url.conf"
  fi

  cat > "$INSTALL_DIR/sl" <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"
SL_HOME="$(cd "$BIN/.." && pwd)"
PENDING="$SL_HOME/pending-update"
if [ -f "$PENDING/ready" ] && [ -d "$PENDING/dist" ] && [ -f "$PENDING/package.json" ]; then
  apply_pending() {
    rm -rf "$BIN/dist.new" "$BIN/dist.bak"
    rm -f "$BIN/package.json.new" "$BIN/package.json.bak"
    cp -R "$PENDING/dist" "$BIN/dist.new" || return 1
    cp "$PENDING/package.json" "$BIN/package.json.new" || return 1
    if [ -d "$BIN/dist" ]; then
      mv "$BIN/dist" "$BIN/dist.bak" || return 1
    fi
    if ! mv "$BIN/dist.new" "$BIN/dist"; then
      if [ -d "$BIN/dist.bak" ]; then
        mv "$BIN/dist.bak" "$BIN/dist" || true
      fi
      return 1
    fi
    if [ -f "$BIN/package.json" ]; then
      mv "$BIN/package.json" "$BIN/package.json.bak" || true
    fi
    if ! mv "$BIN/package.json.new" "$BIN/package.json"; then
      if [ -f "$BIN/package.json.bak" ]; then
        mv "$BIN/package.json.bak" "$BIN/package.json" || true
      fi
      return 1
    fi
    rm -rf "$BIN/dist.bak" "$PENDING"
    rm -f "$BIN/package.json.bak"
    return 0
  }
  if ! apply_pending; then
    rm -rf "$BIN/dist.new" 2>/dev/null || true
    rm -f "$BIN/package.json.new" 2>/dev/null || true
  fi
fi
exec node "$BIN/dist/cli/src/index.js" "$@"
WRAPPER
  chmod +x "$INSTALL_DIR/sl"

  if [ -d "$SCRIPT_DIR/skills" ]; then
    rm -rf "$SL_HOME/skills"
    cp -r "$SCRIPT_DIR/skills" "$SL_HOME/skills"
  fi

  rm -rf "$tmp_dir"
  log_ok "文件安装完成"
}

init_env() {
  local env_file="$SL_HOME/.env"
  local default_env_file="$SCRIPT_DIR/default.env"
  local needs_init=false
  local saved_key=""

  if [ ! -f "$env_file" ]; then
    needs_init=true
  elif ! grep -q 'SL_SLY_BASEURL' "$env_file" 2>/dev/null; then
    needs_init=true
    saved_key=$(grep '^SL_API_KEY=' "$env_file" 2>/dev/null | head -1 | cut -d= -f2- || true)
  fi

  if [ "$needs_init" = true ]; then
    if [ ! -f "$default_env_file" ]; then
      log_err "缺少 default.env，无法初始化连接器配置"
      exit 1
    fi
    cp "$default_env_file" "$env_file"
    chmod 600 "$env_file"
    if [ -n "${saved_key:-}" ]; then
      sed -i.bak "s/^SL_API_KEY=.*/SL_API_KEY=${saved_key}/" "$env_file" && rm -f "${env_file}.bak"
      log_ok "配置已修复（保留原 API Key）"
    else
      log_ok "默认配置已初始化"
    fi
  else
    log_ok "配置文件完整，保留原配置"
  fi
}

setup_path() {
  if echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
    return 0
  fi
  export PATH="$INSTALL_DIR:$PATH"
  log_warn "请将以下内容添加到您的 shell 配置文件（~/.zshrc 或 ~/.bashrc）："
  log ""
  log "    export PATH=\"$INSTALL_DIR:\$PATH\""
  log ""
}

verify_install() {
  local version
  version="$(read_local_version)"
  [ -n "$version" ] || version="unknown"
  log_ok "安装成功: sl v${version}"
}

do_full_install() {
  check_node
  local tmp_tgz
  tmp_tgz="$(mktemp "${TMPDIR:-/tmp}/slclaw-cli.XXXXXX.tgz")"
  cleanup_tgz() { rm -f "$tmp_tgz"; }
  trap cleanup_tgz EXIT
  download_tgz "$tmp_tgz"
  install_from_tgz "$tmp_tgz"
  init_env
  setup_path
  verify_install
}

do_ensure_latest() {
  load_tgz_url
  check_tgz_url
  resolve_version_url
  check_node

  local remote local_ver
  remote="$(fetch_text "$SL_CLI_VERSION_URL" | tr -d '[:space:]')"
  if [ -z "$remote" ]; then
    log_err "无法读取远端版本: $SL_CLI_VERSION_URL"
    exit 1
  fi
  local_ver="$(read_local_version)"

  if [ ! -f "$INSTALL_DIR/package.json" ] || version_gt "$remote" "$local_ver"; then
    log_warn "检测到更新: 本地 ${local_ver:-无} → 远端 $remote"
    do_full_install
    local_ver="$(read_local_version)"
  else
    log_ok "已是最新: v${local_ver}"
  fi

  printf '%s\n' "${local_ver:-unknown}"
}

main() {
  case "${1:-}" in
    --help|-h) usage ;;
    --uninstall) do_uninstall ;;
    --ensure-latest)
      ENSURE_LATEST=1
      do_ensure_latest
      exit 0
      ;;
    --reset)
      log_warn "重置模式：清除所有数据后重新安装"
      rm -rf "$SL_HOME"
      ;;
    -*)
      log_err "未知选项: $1"
      usage >&2
      exit 1
      ;;
  esac

  log "╔═══════════════════════════════════════╗"
  log "║  商龙 CLI 连接器安装                  ║"
  log "╚═══════════════════════════════════════╝"
  log ""
  load_tgz_url
  check_tgz_url
  do_full_install
  log ""
  log "下一步："
  log "  1. 在 WorkBuddy 中完成连接器授权，或编辑 ~/.slclaw/.env 填入 SL_API_KEY"
  log "  2. 执行 sl connector status 验证"
}

main "$@"
