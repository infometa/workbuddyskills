# 分析报告 Schema 规范

本文档定义了分析结果（AnalysisResult）的完整数据结构和枚举取值，确保输出的一致性和可解析性。

---

## 一、核心字段定义

### 基本信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 股票代码 |
| `name` | string | 股票名称 |
| `current_price` | float | 分析时的股价 |
| `change_pct` | float | 分析时的涨跌幅(%) |

### 核心决策指标

| 字段 | 类型 | 取值范围 | 说明 |
|------|------|---------|------|
| `sentiment_score` | int | 0-100 | 综合评分 |
| `trend_prediction` | enum | 见下方 | 趋势预测 |
| `operation_advice` | enum | 见下方 | 操作建议 |
| `decision_type` | enum | buy/hold/sell | 三值决策类型 |
| `action` | enum | 见下方 | 细粒度建议动作 |
| `confidence_level` | enum | 高/中/低 | 置信度 |
| `report_language` | enum | zh/en/ko | 报告输出语言 |

---

## 二、枚举定义

### trend_prediction — 趋势预测

| 中文值 | 英文值 | 对应分数区间 |
|--------|--------|------------|
| 强烈看多 | Strongly Bullish | 80-100 |
| 看多 | Bullish | 60-79 |
| 震荡 | Sideways | 40-59 |
| 看空 | Bearish | 20-39 |
| 强烈看空 | Strongly Bearish | 0-19 |

### operation_advice — 操作建议

| 值 | 说明 |
|----|------|
| 买入 | 明确买入信号 |
| 加仓 | 已持有，可加仓 |
| 持有 | 继续持有不动 |
| 观望 | 不持有时等待机会 |
| 减仓 | 部分卖出 |
| 卖出 | 全部卖出 |

### action — 细粒度建议动作（Taxonomy）

| 值 | 中文标签 | 说明 |
|----|---------|------|
| buy | 买入 | 新建仓位 |
| add | 加仓 | 追加现有仓位 |
| hold | 持有 | 维持不动 |
| reduce | 减仓 | 降低仓位 |
| sell | 卖出 | 清仓 |
| watch | 观望 | 等待确认信号 |
| avoid | 回避 | 远离此标的 |
| alert | 警示 | 需持续关注风险 |

### confidence_level — 置信度

| 值 | 星级 | 适用场景 |
|----|------|---------|
| 高 | ⭐⭐⭐ | 数据完整，多策略共振 |
| 中 | ⭐⭐ | 数据基本完整，信号有一定确认 |
| 低 | ⭐ | 数据不完整、陈旧或信号矛盾 |

**置信度约束规则**：
- 当数据存在 stale（过时）、fallback（降级）、missing（缺失）、fetch_failed（获取失败）、partial（不完整）或 estimated（估算）标记时，置信度**不得为"高"**

---

## 三、Decision Dashboard 结构

`dashboard` 是核心输出对象，包含以下子模块：

### 3.1 core_conclusion — 核心结论

| 字段 | 类型 | 说明 |
|------|------|------|
| `one_sentence` | string | 一句话核心判断 |
| `signal_type` | enum | 信号类型（见下方） |
| `time_sensitivity` | enum | 时效性（见下方） |
| `position_advice` | string | 仓位建议描述 |

**signal_type 枚举**:
- 🟢买入信号
- 🟡持有观望
- 🔴卖出信号
- ⚠️风险警告

**time_sensitivity 枚举**:
- 立即行动
- 今日内
- 本周内
- 不急

### 3.2 data_perspective — 数据透视

| 字段 | 类型 | 说明 |
|------|------|------|
| `trend_status` | string | 趋势状态描述 |
| `price_position` | string | 相对关键均线的位置 |
| `volume_analysis` | string | 量能分析 |
| `chip_structure` | string | 筹码结构 |

### 3.3 intelligence — 情报面

| 字段 | 类型 | 说明 |
|------|------|------|
| `latest_news` | string | 最新关键新闻摘要 |
| `risk_alerts` | List[string] | 风险警报列表 |
| `positive_catalysts` | List[string] | 积极催化因素列表 |
| `earnings_outlook` | string | 业绩预期 |
| `sentiment_summary` | string | 舆情情绪总结 |

