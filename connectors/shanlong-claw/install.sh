#!/usr/bin/env bash
set -euo pipefail

SL_HOME="${SL_CLI_HOME:-$HOME/.slclaw}"
INSTALL_DIR="$SL_HOME/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URL_CONF="$SCRIPT_DIR/install-url.conf"
ENSURE_LATEST=0
SEA_NAME="sl-sea"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "$@" >&2; }
log_ok() { log "${GREEN}✓ $*${NC}"; }
log_err() { log "${RED}✗ $*${NC}"; }
log_warn() { log "${YELLOW}→ $*${NC}"; }

validate_sl_home() {
  local resolved="$SL_HOME"
  if command -v node >/dev/null 2>&1; then
    resolved="$(node -e 'process.stdout.write(require("path").resolve(process.argv[1]))' "$SL_HOME")"
  elif command -v python3 >/dev/null 2>&1; then
    resolved="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$SL_HOME")"
  fi
  case "$resolved" in
    ""|"/"|"$HOME"|"$HOME/"|"."|"..")
      log_err "拒绝使用危险的 SL_CLI_HOME: $resolved"
      exit 1
      ;;
  esac
  if [ -L "$SL_HOME" ]; then
    log_err "SL_CLI_HOME 不允许是符号链接: $SL_HOME"
    exit 1
  fi
}

usage() {
  echo "用法: bash install.sh [选项]"
  echo ""
  echo "选项:"
  echo "  --ensure-latest  对比 OSS 版本，有更新则覆盖安装；stdout 仅输出当前版本号"
  echo "  --uninstall      完全卸载（删除程序、配置、Token）"
  echo "  --reset          重置安装（清除所有数据后重新安装）"
  echo "  (无参数)         从 OSS/CDN 下载平台 SEA 二进制并安装（保留已有配置和 Token）"
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

read_conf_value() {
  local conf_file="$1" wanted_key="$2"
  awk -v wanted="$wanted_key" '
    {
      line = $0
      sub(/\r$/, "", line)
      if (line ~ /^[[:space:]]*(#|$)/) next
      eq = index(line, "=")
      if (eq <= 1) next
      key = substr(line, 1, eq - 1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
      if (key != wanted) next
      value = substr(line, eq + 1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      print value
      exit
    }
  ' "$conf_file"
}

normalize_base_url() {
  local base="$1"
  case "$base" in
    */) ;;
    *) base="${base}/" ;;
  esac
  printf '%s' "$base"
}

resolve_sea_target() {
  local os arch
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) arch="x64" ;;
    aarch64|arm64) arch="arm64" ;;
    i386|i686) arch="x86" ;;
  esac
  case "$os" in
    darwin)
      case "$arch" in
        arm64) SEA_ARTIFACT="sl-darwin-arm64" ;;
        x64) SEA_ARTIFACT="sl-darwin-x64" ;;
        *) SEA_ARTIFACT="" ;;
      esac
      ;;
    linux)
      case "$arch" in
        arm64) SEA_ARTIFACT="sl-linux-arm64" ;;
        x64) SEA_ARTIFACT="sl-linux-x64" ;;
        *) SEA_ARTIFACT="" ;;
      esac
      ;;
    *)
      SEA_ARTIFACT=""
      ;;
  esac
  if [ -z "$SEA_ARTIFACT" ]; then
    log_err "不支持的平台: $(uname -s) $(uname -m)"
    exit 1
  fi
}

load_base_url() {
  local conf_file=""
  if [ -n "${SL_CLI_BASE_URL:-}" ]; then
    :
  elif [ -f "$URL_CONF" ]; then
    conf_file="$URL_CONF"
  elif [ -f "$SL_HOME/install-url.conf" ]; then
    conf_file="$SL_HOME/install-url.conf"
  else
    log_err "缺少 install-url.conf，无法确定 CLI 下载地址"
    exit 1
  fi
  if [ -n "$conf_file" ]; then
    SL_CLI_BASE_URL="$(read_conf_value "$conf_file" SL_CLI_BASE_URL)"
    if [ -z "${SL_CLI_VERSION_URL:-}" ]; then
      SL_CLI_VERSION_URL="$(read_conf_value "$conf_file" SL_CLI_VERSION_URL)"
    fi
    if [ -z "${SL_CLI_MANIFEST_URL:-}" ]; then
      SL_CLI_MANIFEST_URL="$(read_conf_value "$conf_file" SL_CLI_MANIFEST_URL)"
    fi
    if [ -z "${SL_CLI_BASE_URL:-}" ]; then
      local legacy
      legacy="$(read_conf_value "$conf_file" SL_CLI_TGZ_URL)"
      if [ -n "$legacy" ]; then
        log_err "install-url.conf 仍使用已废弃的 SL_CLI_TGZ_URL，请改为 SL_CLI_BASE_URL"
        exit 1
      fi
    fi
  fi
  if [ -z "${SL_CLI_BASE_URL:-}" ]; then
    log_err "未设置 SL_CLI_BASE_URL"
    exit 1
  fi
  SL_CLI_BASE_URL="$(normalize_base_url "$SL_CLI_BASE_URL")"
}

