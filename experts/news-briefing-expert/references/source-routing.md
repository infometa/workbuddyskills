# 数据源路由方法论（source-routing）

> 解决"这个新闻需求用什么关键词、什么参数去检索"的问题。**取数统一走 online-search（ProSearch）**，按领域调整关键词与垂类参数。源的可用性与降级链见 `references/data-sources.md`。

## 一、领域 → 检索策略决策表

所有领域都用 online-search，区别在 keyword + `--freshness` + `--industry`：

| 用户需求领域 | keyword 示例 | 参数 |
|------------|-------------|------|
| AI / 大模型 / LLM | `最新AI新闻` / `OpenAI 最新` | `--freshness=7d` |
| 财经 / 股市 / 宏观 | `今日财经要闻` / `A股 今日` | `--freshness=24h --industry=news` |
| 科技（非 AI）/ 数码 | `科技最新动态` | `--freshness=7d --industry=news` |
| 社会 / 时政 / 民生 | `今日社会新闻` | `--freshness=24h --industry=news` |
| 国际 / 地缘 | `国际新闻 今日` | `--freshness=24h --industry=news` |
| 政策 / 官方 | `XX政策 最新` | `--industry=gov` |
| 数据 / 行情（天气/金价） | `今日黄金价格` | `--mode=2`（VR 卡） |
| 综合 / 多领域简报 | 逐领域分别检索 | 各配上面对应参数 |
| 主题追踪 | `<主题> 最新进展` | `--freshness=7d` 或 `30d` |

## 二、关键词构造（决定检索质量）

把用户的口语问题转成精准 keyword：

| 用户说 | keyword |
|--------|---------|
| "最近的 AI 新闻" | `最新AI新闻` |
| "现在黄金多少钱" | `今日黄金价格`（+ `--mode=2`） |
| "OpenAI 最近干啥了" | `OpenAI 最新动态` |
| "深圳今天天气" | `深圳今天天气`（+ `--mode=2`） |

要点：
- 简洁 2-6 词，去掉"帮我/请问/一下"等填充词
- 有时效就加时间词（"今日""最新""2026"）并配 `--freshness`
- **保留原语言不翻译**（中文 query 用中文，英文 query 用英文）

## 三、时效参数（--freshness，强时效必加）

| 用户意图信号 | --freshness |
|------|------|
| "今天""刚刚""现在" | `24h` |
| "最近""最新""这两天" | `7d` |
| "这周" | `7d` |
| "这个月" | `30d` |
| "今年""2026" | `1y` |
| 无时效（通用事实） | 不加 |

> `--freshness` 与 `--cnt` 互斥，不能同时用。

## 四、综合简报取数顺序（D 线）

```
逐领域用 online-search 分别检索（一个领域一次）：
1. AI 版块     → keyword=最新AI新闻 --freshness=7d
2. 财经版块    → keyword=今日财经要闻 --freshness=24h --industry=news
3. 科技版块    → keyword=科技最新动态 --freshness=7d --industry=news
4. 国际/社会   → keyword=国际新闻今日 --freshness=24h --industry=news
5. 各版块分别多源校验后，再全局编排（见 briefing-format.md）
```

> 每次检索**先原样输出 message 结果条目**，再纳入简报组织（防幻觉）。

## 五、取数失败的降级（详见 data-sources.md）

| 情况 | 降级 |
|------|------|
| online-search 返回"未登录" | 提示用户登录后重试 |
| online-search 不可用 | 试 WebSearch（若配 key）；AI 领域可再试 aihot（若可达） |
| 全部源不通 | 如实告知"当前环境无可用联网源，请检查 online-search 登录态 / WebSearch key" |
| 结果稀少 | 换关键词/措辞重搜（最多 1 次）；放宽时间窗；告知该话题公开信息有限 |
| 关键事实只有单一来源 | 标注"待核实"，不当既定事实（见 cross-verification.md） |

> **绝不在无可用源时用训练记忆编造新闻**——没有就说没有。
