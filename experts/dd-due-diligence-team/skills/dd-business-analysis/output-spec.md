# 经营分析输出规范

> 输出为结构化 JSON，直接写入 `business_analysis` 表的各字段。每个 tab 对应一个 JSON 字段。

## 顶层结构

```json
{
  "c1_layout": { ... },
  "c2_management": { ... },
  "c3_revenue": { ... },
  "c4_supply": { ... },
  "c5_customer": { ... },
  "c6_tax": { ... },
  "c7_production": { ... },
  "c8_cashflow": { ... },
  "riskPoints": [ ... ]
}
```

## c1_layout（经营布局）

```json
{
  "c1_layout": {
    "bases": [
      { "location": "浙江杭州", "function": "总部+研发中心", "capacity": "正常运营" },
      { "location": "安徽合肥", "function": "生产基地", "capacity": "满产" },
      { "location": "广东深圳", "function": "销售中心", "capacity": "正常运营" }
    ],
    "sourceFiles": ["企业年报2025.pdf"]
  }
}
```

## c2_management（管理模式）

```json
{
  "c2_management": {
    "mode": "集团化管控，总部统一财务+人事",
    "subsidiary": "子公司独立经营，季度汇报",
    "digitalization": "已上线 ERP + MES 系统，数字化水平中等",
    "judgments": [
      { "type": "ok", "text": "管控模式清晰，总部对子公司有有效管控" },
      { "type": "info", "text": "数字化水平中等，建议关注信息化投入" }
    ],
    "sourceFiles": ["企业年报2025.pdf", "现场调查报告.pdf"]
  }
}
```

## c3_revenue（营收质量）

```json
{
  "c3_revenue": {
    "composition": [
      { "product": "精密零部件", "ratio": "65%", "change": "↑3pp" },
      { "product": "模具加工", "ratio": "25%", "change": "↓2pp" },
      { "product": "技术服务", "ratio": "10%", "change": "持平" }
    ],
    "marginTrend": [
      { "year": "2023", "margin": "28.5%", "status": "正常" },
      { "year": "2024", "margin": "30.2%", "status": "正向（稳步上升）" },
      { "year": "2025", "margin": "32.5%", "status": "正向（稳步上升）" }
    ],
    "judgments": [
      { "type": "ok", "text": "主营业务集中度高，核心产品占比 65%，毛利率连续 3 年上升" },
      { "type": "info", "text": "模具加工占比下降，需关注是否为主动收缩" }
    ],
    "sourceFiles": ["企业年报2023.pdf", "企业年报2024.pdf", "企业年报2025.pdf"]
  }
}
```

## c4_supply（供应集中度）

```json
{
  "c4_supply": {
    "top5": [
      { "rank": 1, "name": "甲方材料有限公司", "ratio": "22.5%" },
      { "rank": 2, "name": "乙方钢铁集团", "ratio": "18.3%" },
      { "rank": 3, "name": "丙方化工股份", "ratio": "12.1%" },
      { "rank": 4, "name": "丁方电子科技", "ratio": "5.8%" },
      { "rank": 5, "name": "戊方物流有限公司", "ratio": "3.6%" }
    ],
    "total": "62.3%",
    "assessment": "偏高",
    "sourceFiles": ["企业年报2025.pdf", "采购台账.xlsx"]
  }
}
```

## c5_customer（客户集中度）

```json
{
  "c5_customer": {
    "top5": [
      { "rank": 1, "name": "A 汽车集团", "ratio": "35.2%" },
      { "rank": 2, "name": "B 电子有限公司", "ratio": "15.8%" },
      { "rank": 3, "name": "C 机械制造", "ratio": "8.5%" },
      { "rank": 4, "name": "D 科技股份", "ratio": "6.2%" },
      { "rank": 5, "name": "E 工业集团", "ratio": "4.1%" }
    ],
    "total": "69.8%",
    "assessment": "偏高",
    "sourceFiles": ["企业年报2025.pdf", "销售台账.xlsx"]
  }
}
```

## c6_tax（账税一致）

```json
{
  "c6_tax": {
    "diffRate": "3.2%",
    "diffSource": "收入确认时点差异（完工百分比法 vs 开票时点）",
    "assessment": "可接受",
    "judgments": [
      { "type": "ok", "text": "账税差异率 3.2%，低于 5% 阈值，属正常范围" },
      { "type": "info", "text": "差异主要来自收入确认时点，非实质性差异" }
    ],
    "sourceFiles": ["纳税申报表2025.pdf", "企业年报2025.pdf"]
  }
}
```

## c7_production（产销）

