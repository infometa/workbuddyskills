---
description: 并行调用多个插件执行同一任务并比较结果
argument-hint: [任务描述]
allowed-tools: Read, Bash(ls:*, /plugin:*), Task, Write, AskUserQuestion
model: sonnet
---

# Multi-Plugin Parallel Execution and Comparison

Execute task across multiple plugins and compare results: "$ARGUMENTS"

## Step 1: Identify Relevant Plugins from Installed Plugins

**IMPORTANT: Only analyze plugins that are already installed.**

### Step 1.1: List All Installed Plugins

First, get the complete list of installed plugins:

```bash
# Check installed plugins cache
ls -la ~/.codebuddy/plugins/cache/*/

# Or read from installed_plugins list
cat ~/.codebuddy/plugins/installed_plugins.json 2>/dev/null
```

**For each marketplace, list installed plugins:**
```bash
# List plugins in codebuddy-plugins-official
ls ~/.codebuddy/plugins/cache/codebuddy-plugins-official/

# List plugins in claude-plugins-official  
ls ~/.codebuddy/plugins/cache/claude-plugins-official/

# List local plugins
ls ~/.codebuddy/plugins/local/
```

### Step 1.2: Read Plugin Metadata

For each **installed** plugin, read its metadata:

```bash
# Read plugin.json for metadata
cat ~/.codebuddy/plugins/cache/marketplace-name/plugin-name/.codebuddy-plugin/plugin.json

# Or read from marketplace manifest
cat ~/.codebuddy/plugins/known_marketplaces.json | jq '.["marketplace-name"].manifest.plugins[] | select(.name == "plugin-name")'
```

Extract:
- Plugin name
- Description (both `description` and `description_en`)
- Category
- Keywords
- Source path
- Version

### Step 1.3: AI Semantic Matching (From Installed Plugins Only)

**CRITICAL: Only score plugins that are confirmed to be installed.**

Analyze task description: "$ARGUMENTS"

For each **installed** plugin:
1. Read plugin description, category, keywords from metadata
2. Use AI to determine if plugin is relevant to task
3. Score relevance (0-100) based on:
   - Description semantic match (50 points)
   - Keywords match (30 points)
   - Category match (15 points)
   - Name match (5 points)
4. **Only select plugins scoring > 60**

**Scoring criteria:**
- 90-100: Highly relevant, directly addresses the task
- 70-89: Very relevant, good capability match
- 60-69: Relevant, partial capability match
- <60: Not relevant enough, exclude from selection

**Example:**
```
Task: "审查这段代码的安全问题"

Installed plugins found:
✓ code-review@claude-plugins-official (installed)
✓ security-guidance@claude-plugins-official (installed)
✓ plugin-dev@claude-plugins-official (installed)
✓ frontend-design@claude-plugins-official (installed)

After AI semantic matching:
- code-review@claude-plugins-official (score: 95) ✅ Include
- security-guidance@claude-plugins-official (score: 90) ✅ Include
- plugin-dev@claude-plugins-official (score: 30) ❌ Too low
- frontend-design@claude-plugins-official (score: 15) ❌ Too low

Selected for user choice: 2 plugins
```

**Handle edge cases:**
- If no installed plugins score > 60, inform user:
  ```
  未找到相关的已安装插件。
  
  建议：
  1. 使用 /plugin-finder:search 搜索并安装相关插件
  2. 修改任务描述使其更明确
  3. 检查已安装的插件列表：/plugin list
  ```

- If only 1 plugin scores > 60:
  ```
  只找到 1 个相关插件: plugin-name@marketplace
  
  无法进行对比（需要至少 2 个插件）。
  
  选项：
  1. 直接使用该插件执行任务
  2. 搜索并安装更多相关插件
  3. 扩大评分范围（降低阈值到 50）
  ```

## Step 1.5: Ask User to Select Plugins

**CRITICAL: Before proceeding to analysis, ask user which plugins to use.**

**IMPORTANT: Only show plugins that are:**
1. ✅ **Already installed** (verified in Step 1.1)
2. ✅ **Scored > 60** in semantic matching (from Step 1.3)
3. ✅ **Have valid metadata** (description, category, etc.)

Use `AskUserQuestion` tool to display relevant **installed** plugins for user selection:

**Format:**
```json
{
  "questions": [{
    "question": "我找到了以下已安装的相关插件，请选择要用于对比的插件（可多选）：",
    "header": "选择插件",
    "multiSelect": true,
    "options": [
      {
        "label": "plugin1@marketplace1",
        "description": "✅ 已安装 | Plugin description (score: 95) - Component: agent/command/skill"
      },
      {
        "label": "plugin2@marketplace2",
        "description": "✅ 已安装 | Plugin description (score: 85) - Component: agent/command/skill"
      },
      {
        "label": "全部插件",
        "description": "使用所有找到的相关插件进行对比"
      }
    ]
  }]
}
```

**Important notes:**
- Set `multiSelect: true` to allow multiple selections
- **Always prefix with "✅ 已安装"** to confirm plugin is installed
- Always include "全部插件" option for convenience
- Show plugin score and component type in description
- Sort by relevance score (highest first)
- Limit to top 8 plugins (if more found, show top 8 + "全部插件" option)
- **Do NOT show uninstalled plugins** in the selection list

**After user selection:**
- Parse selected plugin names
- If "全部插件" selected, use all relevant **installed** plugins
- If user provides custom input via "Other", parse plugin@marketplace format
- **Validate all selected plugins are actually installed**:
  ```bash
  # Check if plugin directory exists
  test -d ~/.codebuddy/plugins/cache/marketplace-name/plugin-name/ && echo "✓ Installed" || echo "✗ Not installed"
  ```
- If any selected plugin is not installed, warn user and skip it
- Continue to Step 2 with validated, installed plugins only

**Example interaction:**
```
Question: "我找到了以下已安装的相关插件，请选择要用于对比的插件（可多选）："

Options:
1. document-skills-pptx@codebuddy-plugins-official
   ✅ 已安装 | PowerPoint 演示文稿创建、编辑和分析 (score: 98) - Skill
   
2. theme-factory@codebuddy-plugins-official
   ✅ 已安装 | 应用专业主题和配色 (score: 75) - Command
   
3. 全部插件
   使用所有找到的相关插件

User selects: [1, 2]

Validation:
✓ document-skills-pptx: Installed at ~/.codebuddy/plugins/cache/codebuddy-plugins-official/document-skills-pptx/
✓ theme-factory: Installed at ~/.codebuddy/plugins/cache/codebuddy-plugins-official/theme-factory/

Proceed with: document-skills-pptx, theme-factory
```

## Step 2: Analyze Plugin Capabilities

For each **selected** plugin (from Step 1.5), determine invocation method:

**Read plugin structure:**
```bash
ls ~/.codebuddy/plugins/cache/marketplace-name/plugin-name/
```

**Check for components:**
1. **Agents** (`agents/` directory)
   - Most powerful for complex tasks
   - Can use tools and reason about problems
   - **Priority: HIGH**

2. **Commands** (`commands/` directory)
   - Execute specific workflows
   - May require specific arguments
   - **Priority: MEDIUM**

3. **Skills** (`skills/` directory)
   - Provide knowledge and guidance
   - Loaded into current context
   - **Priority: LOW** (for comparison)

4. **Hooks** (`hooks/` directory)
   - Automatic, not manually invoked
   - **Skip for comparison**

**Determine invocation plan:**
```
Plugin: code-review@claude-plugins-official
Components found:
  - agents/code-reviewer.md ✓
  - agents/test-reviewer.md ✓
  - commands/review.md ✓
Plan: Use code-reviewer agent (highest priority)

Plugin: security-guidance@claude-plugins-official
Components found:
  - hooks/hooks.json (automatic)
  - skills/security-patterns/ ✓
Plan: Load security-patterns skill in context
```

## Step 3: Parallel Execution

Execute each plugin's capability concurrently using Task tool:

**For agent-based execution:**
```
Task 1: code-review agent
Prompt: "Use code-review plugin to: $ARGUMENTS"
Tools: All
```

**For command-based execution:**
```
Task 2: Execute command
Prompt: "Run /review-pr command from plugin-name: $ARGUMENTS"
Tools: Bash, Read
```

**For skill-based execution:**
```
Task 3: Apply skill
Prompt: "Using security-patterns skill, analyze: $ARGUMENTS"
Tools: Read
```

**Track execution:**
- Start timestamp for each task
- Monitor task progress
- Collect outputs when complete

## Step 4: Collect Results

For each plugin execution, gather:

### Quality Metrics
- **Completeness**: Did it cover all aspects of the task?
- **Accuracy**: Are findings correct and valid?
- **Depth**: How detailed is the analysis?
- **Actionability**: Are recommendations clear and useful?

