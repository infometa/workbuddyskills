---
name: yj-fin-research
description: 通过自有 MCP 工具集拉取 AI 生成的投研文本（Markdown）：公司一页通、投资逻辑、同业对比、业绩点评、观点辩证、主题跟踪、调研提纲、个股一句话总结、热点话题、投研线索。返回可直接引用的结论性文本，适合纪要、速览、事实与观点补充。注意这些文本定期更新、时效性不足，必须与 yj-fin-data 的结构化数据交叉验证后再引用；不要只靠本技能下结论。
version: 1.0.0
metadata:
  category: research-text
  domain: finance
  tools_prefix: 
---

# 投研文本

## 前置：连接与授权

本技能用到的全部工具都是受保护资源，**调用必须携带用户授权令牌**。用户首次使用时会被自动引导完成一次云极账号授权（登录 + 同意授权），此后令牌自动续期，不再打扰。

技能侧**不需要也绝不应该**要求用户提供 URL、API Key、Token 或环境变量——这些都是不存在的配置项，让用户去找会让对话卡死。

| 被拒情形 | 处置 |
|---|---|
| `UNAUTHORIZED` | 提示"需在连接器里重新完成云极账号授权"，**停止后续调用** |
| `SCOPE_MISSING` | 提示"请重新完成云极账号授权"，**停止后续调用** |
| `QUOTA_EXCEEDED` | **立刻停止全部调用**，用已取到的数据出部分结果并写明缺口 |
| `UPSTREAM_UNAVAILABLE` / `UPSTREAM_TIMEOUT` | 工具返回**错误**（`ok=false`，不返回降级数据）；退避重试一次，仍失败则该项视为缺失、在报告注明缺口；AI 生成类**不得重发**（不可重放，会重复计费） |

配额按**云极账号**累计且跨会话有效，不要建议用户"换个会话再试"。完整说明见技能包 README 第 3 节。

---

## 概览

返回的是 **AI 生成的 Markdown 投研文本**，不是结构化数值。

| 想要 | 用 |
|---|---|
| 一段能直接引用的结论/叙事 | 本技能 |
| 精确数值、时间序列 | `yj-fin-data` |
| 文档原文怎么论述 | `yj-fin-knowledge` |

**最重要的一条纪律**：本技能的文本是**定期更新**的，时点不可控、可能滞后于最新财报或行情。

> **引用前必须用结构化数据交叉验证。** 典型做法：先 `yj-fin-data` 拉出关键数字（营收、净利、估值），再引用本技能的文本做叙事与逻辑补充。文本里出现的数字与结构化数据冲突时，**以结构化数据为准**并在报告里标注差异。

---

## 通用规则

1. **证券先解析**：需要 `security_code` 的工具，先 `securities_search` 拿带后缀代码，一次任务只解析一次。
2. **主题先解析**：`agent_theme_tracking` 的 `theme_id` **只收数字题材 ID**，必须先 `concept_search` 解析（传中文主题名不会报错，只会静默返回空）。
3. **AI 工具不重试生成**：超时/失败**不要重发生成请求**（中止的请求照样计费）。两步类（F8/F9）用 `data_id` 走取内容路径重试。
4. **贵工具最后调**：先铺便宜的结构化事实底座，再决定这篇文本是否值得生成。
5. **不自曝**：成品内不出现工具名，只写"研究观点认为""市场关注点在于"这类自然表述，或直接陈述内容。

---

## 工具一览

| 工具 | 用途 | 形态 |
|---|---|---|
| `stock_highlights` | 个股一句话总结（批量） | 单步 |
| `hot_topic_briefing_list` | 热点话题报告（早/午/盘中/晚） | 单步 · 分页 · **按条计费** |
| `investment_clues` | 投研线索（研报/电话会/公告/观点） | 单步 · 分页 · **按条计费** |
| `agent_one_pager` | 公司一页通 | 单步 · 贵 |
| `agent_investment_logic` | 投资逻辑 | 单步 · 贵 |
| `agent_peer_comparison` | 同业对比 | 单步 · 贵 |
| `agent_research_outline` | 调研提纲 | 单步 · 贵 |
| `agent_earnings_review` | 业绩点评 | **两步**（先取内容 ID，再用它取回内容） |
| `agent_viewpoint_debate` | 观点辩证 PK | **两步** |
| `agent_theme_tracking` | 主题跟踪（晨报/晚报） | 单步 |

---

## 1. 个股一句话总结 · `stock_highlights`

```json
{ "security_list": ["600183.SH", "00700.HK"] }
```

批量、便宜、快。**扫一批票时的第一选择**。仅 A 股/港股个股。

> 🔴 单次上限 6000 条。⚠️ **无看点的证券不会出现在返回列表里**——返回行数少于提交数是正常的，不是丢数据，不要据此重试。

---

## 2. 热点话题 · `hot_topic_briefing_list`

```json
{ "from": 0, "size": 20, "with_related_securities": true, "with_close_reading": true,
  "start_date": "2026-03-22", "end_date": "2026-03-27",
  "category_list": ["morning_briefing","noon_briefing","afternoon_flash"] }
```

| 入参 | 说明 |
|---|---|
| `from` / `size` | 分页，`size` 上限 **20** |
| `category_list` | `morning_briefing` / `noon_briefing` / `afternoon_flash` / `evening_briefing` |
| `with_related_securities` | 是否带相关证券（表格） |
| `with_close_reading` | 是否带精读 |

