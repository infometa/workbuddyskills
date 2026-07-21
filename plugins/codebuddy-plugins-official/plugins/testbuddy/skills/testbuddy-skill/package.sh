#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 技能包源目录（就是当前脚本所在目录）
SOURCE_DIR="${SCRIPT_DIR}"
# 输出目录（打包文件输出到上一级目录）
OUTPUT_DIR="${SCRIPT_DIR}/.."

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印信息
print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 参数验证
if [ -z "$1" ]; then
  print_error "请提供版本号"
  echo "用法: $0 <version>"
  echo "示例: $0 1.5.0"
  exit 1
fi

version=$1

# 验证版本号格式（简单的语义化版本检查）
if ! [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  print_warning "版本号格式不符合语义化版本规范（x.y.z），但继续打包"
fi

# 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
  print_error "技能包源目录不存在: $SOURCE_DIR"
  exit 1
fi

# 检查必要文件是否存在
required_files=("README.md" "SKILL.md")
missing_files=()
for file in "${required_files[@]}"; do
  if [ ! -f "${SOURCE_DIR}/${file}" ]; then
    missing_files+=("$file")
  fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
  print_error "缺少必要文件: ${missing_files[*]}"
  exit 1
fi

# 检查子目录
required_dirs=("references/tools" "references/workflows" "scripts")
missing_dirs=()
for dir in "${required_dirs[@]}"; do
  if [ ! -d "${SOURCE_DIR}/${dir}" ]; then
    missing_dirs+=("$dir")
  fi
done

if [ ${#missing_dirs[@]} -gt 0 ]; then
  print_error "缺少必要目录: ${missing_dirs[*]}"
  exit 1
fi

# 输出包名
PACKAGE_NAME="testbuddy-skill-v${version}.zip"
PACKAGE_PATH="${OUTPUT_DIR}/${PACKAGE_NAME}"

# 开始打包
print_info "开始打包 testbuddy-skill (版本: ${version})"
print_info "源目录: $SOURCE_DIR"
print_info "输出路径: $PACKAGE_PATH"

# 切换到源目录的父目录进行打包，确保tar包内的路径相对简洁
cd "${SOURCE_DIR}/.."

# 获取目录名（用于tar打包）
DIR_NAME=$(basename "${SOURCE_DIR}")

# 如果已存在同名文件，询问是否覆盖
if [ -f "$PACKAGE_PATH" ]; then
  print_warning "文件已存在: $PACKAGE_PATH"
  read -p "是否覆盖？(y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "已取消打包"
    exit 0
  fi
  rm -f "$PACKAGE_PATH"
  print_info "已删除旧文件"
fi

# 执行打包（排除package.sh自身和已有的zip文件）
if zip -r "$PACKAGE_PATH" "${DIR_NAME}/" -x "${DIR_NAME}/package.sh" "${DIR_NAME}/*.zip" "${DIR_NAME}/*.tar.gz"; then
  # 显示打包结果
  file_size=$(du -h "$PACKAGE_PATH" | cut -f1)
  print_info "打包成功！"
  echo "  文件名: $PACKAGE_NAME"
  echo "  文件大小: $file_size"
  echo "  文件路径: $PACKAGE_PATH"

  # 显示包内容统计
  file_count=$(unzip -l "$PACKAGE_PATH" | tail -1 | awk '{print $2}')
  print_info "包含文件数: $file_count"
else
  print_error "打包失败"
  exit 1
fi
