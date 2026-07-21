#!/usr/bin/env bash
# ============================================================
# TeachAny Setup · v1.0
# ============================================================
# 安装完 skill 后运行一次，配置 GitHub 推送凭据。
# 之后 auto-publish.sh 自动读取，无需每次手动设置。
#
# 使用方法：
#   bash ~/.codebuddy/skills/teachany/scripts/setup.sh
#   bash ~/.agents/skills/teachany/scripts/setup.sh
# ============================================================

set -e

CONFIG_DIR="$HOME/.teachany"
CONFIG_FILE="$CONFIG_DIR/config"

echo "══════════════════════════════════════════════"
echo "  TeachAny Setup v1.0"
echo "══════════════════════════════════════════════"
echo ""

# ── 检测已有配置 ──────────────────────────────────
if [ -f "$CONFIG_FILE" ]; then
  echo "✅ 检测到已有配置: $CONFIG_FILE"
  grep -v "TOKEN\|token" "$CONFIG_FILE" || true
  echo ""
  read -r -p "重新配置？(y/N) " _ans
  [[ "$_ans" =~ ^[Yy]$ ]] || { echo "跳过，保留原配置。"; exit 0; }
  echo ""
fi

# ── 检测 SSH 是否已配置 ────────────────────────────
echo "[1/3] 检测 SSH 认证..."
if ssh -T git@github.com -o BatchMode=yes -o ConnectTimeout=5 2>&1 | grep -q "successfully authenticated"; then
  echo "  ✅ SSH 已配置，发布时优先使用 SSH，无需 token。"
  _ssh_ok=true
else
  echo "  ⚠️  SSH 未配置或无法连接 GitHub。"
  _ssh_ok=false
fi
echo ""

# ── 配置 GitHub Token ─────────────────────────────
echo "[2/3] 配置 GitHub Token（用于 HTTPS 推送）..."
echo ""
echo "  前往 https://github.com/settings/tokens/new 创建 token："
echo "  · 类型选 Fine-grained token"
echo "  · Repository: weponusa/teachany（或你的 fork）"
echo "  · 权限：Contents → Read and write"
echo ""

if $_ssh_ok; then
  read -r -p "  已有 SSH，可跳过 token 配置。跳过？(Y/n) " _skip
  [[ "$_skip" =~ ^[Nn]$ ]] || { echo "  跳过 token 配置。"; _token=""; }
fi

if [ -z "${_token+x}" ]; then
  read -r -s -p "  粘贴 GitHub Token（输入不显示）: " _token
  echo ""
  if [ -z "$_token" ]; then
    echo "  ⚠️  未输入 token，跳过。"
    _token=""
  else
    # 验证 token
    _http=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: token $_token" \
      "https://api.github.com/user")
    if [ "$_http" = "200" ]; then
      echo "  ✅ Token 有效"
    else
      echo "  ❌ Token 验证失败 (HTTP $_http)，请检查 token 是否正确或已过期。"
      exit 1
    fi
  fi
fi

# ── 配置仓库路径 ──────────────────────────────────
echo ""
echo "[3/3] 配置本地仓库路径..."
_default_repo="$HOME/CodeBuddy/一次函数/teachany-opensource"
if [ ! -d "$_default_repo" ]; then
  _default_repo="$HOME/teachany"
fi
read -r -p "  TeachAny 仓库本地路径 [$_default_repo]: " _repo
_repo="${_repo:-$_default_repo}"

if [ ! -d "$_repo/.git" ]; then
  echo "  ⚠️  路径 $_repo 不是 Git 仓库，请先 clone："
  echo "     git clone https://github.com/weponusa/teachany.git \"$_repo\""
  echo "  配置已保存，路径可之后修改。"
fi

# ── 写入配置文件 ──────────────────────────────────
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

cat > "$CONFIG_FILE" << EOF
# TeachAny 配置文件 — 由 setup.sh 自动生成
# 修改后无需重新运行 setup.sh，直接生效。

TEACHANY_REPO="$_repo"
EOF

if [ -n "$_token" ]; then
  cat >> "$CONFIG_FILE" << EOF
GH_TOKEN="$_token"
EOF
  chmod 600 "$CONFIG_FILE"
  echo ""
  echo "  🔒 Token 已写入 $CONFIG_FILE（仅本用户可读）"
else
  chmod 644 "$CONFIG_FILE"
fi

# ── 完成 ──────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════"
echo "  ✅ 配置完成！"
echo ""
echo "  配置文件: $CONFIG_FILE"
echo "  仓库路径: $_repo"
[ -n "$_token" ] && echo "  认证方式: GH_TOKEN (HTTPS)" || echo "  认证方式: SSH"
echo ""
echo "  现在可以直接发布课件："
echo "  bash \"\$TEACHANY_SKILL/scripts/auto-publish.sh\" <course-id>"
echo "══════════════════════════════════════════════"
