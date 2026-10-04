#!/usr/bin/env bash
# job-search-coaching · export_pdf.sh
# 使用 Pandoc 与本机浏览器或 Tectonic 将简历 Markdown 渲染为 PDF

set -euo pipefail

# ── 参数解析 ────────────────────────────────────────────
VERSION=""
LANG="zh"
THEME="ats-safe"
OUTPUT=""
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$PWD}"
SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
    cat <<EOF
用法：
    bash export_pdf.sh --version <id> [--lang zh|en] [--theme ats-safe] [--output <name>] [--workspace <path>]

必填：
    --version <id>     resume-output/ 下的版本目录名（例如 v3_tailor_byte_llm_algo 或 _master）

可选：
    --lang             zh / en（默认 zh）
    --theme            ats-safe（当前包内唯一主题）
    --output           输出文件名（默认 resume-{lang}-{theme}.pdf，只允许文件名）
    --workspace        工作区根目录（默认当前目录；也可用 WORKSPACE_ROOT）

示例：
    bash export_pdf.sh --version _master --lang zh
    bash export_pdf.sh --version v3_tailor_byte_llm_algo --lang en --theme ats-safe --workspace /path/to/workspace
EOF
    exit 1
}

require_value() {
    [[ $# -ge 2 && -n "${2:-}" ]] || { echo "❌ 参数 $1 缺少值"; exit 1; }
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version) require_value "$@"; VERSION="$2"; shift 2;;
        --lang) require_value "$@"; LANG="$2"; shift 2;;
        --theme) require_value "$@"; THEME="$2"; shift 2;;
        --output) require_value "$@"; OUTPUT="$2"; shift 2;;
        --workspace) require_value "$@"; WORKSPACE_ROOT="$2"; shift 2;;
        -h|--help) usage;;
        *) echo "未知参数：$1"; usage;;
    esac
done

