# Plugin Rules 标准

插件 `rules/` 目录下的规则文件标准，用于向 AI 助手声明插件能力和使用指导。

---

## 文件位置

```
plugins/<plugin-name>/rules/<plugin-name>_rules.md
```

示例：`plugins/data/rules/data_analysis.md`

---

## Frontmatter 格式

```yaml
---
description: <功能描述 + 激活条件>
alwaysApply: true
enabled: true
updatedAt: YYYY-MM-DDTHH:mm:ss.000Z
provider: 
---
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `description` | string | ✅ | 功能描述，说明何时激活该规则 |
| `alwaysApply` | boolean | ✅ | 始终设为 `true`，确保规则始终加载 |
| `enabled` | boolean | ✅ | 始终设为 `true` |
| `updatedAt` | string | ✅ | ISO 8601 时间戳，格式：`YYYY-MM-DDTHH:mm:ss.000Z` |
| `provider` | string | 可选 | 提供者名称，通常留空 |

### description 字段写法

**功能描述式**（推荐）：
```
Comprehensive [功能] workflows including [子功能1], [子功能2]. Use when [触发场景].
```

**触发词式**：
```
Use when user mentions: [keyword1], [keyword2], [中文关键词1], [中文关键词2].
```

**条件列表式**：
```
MUST USE when user wants to: [具体条件列表].
```

---

## 内容结构

规则内容统一使用 `<system_reminder>` 标签包裹：

```markdown
<system_reminder>
The user has selected the **<场景名称>** scenario.

**You have access to the <plugin-name>@cb-teams-marketplace plugin. 
Please make full use of this plugin's abilities whenever possible.**

## Available Capabilities
[核心能力列表，4-6 个]

## Skills Available
[可用技能清单，每条格式：`skill-name`: 描述]

## Usage Guidelines

**Core Principle: Maximize plugin usage** - [一句话说明使用原则]

1. [步骤1]
2. [步骤2]
...

[可选：Important Notes / Workflow / 注意事项]
</system_reminder>
```

### 各部分说明

| 部分 | 是否必需 | 说明 |
|------|----------|------|
| 场景声明 | ✅ | 告知 AI 当前处于哪个插件场景 |
| 插件能力声明 | ✅ | 强调充分使用插件，包含 `@cb-teams-marketplace` 标识 |
| Available Capabilities | ✅ | 列出插件核心能力（4-6 个） |
| Skills Available | ✅ | 列出所有可用技能名称及描述 |
| Usage Guidelines | ✅ | 具体使用步骤，首行必须是 Core Principle |
| Important Notes | 可选 | 关键注意事项、限制说明 |

---

## 完整示例

```markdown
---
description: Comprehensive data analysis workflows including SQL queries, data exploration, visualization (plotly prioritized), and dashboard building. Use when conducting data analysis tasks.
alwaysApply: true
enabled: true
updatedAt: 2026-02-06T14:15:00.000Z
provider: 
---

<system_reminder>
The user has selected the **Data Analysis (Visualization)** scenario. 

**You have access to the data@cb-teams-marketplace plugin with comprehensive data analysis capabilities. Please make full use of this plugin's abilities whenever possible.**

## Available Capabilities

- **Capability 1**: Description
- **Capability 2**: Description
- **Capability 3**: Description

## Skills Available

- `skill-name-1`: 技能描述
- `skill-name-2`: 技能描述

## Usage Guidelines

**Core Principle: Maximize plugin usage** - Actively use the plugin's skills and workflows.

1. **Step 1**: Description
2. **Step 2**: Description
3. **Step 3**: Description

**Note**: 补充说明（如不需要 MCP 配置等）
</system_reminder>
```

---

## 设计原则

1. **始终强调充分使用插件**：Guidelines 首行必须是 "Core Principle: Maximize plugin usage"
2. **清晰的能力声明**：列出所有可用技能，方便 AI 知道能调用什么
3. **具体的使用步骤**：不只说"使用插件"，要说"怎么用"
4. **alwaysApply 必须为 true**：确保规则在每次对话中都被加载

---

## 检查清单

迁移或新建插件时，rules 文件必须满足：

- [ ] 文件位置正确：`plugins/<name>/rules/<name>_rules.md`
- [ ] Frontmatter 包含所有必需字段
- [ ] `alwaysApply: true`
- [ ] `enabled: true`
- [ ] 内容用 `<system_reminder>` 标签包裹
- [ ] 包含 Available Capabilities 章节
- [ ] 包含 Skills Available 章节
- [ ] 包含 Usage Guidelines 章节，首行是 Core Principle
- [ ] 插件名称包含 `@cb-teams-marketplace` 标识