resolve_version_url() {
  if [ -n "${SL_CLI_VERSION_URL:-}" ]; then
    return 0
  fi
  SL_CLI_VERSION_URL="${SL_CLI_BASE_URL}slclaw-cli.version"
}

resolve_manifest_url() {
  if [ -n "${SL_CLI_MANIFEST_URL:-}" ]; then
    return 0
  fi
  SL_CLI_MANIFEST_URL="${SL_CLI_BASE_URL}slclaw-cli.manifest.json"
}

resolve_artifact_url() {
  resolve_sea_target
  SL_CLI_ARTIFACT_URL="${SL_CLI_BASE_URL}${SEA_ARTIFACT}"
}

check_base_url() {
  if [[ "$SL_CLI_BASE_URL" == *REPLACE_WITH_YOUR_OSS_HOST* ]]; then
    log_err "尚未配置真实 OSS/CDN 地址"
    log "  请编辑: $URL_CONF"
    log "  或导出环境变量 SL_CLI_BASE_URL 后重试"
    exit 1
  fi
}

fetch_to_file() {
  local url="$1"
  local dest="$2"
  if [[ "$url" == file://* ]]; then
    local src="${url#file://}"
    # file:///C:/... on some systems; strip extra leading slash for Windows-style if needed
    if [[ "$src" == /* ]] && [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]]; then
      src="${src:1}"
    fi
    cp "$src" "$dest"
    return 0
  fi
  if command -v curl &>/dev/null; then
    curl -fsSL --connect-timeout 5 --max-time 300 "$url" -o "$dest"
  elif command -v wget &>/dev/null; then
    wget -q --timeout=300 -O "$dest" "$url"
  else
    log_err "未找到 curl 或 wget，无法下载"
    exit 1
  fi
}

fetch_text() {
  local url="$1"
  if [[ "$url" == file://* ]]; then
    local src="${url#file://}"
    if [[ "$src" == /* ]] && [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]]; then
      src="${src:1}"
    fi
    tr -d '\r' < "$src"
    return 0
  fi
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
  local ver_file="$INSTALL_DIR/version"
  if [ -f "$ver_file" ]; then
    tr -d '[:space:]' < "$ver_file"
    return 0
  fi
  # 兼容旧 tgz 布局
  local pkg="$INSTALL_DIR/dist/package.json"
  if [ -f "$pkg" ] && command -v node >/dev/null 2>&1; then
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

download_sea() {
  local dest="$1"
  log_warn "下载 CLI 二进制 ..."
  log "  $SL_CLI_ARTIFACT_URL"
  fetch_to_file "$SL_CLI_ARTIFACT_URL" "$dest"
  if [ ! -s "$dest" ]; then
    log_err "下载失败或文件为空"
    exit 1
  fi
  log_ok "下载完成"
}

sha256_file() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print tolower($1)}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print tolower($1)}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$file" | awk '{print tolower($NF)}'
  else
    log_err "未找到 sha256sum、shasum 或 openssl，无法校验 SEA"
    return 1
  fi
}

verify_sea_manifest() {
  local sea_path="$1" expected_version="$2" manifest artifact_line
  manifest="$(fetch_text "$SL_CLI_MANIFEST_URL")"

  local schema scope manifest_version expected_size expected_hash
  schema="$(printf '%s\n' "$manifest" | awk -F: '/"schemaVersion"/ { gsub(/[ ,]/, "", $2); print $2; exit }')"
  scope="$(printf '%s\n' "$manifest" | awk -F: '/"scope"/ { gsub(/[", ]/, "", $2); print $2; exit }')"
  manifest_version="$(printf '%s\n' "$manifest" | awk -F: '/"version"/ { gsub(/[", ]/, "", $2); print $2; exit }')"
  artifact_line="$(printf '%s\n' "$manifest" | awk -v name="$SEA_ARTIFACT" 'index($0, "\"" name "\"") { print NR; exit }')"
  if [ -n "$artifact_line" ]; then
    expected_size="$(printf '%s\n' "$manifest" | tail -n "+$artifact_line" | awk -F: '/"size"/ { gsub(/[ ,]/, "", $2); print $2; exit }')"
    expected_hash="$(printf '%s\n' "$manifest" | tail -n "+$artifact_line" | awk -F: '/"sha256"/ { gsub(/[", ]/, "", $2); print tolower($2); exit }')"
  fi

  if [ "$schema" != "1" ] || [ "$scope" != "S1-only" ]; then
    log_err "SEA manifest 无效或不是 S1-only"
    return 1
  fi
  if [ "$manifest_version" != "$expected_version" ]; then
    log_err "SEA manifest 版本不匹配: manifest=$manifest_version, version=$expected_version"
    return 1
  fi
  if [ -z "${expected_size:-}" ] || [ -z "${expected_hash:-}" ]; then
    log_err "SEA manifest 缺少当前平台产物: $SEA_ARTIFACT"
    return 1
  fi

  local actual_size actual_hash
  actual_size="$(wc -c < "$sea_path" | tr -d '[:space:]')"
  actual_hash="$(sha256_file "$sea_path")"
  if [ "$actual_size" != "$expected_size" ]; then
    log_err "SEA 文件大小不匹配: expected=$expected_size, actual=$actual_size"
    return 1
  fi
  if [ "$actual_hash" != "$expected_hash" ]; then
    log_err "SEA SHA-256 校验失败"
    return 1
  fi
}

assert_sea_runnable() {
  local sea_path="$1" expected_version="$2" self_check compact
  chmod +x "$sea_path"
  if ! self_check="$(SL_CLI_SKIP_UPDATE=1 "$sea_path" --sl-sea-self-check 2>/dev/null)"; then
    log_err "SEA self-check 执行失败"
    return 1
  fi
  compact="$(printf '%s' "$self_check" | tr -d '[:space:]')"
  case "$compact" in
    *'"ok":true'*'"version":"'"$expected_version"'"'*) ;;
    *)
      log_err "SEA self-check 结果无效或版本不匹配: expected=$expected_version"
      return 1
      ;;
  esac
}

cleanup_legacy_program_assets() {
  local target
  for target in \
    "$SL_HOME/sea" \
    "$INSTALL_DIR/.sea-cache" \
    "$INSTALL_DIR/dist" \
    "$INSTALL_DIR/node_modules"
  do
    if [ -e "$target" ]; then
      rm -rf -- "$target" || log_warn "旧程序资产清理失败，将在后续安装时重试: $target"
    fi
  done
}

write_unix_wrapper() {
  local target_dir="${1:-$INSTALL_DIR}"
  cat > "$target_dir/sl" <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"
SL_HOME="$(cd "$BIN/.." && pwd)"
PENDING="$SL_HOME/pending-update"
SEA="$BIN/sl-sea"
export SL_MAX_SECURITY_LEVEL=S1

if [ -f "$PENDING/ready" ]; then
  if [ -f "$PENDING/sl-sea" ] && [ -s "$PENDING/sl-sea" ]; then
    apply_pending() {
      rm -f "$SEA.new" "$SEA.bak"
      cp "$PENDING/sl-sea" "$SEA.new" || return 1
      chmod +x "$SEA.new" || return 1
      if [ -f "$SEA" ]; then
        mv "$SEA" "$SEA.bak" || return 1
      fi
      if ! mv "$SEA.new" "$SEA"; then
        if [ -f "$SEA.bak" ]; then
          mv "$SEA.bak" "$SEA" || true
        fi
        return 1
      fi
      local expected_version self_check compact
      expected_version="$(tr -d '[:space:]' < "$PENDING/ready")"
      if ! self_check="$(SL_CLI_SKIP_UPDATE=1 "$SEA" --sl-sea-self-check 2>/dev/null)"; then
        rm -f "$SEA"
        if [ -f "$SEA.bak" ]; then
          mv "$SEA.bak" "$SEA" || true
        fi
        return 1
      fi
      compact="$(printf '%s' "$self_check" | tr -d '[:space:]')"
      case "$compact" in
        *'"ok":true'*'"version":"'"$expected_version"'"'*) ;;
        *)
          rm -f "$SEA"
          if [ -f "$SEA.bak" ]; then
            mv "$SEA.bak" "$SEA" || true
          fi
          return 1
          ;;
      esac
      local config_result
      if ! config_result="$("$SEA" --sl-config-migrate --home "$SL_HOME")" || [[ "$config_result" != *'"ok":true'* ]]; then
        rm -f "$SEA"
        if [ -f "$SEA.bak" ]; then mv "$SEA.bak" "$SEA" || true; fi
        return 1
      fi
      if [[ "$config_result" == *'"status":"conflict"'* ]]; then printf '%s\n' "$config_result" >&2; fi
      if [ -f "$PENDING/ready" ]; then
        cp "$PENDING/ready" "$BIN/version" || true
      fi
      rm -rf "$SEA.bak" "$PENDING"
      rm -rf -- "$SL_HOME/sea" "$BIN/.sea-cache" "$BIN/dist" "$BIN/node_modules"
      return 0
    }
    if ! apply_pending; then
      rm -f "$SEA.new" 2>/dev/null || true
      rm -rf "$PENDING"
    fi
  else
    rm -rf "$PENDING"
  fi
fi

if [ ! -x "$SEA" ]; then
  echo "sl-sea binary missing: $SEA" >&2
  exit 1
fi
exec "$SEA" "$@"
WRAPPER
  chmod +x "$target_dir/sl"
}

install_from_sea() {
  local sea_path="$1"
  local remote_version="${2:-}"
  local new_dir="${INSTALL_DIR}.new"
  local backup_dir="${INSTALL_DIR}.bak"

  log_warn "安装到 ${INSTALL_DIR} ..."

  mkdir -p "$SL_HOME"
  chmod 700 "$SL_HOME"
  # 全量安装已写入最新 bin，丢弃陈旧 pending/锁，避免下次启动降级
  rm -rf "$SL_HOME/pending-update" "$SL_HOME/update-stage.lock"
  rm -rf "$SL_HOME"/tmp-update-* "$SL_HOME"/pending-update.staging-* 2>/dev/null || true

  rm -rf "$new_dir" "$backup_dir"
  mkdir -p "$new_dir"

  cp "$sea_path" "$new_dir/$SEA_NAME"
  chmod +x "$new_dir/$SEA_NAME"

  if [ -n "$remote_version" ]; then
    printf '%s\n' "$remote_version" > "$new_dir/version"
  elif [ -n "${SL_CLI_VERSION_URL:-}" ]; then
    fetch_text "$SL_CLI_VERSION_URL" | tr -d '[:space:]' > "$new_dir/version" || true
    if [ -s "$new_dir/version" ]; then
      printf '\n' >> "$new_dir/version"
    fi
  fi

  write_unix_wrapper "$new_dir"

  if [ -d "$INSTALL_DIR" ]; then
    mv "$INSTALL_DIR" "$backup_dir"
  fi
  if ! mv "$new_dir" "$INSTALL_DIR"; then
    if [ -d "$backup_dir" ]; then
      mv "$backup_dir" "$INSTALL_DIR" || true
    fi
    return 1
  fi

  if [ -f "$URL_CONF" ]; then
    cp "$URL_CONF" "$SL_HOME/install-url.conf"
  fi

  # Skills 由 WorkBuddy 从连接器 zip 加载；旧程序资产在新二进制验证成功后清理。
  rm -rf "$SL_HOME/skills"
  rm -f "$SL_HOME/.DS_Store"
  if [ -f "$SL_HOME/token.json" ]; then
    chmod 600 "$SL_HOME/token.json"
  fi

  log_ok "文件安装完成"
}

init_env() {
  if [ -f "$SL_HOME/pending-update/ready" ]; then
    log_warn '配置迁移随 pending-update 激活执行，当前配置保持不变'
    return 0
  fi
  local result
  result="$("$INSTALL_DIR/$SEA_NAME" --sl-config-migrate --home "$SL_HOME")" || return 1
  if [[ "$result" != *'"ok":true'* ]]; then log_err 'config-migration-invalid-result'; return 1; fi
  # The internal command emits field names and status only, never values.
  log_ok "配置迁移: $result"
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
  local version entry_version
  if [ ! -x "$INSTALL_DIR/sl" ]; then
    log_err "安装验证失败: sl 启动脚本缺失或不可执行"
    return 1
  fi
  version="$(read_local_version)"
  [ -n "$version" ] || version="unknown"
  if [ -x "$INSTALL_DIR/$SEA_NAME" ]; then
    if assert_sea_runnable "$INSTALL_DIR/$SEA_NAME" "$version"; then
      if ! entry_version="$(SL_CLI_SKIP_UPDATE=1 "$INSTALL_DIR/sl" --version)" || [ "$entry_version" != "$version" ]; then
        log_err "安装验证失败: sl 启动入口版本不匹配"
        return 1
      fi
      log_ok "安装成功: sl v${version}"
      return 0
    fi
  fi
  log_err "安装验证失败: SEA self-check 未通过"
  return 1
}

do_full_install() {
  resolve_artifact_url
  _SL_TMP_SEA="$(mktemp "${TMPDIR:-/tmp}/slclaw-cli.XXXXXX")"
  cleanup_sea() {
    rm -f "${_SL_TMP_SEA:-}"
    unset -v _SL_TMP_SEA 2>/dev/null || true
  }
  trap cleanup_sea EXIT
  download_sea "$_SL_TMP_SEA"
  local remote_ver=""
  if [ -n "${SL_CLI_VERSION_URL:-}" ]; then
    remote_ver="$(fetch_text "$SL_CLI_VERSION_URL" | tr -d '[:space:]' || true)"
  fi
  if [ -z "$remote_ver" ]; then
    log_err "无法读取远端版本: $SL_CLI_VERSION_URL"
    return 1
  fi
  verify_sea_manifest "$_SL_TMP_SEA" "$remote_ver"
  assert_sea_runnable "$_SL_TMP_SEA" "$remote_ver"
  install_from_sea "$_SL_TMP_SEA" "$remote_ver"
  setup_path
  if ! verify_install || ! init_env; then
    rm -rf "$INSTALL_DIR"
    if [ -d "${INSTALL_DIR}.bak" ]; then
      mv "${INSTALL_DIR}.bak" "$INSTALL_DIR"
    fi
    return 1
  fi
  cleanup_legacy_program_assets || log_warn '安装已完成；旧程序资产清理失败'
  rm -rf "${INSTALL_DIR}.bak" || log_warn '安装已完成；旧版本备份清理失败'
  cleanup_sea
  trap - EXIT
}

do_ensure_latest() {
  load_base_url
  check_base_url
  resolve_version_url
  resolve_manifest_url
  resolve_artifact_url

  local remote local_ver
  remote="$(fetch_text "$SL_CLI_VERSION_URL" | tr -d '[:space:]')"
  if [ -z "$remote" ]; then
    log_err "无法读取远端版本: $SL_CLI_VERSION_URL"
    exit 1
  fi
  local_ver="$(read_local_version)"

  if [ ! -f "$INSTALL_DIR/$SEA_NAME" ] || [ -d "$INSTALL_DIR/dist" ] || version_gt "$remote" "$local_ver"; then
    log_warn "检测到更新: 本地 ${local_ver:-无} → 远端 $remote"
    do_full_install
    local_ver="$(read_local_version)"
  else
    if [ ! -x "$INSTALL_DIR/sl" ]; then write_unix_wrapper; fi
    chmod +x "$INSTALL_DIR/$SEA_NAME"
    verify_install
    init_env
    log_ok "已是最新: v${local_ver}"
  fi

  printf '%s\n' "${local_ver:-unknown}"
}

main() {
  validate_sl_home
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
  load_base_url
  check_base_url
  resolve_version_url
  resolve_manifest_url
  do_full_install
  log ""
  log "下一步："
  log "  1. 在 WorkBuddy 中完成连接器授权，或编辑 ~/.slclaw/.env 填入 SL_API_KEY"
  log "  2. 执行 sl connector status 验证"
}

main "$@"
