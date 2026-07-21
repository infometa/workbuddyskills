#!/usr/bin/env bash
# ============================================================
# TeachAny Image Count Checker (B-3a)
# ============================================================
# 轻量检测：课件是否满足"至少 3 张 AI 生成图片"。
# 用法：
#   bash check_images.sh <课件目录>
# 退出码：
#   0 = 合规（≥3 张且 HTML 引用 ≥3 次）
#   1 = 不合规
# ============================================================

COURSE_DIR="${1:-.}"
HTML="$COURSE_DIR/index.html"

if [ ! -f "$HTML" ]; then
  echo "❌ 未找到 $HTML"
  exit 1
fi

img_files=$(find "$COURSE_DIR" -maxdepth 4 \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) 2>/dev/null | wc -l | tr -d ' ')
img_refs=$(grep -ocE "<img[^>]+src=['\"][^'\"]+['\"]" "$HTML" 2>/dev/null)

echo "图片文件数: $img_files"
echo "HTML img 引用数: $img_refs"

if [ "$img_files" -ge 3 ] && [ "$img_refs" -ge 3 ]; then
  echo "✅ B-3a PASS"
  exit 0
else
  echo "❌ B-3a FAIL（需 ≥3 张图片 + HTML 引用 ≥3 次）"
  echo ""
  echo "建议立即用 image_gen 生成 3 张图：" 
  echo "  1) Hero 知识结构信息图 → assets/hero-infographic.png"
  echo "  2) 核心概念可视化 → assets/concept-visualization.png"
  echo "  3) 拓展插图 → assets/extension-illustration.png"
  echo ""
  echo "然后在 HTML 对应 section 里插入："
  echo "  <img src=\"assets/xxx.png\" alt=\"描述\" style=\"width:100%;border-radius:12px\">"
  exit 1
fi
