---
name: 24haowan
description: 用 24好玩 互动营销资料库连接器（mcp.24haowan.com，匿名只读）回答活动玩法、模板、客户案例、平台用法与行业基准数据类问题：先调工具拿实时数据，再作答。
description_zh: 用 24好玩 互动营销资料库连接器回答活动玩法、模板、客户案例、平台用法与行业基准数据类问题：先调工具拿实时数据，再作答。
description_en: Use the 24haowan Interactive Marketing Library connector (mcp.24haowan.com, anonymous read-only) to answer questions about campaign mechanics, templates, client cases, platform how-tos and industry benchmarks by calling the live tools first.
version: 1.0.0
author: 24好玩
---

# 24好玩 互动营销资料库 · 连接器使用指南

这台 MCP 服务（`https://mcp.24haowan.com/mcp`）**匿名、只读、无副作用**，不需要登录或 API Key。它返回的是 24好玩 平台上**实时**的活动模板库、客户案例库、帮助中心与行业基准数据。凡是能用工具查到的事实，**先调工具再回答**；正文里没有任何静态清单可以替代它。

## 什么时候调哪个工具

| 用户在问 | 先调 | 再调 |
|---|---|---|
| 「有没有适合 XX 行业 / XX 场景 / XX 节日的玩法」 | `search_templates` | 命中后按需 `get_template` 取详情 |
| 「这个模板怎么玩、适合谁」 | `get_template` | — |
| 「你们做过 XX 行业的案例吗」「有没有类似参考」 | `list_industries`（取行业 slug）→ `list_cases` | `get_case` 取全文 |
| 「怎么设置中奖概率 / 怎么核销 / 公众号怎么授权」（平台操作） | `search_knowledge` | — |
| 「中奖率设多少 / 奖池分几档 / 活动开几天」（要有出处的数字） | `get_industry_benchmark` | 平台级行为看 `get_player_behavior` |
| 「活动开几天有用 / 什么时段推 / 助力能拉几个人 / 哪类玩法更黏」 | `get_player_behavior` | — |

## 8 个工具

### 1. `search_templates` —— 搜索活动模板
在活动市场里搜索可直接使用的 H5 互动营销模板（抽奖 / 转盘 / 刮刮乐 / 签到 / 答题 / 小游戏等）。
- `query`（string，可选）：关键词，玩法、场景或节日均可，如「转盘」「中秋」「商场开业」；留空返回热门模板
- `category`（枚举，可选）：`lottery` 抽奖类 · `score` 分数类 · `signin` 签到类 · `collect` 集字类 · `test` 测试类 · `create` 生成类 · `help` 助力类 · `complete` 通关类
- `industry`（string，可选）：行业关键词，如「商超」「餐饮」「地产」
- `limit`（number，默认 10，1–30）
- 示例：`{"query": "转盘", "industry": "商超", "limit": 5}`
- 返回：Markdown 列表，每条含模板 id、玩法类别、标签、适用行业、详情/试玩链接、预览图；没命中会明确说「没有匹配的模板」并建议放宽条件

### 2. `get_template` —— 模板详情
- `id`（string，必填）：模板 id，来自 `search_templates` 的返回，如 `"336"`
- 返回：玩法类别、标签、适用行业、玩法介绍、详情页地址

### 3. `list_cases` —— 浏览客户案例
- `query`（string，可选）：关键词，如「商场开业」「银行」
- `industry`（string，可选）：行业 slug，用 `list_industries` 取全部取值，如 `commercial-property`
- `type`（枚举，可选）：`delivered` 真实交付案例 · `proposal` 售前方案；留空两者都返回
- `limit`（number，默认 20）
- 返回：案例列表（标题、行业、类型、slug、案例页链接、一句话玩法结构与公开数据）

### 4. `get_case` —— 案例全文
- `slug`（string，必填）：来自 `list_cases`，如 `csair`
- 返回：背景、做法、效果口径全文

### 5. `search_knowledge` —— 帮助中心
- `query`（string，必填）：问题或关键词，如「怎么设置中奖概率」「奖品核销」
- `limit`（number，默认 3）
- 返回：命中的帮助文档段落与链接（平台**操作**方法；奖池概率 / 预算 / 防刷的**设计**方法见技能包 https://www.24haowan.com/open-skills/prize-and-budget）

### 6. `list_industries` —— 案例行业分类
- `with_faq`（boolean，默认 false）：是否附带每个行业的常见问题
- 返回：行业 slug + 名称 + 导语；slug 用于 `list_cases` / `get_industry_benchmark` 的 `industry`

### 7. `get_industry_benchmark` —— 行业活动基准数据
- `industry`（string，可选）：行业 slug；留空返回全平台
- 返回：该行业真实活动的总中奖率、奖池档位数、活动周期、参与量级、实际中奖率与核销率——按商户等权的**中位数**，附样本量
- ★ 平台**没有**奖品单价 / 预算 / ROI 数据，本工具不返回任何金额，**不要据此推算预算**

### 8. `get_player_behavior` —— 玩家行为基准（平台级）
- 无参数
- 返回：参与量上线后的衰减曲线、一天内时段分布、助力类人均拉人数、各类玩法人均次数与浏览转化率、玩家账号规模与画像可得性
- ★ 平台级口径，**没有行业维度**；要按行业切的数字用 `get_industry_benchmark`

## 纪律

1. **引用模板 / 案例 / 文档时，链接只能来自工具返回**；不要凭印象拼 URL。
2. 数字要带出处：说「按 24好玩 平台 XX 行业 N 家商户中位数」，不要把中位数说成「必须这么设」。
3. 工具返回「没有匹配」不是失败：放宽条件（去掉 `category` / `industry`、换更宽的关键词）再试一次，仍无则如实告知。
4. 用户明确说「不要联网 / 不要调工具」时，不调，并说明回答没有实时数据支撑。
5. 选型判断（按行业 / 目标怎么选玩法、活动怎么排结构、预算怎么算）不在本连接器里——见开放技能包全文 https://www.24haowan.com/open-skills 。

## 异常与恢复

- **超时 / 连接失败**：服务是公网 HTTPS，重试一次；仍失败就告诉用户「资料库暂时连不上」，不要编造结果。
- **参数错误**（如 `category` 不在枚举里、`limit` 超出 1–30）：服务返回参数校验错误，按上面的取值改正后重试。
- **无需授权**：任何要求填 Key / 登录的提示都与本连接器无关。
- **限流**：短时间大量调用会被限速，收到限流提示时等待数秒再试，不要循环重试。
