# Plugin 开发工具包

一个全面的 CodeBuddy Code Plugin 开发工具包，提供关于 Hook、MCP 集成、Plugin 结构和市场发布的专家指导。

## 概述

plugin-dev 工具包提供七个专门的 Skill 来帮助您构建高质量的 CodeBuddy Code Plugins：

1. **Hook 开发** - 高级 Hook API 和事件驱动自动化
2. **MCP 集成** - Model Context Protocol Server 集成
3. **Plugin 结构** - Plugin 组织和 Manifest 配置
4. **Plugin 设置** - 使用 .codebuddy/plugin-name.local.md 文件的配置模式
5. **Command 开发** - 使用 Frontmatter 和参数创建斜杠命令
6. **Agent 开发** - 使用 AI 辅助生成创建自主 Agent
7. **Skill 开发** - 创建具有渐进式披露和强触发器的 Skill

每个 Skill 都遵循最佳实践，采用渐进式披露原则：精简的核心文档、详细的参考文档、可工作的示例和实用脚本。

## 引导式工作流命令

### /plugin-dev:create-plugin

一个全面的、端到端的工作流命令，用于从零开始创建 Plugin，类似于 feature-dev 工作流。

**8 个阶段：**
1. **发现** - 理解 Plugin 目的和要求
2. **组件规划** - 确定所需的 Skills、Commands、Agents、Hooks、MCP
3. **详细设计** - 规范每个组件并解决歧义
4. **结构创建** - 设置目录和 Manifest
5. **组件实现** - 使用 AI 辅助的 Agent 创建每个组件
6. **验证** - 运行 plugin-validator 和组件特定检查
7. **测试** - 在 CodeBuddy Code 中验证 Plugin 工作
8. **文档** - 完成 README 并准备发布

**功能特性：**
- 在每个阶段提出澄清性问题
- 自动加载相关的 Skills
- 使用 agent-creator 进行 AI 辅助的 Agent 生成
- 运行验证工具（validate-agent.sh、validate-hook-schema.sh 等）
- 遵循 plugin-dev 自身的经过验证的模式
- 指导测试和验证

**用法：**
```bash
/plugin-dev:create-plugin [可选描述]

# 示例：
/plugin-dev:create-plugin
/plugin-dev:create-plugin 一个用于管理数据库迁移的 Plugin
```

使用此工作流进行结构化、高质量的 Plugin 开发，从概念到完成。

## Skills

### 1. Hook 开发

**触发短语：** "create a hook"、"add a PreToolUse hook"、"validate tool use"、"implement prompt-based hooks"、"${CODEBUDDY_PLUGIN_ROOT}"、"block dangerous commands"

**涵盖内容：**
- 基于 Prompt 的 Hook（推荐）和 LLM 决策
- 用于确定性验证的 Command Hook
- 所有 Hook 事件：PreToolUse、PostToolUse、Stop、SubagentStop、SessionStart、SessionEnd、UserPromptSubmit、PreCompact、Notification
- Hook 输出格式和 JSON Schema
- 安全最佳实践和输入验证
- ${CODEBUDDY_PLUGIN_ROOT} 用于可移植路径

**资源：**
- 核心 SKILL.md（1,619 字）
- 3 个示例 Hook 脚本（validate-write、validate-bash、load-context）
- 3 个参考文档：patterns、migration、advanced-techniques
- 3 个实用脚本：validate-hook-schema.sh、test-hook.sh、hook-linter.sh

**使用场景：** 在 Plugin 中创建事件驱动自动化、验证操作或执行策略。

### 2. MCP 集成

**触发短语：** "add MCP server"、"integrate MCP"、"configure .mcp.json"、"Model Context Protocol"、"stdio/SSE/HTTP server"、"connect external service"

**涵盖内容：**
- MCP Server 配置（.mcp.json vs plugin.json）
- 所有 Server 类型：stdio（本地）、SSE（托管/OAuth）、HTTP（REST）、WebSocket（实时）
- 环境变量扩展（${CODEBUDDY_PLUGIN_ROOT}、用户变量）
- MCP 工具命名和在 Commands/Agents 中的使用
- 认证模式：OAuth、Tokens、环境变量
- 集成模式和性能优化

**资源：**
- 核心 SKILL.md（1,666 字）
- 3 个示例配置（stdio、SSE、HTTP）
- 3 个参考文档：server-types（~3,200字）、authentication（~2,800字）、tool-usage（~2,600字）

**使用场景：** 将外部服务、API、数据库或工具集成到您的 Plugin 中。

### 3. Plugin 结构

**触发短语：** "plugin structure"、"plugin.json manifest"、"auto-discovery"、"component organization"、"plugin directory layout"

**涵盖内容：**
- 标准 Plugin 目录结构和自动发现
- plugin.json Manifest 格式和所有字段
- 组件组织（Commands、Agents、Skills、Hooks）
- ${CODEBUDDY_PLUGIN_ROOT} 的使用
- 文件命名约定和最佳实践
- 最小化、标准化和高级 Plugin 模式

