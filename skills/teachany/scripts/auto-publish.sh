#!/usr/bin/env bash
# ============================================================
# TeachAny Auto-Publish · v2.1 (双仓库版)
# ============================================================
# 维护者直推流程：
#   1. 从主仓库或指定目录读取课件
#   2. 同步真实课件到 teachany-courseware/community/<course-id>/
#   3. 在 teachany-courseware 跑 rebuild-index（注册 + 索引）
#   4. git add / commit / push
#   5. 验证 courseware Pages 实体 URL
# ============================================================

set -e

_CONFIG="$HOME/.teachany/config"
if [ -f "$_CONFIG" ]; then
  # shellcheck source=/dev/null
  source "$_CONFIG"
fi

COURSE_ID="${1:-}"
COURSEWARE_REPO="${2:-${TEACHANY_COURSEWARE_REPO:-$HOME/CodeBuddy/一次函数/teachany-courseware}}"
SOURCE_REPO="${3:-${TEACHANY_REPO:-$HOME/CodeBuddy/一次函数/teachany-opensource}}"

if [ -z "$COURSE_ID" ]; then
  echo "用法: $0 <course-id> [courseware-repo] [source-repo]"
  echo "例:   $0 hist-m-greece-rome"
  exit 1
fi

TARGET_DIR="$COURSEWARE_REPO/community/$COURSE_ID"
SOURCE_DIR="$SOURCE_REPO/community/$COURSE_ID"
COURSE_URL="https://weponusa.github.io/teachany-courseware/community/$COURSE_ID/"
GALLERY_URL="https://weponusa.github.io/teachany/"

echo "═══════════════════════════════════════════════"
echo "  TeachAny Auto-Publish v2.1 · 双仓库"
echo "═══════════════════════════════════════════════"
echo "  Course ID:       $COURSE_ID"
echo "  Courseware repo: $COURSEWARE_REPO"
echo "  Source repo:     $SOURCE_REPO"
echo "  Target:          $TARGET_DIR"
echo

if [ ! -d "$COURSEWARE_REPO/.git" ]; then
  echo "❌ 课件仓库不存在或不是 Git 仓库: $COURSEWARE_REPO"
  exit 1
fi

# Step 1: 确保真实课件在 courseware 仓库
if [ ! -d "$TARGET_DIR" ]; then
  if [ -d "$SOURCE_DIR" ]; then
    echo "[1/5] 从主仓库同步课件到 courseware..."
    mkdir -p "$COURSEWARE_REPO/community"
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    echo "  ✅ 已复制: $SOURCE_DIR → $TARGET_DIR"
  else
    echo "❌ 找不到课件目录："
    echo "   - $TARGET_DIR"
    echo "   - $SOURCE_DIR"
    exit 1
  fi
else
  echo "[1/5] 课件已在 courseware 仓库"
fi

MISSING=""
[ ! -f "$TARGET_DIR/index.html" ] && MISSING="$MISSING index.html"
[ ! -f "$TARGET_DIR/manifest.json" ] && MISSING="$MISSING manifest.json"
if [ -n "$MISSING" ]; then
  echo "❌ 缺少必要文件:$MISSING"
  exit 1
fi

if grep -q "location.replace" "$TARGET_DIR/index.html" 2>/dev/null; then
  HTML_SIZE=$(wc -c < "$TARGET_DIR/index.html")
  if [ "$HTML_SIZE" -lt 2000 ]; then
    echo "❌ index.html 是 redirect 页面，不是真实课件内容"
    exit 1
  fi
fi

echo "  ✅ 课件实体校验通过"
echo

# Step 2: rebuild-index
cd "$COURSEWARE_REPO"
echo "[2/5] rebuild-index（注册课件 + 更新索引）..."
if python3 scripts/rebuild-index.py 2>&1 | tee /tmp/rebuild_out.txt | tail -12 | sed 's/^/    /'; then
  echo "  ✅ rebuild-index 完成"
else
  echo "  ❌ rebuild-index 失败"
  exit 1
fi

echo

echo "[3/5] 防 404 链接校验..."
if python3 scripts/check-courseware-links.py --id "$COURSE_ID" 2>&1 | sed 's/^/    /'; then
  echo "  ✅ 链接校验通过"
else
  echo "  ❌ 链接校验失败"
  exit 1
fi

echo

echo "[4/5] git commit + push..."
if [ -z "$(git status --short)" ]; then
  echo "  ⏭️  没有变更，跳过推送"
else
  git add -A
  CHANGES=$(git status --cached --short | wc -l | tr -d ' ')
  echo "  📝 $CHANGES 个文件变更"
  git commit -m "feat: 新增课件 $COURSE_ID"

  if ! git push origin main 2>&1; then
    echo "  🔄 push 失败，尝试 pull --rebase..."
    git pull origin main --rebase
    git push origin main
  fi
  echo "  ✅ origin 推送成功"

  if git remote get-url gitee >/dev/null 2>&1; then
    echo "  📤 push gitee（可选）..."
    git push gitee main 2>&1 | tail -2 || echo "  ⚠️ gitee 推送失败，不影响 GitHub Pages"
  fi
fi

echo

echo "[5/5] 验证线上 URL..."
echo "  ⏳ 等待 GitHub Pages 部署（60秒）..."
sleep 60
CODE=$(curl -sI -L --max-time 10 "$COURSE_URL" 2>/dev/null | head -1 | grep -oE "[0-9]{3}" | head -1)

echo
echo "═══════════════════════════════════════════════"
if [ "$CODE" = "200" ]; then
  echo "  ✅ 发布完成！课件实体已上线 (HTTP 200)"
else
  echo "  ⏳ 已推送，Pages 仍在部署中 (HTTP $CODE)"
  echo "  ⚠️ URL 返回 200 前不得声称发布完成。"
fi
echo "  📚 课件 URL: $COURSE_URL"
echo "  📋 Gallery: $GALLERY_URL"
echo "═══════════════════════════════════════════════"
