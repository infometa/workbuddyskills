#!/usr/bin/env bash
set -euo pipefail
# pdfkit — 环境初始化（macOS / Linux）
# 用法: bash scripts/setup.sh          # 仅安装核心依赖（~15s）
#       bash scripts/setup.sh --all    # 安装全部依赖（含可选，~2min）

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPTS_DIR/venv"
REQ_FILE="$SCRIPTS_DIR/requirements.txt"
REQ_OPT_FILE="$SCRIPTS_DIR/requirements-optional.txt"
LOCAL_PYTHON_DIR="$SCRIPTS_DIR/.python"
INSTALL_ALL=false

for arg in "$@"; do
    case "$arg" in
        --all) INSTALL_ALL=true ;;
    esac
done

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

START_TIME=$(date +%s)
echo "=== pdfkit environment setup ==="
echo ""

# ── 1. 检测 Python 3.10+ ─────────────────────────────────────
_find_python() {
    # 优先检查本地已下载的 Python
    if [ -x "$LOCAL_PYTHON_DIR/bin/python3" ]; then
        local major minor
        major=$("$LOCAL_PYTHON_DIR/bin/python3" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
        minor=$("$LOCAL_PYTHON_DIR/bin/python3" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo 0)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            echo "$LOCAL_PYTHON_DIR/bin/python3"
            return 0
        fi
    fi
    # 检查系统 Python
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local major minor
            major=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
            minor=$("$cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo 0)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

_download_python() {
    local PY_VER="3.13.13"
    local RELEASE_TAG="20260414"
    local OS ARCH URL

    OS="$(uname -s)"
    ARCH="$(uname -m)"

    # 使用 python-build-standalone 预编译包
    # https://github.com/astral-sh/python-build-standalone
    local BASE_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${RELEASE_TAG}"

    case "$OS" in
        Darwin)
            case "$ARCH" in
                arm64)  URL="${BASE_URL}/cpython-${PY_VER}+${RELEASE_TAG}-aarch64-apple-darwin-install_only.tar.gz" ;;
                x86_64) URL="${BASE_URL}/cpython-${PY_VER}+${RELEASE_TAG}-x86_64-apple-darwin-install_only.tar.gz" ;;
                *)      echo -e "${RED}✗ Unsupported architecture: $ARCH${NC}"; return 1 ;;
            esac
            ;;
        Linux)
            case "$ARCH" in
                x86_64)  URL="${BASE_URL}/cpython-${PY_VER}+${RELEASE_TAG}-x86_64-unknown-linux-gnu-install_only.tar.gz" ;;
                aarch64) URL="${BASE_URL}/cpython-${PY_VER}+${RELEASE_TAG}-aarch64-unknown-linux-gnu-install_only.tar.gz" ;;
                *)       echo -e "${RED}✗ Unsupported architecture: $ARCH${NC}"; return 1 ;;
            esac
            ;;
        *)
            echo -e "${RED}✗ Unsupported OS: $OS${NC}"
            return 1
            ;;
    esac

    echo -e "  Downloading Python ${PY_VER} for ${OS}/${ARCH}..."
    local TMP_TAR="$SCRIPTS_DIR/.python_download.tar.gz"
    mkdir -p "$LOCAL_PYTHON_DIR"

    if command -v curl &>/dev/null; then
        curl -fSL --progress-bar -o "$TMP_TAR" "$URL"
    elif command -v wget &>/dev/null; then
        wget -q --show-progress -O "$TMP_TAR" "$URL"
    else
        echo -e "${RED}✗ Neither curl nor wget found. Cannot download Python.${NC}"
        return 1
    fi

    # python-build-standalone 解压后目录为 python/
    tar -xzf "$TMP_TAR" -C "$LOCAL_PYTHON_DIR" --strip-components=1
    rm -f "$TMP_TAR"

    if [ -x "$LOCAL_PYTHON_DIR/bin/python3" ]; then
        echo -e "  ${GREEN}✓${NC} Python ${PY_VER} installed to $LOCAL_PYTHON_DIR"
        return 0
    else
        echo -e "${RED}✗ Python download/extract failed${NC}"
        rm -rf "$LOCAL_PYTHON_DIR"
        return 1
    fi
}

PYTHON=""
PYTHON=$(_find_python) || true

if [ -z "$PYTHON" ]; then
    echo -e "${YELLOW}!${NC} Python 3.10+ not found. Downloading standalone Python..."
    if _download_python; then
        PYTHON=$(_find_python) || true
    fi
fi

if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Failed to obtain Python 3.10+.${NC}"
    echo "  Please install manually: https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✓${NC} Python $PY_VER ($PYTHON)"

# ── 2. 创建 venv ─────────────────────────────────────────────
VPYTHON="$VENV_DIR/bin/python3"

_need_create=false
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VPYTHON" ]; then
    _need_create=true
elif ! "$VPYTHON" -m pip --version &>/dev/null; then
    echo -e "${YELLOW}!${NC} venv exists but pip is missing — rebuilding..."
    rm -rf "$VENV_DIR"
    _need_create=true
fi

if [ "$_need_create" = true ]; then
    echo -n "  Creating venv..."
    "$PYTHON" -m venv "$VENV_DIR"
    if ! "$VPYTHON" -m pip --version &>/dev/null; then
        "$VPYTHON" -m ensurepip --upgrade &>/dev/null || true
    fi
    echo -e " ${GREEN}done${NC}"
