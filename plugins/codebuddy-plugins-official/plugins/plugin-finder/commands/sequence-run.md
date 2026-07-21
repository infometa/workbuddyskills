---
description: 多插件协同分步完成复杂任务 - 每步多插件并行执行并智能汇总
argument-hint: [任务描述]
allowed-tools: Read, Bash(ls:*, /plugin:*), Task, Write, AskUserQuestion
model: sonnet
---

# Multi-Plugin Sequential Collaboration

Orchestrate multiple plugins to collaboratively complete complex task: "$ARGUMENTS"

## Overview

Unlike `/multi-run` which compares plugins on the same task, `sequence-run` breaks down complex tasks into steps, with multiple plugins working together on each step. Results are intelligently synthesized before proceeding to the next step.

---

## Step 1: Mode Selection

First, ask user to select execution mode:

```
AskUserQuestion:
  header: "执行模式"
  question: "请选择任务执行模式："
  options:
    - label: "全自动模式"
      description: "AI 自动完成所有步骤，直接输出最终结果"
    - label: "交互确认模式"
      description: "每步完成后暂停，让您确认或修正结果后再继续"
```

Store selection as `$EXECUTION_MODE`:
- "全自动模式" → `auto`
- "交互确认模式" → `interactive`

---

## Step 2: Task Decomposition

Analyze the task and break it into sequential steps.

**Deep Analysis Process:**

1. **Understand the goal**: What is the user trying to achieve?
2. **Identify dependencies**: What must happen before what?
3. **Consider completeness**: What steps ensure high-quality output?
4. **Evaluate parallelization**: Which parts can benefit from multiple perspectives?

**Decomposition Output Format:**

```
任务分析：$ARGUMENTS

识别到的步骤：

步骤 1: [步骤名称]
  目标: [这一步要完成什么]
  输入: [需要什么输入]
  输出: [产出什么]
  
步骤 2: [步骤名称]
  目标: [这一步要完成什么]
  输入: [上一步的输出 + 其他]
  输出: [产出什么]

...

步骤 N: [最终步骤]
  目标: [整合并输出最终成果]
  输入: [前面步骤的汇总]
  输出: [最终交付物]
```

**Example Task Decomposition:**

```
任务：帮我分析这个项目的代码质量并生成改进方案

步骤 1: 代码扫描
  目标: 全面扫描代码库，识别问题
  输入: 项目源代码
  输出: 问题列表（安全、性能、代码风格等）

步骤 2: 问题分类与优先级
  目标: 对问题进行分类和优先级排序
  输入: 步骤1的问题列表
  输出: 分类优先级报告

步骤 3: 改进方案生成
  目标: 针对高优先级问题生成具体改进方案
  输入: 步骤2的优先级报告
  输出: 详细改进方案

步骤 4: 综合报告
  目标: 整合所有分析，输出完整报告
  输入: 所有步骤的输出
  输出: 最终质量分析与改进报告
```

---

## Step 3: Plugin Recommendation Per Step

For each step, identify and recommend relevant plugins.

**Read installed plugins:**

```bash
/plugin list
```

**For CodeBuddy, also check:**
- Marketplace registries: `~/.codebuddy/plugins/known_marketplaces.json`
- Extract installed plugin names from manifest

**Plugin Matching Process:**

For each step:
1. Analyze step requirements (goal, input, output)
2. Match against plugin capabilities:
   - Description semantic matching
   - Keywords/category matching
   - Known strengths (from previous usage)
3. Score relevance (0-100)
4. Select plugins scoring > 50

**Present Recommendations via AskUserQuestion:**

For each step, ask user to select plugins:

```
AskUserQuestion:
  header: "步骤 1"
  question: "【代码扫描】请选择参与此步骤的插件（可多选）："
  multiSelect: true
  options:
    - label: "code-review@claude-plugins-official"
      description: "全面代码审查，擅长发现逻辑问题和最佳实践 [推荐度: 95]"
    - label: "security-guidance@claude-plugins-official"
      description: "专注安全漏洞检测，OWASP 标准 [推荐度: 90]"
    - label: "lint-master@marketplace"
      description: "代码风格检查，支持多种语言 [推荐度: 85]"
```

**Collect all step selections before execution:**

Store as structured plan:
```
$EXECUTION_PLAN = {
  "steps": [
    {
      "name": "代码扫描",
      "goal": "全面扫描代码库，识别问题",
      "plugins": ["code-review@claude-plugins-official", "security-guidance@claude-plugins-official"],
      "input": "项目源代码",
      "output_type": "问题列表"
    },
    ...
  ]
}
```

---

## Step 4: Sequential Execution with Parallel Plugin Calls

Execute each step in sequence. Within each step, call selected plugins in parallel.

