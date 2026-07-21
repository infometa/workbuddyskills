#!/usr/bin/env bash
# pack.sh — 把 aipage 工作目录打包成符合 aicanvas McpImport 规范的 .aipage 文件（zip 格式，.aipage 后缀）。
#
# Usage:
#   pack.sh <src_dir> [<out_path>]
#
# Behaviors:
#   1. 校验 <src_dir>/index.html 与 <src_dir>/manifest.json 存在
#   2. 扁平化打包（cd 到 src_dir 再 zip，zip 内无顶层目录）
#   3. 排除 macOS / Windows 打包副产物，避免触发 aicanvas 白名单拒绝
#   4. 输出产物强制使用 .aipage 后缀（若 <out_path> 以 .zip 或 .page 结尾会被替换为 .aipage；
#      若无 .aipage 后缀则自动追加）
#   5. 若未显式指定 <out_path>，默认取 <src_dir> 的 basename 作为产物名，
#      输出到 <src_dir> 的父目录下，即 "<parent>/<basename(src_dir)>.aipage"
#   6. 输出结构化 stdout（供调用方正则解析）：
#        AIPAGE_PATH=...
#        AIPAGE_SIZE=...
#        AIPAGE_MD5=...
#
# Exit codes:
#   0  成功
#   2  参数错误
#   3  产物结构不合规
#   4  打包或校验工具缺失

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: pack.sh <src_dir> [<out_path>]

  <src_dir>   源目录，必须包含 index.html 和 manifest.json
  <out_path>  输出文件的绝对/相对路径（可选，后缀会被强制规范为 .aipage）
              未指定时默认：<src_dir 的父目录>/<src_dir 的 basename>.aipage

示例:
  pack.sh /tmp/aipage_1714000000 /tmp/aipage.aipage
  pack.sh /tmp/清华大学            # 产物自动为 /tmp/清华大学.aipage
EOF
  exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage

SRC="$1"
OUT="${2:-}"

# ---- 结构校验（先校验 SRC 合法，再据此推导默认 OUT）----
[[ -d "$SRC" ]] || { echo "pack.sh: src_dir not a directory: $SRC" >&2; exit 3; }
[[ -f "$SRC/index.html" ]]   || { echo "pack.sh: missing $SRC/index.html" >&2; exit 3; }
[[ -f "$SRC/manifest.json" ]] || { echo "pack.sh: missing $SRC/manifest.json" >&2; exit 3; }

# ---- 未指定 OUT 时：取 <src_dir> 的 basename 作为产物名 ----
# 设计：
#   - pack.sh 只能看到 index.html（已被上游重命名），无法直接拿到"原始 HTML 文件名"；
#   - 约定由调用方（如 prepare-pack.sh）把"原始 HTML 文件名（去 .html）"作为 <src_dir>
#     的 basename 传下来，本脚本据此推导默认产物名。
if [[ -z "$OUT" ]]; then
  SRC_ABS="$(cd "$SRC" && pwd)"
  PARENT_DIR="$(dirname "$SRC_ABS")"
  BASE_NAME="$(basename "$SRC_ABS")"
  OUT="${PARENT_DIR}/${BASE_NAME}.aipage"
fi

# ---- 规范化输出后缀为 .aipage ----
# 规则：
#   - 以 .aipage 结尾 → 保持
#   - 以 .page 结尾   → 替换为 .aipage
#   - 以 .zip 结尾    → 替换为 .aipage
#   - 其它情况（无后缀或其它后缀）→ 追加 .aipage
case "$OUT" in
  *.aipage) ;;
  *.page)   OUT="${OUT%.page}.aipage" ;;
  *.zip)    OUT="${OUT%.zip}.aipage" ;;
  *)        OUT="${OUT}.aipage" ;;
esac

# ---- 依赖检查 ----
command -v zip >/dev/null 2>&1 || { echo "pack.sh: zip command not found" >&2; exit 4; }

# md5: macOS 用 `md5 -q`，Linux 用 `md5sum`
md5_of() {
  if command -v md5 >/dev/null 2>&1; then
    md5 -q "$1"
  elif command -v md5sum >/dev/null 2>&1; then
    md5sum "$1" | awk '{print $1}'
  else
    echo "pack.sh: neither md5 nor md5sum found" >&2
    exit 4
  fi
}

# size: macOS 用 `stat -f%z`，Linux 用 `stat -c%s`
size_of() {
  if stat -f%z "$1" >/dev/null 2>&1; then
    stat -f%z "$1"
  else
    stat -c%s "$1"
  fi
}

# 轻量校验 manifest.json 是合法 JSON（若系统有 python3）
if command -v python3 >/dev/null 2>&1; then
  if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SRC/manifest.json" 2>/dev/null; then
    echo "pack.sh: invalid JSON in manifest.json" >&2
    exit 3
  fi
fi

# 轻量校验：html 不应含有 http(s) 协议的 js/css 外链（仅告警，不拦截）
if grep -REho 'src=["'\''"]https?://[^"'\'' ]+\.js' "$SRC"/*.html 2>/dev/null | head -1 | grep -q .; then
  echo "pack.sh: WARNING html references remote .js via http(s), may fail to render offline" >&2
fi
if grep -REho 'href=["'\''"]https?://[^"'\'' ]+\.css' "$SRC"/*.html 2>/dev/null | head -1 | grep -q .; then
  echo "pack.sh: WARNING html references remote .css via http(s), may fail to render offline" >&2
fi

# ---- 准备输出路径 ----
OUT_DIR="$(dirname "$OUT")"
mkdir -p "$OUT_DIR"
rm -f "$OUT"

# ---- 打包（扁平化 + 剥离副产物）----
# 说明：
#   - 产物使用 .aipage 后缀，但内部仍是标准 zip 格式（aicanvas McpImport 兼容）
#   - 用子 shell + cd，避免污染调用方 cwd
#   - -q 静默，-r 递归
#   - -x 排除 macOS Finder zip 产生的 __MACOSX/、AppleDouble ._*、.DS_Store
#   - 以及 Windows 缩略图 Thumbs.db
(
  cd "$SRC"
  zip -qr "$OUT" . \
    -x "__MACOSX/*"      "*/__MACOSX/*" \
    -x ".DS_Store"       "*/.DS_Store"  \
    -x "._*"             "*/._*"        \
    -x "Thumbs.db"       "*/Thumbs.db"
)

[[ -f "$OUT" ]] || { echo "pack.sh: zip produced no output: $OUT" >&2; exit 4; }

SIZE="$(size_of "$OUT")"
MD5="$(md5_of "$OUT")"

# ---- 结构化输出（供上层 agent 解析）----
printf 'AIPAGE_PATH=%s\n' "$OUT"
printf 'AIPAGE_SIZE=%s\n' "$SIZE"
printf 'AIPAGE_MD5=%s\n'  "$MD5"
