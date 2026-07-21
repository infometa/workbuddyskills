---
name: deep-research
description: Complete research workflow system for codebase analysis, deep external research, and comprehensive technical wiki generation
---

# Deep Research Workflow Skill

完整的研究型工作流系统，实现从代码库分析、深度调研到技术文档生成的完整流程。

## 功能概述

本技能提供了一套完整的研究型工作流系统，包括：

1. **代码库研究分析** (`/init-research`) - 分析代码库并标记需要联网调研的内容
2. **深度调研循环** (`/ralph-loop-research`) - 处理所有 TODO 标记，执行深度调研
3. **Wiki 生成循环** (`/ralph-loop-wiki`) - 生成完整的技术分析文档
4. **GitHub 仓库研究** (`gh-repo-research`) - 克隆并分析 GitHub 仓库

## 命令

### /init-research

初始化研究文档，分析代码库并生成 `deep-search.md` 文件，在需要联网调研的地方标记 `TODO: RESEARCH HERE`。

**用法**:
```
/init-research                      # 更新模式
/init-research --create-new         # 重新生成所有文件
/init-research --max-depth=2        # 限制目录深度
```

**输出**: `deep-search.md` 文件（根目录 + 重要子目录）

### /ralph-loop-research

深度调研循环，处理所有 `TODO: RESEARCH HERE` 标记。

**用法**:
```
/ralph-loop-research                      # 默认 3 次循环
/ralph-loop-research --max-iterations=5   # 自定义循环次数
```

**功能**:
- 扫描所有 `deep-search.md` 文件
- 查找所有 `TODO: RESEARCH HERE` 标记
- 执行深度调研（联网搜索）
- 生成专业的 wiki 格式内容
- 替换 TODO 标记为实际内容
- 处理发现的链接（GitHub 链接激活 `gh-repo-research`）

**输出**: 
- 替换所有 TODO 标记
- 调研笔记保存在 `.research/` 目录

### /ralph-loop-wiki

生成完整的技术 wiki 文档。

**用法**:
```
/ralph-loop-wiki                              # 默认 3 次循环
/ralph-loop-wiki --prd-path=docs/PRD.md      # 指定 PRD 文件
/ralph-loop-wiki --max-iterations=5           # 自定义循环次数
```

**功能**:
- 读取 PRD 文档（如果存在）
- 读取 `.research/` 目录下的所有调研内容
- 结合 `init-deep` 生成的 CODEBUDDY.md 文件
- 按照 `wiki_template.md` 的格式生成完整 wiki
- 循环 3 次，确保内容完整
- 生成优化建议和总结

**输出**: 
- `wiki.md` - 完整的技术分析文档
- `wiki-optimization-suggestions.md` - 优化建议
- `wiki-summary.md` - 总结报告

## 智能体

### gh-repo-research

GitHub 仓库研究智能体，用于克隆和分析 GitHub 仓库。

**功能**:
- 克隆 GitHub 仓库到 `.gh-repo/` 目录
- 在克隆的仓库中执行 `/init-deep` 操作
- 生成技术文档（架构、核心模块、API、功能分析）
- 保存到 `.research/gh-repo/repo-name/` 目录

**使用方式**:
通过 `ralph-loop-research` 自动调用（当发现 GitHub 链接时），或手动调用。

## 工作流程

### 完整工作流

```
1. /init-research
   ↓
   生成 deep-search.md（带 TODO: RESEARCH HERE 标记）
   
2. /ralph-loop-research
   ↓
   处理所有 TODO 标记
   ↓
   深度调研 → 生成 wiki 格式内容
   ↓
   发现链接 → GitHub 链接 → gh-repo-research
   ↓
   所有 TODO 替换完成
   
3. /ralph-loop-wiki
   ↓
   整合 PRD + .research + CODEBUDDY.md
   ↓
   生成完整 wiki（按 wiki_template.md 格式）
   ↓
   3 次验证循环
   ↓
   生成优化建议和总结
```

### 快速开始

```bash
# 步骤 1: 初始化研究文档
/init-research

# 步骤 2: 执行深度调研
/ralph-loop-research

# 步骤 3: 生成技术 Wiki
/ralph-loop-wiki
```

## 文件结构

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

## 安装

运行安装脚本：

```bash
cd codebuddy-marketplace/skills/deep-research
bash install.sh
```

这将安装到：
- `~/.codebuddy/skills/deep-research/`
- `~/.claude/skills/deep-research/`

## 注意事项

1. **首次使用前**：建议先运行 `/init-deep` 生成 CODEBUDDY.md 文件
2. **PRD 文档**：如果有 PRD 文档，放在项目根目录或使用 `--prd-path` 指定
3. **网络要求**：深度调研需要联网访问外部资源
4. **GitHub 访问**：`gh-repo-research` 需要能够克隆 GitHub 仓库
5. **存储空间**：克隆的仓库会占用磁盘空间，注意 `.gh-repo/` 目录大小

## 相关文档

- [README.md](README.md) - 详细使用文档
- [init-research.md](../omc-commands/init-research.md) - init-research 命令文档
- [ralph-loop-research.md](../omc-commands/ralph-loop-research.md) - ralph-loop-research 命令文档
- [ralph-loop-wiki.md](../omc-commands/ralph-loop-wiki.md) - ralph-loop-wiki 命令文档
- [gh-repo-research.md](../omc-agents/gh-repo-research.md) - gh-repo-research 智能体文档
