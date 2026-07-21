---
description: 智能搜索和推荐插件
argument-hint: [需求描述]
allowed-tools: Read, AskUserQuestion, Bash(/plugin:*)
model: sonnet
---

# Plugin Search and Recommendation

Search for plugins matching user needs: "$ARGUMENTS"

## Step 1: Read Marketplace Data

Read both CodeBuddy and Claude marketplace registries:

**CodeBuddy marketplaces:**
@~/.codebuddy/plugins/known_marketplaces.json

**Claude marketplaces (if exists):**
@~/.claude/plugins/known_marketplaces.json

Extract all plugins from the `manifest.plugins` arrays in each marketplace entry.

## Step 2: AI Semantic Matching

Analyze user query: "$ARGUMENTS"

Match plugins based on:
1. **Description** (primary) - Use AI semantic understanding, not just keyword matching
2. **Keywords** - Exact and partial matches
3. **Category** - Broad classification matching
4. **Tags** - Additional metadata
5. **Name** - Fuzzy name matching

**Scoring algorithm:**
- Description semantic match: 50 points (AI understands intent)
- Keywords exact match: 30 points
- Category match: 15 points
- Tags/Name match: 5 points

Recommend ALL plugins scoring above 40 points. Do not limit the number of results.

## Step 3: Present Recommendations

Use `AskUserQuestion` tool to display recommendations:

**Format each option as:**
```
[plugin-name]@[marketplace-name]
[Brief description from marketplace]
Category: [category] | Keywords: [keywords]
```

**Configuration:**
- Set `multiSelect: true` to allow multiple selections
- Include "Other" option for custom input
- Show installation count if available

**Question structure:**
```
header: "选择插件"
question: "以下是为您推荐的插件，您想安装哪些？（可多选）"
multiSelect: true
options: [
  {
    label: "plugin1@market1",
    description: "Plugin 1 description and features"
  },
  {
    label: "plugin2@market2",
    description: "Plugin 2 description and features"
  },
  ...
]
```

## Step 4: Install Selected Plugins

After user selects plugins:

1. **Parse selections** - Extract plugin@marketplace pairs
2. **Batch install** - Use single command for all selections:

```bash
/plugin install plugin1@market1 plugin2@market2 plugin3@market3
```

3. **Monitor installation** - Watch for success/error messages
4. **Handle errors** - If any installation fails, report which ones failed and why

## Step 5: Post-Installation Reminder

**CRITICAL:** Always display this reminder after installation:

```
✅ 插件安装成功！

⚠️  重要提示：您必须退出并重新启动 CodeBuddy Code，插件才能生效。

步骤：
1. 完全退出 CodeBuddy Code
2. 重新启动 CodeBuddy Code
3. 使用 /plugin list 验证插件已加载
```

## Edge Cases

**No marketplaces found:**
```
未找到任何插件市场。请先添加插件市场：

/plugin marketplace add https://github.com/anthropics/claude-plugins-official
```

**No matching plugins:**
```
😔 未找到匹配的插件。

建议：
- 尝试更宽泛的搜索词
- 检查拼写
- 更新插件市场：/plugin marketplace update

💡 找不到您需要的插件？
   您可以许愿新插件：/plugin-finder:wish "您的需求描述"
   我们会将您的需求反馈给 CodeBuddy 团队！
```

**User selects "Other":**
Ask user for specific plugin details:
- Plugin name
- Marketplace name
- Confirm before installing

**User finds results unsatisfactory:**
If user indicates none of the recommendations meet their needs:
```
😔 推荐的插件都不满意？

💡 您可以许愿新插件！

使用命令：/plugin-finder:wish "详细描述您的需求"

我们会帮您整理一封详细的许愿邮件，您可以发送到：
📧 codebuddy@tencent.com

CodeBuddy 团队会认真考虑每一个用户的需求！
```

## Configuration Support

Check if user has configuration file `~/.codebuddy/.local.md`:

If exists, read and apply settings:
- `preferred_marketplaces`: Search these first
- `recommendation_threshold`: Adjust scoring threshold (high: 50, medium: 40, low: 30)
- `show_install_count`: Display popularity if available

## Success Criteria

✅ User query understood correctly
✅ All marketplaces searched
✅ Relevant plugins identified through AI matching
✅ Clear recommendations presented
✅ Multi-select UI provided
✅ Batch installation executed
✅ User reminded to restart
