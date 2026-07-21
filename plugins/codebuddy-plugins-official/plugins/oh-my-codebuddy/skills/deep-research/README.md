# Deep Research Workflow Skill

完整的研究型工作流系统，实现从代码库分析、深度调研到技术文档生成的完整流程。

## 功能概述

本技能提供了一套完整的研究型工作流系统，包括：

1. **代码库研究分析** (`/init-research`) - 分析代码库并标记需要联网调研的内容
2. **深度调研循环** (`/ralph-loop-research`) - 处理所有 TODO 标记，执行深度调研
3. **Wiki 生成循环** (`/ralph-loop-wiki`) - 生成完整的技术分析文档
4. **GitHub 仓库研究** (`gh-repo-research`) - 克隆并分析 GitHub 仓库

## 安装

### 方式一：使用安装脚本（推荐）

```bash
cd codebuddy-marketplace/skills/deep-research
bash install.sh
```

### 方式二：手动安装

```bash
# 创建目录
mkdir -p ~/.codebuddy/skills/deep-research/{commands,agents}
mkdir -p ~/.claude/skills/deep-research/{commands,agents}

# 复制命令
cp omc-commands/init-research.md ~/.codebuddy/skills/deep-research/commands/
cp omc-commands/ralph-loop-research.md ~/.codebuddy/skills/deep-research/commands/
cp omc-commands/ralph-loop-wiki.md ~/.codebuddy/skills/deep-research/commands/

# 复制智能体
cp omc-agents/gh-repo-research.md ~/.codebuddy/skills/deep-research/agents/

# 同样复制到 Claude Code 目录
cp omc-commands/*.md ~/.claude/skills/deep-research/commands/
cp omc-agents/gh-repo-research.md ~/.claude/skills/deep-research/agents/
```

## 使用流程

### 步骤 1: 初始化研究文档

```bash
/init-research
```

这将：
- 分析整个代码库
- 识别需要联网调研的内容
- 生成 `deep-search.md` 文件（根目录 + 重要子目录）
- 在需要联网的地方标记 `TODO: RESEARCH HERE`

### 步骤 2: 执行深度调研

```bash
/ralph-loop-research
```

这将：
- 扫描所有 `deep-search.md` 文件
- 查找所有 `TODO: RESEARCH HERE` 标记
- 对每个标记执行深度调研
- 生成专业的 wiki 格式内容
- 替换 TODO 标记为实际内容
- 处理发现的链接（GitHub 链接会激活 `gh-repo-research`）
- 循环直到所有 TODO 标记都被替换（默认最多 3 次）

### 步骤 3: 生成技术 Wiki

```bash
/ralph-loop-wiki
```

这将：
- 读取 PRD 文档（如果存在）
- 读取 `.research/` 目录下的所有调研内容
- 结合 `init-deep` 生成的 CODEBUDDY.md 文件
- 按照 `wiki_template.md` 的格式生成完整 wiki
- 循环 3 次，确保内容完整
- 生成优化建议和总结

## 文件结构

安装后的目录结构：

```
~/.codebuddy/skills/deep-research/
├── SKILL.md
├── README.md
├── commands/
│   ├── init-research.md
│   ├── ralph-loop-research.md
│   └── ralph-loop-wiki.md
└── agents/
    └── gh-repo-research.md
```

## 工作流输出

执行工作流后，项目目录将包含：

```
项目根目录/
├── deep-search.md                    # 研究文档（带 TODO 标记）
├── CODEBUDDY.md                      # 代码库分析（来自 init-deep）
├── .research/                        # 调研结果
│   ├── research-001.md              # 调研笔记
│   ├── research-002.md
│   └── gh-repo/                      # GitHub 仓库研究
│       └── repo-name/
│           ├── architecture.md
│           ├── core-modules.md
│           ├── api-reference.md
│           └── features.md
├── .gh-repo/                         # 克隆的仓库
│   └── repo-name/
├── wiki.md                           # 最终生成的 wiki
├── wiki-optimization-suggestions.md # 优化建议
└── wiki-summary.md                   # 总结报告
```

## 命令详解

### /init-research

基于 `init-deep` 的工作流程，分析代码库并生成研究文档。

**选项**:
- `--create-new`: 重新生成所有文件
- `--max-depth=N`: 限制目录深度（默认 3）

**输出**: `deep-search.md` 文件，包含 `TODO: RESEARCH HERE` 标记

### /ralph-loop-research

深度调研循环，处理所有 TODO 标记。

**选项**:
- `--max-iterations=N`: 最大循环次数（默认 3）
- `--completion-promise=TEXT`: 自定义完成标记（默认 "ALL_RESEARCHED"）

**输出**: 
- 替换所有 TODO 标记为实际内容
- 调研笔记保存在 `.research/` 目录

### /ralph-loop-wiki

生成完整的技术 wiki 文档。

**选项**:
- `--max-iterations=N`: 最大循环次数（默认 3）
- `--prd-path=PATH`: 指定 PRD 文件路径
- `--completion-promise=TEXT`: 自定义完成标记（默认 "WIKI_COMPLETE"）

**输出**: 
- `wiki.md` - 完整的技术分析文档
- `wiki-optimization-suggestions.md` - 优化建议
- `wiki-summary.md` - 总结报告

## 智能体

### gh-repo-research

GitHub 仓库研究智能体，用于克隆和分析 GitHub 仓库。

**使用方式**:
通过 `ralph-loop-research` 自动调用，或手动调用：

```
Task: gh-repo-research
Input:
## Repository URL
https://github.com/owner/repo

## Context
[上下文信息]

## Output Location
.research/gh-repo/repo-name/
```

**输出**:
- `architecture.md` - 架构分析
- `core-modules.md` - 核心模块详解
- `api-reference.md` - API 参考
- `features.md` - 产品功能分析

## 注意事项

1. **首次使用前**：建议先运行 `/init-deep` 生成 CODEBUDDY.md 文件
2. **PRD 文档**：如果有 PRD 文档，放在项目根目录或使用 `--prd-path` 指定
3. **网络要求**：深度调研需要联网访问外部资源
4. **GitHub 访问**：`gh-repo-research` 需要能够克隆 GitHub 仓库
5. **存储空间**：克隆的仓库会占用磁盘空间，注意 `.gh-repo/` 目录大小

## 故障排除

### 问题：找不到 deep-search.md 文件

**解决**：先运行 `/init-research` 生成研究文档

### 问题：TODO 标记没有被替换

**解决**：
- 检查网络连接
- 检查 `librarian` 智能体是否可用
- 查看 `.research/` 目录中的调研笔记

### 问题：Wiki 生成不完整

**解决**：
- 确保已运行 `/ralph-loop-research` 完成所有调研
- 检查 PRD 文档是否存在
- 检查 CODEBUDDY.md 文件是否存在

## 相关文档

- [init-deep 命令文档](../omc-commands/init-deep.md)
- [ralph-loop 命令文档](../omc-commands/ralph-loop.md)
- [wiki_template.md](../../wiki_template.md)