```json
{
  "c7_production": {
    "metrics": [
      { "label": "年产量", "value": "120,000 件" },
      { "label": "年销量", "value": "115,000 件" },
      { "label": "产销率", "value": "95.8%" },
      { "label": "库存周转天数", "value": "45 天" }
    ],
    "purchaseLedger": [
      { "name": "特种钢材", "qty": "500 吨", "amount": "2,500 万元", "priceChange": "+5.2%" },
      { "name": "铝合金", "qty": "200 吨", "amount": "800 万元", "priceChange": "-2.1%" },
      { "name": "电子元器件", "qty": "50 万件", "amount": "600 万元", "priceChange": "+8.5%" }
    ],
    "salesLedger": [
      {
        "name": "精密零部件-A型",
        "qty": "80,000 件",
        "amount": "4,800 万元",
        "priceChange": "+3.0%"
      },
      {
        "name": "精密零部件-B型",
        "qty": "35,000 件",
        "amount": "2,100 万元",
        "priceChange": "持平"
      },
      { "name": "模具加工", "qty": "200 套", "amount": "1,500 万元", "priceChange": "-1.5%" }
    ],
    "judgments": [
      { "type": "ok", "text": "产销率 95.8%，处于健康区间（90%-105%）" },
      { "type": "info", "text": "库存周转天数 45 天，行业平均 40 天，略偏高" },
      { "type": "warn", "text": "电子元器件采购单价上涨 8.5%，需关注成本传导能力" }
    ],
    "sourceFiles": ["采购台账.xlsx", "销售台账.xlsx"]
  }
}
```

## c8_cashflow（流水）

```json
{
  "c8_cashflow": {
    "metrics": [
      { "label": "总进账", "value": "8,500 万元" },
      { "label": "总出账", "value": "7,200 万元" },
      { "label": "净流量", "value": "1,300 万元" },
      { "label": "日均余额", "value": "350 万元" },
      { "label": "我行结算占比", "value": "65%" },
      { "label": "进账集中度", "value": "0.58" },
      { "label": "月度波动率", "value": "0.15" },
      { "label": "支出收入比", "value": "0.85" }
    ],
    "topCounterparties": [
      { "direction": "收款", "name": "A 汽车集团", "amount": "3,200 万元" },
      { "direction": "收款", "name": "B 电子有限公司", "amount": "1,500 万元" },
      { "direction": "付款", "name": "甲方材料有限公司", "amount": "2,100 万元" },
      { "direction": "付款", "name": "乙方钢铁集团", "amount": "1,600 万元" }
    ],
    "judgments": [
      { "type": "ok", "text": "我行结算占比 65%，客户粘性强" },
      { "type": "ok", "text": "净流量为正，经营现金流健康" },
      { "type": "info", "text": "进账集中度 0.58，前两大客户贡献 55% 进账" }
    ],
    "sourceFiles": ["银行流水2025.pdf"]
  }
}
```

## riskPoints（风险要点）

```json
{
  "riskPoints": [
    {
      "level": "medium",
      "category": "客户集中度",
      "title": "前五大客户销售占比 69.8%，客户集中度偏高",
      "detail": "第一大客户 A 汽车集团占比 35.2%，若该客户订单下滑将显著影响营收",
      "suggest": "建议要求提供与 A 汽车集团的长期合作协议，关注合同续签情况"
    },
    {
      "level": "medium",
      "category": "供应集中度",
      "title": "前五大供应商采购占比 62.3%，供应集中度偏高",
      "detail": "前两大供应商合计占比 40.8%，存在供应链中断风险",
      "suggest": "建议了解是否有备选供应商，关注原材料价格波动对成本的影响"
    },
    {
      "level": "low",
      "category": "产销",
      "title": "电子元器件采购单价上涨 8.5%",
      "detail": "原材料成本上升可能压缩毛利空间，但目前毛利率仍在上升通道",
      "suggest": "关注下一期毛利率变化，评估成本传导能力"
    },
    {
      "level": "note",
      "category": "流水",
      "title": "进账集中度 0.58，前两大客户贡献 55% 进账",
      "detail": "流水进账与销售台账客户集中度一致，数据交叉验证通过",
      "suggest": "无需额外措施，持续监控"
    }
  ]
}
```

## HTML class 约束（必须在模板中使用的 class）

### 主容器

```html
<div class="pcf-section">...</div>
```

### 指标卡片、网格字段、数据块、研判块、评级、摘要/补充

与 dd-profile-analysis 的 output-spec.md 中定义的 `pcf-section__*` class 完全一致。

> ❗ **禁止使用 `pcf-section__evidence` 证据链块**，统一使用下方的 `pcf-section__source` 文件溯源块。

### 数据来源文件溯源（必须）

每个 section 的 HTML **末尾必须**包含文件溯源区块，列出该 section 数据所依赖的进件文件。

```html
<div class="pcf-section__source">
  <div class="pcf-section__source-title">数据来源文件</div>
  <div class="pcf-section__source-list">
    <span class="pcf-section__source-item">企业年报.pdf</span>
    <span class="pcf-section__source-item">采购台账.pdf</span>
    <span class="pcf-section__source-item">销售台账.pdf</span>
  </div>
</div>
```

- **必须列出该 section 实际使用到的所有进件文件**，以精确文件名为单位（如 "企业年报2025.pdf"、"采购台账.xlsx"）
- **禁止使用概括性描述**（如 "企业年报"、"现场调查"），必须使用进件文件的精确文件名
- 文件列表用 `<span class="pcf-section__source-item">` 标签包裹
- 如果多个 section 共用同一批文件，每个 section 也要独立列出
- 风险要点(risks.json)不需要此溯源区块

## 格式约束

1. 所有金额使用千分位分隔（如 3,200 万元）
2. 比率保留 1 位小数（如 62.3%）
3. 每个 tab 必须有 `sourceFiles` 数组字段列出精确文件名（替代旧的 `source` 字符串字段）
4. 材料不足的 tab 整体输出 `null`
5. `judgments` 中 `type` 只能是 `ok` / `warn` / `info`
6. `riskPoints` 数量 3-8 条