🔴 **按条计费 + no-replay**。先小 `size` 试一次确认内容形态，再决定要不要继续翻页。

---

## 3. 投研线索 · `investment_clues`

按证券或行业，提取研报、电话会议、公告、观点。

```json
{ "from": 0, "size": 100, "query_mode": "by_security",
  "code_list": ["600519.SH","002594.SZ"],
  "start_time": "2026-01-01 00:00:00", "end_time": "2026-03-23 23:59:59",
  "source_list": ["research_report","conference","announcement","view"] }
```

| 入参 | 说明 |
|---|---|
| `query_mode` | **闭集**：`by_security` / `by_industry` |
| `code_list` | 证券或行业代码；行业用 `888888.CI` / `999999.CI` 这类 |
| `start_time` / `end_time` | **注意是 start/end_time 不是 start_date/end_date**；均不传时默认近 7 日 |
| `source_list` | `research_report` / `conference` / `announcement` / `view` |
| `size` | 上限 **500** |

🔴 **按条计费 + no-replay**。`size` 直接决定账单，**不要无脑设 500**。

---

## 4. 单步 AI Agent（F4–F7）

| 工具 | 入参 |
|---|---|
| `agent_one_pager` | `{security_code}` |
| `agent_investment_logic` | `{security_code}` |
| `agent_peer_comparison` | `{security_code}` |
| `agent_research_outline` | `{security_code}` |

共同点：**同步生成、超时下限 120s、`no-replay`**。

- 调用后**耐心等**，不要在超时边缘放弃——中止的请求照样计费，钱花了拿不到结果。
- 失败只重试**一次**；第二次失败直接降级为"该文本不可用"，改用结构化数据 + 知识库补。
- `agent_peer_comparison` 的返回里通常**已含可比公司的基本面与估值数据**（营收、净利、ROE、增速、PE/PB/PS/市值），优先直接采用（详见 `yj-fin-comparable`）。

---

## 5. 业绩点评 · `agent_earnings_review`（两步）

```json
// ① 提交
{ "security_code": "300750.SZ", "period": "2025q3" }
// → { data_id, status }

// ② 取内容（可重复，不重新计费生成）
{ "data_id": "<上一步的 data_id>" }
```

这是**两步式**调用：先提交任务拿到内容 ID，再用该 ID 取回内容。

`period` 形如 `2025q3`（小写 q）。

🔴 **等待到期后必须停止轮询**，`data_id` 在下一次调用中**仍然有效**。异步等待上限建议 **55s**（低于 MCP 客户端 ~60s 默认超时），否则连接先断、`data_id` 丢失——已经付费的生成任务就白瞎了。

轮询间隔建议 5s。若返回 `status:"timeout"`，**换个回合再调用一次取内容**，不要重新提交。

---

## 6. 观点辩证 · `agent_viewpoint_debate`（两步）

```json
// ①
{ "viewpoint": "飞天茅台的批价低点是1500元" }   // ≤1000 字，必填
// ②
{ "data_id": "<data_id>" }
```

对一个观点做正反辨析与论据组织。同样是 `data_id` 可复用、轮询上限 55s。

---

## 7. 主题跟踪 · `agent_theme_tracking`

```json
{ "theme_id": "23600839952306231", "date": "2026-04-01", "info_type": ["morning","night"] }
```

- 🔴 `theme_id` **只接受数字题材 ID**（如 `23600839952306231`）。传中文主题名不会报错、只会静默返回空——必须先 `concept_search` 解析出 ID 再调用。
- `info_type`：`morning` / `night`，**必填**可多选。
- `date`：`yyyy-MM-dd`。

晨报/晚报式的产业链与主题脉络，适合做"最近这个主题发生了什么"的时间线。

---

## 8. 典型编排

**个股速览（最常用）**

```text
stock_highlights([codes])            # 便宜，先扫
  → agent_one_pager(code)         # 一页通：核心要素与结论
  → quote_realtime / quote_daily   # 用结构化数据校准文本里的数字
  → （可选）knowledge_search       # 找原文旁证
```

**行业主题扫描**

```text
concept_search("机器人")          # 主题名 → concept_id
  → concept_info / concept_securities   # 题材画像 + 成分股
  → agent_theme_tracking(id, date, [morning,night])
  → investment_clues(by_industry, ...)         # 注意按条计费，size 别给满
  → hot_topic_briefing_list(...)                          # 同上
```

**财报季**

```text
securities_search(code)
  → financial_income(code, period=[最近报告期])   # 先把实际数字拿到手
  → agent_earnings_review(code, period)           # 再取点评文本
  → 比对文本里的数字与报表数字                        # 冲突以报表为准
```

---

## 9. 排障速查

| 现象 | 处置 |
|---|---|
| 超时 | 不重发生成；两步类用 `data_id` 重新取内容 |
| 返回空/无内容 | AI 类能力可能确实无覆盖；降级用结构化数据，不要重试第三次 |
| 分页结果看着完整但怀疑截断 | `total` 可能是 ES 封顶值；用 `from=total,size=1` 探针验证 |
| 文本里的数字和财报对不上 | **以财报为准**，在报告里标注；AI 文本有时点滞后 |
| `meta.degraded=true` | 报告里写明缺什么 |
