#!/usr/bin/env bash
# ============================================================
# 腾讯校招可选 JD MCP 自动安装脚本
# 作用：安装 campus-recruit-jd-qa 到 WorkBuddy 本地/受控内测调试环境
# 用法：bash install_mcp.sh
#      bash install_mcp.sh --allow-system-install   # 明确允许脚本调用系统包管理器安装 Python
# ============================================================

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ALLOW_SYSTEM_INSTALL=false
for arg in "$@"; do
    case "$arg" in
        --allow-system-install)
            ALLOW_SYSTEM_INSTALL=true
            ;;
        -h|--help)
            echo "用法: bash scripts/install_mcp.sh [--allow-system-install]"
            echo "默认只使用本机已有 Python；如需脚本调用 brew/apt/dnf/yum 安装 Python，必须显式添加 --allow-system-install。"
            exit 0
            ;;
        *)
            echo "未知参数: $arg"
            echo "用法: bash scripts/install_mcp.sh [--allow-system-install]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  腾讯校招可选 JD MCP 安装向导${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""
echo -e "${YELLOW}说明：本脚本仅用于 WorkBuddy 本地调试/受控内测，会安装依赖并更新本地 JD MCP 配置。${NC}"
echo -e "${YELLOW}普通外部用户不需要安装 MCP；通用流程动态查询官网公告，个人流程信息引导 join.qq.com 校招官网 offer 鹅智能体。${NC}"
echo ""

# ------------------------------------------------------------
# Step 0: 确定脚本所在的 skill 目录
# ------------------------------------------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
JD_MCP_SCRIPT_SRC="$SKILL_DIR/scripts/campus_recruit_jd_qa_mcp.py"

if [ ! -f "$JD_MCP_SCRIPT_SRC" ]; then
    echo -e "${RED}[ERROR] 找不到 JD MCP 脚本: $JD_MCP_SCRIPT_SRC${NC}"
    exit 1
fi

# ------------------------------------------------------------
# Step 1: 确定安装目录
# ------------------------------------------------------------
INSTALL_DIR="$HOME/.codebuddy/skills-runtime/tencent-campus-recruit"
VENV_DIR="$INSTALL_DIR/venv"
JD_MCP_SCRIPT_DEST="$INSTALL_DIR/campus_recruit_jd_qa_mcp.py"

echo -e "${YELLOW}[INFO] 安装位置: $INSTALL_DIR${NC}"
mkdir -p "$INSTALL_DIR"

# ------------------------------------------------------------
# Step 2: 检查 Python（不符合则自动尝试安装）
# ------------------------------------------------------------
echo ""
echo -e "${BLUE}[1/5] 检查 Python 环境...${NC}"

# 查找本机已存在的合适 Python（3.10 ~ 3.13）
find_suitable_python() {
    for candidate in python3.11 python3.10 python3.12 python3.13 python3; do
        if command -v "$candidate" &> /dev/null; then
            ver=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "")
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" = "3" ] && [ "$minor" -ge 10 ] && [ "$minor" -lt 14 ] 2>/dev/null; then
                echo "$(command -v "$candidate")"
                return 0
            fi
        fi
    done
    return 1
}

