---
name: plugin-discovery
description: This skill should be used when the user asks to "推荐插件", "查找插件", "搜索插件", "有什么插件", "安装插件", "plugin recommendation", "find plugins", "search plugins", or needs help discovering and managing CodeBuddy Code plugins from marketplaces.
version: 0.1.0
---

# Plugin Discovery and Management

## Purpose

This skill provides comprehensive guidance for discovering, recommending, installing, and comparing plugins from CodeBuddy Code and Claude Code plugin marketplaces. Enable intelligent plugin discovery through AI semantic matching, streamlined installation workflows, and multi-plugin comparison capabilities.

## When to Use

Activate this skill when users:
- Request plugin recommendations for specific needs
- Want to explore available plugins in marketplaces
- Need help installing plugins
- Want to compare multiple plugins for the same task
- Ask general questions about plugin capabilities

## Core Concepts

### Dual Platform Support

CodeBuddy Code supports both CodeBuddy and Claude plugin ecosystems:

**CodeBuddy Platform:**
- Marketplace registry: `~/.codebuddy/plugins/known_marketplaces.json`
- Plugin installation uses CodeBuddy-specific paths
- Uses `.codebuddy-plugin/` directory structure

**Claude Platform:**
- Marketplace registry: `~/.claude/plugins/known_marketplaces.json`
- Installed plugins: `~/.claude/plugins/installed_plugins.json`
- Uses `.claude-plugin/` directory structure

### Marketplace Structure

Each marketplace in `known_marketplaces.json` contains:
- `name`: Marketplace identifier
- `installLocation`: Local path to marketplace
- `manifest`: Full marketplace.json content with plugin listings
- `lastUpdated`: Last update timestamp

Example entry:
```json
{
  "claude-plugins-official": {
    "type": "git",
    "source": {
      "source": "git",
      "url": "https://github.com/anthropics/claude-plugins-official"
    },
    "installLocation": "/Users/user/.codebuddy/plugins/marketplaces/...",
    "manifest": {
      "plugins": [...]
    }
  }
}
```

### Plugin Metadata

Each plugin in marketplace.json includes:
- `name`: Plugin identifier
- `description`: What the plugin does
- `category`: Plugin type (development, productivity, security, etc.)
- `keywords`: Search tags
- `tags`: Additional metadata
- `source`: Plugin location (local path or git URL)
- `version`: Plugin version

## Plugin Discovery Workflow

### Step 1: Read Marketplace Data

Read marketplace registry files to get all available plugins:

```bash
# CodeBuddy marketplaces
cat ~/.codebuddy/plugins/known_marketplaces.json

# Claude marketplaces
cat ~/.claude/plugins/known_marketplaces.json
```

Extract plugin information from the `manifest.plugins` array in each marketplace.

### Step 2: Semantic Matching

Use AI to understand user intent and match against plugin metadata:

**Match against:**
1. **Description** - Primary matching field, use semantic similarity
2. **Keywords** - Exact and partial matches
3. **Category** - Broad classification matching
4. **Tags** - Additional metadata matching
5. **Name** - Fuzzy name matching

**Scoring algorithm:**
- Description semantic match: 50 points
- Keywords exact match: 30 points
- Category match: 15 points
- Tags match: 5 points

Recommend plugins scoring above 40 points.

### Step 3: Present Recommendations

Use `AskUserQuestion` tool to display recommendations with:
- Plugin name and marketplace
- Description
- Category and keywords
- Installation count (if available)
- Multi-select option enabled

Example presentation:
```
Question: "Which plugins would you like to install?"
Options:
1. code-review@claude-plugins-official
   Description: Automated code review with multiple specialized agents
   Category: productivity
   
2. security-guidance@claude-plugins-official
   Description: Security reminder hook for potential security issues
   Category: security
```

### Step 4: Install Selected Plugins

For each selected plugin, execute installation command:

```bash
/plugin install plugin-name@marketplace-name
```

**Batch installation:**
```bash
/plugin install plugin1@market1 plugin2@market2 plugin3@market3
```

### Step 5: Post-Installation

After installation, always inform user:

**Critical reminder:**
```
✅ Plugins installed successfully!

⚠️  IMPORTANT: You must restart CodeBuddy Code for plugins to take effect.

Steps:
1. Exit CodeBuddy Code completely
2. Relaunch CodeBuddy Code
3. Verify plugins loaded with /plugin list
```

## Plugin Comparison Workflow

When comparing multiple plugins for the same task:

### Step 1: Identify Relevant Plugins

Search installed plugins that could handle the task:

```bash
# List installed plugins
/plugin list
```

Match task requirements against:
- Plugin description
- Plugin category
- Known capabilities from plugin.json

### Step 2: Determine Invocation Method

For each relevant plugin, check what components it provides:

**Check plugin structure:**
```bash
ls ~/.codebuddy/plugins/cache/marketplace-name/plugin-name/
```

**Invocation priority:**
1. **If plugin has agents** → Invoke agent with task description
2. **If plugin has commands** → Execute relevant command
3. **If plugin has skills** → Load skill and use in current context
4. **If plugin has hooks** → Note: hooks run automatically, not invoked

### Step 3: Parallel Execution

Execute each plugin's capability concurrently:

```bash
# Create parallel tasks
Task 1: Use plugin-1's agent
Task 2: Use plugin-2's command
Task 3: Apply plugin-3's skill
```

Track outputs and artifacts from each execution.

### Step 4: Results Collection

Collect for each plugin:
- **Output quality**: Completeness, accuracy, usefulness
- **Execution time**: How long it took
- **Artifacts generated**: Files, reports, modifications
- **User experience**: Ease of use, clarity

### Step 5: AI Analysis and Comparison

Analyze collected results across dimensions:

