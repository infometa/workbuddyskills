# Plugin Finder 开发文档

本文档面向希望理解、修改或扩展 plugin-finder 的开发者。

## 架构概览

### 组件结构

```
plugin-finder/
├── .codebuddy-plugin/
│   └── plugin.json           # 插件元数据
├── commands/                  # 用户命令
│   ├── search.md             # 搜索和推荐
│   ├── install.md            # 手动安装
│   └── multi-run.md          # 多插件比较
├── agents/                    # 自主代理
│   └── plugin-recommender.md # 智能推荐 agent
├── skills/                    # 知识库
│   └── plugin-discovery/
│       ├── SKILL.md          # 核心知识
│       ├── references/       # 详细文档
│       └── examples/         # 示例
├── hooks/                     # 事件钩子
│   └── hooks.json            # UserPromptSubmit hook
├── scripts/                   # 辅助脚本
│   └── search-plugins.sh     # 命令行搜索
└── .codebuddy/               # 用户配置
    └── .local.md.example     # 配置模板
```

### 数据流

```
用户输入
    ↓
[UserPromptSubmit Hook] → 判断是否需要推荐
    ↓                        ↓
继续对话          触发 plugin-recommender agent
                            ↓
                     读取 marketplace 数据
                            ↓
                     AI 语义匹配
                            ↓
                     展示推荐 (AskUserQuestion)
                            ↓
                     批量安装
                            ↓
                     提醒重启
```

## 核心组件详解

### 1. Skill: plugin-discovery

**位置：** `skills/plugin-discovery/SKILL.md`

**职责：**
- 提供插件发现和管理的核心知识
- 定义 marketplace 数据格式
- 说明语义匹配算法
- 指导安装流程
- 说明多插件比较方法

**关键内容：**
- Marketplace 结构和解析
- AI 语义匹配算法（描述 50分，关键词 30分，分类 15分，标签 5分）
- 双平台支持（CodeBuddy 和 Claude）
- 配置文件读取

**触发条件：**
当用户询问以下内容时触发：
- "推荐插件"
- "查找插件"
- "安装插件"
- "有什么插件"
- Plugin 相关问题

**引用的 references：**
- `marketplace-format.md` - 完整的 marketplace 格式规范

### 2. Command: search

**位置：** `commands/search.md`

**参数：** `[需求描述]`

**工作流程：**
1. 读取 marketplace 数据
   - CodeBuddy: `~/.codebuddy/plugins/known_marketplaces.json`
   - Claude: `~/.claude/plugins/known_marketplaces.json`

2. AI 语义匹配
   - 分析用户需求
   - 对每个插件评分
   - 选择得分 ≥40 的插件

3. 展示推荐
   - 使用 `AskUserQuestion` 工具
   - multiSelect: true
   - 格式化展示信息

4. 批量安装
   - 解析用户选择
   - 执行 `/plugin install plugin1@market1 plugin2@market2 ...`

5. 后续提醒
   - 显示安装结果
   - 提醒重启 CodeBuddy Code

**允许的工具：**
- Read（读取 marketplace 数据）
- AskUserQuestion（展示选项）
- Bash（执行安装命令）

**模型：** sonnet（平衡速度和质量）

### 3. Command: install

**位置：** `commands/install.md`

**参数：** `[plugin1@marketplace1] [plugin2@marketplace2] ...`

**工作流程：**
1. 解析参数
   - 提取 plugin@marketplace 对
   - 验证格式

2. 验证插件
   - 检查 marketplace 是否存在
   - 检查插件是否在 marketplace 中
   - 提供错误提示

3. 显示安装计划
   - 列出将要安装的插件
   - 显示版本、描述等信息

4. 执行安装
   - 批量安装命令
   - 监控输出

5. 报告结果
   - 成功/失败状态
   - 错误信息
   - 重启提醒

**允许的工具：**
- Read（验证插件）
- Bash（安装命令）

**模型：** haiku（快速执行）

### 4. Command: multi-run

**位置：** `commands/multi-run.md`

**参数：** `[任务描述]`

**工作流程：**
1. 识别相关插件
   - 列出已安装插件
   - AI 匹配任务需求
   - 选择相关插件（得分 >60）

