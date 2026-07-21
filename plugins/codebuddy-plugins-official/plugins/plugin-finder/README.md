# Plugin Finder

智能插件发现和管理助手，帮助用户从众多插件市场中轻松发现、安装和比较插件。

## 功能特性

### 🔍 智能插件搜索
- AI 语义理解用户需求
- 自动匹配最相关的插件
- 支持从所有已添加的 marketplace 搜索
- 同时支持 CodeBuddy 和 Claude 平台

### 🧠 智能多维度任务分析（smart-search）
- 深度分析任务，分解为多个能力维度
- 为每个能力维度推荐相关插件
- 多问题多选形式呈现（核心功能 + 辅助能力）
- 批量安装用户选中的所有插件

### 🔎 插件详情查看
- 查看插件的所有组件（commands、agents、skills、hooks、mcp）
- 了解每个组件的功能和用途
- 掌握插件的核心实现思路
- 支持查看所有 marketplace 中的插件

### 📦 便捷插件安装
- 多选批量安装插件
- 自动处理依赖关系
- 安装后自动提示重启

### 🔄 多插件比较
- 并行执行同一任务
- AI 智能分析比较结果
- 生成详细对比报告
- 帮助用户选择最适合的插件

### 🔗 多插件协同执行
- 将复杂任务分解为多个步骤
- 每步推荐多个插件，用户可多选
- 并行执行后智能汇总结果
- 取长补短，综合各插件优势
- 支持全自动和交互确认两种模式

### 🤖 智能推荐
- 自动识别用户需求
- 主动推荐相关插件
- 可配置推荐频率和阈值

### 💡 插件许愿
- 找不到需要的插件？可以许愿！
- 自动生成详细的需求邮件
- 直接反馈给 CodeBuddy 团队
- 帮助改进插件生态

## 使用方法

### 搜索插件

```bash
/plugin-finder:search "我需要一个代码审查插件"
```

AI 会理解您的需求，推荐最相关的插件，您可以多选安装。

### 智能多维度搜索

```bash
/plugin-finder:smart-search "我想做一个自动化测试流程"
```

系统会：
1. 深度分析您的任务需求
2. 分解为多个能力维度（如：测试框架、覆盖率分析、CI/CD 集成）
3. 每个维度推荐相关插件，您可以多选
4. 批量安装选中的所有插件

### 查看插件详情

想了解某个插件有哪些功能和机制？

```bash
/plugin-finder:info plugin-name
```

或指定 marketplace：

```bash
/plugin-finder:info plugin-name@marketplace-name
```

系统会展示：
- 📦 插件基本信息（名称、版本、作者、描述）
- 🛠️ 组件统计（commands、agents、skills、hooks、mcp 数量）
- 📋 每个组件的详细说明
- 💡 功能描述和使用场景
- 🔧 核心实现思路

### 手动安装插件

```bash
/plugin-finder:install plugin-name@marketplace-name
```

支持批量安装：

```bash
/plugin-finder:install plugin1@market1 plugin2@market2
```

### 许愿新插件

找不到您需要的插件？可以许愿！

```bash
/plugin-finder:wish "我需要一个能自动生成 API 文档的插件"
```

系统会：
1. 理解并整理您的需求
2. 生成详细的许愿邮件
3. 保存到本地文件
4. 提供发送指引

邮件发送到：📧 **codebuddy@tencent.com**

我们会认真考虑每一个用户的需求！

### 多插件比较

```bash
/plugin-finder:multi-run "审查这段代码的安全问题"
```

系统会：
1. 识别所有相关的已安装插件
2. 并行执行任务
3. 收集和比较结果
4. 生成详细的对比报告

### 多插件协同执行

```bash
/plugin-finder:sequence-run "分析这个项目的代码质量并生成改进方案"
```

与 `multi-run` 不同，`sequence-run` 会：
1. 将复杂任务分解为多个步骤
2. 每步推荐多个相关插件，您可以多选
3. 每步并行执行选中的插件
4. 智能汇总各插件结果（取长补短/共识优先/质量择优）
5. 用汇总结果进入下一步
6. 生成综合报告，追踪各插件贡献

**执行模式：**
- **全自动模式**：AI 自动完成所有步骤，直接输出最终结果
- **交互确认模式**：每步完成后暂停，让您确认或修正后再继续

## 配置

创建 `~/.codebuddy/.local.md` 文件配置插件行为：

```yaml
---
auto_recommend: true
recommendation_threshold: medium
show_install_count: true
preferred_marketplaces:
  - codebuddy-plugins-official
  - claude-plugins-official

# sequence-run 配置
sequence_run:
  default_mode: auto  # auto | interactive
  max_plugins_per_step: 5
  synthesis_verbosity: detailed  # brief | detailed
  save_reports: true
---
```

### 配置项说明

- `auto_recommend`: 是否自动推荐插件（默认 true）
- `recommendation_threshold`: 推荐阈值 - high/medium/low（默认 medium）
- `show_install_count`: 是否显示插件安装量（默认 true）
- `preferred_marketplaces`: 优先搜索的 marketplace 列表

#### sequence-run 配置
- `sequence_run.default_mode`: 默认执行模式 - auto/interactive（默认 auto）
- `sequence_run.max_plugins_per_step`: 每步最多推荐的插件数（默认 5）
- `sequence_run.synthesis_verbosity`: 汇总详细程度 - brief/detailed（默认 detailed）
- `sequence_run.save_reports`: 是否自动保存报告（默认 true）

## 工作原理

### 数据源
- CodeBuddy: `~/.codebuddy/plugins/known_marketplaces.json`
- Claude: `~/.claude/plugins/known_marketplaces.json`

### 推荐算法
使用 AI 语义理解，综合分析：
- 插件描述（description）
- 关键词（keywords）
- 分类（category）
- 标签（tags）

### 安装机制
通过 CodeBuddy Code 内置命令：
```bash
/plugin install plugin-name@marketplace-name
```

## 组件说明

### Commands
- `search.md` - 搜索和推荐插件
- `smart-search.md` - 智能多维度任务分析搜索
- `install.md` - 手动安装插件
- `info.md` - 查看插件详情
- `wish.md` - 许愿新插件
- `multi-run.md` - 多插件并行比较
- `sequence-run.md` - 多插件协同分步执行

### Agents
- `plugin-recommender.md` - 智能推荐 agent

### Skills
- `plugin-discovery/` - 插件发现和管理的核心知识

### Hooks
- `hooks.json` - UserPromptSubmit hook，自动识别插件需求

## 注意事项

- 安装插件后需要重启 CodeBuddy Code 才能生效
- 建议定期更新 marketplace 以获取最新插件信息
- 首次使用建议配置 `preferred_marketplaces` 提升搜索速度

## 许可证

MIT License
