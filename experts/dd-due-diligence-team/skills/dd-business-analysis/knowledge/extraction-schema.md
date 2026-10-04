# 经营分析 — 8 大块 JSON Schema

## 字段清单

### C1 经营布局

| 字段             | 类型   | 必填 | 说明                                 |
| ---------------- | ------ | ---- | ------------------------------------ |
| bases[].location | string | ✓    | 基地位置                             |
| bases[].function | string | ✓    | 功能定位（总部/生产/销售/研发/仓储） |
| bases[].capacity | string | ✓    | 产能状态（满产/正常/闲置/在建）      |
| source           | string | ✓    | 数据来源                             |

### C2 管理模式

| 字段           | 类型     | 必填 | 说明           |
| -------------- | -------- | ---- | -------------- |
| mode           | string   | ✓    | 管控模式       |
| subsidiary     | string   | ✓    | 子公司管控方式 |
| digitalization | string   | ✓    | 数字化水平     |
| judgments[]    | Judgment | ✓    | 研判结论       |
| source         | string   | ✓    | 数据来源       |

### C3 营收质量

| 字段                  | 类型     | 必填 | 说明                  |
| --------------------- | -------- | ---- | --------------------- |
| composition[].product | string   | ✓    | 产品/服务名           |
| composition[].ratio   | string   | ✓    | 营收占比（如 "65%"）  |
| composition[].change  | string   | ✓    | 同比变化（如 "↑3pp"） |
| marginTrend[].year    | string   | ✓    | 年份                  |
| marginTrend[].margin  | string   | ✓    | 毛利率                |
| marginTrend[].status  | string   | ✓    | 状态判定              |
| judgments[]           | Judgment | ✓    | 研判结论              |
| source                | string   | ✓    | 数据来源              |

### C4 供应集中度

| 字段         | 类型   | 必填 | 说明                 |
| ------------ | ------ | ---- | -------------------- |
| top5[].rank  | number | ✓    | 排名 1-5             |
| top5[].name  | string | ✓    | 供应商名称           |
| top5[].ratio | string | ✓    | 采购占比             |
| total        | string | ✓    | 前五合计（沙箱计算） |
| assessment   | string | ✓    | 评估结论（沙箱计算） |
| source       | string | ✓    | 数据来源             |

### C5 客户集中度

同 C4 结构，字段含义替换为客户/销售。

### C6 账税一致

| 字段        | 类型     | 必填 | 说明               |
| ----------- | -------- | ---- | ------------------ |
| diffRate    | string   | ✓    | 差异率（沙箱计算） |
| diffSource  | string   | ✓    | 差异主要来源       |
| assessment  | string   | ✓    | 评估结论           |
| judgments[] | Judgment | ✓    | 研判结论           |
| source      | string   | ✓    | 数据来源           |

### C7 产销

| 字段                         | 类型     | 必填 | 说明     |
| ---------------------------- | -------- | ---- | -------- |
| metrics[].label              | string   | ✓    | 指标名   |
| metrics[].value              | string   | ✓    | 指标值   |
| purchaseLedger[].name        | string   | ✓    | 原材料名 |
| purchaseLedger[].qty         | string   | ✓    | 采购量   |
| purchaseLedger[].amount      | string   | ✓    | 采购金额 |
| purchaseLedger[].priceChange | string   | ✓    | 单价波动 |
| salesLedger[].name           | string   | ✓    | 产品名   |
| salesLedger[].qty            | string   | ✓    | 销量     |
| salesLedger[].amount         | string   | ✓    | 销售额   |
| salesLedger[].priceChange    | string   | ✓    | 单价波动 |
| judgments[]                  | Judgment | ✓    | 研判结论 |
| source                       | string   | ✓    | 数据来源 |

### C8 流水

| 字段                          | 类型     | 必填 | 说明             |
| ----------------------------- | -------- | ---- | ---------------- |
| metrics[].label               | string   | ✓    | 指标名           |
| metrics[].value               | string   | ✓    | 指标值           |
| topCounterparties[].direction | string   | ✓    | "收款" 或 "付款" |
| topCounterparties[].name      | string   | ✓    | 对手方名称       |
| topCounterparties[].amount    | string   | ✓    | 金额             |
| judgments[]                   | Judgment | ✓    | 研判结论         |
| source                        | string   | ✓    | 数据来源         |

## 通用类型

### Judgment

```json
{ "type": "ok|warn|info", "text": "研判结论文本" }
```

- `ok` — 正向/达标/无风险
- `warn` — 需关注/有风险信号
- `info` — 中性说明/补充信息