**资源：**
- 核心 SKILL.md（1,619 字）
- 3 个示例结构（minimal、standard、advanced）
- 2 个参考文档：component-patterns、manifest-reference

**使用场景：** 启动新 Plugin、组织组件或配置 Plugin Manifest。

### 4. Plugin 设置

**触发短语：** "plugin settings"、"store plugin configuration"、".local.md files"、"plugin state files"、"read YAML frontmatter"、"per-project plugin settings"

**涵盖内容：**
- 用于配置的 .codebuddy/plugin-name.local.md 模式
- YAML Frontmatter + Markdown 正文结构
- Bash 脚本的解析技术（sed、awk、grep 模式）
- 临时活动的 Hooks（标志文件和快速退出）
- 来自 multi-agent-swarm 和 ralph-loop Plugins 的真实示例
- 原子文件更新和验证
- Gitignore 和生命周期管理

**资源：**
- 核心 SKILL.md（1,623 字）
- 3 个示例（read-settings hook、create-settings command、templates）
- 2 个参考文档：parsing-techniques、real-world-examples
- 2 个实用脚本：validate-settings.sh、parse-frontmatter.sh

**使用场景：** 使 Plugins 可配置、存储每个项目的状态或实现用户偏好。

### 5. Command 开发

**触发短语：** "create a slash command"、"add a command"、"command frontmatter"、"define command arguments"、"organize commands"

**涵盖内容：**
- 斜杠命令结构和 Markdown 格式
- YAML Frontmatter 字段（description、argument-hint、allowed-tools）
- 动态参数和文件引用
- 用于上下文的 Bash 执行
- Command 组织和命名空间
- Command 开发的最佳实践

**资源：**
- 核心 SKILL.md（1,535 字）
- 示例和参考文档
- Command 组织模式

**使用场景：** 创建斜杠命令、定义命令参数或组织 Plugin Commands。

### 6. Agent 开发

**触发短语：** "create an agent"、"add an agent"、"write a subagent"、"agent frontmatter"、"when to use description"、"agent examples"、"autonomous agent"

**涵盖内容：**
- Agent 文件结构（YAML Frontmatter + System Prompt）
- 所有 Frontmatter 字段（name、description、model、color、tools）
- 带有 <example> 块的 Description 格式，用于可靠触发
- System Prompt 设计模式（analysis、generation、validation、orchestration）
- 使用 CodeBuddy Code 经过验证的 Prompt 进行 AI 辅助的 Agent 生成
- 验证规则和最佳实践
- 完整的生产就绪 Agent 示例

**资源：**
- 核心 SKILL.md（1,438 字）
- 2 个示例：agent-creation-prompt（AI 辅助工作流）、complete-agent-examples（4 个完整 Agents）
- 3 个参考文档：agent-creation-system-prompt（来自 CodeBuddy Code）、system-prompt-design（~4,000字）、triggering-examples（~2,500字）
- 1 个实用脚本：validate-agent.sh

**使用场景：** 创建自主 Agents、定义 Agent 行为或实现 AI 辅助的 Agent 生成。

### 7. Skill 开发

**触发短语：** "create a skill"、"add a skill to plugin"、"write a new skill"、"improve skill description"、"organize skill content"

**涵盖内容：**
- Skill 结构（带有 YAML Frontmatter 的 SKILL.md）
- 渐进式披露原则（metadata → SKILL.md → resources）
- 带有特定短语强触发器描述
- 写作风格（命令式/不定式形式，第三人称）
- 捆绑资源组织（references/、examples/、scripts/）
- Skill 创建工作流
- 基于适配 CodeBuddy Code Plugins 的 skill-creator 方法论

**资源：**
- 核心 SKILL.md（1,232 字）
- 参考资料：skill-creator 方法论、plugin-dev 模式
- 示例：研究 plugin-dev 自身的 Skills 作为模板

**使用场景：** 为 Plugins 创建新 Skills 或改进现有 Skill 质量。


## 安装

从 codebuddy-marketplace 安装：

```bash
/plugin install plugin-dev@codebuddy-marketplace
```

或用于开发，直接使用：

```bash
cc --plugin-dir /path/to/plugin-dev
```

## 快速开始

### 创建您的第一个 Plugin

1. **规划您的 Plugin 结构：**
   - 询问："What's the best directory structure for a plugin with commands and MCP integration?"
   - plugin-structure Skill 将指导您

2. **添加 MCP 集成（如需要）：**
   - 询问："How do I add an MCP server for database access?"
   - mcp-integration Skill 提供示例和模式

3. **实现 Hooks（如需要）：**
   - 询问："Create a PreToolUse hook that validates file writes"
   - hook-development Skill 提供可工作的示例和工具


