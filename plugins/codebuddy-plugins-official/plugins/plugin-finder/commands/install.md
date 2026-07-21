---
description: 手动安装指定插件
argument-hint: [plugin1@marketplace1] [plugin2@marketplace2] ...
allowed-tools: Read, Bash(/plugin:*)
model: haiku
---

# Manual Plugin Installation

Install specified plugins: $ARGUMENTS

## Step 1: Parse Arguments

Extract plugin@marketplace pairs from arguments: "$ARGUMENTS"

Expected format:
- Single: `plugin-name@marketplace-name`
- Multiple: `plugin1@market1 plugin2@market2 plugin3@market3`

Parse each argument to extract:
- Plugin name (before @)
- Marketplace name (after @)

## Step 2: Validate Plugins

For each plugin@marketplace pair:

1. **Read marketplace registry:**
   - CodeBuddy: `~/.codebuddy/plugins/known_marketplaces.json`
   - Claude: `~/.claude/plugins/known_marketplaces.json`

2. **Verify marketplace exists:**
   - Check marketplace name is in registry
   - If not found, list available marketplaces

3. **Verify plugin exists in marketplace:**
   - Search `manifest.plugins` array
   - Check plugin name matches
   - If not found, suggest similar names

## Step 3: Display Installation Plan

Before installing, show user what will be installed:

```
准备安装以下插件：

1. plugin1@marketplace1
   Description: [plugin description]
   Version: [version]
   Category: [category]

2. plugin2@marketplace2
   Description: [plugin description]
   Version: [version]
   Category: [category]

总计: 2 个插件
```

## Step 4: Execute Installation

Install all plugins in a single batch command:

```bash
/plugin install plugin1@marketplace1 plugin2@marketplace2
```

**Monitor output:**
- Watch for success messages
- Capture any error messages
- Track which plugins installed successfully

## Step 5: Report Results

**If all succeeded:**
```
✅ 成功安装所有插件！

已安装:
  - plugin1@marketplace1
  - plugin2@marketplace2

⚠️  重要：退出并重启 CodeBuddy Code 使插件生效。
```

**If some failed:**
```
⚠️  部分插件安装失败

成功:
  ✓ plugin1@marketplace1

失败:
  ✗ plugin2@marketplace2
    错误: [error message]

请检查失败原因并重试。
```

**If all failed:**
```
❌ 所有插件安装失败

原因可能是:
  - 插件名称或市场名称错误
  - 网络连接问题
  - 权限不足
  - 磁盘空间不足

详细错误: [error messages]
```

## Edge Cases

**No arguments provided:**
```
用法: /plugin-finder:install plugin-name@marketplace-name

示例:
  /plugin-finder:install code-review@claude-plugins-official
  /plugin-finder:install plugin1@market1 plugin2@market2

提示: 使用 /plugin-finder:search 搜索可用插件
```

**Invalid format (missing @):**
```
错误: 无效的格式

正确格式: plugin-name@marketplace-name

您输入的: $ARGUMENTS

请使用正确格式重试。
```

**Marketplace not found:**
```
错误: 未找到市场 "[marketplace-name]"

可用的市场:
  - codebuddy-plugins-official
  - claude-plugins-official
  - local-dev

添加新市场:
  /plugin marketplace add [marketplace-url]
```

**Plugin not found:**
```
错误: 在市场 "[marketplace]" 中未找到插件 "[plugin-name]"

建议:
  - 检查插件名称拼写
  - 使用 /plugin-finder:search 查找正确名称
  - 更新市场: /plugin marketplace update [marketplace]
```

**Already installed:**
```
ℹ️  插件 "[plugin-name]" 已安装

选项:
  - 跳过 (continue with other plugins)
  - 重新安装 (reinstall)
  - 更新 (update to latest version)
```

## Post-Installation

Always display restart reminder:

```
⚠️  重要提示

插件已安装，但需要重启 CodeBuddy Code 才能生效。

步骤:
1. 完全退出 CodeBuddy Code
2. 重新启动 CodeBuddy Code  
3. 验证: /plugin list
```

## Success Criteria

✅ Arguments parsed correctly
✅ All plugins validated before installation
✅ Installation command executed
✅ Results clearly reported
✅ Errors handled gracefully
✅ User reminded to restart
