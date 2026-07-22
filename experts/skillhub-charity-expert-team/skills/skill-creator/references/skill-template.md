# WorkBuddy Skill 包模板（v2026.4 标准）

> 本文件提供符合 WorkBuddy Skill 生态合作介绍标准的完整 Skill 包模板。所有字段值默认使用中文（面向中文用户场景）。

---

## 一、目录结构

```
{skill-name}/
├── SKILL.md                  # ★ 核心：技能指令与元数据（必须）
├── references/               # 参考资料（推荐）
│   ├── api-guide.md          #   API 文档、字段类型
│   ├── examples.md           #   示例数据
│   └── workflow-detail.md    #   详细工作流模板
├── scripts/                  # 辅助脚本（可选）
│   └── helper.py             #   只在需要执行时使用，禁止硬编码密钥
├── icons/                    # 图标（推荐：提升市场列表点击率）
│   ├── icon.svg              #   矢量原图
│   └── icon.png              #   32×32 PNG（市场列表展示用）
├── CASES.md                  # Playbook 案例（推荐：获得发现页二次曝光）
├── README.md                 # 上架材料（推荐）
├── GUIDE.md                  # 用户使用指南（可选）
├── Prompt.md                 # 推荐提示词集（可选）
└── CHANGELOG.md              # 版本变更记录（推荐）
```

> **辅助文档说明**：`README.md`、`GUIDE.md`、`CASES.md`、`Prompt.md`、`CHANGELOG.md` 与 SKILL.md 同存于 git 仓库；WorkBuddy 上架时仅识别 `SKILL.md`、`references/`、`scripts/` 作为标准上架内容。如需离线分发为 tar.gz，使用 `pack.sh` 会自动将辅助文档移到 `{skill-name}_上架材料/` 子目录。

---

## 二、SKILL.md 完整模板

```markdown
---
name: tencent-ssv-techforgood
display_name: 公益虾🦞 — 腾讯技术公益智能助手
display_name_en: TechForGood Assistant 🦞
description: 专注公益机构数字化赋能的智能助手，围绕腾讯技术公益数字工具箱（techforgood.qq.com）为社会组织匹配免费或低成本数字化产品，支持需求诊断、产品推荐、申领指引、数字化实施参考与必要的机构合规边界提示。当用户提到公益机构数字化、社会组织工具选型、技术公益工具箱、公益虾时使用。
description_zh: 专注公益机构数字化赋能的智能助手，围绕腾讯技术公益数字工具箱（techforgood.qq.com）为社会组织匹配免费或低成本数字化产品。
description_en: Tencent Tech for Good digital assistant for NGO empowerment. Matches nonprofits with free or low-cost digital tools.
category: industry-consultant
version: 1.0.0
author: Tencent_SSV_Tech4Good
license: Tencent SSV Internal
---

# {Skill 中文名称}

## 概述

本 Skill 是一段话描述：是什么、解决什么问题、产出物是什么。让用户和 AI 一目了然此 Skill 的定位。

## 能力边界

### ✅ 能做什么

- {能力 1：动词开头，具体可衡量}
- {能力 2}
- {能力 3}
- {能力 4}

### ❌ 不做什么

- {边界 1：明确拒绝的场景}
- {边界 2}
- {边界 3}

## 核心约束

1. **{约束 1，如"数据来源唯一性"}**：{说明}
2. **{约束 2，如"渠道感知"}**：{说明}
3. **{约束 3，如"安全合规"}**：{说明}

## 工作流程

### Step 1：{阶段名}

{核心动作描述，3-5 句话}

**输入**：{用户提供的格式或字段}
**输出**：{Skill 产出的格式或字段}
**降级**：{此步失败时的兜底方案}

### Step 2：{阶段名}

（按需 3-6 步，每步明确输入/输出/降级）

## 参考资料

本 Skill 使用以下 references/ 文件：

| 文件 | 用途 | 触发条件 |
|---|---|---|
| `references/{file1}.md` | {用途} | {何时读取} |
| `references/{file2}.md` | {用途} | {何时读取} |

## 示例

### 示例 1：{典型场景名}

**输入**：

\`\`\`text
{用户的真实输入示例}
\`\`\`

**输出**：

\`\`\`text
{Skill 的真实输出示例（节选）}
\`\`\`

### 示例 2：{边界场景名}

（建议至少 1-2 组 input → output 示例，体现典型场景与边界场景）

## 安全要求

- **API 密钥**：本 Skill {不直接处理 / 通过环境变量 OPENAI_API_KEY 引入 / 通过 MCP 配置 ...}；禁止在 SKILL.md 或 scripts 中硬编码
- **敏感信息**：涉及身份证号、手机号、签字盖章件、AppSecret 时，必须以占位符或脱敏后形式处理
- **文件读写**：仅在 {范围说明，如"用户工作目录"} 内读写文件
- **网络请求**：仅访问 {官方域名清单}；不向未声明域名发起请求
- **数据可追溯**：涉及法规、案例、关键数字时附数据来源或快照日期；禁止编造事实

## 降级策略

- **网络不可用** → 使用 `references/{snapshot}.md` 中的本地快照数据，并告知用户"数据来自快照（{快照日期}）"
- **API 失败** → 提供降级方案 {如：手动指引 / 本地工具 / 替代路径}
- **工具不可用**（如某 SDK 缺失） → 透明告知用户当前能力限制，并给出替代建议

## 质量目标

- **意图命中率**：≥ 85%（用户输入关键词时正确触发本 Skill）
- **流程完成率**：≥ 90%（用户走完全流程的比例）
- **首屏响应**：≤ 2 秒（不让用户为前置流程干等）
- **数据准确率**：≥ 95%（关键字段来源可追溯）
```

