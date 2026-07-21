#!/bin/bash
# pack.sh
# 用途：把 skill 当前目录打包成一份 zip，用于分发到 WorkBuddy / SkillHub 等平台或外部测试机。
# 用法：在 skill 根目录运行：bash pack.sh
# 不会改动你本地工作区的任何文件，所有操作都在临时目录里完成。

set -e

SKILL_NAME="gaokao-zhiyuan-assistant"
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
STAMP=$(date +%Y%m%d-%H%M%S)

TMP_DIR=$(mktemp -d)
TARGET_DIR="$TMP_DIR/$SKILL_NAME"

echo "============================================"
echo "  打包脚本启动"
echo "  根目录：$ROOT_DIR"
echo "  时间戳：$STAMP"
echo "============================================"

echo "📦 复制 skill 到临时目录：$TARGET_DIR"
mkdir -p "$TARGET_DIR"
# 排除 .git / node_modules / 已有 zip / macOS 元数据 / 点文件（.gitignore 等会被 SkillHub 校验拒绝）/ 打包脚本自身
rsync -a \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='.gitattributes' \
  --exclude='node_modules' \
  --exclude='*.zip' \
  --exclude='.DS_Store' \
  --exclude='pack.sh' \
  "$ROOT_DIR/" "$TARGET_DIR/"

echo "📁 打包 zip"
ZIP_NAME="${SKILL_NAME}-${STAMP}.zip"
( cd "$TMP_DIR" && zip -qr "$ZIP_NAME" "$SKILL_NAME" )
mv "$TMP_DIR/$ZIP_NAME" "$ROOT_DIR/"

echo "🧹 清理临时目录"
rm -rf "$TMP_DIR"

echo ""
echo "============================================"
echo "🎉 完成：$ROOT_DIR/$ZIP_NAME"
echo ""
echo "下一步："
echo "  · WorkBuddy → 推到工蜂 main 分支即自动同步。"
echo "  · SkillHub  → 把该 zip 上传到平台，或解压到外部测试机的 .codebuddy/skills/ 下测试。"
echo "============================================"
