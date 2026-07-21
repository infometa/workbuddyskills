#!/usr/bin/env bash
# ============================================================================
# AiCrasher Crash Expert Skill — 自动安装 & MCP Server 注册
# ============================================================================
#
# 功能：
#   1. 检测并安装 aicrasher MCP Python 包（pip install -e .[cli]）
#   2. 检测并注册 aicrasher MCP server 到 CodeBuddy / Claude Code / OpenClaw
#   3. 将 skill 文件安装到 ~/.codebuddy/skills/crash-expert-skill/
#
# 用法：
#   bash setup.sh                 # 自动完成所有安装步骤
#   bash setup.sh --check         # 仅检测安装状态，不执行安装
#   bash setup.sh --install-mcp   # 仅安装 MCP Python 包
#   bash setup.sh --register-mcp  # 仅注册 MCP server
#   bash setup.sh --install-skill # 仅安装 skill 文件
#
# ============================================================================

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}" >&2; }

# ── 路径检测 ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# skill 根目录（脚本的上级目录，即 crash-expert-skill/）
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# 项目根目录就是 skill 根目录（pyproject.toml 在 skill 根目录下）
PROJECT_ROOT="$SKILL_DIR"
# pyproject.toml 路径
PYPROJECT="$PROJECT_ROOT/pyproject.toml"

SKILL_TARGET_DIR="$HOME/.codebuddy/skills/crash-expert-skill"

# ── 状态检测函数 ────────────────────────────────────────────────────────

check_mcp_package_installed() {
    # 检查 aicrasher 包是否已安装
    python3 -c "import aicrasher" 2>/dev/null
}

check_mcp_server_registered() {
    # 检查 MCP server 是否已注册到 CodeBuddy / Claude Code / OpenClaw(mcporter)
    # 使用 detect_cli_tool 的结果来确定检查哪个工具
    local cli_tool
    cli_tool=$(detect_cli_tool)
    
    case "$cli_tool" in
        codebuddy)
            codebuddy mcp list 2>/dev/null | grep -q "aicrasher" 2>/dev/null
            ;;
        claude)
            claude mcp list 2>/dev/null | grep -q "aicrasher" 2>/dev/null
            ;;
        mcporter)
            mcporter list 2>/dev/null | grep -q "aicrasher" 2>/dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

detect_cli_tool() {
    # 检测可用的 CLI 工具，返回工具名称
    # 
    # 优先级:
    # 1. 环境变量 AICRASHER_CLI_TOOL（如果不是 auto）
    # 2. 自动检测: codebuddy > claude > mcporter(OpenClaw)
    
    # 尝试从 .env 文件加载配置
    local env_file=""
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        env_file="$PROJECT_ROOT/.env"
    elif [[ -f "$SKILL_DIR/.env" ]]; then
        env_file="$SKILL_DIR/.env"
    fi
    
    local cli_tool_pref=""
    
    if [[ -n "$env_file" ]]; then
        cli_tool_pref=$(grep -E "^AICRASHER_CLI_TOOL=" "$env_file" 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || true)
    fi
    
    # 也检查环境变量（环境变量优先于文件）
    cli_tool_pref="${AICRASHER_CLI_TOOL:-$cli_tool_pref}"
    
    # 1. 如果明确指定了 CLI 工具且不是 auto，直接返回（需要验证存在性）
    if [[ -n "$cli_tool_pref" && "$cli_tool_pref" != "auto" ]]; then
        case "$cli_tool_pref" in
            codebuddy)
                if command -v codebuddy &>/dev/null; then
                    echo "codebuddy"
                    return 0
                fi
                ;;
            claude)
                if command -v claude &>/dev/null; then
                    echo "claude"
                    return 0
                fi
                ;;
            mcporter)
                if command -v mcporter &>/dev/null; then
                    echo "mcporter"
                    return 0
                fi
                ;;
        esac
        # 指定的工具不存在，继续自动检测
        warn "配置的 CLI 工具 '$cli_tool_pref' 未找到，将自动检测..."
    fi
    
    # 2. 自动检测（默认优先级）
    if command -v codebuddy &>/dev/null; then
        echo "codebuddy"
    elif command -v claude &>/dev/null; then
        echo "claude"
    elif command -v mcporter &>/dev/null; then
        echo "mcporter"
    else
        echo ""
    fi
}

