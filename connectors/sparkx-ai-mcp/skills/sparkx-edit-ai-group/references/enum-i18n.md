# Enum i18n - managed groups (中文 <-> English <-> code)

Use this table **both directions**:
- **Parsing user input** (中文 -> code): when the user describes what they want in
  Chinese, map their words to the API field + coded value before building the call.
- **Reporting back** (code -> 中文): when you echo a group's config to the user,
  translate codes/English back to the Chinese labels they'd see in the platform UI.

Authoritative Chinese labels follow the platform UI and the MCP Tool specification.
Synonyms列 lists casual/口语 phrasings so real user requests still match.

## campaignType - 广告类型

| code | 中文(UI) | English | 常见说法 |
|---|---|---|---|
| `sponsoredProducts` | 商品推广 | Sponsored Products | SP、商品广告 |
| `sponsoredBrands` | 品牌推广 | Sponsored Brands | SB、品牌广告 |
| `sponsoredDisplay` | 展示型推广 | Sponsored Display | SD、展示广告 |

## targetType (SP/SB) - 托管目标 / 基础设置

Two UI groups (扩大销量 / 控制成本) are **headings only** - the value sent is one of
the three goals below. `4` is a legacy value not shown in the UI; don't offer it.

| code | 中文(UI 选项) | English | 所属大类 | 常见说法 |
|---|---|---|---|---|
| `1` | 推动增长 | Drive growth | 扩大销量 / Increase sales | 增长型、还能涨、拉增长 |
| `2` | 保持订单稳定 | Optimize ROAS | 控制成本 / Drive efficiency | 稳定型、保利润、提 ROAS、降 ACOS、控成本 |
| `3` | 活动冲量 | Promotion sales boost | 扩大销量 / Increase sales | 冲量、大促冲量、快速起量、积累订单、放量 |
| `4` | (旧值,UI 无) | legacy growth | - | - |

## optimizeType (SD) - 优化类型

SD `optimizeType` accepts `1`/`2`/`3`.

| code | 中文 | English | 常见说法 |
|---|---|---|---|
| `1` | 推动增长 | drive growth | 增长型 |
| `2` | 保持稳定 | maintain stability | 稳定型、控成本 |
| `3` | 活动冲量 | Event Boost | 冲量、大促冲量 |

## AI status

`status` (SD create) and `aiStatus` (SP/SB) - you send `0`/`1` on create/edit; a
group reads back as `2` once turned off.

| code | 中文 | English | 说明 |
|---|---|---|---|
| `0` | 未开启 | off / never enabled | 创建时传 0 = 不启动 AI |
| `1` | 开启 | on / running | AI 正在优化、会花钱 |
| `2` | 暂停 | paused / turned off | 读回值:曾开过又关掉的状态("AI Turned Off") |

常见说法:开/启用/打开/跑起来 -> `1`;关/关闭/停/暂停/先别开 -> `0`(创建)。

## aiPersonality - AI 人格

| code | 中文 | English |
|---|---|---|
| `1` | 非常保守 | Very Conservative |
| `2` | 保守 | Conservative |
| `3` | 平衡 | Balanced |
| `4` | 激进 | Aggressive |
| `5` | 非常激进 | Very Aggressive |

⚠️ **这份映射只用于理解用户输入**（把"偏保守""跑激进点"这类口语映射到 `1`-`5`）。向用户展示时——确认信息、查询结果、报告——一律直接显示数字（例如 **AI 人格：4**），不要替换或补充成"激进"/"Aggressive"这类文字标签。

## targetHarvestStatus - 目标收割

| code | 中文 | English |
|---|---|---|
| `0` | 关 | off |
| `1` | 开 | on |
| `2` | 开 + 源广告组精确否定 | on with exact negation in source ad group |

常见说法:收割/自动收词/挖词 -> 开;"收割并否掉源头" -> `2`。

## numType / budgetNumType - 值类型

| code | 中文 | English |
|---|---|---|
| `1` | 百分比 | percentage |
| `2` | 固定值 | fixed value |

## bidRangeType - 值类型（`1` 待确认）

| code | 中文 | English |
|---|---|---|
| `1` | 单位待确认（页面疑似竞价系数） | unit unconfirmed — UI looks coefficient-like |
| `2` | 固定值 | fixed value |

## 匹配 / 名单类型（action space）

| 字段 | code | 中文 | English |
|---|---|---|---|
| *MatchType | `1` | 精确 | exact |
| *MatchType | `2` | 词组 | phrase |
| *ListType | `1` | 包含 / 白名单 | include / whitelist |
| *ListType | `2` | 排除 / 黑名单 | exclude / blacklist |

## 自动化规则 / Rule-based automation terms

Use these terms when users mention automation templates that can be paired with AI Action
Space in Rule/RBA mode. Rule-template configuration is readable through
`get_entity_metadata.aiAutomation`, but not writable through this skill.