**Quality comparison:**
- Which plugin produced most accurate results?
- Which had most comprehensive coverage?
- Which provided most actionable insights?

**Performance comparison:**
- Which was fastest?
- Which used resources most efficiently?

**Output comparison:**
- Which generated most useful artifacts?
- Which had best formatting and presentation?

**Overall assessment:**
- Recommend best plugin for this specific task
- Note strengths of each plugin
- Suggest when to use alternatives

Generate comparison report:

```markdown
## Plugin Comparison Report

### Task: [Task Description]

### Plugins Tested
1. plugin-1@marketplace-1
2. plugin-2@marketplace-2
3. plugin-3@marketplace-3

### Results Summary

**plugin-1:**
- Quality: ⭐⭐⭐⭐⭐ (5/5)
- Speed: ⭐⭐⭐⭐ (4/5)
- Output: [Description of output]
- Strengths: [List strengths]
- Weaknesses: [List weaknesses]

[Repeat for other plugins]

### Recommendation

For this specific task, **plugin-1** is recommended because:
- [Reason 1]
- [Reason 2]

However, consider **plugin-2** when:
- [Scenario 1]
- [Scenario 2]

### Detailed Comparison

[Detailed analysis of differences]
```

## Installation Commands Reference

### Basic Installation
```bash
/plugin install plugin-name@marketplace-name
```

### Batch Installation
```bash
/plugin install plugin1@market1 plugin2@market2
```

### List Installed Plugins
```bash
/plugin list
```

### Uninstall Plugin
```bash
/plugin uninstall plugin-name
```

### Update Marketplace
```bash
/plugin marketplace update marketplace-name
```

## User Configuration

Users can configure plugin finder behavior via `~/.codebuddy/.local.md`:

```yaml
---
auto_recommend: true
recommendation_threshold: medium
show_install_count: true
preferred_marketplaces:
  - codebuddy-plugins-official
  - claude-plugins-official
---
```

**Configuration options:**
- `auto_recommend`: Enable automatic plugin recommendations (default: true)
- `recommendation_threshold`: Matching threshold - high/medium/low (default: medium)
- `show_install_count`: Display installation popularity (default: true)
- `preferred_marketplaces`: Priority order for searching (default: all)

**Reading configuration:**
```bash
# Check if config exists
if [ -f ~/.codebuddy/.local.md ]; then
  # Parse YAML frontmatter
  # Apply settings
fi
```

## Best Practices

### Discovery

1. **Search all marketplaces**: Don't limit to single marketplace unless user specifies
2. **Show diverse results**: Include plugins from different categories if relevant
3. **Explain recommendations**: Always provide reasoning for each recommendation
4. **Respect user preferences**: Honor settings from .local.md configuration

### Installation

1. **Verify marketplace exists**: Check plugin is in known marketplaces
2. **Batch when possible**: Install multiple plugins in single command
3. **Always remind to restart**: Critical for plugins to take effect
4. **Confirm success**: Verify installation completed

### Comparison

1. **Clear task definition**: Ensure task is well-defined before comparing
2. **Fair testing**: Use same inputs for all plugins
3. **Multiple dimensions**: Evaluate quality, speed, output, UX
4. **Actionable recommendations**: Clear guidance on which to use when

## Troubleshooting

### Plugin Not Found
```
Error: Plugin 'name' not found in any marketplace
```

**Solutions:**
1. Update marketplaces: `/plugin marketplace update`
2. Verify plugin name spelling
3. Check if plugin was removed from marketplace

### Installation Fails
```
Error: Failed to install plugin-name@marketplace
```

**Solutions:**
1. Check internet connectivity (for remote sources)
2. Verify marketplace location exists
3. Check disk space
4. Review error message details

### Plugin Not Loading After Install
```
Issue: Plugin installed but not showing in /plugin list
```

**Solutions:**
1. **Primary**: Restart CodeBuddy Code (exit completely and relaunch)
2. Verify installation: `ls ~/.codebuddy/plugins/cache/`
3. Check plugin.json syntax
4. Review CodeBuddy Code logs

## Additional Resources

### Reference Files

For detailed implementation patterns:
- **`references/marketplace-format.md`** - Complete marketplace.json schema
- **`references/matching-algorithm.md`** - Semantic matching implementation details

### Scripts

Utility scripts in `scripts/`:
- **`search-plugins.sh`** - Search across all marketplaces
- **`compare-plugins.sh`** - Compare plugin capabilities

### Examples

Working examples in `examples/`:
- **`search-example.md`** - Example search workflow
- **`install-example.md`** - Example installation process
- **`compare-example.md`** - Example comparison report

## Implementation Notes

When implementing plugin finder commands and agents:

1. **Read both platform registries**: Check both `~/.codebuddy/` and `~/.claude/` paths
2. **Handle missing files gracefully**: Marketplace files may not exist
3. **Parse JSON carefully**: Marketplace structure varies by version
4. **Use semantic matching**: Don't rely solely on keyword matching
5. **Provide multi-select UI**: Allow users to install multiple plugins at once
6. **Track execution context**: Remember what plugins are being compared
7. **Generate comprehensive reports**: Make comparison results actionable

## Success Criteria

A successful plugin discovery interaction:

✅ User describes need clearly or vaguely
✅ AI understands intent through semantic matching
✅ Relevant plugins identified from all marketplaces
✅ Recommendations presented with clear reasoning
✅ User selects plugins easily (multi-select)
✅ Installation completes successfully
✅ User reminded to restart
✅ Plugins load correctly after restart

A successful plugin comparison:

✅ Task clearly defined
✅ Relevant installed plugins identified
✅ All plugins tested fairly with same inputs
✅ Results collected across multiple dimensions
✅ AI analysis provides clear insights
✅ Recommendation actionable and justified
✅ Report helps user make informed decision
