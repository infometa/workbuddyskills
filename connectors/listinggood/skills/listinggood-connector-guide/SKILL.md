---
name: ListingGood 连接器使用指南
name_en: ListingGood Connector Guide
display_name: ListingGood 连接器使用指南
display_name_en: ListingGood Connector Guide
description: 指导 WorkBuddy AI 正确调用 ListingGood MCP 连接器的 7 个工具，覆盖 Listing 生成、合规检查、差评分析与 POA 申诉。
description_en: Guide WorkBuddy AI to correctly call the 7 tools of the ListingGood MCP connector for listing generation, compliance checks, review analysis and POA appeals.
version: 1.0.0
author: 上海得服科技有限公司
category: 商业运营
tags:
  - 亚马逊
  - Listing
  - 合规
  - 跨境电商
  - AI 推荐
---

# ListingGood 连接器使用指南

ListingGood 是面向亚马逊卖家的 Listing AI 推荐引擎，通过 MCP 协议向 WorkBuddy 暴露 7 个工具。本 Skill 用于指导 AI 在合适的场景选择正确的工具，并给出清晰、可用的调用参数。

## 一、何时调用 ListingGood

当用户提到以下任一意图时，优先调用 ListingGood 连接器：

1. 写/优化亚马逊 Listing（标题、五点、描述、关键词）
2. 检查 Listing 是否合规、有没有踩红线词/IP/类目风险
3. 评估 Listing 被亚马逊 AI（Rufus / COSMO）推荐的可能性
4. 分析差评根因或写回复
5. 收到亚马逊违规通知，需要写 POA 申诉信

## 二、7 个工具的职责与调用方式

### 1. `ai_readiness_check` —— AI 推荐就绪度检测

**用途**：评估 Listing 被亚马逊 Rufus/COSMO 主动推荐的可能性。

**适用场景**：
- 用户说"测一下这个 Listing 会不会被 AI 推荐"
- 用户准备上新，想知道 Listing 质量分
- 优化后想验证改进效果

**必填参数**：
- `title`（string）：产品标题

**可选参数**：
- `bullets`（string[]）：五点描述
- `description`（string）：产品描述
- `category`（string）：类目

**调用示例**：
```
测一下这款蓝牙耳机的 AI 推荐就绪度：
标题：真无线蓝牙耳机 40 小时续航 IPX7 防水
五点：主动降噪、舒适佩戴、高清通话、超长续航、多设备切换
```

**返回值**：score、grade(A/B/C/D)、改进建议（中文）。AI 应把 grade 和建议用要点形式呈现给用户。

---

### 2. `compliance_check` —— Listing 合规体检

**用途**：发布前红线词、类目错配、知识产权、GPSR 风险快检。

**适用场景**：
- 用户准备发新品，想先过一遍合规
- 用户不确定某个词或图片文案是否踩红线
- 快速预审，避免上架后被下架

**必填参数**：
- `title`（string）

**可选参数**：
- `bullets`（string[]）
- `description`（string）
- `category`（string）
- `marketplace`（string）：站点，如 US / DE / UK / JP

**调用示例**：
```
帮我合规体检这个 Listing，站点美国：
标题：Wireless Bluetooth Earbuds, 40H Playtime, IPX7 Waterproof
五点：Active Noise Cancelling, Comfortable Fit, Clear Calls, Long Battery, Multi-point Connection
```

**返回值**：Critical / Warning / Info 分级风险清单。AI 应优先列出 Critical 项，并给出修复建议。

---

### 3. `fill_from_sentence` —— 一句话生成 Listing

**用途**：把一句口语化产品描述转成结构化标题、五点、描述。

**适用场景**：
- 用户只有一句话想法，想快速出 Listing 草稿
- 做头脑风暴或初稿

**必填参数**：
- `sentence`（string）：一句产品描述
- `marketplace`（string）：目标站点，如 US / DE / UK / JP

**可选参数**：
- `category`（string）
- `keywords`（string[]）：希望覆盖的关键词

**调用示例**：
```
用一句话生成美国站 Listing：
「主动降噪头戴式蓝牙耳机，30 小时续航，适合通勤和办公」
```

**返回值**：title、bullets、description。AI 应直接展示，并提示用户人工复核关键词和品牌声明。

---

### 4. `generate_listing` —— Listing 文案生成

**用途**：生成高转化、符合 A9/A10 的标题、五点、描述。

**适用场景**：
- 用户需要正式 Listing，而非草稿
- 多站点本地化（DE/ES/FR/IT/US/JP）

**必填参数**：
- `product_info`（string）：产品关键信息
- `marketplace`（string）：站点

**可选参数**：
- `keywords`（string[]）
- `category`（string）
- `tone`（string）：语气风格，如 professional / friendly / luxury