### 4.1 Step Execution Loop

```
for each step in $EXECUTION_PLAN.steps:
    
    # Show progress
    display: "
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📍 执行步骤 {step.index}/{total}: {step.name}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    目标: {step.goal}
    参与插件: {step.plugins}
    "
    
    # Parallel plugin execution
    results = parallel_execute(step.plugins, step.input)
    
    # Synthesize results
    synthesized = synthesize_results(results)
    
    # Mode-specific handling
    if $EXECUTION_MODE == "interactive":
        confirmed = ask_user_confirmation(synthesized)
        step.output = confirmed
    else:
        step.output = synthesized
    
    # Prepare input for next step
    next_step.input = step.output
```

### 4.2 Parallel Plugin Execution

Use Task tool to execute plugins concurrently:

```
For step with plugins [plugin1, plugin2, plugin3]:

Task 1: plugin1 execution
  subagent_type: "general-purpose"
  prompt: "Using {plugin1}, execute: {step.goal}
           Input context: {step.input}
           Expected output: {step.output_type}"

Task 2: plugin2 execution  
  subagent_type: "general-purpose"
  prompt: "Using {plugin2}, execute: {step.goal}
           Input context: {step.input}
           Expected output: {step.output_type}"

Task 3: plugin3 execution
  subagent_type: "general-purpose"
  prompt: "Using {plugin3}, execute: {step.goal}
           Input context: {step.input}
           Expected output: {step.output_type}"

# Execute all tasks in parallel (single message with multiple Task calls)
```

### 4.3 Result Collection

For each plugin execution, collect:
- Raw output content
- Execution success/failure
- Unique findings/contributions
- Confidence level (if applicable)

---

## Step 5: Intelligent Result Synthesis

For each step, intelligently synthesize results from multiple plugins.

### Synthesis Strategies

**Strategy Selection (AI decides based on output nature):**

1. **取长补短 (Complementary Merge)**
   - When: Plugins provide different aspects of analysis
   - Method: Combine unique contributions from each plugin
   - Example: Security plugin finds XSS, code-review finds logic errors → merge both

2. **共识优先 (Consensus Priority)**
   - When: Plugins provide overlapping findings
   - Method: Prioritize issues identified by multiple plugins
   - Example: 3 plugins flag same function as problematic → high confidence

3. **质量择优 (Quality Selection)**
   - When: One plugin output is clearly superior
   - Method: Use the best output, note others as supplementary
   - Example: Plugin A gives detailed fix, Plugin B only reports issue → use A

4. **结构化整合 (Structured Integration)**
   - When: Outputs have different formats
   - Method: Extract and restructure into unified format
   - Example: JSON output + Markdown output → unified report

### Synthesis Process

```
analyze_outputs(results):
    
    # Detect output characteristics
    - Are outputs complementary or overlapping?
    - Is one clearly more comprehensive?
    - Do they agree or conflict?
    
    # Apply appropriate strategy
    if complementary:
        merge_unique_contributions()
    elif overlapping_with_agreement:
        strengthen_consensus_findings()
    elif one_superior:
        select_best_with_supplements()
    elif conflicting:
        present_both_perspectives_with_analysis()
    
    # Generate synthesis summary
    return {
        "synthesized_output": ...,
        "synthesis_strategy": "取长补短 | 共识优先 | 质量择优 | 结构化整合",
        "plugin_contributions": {
            "plugin1": "贡献了X、Y",
            "plugin2": "贡献了Z",
            "best_performer": "plugin1 (覆盖最全面)"
        }
    }
```

### Synthesis Output Format

```
┌─────────────────────────────────────────────────────────────┐
│ 步骤 1 汇总：代码扫描                                        │
├─────────────────────────────────────────────────────────────┤
│ 汇总策略：取长补短                                           │
│                                                             │
│ 各插件贡献：                                                 │
│   • code-review: 发现 8 个逻辑问题、5 个性能问题            │
│   • security-guidance: 发现 3 个安全漏洞                    │
│   • lint-master: 发现 12 个代码风格问题                     │
│                                                             │
│ 综合结果：                                                   │
│   共识问题 (多插件确认): 2 个                                │
│   独特发现: 26 个                                           │
│   总计: 28 个问题                                           │
│                                                             │
│ 最佳贡献者：code-review (覆盖面最广)                         │
└─────────────────────────────────────────────────────────────┘

[详细汇总内容...]
```

---

## Step 6: Interactive Confirmation (If Enabled)

When `$EXECUTION_MODE == "interactive"`:

After each step synthesis, ask user:

```
AskUserQuestion:
  header: "确认步骤结果"
  question: "步骤「{step.name}」已完成，请确认或修正："
  options:
    - label: "确认，继续下一步"
      description: "接受当前汇总结果，继续执行"
    - label: "需要调整"
      description: "我想修改或补充一些内容"
    - label: "重新执行此步骤"
      description: "对结果不满意，重新运行"
    - label: "跳过此步骤"
      description: "此步骤不需要，直接进入下一步"
```

**Handle user feedback:**
- "确认" → Proceed with current output
- "需要调整" → Ask for specific adjustments, incorporate into output
- "重新执行" → Re-run step with same or different plugins
- "跳过" → Mark step as skipped, proceed

---

## Step 7: Final Output Generation

After all steps complete:

### Generate Comprehensive Report

```markdown
# 任务完成报告

## 任务描述
$ARGUMENTS

## 执行概览

| 步骤 | 名称 | 参与插件 | 汇总策略 | 状态 |
|------|------|----------|----------|------|
| 1 | 代码扫描 | 3 个 | 取长补短 | ✅ |
| 2 | 问题分类 | 2 个 | 共识优先 | ✅ |
| 3 | 方案生成 | 2 个 | 质量择优 | ✅ |
| 4 | 综合报告 | 1 个 | - | ✅ |

## 插件贡献统计

| 插件 | 参与步骤 | 主要贡献 | 被采纳率 |
|------|----------|----------|----------|
| code-review | 1, 2 | 逻辑问题识别 | 85% |
| security-guidance | 1, 3 | 安全漏洞分析 | 90% |
| lint-master | 1 | 代码风格检查 | 70% |

## 各步骤详情

### 步骤 1: 代码扫描
[步骤详细内容...]

### 步骤 2: 问题分类
[步骤详细内容...]

...

## 最终成果

[综合所有步骤的最终输出]

---

## 执行统计

- 总步骤数: N
- 参与插件数: M
- 执行模式: 全自动 / 交互确认
- 总耗时: X 分钟
- 执行时间: [timestamp]
```

### Display Summary to User

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 任务完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 任务: $ARGUMENTS

📊 执行统计:
   • 完成步骤: 4/4
   • 参与插件: 6 个
   • 执行模式: 全自动

🏆 插件贡献排名:
   1. code-review@claude-plugins-official - 贡献最多
   2. security-guidance@claude-plugins-official - 安全专家
   3. lint-master@marketplace - 风格检查

📄 详细报告: sequence-run-report-[timestamp].md

💡 提示: 如果对某个步骤结果不满意，可以使用交互模式重新执行：
   /plugin-finder:sequence-run "您的任务" 并选择"交互确认模式"
```

---

## Edge Cases

### No Relevant Plugins Found

```
😔 未找到与任务相关的插件。

建议:
1. 使用 /plugin-finder:search 搜索并安装相关插件
2. 检查任务描述是否清晰
3. 尝试将任务拆分为更具体的子任务

💡 或者尝试 /plugin-finder:wish 许愿您需要的功能！
```

### Only One Plugin Per Step

```
⚠️ 步骤「{step.name}」只有 1 个相关插件。

单插件模式将无法发挥多插件协同优势。

选项:
1. 继续使用单插件执行
2. 搜索更多相关插件
3. 跳过此步骤
```

### Plugin Execution Failed

```
⚠️ 步骤「{step.name}」中部分插件执行失败：

成功:
  ✅ plugin1@marketplace1
  ✅ plugin2@marketplace2

失败:
  ❌ plugin3@marketplace3
     错误: [error message]

处理方式:
- 使用成功插件的结果继续
- 如需重试失败插件，请选择"重新执行此步骤"
```

### Conflicting Results

```
⚠️ 插件结果存在冲突：

plugin1 认为: [观点A]
plugin2 认为: [观点B]

AI 分析:
- 冲突原因: [分析]
- 建议采纳: plugin1 的观点
- 理由: [说明]

如需人工裁决，请选择"需要调整"
```

---

## Configuration Support

Check user configuration `~/.codebuddy/.local.md`:

```yaml
# sequence-run 配置
sequence_run:
  default_mode: auto | interactive
  max_plugins_per_step: 5
  synthesis_verbosity: brief | detailed
  save_reports: true
  report_path: ./reports/
```

Apply configuration:
- `default_mode`: Skip mode selection if set
- `max_plugins_per_step`: Limit plugin recommendations
- `synthesis_verbosity`: Control synthesis detail level
- `save_reports`: Auto-save reports to file
- `report_path`: Custom report save location

---

## Success Criteria

✅ Task successfully decomposed into logical steps
✅ Relevant plugins identified for each step
✅ User can select multiple plugins per step
✅ Plugins executed in parallel within each step
✅ Results intelligently synthesized
✅ Interactive mode works when enabled
✅ Final comprehensive report generated
✅ Plugin contributions tracked and attributed
✅ User understands what each plugin contributed