### Performance Metrics
- **Execution time**: How long did it take?
- **Resource usage**: Did it run efficiently?

### Output Analysis
- **Artifacts generated**: Files, reports, modifications
- **Format quality**: Is output well-organized?
- **Presentation**: Is it easy to understand?

### User Experience
- **Ease of use**: Was invocation straightforward?
- **Clarity**: Are results clear?
- **Follow-up**: Does it suggest next steps?

**Example collection:**
```
Plugin: code-review@claude-plugins-official
Execution time: 45 seconds
Findings:
  - 12 issues identified
  - 3 critical, 6 medium, 3 low severity
  - Specific line numbers provided
  - Fix suggestions included
Output format: Markdown report
Artifacts: review-report.md

Plugin: security-guidance@claude-plugins-official  
Execution time: 20 seconds
Findings:
  - 5 security issues
  - All high severity
  - OWASP classifications
  - Code examples for fixes
Output format: Inline comments
Artifacts: None (comments only)
```

## Step 5: AI Analysis and Comparison

Analyze results across all dimensions:

### Quality Comparison

**Completeness:**
```
Plugin A: Covered 95% of code (excellent)
Plugin B: Covered 60% of code (good)
Plugin C: Covered 40% of code (fair)
```

**Accuracy:**
```
Plugin A: 2 false positives out of 12 findings (good)
Plugin B: 0 false positives out of 5 findings (excellent)
Plugin C: 5 false positives out of 8 findings (poor)
```

**Depth:**
```
Plugin A: Detailed analysis with root causes (excellent)
Plugin B: Surface-level checks (fair)
Plugin C: Comprehensive with examples (excellent)
```

### Performance Comparison

```
Plugin A: 45s (medium)
Plugin B: 20s (fast)
Plugin C: 120s (slow)
```

### Output Comparison

**Format:**
- Plugin A: Structured Markdown report ⭐
- Plugin B: Inline comments ⭐⭐
- Plugin C: Plain text list

**Artifacts:**
- Plugin A: Generated 1 file
- Plugin B: No artifacts
- Plugin C: Generated 3 files (report, summary, recommendations)

### Overall Assessment

Synthesize findings into recommendation:

```
Best overall: Plugin A
  - Most complete coverage
  - Good accuracy (few false positives)
  - Detailed analysis
  - Reasonable performance
  - Professional report format

Best for speed: Plugin B
  - Fastest execution
  - Perfect accuracy
  - Good for quick checks
  - Inline feedback

Best for depth: Plugin C
  - Most comprehensive analysis
  - Multiple artifact types
  - Educational examples
  - Worth the wait for critical reviews
```

## Step 6: Generate Comparison Report

Create comprehensive comparison report:

````markdown
# Plugin Comparison Report

## Task
$ARGUMENTS

## Execution Date
[Current timestamp]

## Plugins Tested
1. plugin1@marketplace1 (version)
2. plugin2@marketplace2 (version)
3. plugin3@marketplace3 (version)

---

## Summary

| Plugin | Quality | Speed | Output | Overall |
|--------|---------|-------|--------|---------|
| plugin1 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| plugin2 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| plugin3 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Detailed Results

### Plugin 1: [name]@[marketplace]

**Invocation Method:** [Agent/Command/Skill]
**Execution Time:** [X] seconds

**Quality Assessment:**
- Completeness: ⭐⭐⭐⭐⭐ (5/5)
  - [Detailed explanation]
- Accuracy: ⭐⭐⭐⭐ (4/5)
  - [Detailed explanation]
- Depth: ⭐⭐⭐⭐⭐ (5/5)
  - [Detailed explanation]
- Actionability: ⭐⭐⭐⭐⭐ (5/5)
  - [Detailed explanation]

**Findings:**
- [Number] total findings
- Severity breakdown
- Key issues highlighted

**Output:**
- Format: [Markdown/JSON/Plain text]
- Artifacts: [List of generated files]
- Presentation: [Rating and explanation]

**Strengths:**
- [Strength 1]
- [Strength 2]
- [Strength 3]

**Weaknesses:**
- [Weakness 1]
- [Weakness 2]

**Best For:**
- [Use case 1]
- [Use case 2]

---

[Repeat for each plugin]

---

## Recommendation

### For This Specific Task

**Best Choice: [Plugin Name]**

Reasons:
1. [Primary reason]
2. [Secondary reason]
3. [Additional reason]