| 中文 | English | related action-space field / ruleType |
|---|---|---|
| 自动化规则 | Rule-based automation / Automation rules | `aiAutomation` |
| 自动化规则模板 | Automation rule template | template configured in the platform UI |
| 分时调价 | Bid dayparting | `bidDaypart` / ruleType `2` |
| 分时预算 | Budget dayparting | `budgetDaypart` / ruleType `13` |
| 定向规则 | Targeting rules | standalone ruleType `15` / `18` |
| 添加搜索词 | Harvest Keywords / Add Search Keywords | `targetHarvest` / ruleType `4` |
| 添加否定词 | Add Negative Keywords | `negativeTarget` / ruleType `5` |
| 预算规则 | Budget rules | `budgetPerformance` / ruleType `17` |
| 广告位规则 | Placement Rules | `bidAdPlace` / ruleType `19` |
| 开启/暂停广告活动（新版） | Campaign activation/pausing (New) | `structPauseCampaign` / ruleType `20` |
| 商品库存规则 | Product inventory rules | standalone automation rule, not an AI Action Space switch |
| 基于当日实时数据的策略 | strategy based on real-time data of the current day | automation rule strategy type |
| 基于历史数据的策略 | strategy based on historical data | automation rule strategy type |
| 频率设置 / 执行频次 | Frequency settings / Execution frequency | rule schedule |
| 关联广告活动 | Associate Campaigns | campaign-template binding |
| 自定义定时策略 | Custom scheduled strategy | scheduled campaign/budget rule strategy |
| 不循环 | No recurrence | one-time campaign activation/pausing schedule |

## 行动空间(AI Action Space)开关 - UI 中文 <-> 字段族

UI 里"AI 行动空间设置 / AI Action Space"分 4 个模块,每个开关右侧的 **AI** 徽标 =
交给 AI 自动决策;"高级设置模式 / Advanced settings mode"("Click to enter advanced
settings in the action space")= 展开细项。下表按 UI 分组给出 **UI 中文 / UI English /
字段族** 三列(具体开关取值见 `field-reference.md`)。解析用户意图或复述配置时对照使用。

**竞价优化 / Bid optimization**

| UI 中文 | UI English | 字段族 |
|---|---|---|
| 广告位调价 | Adjust placement bids | bidAdPlaceStatus (SP only; SD/SB: skip) |
| B2B 调价 | Amazon Business Bid Adjustment | bidAmazonBusiness |
| 分时调价 | Bid dayparting | bidDaypart |
| 按表现调价 | Optimize base bids | bidPerformance |

**预算优化 / Budget optimization**

| UI 中文 | UI English | 字段族 |
|---|---|---|
| 分时预算 | Budget dayparting | budgetDaypart |
| 按表现调预算 | Boost budget | budgetDynamic（值用 numType/num) |
| 预算重新分配 | Reallocate budget | budgetRedistribute |

**定向优化 / Targeting optimization**

| UI 中文 | UI English | 字段族 |
|---|---|---|
| 添加否定定向 | Negate targets | negativeTarget |
| 定向收割 | Harvest targets | targetHarvest |
| 定向暂停 | Pause targets | targetPausedAdd（0=off,1=on,2=on+supplement) |

**结构优化 / Structure optimization(SP only)**

| UI 中文 | UI English | 字段族 |
|---|---|---|
| 暂停商品 | Pause products | structPauseProduct |
| 暂停广告活动和广告组 | Pause campaigns & ad groups | `structPauseCampaign` (SP only) |

**品牌/非品牌/竞品模式 (Branded / Competitor mode)**

区分品牌 / 非品牌 / 竞品流量,让 AI 精准拓展与收割。总开关 = `品牌/非品牌/竞品模式`。

| UI 中文 | 字段 | 说明 |
|---|---|---|
| 品牌(勾选) | `brandedStatus` | 0=关, 1=开 |
| 选择品牌词库 | `brandedList` | 品牌词库 ID 列表(开品牌时必选) |
| 判断条件:等于 / 包含 | `brandedMatchType` | 等于=`1`(exact), 包含=`2`(phrase) |
| 竞品(勾选) | `competitorStatus` | 0=关, 1=开 |
| 选择竞品词库 | `competitorList` | 竞品词库 ID 列表 |
| 判断条件:等于 / 包含 | `competitorMatchType` | 等于=`1`(exact), 包含=`2`(phrase) |

> 注意此处"判断条件"的 UI 用词是 **等于 / 包含**(对应码 `1`/`2`),而定向/收割等
> 其它场景的同一组码 UI 叫 **精确 / 词组**--码相同,展示措辞按场景不同。
> 另:未勾选竞品模式并选竞品词库时,AI 收割**无法识别和收割竞品搜索词**。

> **预算消耗优先 / Budget utilization priority(Beta)** 是 UI 上的独立开关(更激进的
> 加价 / 加词 / 预算分配),不是 targetType 的一部分--如用户提到,按独立设置处理,
> 不要塞进目标类型。