### 3.4 battle_plan — 作战计划

| 字段 | 类型 | 说明 |
|------|------|------|
| `sniper_points` | object | 狙击点位（见下方子结构） |
| `position_strategy` | string | 仓位策略描述 |
| `action_checklist` | List[string] | 操作检查清单 |

**sniper_points 子结构**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `ideal_buy` | float/string | 理想买入价位 |
| `secondary_buy` | float/string | 次优买入价位 |
| `stop_loss` | float/string | 止损价位 |
| `take_profit` | float/string | 止盈目标价 |

### 3.5 signal_attribution — 信号归因（重要）

| 字段 | 类型 | 取值范围 | 说明 |
|------|------|---------|------|
| `technical_indicators` | int | 0-100 | 技术指标对最终结论的贡献度 |
| `news_sentiment` | int | 0-100 | 新闻情绪对结论的贡献度 |
| `fundamentals` | int | 0-100 | 基本面对结论的贡献度 |
| `market_conditions` | int | 0-100 | 市场环境对结论的贡献度 |
| `strongest_bullish_signal` | string | - | 最强看多信号来源描述 |
| `strongest_bearish_signal` | string | - | 最强看空信号来源描述 |

> 四项贡献度之和应接近 100（允许小幅偏差）

### 3.6 phase_decision — 市场阶段决策（可选）

| 字段 | 类型 | 说明 |
|------|------|------|
| `phase_context.phase` | enum | 市场阶段（见下方） |
| `action_window` | string | 建议操作时间窗口 |
| `immediate_action` | string | 即时操作建议 |
| `watch_conditions` | string | 观察条件 |
| `next_check_time` | string | 下次检查时间 |
| `confidence_reason` | string | 置信度解释 |
| `data_limitations` | string | 数据局限说明 |

**phase 枚举**:
- premarket（盘前）
- intraday（盘中）
- lunch_break（午间休市）
- closing_auction（临近收盘）
- postmarket（盘后）
- non_trading（非交易日）
- unknown（未知）

---

## 四、详细分析字段

| 字段 | 说明 |
|------|------|
| `trend_analysis` | 走势形态分析 |
| `short_term_outlook` | 短期展望（1-3日） |
| `medium_term_outlook` | 中期展望（1-2周） |
| `technical_analysis` | 技术指标综合分析 |
| `ma_analysis` | 均线分析 |
| `volume_analysis` | 量能分析 |
| `pattern_analysis` | K线形态分析 |
| `fundamental_analysis` | 基本面综合分析 |
| `sector_position` | 板块地位和行业趋势 |
| `company_highlights` | 公司亮点/风险点 |
| `news_summary` | 近期重要新闻/公告摘要 |
| `market_sentiment` | 市场情绪分析 |
| `hot_topics` | 相关热点话题 |
| `analysis_summary` | 综合分析摘要 |
| `key_points` | 核心看点（3-5个要点） |
| `risk_warning` | 风险提示 |
| `buy_reason` | 买入/卖出理由 |
| `data_sources` | 数据来源说明 |

---

## 五、元数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `market_snapshot` | object | 当日行情快照 |
| `search_performed` | bool | 是否执行了联网搜索 |
| `data_sources` | string | 数据来源说明 |
| `model_used` | string | 使用的 LLM 模型名 |
| `query_id` | string | 本次分析唯一标识 |
| `success` | bool | 分析是否成功 |
| `error_message` | string | 错误信息（失败时） |

---

## 六、一致性校验规则

1. **sentiment_score 与 trend_prediction 一致**：不可出现 80 分但趋势"看空"
2. **sentiment_score 与 operation_advice 一致**：参见评分→建议收敛规则
3. **action 与 decision_type 一致**：buy/add → decision_type=buy；hold/watch → hold；reduce/sell/avoid → sell
4. **信号归因贡献度之和 ≈ 100**
5. **置信度受数据质量约束**：数据不完整时不可为"高"