# 自动安装 Python 3.11（根据系统类型选择方式）
auto_install_python() {
    local os_name
    os_name="$(uname -s)"

    echo -e "${YELLOW}[INFO] 正在尝试为你自动安装 Python 3.11...${NC}"

    if [ "$os_name" = "Darwin" ]; then
        # macOS：使用 Homebrew
        if ! command -v brew &> /dev/null; then
            echo -e "${YELLOW}   未检测到 Homebrew，先安装 Homebrew（国内网络可能需要几分钟）${NC}"
            echo -e "${YELLOW}   若长时间无响应可 Ctrl+C 中断，手动安装后重跑本脚本${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
                echo -e "${RED}   [ERROR] Homebrew 安装失败${NC}"
                return 1
            }
            # 让当前 shell 识别到 brew
            if [ -x "/opt/homebrew/bin/brew" ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [ -x "/usr/local/bin/brew" ]; then
                eval "$(/usr/local/bin/brew shellenv)"
            fi
        fi

        echo -e "${YELLOW}   brew install python@3.11 ...${NC}"
        brew install python@3.11 || {
            echo -e "${RED}   [ERROR] brew install python@3.11 失败${NC}"
            return 1
        }
        # brew 装完后 python3.11 会在 PATH
        return 0

    elif [ "$os_name" = "Linux" ]; then
        # Linux：根据包管理器选择
        if command -v apt-get &> /dev/null; then
            echo -e "${YELLOW}   使用 apt 安装 python3.11（需要 sudo 权限）${NC}"
            # 尝试 deadsnakes PPA（Ubuntu 常用），若失败则退回默认源的 python3
            if command -v add-apt-repository &> /dev/null; then
                sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
            fi
            sudo apt-get update -y && sudo apt-get install -y python3.11 python3.11-venv python3.11-distutils 2>/dev/null \
                || sudo apt-get install -y python3 python3-venv || {
                echo -e "${RED}   [ERROR] apt 安装失败${NC}"
                return 1
            }
            return 0
        elif command -v dnf &> /dev/null; then
            echo -e "${YELLOW}   使用 dnf 安装 python3.11（需要 sudo 权限）${NC}"
            sudo dnf install -y python3.11 || sudo dnf install -y python3 || {
                echo -e "${RED}   [ERROR] dnf 安装失败${NC}"
                return 1
            }
            return 0
        elif command -v yum &> /dev/null; then
            echo -e "${YELLOW}   使用 yum 安装 python3（需要 sudo 权限）${NC}"
            sudo yum install -y python3 || {
                echo -e "${RED}   [ERROR] yum 安装失败${NC}"
                return 1
            }
            return 0
        else
            echo -e "${RED}   [ERROR] 未检测到 apt/dnf/yum，无法自动安装${NC}"
            return 1
        fi
    else
        echo -e "${RED}   [ERROR] 暂不支持自动安装此系统（$os_name）${NC}"
        return 1
    fi
}

safe_remove_venv() {
    case "$VENV_DIR" in
        "$INSTALL_DIR"/venv)
            rm -rf "$VENV_DIR"
            ;;
        *)
            echo -e "${RED}[ERROR] 拒绝删除非预期虚拟环境目录: $VENV_DIR${NC}"
            exit 1
            ;;
    esac
}

PYTHON_BIN="$(find_suitable_python || true)"

if [ -n "$PYTHON_BIN" ]; then
    ver=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}[OK] 找到 Python $ver: $PYTHON_BIN${NC}"
else
    echo -e "${YELLOW}[WARN]  未找到合适的 Python（需要 3.10 ~ 3.13，不支持 3.14+）${NC}"
    echo -e "${YELLOW}   原因：trag SDK 目前不兼容 Python 3.14${NC}"
    echo ""

    if [ "$ALLOW_SYSTEM_INSTALL" != "true" ]; then
        echo -e "${YELLOW}   出于安全考虑，默认不自动调用 curl/brew/apt/dnf/yum 安装系统软件。${NC}"
        echo -e "${YELLOW}   请先手动安装 Python 3.10~3.13，或在受控内测环境中显式运行：${NC}"
        echo -e "${YELLOW}   bash scripts/install_mcp.sh --allow-system-install${NC}"
        exit 1
    fi

    if auto_install_python; then
        # 安装完重新查找
        PYTHON_BIN="$(find_suitable_python || true)"
        if [ -n "$PYTHON_BIN" ]; then
            ver=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            echo -e "${GREEN}[OK] Python 安装成功: Python $ver ($PYTHON_BIN)${NC}"
        else
            echo -e "${RED}[ERROR] 安装完成但仍未检测到合适的 Python，请手动重试${NC}"
            exit 1
        fi
    else
        echo -e "${RED}[ERROR] 自动安装失败${NC}"
        echo -e "${YELLOW}   请手动安装 Python 3.11 后重跑本脚本：${NC}"
        echo -e "${YELLOW}   - Mac:   brew install python@3.11${NC}"
        echo -e "${YELLOW}   - Ubuntu: sudo apt install python3.11 python3.11-venv${NC}"
        echo -e "${YELLOW}   - 其他:  https://www.python.org/downloads/${NC}"
        exit 1
    fi
