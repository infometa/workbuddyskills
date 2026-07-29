# 新股数据源优先级与多源交叉验证规范

## 一、数据源清单

| 数据源 | 类型 | 适用字段 | 命令路径 |
|---|---|---|---|
| **westock-data** | 结构化 CLI | 行情、K 线、分时、财务、IPO 日历、板块、股东、风险事件、机构评级、资金流向 | `node <westock-skill-dir>/scripts/index.js <cmd> <args>` |
| **NeoData** | 自然语言搜索 | 招股书要素、发行价、市盈率、募资额、可比公司、行业估值、宏观背景 | `python3 <neodata-skill-dir>/scripts/query.py --query "..."` |
| **交易所公告**（fallback） | Web 检索 | 北交所新股、补充招股资料、最新规则变更 | WebSearch / WebFetch |

> 路径变量见专家主 MD 的「数据源路径」段落。

## 二、字段级优先级（A 股新股）

| 字段 | 主源 | 辅源 | 备注 |
|---|---|---|---|
| 申购日期 / 上市日期 | westock `ipo hs` | NeoData 招股资料 | 双向交叉，差异即报警 |
| 发行价 | NeoData 招股资料 | westock `ipo hs` | 询价中标注「待定」 |
| 发行市盈率 | NeoData | — | 与行业 PE 对照 |
| 募资额 | NeoData | westock | 拟募资 vs 实际募资分别标注 |
| 网上发行股数 / 单户上限 | NeoData 招股说明书 | — | |
| 顶格申购市值要求 | NeoData / 券商发行公告 | — | |
| 实控人 / 保荐机构 | NeoData / 公司简况 | westock `profile` | |
| 财务三年趋势 | westock `finance --num 4` | NeoData | |
| 行业估值参照 | westock `sector` | NeoData | |
| 中签率 / 配售率 | NeoData | 申购结束后才有 | |
| 上市首日 K 线 | westock `kline --period day` | — | |
| 上市首日分时 | westock `minute` | — | |
| 资金流向 | westock `asfund` | — | 仅 A 股 |
| 风险事件（解禁等） | westock `risk` | — | 仅 A 股 |

## 三、强制多源交叉规则

凡涉及以下「关键事实字段」，**必须**调用 ≥ 2 个数据源后通过 `ipo-cross-check` skill 比对：

1. 申购日期、上市日期
2. 发行价、发行市盈率
3. 拟募资额、实际募资额
4. 网上发行股数

比对结果：
- **一致**：标注「✅ 多源一致（westock + NeoData）」
- **不一致**：必须**同时输出两边的值**，并标注「⚠️ 多源差异，需用户根据券商发行公告复核」
- **单源**：标注「⚠️ 仅单源，未交叉」

> 严禁仅输出单源结果而不标注。严禁在多源不一致时擅自选取一个值。

## 四、来源标注模板

```
（来源：westock-data ipo hs，<时间戳>）
（来源：NeoData，<查询关键词>）
（来源：westock-data ✕ NeoData，已交叉一致）
（来源：westock-data: 7.08 / NeoData: 7.10，存在差异，需用户复核）
（来源：交易所公告 <URL>）
```

每个 8 段事实矩阵的栏目末尾必须出现至少一个来源标注。

## 五、缺失数据处理

- 字段无法获取 → 标注 `数据暂不可得`
- 字段在申购前不存在（如中签率） → 标注 `申购结束后才公布`
- 字段不在覆盖范围（如港股募资额） → 标注 `本专家不覆盖，建议查询发行人公告`

严禁臆造、估算或基于经验推测后冒充事实。
