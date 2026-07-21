#!/bin/bash
# 输出格式化工具
# 提供统一的输出格式，支持 JSON、Table、Plain 等格式

# 设置输出格式：json, table, plain
OUTPUT_FORMAT=${OUTPUT_FORMAT:-"plain"}

# JSON 输出
json_output() {
    local data=$1
    if command -v jq &> /dev/null; then
        echo "$data" | jq '.'
    else
        echo "$data"
    fi
}

# 表格输出
table_output() {
    local header=$1
    shift
    local data=("$@")
    
    # 打印表头
    echo "$header"
    echo "${header//?/-}"
    
    # 打印数据
    for row in "${data[@]}"; do
        echo "$row"
    done
}

# Markdown 表格输出
markdown_table() {
    local header=$1
    shift
    local separator=$1
    shift
    local data=("$@")
    
    echo "| $header |"
    echo "| $separator |"
    
    for row in "${data[@]}"; do
        echo "| $row |"
    done
}

# 进度条
progress_bar() {
    local current=$1
    local total=$2
    local width=${3:-50}
    
    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))
    
    printf "\r["
    printf "%${filled}s" '' | tr ' ' '#'
    printf "%${empty}s" '' | tr ' ' '-'
    printf "] %d%%" "$percentage"
}

# 分隔线
separator() {
    local char=${1:-"-"}
    local width=${2:-80}
    printf '%*s\n' "$width" '' | tr ' ' "$char"
}

# 标题
print_title() {
    local title=$1
    local width=${2:-80}
    
    separator "="
    printf "%*s\n" $(((${#title} + width) / 2)) "$title"
    separator "="
}

# 子标题
print_subtitle() {
    local title=$1
    echo ""
    echo "## $title"
    separator "-" 40
}

# Key-Value 输出
kv_output() {
    local key=$1
    local value=$2
    local width=${3:-20}
    
    printf "%-${width}s : %s\n" "$key" "$value"
}

# 列表输出
list_output() {
    local items=("$@")
    local index=1
    
    for item in "${items[@]}"; do
        echo "  $index. $item"
        ((index++))
    done
}

# 树形输出
tree_output() {
    local prefix=$1
    local item=$2
    local is_last=$3
    
    if [ "$is_last" = "true" ]; then
        echo "${prefix}└── $item"
    else
        echo "${prefix}├── $item"
    fi
}

# 状态输出
status_output() {
    local name=$1
    local status=$2
    local width=${3:-40}
    
    local status_icon
    case $status in
        "ok"|"success"|"running")
            status_icon="✓"
            ;;
        "warning"|"degraded")
            status_icon="⚠"
            ;;
        "error"|"failed"|"stopped")
            status_icon="✗"
            ;;
        *)
            status_icon="?"
            ;;
    esac
    
    printf "%-${width}s [%s] %s\n" "$name" "$status_icon" "$status"
}
