# Agency Workflow Skills 使用说明

这份说明写给第一次使用 Agency Workflow Skills 的人。你不需要懂广告公司内部流程，也不需要会写复杂提示词。只要按下面的步骤，把你的项目资料交给 Codex，它就会按照广告公司的岗位分工和工作顺序，带你从 Brief 走到策略、创意、文案、设计和提案整理。

## 1. 这套 Skills 是什么

Agency Workflow Skills 是一套给 Codex 使用的广告公司工作流 skills。它把一个广告项目里常见的 6 个岗位拆成 6 个 skill：

- `boss`: 总控角色，负责统筹完整流程。
- `account-executive`: AE 客服，负责收集 Brief、整理需求、发现缺失资料。
- `strategy-director`: 策略总监，负责定义问题、定位、洞察、策略和 Creative Brief。
- `creative-director`: 创意总监，负责创意方向、Big Idea 判断、卖稿逻辑和创意复核。
- `copywriter`: 文案，负责 campaign line、KV 文案、社媒文案、脚本、命名和提案表达。
- `designer`: 设计，负责视觉方向、KV 描述、moodboard、品牌视觉系统和 AI 生图 prompt。

你可以把它理解成：不是让 Codex 直接生成一堆内容，而是让 Codex 按广告公司的方式分工协作。

## 2. 它适合做什么

这套 skills 适合处理以下任务：

- 品牌全案
- 整合营销 Campaign
- 新品上市 Launch Campaign
- 品牌定位和策略推导
- 创意方向发散和筛选
- 小红书、微信、短视频等内容规划
- 品牌宣言、slogan、KV 文案、社媒文案
- 视觉方向、moodboard、AI 生图 prompt
- 提案 deck 页级结构和内容整理
- 品牌部日常内容制作和供应商沟通

它尤其适合两类人：

- 广告从业者：策略、创意、文案、设计、AE、品牌顾问、自由职业者。
- 品牌方团队：品牌部、市场部、内容团队、电商内容团队。

## 3. 先安装到 Codex

如果你已经把这些 skill 文件夹放进了 Codex 全局 skills 目录，可以跳过这一节。

如果还没有安装，把本仓库里的 6 个 skill 文件夹复制到 `~/.codex/skills/`。

如果你的仓库结构是直接显示 6 个 skill 文件夹：

```bash
cp -R account-executive ~/.codex/skills/
cp -R strategy-director ~/.codex/skills/
cp -R creative-director ~/.codex/skills/
cp -R copywriter ~/.codex/skills/
cp -R designer ~/.codex/skills/
cp -R boss ~/.codex/skills/
```

如果你的仓库外层还有一个 `skills/` 文件夹：

```bash
cp -R skills/account-executive ~/.codex/skills/
cp -R skills/strategy-director ~/.codex/skills/
cp -R skills/creative-director ~/.codex/skills/
cp -R skills/copywriter ~/.codex/skills/
cp -R skills/designer ~/.codex/skills/
cp -R skills/boss ~/.codex/skills/
```

如果已经安装过旧版本，可以用下面的方式覆盖更新：

```bash
cp -R account-executive/. ~/.codex/skills/account-executive/
cp -R strategy-director/. ~/.codex/skills/strategy-director/
cp -R creative-director/. ~/.codex/skills/creative-director/
cp -R copywriter/. ~/.codex/skills/copywriter/
cp -R designer/. ~/.codex/skills/designer/
cp -R boss/. ~/.codex/skills/boss/
```

## 4. 最简单的使用方式

如果你不知道该从哪个岗位开始，直接使用 `boss`。

你可以这样发给 Codex：

```text
Use $boss to run this brief through the full agency workflow.

要求：
1. 先让 AE 根据 Brief 模板整理需求。
2. 缺少资料时直接问我，不要自己编。
3. 每个岗位产出后都先给我确认。
4. 我确认后，再进入下一步。

以下是我的项目 Brief：
[把你的项目资料粘贴在这里]
```

这是最推荐的方式。`boss` 会负责调度 AE、策略、创意、文案、设计这些角色，并在关键节点停下来等你确认。

## 5. 完整工作流怎么跑

一个完整项目通常按这个顺序推进：

```text
AE 收集 Brief
-> AE / Strategy Director / Creative Director 三方确认问题和目标
-> 补充行业、竞品、用户、品牌和产品资料
-> Strategy Director 制定策略
-> Creative Director 制定创意方向
-> AE / Strategy Director / Creative Director 三方确认创意方向
-> Copywriter 输出文案
-> Designer 输出视觉方向
-> Creative Director 复核创意一致性
-> BOSS 整理提案或最终交付
```

