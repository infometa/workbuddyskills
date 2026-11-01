#!/bin/sh
# 腾讯网盘 tdrive —— WorkBuddy 连接器安装脚本（macOS / Linux）
#
# 由 WorkBuddy 连接器的 `init` 命令下载后执行（见 connector/workbuddy/cli.json）。
# 非交互、幂等：已是目标版本则跳过下载；每次都会校验并补齐 WorkBuddy 会话钩子。
#
# 占位符 https://ai-drivecli-1251316161.cos.ap-guangzhou.myqcloud.com / 1.1.1-beta 由 scripts/package-connector.sh 在打包时替换。
#
# 安全约定：
#   - 只访问 DOWNLOAD_BASE_URL 白名单域，严格 TLS（https only, TLS>=1.2）；
#   - 下载的二进制必须通过同名 .sha256 校验，失败即中止（不落盘、不执行）；
#   - 全部变量加引号，不执行任何用户可注入的 URL；
#   - 不修改用户 shell 配置（PATH 仅提示）。

set -eu

main() {
  DOWNLOAD_BASE_URL="https://ai-drivecli-1251316161.cos.ap-guangzhou.myqcloud.com"
  VERSION="1.1.1-beta"
  # 布局与 skill 的 Install 章节一致：真实产物在专属目录，PATH 目录只放符号链接
  INSTALL_DIR="$HOME/.local/share/tdrive/bin"
  LINK_DIR="$HOME/.local/bin"

  os_uname=$(uname -s)
  arch_uname=$(uname -m)
  case "$os_uname/$arch_uname" in
    Linux/x86_64)  target="linux-x86_64" ;;
    Darwin/arm64)  target="darwin-aarch64" ;;
    Darwin/x86_64) target="darwin-x86_64" ;;
    *) echo "不支持的平台: $os_uname/$arch_uname" >&2; exit 1 ;;
  esac

  BIN_URL="${DOWNLOAD_BASE_URL}/${VERSION}/tdrive-${target}"
  SHA_URL="${BIN_URL}.sha256"

  need_download=1
  if [ -x "$INSTALL_DIR/tdrive" ] && [ -L "$LINK_DIR/tdrive" ]; then
    cur=$("$INSTALL_DIR/tdrive" --version 2>/dev/null | awk '{print $NF}') || cur=""
    if [ "$cur" = "$VERSION" ]; then
      echo "tdrive $cur 已安装，跳过下载。"
      need_download=0
    fi
  fi

  mkdir -p "$INSTALL_DIR" "$LINK_DIR"

  if [ "$need_download" = "1" ]; then
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT

    curl --fail --location --proto '=https' --tlsv1.2 -sSo "$tmp/tdrive" "$BIN_URL"
    curl --fail --location --proto '=https' --tlsv1.2 -sSo "$tmp/tdrive.sha256" "$SHA_URL"

    # macOS 只有 shasum，多数 Linux 只有 sha256sum：双路兜底
    expected=$(awk '{print $1}' "$tmp/tdrive.sha256" | tr 'A-Z' 'a-z')
    if command -v sha256sum >/dev/null 2>&1; then
      actual=$(sha256sum "$tmp/tdrive" | awk '{print $1}')
    elif command -v shasum >/dev/null 2>&1; then
      actual=$(shasum -a 256 "$tmp/tdrive" | awk '{print $1}')
    else
      echo "缺少 sha256 校验工具（sha256sum / shasum 均不可用），拒绝安装未校验的二进制" >&2
      exit 1
    fi
    actual=$(printf '%s' "$actual" | tr 'A-Z' 'a-z')
    if [ "$expected" != "$actual" ]; then
      echo "SHA256 校验失败: expected=$expected actual=$actual" >&2
      exit 1
    fi

    chmod +x "$tmp/tdrive"
    # 先写同目录临时名再 rename：覆盖运行中的二进制不会出现半写状态
    cp "$tmp/tdrive" "$INSTALL_DIR/tdrive.new"
    mv -f "$INSTALL_DIR/tdrive.new" "$INSTALL_DIR/tdrive"
  fi

  ln -sfn "$INSTALL_DIR/tdrive" "$LINK_DIR/tdrive"

  # 注册 WorkBuddy 会话钩子（写 ~/.workbuddy/settings.json：只增不毁、幂等、改动前自动备份）。
  # 失败不应让整个安装失败（二进制已就绪，网盘命令可用），仅提示。
  if ! "$INSTALL_DIR/tdrive" hook register --host workbuddy >/dev/null 2>&1; then
    echo "提示：未能写入 WorkBuddy 会话钩子（会话自动备份不可用，其余功能不受影响）。" >&2
    echo "      可稍后手动执行：$INSTALL_DIR/tdrive hook register --host workbuddy" >&2
  fi

  "$INSTALL_DIR/tdrive" --version
}

main "$@"
