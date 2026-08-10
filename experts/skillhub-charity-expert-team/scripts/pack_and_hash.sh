#!/usr/bin/env bash
# pack_and_hash.sh — 技术公益专家团 · 运维专家打包工具
#
# 用途：把技能目录 或 Agent 型专家包目录打包为 zip，计算 MD5，并打包材料包。
# 由运维专家（J）在 Phase 5 调用，保证 MD5 计算的确定性（不依赖 LLM 口算）。
# 自动识别目录结构类型（Skill / Agent 专家），分别做对应的必需文件校验。
#
# 用法：
#   ./pack_and_hash.sh <目标目录> <版本号> <材料目录> <输出目录>
#
# 示例：
#   ./pack_and_hash.sh ./charity-volunteer-tracker 1.0.0 ./materials ~/.workbuddy/skillhub-outputs   # Skill
#   ./pack_and_hash.sh ./my-charity-expert 1.0.0 ./materials ~/.workbuddy/skillhub-outputs           # Agent 专家
#
# 目录类型判定（自动识别，无需额外传参）：
#   Skill 目录：根目录存在 SKILL.md，必需视觉资产为 icons/icon.png
#   Agent 专家目录：根目录存在 .workbuddy-plugin/plugin.json，必需视觉资产为 avatars/expert.png
#   两者都不存在 → 报错中止（无法识别目录类型）
#   两者都存在 → 报错中止（目录类型有歧义，需人工确认）
#
# 产物（输出到 <输出目录>）：
#   {名称}-v{版本}.zip           主包（≤ 10 MiB，超限会报错中止，不生成产物）
#   {名称}-v{版本}.zip.md5       主包 MD5（单行：md5值  文件名）
#   {名称}-material-{日期}.zip   材料包（含 test-report.md 或 审查报告-*.md / social-value-report.md / metadata.md，≤ 1 MiB）
#
# 大小限制来自 MCP Server 上传接口硬性要求（见 agents/references/skillhub-ops-expert-mcp-protocol.md §四）：
#   skill.zip ≤ 10 MiB，material.zip ≤ 1 MiB，超限直接在打包阶段拦截，避免生成注定会被服务端拒绝的产物。
#
# 打包时自动剔除的过程文件（对内容本身无价值，只是流程中间产物，不应随包上传）：
#   icons/candidates/    图标候选草稿（Skill 模式，图标设计专家产出，仅供用户选稿参考，定稿已复制到 icons/icon.png）
#   avatars/candidates/  头像候选草稿（Agent 专家模式，同上性质，定稿已复制到 avatars/expert.png）
#   icons/_drafts/       候选草稿的历史命名兼容（同上性质）
#   reports/             测试报告/评审报告若误落盘在目标目录内部，同样视为过程物料剔除
#   *_legacy/            历史遗留目录
#   .review-cache/ .review-work/  expert-reviewer 审查过程缓存目录
#   .DS_Store / __pycache__ / *.pyc  系统与缓存文件

set -euo pipefail

TARGET_DIR="${1:?需要目标目录（技能目录 或 Agent 专家包目录）}"
VERSION="${2:?需要版本号}"
MATERIAL_DIR="${3:?需要材料目录（含 test-report.md 或 审查报告-*.md / social-value-report.md / metadata.md）}"
OUT_DIR="${4:?需要输出目录}"

# 统一转为绝对路径（脚本内部会 cd 到不同目录，相对路径在 cd 后会失效）
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
MATERIAL_DIR="$(cd "$MATERIAL_DIR" && pwd)"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

TARGET_NAME="$(basename "$TARGET_DIR")"
DATE="$(date +%Y-%m-%d)"

# ── 0. 识别目录类型（Skill / Agent 专家）──────────────
IS_SKILL=0
IS_AGENT=0
[[ -f "$TARGET_DIR/SKILL.md" ]] && IS_SKILL=1
[[ -f "$TARGET_DIR/.workbuddy-plugin/plugin.json" ]] && IS_AGENT=1

if [[ "$IS_SKILL" -eq 1 && "$IS_AGENT" -eq 1 ]]; then
  echo "❌ 错误：$TARGET_DIR 同时存在 SKILL.md 和 .workbuddy-plugin/plugin.json，目录类型有歧义，需人工确认后再打包" >&2
  exit 1
elif [[ "$IS_SKILL" -eq 0 && "$IS_AGENT" -eq 0 ]]; then
  echo "❌ 错误：$TARGET_DIR 下既无 SKILL.md 也无 .workbuddy-plugin/plugin.json，无法识别目录类型（Skill / Agent 专家）" >&2
  exit 1
elif [[ "$IS_SKILL" -eq 1 ]]; then
  PACKAGE_TYPE="skill"
  VISUAL_ASSET="icons/icon.png"
  CANDIDATES_DIR="icons/candidates"
else
  PACKAGE_TYPE="agent"
  VISUAL_ASSET="avatars/expert.png"
  CANDIDATES_DIR="avatars/candidates"
fi

EXCLUDES=(-x "*.DS_Store" "*/__pycache__/*" "*.pyc" "*/_legacy/*" "*/icons/_drafts/*" "*/icons/candidates/*" "*/avatars/candidates/*" "*/reports/*" "*/.review-cache/*" "*/.review-work/*")

echo "ℹ️  识别到目录类型：$PACKAGE_TYPE（视觉资产：$VISUAL_ASSET）" >&2

# ── 0.1 提示即将剔除的过程文件（仅告知，不阻断）──────────
for stripped_dir in "icons/candidates" "avatars/candidates" "icons/_drafts" "reports" ".review-cache" ".review-work"; do
  if [[ -d "$TARGET_DIR/$stripped_dir" ]]; then
    echo "ℹ️  检测到过程目录 $stripped_dir/，将从主包中剔除（不影响内容本身）" >&2
  fi
