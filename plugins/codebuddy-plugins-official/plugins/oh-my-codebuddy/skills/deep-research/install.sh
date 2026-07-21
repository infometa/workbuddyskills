#!/bin/bash
# Deep Research Workflow Installation Script
# Installs deep-research commands and agents to CodeBuddy and Claude Code

set -e

# Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "  ${RED}✗${NC} $1" >&2
}

print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

print_header() {
    echo -e "${BOLD}${CYAN}$1${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Source files are in the codebuddy-marketplace root (parent of skills directory)
SOURCE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Target directories
CODEBUDDY_DIR="$HOME/.codebuddy"
CLAUDE_DIR="$HOME/.claude"

# Create target directories
CODEBUDDY_SKILLS_DIR="$CODEBUDDY_DIR/skills/deep-research"
CLAUDE_SKILLS_DIR="$CLAUDE_DIR/skills/deep-research"

print_header "📦 Deep Research Workflow 安装程序"
echo ""

# Check if source files exist
print_info "检查源文件..."

FILES=(
    "omc-commands/init-research.md"
    "omc-commands/ralph-loop-research.md"
    "omc-commands/ralph-loop-wiki.md"
    "omc-agents/gh-repo-research.md"
)

MISSING_FILES=()
for file in "${FILES[@]}"; do
    if [ ! -f "$SOURCE_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    print_error "以下源文件不存在:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

print_success "所有源文件检查通过"
echo ""

# Install to CodeBuddy
print_info "安装到 CodeBuddy ($CODEBUDDY_SKILLS_DIR)..."
mkdir -p "$CODEBUDDY_SKILLS_DIR/commands"
mkdir -p "$CODEBUDDY_SKILLS_DIR/agents"

# Copy commands
cp "$SOURCE_DIR/omc-commands/init-research.md" "$CODEBUDDY_SKILLS_DIR/commands/"
cp "$SOURCE_DIR/omc-commands/ralph-loop-research.md" "$CODEBUDDY_SKILLS_DIR/commands/"
cp "$SOURCE_DIR/omc-commands/ralph-loop-wiki.md" "$CODEBUDDY_SKILLS_DIR/commands/"

# Copy agents
cp "$SOURCE_DIR/omc-agents/gh-repo-research.md" "$CODEBUDDY_SKILLS_DIR/agents/"

print_success "已安装到 CodeBuddy"
echo ""

# Install to Claude Code
print_info "安装到 Claude Code ($CLAUDE_SKILLS_DIR)..."
mkdir -p "$CLAUDE_SKILLS_DIR/commands"
mkdir -p "$CLAUDE_SKILLS_DIR/agents"

# Copy commands
cp "$SOURCE_DIR/omc-commands/init-research.md" "$CLAUDE_SKILLS_DIR/commands/"
cp "$SOURCE_DIR/omc-commands/ralph-loop-research.md" "$CLAUDE_SKILLS_DIR/commands/"
cp "$SOURCE_DIR/omc-commands/ralph-loop-wiki.md" "$CLAUDE_SKILLS_DIR/commands/"

# Copy agents
cp "$SOURCE_DIR/omc-agents/gh-repo-research.md" "$CLAUDE_SKILLS_DIR/agents/"

print_success "已安装到 Claude Code"
echo ""

# Create SKILL.md file
print_info "创建 SKILL.md 文件..."

SKILL_MD_CONTENT="# Deep Research Workflow Skill

This skill provides a complete research workflow system for codebase analysis, deep research, and technical wiki generation.

## Commands

- \`/init-research\` - Initialize research documentation with TODO markers
- \`/ralph-loop-research\` - Deep research loop that processes all TODO markers
- \`/ralph-loop-wiki\` - Generate comprehensive technical wiki from research findings

## Agents

- \`gh-repo-research\` - Clone and analyze GitHub repositories

## Workflow

1. Run \`/init-research\` to analyze codebase and identify research needs
2. Run \`/ralph-loop-research\` to perform deep research on all TODO markers
3. Run \`/ralph-loop-wiki\` to generate comprehensive technical wiki

## Installation

This skill is installed to:
- \`~/.codebuddy/skills/deep-research/\`
- \`~/.claude/skills/deep-research/\`

Run \`bash install.sh\` from the skill directory to install.
"

echo "$SKILL_MD_CONTENT" > "$CODEBUDDY_SKILLS_DIR/SKILL.md"
echo "$SKILL_MD_CONTENT" > "$CLAUDE_SKILLS_DIR/SKILL.md"

print_success "SKILL.md 文件已创建"
echo ""

# Summary
print_header "✅ 安装完成！"
echo ""
echo -e "安装位置："
echo -e "  ${CYAN}CodeBuddy:${NC} $CODEBUDDY_SKILLS_DIR"
echo -e "  ${CYAN}Claude Code:${NC} $CLAUDE_SKILLS_DIR"
echo ""
echo -e "已安装文件："
echo -e "  ${GREEN}命令:${NC}"
echo -e "    - init-research.md"
echo -e "    - ralph-loop-research.md"
echo -e "    - ralph-loop-wiki.md"
echo -e "  ${GREEN}智能体:${NC}"
echo -e "    - gh-repo-research.md"
echo ""
echo -e "${BOLD}下一步：${NC}"
echo -e "  1. 重启 CodeBuddy/Claude Code 以加载新技能"
echo -e "  2. 运行 ${CYAN}/init-research${NC} 开始分析代码库"
echo ""