This plugin excelled in:
- [Key strength 1]
- [Key strength 2]

### Alternative Recommendations

**Consider [Plugin B] when:**
- [Scenario 1]
- [Scenario 2]

**Consider [Plugin C] when:**
- [Scenario 1]
- [Scenario 2]

---

## Detailed Comparison

### Quality Analysis

[In-depth comparison of quality metrics]

### Performance Analysis

[In-depth comparison of speed and efficiency]

### Output Analysis

[In-depth comparison of outputs and artifacts]

### User Experience

[In-depth comparison of ease of use]

---

## Conclusion

For the task "$ARGUMENTS", we recommend using **[Plugin Name]** because:

[Comprehensive justification]

However, keep in mind:
- [Important consideration 1]
- [Important consideration 2]

---

## Execution Details

- Total plugins tested: [N]
- Total execution time: [X] seconds
- Comparison performed: [Timestamp]
- CodeBuddy Code version: [Version]

````

Write this report to file: `plugin-comparison-report-[timestamp].md`

## Step 7: Present Results to User

Display summary to user:

```
📊 多插件比较完成！

测试的插件:
  1. plugin1@marketplace1
  2. plugin2@marketplace2
  3. plugin3@marketplace3

🏆 推荐: plugin1@marketplace1
  原因: [简短说明]

📄 详细报告已生成: plugin-comparison-report-[timestamp].md

使用 /read 查看完整报告
```

## Edge Cases

**User cancels selection or selects nothing:**
```
您没有选择任何插件。

要继续，请：
1. 重新运行命令并选择插件
2. 或使用 /plugin-finder:search 搜索其他插件
```

**No installed plugins found:**
```
❌ 未找到任何已安装的插件。

请先安装插件：
1. 浏览可用插件：/plugin-finder:search [关键词]
2. 安装推荐插件：/plugin install plugin-name@marketplace
3. 查看插件市场：查看 ~/.codebuddy/plugins/known_marketplaces.json
```

**No relevant plugins found (among installed):**
```
未找到与任务 "$ARGUMENTS" 相关的已安装插件。

已安装插件数量: [N]
相关性评分 > 60: 0

建议:
1. 使用 /plugin-finder:search 搜索并安装相关插件
   示例: /plugin-finder:search AI PPT generation
2. 修改任务描述使其更明确
3. 降低相关性阈值重试（评分 > 50）
4. 查看所有已安装插件: /plugin list
```
```
未找到与任务 "$ARGUMENTS" 相关的已安装插件。

建议:
1. 使用 /plugin-finder:search 搜索相关插件
2. 安装推荐的插件
3. 重新运行 /plugin-finder:multi-run
```

**Only one relevant plugin found (among installed):**
```
只找到 1 个相关的已安装插件: plugin1@marketplace1 (score: 85)

无法进行对比（需要至少 2 个插件）。

选项:
1. 直接使用该插件执行任务 ✓
2. 搜索并安装更多相关插件
   /plugin-finder:search [关键词]
3. 降低评分阈值，包含更多插件（score > 50）
```

**Selected plugin not actually installed:**
```
⚠️  警告：选中的插件未正确安装

未安装的插件:
  ✗ plugin-name@marketplace (路径不存在)

已验证安装的插件:
  ✓ other-plugin@marketplace

将只使用已安装的插件继续执行...
```

**Some plugins failed:**
```
部分插件执行失败:

成功:
  ✓ plugin1@marketplace1
  ✓ plugin2@marketplace2

失败:
  ✗ plugin3@marketplace3
    错误: [error message]

继续比较成功的插件...
```

**All plugins failed:**
```
❌ 所有插件执行失败

可能原因:
- 任务描述不明确
- 插件配置错误
- 权限不足

请检查:
1. 任务描述是否清晰: "$ARGUMENTS"
2. 插件是否正确安装: /plugin list
3. 详细错误信息
```

## Configuration Support

Check user configuration `~/.codebuddy/.local.md`:

If `preferred_plugins` specified:
- Prioritize these plugins in comparison
- Still include other relevant plugins

If `comparison_output_format` specified:
- Adjust report format accordingly
- Support: markdown, json, html

## Success Criteria

✅ Task clearly understood
✅ Relevant plugins identified
✅ **User selected plugins via multi-select interface**
✅ All selected plugins invoked correctly
✅ Results collected comprehensively
✅ Fair comparison across dimensions
✅ Clear recommendation provided
✅ Detailed report generated
✅ User can make informed decision
