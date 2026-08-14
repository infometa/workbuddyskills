#!/usr/bin/env bash
# ============================================================
# agent-boost remote-exec — 包装 page-deliver 的 anydev remote-exec
#
# 核心解决：用 Python json.dumps() 构造请求 JSON，避免 shell 字符串
# 拼接导致的转义地狱（嵌套引号、$(...) 误展开、JSON-in-JSON 断裂）。
#
# 用法:
#   PD="/path/to/page-deliver.js" \
#   PROJECT_DIR="/path/to/project" \
#   CMD="echo hello" \
#   bash remote-exec.sh              # 输出完整 JSON 信封
#   bash remote-exec.sh --stdout      # 仅输出 data.stdout（命令的标准输出）
#
# 可选环境变量:
#   PD_SKILL_DIR  page-deliver skill 目录（帮助 anydev 快速定位 any CLI 二进制；
#                 未设置时 page-deliver 内部 resolveInternalSkillDir() 自动遍历目录树发现）
#
# CMD 中的 \$(...) 会在容器侧执行（本地 \$ 转义为字面 $）。
# ============================================================
set -euo pipefail

# 模式选择
STDOUT_ONLY=false
if [ "${1:-}" = "--stdout" ]; then
    STDOUT_ONLY=true
    shift
fi

: "${PD:?PD (page-deliver.js path) is required}"
: "${PROJECT_DIR:?PROJECT_DIR is required}"
: "${CMD:?CMD is required}"

# Python 构造 JSON → 管道传给 node
# 关键：CMD 通过环境变量传递，json.dumps() 自动处理所有转义
# PD_SKILL_DIR 作为可选 hint 透传给 node 进程环境（page-deliver 内部 resolveInternalSkillDir() 会读取）
RAW=$(PROJECT_DIR="$PROJECT_DIR" PD_SKILL_DIR="${PD_SKILL_DIR:-}" CMD="$CMD" python3 << 'PYEOF' | node "$PD" anydev remote-exec --input -
import json, os
print(json.dumps({
    "projectDir": os.environ["PROJECT_DIR"],
    "cmd": os.environ["CMD"],
}))
PYEOF
)

if [ "$STDOUT_ONLY" = "true" ]; then
    # 从信封中提取 data.stdout
    echo "$RAW" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('stdout',''),end='')"
else
    echo "$RAW"
fi