check_skill_installed() {
    # 检查 skill 文件是否已安装到目标位置
    [[ -f "$SKILL_TARGET_DIR/SKILL.md" ]]
}

# ── 安装函数 ────────────────────────────────────────────────────────────

install_mcp_package() {
    info "正在安装 aicrasher MCP Python 包..."

    if [[ ! -f "$PYPROJECT" ]]; then
        error "未找到 pyproject.toml: $PYPROJECT"
        error "请确保在 AiCrasher 项目目录中运行此脚本"
        return 1
    fi

    cd "$PROJECT_ROOT"

    # 检测 pip 命令
    local PIP_CMD
    if command -v pip3 &>/dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &>/dev/null; then
        PIP_CMD="pip"
    elif python3 -m pip --version &>/dev/null; then
        # pip 命令不在 PATH 中，但 python3 -m pip 可用
        PIP_CMD="python3 -m pip"
    else
        # 尝试通过 ensurepip 自动安装 pip
        warn "未找到 pip，尝试通过 ensurepip 自动安装..."
        if python3 -m ensurepip --default-pip 2>/dev/null; then
            success "pip 安装成功（via ensurepip）"
            if command -v pip3 &>/dev/null; then
                PIP_CMD="pip3"
            else
                PIP_CMD="python3 -m pip"
            fi
        else
            error "未找到 pip，且 ensurepip 自动安装失败"
            error "请手动安装 pip 后重试："
            echo ""
            echo "  # Debian/Ubuntu："
            echo "  sudo apt-get install python3-pip"
            echo ""
            echo "  # CentOS/RHEL："
            echo "  sudo yum install python3-pip"
            echo ""
            echo "  # 通用方式："
            echo "  curl https://bootstrap.pypa.io/get-pip.py | python3"
            echo ""
            return 1
        fi
    fi

    # 安装（带 cli 依赖）
    info "执行: $PIP_CMD install -e '.[cli]'"
    $PIP_CMD install -e ".[cli]" || {
        error "MCP 包安装失败"
        return 1
    }

    # 验证安装
    if check_mcp_package_installed; then
        success "aicrasher MCP Python 包安装成功"
    else
        error "安装后验证失败，请检查 Python 环境"
        return 1
    fi
}

register_mcp_server() {
    info "正在注册 aicrasher MCP server..."

    # 优先使用 codebuddy，其次 claude，最后 mcporter(OpenClaw)
    local CLI_CMD=""
    CLI_CMD=$(detect_cli_tool)

    if [[ -z "$CLI_CMD" ]]; then
        warn "未找到 codebuddy、claude 或 mcporter CLI 工具"
        warn "请手动注册 MCP server："
        echo ""
        echo "  # CodeBuddy："
        echo "  codebuddy mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server"
        echo ""
        echo "  # Claude Code："
        echo "  claude mcp add aicrasher -- python3 -m aicrasher.mcp_server"
        echo ""
        echo "  # OpenClaw (mcporter)："
        echo "  mcporter config add aicrasher --stdio \"python3 -m aicrasher.mcp_server\" --scope home"
        echo "  # ⚠️ 注册后需在 mcporter.json 中为 aicrasher 添加 \"lifecycle\": \"keep-alive\""
        echo "  #    （aicrasher 是有状态 MCP Server，需要 daemon 维持进程常驻）"
        echo ""
        return 0
    fi

    # 先尝试移除旧注册（忽略错误）
    if [[ "$CLI_CMD" == "mcporter" ]]; then
        mcporter config remove aicrasher 2>/dev/null || true
    else
        $CLI_CMD mcp remove aicrasher 2>/dev/null || true
    fi

    # 注册 MCP server
    if [[ "$CLI_CMD" == "codebuddy" ]]; then
        info "执行: codebuddy mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server"
        codebuddy mcp add -s user aicrasher -- python3 -m aicrasher.mcp_server || {
            error "MCP server 注册失败"
            return 1
        }
    elif [[ "$CLI_CMD" == "claude" ]]; then
        info "执行: claude mcp add aicrasher -- python3 -m aicrasher.mcp_server"
        claude mcp add aicrasher -- python3 -m aicrasher.mcp_server || {
            error "MCP server 注册失败"
            return 1
        }
    elif [[ "$CLI_CMD" == "mcporter" ]]; then
        info "执行: mcporter config add aicrasher --stdio \"python3 -m aicrasher.mcp_server\" --scope home"
        mcporter config add aicrasher --stdio "python3 -m aicrasher.mcp_server" --scope home || {
            error "MCP server 注册失败"
            return 1
        }

        # aicrasher 是有状态的 MCP Server（session 需跨调用保留），
        # mcporter stdio 默认是 ephemeral 模式（每次调用结束后进程关闭），
        # 必须设置 lifecycle: keep-alive 使 daemon 维持进程常驻。
        info "为 aicrasher 设置 lifecycle: keep-alive（有状态 MCP Server 必需）..."
        _patch_mcporter_lifecycle
    fi

    success "aicrasher MCP server 注册成功 (via $CLI_CMD)"
}

