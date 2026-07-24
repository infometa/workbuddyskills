#!/usr/bin/env bash
set -euo pipefail

MIN_NODE_VERSION=18
SL_HOME="$HOME/.slclaw"
INSTALL_DIR="$SL_HOME/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
  echo "用法: bash install.sh [选项]"
  echo ""
  echo "选项:"
  echo "  --uninstall   完全卸载（删除程序、配置、Token）"
  echo "  --reset       重置安装（清除所有数据后重新安装）"
  echo "  (无参数)      安装/升级（保留已有配置和 Token）"
  exit 0
}

do_uninstall() {
  echo "→ 卸载商龙 CLI ..."
  rm -rf "$SL_HOME"
  echo -e "${GREEN}✓ 卸载完成${NC}"
  echo ""
  echo "提示：如果之前手动将 ~/.slclaw/bin 添加到 PATH，请自行移除。"
  exit 0
}

check_node() {
  if ! command -v node &>/dev/null; then
    echo -e "${RED}✗ 未检测到 Node.js，请先安装 Node.js >= ${MIN_NODE_VERSION}${NC}"
    echo "  macOS:   brew install node"
    echo "  Linux:   curl -fsSL https://deb.nodesource.com/setup_${MIN_NODE_VERSION}.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "  Windows: https://nodejs.org/"
    exit 1
  fi
  local node_version
  node_version=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$node_version" -lt "$MIN_NODE_VERSION" ]; then
    echo -e "${RED}✗ Node.js 版本过低: $(node -v)，需要 >= ${MIN_NODE_VERSION}${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Node.js $(node -v)${NC}"
}

install_local() {
  echo "→ 安装到 ${INSTALL_DIR} ..."

  rm -rf "$INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
  mkdir -p "$SL_HOME"

  cp -r "$SCRIPT_DIR/dist" "$INSTALL_DIR/dist"
  cp "$SCRIPT_DIR/package.json" "$INSTALL_DIR/package.json"
  if [ -f "$SCRIPT_DIR/default.env" ]; then
    cp "$SCRIPT_DIR/default.env" "$INSTALL_DIR/default.env"
    cp "$SCRIPT_DIR/default.env" "$SL_HOME/default.env"
  fi

  cat > "$INSTALL_DIR/sl" <<'WRAPPER'
#!/usr/bin/env node
require('./dist/cli/src/index.js');
WRAPPER
  chmod +x "$INSTALL_DIR/sl"

  [ -d "$SCRIPT_DIR/skills" ] && rm -rf "$SL_HOME/skills" && cp -r "$SCRIPT_DIR/skills" "$SL_HOME/skills"

  echo -e "${GREEN}✓ 文件安装完成${NC}"
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
      echo -e "${RED}✗ 缺少 default.env，无法初始化连接器配置${NC}"
      exit 1
    fi
    cp "$default_env_file" "$env_file"
    chmod 600 "$env_file"
    if [ -n "${saved_key:-}" ]; then
      sed -i.bak "s/^SL_API_KEY=.*/SL_API_KEY=${saved_key}/" "$env_file" && rm -f "${env_file}.bak"
      echo -e "${GREEN}✓ 配置已修复（保留原 API Key）${NC}"
    else
      echo -e "${GREEN}✓ 默认配置已初始化${NC}"
    fi
  else
    echo -e "${GREEN}✓ 配置文件完整，保留原配置${NC}"
  fi
}

setup_path() {
  if echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/.slclaw/bin"; then
    return 0
  fi
  export PATH="$HOME/.slclaw/bin:$PATH"
  echo -e "${YELLOW}⚠ 请将以下内容添加到您的 shell 配置文件（~/.zshrc 或 ~/.bashrc）：${NC}"
  echo ""
  echo "    export PATH=\"\$HOME/.slclaw/bin:\$PATH\""
  echo ""
}

verify_install() {
  local version
  version=$("$INSTALL_DIR/sl" --version 2>/dev/null || echo "unknown")
  echo -e "${GREEN}✓ 安装成功: sl v${version}${NC}"
}

main() {
  case "${1:-}" in
    --help|-h) usage ;;
    --uninstall) do_uninstall ;;
    --reset)
      echo -e "${YELLOW}→ 重置模式：清除所有数据后重新安装${NC}"
      rm -rf "$SL_HOME"
      ;;
  esac

  echo "╔═══════════════════════════════════════╗"
  echo "║  商龙 CLI 连接器安装                  ║"
  echo "╚═══════════════════════════════════════╝"
  echo ""
  check_node
  install_local
  init_env
  setup_path
  verify_install
  echo ""
  echo "下一步："
  echo "  1. 编辑 ~/.slclaw/.env，填入 SL_API_KEY"
  echo "  2. 执行 sl connector status 验证"
}

main "$@"