---

## 三、references/ 标准文件示例

### 3.1 references/api-guide.md（API 调用规范）

```markdown
# {API 名称} 调用规范

> 数据快照日期：YYYY-MM-DD（如有时效性）

## 一、认证方式

- 认证类型：{Bearer Token / API Key / OAuth 2.0}
- 密钥获取：{通过环境变量 XXX_API_KEY 引入}
- 文档地址：{官方文档 URL}

## 二、核心接口

| 接口 | 方法 | 用途 | 触发条件 |
|---|---|---|---|
| `/api/v1/...` | GET | {用途} | {何时调用} |
| `/api/v1/...` | POST | {用途} | {何时调用} |

## 三、字段类型

（具体字段类型枚举、必填项、长度限制等）

## 四、错误码

| 码 | 含义 | 处理方式 |
|---|---|---|
| 400 | {含义} | {处理} |
| 429 | 限流 | 等待并重试 |
```

### 3.2 references/examples.md（示例数据）

```markdown
# 示例数据集

## 示例 1：{典型输入}

\`\`\`json
{
  "field1": "value1",
  "field2": "value2"
}
\`\`\`

## 示例 2：{边界输入}

（覆盖典型场景 + 边界场景 + 错误输入）
```

### 3.3 references/workflow-detail.md（详细工作流）

如果 SKILL.md 中的工作流过于复杂，可拆分到此文件，SKILL.md 仅保留概要。

---

## 四、scripts/ 目录（仅在需要时）

> ⚠️ PDF §3.1 强调："Skill 是纯文本的提示词工程，不需要写代码"。仅在确实需要执行命令行工具或数据处理时才使用 scripts/。

### 4.1 命名规范

- `scripts/{action}-{target}.{ext}`：动词-名词结构
- 例：`fetch-data.js`、`transform-csv.py`、`validate-schema.sh`

### 4.2 安全约束

- ❌ 禁止硬编码 API 密钥
- ❌ 禁止 `rm -rf` 等高风险操作
- ❌ 禁止下载外部可执行文件
- ✅ 通过环境变量读取密钥
- ✅ 在脚本头部注明：用途 / 输入 / 输出 / 依赖

### 4.3 调用示例

```python
# scripts/fetch-data.py
# 用途：从 {API} 拉取数据
# 输入：sys.argv[1] = 查询关键词
# 输出：标准输出 JSON
# 依赖：requests（pip install requests）

import os
import sys
import json
import requests

API_KEY = os.environ.get("MY_SERVICE_API_KEY")
if not API_KEY:
    print(json.dumps({"error": "MY_SERVICE_API_KEY 未配置"}), file=sys.stderr)
    sys.exit(1)

# ... 实际逻辑 ...
```

---

## 五、icons/ 目录（推荐）

### 5.1 32×32 SVG 模板

```svg
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
      <stop stop-color="#00C853"/>
      <stop offset="1" stop-color="#00A86B"/>
    </linearGradient>
  </defs>
  <rect width="32" height="32" rx="8" fill="url(#bg)"/>
  <!-- 居中放置代表性符号或首字母 -->
  <text x="16" y="22" text-anchor="middle"
        font-family="PingFang SC, Microsoft YaHei, sans-serif"
        font-size="16" font-weight="bold" fill="white">技</text>
</svg>
```

### 5.2 PNG 渲染脚本