你不需要一次性把所有内容准备完。资料缺失时，skill 会直接告诉你缺什么，以及缺少这项资料会影响什么。

## 6. 第一次使用可以准备哪些资料

你可以尽量提供这些信息。不是每项都必须有，但越完整，输出越稳定。

```text
品牌名称：
产品或服务：
项目背景：
这次要解决的问题：
商业目标：
传播目标：
目标人群：
核心卖点：
竞争对手：
品牌调性：
必须说的信息：
不能说的信息：
预算或资源限制：
渠道和触点：
需要的交付物：
截止时间：
客户或老板的偏好：
已有资料链接或附件：
```

如果你资料很少，也可以直接说：

```text
我现在只有一个粗略想法，请先用 $account-executive 帮我整理成 Brief，并列出还缺什么资料。
```

## 7. 每个岗位什么时候用

### boss

当你想让 Codex 管完整流程时，用 `boss`。

适合：

- 从 0 到 1 跑一个项目
- 品牌全案或整合营销
- 不知道该先找哪个角色
- 需要每一步确认后再继续
- 需要最后整理提案结构

示例：

```text
Use $boss to manage this campaign from brief intake to strategy, creative direction, copy, design, and final proposal structure. Stop for my confirmation after each stage.
```

### account-executive

当你有一段客户需求、会议记录、老板口头要求，但还没有清楚 Brief 时，用 `account-executive`。

适合：

- 整理客户 Brief
- 提炼项目背景和目标
- 找出缺失资料
- 整理会议纪要和修改意见
- 给策略和创意准备输入

示例：

```text
Use $account-executive to turn this rough client request into an internal brief, missing-material list, and next-step questions.
```

### strategy-director

当 Brief 已经比较清楚，需要定义真正问题、定位、洞察和策略时，用 `strategy-director`。

适合：

- 品牌定位
- 消费者洞察
- 竞品和品类分析
- 策略主张
- Creative Brief
- Campaign strategy

示例：

```text
Use $strategy-director to diagnose the real business problem behind this brief and produce positioning, audience insight, strategic proposition, and a Creative Brief.
```

### creative-director

当策略已经确认，需要创意方向、Big Idea、创意取舍或卖稿逻辑时，用 `creative-director`。

适合：

- 生成创意方向
- 筛选 Big Idea
- 判断哪个方向更值得推进
- 用 52 创意透镜发散
- 用 81 创意矩阵开脑暴
- 把创意包装成客户愿意买单的理由
- 复核文案和视觉是否偏离创意方向

示例：

```text
Use $creative-director to generate 3 creative routes from this confirmed strategy, recommend the strongest Big Idea, and explain why it should win.
```

### copywriter

当策略和创意方向已经确认，需要具体文字输出时，用 `copywriter`。

适合：

- Campaign slogan
- KV headline
- Brand manifesto
- 小红书标题和正文
- 微信推文
- 短视频脚本
- 产品卖点转译
- 活动文案
- 提案文案
- 命名

示例：

```text
Use $copywriter to write campaign lines, KV copy, social hooks, and a brand manifesto based on this confirmed strategy and creative direction.
```

### designer

当策略和创意方向已经确认，需要视觉方向或 AI 生图 prompt 时，用 `designer`。

适合：

- Visual direction
- Key Visual 画面描述
- Moodboard 方向
- 品牌视觉系统建议
- 包装设计方向
- AI 生图 prompt
- 设计复核意见

示例：

```text
Use $designer to translate this confirmed creative direction into visual directions, KV descriptions, moodboard prompts, and AI image prompts.
```

## 8. 如何让输出更稳定

使用时尽量遵守 5 个原则：

1. 先给背景，再让它输出。
2. 不要让后面的岗位跳过前面的确认。
3. 每次只推进一个阶段。
4. 缺资料时先补资料，不要急着要最终稿。
5. 你不满意时，说清楚不满意的是策略、创意、语气、结构、事实还是审美。

不推荐这样问：

```text
帮我做一个品牌营销方案。
```

更推荐这样问：

```text
Use $boss to run this brand launch brief through the full agency workflow. Start with AE brief intake and missing-material questions. Do not move into strategy until I confirm the brief.
```

## 9. 常用提示词模板

### 从一段粗略需求开始

```text
Use $boss to run this project through the full agency workflow.

请先让 AE 整理 Brief，并列出缺失资料。
每一步输出后都等我确认。

项目资料：
[粘贴你的内容]
```

### 只整理 Brief

