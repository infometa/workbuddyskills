#!/bin/bash
# 共享工具函数库
# 所有 Skill 脚本可以 source 这个文件使用通用函数

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印信息函数
info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# 检查命令是否存在
check_command() {
    local cmd=$1
    if ! command -v "$cmd" &> /dev/null; then
        error "Command '$cmd' not found. Please install it first."
        return 1
    fi
    return 0
}

# 检查多个命令
check_commands() {
    local missing=()
    for cmd in "$@"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing required commands: ${missing[*]}"
        return 1
    fi
    return 0
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        return 1
    fi
    return 0
}

# 检查操作系统
check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$NAME $VERSION"
    elif [ -f /etc/redhat-release ]; then
        cat /etc/redhat-release
    else
        echo "Unknown OS"
    fi
}

# 获取内核版本
get_kernel_version() {
    uname -r
}

# 格式化输出表格
print_table_header() {
    local format=$1
    shift
    printf "$format\n" "$@"
    printf '%*s\n' "${COLUMNS:-80}" '' | tr ' ' '-'
}

# 确认操作
confirm() {
    local prompt=${1:-"Continue?"}
    read -p "$prompt [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# 日志函数
log() {
    local level=$1
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $*"
}

# 安全执行命令并捕获输出
safe_exec() {
    local output
    local exit_code
    
    output=$("$@" 2>&1)
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        error "Command failed: $*"
        error "Output: $output"
        return $exit_code
    fi
    
    echo "$output"
    return 0
}

# 检查文件是否存在
check_file() {
    local file=$1
    if [ ! -f "$file" ]; then
        error "File not found: $file"
        return 1
    fi
    return 0
}

# 检查目录是否存在
check_dir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        error "Directory not found: $dir"
        return 1
    fi
    return 0
}

# 创建临时目录
create_temp_dir() {
    local prefix=${1:-"skill"}
    mktemp -d "/tmp/${prefix}.XXXXXX"
}

# 清理临时文件
cleanup_temp() {
    local dir=$1
    if [ -d "$dir" ] && [[ "$dir" == /tmp/* ]]; then
        rm -rf "$dir"
    fi
}

# 获取进程信息
get_process_info() {
    local pid=$1
    if [ -d "/proc/$pid" ]; then
        local comm=$(cat "/proc/$pid/comm" 2>/dev/null)
        local cmdline=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null)
        echo "PID: $pid, Name: $comm, Cmdline: $cmdline"
    else
        error "Process $pid not found"
        return 1
    fi
}

# 人性化显示大小
human_size() {
    local size=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0
    
    while [ "$size" -ge 1024 ] && [ "$unit" -lt 4 ]; do
        size=$((size / 1024))
        unit=$((unit + 1))
    done
    
    echo "${size}${units[$unit]}"
}