fi

# ------------------------------------------------------------
# Step 3: 创建虚拟环境 + 安装依赖
# ------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/5] 创建虚拟环境...${NC}"

# 如果已有 venv，校验它的 Python 版本是否在允许范围内
REBUILD_VENV=false
if [ -d "$VENV_DIR" ]; then
    if [ -x "$VENV_DIR/bin/python" ]; then
        old_ver=$("$VENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "unknown")
        old_major=$(echo "$old_ver" | cut -d. -f1)
        old_minor=$(echo "$old_ver" | cut -d. -f2)
        if [ "$old_major" = "3" ] && [ "$old_minor" -ge 10 ] && [ "$old_minor" -lt 14 ] 2>/dev/null; then
            echo -e "${GREEN}[OK] 已有虚拟环境 (Python $old_ver)，继续使用${NC}"
        else
            echo -e "${YELLOW}[WARN]  已有虚拟环境使用 Python $old_ver，不兼容，将重建${NC}"
            REBUILD_VENV=true
        fi
    else
        REBUILD_VENV=true
    fi

    if [ "$REBUILD_VENV" = "true" ]; then
        safe_remove_venv
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo -e "${GREEN}[OK] 虚拟环境已创建${NC}"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

echo ""
echo -e "${BLUE}[3/5] 安装依赖（trag / mcp）...${NC}"

# 腾讯内部 PyPI 镜像源（trag 是腾讯内部 RAG SDK，仅此源有正确的包）
TENCENT_PYPI="https://mirrors.tencent.com/pypi/simple/"
TENCENT_HOST="mirrors.tencent.com"

"$VENV_PIP" install --upgrade pip --quiet

# 先装 mcp（公网源即可）
echo -e "${YELLOW}   安装 mcp...${NC}"
"$VENV_PIP" install --quiet mcp || {
    echo -e "${RED}   [ERROR] mcp 安装失败${NC}"
    exit 1
}

# 再装 trag（必须用腾讯内部源，PyPI 官方同名包不是同一个项目）
echo -e "${YELLOW}   安装 trag（腾讯内部源）...${NC}"
if ! "$VENV_PIP" install --quiet \
        --index-url "$TENCENT_PYPI" \
        --trusted-host "$TENCENT_HOST" \
        trag; then
    echo -e "${RED}   [ERROR] 从腾讯内部源安装 trag 失败${NC}"
    echo -e "${YELLOW}   可能原因：当前网络无法访问 $TENCENT_HOST${NC}"
    echo -e "${YELLOW}   请确认：①已连接腾讯内网或办公网 ②VPN 已开启${NC}"
    exit 1
fi

# 立即验证 trag 是否为正确的包（含 TRAG 或 TRAGClient 入口）
echo -e "${YELLOW}   校验 trag 是否正确...${NC}"
if ! "$VENV_PYTHON" -c "import trag; assert hasattr(trag,'TRAG') or hasattr(trag,'TRAGClient'), 'wrong trag'" 2>/dev/null; then
    echo -e "${RED}   [ERROR] 装到的 trag 不是腾讯 RAG SDK（缺少 TRAG/TRAGClient）${NC}"
    echo -e "${YELLOW}   正在强制从腾讯源重装...${NC}"
    "$VENV_PIP" uninstall -y trag --quiet || true
    "$VENV_PIP" install --quiet --no-cache-dir --force-reinstall \
        --index-url "$TENCENT_PYPI" \
        --trusted-host "$TENCENT_HOST" \
        trag || {
        echo -e "${RED}   [ERROR] 重装失败${NC}"
        exit 1
    }
    # 再次校验
    if ! "$VENV_PYTHON" -c "import trag; assert hasattr(trag,'TRAG') or hasattr(trag,'TRAGClient')" 2>/dev/null; then
        echo -e "${RED}   [ERROR] 仍然拿到错误的 trag 包，请联系管理员检查腾讯内部源配置${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}[OK] 依赖安装完成（trag 已校验为腾讯 RAG SDK）${NC}"

# ------------------------------------------------------------
# Step 4: 部署 MCP 脚本
# ------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/5] 部署 JD MCP 脚本...${NC}"
cp "$JD_MCP_SCRIPT_SRC" "$JD_MCP_SCRIPT_DEST"
echo -e "${GREEN}[OK] JD MCP 脚本已部署到 $JD_MCP_SCRIPT_DEST${NC}"

# ------------------------------------------------------------
# Step 5: 更新 WorkBuddy 本地 MCP 配置
# ------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/5] 更新 WorkBuddy 本地 MCP 配置...${NC}"

CB_CONFIG_DIR="$HOME/.codebuddy"
CB_MCP_JSON="$CB_CONFIG_DIR/mcp.json"

mkdir -p "$CB_CONFIG_DIR"

# 如果 mcp.json 不存在，创建一个空壳
if [ ! -f "$CB_MCP_JSON" ]; then
    echo '{"mcpServers": {}}' > "$CB_MCP_JSON"
    echo -e "${YELLOW}[INFO] 创建了新的 mcp.json${NC}"
fi

# 使用 Python 安全地更新 JSON（保留已有配置）
"$VENV_PYTHON" - "$CB_MCP_JSON" "$VENV_PYTHON" "$JD_MCP_SCRIPT_DEST" <<'PYEOF'
import json, sys, os, shutil

config_path = sys.argv[1]
python_bin = sys.argv[2]
jd_mcp_script = sys.argv[3]

# 读取现有配置
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception:
    config = {}

if 'mcpServers' not in config or not isinstance(config['mcpServers'], dict):
    config['mcpServers'] = {}

# 备份（只保留一份最新备份）
if os.path.exists(config_path):
    backup_path = config_path + '.bak'
    shutil.copy2(config_path, backup_path)
    print(f"[INFO] 已备份原配置到: {backup_path}")

# 删除旧版流程/制度 FAQ MCP 配置，避免外部用户误用过期或不可连接的数据源
config['mcpServers'].pop('campus-recruit-qa', None)

# 添加/更新 campus-recruit-jd-qa（可选在招岗位 JD 知识库）
config['mcpServers']['campus-recruit-jd-qa'] = {
    "command": python_bin,
    "args": [jd_mcp_script]
}

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("[OK] mcp.json 已更新（campus-recruit-jd-qa，可选 JD MCP）")
PYEOF

if [ -z "${TRAG_API_KEY:-}" ]; then
    echo -e "${YELLOW}[WARN]  当前终端未检测到 TRAG_API_KEY。MCP 已注册，但运行时需要由平台或本机环境变量安全注入该值。${NC}"
fi

# ------------------------------------------------------------
# 完成提示
# ------------------------------------------------------------
echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}  [OK] 安装完成！${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo -e "${YELLOW}[WARN]  重要：请完全退出 WorkBuddy 后重新打开，${NC}"
echo -e "${YELLOW}   新的 MCP 服务才会被加载生效。${NC}"
echo ""
echo -e "${BLUE}注册自检：${NC}"
echo -e "  python scripts/check_mcp_registration.py"
echo ""
echo -e "${BLUE}验证方法：${NC}"
echo -e "  1. 重启后问：\"技术方向有哪些岗位？\"（验证可选 campus-recruit-jd-qa）"
echo -e "  2. 流程/制度类问题不验证 MCP；通用流程动态查询官网公告，个人流程信息引导 join.qq.com 校招官网 offer 鹅智能体。"
echo -e "  如国产模型仍看不到 MCP 工具，请优先使用官网岗位脚本兜底。"
echo ""