[[ -z "$VERSION" ]] && { echo "❌ --version 必填"; usage; }
[[ "$VERSION" =~ ^[A-Za-z0-9._-]+$ && "$VERSION" != *".."* ]] || { echo "❌ --version 只能包含字母、数字、点、下划线和连字符，且不能包含 .."; exit 1; }
[[ "$LANG" == "zh" || "$LANG" == "en" ]] || { echo "❌ --lang 只支持 zh 或 en"; exit 1; }
[[ "$THEME" == "ats-safe" ]] || { echo "❌ 当前包内只提供 ats-safe 主题"; exit 1; }
if [[ -n "$OUTPUT" ]]; then
    [[ "$OUTPUT" != */* && "$OUTPUT" == *.pdf ]] || { echo "❌ --output 必须是不含路径的 .pdf 文件名"; exit 1; }
fi

# ── 校验输入 ─────────────────────────────────────────────
INPUT_MD="$WORKSPACE_ROOT/resume-output/$VERSION/resume-$LANG.md"
if [[ ! -f "$INPUT_MD" ]]; then
    echo "❌ 找不到输入：$INPUT_MD"
    echo "   请先用 generate / tailor / rewrite 生成对应版本"
    exit 2
fi

THEME_CSS="$SKILL_ROOT/assets/themes/$THEME.css"
if [[ ! -f "$THEME_CSS" ]]; then
    echo "❌ 主题不存在：$THEME_CSS"
    echo "   当前包内可选：ats-safe"
    exit 3
fi

[[ -z "$OUTPUT" ]] && OUTPUT="resume-$LANG-$THEME.pdf"
OUTPUT_PATH="$WORKSPACE_ROOT/resume-output/$VERSION/$OUTPUT"

# ── 依赖检测（降级链）─────────────────────────────────
# macOS / Windows 图形浏览器通常不在 PATH，需单独探测
MAC_CHROME_BIN=""
for p in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    if [[ -x "$p" ]]; then MAC_CHROME_BIN="$p"; break; fi
done

WINDOWS_CHROME_BIN=""
for p in \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
    "/c/Program Files/Microsoft/Edge/Application/msedge.exe" \
    "/c/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"; do
    if [[ -x "$p" ]]; then WINDOWS_CHROME_BIN="$p"; break; fi
done

ENGINE=""
if command -v pandoc >/dev/null 2>&1; then
    if [[ -n "$MAC_CHROME_BIN" ]]; then
        ENGINE="chrome-headless-mac"
    elif [[ -n "$WINDOWS_CHROME_BIN" ]]; then
        ENGINE="chrome-headless-windows"
    elif command -v chromium >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; then
        ENGINE="chrome-headless"
    elif command -v tectonic >/dev/null 2>&1; then
        ENGINE="tectonic"
    fi
fi

if [[ -z "$ENGINE" ]]; then
    cat <<EOF
❌ 未检测到 PDF 渲染依赖。请安装其中之一：

macOS:
    brew install pandoc                   （推荐；另需 Chrome、Edge、Brave 或 Chromium）
    brew install pandoc tectonic          （降级路线；中文字体需额外配置）

Windows:
    安装 Pandoc，并保留 Chrome 或 Edge 的默认安装路径

Linux (Ubuntu/Debian):
    sudo apt install pandoc chromium

或者直接打开 HTML 版本，使用浏览器“打印为 PDF”。
EOF
    exit 4
fi

echo "✅ 渲染引擎：pandoc + $ENGINE"
echo "📄 输入：$INPUT_MD"
echo "🎨 主题：$THEME"
echo "📦 输出：$OUTPUT_PATH"
echo ""

# ── 渲染 ─────────────────────────────────────────────────
TMP_HTML=""
cleanup() {
    [[ -n "$TMP_HTML" && -f "$TMP_HTML" ]] && rm -f "$TMP_HTML"
}
trap cleanup EXIT INT TERM

case "$ENGINE" in
    tectonic)
        pandoc "$INPUT_MD" \
            --from gfm \
            --to pdf \
            --pdf-engine=tectonic \
            -V CJKmainfont="PingFang SC" \
            -V geometry:margin=15mm \
            -o "$OUTPUT_PATH"
        ;;
    chrome-headless|chrome-headless-mac|chrome-headless-windows)
        # 用 --embed-resources 把 CSS 内联，确保 Chrome headless 能离线渲染
        TMP_HTML="$(mktemp "${TMPDIR:-/tmp}/resume-export.XXXXXX.html")"
        pandoc "$INPUT_MD" \
            --from gfm \
            --to html5 \
            --metadata title="" \
            --css "$THEME_CSS" \
            --standalone \
            --embed-resources \
            -o "$TMP_HTML"

        if [[ "$ENGINE" == "chrome-headless-mac" ]]; then
            CHROME_BIN="$MAC_CHROME_BIN"
        elif [[ "$ENGINE" == "chrome-headless-windows" ]]; then
            CHROME_BIN="$WINDOWS_CHROME_BIN"
        else
            CHROME_BIN="$(command -v chromium 2>/dev/null || command -v google-chrome 2>/dev/null)"
        fi

        if [[ "$ENGINE" == "chrome-headless-windows" ]] && command -v cygpath >/dev/null 2>&1; then
            OUTPUT_NATIVE="$(cygpath -w "$OUTPUT_PATH")"
            HTML_URI="file:///$(cygpath -m "$TMP_HTML")"
            MSYS2_ARG_CONV_EXCL="*" "$CHROME_BIN" \
                --headless --disable-gpu --disable-dev-shm-usage --no-sandbox \
                --no-pdf-header-footer \
                --print-to-pdf="$OUTPUT_NATIVE" \
                "$HTML_URI" 2>/dev/null
        else
            "$CHROME_BIN" \
                --headless --disable-gpu --disable-dev-shm-usage --no-sandbox \
                --no-pdf-header-footer \
                --print-to-pdf="$OUTPUT_PATH" \
                "file://$TMP_HTML" 2>/dev/null
        fi
        ;;
esac

if [[ ! -s "$OUTPUT_PATH" ]]; then
    echo "❌ PDF 未成功生成：$OUTPUT_PATH"
    exit 5
fi

echo ""
echo "✅ 完成：$OUTPUT_PATH"
echo "   文件大小：$(du -h "$OUTPUT_PATH" | cut -f1)"
echo "💡 请继续检查页数、联系方式、事实和链接后再投递。"
