# 数据源与降级链（data-sources）

> **核心原则：探测可用源 + 降级链，绝不硬绑单一数据源。** 不同运行环境下各源可用性不同（某些源可能需要登录态、API Key 或地区可达）。专家取数时按优先级探测，**谁通用谁**，全不通则如实告知。

## 一、数据源优先级（降级链）

| 优先级 | 数据源 | 形态 | 适用 | 备注 |
|--------|--------|------|------|------|
| **1·首选** | **online-search（ProSearch）** | 内置 skill | **全领域**（含 AI/财经/科技/社会/国际） | 腾讯元宝联网搜索，免 key、鉴权走本地网关登录态。覆盖中文高权威信源（官媒/政府/腾讯生态） |
| 2·备选 | WebSearch | 平台内置工具 | 全领域 | **需配置 API Key 才可用**；未配则自动跳过 |
| 3·AI 加分项 | aihot（aihot.virxact.com） | 联网调用 | 仅 AI 领域 | **可能已加登录墙**（部分环境返回 302→登录页）；通则用、不通则跳过，不依赖 |
| — | WebFetch | 平台内置工具 | 进原文核实 | 配合任一搜索源做交叉验证 |

> **取数主力是 online-search**。它一个就能覆盖全领域新闻取数，是这个专家"实际能跑通"的基石。

## 二、取数探测逻辑（每次取数遵循）

```
取数时按顺序尝试，第一个成功的即用：
  1. 调 online-search（prosearch.cjs）
     → success:true 且有结果 → 用它 ✅
     → message 含"未登录" → 提示用户登录后重试
  2. online-search 不可用时 → 试 WebSearch（若环境配了 key）
  3. 仅 AI 领域、且前两者都不理想时 → 试 aihot（通则用，302/失败则跳过）
  4. 全部不通 → 如实告知用户："当前环境暂无可用的联网搜索源，
     请检查 online-search 登录态 / WebSearch API Key 配置后重试。"
```

> 不要在一个源失败时假装有数据或用训练记忆编造。**没有可用源 = 诚实说没有，而不是脑补。**

## 三、online-search（ProSearch）调用速查

完整规范见 `skills/online-search/SKILL.md`。高频用法：

```bash
node 'skills/online-search/scripts/prosearch.cjs' --keyword=关键词
node 'skills/online-search/scripts/prosearch.cjs' --keyword=最新AI新闻 --freshness=7d
node 'skills/online-search/scripts/prosearch.cjs' --keyword=国内新闻 --freshness=24h --industry=news
node 'skills/online-search/scripts/prosearch.cjs' --keyword="React 19" --site=github.com
```

**关键规则**（来自 skill）：
- 时效查询必加 `--freshness`（24h/7d/30d/1y）；`--freshness` 与 `--cnt` 互斥。
- 垂类 `--industry=gov|news|acad`；VR 卡（天气/金价）`--mode=2`。
- 返回 JSON 的 **`message` 字段必须先原样输出**（已预渲染成带可点击超链接的结果条目，是防幻觉核心），再补分析。
- 关键词简洁（2-6 词），保留原语言不翻译。

## 四、按领域用 online-search 取数

新闻专家用统一的 online-search 覆盖各版块，靠 keyword + 参数区分：

| 版块 | keyword 示例 | 参数 |
|------|-------------|------|
| AI | `最新AI新闻` / `OpenAI 最新` | `--freshness=7d` |
| 财经 | `今日财经要闻` / `A股 今日` | `--freshness=24h --industry=news` |
| 科技 | `科技最新动态` | `--freshness=7d --industry=news` |
| 国际 | `国际新闻 今日` | `--freshness=24h --industry=news` |
| 社会 | `今日社会新闻` | `--freshness=24h --industry=news` |
| 主题追踪 | `<主题> 最新进展` | `--freshness=7d/30d` |
| 数据/行情 | `今日黄金价格` | `--mode=2`（VR 卡） |

## 五、aihot（可选 AI 加分项，不依赖）

- 仅在 online-search 之外想要"AI 领域人工精选策展"时尝试。
- **可能已加登录墙**：带浏览器 UA 调 `aihot.virxact.com/api/public/items`，若返回 302→登录页 或非 JSON，则判定不可用，**直接跳过、改用 online-search**，不报错给用户、不纠缠。
- 务实：aihot 是锦上添花，不是必需品。它的可用性会变，专家不绑它。

## 六、务实定位

新闻专家的取数能力 = **online-search 主力 + 探测降级**。无论运行环境里 WebSearch 有没有 key、aihot 有没有登录墙，只要 online-search 可用，专家就能跑通全领域新闻。这正是"纯方法论型、数据源可替换"定位的落地——**源会变，方法论（选源/校验/排版/溯源）不变。**
