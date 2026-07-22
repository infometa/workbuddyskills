#!/usr/bin/env bash
# pack_and_hash.sh — 技术公益专家团 · 运维专家打包工具
#
# 用途：把技能目录打包为 zip，计算 MD5，并打包材料包。
# 由运维专家（J）在 Phase 5 调用，保证 MD5 计算的确定性（不依赖 LLM 口算）。
#
# 用法：
#   ./pack_and_hash.sh <技能目录> <版本号> <材料目录> <输出目录>
#
# 示例：
#   ./pack_and_hash.sh ./charity-volunteer-tracker 1.0.0 ./materials ~/.workbuddy/skillhub-outputs
#
# 产物（输出到 <输出目录>）：
#   {技能名}-v{版本}.zip          技能包
#   {技能名}-v{版本}.zip.md5      技能包 MD5（单行：md5值  文件名）
#   {技能名}-material-{日期}.zip  材料包（含 test-report.md / social-value-report.md / metadata.md）

set -euo pipefail

SKILL_DIR="${1:?需要技能目录}"
VERSION="${2:?需要版本号}"
MATERIAL_DIR="${3:?需要材料目录（含 test-report.md / social-value-report.md / metadata.md）}"
OUT_DIR="${4:?需要输出目录}"

# 统一转为绝对路径（脚本内部会 cd 到不同目录，相对路径在 cd 后会失效）
SKILL_DIR="$(cd "$SKILL_DIR" && pwd)"
MATERIAL_DIR="$(cd "$MATERIAL_DIR" && pwd)"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

SKILL_NAME="$(basename "$SKILL_DIR")"
DATE="$(date +%Y-%m-%d)"
EXCLUDES=(-x "*.DS_Store" "*/__pycache__/*" "*.pyc" "*/_legacy/*" "*/icons/_drafts/*")

# ── 1. 校验技能目录结构 ──────────────────────────────
if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
  echo "❌ 错误：$SKILL_DIR 下缺少 SKILL.md" >&2
  exit 1
fi

# ── 1.1 校验图标齐备（WorkBuddy Skill 规范要求每个 Skill 必须有图标）──
if [[ ! -f "$SKILL_DIR/icons/icon.png" ]]; then
  echo "❌ 错误：$SKILL_DIR/icons/ 下缺少 icon.png，需先完成 Phase 2.5 图标设计（图标设计专家）" >&2
  exit 1
fi

# ── 2. 校验材料包三件齐全 ────────────────────────────
REQUIRED_MATERIALS=("test-report.md" "social-value-report.md" "metadata.md")
for f in "${REQUIRED_MATERIALS[@]}"; do
  if [[ ! -f "$MATERIAL_DIR/$f" ]]; then
    echo "❌ 错误：材料目录缺少 $f" >&2
    exit 1
  fi
done

# ── 3. 打包技能包 ────────────────────────────────────
SKILL_ZIP="$OUT_DIR/${SKILL_NAME}-v${VERSION}.zip"
rm -f "$SKILL_ZIP"
( cd "$(dirname "$SKILL_DIR")" && zip -r -q "$SKILL_ZIP" "$SKILL_NAME" "${EXCLUDES[@]}" )

# ── 4. 计算 MD5（跨平台：优先 md5sum，回退 md5）──────────
if command -v md5sum >/dev/null 2>&1; then
  MD5="$(md5sum "$SKILL_ZIP" | awk '{print $1}')"
else
  MD5="$(md5 -q "$SKILL_ZIP")"   # macOS
fi
echo "$MD5  ${SKILL_NAME}-v${VERSION}.zip" > "$SKILL_ZIP.md5"

# ── 5. 打包材料包 ────────────────────────────────────
MATERIAL_ZIP="$OUT_DIR/${SKILL_NAME}-material-${DATE}.zip"
rm -f "$MATERIAL_ZIP"
( cd "$MATERIAL_DIR" && zip -q "$MATERIAL_ZIP" "${REQUIRED_MATERIALS[@]}" )

# ── 6. 输出结果（JSON，便于 Agent 解析）─────────────────
cat <<EOF
{
  "skill_zip": "$SKILL_ZIP",
  "skill_md5": "$MD5",
  "material_zip": "$MATERIAL_ZIP",
  "skill_name": "$SKILL_NAME",
  "version": "$VERSION"
}
EOF