2. 分析插件能力
   - 检查插件结构
   - 确定调用方法（agent/command/skill）
   - 优先级：agent > command > skill

3. 并行执行
   - 使用 Task 工具并发执行
   - 跟踪执行时间
   - 收集输出

4. 收集结果
   - 质量指标（完整性、准确性、深度）
   - 性能指标（执行时间）
   - 输出指标（格式、文件）
   - 用户体验

5. AI 分析比较
   - 跨多个维度比较
   - 生成详细报告
   - 提供推荐

6. 生成报告
   - Markdown 格式
   - 包含摘要表格
   - 详细分析
   - 推荐建议

**允许的工具：**
- Read（读取插件信息）
- Bash（列出插件）
- Task（并行执行）
- Write（生成报告）

**模型：** sonnet（需要复杂分析）

### 5. Agent: plugin-recommender

**位置：** `agents/plugin-recommender.md`

**角色：** Plugin Discovery Expert

**触发条件：**
用户表达功能需求但没有提到插件时。

**示例：**
- "我想检查代码质量" → 触发
- "如何自动化测试？" → 触发
- "帮我推荐插件" → 不触发（用 /plugin-finder:search）

**核心职责：**
1. 理解用户意图
2. 搜索 marketplace
3. 语义匹配插件
4. 展示推荐
5. 协助安装

**系统提示关键点：**
- 使用语义理解，不仅是关键词匹配
- 评分算法明确
- 清晰解释推荐理由
- 友好的用户交互
- 完整的错误处理

**允许的工具：**
- Read（marketplace 数据）
- AskUserQuestion（展示选项）
- Bash（安装命令）

**模型：** inherit（继承当前模型）

**颜色：** magenta（创意性任务）

### 6. Hook: UserPromptSubmit

**位置：** `hooks/hooks.json`

**事件：** UserPromptSubmit

**类型：** prompt（基于提示词的 Hook）

**功能：**
监听用户每次输入，判断是否需要推荐插件。

**判断逻辑：**
```
IF (用户表达需求 
    AND 需求具体 
    AND 未提及插件
    AND auto_recommend = true)
THEN 触发 plugin-recommender agent
ELSE 继续对话
```

**触发示例：**
- "我想检查代码质量" ✓
- "如何自动化测试？" ✓
- "需要部署工具" ✓
- "今天天气怎么样？" ✗ （非技术需求）
- "帮我推荐插件" ✗ （已提及插件）

**配置检查：**
Hook 会检查 `~/.codebuddy/.local.md` 中的 `auto_recommend` 设置。

**保守策略：**
只在明确、具体的需求时触发，避免过度打扰用户。

### 7. Script: search-plugins.sh

**位置：** `scripts/search-plugins.sh`

**用途：** 命令行快速搜索插件

**参数：** 搜索关键词

**功能：**
- 读取 CodeBuddy 和 Claude marketplace
- 使用 jq 进行 JSON 解析
- 大小写不敏感搜索
- 匹配 description、name、keywords、category
- 格式化输出结果

**使用方法：**
```bash
~/.codebuddy/plugins/local/plugin-finder/scripts/search-plugins.sh "keyword"
```

## 数据源

### Marketplace 数据结构

#### CodeBuddy Format

```json
{
  "marketplace-name": {
    "type": "git|directory|github",
    "source": {...},
    "installLocation": "/path/to/marketplace",
    "manifest": {
      "plugins": [
        {
          "name": "plugin-name",
          "description": "...",
          "category": "...",
          "keywords": [...],
          ...
        }
      ]
    }
  }
}
```

**关键字段：**
- `manifest.plugins` - 插件数组，包含所有插件元数据
- 数据已内嵌，无需额外读取文件

#### Claude Format

```json
{
  "marketplace-name": {
    "source": {...},
    "installLocation": "/path/to/marketplace"
  }
}
```

**注意：** Claude 格式可能没有内嵌 manifest，需要单独读取文件。

### 配置文件格式

**位置：** `~/.codebuddy/.local.md`

**格式：** Markdown with YAML frontmatter