_patch_mcporter_lifecycle() {
    # 在 mcporter 配置文件中为 aicrasher 补上 "lifecycle": "keep-alive"。
    # aicrasher 是有状态的 MCP Server（crash session 需跨多次 tool call 保留），
    # mcporter stdio 模式默认是 ephemeral（每次调用后进程关闭，session 丢失），
    # 必须通过 keep-alive 让 daemon 维持进程常驻。

    # 查找 mcporter 配置文件
    local MCPORTER_CONFIG=""
    if [[ -f "$HOME/.mcporter/mcporter.json" ]]; then
        MCPORTER_CONFIG="$HOME/.mcporter/mcporter.json"
    elif [[ -f "./config/mcporter.json" ]]; then
        MCPORTER_CONFIG="./config/mcporter.json"
    fi

    if [[ -z "$MCPORTER_CONFIG" ]]; then
        warn "未找到 mcporter.json，请手动在 aicrasher 配置中添加 \"lifecycle\": \"keep-alive\""
        return 0
    fi

    python3 -c "
import json, sys

config_path = '$MCPORTER_CONFIG'
with open(config_path) as f:
    cfg = json.load(f)

# mcporter 配置可能在 mcpServers.aicrasher 或顶级 aicrasher
patched = False
if 'mcpServers' in cfg and 'aicrasher' in cfg['mcpServers']:
    cfg['mcpServers']['aicrasher']['lifecycle'] = 'keep-alive'
    patched = True
elif 'aicrasher' in cfg:
    cfg['aicrasher']['lifecycle'] = 'keep-alive'
    patched = True

if patched:
    with open(config_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    print('OK')
else:
    print('aicrasher entry not found in config', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null && {
        success "lifecycle: keep-alive 已设置"
    } || {
        warn "自动设置 lifecycle 失败，请手动在 mcporter.json 的 aicrasher 配置中添加 \"lifecycle\": \"keep-alive\""
    }
}


install_skill() {
    info "正在安装 crash-expert skill 文件..."

    mkdir -p "$SKILL_TARGET_DIR/scripts"
    mkdir -p "$SKILL_TARGET_DIR/reference"

    # 复制根目录文件
    local root_files=(
        "SKILL.md"
    )
    for f in "${root_files[@]}"; do
        if [[ -f "$SKILL_DIR/$f" ]]; then
            cp -f "$SKILL_DIR/$f" "$SKILL_TARGET_DIR/$f"
        fi
    done

    # 复制 scripts/ 子目录文件
    local script_files=(
        "scripts/crash_report_generator.py"
        "scripts/setup.sh"
    )
    for f in "${script_files[@]}"; do
        if [[ -f "$SKILL_DIR/$f" ]]; then
            cp -f "$SKILL_DIR/$f" "$SKILL_TARGET_DIR/$f"
        fi
    done

    # 复制 reference/ 子目录文件
    local ref_files=(
        "reference/crash_commands.md"
        "reference/scenario_analysis.md"
    )
    for f in "${ref_files[@]}"; do
        if [[ -f "$SKILL_DIR/$f" ]]; then
            cp -f "$SKILL_DIR/$f" "$SKILL_TARGET_DIR/$f"
        fi
    done

    # 记录项目路径供后续使用
    echo "$PROJECT_ROOT" > "$SKILL_TARGET_DIR/.project_root"

    success "Skill 文件已安装到: $SKILL_TARGET_DIR"
}

# ── 综合状态检查 ────────────────────────────────────────────────────────

show_status() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  AiCrasher Crash Expert Skill — 安装状态"
    echo "═══════════════════════════════════════════════════════"
    echo ""

    # 1. MCP Python 包
    if check_mcp_package_installed; then
        success "MCP Python 包 (aicrasher): 已安装"
    else
        error "MCP Python 包 (aicrasher): 未安装"
    fi

    # 2. MCP Server 注册
    if check_mcp_server_registered; then
        local detected_cli
        detected_cli=$(detect_cli_tool)
        success "MCP Server 注册: 已注册 (via ${detected_cli:-unknown})"
    else
        warn "MCP Server 注册: 未注册或无法检测"
    fi

    # 3. 检测可用的 CLI 工具
    local cli_tool
    cli_tool=$(detect_cli_tool)
    if [[ -n "$cli_tool" ]]; then
        success "CLI 工具: $cli_tool"
    else
        warn "CLI 工具: 未找到 codebuddy / claude / mcporter"
    fi

    # 4. Skill 文件
    if check_skill_installed; then
        success "Skill 文件: 已安装 ($SKILL_TARGET_DIR)"
    else
        warn "Skill 文件: 未安装到 ~/.codebuddy/skills/"
    fi

    echo ""
}

# ── 完整安装流程 ────────────────────────────────────────────────────────

full_install() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  AiCrasher Crash Expert Skill — 自动安装"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    info "项目目录: $PROJECT_ROOT"
    info "Skill 目录: $SKILL_DIR"
    echo ""

    # 步骤 1：安装 MCP Python 包
    if check_mcp_package_installed; then
        success "MCP Python 包已安装，跳过"
    else
        install_mcp_package
    fi

    echo ""

    # 步骤 2：注册 MCP Server
    if check_mcp_server_registered; then
        success "MCP Server 已注册，跳过"
    else
        register_mcp_server
    fi

    echo ""

    # 步骤 3：安装 Skill 文件
    install_skill

    echo ""
    echo "═══════════════════════════════════════════════════════"
    success "🎉 安装完成！"
    echo ""
    info "使用方法："
    echo "  1. 在 CodeBuddy / Claude Code / OpenClaw 中打开内核源码目录"
    echo "  2. 输入提示词: 分析vmcore /path/to/vmcore /path/to/vmlinux"
    echo ""
    echo "═══════════════════════════════════════════════════════"
}

# ── 入口 ────────────────────────────────────────────────────────────────

case "${1:-}" in
    --check)
        show_status
        ;;
    --install-mcp)
        install_mcp_package
        ;;
    --register-mcp)
        register_mcp_server
        ;;
    --install-skill)
        install_skill
        ;;
    --help|-h)
        echo "用法: bash setup.sh [选项]"
        echo ""
        echo "选项:"
        echo "  (无参数)        完整安装（安装包 + 注册 MCP + 安装 skill）"
        echo "  --check         仅检查安装状态"
        echo "  --install-mcp   仅安装 MCP Python 包"
        echo "  --register-mcp  仅注册 MCP server"
        echo "  --install-skill 仅安装 skill 文件"
        echo "  --help, -h      显示此帮助"
        ;;
    *)
        full_install
        ;;
esac
