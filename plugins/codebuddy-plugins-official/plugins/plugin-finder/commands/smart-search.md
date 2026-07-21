---
description: 智能分析任务需求，多维度推荐相关插件
argument-hint: [任务描述]
allowed-tools: Read, Glob, Grep, AskUserQuestion, Bash(/plugin:*)
model: sonnet
---

# Smart Plugin Search with Task Capability Analysis

Intelligently analyze the user's task "$ARGUMENTS" and recommend plugins across multiple capability dimensions.

## Step 1: Load Marketplace Data

Read all marketplace data:

**CodeBuddy marketplaces:**
@~/.codebuddy/plugins/known_marketplaces.json

**Claude marketplaces (if exists):**
@~/.claude/plugins/known_marketplaces.json

Extract the `installLocation` for each marketplace and **build a complete plugin index**.

## Step 2: Deep Exploration of Plugins

For each marketplace's `installLocation`, use **Glob and Grep** to explore plugin structures:

```bash
# Find all plugin.json files
find $INSTALL_LOCATION -name "plugin.json" -type f

# Read plugin.json to get plugin metadata
Read each plugin.json file

# Explore plugin capabilities:
# - Read README.md for detailed description
# - Check commands/ directory for available commands
# - Check agents/ directory for autonomous capabilities
# - Check skills/ directory for specialized knowledge
```

**Build a rich plugin profile including:**
- Plugin name, description, keywords, category
- Capabilities (commands, agents, skills)
- Use cases (extracted from README)
- Related domains (inferred from content)

**DO NOT** rely on simple text matching. Use deep exploration and semantic understanding.

## Step 3: Task Capability Decomposition

Analyze the user's task: "$ARGUMENTS"

**Use AI reasoning to decompose the task into required capabilities.**

Example thought process (do not use this example in responses):
- If task involves creating documentation → needs: content generation, structure planning, formatting
- If task involves data processing → needs: data extraction, transformation, analysis
- If task involves automation → needs: workflow design, scripting, monitoring

**Output format:**
```
核心任务：[用户的原始需求]

需要的能力：
1. [能力1名称] - [简短说明为什么需要]
2. [能力2名称] - [简短说明为什么需要]
3. [能力3名称] - [简短说明为什么需要]
...
```

Keep explanations concise (5-10 words per capability).

## Step 4: Match Plugins to Capabilities

For each identified capability, find relevant plugins using:

1. **Semantic matching** - Understand plugin purpose beyond keywords
2. **Capability analysis** - Check what the plugin can actually do
3. **Use case alignment** - Match plugin use cases to required capabilities

**Organize matches by capability dimension:**

```
能力维度 1: [能力名称]
- plugin1@marketplace1 (最相关)
- plugin2@marketplace2 (次相关)
...

能力维度 2: [能力名称]
- plugin3@marketplace3
- plugin4@marketplace4
...
```

## Step 5: Present Multi-Dimensional Recommendations

Use `AskUserQuestion` to present recommendations with **multiple questions**:

**Question 1 (PRIMARY):** Plugins directly matching the user's original task
- Header: "核心功能"
- Question: "这些插件直接支持您的任务，推荐安装哪些？（可多选）"
- `multiSelect: true`
- Options: Top 3-5 most relevant plugins for the core task

**Question 2-N (SUPPORTING):** Plugins for each supporting capability
- Header: "[能力维度名称]"
- Question: "为了完成任务，您可能还需要[能力名称]，推荐哪些？（可多选）"
- `multiSelect: true`
- Options: Top 2-4 plugins for this capability

**Format each option as:**
```json
{
  "label": "plugin-name@marketplace",
  "description": "[One-line capability description] | [Key features]"
}
```

**Example structure:**
```javascript
// Question 1: Core task plugins
{
  header: "核心功能",
  question: "这些插件直接支持您的任务，推荐安装哪些？（可多选）",
  multiSelect: true,
  options: [
    {
      label: "plugin-a@official",
      description: "专注于[核心功能] | 特性：[关键特性列表]"
    },
    ...
  ]
}

// Question 2: Supporting capability 1
{
  header: "数据分析",
  question: "为了完成任务，您可能还需要数据分析能力，推荐哪些？（可多选）",
  multiSelect: true,
  options: [
    {
      label: "analyzer@official",
      description: "强大的数据分析工具 | 特性：统计、可视化、导出"
    },
    ...
  ]
}

// Question 3: Supporting capability 2
{
  header: "文档生成",
  question: "为了完成任务，您可能还需要文档生成能力，推荐哪些？（可多选）",
  multiSelect: true,
  options: [...]
}
```

**Important rules:**
- First question MUST match user's original request
- Limit to 3-5 capability dimensions (avoid overwhelming user)
- Show top 2-4 plugins per dimension
- Each description should be clear and actionable

## Step 6: Install Selected Plugins

After user selects plugins from all questions:

1. **Aggregate all selections** across all questions
2. **Deduplicate** - Remove duplicate plugin@marketplace pairs
3. **Batch install** using single command:

```bash
/plugin install plugin1@market1 plugin2@market2 plugin3@market3 ...
```

4. **Monitor installation** and report status
5. **Handle errors** - Report failed installations clearly

## Step 7: Post-Installation Summary

After installation, show a summary:

```
✅ 插件安装完成！

已安装插件：
- [核心功能] plugin1@market1 ✓
- [能力1] plugin2@market2 ✓
- [能力2] plugin3@market3 ✓

⚠️  重要：请重启 CodeBuddy Code 使插件生效。

步骤：
1. 完全退出 CodeBuddy Code
2. 重新启动
3. 使用 /plugin list 验证插件已加载

💡 使用提示：
- 使用 /help 查看新增的命令
- 查看各插件的 README 了解详细用法
```

## Edge Cases

**No plugins found for a capability:**
- Skip that question
- Inform user in summary: "未找到 [能力名称] 相关的插件"

**User selects nothing:**
```
未选择任何插件。

💡 需要其他功能？试试：
- /plugin-finder:search [关键词] - 搜索特定插件
- /plugin-finder:wish - 许愿新功能
```

**Only core task plugins found (no supporting capabilities):**
- Only show Question 1
- Proceed with installation normally

**User is overwhelmed by options:**
- Keep capability dimensions to 3-5 max
- Show only top-ranked plugins per dimension
- Use clear, concise descriptions

## Quality Standards

✅ Capability decomposition is logical and relevant
✅ First question matches user's original intent
✅ Supporting capabilities are genuinely helpful
✅ Plugin matches are accurate (not keyword-based)
✅ Descriptions are clear and actionable
✅ User can select across multiple dimensions
✅ Installation and restart reminder are shown

## Example Workflow

**User input:** "我想做一个自动化测试的插件"

**Step 3 output:**
```
核心任务：自动化测试

需要的能力：
1. 测试框架集成 - 支持主流测试工具
2. 代码覆盖率分析 - 评估测试质量
3. CI/CD集成 - 自动运行测试
4. 测试报告生成 - 可视化测试结果
```

**Step 5 questions:**
```
Question 1:
  header: "核心功能"
  question: "这些插件直接支持自动化测试，推荐安装哪些？"
  options: [test-runner@official, qa-automation@community, ...]

Question 2:
  header: "代码覆盖率"
  question: "为了完成任务，您可能还需要代码覆盖率分析，推荐哪些？"
  options: [coverage-analyzer@official, ...]

Question 3:
  header: "CI/CD集成"
  question: "为了完成任务，您可能还需要CI/CD集成能力，推荐哪些？"
  options: [github-actions@official, jenkins-plugin@community, ...]
```

---

**Begin execution starting from Step 1.**