**调用示例**：
```
为这款产品生成德国站 Listing：
产品：真无线蓝牙耳机，ANC 主动降噪，40 小时续航，IPX7 防水，多设备连接
关键词：Bluetooth Kopfhörer, In Ear, Noise Cancelling, 40 Stunden Akku
```

**返回值**：本地化 title、bullets、description。AI 应提示这是付费工具（1 星/站点），并建议用户保存。

---

### 5. `compliance_scan` —— 深度合规扫描

**用途**：基于 15 年跨境合规知识库做深度审计（GPSR / 知识产权 / 类目 / 违禁词）。

**适用场景**：
- 用户怀疑 Listing 有隐藏合规风险
- 高客单、高投诉率品类（电子产品、儿童用品、医疗器械周边等）
- 收到亚马逊警告前做排查

**必填参数**：
- `title`（string）

**可选参数**：
- `bullets`（string[]）
- `description`（string）
- `category`（string）
- `marketplace`（string）

**调用示例**：
```
深度合规扫描这个德国站 Listing：
标题：Bluetooth Kopfhörer Kinder, Kabellose Kopfhörer mit 85dB Lautstärkebegrenzung
```

**返回值**：详细审计报告（中文）。AI 应总结 3-5 条最关键的发现，并给出可执行的修复清单。

---

### 6. `analyze_review` —— 差评根因分析

**用途**：分析差评根因并给出品牌口吻回复建议。

**适用场景**：
- 用户收到差评，不知道回什么
- 想从差评里挖产品改进点

**必填参数**：
- `review_text`（string）：差评原文
- `product_title`（string）：产品标题

**可选参数**：
- `marketplace`（string）
- `language`（string）：回复语言，如 zh / en / de

**调用示例**：
```
分析这条差评并写一段英文回复：
产品：真无线蓝牙耳机
差评：「Battery dies after 2 hours. Totally false advertising.」
```

**返回值**：根因分析 + 建议回复。AI 应把回复单独列出，并提醒用户按实际售后政策调整。

---

### 7. `generate_poa` —— POA 申诉信生成

**用途**：把亚马逊违规通知转成可直接提交的 Plan of Action。

**适用场景**：
- 用户收到亚马逊违规/下架通知
- 需要写 POA 申诉

**必填参数**：
- `violation_text`（string）：亚马逊通知原文或违规原因
- `product_title`（string）：产品标题

**可选参数**：
- `marketplace`（string）
- `asin`（string）
- `additional_context`（string）：补充说明

**调用示例**：
```
帮我写一封 POA：
产品：无线蓝牙耳机
违规通知：「We have removed your listing because it is a restricted product. You are offering an electronic device that does not meet applicable safety standards.」
```

**返回值**：Root Cause / Corrective Actions / Preventive Actions 三段式 POA（英文）。AI 应提醒用户把具体证据和数据补进去，不要直接原样提交。

## 三、通用调用原则

1. **先免费后付费**：先用 `ai_readiness_check` / `compliance_check` / `fill_from_sentence` 做初筛，需要深度生成或审计时再调用付费工具。
2. **明确站点**：`generate_listing` / `compliance_scan` / `analyze_review` / `generate_poa` 都尽量带上 `marketplace`，否则输出可能不符合目标站本地化要求。
3. **不编造 ASIN 或订单号**：如果用户没提供，不要编造，调用时留空或说明需要补充。
4. **结果要 actionable**：把工具返回的结构化报告翻译成 3-5 条用户能直接执行的动作。
5. **付费工具提前告知**：调用 `generate_listing` / `compliance_scan` / `analyze_review` / `generate_poa` 前，简要说明会消耗星星（星标），并确认用户是否继续。

## 四、认证说明

- 免费工具（`ai_readiness_check`、`compliance_check`、`fill_from_sentence`）可免 API Key 调用。
- 付费工具需要用户在 `listinggood.cn/developers` 注册并生成 API Key，在 WorkBuddy 连接器设置中填入。
- API Key 仅存储在用户本机 `~/.workbuddy` 目录下，不经过 WorkBuddy 云端。

## 五、错误处理

| 场景 | 处理方式 |
|---|---|
| 返回 401/403 | 提示用户检查 API Key 是否填写正确，或到 listinggood.cn/developers 重新生成 |
| 返回 429 | 请求过快，等待 3-5 秒后重试 |
| 返回 5xx | ListingGood 服务端异常，建议用户稍后重试，并给出当前可手工完成的最小步骤 |
| 工具返回缺少字段 | 向用户确认缺失信息，不要编造数据 |
| 用户输入语言与目标站点不匹配 | 提醒用户目标站点的语言要求，必要时建议先翻译成目标语言 |