```yaml
---
auto_recommend: true
recommendation_threshold: medium
show_install_count: true
preferred_marketplaces:
  - codebuddy-plugins-official
  - claude-plugins-official
comparison_output_format: markdown
preferred_plugins:
  - plugin1@market1
---

# 配置说明（可选）
...
```

## 语义匹配算法

### 评分系统

```
总分 = 描述匹配分 + 关键词匹配分 + 分类匹配分 + 标签匹配分

描述匹配分 (0-50):
  - 使用 AI 语义理解
  - 判断插件描述是否解决用户需求
  - 不仅仅是关键词匹配

关键词匹配分 (0-30):
  - 精确匹配：30分
  - 部分匹配：15分
  - 无匹配：0分

分类匹配分 (0-15):
  - 分类对应：15分
  - 相关分类：10分
  - 无关：0分

标签/名称匹配分 (0-5):
  - 标签匹配：5分
  - 名称相似：3分
  - 其他：0分
```

### 阈值

```
High threshold: ≥50分
Medium threshold: ≥40分
Low threshold: ≥30分
```

### 示例

```
用户需求: "代码质量检查"

Plugin: code-review@claude-plugins-official
- Description: "Automated code review with agents" 
  → AI 理解：高度相关 → 45分
- Keywords: ["review", "quality", "code"]
  → 精确匹配 → 30分
- Category: "productivity"
  → 相关分类 → 10分
- Total: 85分 ✅ 强烈推荐

Plugin: typescript-lsp@claude-plugins-official
- Description: "TypeScript language server"
  → AI 理解：弱相关 → 20分
- Keywords: ["typescript", "lsp"]
  → 无匹配 → 0分
- Category: "development"
  → 相关分类 → 10分
- Total: 30分 ⚠️ 低阈值推荐
```

## 扩展开发

### 添加新命令

1. 在 `commands/` 目录创建新文件：
```bash
touch commands/new-command.md
```

2. 添加 YAML frontmatter：
```yaml
---
description: 命令描述
argument-hint: [参数]
allowed-tools: Read, Write
model: sonnet
---
```

3. 编写命令内容（为 Claude 写的指令）

4. 重启 CodeBuddy Code

5. 测试：`/plugin-finder:new-command`

### 添加新 Agent

1. 在 `agents/` 目录创建文件：
```bash
touch agents/new-agent.md
```

2. 定义 frontmatter：
```yaml
---
name: new-agent
description: Use when... Examples: <example>...</example>
model: inherit
color: blue
tools: ["Read"]
---
```

3. 编写系统提示

4. 测试触发条件

### 修改 Skill

1. 编辑 `skills/plugin-discovery/SKILL.md`

2. 保持核心内容在 SKILL.md（<2000 词）

3. 详细内容移到 `references/`

4. 添加新的 reference 文件：
```bash
touch skills/plugin-discovery/references/new-topic.md
```

5. 在 SKILL.md 中引用

### 添加新 Hook

1. 编辑 `hooks/hooks.json`

2. 添加新事件类型：
```json
{
  "hooks": {
    "NewEvent": [
      {
        "name": "hook-name",
        "hooks": [...]
      }
    ]
  }
}
```

3. 测试触发

## 调试技巧

### 1. 查看 Marketplace 数据

```bash
# 查看 CodeBuddy marketplace
cat ~/.codebuddy/plugins/known_marketplaces.json | jq '.'

# 查看特定 marketplace
cat ~/.codebuddy/plugins/known_marketplaces.json | \
  jq '.["claude-plugins-official"].manifest.plugins'

# 搜索特定插件
cat ~/.codebuddy/plugins/known_marketplaces.json | \
  jq '.[] | .manifest.plugins[] | select(.name == "code-review")'
```

### 2. 测试语义匹配

在 CodeBuddy Code 中：
```
加载 plugin-discovery skill，然后测试匹配：

用户需求："代码审查"
分析每个插件的相关性
显示评分
```

### 3. 调试 Hook

```bash
# 启用 debug 模式（如果支持）
cc --debug

# 观察 Hook 触发
# 输入测试语句
# 查看是否触发 plugin-recommender
```

### 4. 验证配置

```bash
# 检查配置文件
cat ~/.codebuddy/.local.md

# 测试配置加载
# 在命令中读取配置并输出
```

