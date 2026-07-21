#!/usr/bin/env bash
# resume-assistant · export_pdf.sh
# 路径 A：用 Pandoc 把简历 Markdown 渲染成 PDF
# v0.3.2 新增 · 详见 modes/export.md §五

set -uo pipefail

# ── 参数解析 ────────────────────────────────────────────
VERSION=""
LANG="zh"
THEME="ats-safe"
OUTPUT=""
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "$0")/../../../.." && pwd)}"
SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
    cat <<EOF
用法：
    bash export_pdf.sh --version <id> [--lang zh|en] [--theme ats-safe|modern|compact] [--output <name>]

必填：
    --version <id>     resume-output/ 下的版本目录名（例如 v3_tailor_byte_llm_algo 或 _master）

可选：
    --lang             zh / en（默认 zh）
    --theme            ats-safe / modern / compact（默认 ats-safe · v0.3.2 推荐）
    --output           输出文件名（默认 resume-{lang}-{theme}.pdf）

示例：
    bash export_pdf.sh --version _master --lang zh
    bash export_pdf.sh --version v3_tailor_byte_llm_algo --lang en --theme modern
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version) VERSION="$2"; shift 2;;
        --lang) LANG="$2"; shift 2;;
        --theme) THEME="$2"; shift 2;;
        --output) OUTPUT="$2"; shift 2;;
        --workspace) WORKSPACE_ROOT="$2"; shift 2;;
        -h|--help) usage;;
        *) echo "未知参数：$1"; usage;;
    esac
done

[[ -z "$VERSION" ]] && { echo "❌ --version 必填"; usage; }

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
    echo "   可选：ats-safe / modern / compact"
    exit 3
fi

[[ -z "$OUTPUT" ]] && OUTPUT="resume-$LANG-$THEME.pdf"
OUTPUT_PATH="$WORKSPACE_ROOT/resume-output/$VERSION/$OUTPUT"

# ── 依赖检测（降级链）─────────────────────────────────
# macOS Chrome / Edge / Brave 通常以 .app 包形式存在，CLI 不在 PATH，需单独探测
MAC_CHROME_BIN=""
for p in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    if [[ -x "$p" ]]; then MAC_CHROME_BIN="$p"; break; fi
done

ENGINE=""
if command -v pandoc >/dev/null 2>&1; then
    if command -v wkhtmltopdf >/dev/null 2>&1; then
        ENGINE="wkhtmltopdf"
    elif command -v tectonic >/dev/null 2>&1; then
        ENGINE="tectonic"
    elif command -v chromium >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; then
        ENGINE="chrome-headless"
    elif [[ -n "$MAC_CHROME_BIN" ]]; then
        ENGINE="chrome-headless-mac"
    fi
fi

if [[ -z "$ENGINE" ]]; then
    cat <<EOF
❌ 未检测到 PDF 渲染依赖。请安装其中之一：

macOS:
    brew install pandoc wkhtmltopdf       (推荐 · 30 秒)
    brew install pandoc tectonic          (LaTeX 路线 · 中文需多配置)

Linux (Ubuntu/Debian):
    sudo apt install pandoc wkhtmltopdf

或者改用「路径 B：JSON Resume」：
    python3 scripts/to_json_resume.py --version $VERSION --lang $LANG
    然后用 https://rxresu.me/ 在线选模板出 PDF
EOF
    exit 4
fi

echo "✅ 渲染引擎：pandoc + $ENGINE"
echo "📄 输入：$INPUT_MD"
echo "🎨 主题：$THEME"
echo "📦 输出：$OUTPUT_PATH"
echo ""

# ── 渲染 ─────────────────────────────────────────────────
case "$ENGINE" in
    wkhtmltopdf)
        # pandoc ≥3.0 移除了 --self-contained，统一用 --embed-resources
        pandoc "$INPUT_MD" \
            --from gfm \
            --to html5 \
            --metadata title="Resume" \
            --css "$THEME_CSS" \
            --standalone \
            --embed-resources \
            -o "/tmp/resume-export-$$.html"

        if [[ ! -f "/tmp/resume-export-$$.html" ]]; then
            echo "❌ pandoc HTML 生成失败，请检查 pandoc 版本（需 ≥2.11）"
            exit 5
        fi

        wkhtmltopdf \
            --enable-local-file-access \
            --margin-top 15mm --margin-bottom 15mm \
            --margin-left 15mm --margin-right 15mm \
            --page-size A4 \
            --encoding utf-8 \
            "/tmp/resume-export-$$.html" \
            "$OUTPUT_PATH"

        rm -f "/tmp/resume-export-$$.html"
        ;;
    tectonic)
        pandoc "$INPUT_MD" \
            --from gfm \
            --to pdf \
            --pdf-engine=tectonic \
            -V CJKmainfont="PingFang SC" \
            -V geometry:margin=15mm \
            -o "$OUTPUT_PATH"
        ;;
    chrome-headless|chrome-headless-mac)
        # 用 --embed-resources 把 CSS 内联，确保 Chrome headless 能离线渲染
        pandoc "$INPUT_MD" \
            --from gfm \
            --to html5 \
            --metadata title="Resume" \
            --css "$THEME_CSS" \
            --standalone \
            --embed-resources \
            -o "/tmp/resume-export-$$.html"

        if [[ "$ENGINE" == "chrome-headless-mac" ]]; then
            CHROME_BIN="$MAC_CHROME_BIN"
        else
            CHROME_BIN="$(command -v chromium 2>/dev/null || command -v google-chrome 2>/dev/null)"
        fi

        "$CHROME_BIN" \
            --headless --disable-gpu --no-sandbox \
            --no-pdf-header-footer \
            --print-to-pdf="$OUTPUT_PATH" \
            "file:///tmp/resume-export-$$.html" 2>/dev/null

        rm -f "/tmp/resume-export-$$.html"
        ;;
esac

echo ""
echo "✅ 完成：$OUTPUT_PATH"
echo "   文件大小：$(du -h "$OUTPUT_PATH" | cut -f1)"

# ── 提示更新 manifest ─────────────────────────────────────
MANIFEST="$WORKSPACE_ROOT/resume-output/_manifest.json"
if [[ -f "$MANIFEST" ]]; then
    echo ""
    echo "💡 提醒：请把以下路径加入 _manifest.json.versions[$VERSION].file_paths"
    echo "   resume_pdf_${LANG}_${THEME}: \"resume-output/$VERSION/$OUTPUT\""
fi
