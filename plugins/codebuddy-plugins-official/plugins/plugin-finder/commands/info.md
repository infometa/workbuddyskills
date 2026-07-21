---
description: 查看插件详细信息（机制、功能、实现）
argument-hint: <plugin-name>[@marketplace-name]
allowed-tools: Read, Bash
model: haiku
---

# Plugin Information Display

Display comprehensive information about a plugin: "$ARGUMENTS"

## Step 1: Parse Arguments

Extract plugin identifier from arguments: "$ARGUMENTS"

**Expected formats:**
- Simple: `plugin-name` (search all marketplaces)
- Qualified: `plugin-name@marketplace-name` (specific marketplace)

Parse into:
- `plugin_name`: The plugin identifier (before @, or entire string if no @)
- `marketplace_name`: The marketplace identifier (after @, or empty for all)

**Validation:**
- If empty arguments, show usage and exit
- Trim whitespace from parsed values

## Step 2: Locate Plugin in Marketplaces

Read marketplace registries to find the plugin:

**Marketplace files:**
- CodeBuddy: `~/.codebuddy/plugins/known_marketplaces.json`
- Claude: `~/.claude/plugins/known_marketplaces.json` (if exists)

**Search logic:**

1. **If marketplace specified** (`plugin-name@marketplace`):
   - Find marketplace by name
   - Check if plugin exists in `manifest.plugins`
   - Extract `path` field from plugin entry
   
2. **If no marketplace specified** (`plugin-name` only):
   - Search ALL marketplaces
   - Find first marketplace containing this plugin
   - Extract `path` field from plugin entry
   - If found in multiple marketplaces, note which one is used

**Error handling:**
- If marketplace not found → List available marketplaces
- If plugin not found → Suggest using `/plugin-finder:search`
- If path field missing → Report error

**Extract plugin path:**
The `path` field in marketplace JSON points to the plugin directory:
```json
{
  "name": "plugin-dev",
  "path": "/path/to/marketplace/plugins/plugin-dev"
}
```

Store this path for analysis in Step 3.

## Step 3: Analyze Plugin Structure

Run the analysis script to extract plugin information:

```bash
${CODEBUDDY_PLUGIN_ROOT}/examples/analyze-plugin-info.sh "<plugin-path>"
```

**Script output:** JSON containing:
- Basic info: name, version, description, author, keywords
- Components: commands[], agents[], skills[], hooks[], mcp[]
- Counts: component statistics

**Parse the JSON output** and store for display in Step 4.

**Error handling:**
- If script fails → Report error and suggest checking plugin structure
- If JSON invalid → Report parsing error
- If plugin directory doesn't exist → Report path issue

## Step 4: Display Plugin Information

Format and present the plugin information in a clear, structured way:

### 4.1 Basic Information

```
📦 插件名称: [name]
🏷️  版本: [version]
👤 作者: [author]

📝 功能描述:
[description from plugin.json]

🔖 关键词: [keywords]
```

### 4.2 组件统计

```
🛠️  组件组成:
├─ Commands (命令):    [count] 个
├─ Agents (智能体):    [count] 个
├─ Skills (技能):      [count] 个
├─ Hooks (钩子):       [count] 个
└─ MCP Servers:        [count] 个
```

### 4.3 Commands 详情

If commands exist (count > 0):

```
📜 命令列表:

1. /[plugin-name]:[command-name] [arguments]
   描述: [command description]
   参数: [argument-hint]

2. /[plugin-name]:[command-name2] [arguments]
   描述: [command description]
   参数: [argument-hint]

[继续列出所有命令...]
```

### 4.4 Agents 详情

If agents exist (count > 0):

```
🤖 智能体 (Agent):

1. [agent-name]
   功能: [agent description]
   触发时机: [whenToUse summary]

2. [agent-name2]
   功能: [agent description]
   触发时机: [whenToUse summary]

[继续列出所有 agents...]
```

### 4.5 Skills 详情

If skills exist (count > 0):

```
💡 技能 (Skill):

1. [skill-name]
   说明: [first paragraph from SKILL.md]

2. [skill-name2]
   说明: [first paragraph from SKILL.md]

[继续列出所有 skills...]
```

### 4.6 Hooks 详情

If hooks exist (count > 0):

```
🔗 钩子 (Hook):

1. [event-name] Hook
   类型: [prompt/command]
   说明: [description]

2. [event-name2] Hook
   类型: [prompt/command]
   说明: [description]

[继续列出所有 hooks...]
```