### 5. 检查插件结构

```bash
# 验证文件存在
ls -la ~/.codebuddy/plugins/local/plugin-finder/

# 检查 JSON 语法
jq . ~/.codebuddy/plugins/local/plugin-finder/.codebuddy-plugin/plugin.json
jq . ~/.codebuddy/plugins/local/plugin-finder/hooks/hooks.json

# 验证 frontmatter
head -20 ~/.codebuddy/plugins/local/plugin-finder/commands/search.md
head -20 ~/.codebuddy/plugins/local/plugin-finder/agents/plugin-recommender.md
```

## 性能优化

### 1. Marketplace 缓存

当前实现直接读取文件。可优化为：
- 内存缓存 marketplace 数据
- 定期自动更新
- 增量更新机制

### 2. 语义匹配优化

- 使用更快的模型（haiku）进行初筛
- 只对高分插件进行详细分析
- 缓存常见查询结果

### 3. 并行执行优化

在 multi-run 中：
- 限制并发数量
- 实现超时机制
- 增量显示结果

## 测试

### 单元测试场景

**Command: search**
- [ ] 正确读取 marketplace 数据
- [ ] 语义匹配算法正确
- [ ] 多选 UI 正常工作
- [ ] 批量安装命令正确
- [ ] 错误处理完善

**Command: install**
- [ ] 参数解析正确
- [ ] 格式验证有效
- [ ] marketplace 验证工作
- [ ] 插件验证工作
- [ ] 批量安装成功
- [ ] 错误提示清晰

**Command: multi-run**
- [ ] 插件识别准确
- [ ] 并行执行正常
- [ ] 结果收集完整
- [ ] 比较分析合理
- [ ] 报告格式正确

**Agent: plugin-recommender**
- [ ] 触发条件准确
- [ ] 不会过度触发
- [ ] 推荐相关性高
- [ ] 用户交互流畅

**Hook: UserPromptSubmit**
- [ ] 正确识别需求
- [ ] 配置检查有效
- [ ] 不会误触发
- [ ] 性能影响小

### 集成测试场景

1. **完整搜索→安装流程**
   - 搜索插件
   - 多选安装
   - 重启验证

2. **自动推荐流程**
   - 表达需求
   - 触发推荐
   - 接受安装

3. **多插件比较流程**
   - 安装多个插件
   - 执行比较
   - 查看报告

## 贡献指南

### 代码规范

**Markdown:**
- 使用 GitHub Flavored Markdown
- 中英文混排时注意空格
- 代码块指定语言

**YAML:**
- 2 空格缩进
- 使用引号包裹字符串
- 布尔值小写

**Bash:**
- 使用 `set -euo pipefail`
- 添加错误处理
- 提供有用的错误信息

### 提交流程

1. Fork 或创建分支
2. 进行修改
3. 测试更改
4. 更新文档
5. 提交 PR

### 文档要求

修改时更新：
- README.md（如果功能变化）
- USAGE_GUIDE.md（如果用法变化）
- DEVELOPMENT.md（如果架构变化）
- CHANGELOG.md（记录变更）

## 未来规划

### 短期 (v0.2.0)
- [ ] 插件更新通知
- [ ] 插件依赖解析
- [ ] 收藏插件功能
- [ ] 使用历史记录

### 中期 (v0.3.0)
- [ ] Web UI 浏览
- [ ] 插件评分系统
- [ ] 社区推荐
- [ ] 插件集合

### 长期 (v1.0.0)
- [ ] 插件使用分析
- [ ] 团队协同功能
- [ ] 自定义 marketplace
- [ ] 插件发布工作流

## 维护

### 定期任务

**每周：**
- 检查 marketplace 更新
- 测试核心功能
- 查看用户反馈

**每月：**
- 更新依赖
- 审查性能
- 优化算法

**每季度：**
- 架构审查
- 重构优化
- 功能规划

### 问题追踪

使用 Issue 系统跟踪：
- Bug 报告
- 功能请求
- 性能问题
- 文档改进

---

**开发问题？**
- 查看代码注释
- 阅读 skill 文档
- 参考 plugin-dev@claude-plugins-official
- 联系维护者
