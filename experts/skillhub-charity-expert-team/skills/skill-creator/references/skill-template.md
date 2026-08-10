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

> **辅助文档说明**：WorkBuddy 上架时仅识别 `SKILL.md`、`references/`、`scripts/` 作为标准上架内容。

---

## 二、SKILL.md 完整模板

> ⚠️ **本模板已内置 U1-U7 实战质量规则必备章节**（U1 description 负向排除 / U2 越界拒绝模板 / U3 工具能力契约 / U4 前置校验 / U5 失败降级阈值 / U6 数据真实性 / U7 完整交付保障）——按本模板生成即默认满足「一键检查清单」与解决方案专家步骤 4 的必含章节要求，**不得因"用户没要求"而删减这些章节**；仅标注「按需」的章节（🛠️ 工具能力契约）在技能确实不涉及受限工具/MCP/外部 API 时可省略。

```markdown
---
name: {Skill 英文id标识}
display_name: {Skill 中文名称}
display_name_en: {Skill 英文名称}
description: {Skill 中文描述：一句话说清定位 + 领域限定关键词 + 触发词；末尾必须附"⚠️ 不适用于：{相邻易混淆场景 1}、{相邻易混淆场景 2}、{相邻易混淆场景 3}"（U1 负向排除，至少 2-3 个）}
description_zh: {Skill 中文描述}
description_en: {Skill 英文描述}
category: {Skill 分类}
version: {Skill 版本}
author: {Skill 作者}
license: Tencent SSV Internal
---

# {Skill 中文名称}

## 概述

本 Skill 是一段话描述：是什么、解决什么问题、产出物是什么。让用户和 AI 一目了然此 Skill 的定位。

## 🎯 能力边界

### ✅ 能做什么

- {能力 1：动词开头，具体可衡量}
- {能力 2}
- {能力 3}
- {能力 4}

### ❌ 不做什么（越界即拒）

| 越界类型 | 示例 | 应答模板 |
|---|---|---|
| {高频误触发场景 1} | {示例} | "本 Skill 专注 {X}，不支持 {Y}。如您需要 {相关替代}，我可以帮上忙。" |
| {高频误触发场景 2} | {示例} | ... |
| {高频误触发场景 3} | {示例} | ... |

**越界拒绝标准模板**：
您好，您的需求 {简述意图} 超出本 Skill 能力范围。本 Skill 专注于 {X}，建议使用 {替代方案}。如有 {本领域} 相关需求（比如 {示例 1}、{示例 2}），我可以为您提供支持。

## 🛠️ 工具能力契约（按需：技能依赖受限工具/MCP/外部 API 时必备）

| 工具/依赖 | 可用范围 | 不可用时处置 | 禁止用途 |
|---|---|---|---|
| {工具或 MCP 服务名} | {可用功能/限定范围} | {降级方案} | ❌ {禁止的非标替代方式} |

- 核心依赖（MCP/API）不可用时提供手动操作指引，**禁止绕过到非标方式**（如用 Python 脚本绕过受限 Bash、用浏览器自动化替代 MCP）

## 核心约束

1. **{约束 1，如"数据来源唯一性"}**：{说明}
2. **{约束 2，如"渠道感知"}**：{说明}
3. **{约束 3，如"安全合规"}**：{说明}

## 工作流程

### Step 1：{阶段名}

{核心动作描述，3-5 句话}

**输入**：{用户提供的格式或字段}
**输出**：{Skill 产出的格式或字段}
**交互点**：{本步是否需要 AskUserQuestion 选项卡 / 纯文本继续}
**降级**：{此步失败时的兜底方案}

### Step 2：{阶段名}

（按需 3-6 步，每步明确输入/输出/交互点/降级）

## 🛡️ 实战质量规则（U4-U7 必备章节，不可删减）

### ✅ 执行前置校验（U4）

涉及外部资源（文件、API、MCP、网络）的步骤，必须"校验 → 告知 → 执行"：

1. 先确认资源可访问（文件已上传？API 可达？MCP 已授权？）
2. 校验失败立即告知用户具体问题 + 解决方案
3. 仅校验通过后才执行实际操作；**禁止在前置条件未满足时编造或推测结果**

### 🛡️ 失败降级机制（U5）

| 失败类型 | 阈值 | 降级动作 |
|---|---|---|
| 工具调用失败 | 1 次 | 立即告知用户限制，切换到可行替代方案 |
| 核心依赖（MCP/API）不可用 | 1 次 | 提供手动操作指引，禁止绕过到非标方式 |
| 用户连续否定产出 | 2 次 | 暂停重写，追问具体维度 + 索取参考案例 |
| 创意/方案类需求多轮无法满足 | 3 次 | 主动告知"非核心能力"，建议转用专业工具 |
| API 限流（429） | 1 次 | 友好提示等待时长，指数退避自动重试 |

- ❌ 反复重试同类工具（≥ 2 次同类失败视为缺陷）
- ❌ 把原始 API 错误 JSON 直接展示给用户

### 🚫 数据真实性约束（U6）

- **提取型场景**（OCR/解析/读取）：未实际读取文件时禁止输出"提取结果"；禁止根据文件名、上下文猜测内容；多次失败时禁止反复输出相同的虚假数据
- **生成型场景**（润色/改写/扩展）：禁止添加原文未提及的具体对象（人物、机构、合作方）；禁止编造数据、数字、覆盖范围；含新增事实时必须输出「新增内容标注表」，并设用户审核闸门（用户确认后才进入下一步）

### 📦 完整交付保障（U7）

- 单次输出预计 > 2500 字时**主动分段**（标注"第 N/M 部分"），用户确认后从断点继续，禁止重复已输出内容
- 遇到外部错误（API 限流、超时、404 等）翻译为用户友好描述，**禁止直接展示原始 JSON 错误**
- 结构化输出（Excel/JSON/表格）按本文件声明的格式规范自检（如 Excel 汇总行用公式而非硬编码数值、日期列用 datetime 类型）

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

- **API 密钥**：本 Skill {不直接处理 / 通过环境变量 XXX_API_KEY 引入 / 通过 MCP 配置 ...}；禁止在 SKILL.md 或 scripts 中硬编码
- **敏感信息**：涉及身份证号、手机号、签字盖章件、AppSecret 时，必须以占位符或脱敏后形式处理
- **文件读写**：仅在 {范围说明，如"用户工作目录"} 内读写文件；禁止读取 ~/.ssh、~/.aws 等敏感目录
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

### 4.2.1 跨平台兼容约束（生成的脚本必须满足）

Skill 的终端用户可能使用 macOS、Linux 或 Windows，生成的 `scripts/` 及 SKILL.md 中的调用命令必须保证三端可用：

- ✅ **优先用 Python 实现**：同一份 `.py` 脚本三端行为一致，是最稳妥的跨平台方案；SKILL.md 中调用命令写 `python3 scripts/xxx.py` 时，必须同时注明"Windows 若无 `python3` 命令（只注册了 `python`），改用 `python scripts/xxx.py`"
- ✅ 文件路径用 Python 的 `pathlib` 拼接，不手写 `/` 或 `\` 分隔符；文件读写显式指定 `encoding="utf-8"`（Windows 默认 GBK，不指定会乱码）
- ❌ 避免把 `.sh` / bash 脚本作为唯一实现（Windows 原生不支持，用户需额外装 Git Bash/WSL）；如确需 bash，必须同时提供 Windows 可执行的替代（PowerShell 版或 Python 版）
- ❌ 避免在脚本或 SKILL.md 正文中直接调用平台专属命令：`sips`（仅 macOS）、`cp`/`mv`/`grep`/`sed`（Windows 无）、`Copy-Item`（仅 PowerShell）；必须使用时需给出各平台替代命令
- ✅ 依赖的外部命令行工具（如 ffmpeg、pandoc）需在 SKILL.md 中声明三端安装方式（如 `brew` / `apt` / `choco`）

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
# 1. 安装依赖（按你的环境选择）：
#    通用（含 Windows）：pip install cairosvg
#    macOS/Linux 若报 "externally-managed-environment"（PEP 668）：pip3 install cairosvg --break-system-packages
#    注意：--break-system-packages 仅 macOS Homebrew / 新版 Debian-Ubuntu 需要，Windows 和不报 PEP 668 错误的环境不要加此 flag
#
# 2. 渲染（macOS/Linux 用 python3；Windows 若无 python3 命令改用 python）
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

或者本地手动安装（按操作系统选对应命令）：

\`\`\`bash
# macOS / Linux
cp -r {skill-name} ~/.workbuddy/skills/
\`\`\`

\`\`\`powershell
# Windows（PowerShell）
Copy-Item -Recurse {skill-name} "$env:USERPROFILE\.workbuddy\skills\"
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
