#!/usr/bin/env bash
# prepare-pack.sh — 从 output/ 产物一键组装打包目录并生成 zip。
#
#
# Usage:
#   prepare-pack.sh --html <html_path> --title <title> [--output <out_path>]
#
# Examples:
#   prepare-pack.sh --html "output/清华大学.html" --title "清华大学"
#   prepare-pack.sh --html "output/婚礼邀请函.html" --title "婚礼邀请函" --output /tmp/wedding.aipage
#
# Behaviors:
#   1. 创建临时打包目录
#   2. 将 HTML 复制为 index.html（aipage 硬要求）
#   3. 复制同级 assets/ 目录（如果存在）
#   4. 生成 manifest.json（安全转义 title）
#   5. 调用同目录下的 pack.sh 完成打包
#   6. 清理临时目录
#   7. 输出与 pack.sh 一致的三行结构化结果：
#        AIPAGE_PATH=...
#        AIPAGE_SIZE=...
#        AIPAGE_MD5=...
#
# Exit codes:
#   0  成功
#   1  参数错误
#   2  源文件不存在
#   3  pack.sh 失败（透传其退出码）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- 参数解析 ----
HTML_PATH=""
TITLE=""
ZIP_OUT=""

usage() {
  cat >&2 <<'EOF'
Usage: prepare-pack.sh --html <html_path> --title <title> [--output <out_path>]

  --html    步骤 5 产出的 HTML 文件路径（如 output/清华大学.html）
  --title   文档标题（中文主题名，将写入 manifest.json 的 title 字段）
  --output  输出产物路径（可选，默认为 /tmp/<html 文件名去掉 .html>.aipage）

示例:
  prepare-pack.sh --html "output/清华大学.html" --title "清华大学"
  prepare-pack.sh --html "output/婚礼邀请函.html" --title "婚礼邀请函" --output /tmp/wedding.aipage
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --html)   HTML_PATH="$2"; shift 2 ;;
    --title)  TITLE="$2";     shift 2 ;;
    --output) ZIP_OUT="$2";   shift 2 ;;
    --help|-h) usage ;;
    *) echo "prepare-pack.sh: unknown argument: $1" >&2; usage ;;
  esac
done

[[ -n "$HTML_PATH" ]] || { echo "prepare-pack.sh: --html is required" >&2; usage; }
[[ -n "$TITLE" ]]     || { echo "prepare-pack.sh: --title is required" >&2; usage; }
[[ -f "$HTML_PATH" ]] || { echo "prepare-pack.sh: HTML file not found: $HTML_PATH" >&2; exit 2; }

# ---- 默认输出路径 ----
# 默认取 --html 传入的 HTML 文件 basename（去掉 .html 后缀），
# 输出到 /tmp 下，后缀为 .aipage（由 pack.sh 统一规范）。
# 例：--html "output/清华大学.html"  →  /tmp/清华大学.aipage
if [[ -z "$ZIP_OUT" ]]; then
  HTML_BASE="$(basename "$HTML_PATH")"
  # 去掉 .html / .htm 后缀（大小写不敏感）
  case "$HTML_BASE" in
    *.html|*.HTML) HTML_STEM="${HTML_BASE%.*}" ;;
    *.htm|*.HTM)   HTML_STEM="${HTML_BASE%.*}" ;;
    *)             HTML_STEM="$HTML_BASE" ;;
  esac
  ZIP_OUT="/tmp/${HTML_STEM}.aipage"
fi

# ---- 获取 HTML 所在目录（用于查找同级 assets/ ）----
HTML_DIR="$(cd "$(dirname "$HTML_PATH")" && pwd)"

# ---- 创建临时打包目录 ----
PACK_DIR="$(mktemp -d "/tmp/aipage_pack_XXXXXX")"
trap 'rm -rf "$PACK_DIR"' EXIT

# ---- 1) 入口 HTML → index.html ----
cp "$HTML_PATH" "$PACK_DIR/index.html"

# ---- 2) 复制同级 assets/ （Vite 非内联资源）----
if [[ -d "$HTML_DIR/assets" ]]; then
  cp -r "$HTML_DIR/assets" "$PACK_DIR/assets"
fi

# ---- 3) 生成 manifest.json（安全转义 title）----
# 使用 python3 生成 JSON，确保特殊字符（引号、反斜杠、换行等）被正确转义，
# 避免 heredoc 被特殊字符破坏的问题。
if command -v python3 >/dev/null 2>&1; then
  python3 -c "
import json, sys
obj = {'entry': 'index.html', 'title': sys.argv[1], 'version': '1.0'}
print(json.dumps(obj, ensure_ascii=False, indent=2))
" "$TITLE" > "$PACK_DIR/manifest.json"
else
  # fallback: 手动转义双引号和反斜杠
  ESCAPED_TITLE="$(printf '%s' "$TITLE" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  cat > "$PACK_DIR/manifest.json" <<EOF
{
  "entry": "index.html",
  "title": "${ESCAPED_TITLE}",
  "version": "1.0"
}
EOF
fi

# ---- 4) 生成 janus.manifest.json ----
cat > "$PACK_DIR/janus.manifest.json" <<'JEOF'
{"version":"1.0.0","render_engine":"native","scene":""}
JEOF

# ---- 5) 调用 pack.sh 完成打包 ----
bash "$SCRIPT_DIR/pack.sh" "$PACK_DIR" "$ZIP_OUT"