```bash
# 需要先安装：pip3 install cairosvg --break-system-packages
python3 -c "
import cairosvg
cairosvg.svg2png(
    url='icons/icon.svg',
    output_width=32,
    output_height=32,
    write_to='icons/icon.png'
)
"
```

> 32×32 是 PDF §4.3 推荐的市场列表展示尺寸；建议同时提供 128×128 PNG 用于详情页。

---

## 六、CASES.md（Playbook 案例 — PDF §4.3 强烈推荐）

附带 ≥ 1 个 Playbook 案例可获得「发现页 — 案例卡片」二次曝光。每个案例采用五段式：

```markdown
# {Skill 中文名} — 实践 Playbook

---

## Playbook 1：{场景名}

> 🎯 **适用场景**：{描述}
> ⏱️ **预计耗时**：{X 分钟}

### ① 触发场景

{用户在什么情况下遇到此问题，含痛点清单}

### ② 推荐 Prompt

\`\`\`text
{用户可直接复制使用的 prompt 示例}
\`\`\`

### ③ 完整对话流

| 步骤 | Skill 动作 | 用户响应 |
|---|---|---|
| 1 | {动作描述} | {响应示例} |
| 2 | {动作描述} | {响应示例} |
| 3 | {动作描述} | {响应示例} |

### ④ 最终产出

> {展示 Skill 输出的关键内容，含表格、清单、文档片段等}

### ⑤ 价值点

- ✅ {价值 1}
- ✅ {价值 2}
- ✅ {价值 3}

---

## Playbook 2、3...

（建议 2-3 个案例覆盖不同场景）
```

---

## 七、README.md（上架材料推荐）

```markdown
# {Skill 中文名称}（{technical-name}）

> WorkBuddy Skill 上架包 · 符合《WorkBuddy Skill 生态合作介绍》v2026.4

## 概述

{一段话简介：本 Skill 解决什么问题、面向哪些用户、核心能力是什么}

## 安装

\`\`\`bash
# 在 WorkBuddy 对话中输入
@skill://{technical-name}
\`\`\`

或者本地手动安装：

\`\`\`bash
cp -r {skill-name} ~/.workbuddy/skills/
\`\`\`

## 快速上手

（3-5 个最简使用示例）

## 目录结构

\`\`\`
{tree 展示}
\`\`\`

## 参考资料索引

| 文件 | 用途 |
|---|---|
| `references/...` | ... |

## 上架自检清单

按 PDF v2026.4 §4 准入标准：

### 元数据完整性
- [x] `name`、`description`、`category`、`version`、`author` 齐全
- [x] `display_name` / `description_zh` 等推荐字段已填

### 内容质量
- [x] SKILL.md 正文 ≥ 200 字
- [x] 中文友好
- [x] 能力边界清晰
- [x] 工作流分步拆分
- [x] 至少 1 组 input → output 示例

### 安全要求
- [x] 不含 API 密钥硬编码
- [x] 涉及文件读写 / 网络请求已声明
- [x] 不含个人隐私、内部 URL

### 加分项
- [x] Playbook 案例 ≥ 1 个（CASES.md）
- [x] Skill 图标（icons/icon.png 32×32）
```

---

## 八、CHANGELOG.md（版本变更记录推荐）

```markdown
# 版本管理 / CHANGELOG

> **重要约定**：
> - `SKILL.md` 中 `version` 字段始终保持**与 WorkBuddy 市场公开版本一致**
> - 本地特性迭代**不立即**修改 `version`，只在本文件 `[未发布]` 章节追加条目
> - 想正式发版上架时直接修改 `SKILL.md` 的 `version` + commit + push（仓库已登记 git 路径，push 即上架）

## 当前公开版本

**1.0.0** — {YYYY-MM-DD} 首次上架

## [未发布]

（记录尚未发版的本地变更；想发版时把这里整理到新版本块下，并修改 SKILL.md 的 version + push）

### 内容更新
- ...

### 工程改造
- ...

### UX 优化
- ...

## 历史版本

### 1.0.0 — {YYYY-MM-DD}
- 上架 WorkBuddy 市场首版
- ...
```

---

## 九、生产参考样板

完整可用的 Skill 样板：

- 📂 `charity/skills/腾讯技术公益智能助手/` — 复杂工作流 + 完整 references/ + Playbook 案例 + 惰性更新机制
- 📂 `charity/skills/公益文书助手/` — 多平台适配 + 模板加载器
- 📂 `charity/skills/公益财会助手/` — OCR 脚本 + 复合工作流
- 📂 `charity/expert-creator/` — 工具型 Skill 标准模板（适合作为 skill-creator 自身的参考）

建议在创建新 Skill 时，先复制其中一个作为起点，再按需修改字段值。