```text
Use $account-executive to organize this client request into:
1. Project background
2. Business objective
3. Communication objective
4. Target audience
5. Known mandatories
6. Missing materials
7. Questions to ask the client

Client request:
[粘贴内容]
```

### 做策略

```text
Use $strategy-director to develop strategy from this confirmed brief.

请输出：
1. Real business problem
2. Category / competitor observation
3. Audience insight
4. Brand positioning
5. Strategic proposition
6. Creative Brief
7. Missing assumptions and risks

Confirmed brief:
[粘贴内容]
```

### 做创意方向

```text
Use $creative-director to create 3 creative routes from this confirmed strategy.

每个方向请包含：
1. Route name
2. Big Idea
3. Creative mechanism
4. Key visual / key message direction
5. Channel extension
6. Why it should or should not move forward

Confirmed strategy:
[粘贴内容]
```

### 写文案

```text
Use $copywriter to write copy based on this confirmed creative direction.

请输出：
1. Campaign slogan options
2. KV headline options
3. Brand manifesto
4. Xiaohongshu titles
5. Social post copy
6. Recommendation and rationale

Confirmed creative direction:
[粘贴内容]
```

### 做视觉方向和 AI 生图 prompt

```text
Use $designer to turn this confirmed creative direction into visual outputs.

请输出：
1. Visual direction
2. Key Visual description
3. Moodboard keywords
4. Packaging / layout direction
5. AI image prompts for Midjourney, Gemini, and GPT-Image
6. Execution notes and risks

Confirmed creative direction:
[粘贴内容]
```

### 整理提案结构

```text
Use $boss to turn the confirmed strategy, creative direction, copy, and visual direction into a proposal deck structure.

请不要刻意限制页数。
以逻辑完整、客户能理解和能做决策为优先。

Confirmed materials:
[粘贴内容]
```

## 10. 如果 Codex 问你确认，应该怎么回复

你可以直接回复：

```text
确认，进入下一步。
```

也可以带修改意见：

```text
方向基本确认，但目标人群需要改成一二线城市 28-35 岁女性。请基于这个修改后进入策略。
```

如果你不确定，可以让它解释：

```text
先不要进入下一步。请解释这一步的判断依据，以及还有哪些风险。
```

## 11. 如果缺资料怎么办

如果 skill 提示缺资料，不要担心。这是正常流程。

你可以选择：

```text
我暂时没有这些资料，请基于合理假设继续，但把所有假设标注出来。
```

或者：

```text
我先补充资料，暂时不要进入下一步。
```

如果是正式项目，更推荐补充资料后再继续。

## 12. 常见问题

### 我完全不懂广告流程，可以用吗

可以。建议从 `boss` 开始，让它带你一步步走。你只需要不断确认、补资料、提出修改意见。

### 我只想写几句文案，可以直接用 copywriter 吗

可以，但最好提供已确认的策略和创意方向。如果没有这些内容，`copywriter` 可能会先提示你补充背景，或明确它只能做试写草案。

### 为什么它总是让我确认

因为真实广告工作需要确认节点。确认机制是为了避免 AI 自动脑补、跳步、把前面的错误放大到后面。

### 为什么它总问我要资料

因为这套 skills 被设计成不默认编造信息。缺资料时直接问，是为了保护真实项目的准确性。

### 能不能一次性让它生成完整方案

可以，但不推荐。更稳的方式是分阶段推进：Brief -> Strategy -> Creative Direction -> Copy / Design -> Proposal。

### 这套 skills 会替代广告人吗

不会。它更像一个协作框架，用来帮助广告人和品牌部复用流程、方法论和判断标准。

## 13. 推荐的第一次测试方式

如果你第一次使用，可以拿一个真实或虚拟项目这样测试：

```text
Use $boss to run this brief through the full agency workflow.

要求：
1. 从 AE Brief Intake 开始。
2. 缺少资料就问我。
3. 每一步都先给我确认。
4. 不要跳到最终方案。

Brief:
品牌：
产品：
目标：
人群：
渠道：
需要交付：
限制：
```

第一次不要急着要最终稿。先观察它怎么问问题、怎么定义目标、怎么把策略和创意一步步拆出来。你会更容易理解这套 skills 的价值。

## 14. 一句话记住

如果你不知道怎么用，就从这句话开始：

```text
Use $boss to run this brief through the full agency workflow, stopping for my confirmation after each stage and asking me directly for missing materials.
```

Agency Workflow Skills 的核心不是生成更多内容，而是让 Codex 按真实广告公司的流程、角色和判断方式协作。