done

# ── 1. 校验必需的视觉资产齐备（WorkBuddy 规范要求 Skill/Agent 专家均需有图标/头像）──
if [[ ! -f "$TARGET_DIR/$VISUAL_ASSET" ]]; then
  echo "❌ 错误：$TARGET_DIR 下缺少 $VISUAL_ASSET，需先完成 Phase 2.5 图标/头像设计（图标设计专家）" >&2
  exit 1
fi

# ── 2. 校验材料包三件齐全 ────────────────────────────
# metadata.md / social-value-report.md 两个文件名固定；第三件报告文件名因产出物类型而异：
#   Skill 模式：test-report.md（安全测试专家 skill-tester 报告重命名而来）
#   Agent 专家模式：test-report.md（expert-reviewer 审查报告重命名而来，命名规则不变，内容语义不同）
# 二者在 material.zip 内的固定文件名保持一致（均为 test-report.md），便于 MCP 上传接口沿用同一套三件套校验规则。
REQUIRED_MATERIALS=("test-report.md" "social-value-report.md" "metadata.md")
for f in "${REQUIRED_MATERIALS[@]}"; do
  if [[ ! -f "$MATERIAL_DIR/$f" ]]; then
    echo "❌ 错误：材料目录缺少 $f" >&2
    exit 1
  fi
done

# ── 3. 打包主包 ────────────────────────────────────
MAIN_ZIP="$OUT_DIR/${TARGET_NAME}-v${VERSION}.zip"
rm -f "$MAIN_ZIP"
( cd "$(dirname "$TARGET_DIR")" && zip -r -q "$MAIN_ZIP" "$TARGET_NAME" "${EXCLUDES[@]}" )

# ── 3.1 校验主包大小（MCP 上传硬性限制：≤ 10 MiB）──────
MAIN_ZIP_SIZE=$(wc -c < "$MAIN_ZIP" | tr -d ' ')
MAIN_ZIP_LIMIT=$((10 * 1024 * 1024))
if [[ "$MAIN_ZIP_SIZE" -gt "$MAIN_ZIP_LIMIT" ]]; then
  echo "❌ 错误：主包 $MAIN_ZIP 大小 $MAIN_ZIP_SIZE 字节，超出 MCP 上传限制 10 MiB（$MAIN_ZIP_LIMIT 字节），需精简内容后重新打包" >&2
  rm -f "$MAIN_ZIP" "$MAIN_ZIP.md5"
  exit 1
fi

# ── 4. 计算 MD5（跨平台：优先 md5sum，回退 md5）──────────
if command -v md5sum >/dev/null 2>&1; then
  MD5="$(md5sum "$MAIN_ZIP" | awk '{print $1}')"
  MD5_CMD="md5sum"
else
  MD5="$(md5 -q "$MAIN_ZIP")"   # macOS
  MD5_CMD="md5"
fi
echo "$MD5  ${TARGET_NAME}-v${VERSION}.zip" > "$MAIN_ZIP.md5"

# ── 5. 打包材料包 ────────────────────────────────────
MATERIAL_ZIP="$OUT_DIR/${TARGET_NAME}-material-${DATE}.zip"
rm -f "$MATERIAL_ZIP"
( cd "$MATERIAL_DIR" && zip -q "$MATERIAL_ZIP" "${REQUIRED_MATERIALS[@]}" )

# ── 5.1 校验材料包大小（MCP 上传硬性限制：≤ 1 MiB）───────
MATERIAL_ZIP_SIZE=$(wc -c < "$MATERIAL_ZIP" | tr -d ' ')
MATERIAL_ZIP_LIMIT=$((1 * 1024 * 1024))
if [[ "$MATERIAL_ZIP_SIZE" -gt "$MATERIAL_ZIP_LIMIT" ]]; then
  echo "❌ 错误：材料包 $MATERIAL_ZIP 大小 $MATERIAL_ZIP_SIZE 字节，超出 MCP 上传限制 1 MiB（$MATERIAL_ZIP_LIMIT 字节），需精简测试/评审报告内容后重新打包" >&2
  rm -f "$MAIN_ZIP" "$MAIN_ZIP.md5" "$MATERIAL_ZIP"
  exit 1
fi

# ── 5.2 计算材料包 MD5（request_upload 的 material_md5 参数需要）──
if [[ "$MD5_CMD" == "md5sum" ]]; then
  MATERIAL_MD5="$(md5sum "$MATERIAL_ZIP" | awk '{print $1}')"
else
  MATERIAL_MD5="$(md5 -q "$MATERIAL_ZIP")"
fi
echo "$MATERIAL_MD5  ${TARGET_NAME}-material-${DATE}.zip" > "$MATERIAL_ZIP.md5"

# ── 6. 输出结果（JSON，便于 Agent 解析）─────────────────
# 字段名保留 skill_zip/skill_md5 等历史命名，供运维专家 request_upload 调用直接沿用（
# request_upload 的 skill_name/skill_md5 参数对 Skill 和 Agent 专家包均通用，是协议既定字段名，不因产出物类型改名）。
cat <<EOF
{
  "package_type": "$PACKAGE_TYPE",
  "skill_zip": "$MAIN_ZIP",
  "skill_md5": "$MD5",
  "skill_zip_size_bytes": $MAIN_ZIP_SIZE,
  "material_zip": "$MATERIAL_ZIP",
  "material_md5": "$MATERIAL_MD5",
  "material_zip_size_bytes": $MATERIAL_ZIP_SIZE,
  "skill_name": "$TARGET_NAME",
  "version": "$VERSION"
}
EOF
