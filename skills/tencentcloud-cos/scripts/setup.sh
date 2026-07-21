#!/bin/bash
# 腾讯云 COS Skill 自动设置脚本
# 用法:
#   setup.sh --check-only              仅检查环境状态
#   setup.sh --from-env                从已有环境变量读取凭证并安装依赖（不持久化）
#   setup.sh --from-env --persist      从已有环境变量读取凭证并写入项目本地 .env 文件
#
# 安全默认行为:
#   - 默认凭证仅存于当前 shell session 环境变量，不写入磁盘
#   - --persist 将凭证写入项目本地 .env 文件（权限 600），下次脚本自动读取
#   - npm 包安装到项目本地 node_modules/，不使用全局安装

set -e

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
info() { echo -e "${CYAN}ℹ${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$BASE_DIR/.env"

# ========== 检查函数 ==========

check_node() {
  if command -v node &>/dev/null; then
    ok "Node.js $(node --version)"
    return 0
  else
    fail "Node.js 未安装"
    return 1
  fi
}

check_npm() {
  if command -v npm &>/dev/null; then
    ok "npm $(npm --version)"
    return 0
  else
    fail "npm 未安装"
    return 1
  fi
}

check_cos_sdk() {
  if node -e "require('cos-nodejs-sdk-v5')" &>/dev/null 2>&1; then
    ok "cos-nodejs-sdk-v5 已安装"
    return 0
  else
    fail "cos-nodejs-sdk-v5 未安装"
    return 1
  fi
}

check_env_vars() {
  local all_set=true
  for var in TENCENT_COS_SECRET_ID TENCENT_COS_SECRET_KEY TENCENT_COS_REGION TENCENT_COS_BUCKET; do
    if [ -n "${!var}" ]; then
      ok "$var 已设置"
    else
      fail "$var 未设置"
      all_set=false
    fi
  done
  if [ -n "$TENCENT_COS_TOKEN" ]; then
    ok "TENCENT_COS_TOKEN 已设置（STS 临时凭证）"
  fi
  if [ -n "$TENCENT_COS_DATASET_NAME" ]; then
    ok "TENCENT_COS_DATASET_NAME 已设置"
  fi
  $all_set
}

check_env_file() {
  local ENV_ENC_FILE="$BASE_DIR/.env.enc"
  if [ -f "$ENV_ENC_FILE" ] && [ -f "$ENV_FILE" ]; then
    ok ".env.enc 加密文件已存在 + .env 明文文件也存在（建议执行 encrypt-env 统一为加密模式）"
    return 0
  elif [ -f "$ENV_ENC_FILE" ]; then
    ok ".env.enc 加密文件已存在（凭证已加密持久化，AES-256-GCM）"
    return 0
  elif [ -f "$ENV_FILE" ]; then
    ok ".env 文件已存在（凭证已明文持久化）"
    warn "建议执行 node scripts/cos_node.mjs encrypt-env 加密凭证"
    return 0
  else
    info ".env / .env.enc 均不存在（凭证未持久化）"
    return 1
  fi
}

# ========== 写入 .env 文件 ==========

write_env_file() {
  local ENV_ENC_FILE="$BASE_DIR/.env.enc"

  # 兼容：如果已有加密文件，备份后提示用户重新加密
  if [ -f "$ENV_ENC_FILE" ]; then
    warn "检测到已有加密凭证文件 .env.enc"
    info "将写入新的 .env 明文文件，旧的 .env.enc 保留"
    info "写入完成后建议执行 node scripts/cos_node.mjs encrypt-env 重新加密"
  fi

  {
    echo "# 腾讯云 COS 凭证配置（由 setup.sh --persist 生成）"
    echo "# ⚠️ 此文件包含敏感凭证，请勿提交到版本控制"
    echo "TENCENT_COS_SECRET_ID='$TENCENT_COS_SECRET_ID'"
    echo "TENCENT_COS_SECRET_KEY='$TENCENT_COS_SECRET_KEY'"
    echo "TENCENT_COS_REGION='$TENCENT_COS_REGION'"
    echo "TENCENT_COS_BUCKET='$TENCENT_COS_BUCKET'"
    [ -n "$TENCENT_COS_TOKEN" ] && echo "TENCENT_COS_TOKEN='$TENCENT_COS_TOKEN'"
    [ -n "$TENCENT_COS_DATASET_NAME" ] && echo "TENCENT_COS_DATASET_NAME='$TENCENT_COS_DATASET_NAME'"
    [ -n "$TENCENT_COS_DOMAIN" ] && echo "TENCENT_COS_DOMAIN='$TENCENT_COS_DOMAIN'"
    [ -n "$TENCENT_COS_SERVICE_DOMAIN" ] && echo "TENCENT_COS_SERVICE_DOMAIN='$TENCENT_COS_SERVICE_DOMAIN'"
    [ -n "$TENCENT_COS_PROTOCOL" ] && echo "TENCENT_COS_PROTOCOL='$TENCENT_COS_PROTOCOL'"
  } > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  ok ".env 文件已写入（权限 600）"

  # 确保 .gitignore 包含 .env
  local GITIGNORE="$BASE_DIR/.gitignore"
  if [ -f "$GITIGNORE" ]; then
    if ! grep -qx '.env' "$GITIGNORE" 2>/dev/null; then
      echo '.env' >> "$GITIGNORE"
      ok ".env 已追加到 .gitignore"
    fi
  else
    echo '.env' > "$GITIGNORE"
    ok "已创建 .gitignore 并添加 .env"
  fi
}

# ========== 检查模式 ==========

do_check() {
  echo "=== 腾讯云 COS Skill 环境检查 ==="
  echo ""
  echo "--- 基础环境 ---"
  check_node || true
  check_npm || true
  echo ""
  echo "--- COS Node.js SDK ---"
  check_cos_sdk || true
  echo ""
  echo "--- 凭证状态 ---"
  check_env_file || true
  check_env_vars || true
  echo ""
  echo "--- Skill 文件 ---"
  [ -f "$BASE_DIR/SKILL.md" ] && ok "SKILL.md" || fail "SKILL.md 不存在"
  [ -f "$BASE_DIR/scripts/cos_node.mjs" ] && ok "scripts/cos_node.mjs" || fail "scripts/cos_node.mjs 不存在"
  echo ""
}

# ========== 设置模式 ==========

do_setup() {
  local PERSIST=false
  if [ "$1" = "--persist" ]; then
    PERSIST=true
  fi

  if $PERSIST; then
    echo "=== 腾讯云 COS Skill 自动设置（--persist 模式） ==="
  else
    echo "=== 腾讯云 COS Skill 自动设置 ==="
  fi
  echo ""

  # 1. 检查 Node.js
  echo "--- 步骤 1: 检查 Node.js ---"
  if ! check_node; then
    fail "请先安装 Node.js: https://nodejs.org/"
    exit 1
  fi

  # 2. 确保 package.json 存在
  echo ""
  echo "--- 步骤 2: 初始化项目 ---"
  if [ ! -f "$BASE_DIR/package.json" ]; then
    (cd "$BASE_DIR" && npm init -y &>/dev/null)
    ok "已创建 package.json"
  else
    ok "package.json 已存在"
  fi

  # 3. 安装 cos-nodejs-sdk-v5
  echo ""
  echo "--- 步骤 3: 安装依赖 ---"
  (cd "$BASE_DIR" && npm install cos-nodejs-sdk-v5 --no-progress 2>&1 | tail -3)
  ok "cos-nodejs-sdk-v5 安装完成"

  # 4. 持久化凭证（如果指定 --persist）
  echo ""
  if $PERSIST; then
    echo "--- 步骤 4: 持久化凭证到 .env ---"
    write_env_file
  else
    echo "--- 步骤 4: 凭证模式 ---"
    info "默认模式：凭证仅存于当前 session 环境变量"
    info "如需持久化，请加 --persist 重新运行"
  fi

  # 5. 验证连接
  echo ""
  echo "--- 步骤 5: 验证连接 ---"
  if (cd "$BASE_DIR" && node scripts/cos_node.mjs list --max-keys 1 2>/dev/null | grep -q '"success": true'); then
    ok "COS 连接验证成功"
  else
    warn "COS 连接验证失败，请检查凭证和网络"
  fi

  echo ""
  echo "=== 设置完成 ==="
  echo ""
  echo "使用方式："
  echo "  node $BASE_DIR/scripts/cos_node.mjs <action> [--option value ...]"
  echo ""
  echo "查看所有可用操作："
  echo "  node $BASE_DIR/scripts/cos_node.mjs"
  echo ""
  if $PERSIST; then
    info "凭证已持久化到 $ENV_FILE，下次运行脚本自动读取"
    warn "⚠️ .env 文件包含明文敏感凭证，建议加密："
    info "  node $BASE_DIR/scripts/cos_node.mjs encrypt-env"
    info "清理凭证：rm -f $ENV_FILE $BASE_DIR/.env.enc"
  else
    info "凭证仅在当前 session 有效，关闭终端后需重新设置"
  fi
  if [ -n "$TENCENT_COS_TOKEN" ]; then
    info "STS 临时凭证有有效期，过期后需重新获取"
  fi
}

# ========== 主入口 ==========

case "$1" in
  --check-only)
    do_check
    ;;
  --from-env)
    if [ -z "$TENCENT_COS_SECRET_ID" ] || [ -z "$TENCENT_COS_SECRET_KEY" ] || [ -z "$TENCENT_COS_REGION" ] || [ -z "$TENCENT_COS_BUCKET" ]; then
      echo "错误: --from-env 模式需要先设置环境变量："
      echo "  export TENCENT_COS_SECRET_ID='<ID>'"
      echo "  export TENCENT_COS_SECRET_KEY='<KEY>'"
      echo "  export TENCENT_COS_REGION='<Region>'"
      echo "  export TENCENT_COS_BUCKET='<Bucket>'"
      echo "  # 可选："
      echo "  export TENCENT_COS_TOKEN='<SecurityToken>'"
      echo "  export TENCENT_COS_DATASET_NAME='<DatasetName>'"
      exit 1
    fi
    do_setup "$2"
    ;;
  *)
    echo "腾讯云 COS Skill 设置工具"
    echo ""
    echo "用法:"
    echo "  $0 --check-only"
    echo "    仅检查环境状态"
    echo ""
    echo "  $0 --from-env"
    echo "    从已有环境变量读取凭证并安装依赖（默认不持久化）"
    echo ""
    echo "  $0 --from-env --persist"
    echo "    从已有环境变量读取凭证 + 写入项目本地 .env 文件（权限 600）"
    echo "    下次运行脚本时自动从 .env 读取凭证，无需重新 export"
    echo ""
    echo "安全默认行为："
    echo "  • 默认凭证不写入磁盘，仅存于当前 session 环境变量"
    echo "  • --persist 写入项目本地 .env（自动添加到 .gitignore）"
    echo "  • npm 包安装到项目本地 node_modules/"
    echo "  • 必须使用子账号最小权限密钥"
    ;;
esac
