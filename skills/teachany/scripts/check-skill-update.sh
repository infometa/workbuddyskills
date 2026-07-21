#!/usr/bin/env bash
# ============================================================
# TeachAny Skill Auto-Update Checker · v6.9
# ============================================================
# Phase 0.5 步骤 0 调用：检测 skill 是否为最新版，必要时自动 git pull。
#
# 退出码（非 0 不阻断 AI 流程，只是日志告警）:
#   0  = 已是最新 / 已成功更新 / 静默降级
#   非 0 仅在错误必须暴露时使用（当前都返回 0，确保不阻断课件生成）
#
# 调用：
#   bash ~/.codebuddy/skills/teachany/scripts/check-skill-update.sh
# ============================================================

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ─── 1. 定位 skill 所在的 git 仓库（找最近的 .git）───────
find_git_root() {
  local d="$1"
  while [ "$d" != "/" ]; do
    if [ -d "$d/.git" ]; then echo "$d"; return; fi
    d="$(dirname "$d")"
  done
}

# 软链情况：解软链取真实路径
real_skill="$(cd "$(dirname "$(readlink "$SKILL_DIR" 2>/dev/null || echo "$SKILL_DIR")")" && pwd)/$(basename "$SKILL_DIR")"
[ -d "$real_skill" ] || real_skill="$SKILL_DIR"

REPO_ROOT="$(find_git_root "$real_skill")"

if [ -z "$REPO_ROOT" ]; then
  echo "ℹ️  skill 不在 git 仓库内（手动安装），跳过版本检测"
  exit 0
fi

# ─── 2. 检测 remote ──────────────────────────────────
cd "$REPO_ROOT" || exit 0

if ! git remote -v | grep -qE "(github|gitee).*teachany"; then
  echo "ℹ️  skill 仓库无 teachany 上游 remote，跳过更新"
  exit 0
fi

# ─── 3. fetch 远程（最多 5s 超时，离线静默降级）─────
if ! timeout 5 git fetch --quiet origin main 2>/dev/null; then
  echo "ℹ️  skill 更新检测失败（网络/超时），使用本地版本"
  exit 0
fi

LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git rev-parse origin/main)

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
  echo "✅ skill 已是最新版（$(echo $LOCAL_SHA | cut -c1-7)）"
  exit 0
fi

# ─── 4. 远程比本地新 → 自动 pull ──────────────────────
echo "🔄 检测到 skill 新版："
echo "   本地: $(echo $LOCAL_SHA | cut -c1-7)"
echo "   远程: $(echo $REMOTE_SHA | cut -c1-7)"

# 检查是否有未提交修改
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  本地有未提交修改，先 stash"
  git stash push -m "auto-stash before skill update $(date +%s)" 2>&1 | tail -2
  STASHED=1
fi

if git pull --rebase origin main --quiet 2>&1; then
  echo "✅ skill 已自动更新到 $(git rev-parse --short HEAD)"
  echo "📌 AI 必须重新读取 SKILL_CN.md（内容可能已变）"
  if [ "$STASHED" = "1" ]; then
    echo "🔓 恢复 stash..."
    git stash pop 2>&1 | tail -2
  fi
else
  echo "⚠️  自动更新失败（可能有冲突），保留本地版本"
  if [ "$STASHED" = "1" ]; then
    git stash pop 2>&1 | tail -2
  fi
fi

exit 0