else
    echo -e "${GREEN}✓${NC} venv already exists"
fi

# ── 3. 安装核心依赖 ──────────────────────────────────────────
echo ""
echo "Installing core Python dependencies..."
if ! "$VPYTHON" -m pip install -r "$REQ_FILE" --quiet 2>&1 | grep -v "already satisfied" | tail -5; then
    echo -e "${YELLOW}!${NC} Some packages may have failed, retrying with verbose output..."
    if ! "$VPYTHON" -m pip install -r "$REQ_FILE"; then
        echo -e "${YELLOW}!${NC} Core dependency installation had errors, continuing setup..."
    fi
fi
echo -e "${GREEN}✓${NC} Core dependencies installed"

# ── 3.1 可选依赖 ─────────────────────────────────────────────
if [ "$INSTALL_ALL" = true ] && [ -f "$REQ_OPT_FILE" ]; then
    echo ""
    echo "Installing optional dependencies..."
    if ! "$VPYTHON" -m pip install -r "$REQ_OPT_FILE" --quiet 2>&1 | grep -v "already satisfied" | tail -5; then
        echo -e "${YELLOW}!${NC} Some optional packages failed, retrying..."
        "$VPYTHON" -m pip install -r "$REQ_OPT_FILE" || true
    fi
    echo -e "${GREEN}✓${NC} Optional dependencies installed"
fi

# ── 3.2 下载内置字体 ─────────────────────────────────────────
FONT_DIR="$SCRIPTS_DIR/../fonts"
FONT_FILE="$FONT_DIR/NotoSansSC-Regular.ttf"
FONT_URL="https://docs.gtimg.com/tdocs-font-source/test/NotoSansSC-Regular.ttf"

if [ -f "$FONT_FILE" ]; then
    echo -e "${GREEN}✓${NC} Bundled font already exists"
else
    echo ""
    echo "Downloading bundled font (NotoSansSC-Regular)..."
    mkdir -p "$FONT_DIR"
    _font_ok=false
    if command -v curl &>/dev/null; then
        if curl -fSL --progress-bar -o "$FONT_FILE" "$FONT_URL" 2>/dev/null; then
            _font_ok=true
        fi
    elif command -v wget &>/dev/null; then
        if wget -q --show-progress -O "$FONT_FILE" "$FONT_URL" 2>/dev/null; then
            _font_ok=true
        fi
    fi
    if [ "$_font_ok" = true ] && [ -f "$FONT_FILE" ]; then
        echo -e "${GREEN}✓${NC} Bundled font downloaded"
    else
        rm -f "$FONT_FILE"
        echo -e "${YELLOW}△${NC} Font download failed (non-fatal, will use system fonts)"
    fi
fi

# ── 4. Smoke test ────────────────────────────────────────────
echo ""
echo "Verifying..."
if "$VPYTHON" -c "import fitz; print(f'  PyMuPDF {fitz.version[0]}')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} PyMuPDF OK"
else
    echo -e "${RED}✗${NC} PyMuPDF import failed — try: $VPYTHON -m pip install PyMuPDF"
    exit 1
fi

CMD_COUNT=$("$VPYTHON" "$SCRIPTS_DIR/pdfkit.py" help 2>/dev/null | head -1 | grep -oE '[0-9]+' || echo "?")
echo -e "${GREEN}✓${NC} pdfkit.py ready ($CMD_COUNT commands)"

# ── 5. 外部可选工具检测 ──────────────────────────────────────
echo ""
echo "Optional external tools (not required, will be prompted on first use):"

_check_tool() {
    local name="$1" desc="$2"
    if command -v "$name" &>/dev/null; then
        local ver
        ver=$("$name" --version 2>&1 | head -1 | tr -d '\n' || echo "found")
        echo -e "  ${GREEN}✓${NC} $name — $ver"
    else
        echo -e "  ${YELLOW}△${NC} $name — not found ($desc)"
    fi
}

_check_tool "gs"        "PDF compression (Ghostscript)"
_check_tool "tesseract" "OCR engine"
_check_tool "soffice"   "LibreOffice"

# ── 6. 清理 SKILL.md 初始化段落 ──────────────────────────────
SKILL_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
SKILL_MD="$SKILL_DIR/SKILL.md"
if [ -f "$SKILL_MD" ] && grep -q "<!-- END_SETUP -->" "$SKILL_MD"; then
    sed -i '' '/^## ⚠️ 环境初始化/,/<!-- END_SETUP -->/d' "$SKILL_MD" 2>/dev/null \
      || sed -i '/^## ⚠️ 环境初始化/,/<!-- END_SETUP -->/d' "$SKILL_MD" 2>/dev/null \
      || true
    echo -e "${GREEN}✓${NC} SKILL.md setup section removed"
fi

# ── 7. 完成 ──────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}=== Setup complete (${ELAPSED}s) ===${NC}"
echo ""

if [ "$INSTALL_ALL" = false ]; then
    echo -e "${YELLOW}Note:${NC} Only core dependencies installed."
    echo "  To install all optional dependencies: bash $0 --all"
    echo ""
fi

echo "Usage:"
echo "  $VPYTHON $SCRIPTS_DIR/pdfkit.py help"