### 4.7 MCP Servers 详情

If MCP servers exist (count > 0):

```
🔌 MCP 集成:

1. [server-name]
   类型: [stdio/sse/http/websocket]

2. [server-name2]
   类型: [stdio/sse/http/websocket]

[继续列出所有 MCP servers...]
```

### 4.8 实现概述

Read README.md from plugin directory (if exists) and extract implementation overview:

```
🔧 实现方式:

[Extract 2-3 key points about implementation from README:
 - Core technology/approach
 - Key dependencies or integrations
 - Architecture pattern if mentioned]

详细文档: [plugin-path]/README.md
```

If README not found or too short, provide generic overview based on components:
```
🔧 实现方式:

基于 CodeBuddy Code 插件系统实现:
- 使用 [X] 个命令提供用户交互入口
- [如果有 agent] 通过 Agent 实现自动化任务执行
- [如果有 skill] 通过 Skill 提供专业领域知识
- [如果有 hook] 通过 Hook 实现事件驱动的自动化
- [如果有 MCP] 通过 MCP 集成外部服务

详细信息请查看插件目录: [plugin-path]
```

### 4.9 Footer

```
---
💡 提示:
- 安装: /plugin-finder:install [plugin-name]@[marketplace-name]
- 搜索相关插件: /plugin-finder:search "[关键词]"
- 查看插件源码: [plugin-path]
```

## Step 5: Summary Statistics

At the end, provide a brief summary:

```
📊 统计摘要:
总组件数: [total] 个
- [X] 个命令、[Y] 个智能体、[Z] 个技能、[W] 个钩子、[V] 个 MCP 服务

[Plugin name] 是一个 [category/purpose] 插件。
```

Infer category/purpose from:
- Description
- Component types (e.g., many commands → user-facing tool, many agents → automation)
- Keywords

## Edge Cases

**No arguments provided:**
```
用法: /plugin-finder:info <plugin-name>[@marketplace-name]

示例:
  /plugin-finder:info plugin-dev
  /plugin-finder:info github@codebuddy-plugins-official

查找插件: /plugin-finder:search "[关键词]"
```

**Plugin not found:**
```
❌ 未找到插件 "[plugin-name]"

建议:
  - 检查插件名称拼写
  - 指定具体的 marketplace: [plugin-name]@[marketplace]
  - 搜索相关插件: /plugin-finder:search "[plugin-name]"

可用的 marketplace:
  - codebuddy-plugins-official
  - claude-plugins-official
  - local-dev
```

**Marketplace not found:**
```
❌ 未找到 marketplace "[marketplace-name]"

可用的 marketplace:
  - codebuddy-plugins-official
  - claude-plugins-official
  - local-dev

添加 marketplace: /plugin marketplace add [url]
```

**Plugin path doesn't exist:**
```
⚠️  插件已在 marketplace 注册，但本地路径不存在

插件: [plugin-name]
预期路径: [path]

可能原因:
  - 插件尚未下载
  - 插件已被删除
  - Marketplace 配置错误

尝试重新安装: /plugin-finder:install [plugin-name]@[marketplace]
```

**Analysis script fails:**
```
⚠️  无法完整分析插件结构

插件: [plugin-name]
路径: [path]
错误: [error message]

已知信息:
[显示从 marketplace 获取的基本信息]

手动查看: [path]
```

**No components found:**
```
📦 插件名称: [name]
🏷️  版本: [version]

⚠️  此插件没有任何组件（commands/agents/skills/hooks/mcp）

这可能是:
  - 一个空插件模板
  - 配置文件型插件（仅 plugin.json）
  - 插件结构不完整

手动查看: [path]
```

## Configuration Support

Check for user config at `~/.codebuddy/plugin-finder.local.md`:

If exists, read YAML frontmatter for settings:
- `show_implementation_details: true/false` - Include/exclude implementation section
- `verbose_output: true/false` - Show more/less detail
- `preferred_language: zh/en` - Output language preference

Apply settings to output format.

## Success Criteria

✅ Plugin located in marketplace
✅ Plugin structure analyzed successfully
✅ All components identified and counted
✅ Information displayed in clear, structured format
✅ Implementation overview provided
✅ Helpful tips and next steps shown
✅ Errors handled gracefully with actionable suggestions