## 开发工作流

plugin-dev 工具包支持您的整个 Plugin 开发生命周期：

```
┌─────────────────────┐
│  设计结构            │  → plugin-structure skill
│  (manifest, layout) │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  添加组件           │
│  (commands, agents, │  → 所有 Skills 提供指导
│   skills, hooks)    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  集成服务           │  → mcp-integration skill
│  (MCP servers)      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  添加自动化         │  → hook-development skill
│  (hooks, validation)│     + utility scripts
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  测试和验证         │  → hook-development utilities
│                     │     validate-hook-schema.sh
└──────────┬──────────┘     test-hook.sh
           │                 hook-linter.sh
```

## 功能特性

### 渐进式披露

每个 Skill 使用三级披露系统：
1. **Metadata**（始终加载）：带有强触发器的简明描述
2. **核心 SKILL.md**（触发时加载）：必要的 API 参考（~1,500-2,000 字）
3. **References/Examples**（按需加载）：详细指南、模式和可工作的代码

这使 CodeBuddy Code 的上下文保持专注，同时在需要时提供深入的知识。

### 实用脚本

hook-development Skill 包含生产就绪的工具：

```bash
# 验证 hooks.json 结构
./validate-hook-schema.sh hooks/hooks.json

# 部署前测试 Hooks
./test-hook.sh my-hook.sh test-input.json

# 对 Hook 脚本进行 Lint 检查最佳实践
./hook-linter.sh my-hook.sh
```

### 可工作的示例

每个 Skill 提供可工作的示例：
- **Hook 开发**：3 个完整的 Hook 脚本（bash、write validation、context loading）
- **MCP 集成**：3 个 Server 配置（stdio、SSE、HTTP）
- **Plugin 结构**：3 个 Plugin 布局（minimal、standard、advanced）
- **Plugin 设置**：3 个示例（read-settings hook、create-settings command、templates）
- **Command 开发**：10 个完整的 Command 示例（review、test、deploy、docs 等）

## 文档标准

所有 Skills 遵循一致的标准：
- 第三人称描述（"This skill should be used when..."）
- 强触发器短语以可靠加载
- 全文使用命令式/不定式形式
- 基于官方 CodeBuddy Code 文档
- 安全优先的方法和最佳实践

## 内容总计

- **核心 Skills**：7 个 SKILL.md 文件，约 11,065 字
- **参考文档**：约 10,000+ 字的详细指南
- **示例**：12+ 个可工作的示例（hook 脚本、MCP 配置、plugin 布局、settings 文件）
- **工具**：6 个生产就绪的验证/测试/解析脚本

## 使用场景

### 构建数据库 Plugin

```
1. "What's the structure for a plugin with MCP integration?"
   → plugin-structure Skill 提供布局

2. "How do I configure an stdio MCP server for PostgreSQL?"
   → mcp-integration Skill 显示配置

3. "Add a Stop hook to ensure connections close properly"
   → hook-development Skill 提供模式
```

### 创建验证 Plugin

```
1. "Create hooks that validate all file writes for security"
   → hook-development Skill 提供示例

2. "Test my hooks before deploying"
   → 使用 validate-hook-schema.sh 和 test-hook.sh

3. "Organize my hooks and configuration files"
   → plugin-structure Skill 显示最佳实践
```

### 集成外部服务

```
1. "Add Asana MCP server with OAuth"
   → mcp-integration Skill 涵盖 SSE Servers

2. "Use Asana tools in my commands"
   → mcp-integration tool-usage 参考

3. "Structure my plugin with commands and MCP"
   → plugin-structure Skill 提供模式
```

## 最佳实践

所有 Skills 强调：

✅ **安全优先**
- Hooks 中的输入验证
- MCP Servers 使用 HTTPS/WSS
- 凭证使用环境变量
- 最小权限原则

✅ **可移植性**
- 到处使用 ${CODEBUDDY_PLUGIN_ROOT}
- 仅使用相对路径
- 环境变量替换

✅ **测试**
- 部署前验证配置
- 使用示例输入测试 Hooks
- 使用调试模式（`codebuddy --debug`）

✅ **文档**
- 清晰的 README 文件
- 记录环境变量
- 使用示例

## 贡献

此 Plugin 是 codebuddy-marketplace 的一部分。要贡献改进：

1. Fork Marketplace 仓库
2. 修改 plugin-dev/
3. 使用 `cc --plugin-dir` 本地测试
4. 按照 marketplace-publishing 指南创建 PR

## 版本

0.1.0 - 初始版本，包含七个全面的 Skills 和三个验证 Agents

## 作者

Daisy Hollman (daisy@anthropic.com)

## 许可证

MIT License - 详情见仓库

---

**注意：** 此工具包旨在帮助您构建高质量的 Plugins。当您提出相关问题时，Skills 会自动加载，在您需要时提供专家指导。
