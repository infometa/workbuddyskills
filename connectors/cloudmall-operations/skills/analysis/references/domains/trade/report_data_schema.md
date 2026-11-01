# report_data.json Schema (v2.0)

> ⚠️ **本文件已降级为开发者参考文档**（2026-04-24）
> workflow_report.md 步骤 4 不再引用本文件。模型组装 JSON 时读取 `schema_examples/cap_{capability_id}.json`。
> 本文件保留作为字段类型、衍生指标公式、数据来源表映射等技术细节的参考。

报告生成脚本所需的标准数据格式。主控负责执行 SQL、组装数据、撰写文案，统一放入**一个 JSON 文件**，脚本读取后计算衍生指标 + 渲染 HTML。

> **设计原则**：一个 JSON 包含两部分 — 上半部分是 SQL 原始数据（主控从查询结果灌入），下半部分是主控撰写的文案（summary/findings/recommendations）。脚本负责格式化和渲染。

---

## ★ v2.0 新增：自动 Findings 模式

**当 `findings` 字段缺失或为空数组时**，脚本会自动从原始数据生成 6 个标准分析章节（含表格+图表+文字）。

### 简化版 JSON（推荐）

主控只需提供以下字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `meta` | ✅ | 报告元信息 |
| `overview` | ✅ | 当期汇总数据 |
| `previous_overview` | ✅ | 环比期汇总数据 |
| `daily_summary` | ✅ | 当期逐日明细 |
| `previous_daily_summary` | ✅ | 环比期逐日明细 |
| `weekly_trend` | 推荐 | 近 N 周汇总趋势 |
| `refund_by_category` | 可选 | 品类退款拆分 |
| `executive_summary` | 推荐 | 执行摘要 HTML |
| `highlights` | 推荐 | 亮点+痛点卡片 |
| `insights` | 推荐 | 关键洞察列表 |
| `recommendations` | 推荐 | 业务建议列表 |
| `finding_narratives` | **推荐** | 5 段分析文案（HTML），按顺序覆盖自动生成的模板文字 |
| ~~`findings`~~ | **不需要** | 脚本自动生成！ |

### 自动生成的 6 个章节

| 编号 | 章节 | 数据来源 | 包含 |
|------|------|---------|------|
| 2.1 | 逐日 GMV 走势 | daily_summary + previous_daily_summary | 趋势图×2 + 逐日明细表 |
| 2.2 | 增长驱动力拆解 | overview + previous_overview | 瀑布图 + 因子表 + 效率表 |
| 2.3 | 退款多维诊断 | overview + daily_summary + weekly_trend | 柱状图 + 趋势图 + 指标表 + 逐日表 |
| 2.4 | 下单→支付转化 | overview | 对比图 + 折损表 |
| 2.5 | 补贴效率分析 | overview + weekly_trend | 趋势图 + 环形图 + 效率表 |
| 2.6 | 增长含金量评级 | 综合计算 | 净GMV图 + 评级表（A/B/C/D） |

### 简化版 vs 完整版对比

| 维度 | 简化版（v2.0 推荐） | 完整版（v1.x） |
|------|-------------------|---------------|
| findings 字段 | 不需要 | 手写 60-300 行 JSON |
| 表格 | 脚本自动生成 | 手工构造 headers+rows |
| 图表 | 脚本自动生成 | 手工配置 Chart.js |
| 文案 | 脚本自动生成分析文字 | 手写 content_html |
| 灵活度 | 固定 6 章节结构 | 完全自定义 |
| JSON 行数 | ~50 行 | ~350 行 |

> 如果需要自定义 findings，仍可手动提供 `findings` 数组，脚本会优先使用手动版本。

---

## 完整结构

```json
{
  "meta": {
    "brand_name": "Demo超市",
    "title": "日常经营看板报告",
    "subtitle": "核心经营指标全貌 + 订单效率 + 增长含金量",
    "start_date": "20260324",
    "end_date": "20260330",
    "domain": "trade",
    "capability_id": 1,
    "generated_at": "2026-04-07T14:30:00"
  },

  "_comment_data": "=== 以下为 SQL 原始数据（主控从查询结果灌入） ===",

  "overview": {
    "gmv": 1284530, "pay_uv": 18432, "pay_cnt": 26134,
    "order_uv": 21800, "order_cnt": 28200, "order_amt": 1527200,
    "sales_qty": 37110, "refund_amt": 87268, "refund_uv": 1509,
    "refund_order_cnt": 1420,
    "visit_pv": 245000, "visit_uv": 68000,
    "browse_pv": 186000, "browse_uv": 52000, "register_uv": 3200
  },
  "previous_overview": {
    "gmv": 1144000, "pay_uv": 16956, "pay_cnt": 23560,
    "order_uv": 19760, "order_cnt": 25200, "order_amt": 1336000,
    "sales_qty": 34868, "refund_amt": 63040, "refund_uv": 1137,
    "refund_order_cnt": 1080,
    "visit_pv": 220000, "visit_uv": 62000,
    "browse_pv": 168000, "browse_uv": 48000, "register_uv": 2850
  },
  "daily_summary": [
    {"stat_date": "20260324", "gmv": 152000, "pay_uv": 2280, "pay_cnt": 3420, "order_uv": 2780, "order_cnt": 3680, "order_amt": 192000, "sales_qty": 4856, "refund_amt": 8200}
  ],
  "previous_daily_summary": [
    {"stat_date": "20260317", "gmv": 138000, "pay_uv": 2100, "pay_cnt": 3080, "order_uv": 2450, "order_cnt": 3320, "order_amt": 172000, "sales_qty": 4558, "refund_amt": 7120}
  ],
  "refund_by_category": [
    {"category_name": "生鲜果蔬", "refund_amt": 28400, "refund_cnt": 362, "gmv": 126222}
  ],
  "weekly_trend": [
    {"week_label": "W10", "gmv": 1020000, "pay_uv": 15200, "pay_cnt": 21280, "order_uv": 17600, "refund_amt": 48960}
  ],

  "_comment_narratives": "=== 以下为主控撰写的文案 ===",

  "executive_summary": "<p>本周Demo超市整体经营表现向好...</p>",
  "highlights": {
    "positive": {"label": "最超预期的亮点", "text": "支付人数增长..."},
    "negative": {"label": "最不及预期的痛点", "text": "连带率降至..."}
  },
  "insights": ["<strong>量驱动型增长</strong>：...", "<strong>增长含金量缺口</strong>：..."],
  "findings": [
    {
      "title": "GMV 走势呈现明显的周末效应",
      "content_html": "<p>分析描述...</p>",
      "tables": [{"headers": [...], "rows": [...], "summary_row": [...]}],
      "charts": [{"id": "chart_xxx", "title": "...", "type": "line", "half_width": true, "data": {...}, "options": {...}}]
    }
  ],
  "recommendations": [
    {"priority": "P0", "title": "退款率止血", "items": ["...", "..."]}
  ],
  "appendix_tables": [
    {"title": "指标口径说明", "headers": [...], "rows": [...]}
  ]
}
```

---

## 字段说明

### meta

报告元信息。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `brand_name` | string | ✅ | 分析对象名称 |
| `title` | string | ✅ | 报告标题（如"日常经营看板报告"） |
| `subtitle` | string | 可选 | 副标题，不填时脚本按 capability_id 自动选默认文案 |
| `start_date` | string | ✅ | 起始日期 YYYYMMDD |
| `end_date` | string | ✅ | 截止日期 YYYYMMDD |
| `domain` | string | ✅ | 业务域：`trade` / `commodity` / `user` / `marketing` / `cross` |
| `capability_id` | int | ✅ | 能力编号（如 1 = 日常经营看板） |
| `generated_at` | string | ✅ | 生成时间 ISO 格式 |

### overview

当期汇总数据。一行，所有指标为整个分析周期的聚合值。

| 字段 | 类型 | 说明 | SQL 来源 |
|------|------|------|---------|
| `gmv` | float | 成交金额 | `SUM(gmv)` |
| `pay_uv` | int | 支付人数 | `BITMAP_COUNT(BITMAP_UNION(pay_uv))` |
| `pay_cnt` | int | 支付订单数 | `BITMAP_COUNT(BITMAP_UNION(pay_cnt))` |
| `order_uv` | int | 下单人数 | `BITMAP_COUNT(BITMAP_UNION(order_uv))` |
| `order_cnt` | int | 下单订单数 | `BITMAP_COUNT(BITMAP_UNION(order_cnt))` |
| `order_amt` | float | 下单金额 | `SUM(order_amt)` |
| `sales_qty` | int | 销售件数 | `SUM(sales_qty)` |
| `refund_amt` | float | 退款金额 | `SUM(refund_amt)` |
| `refund_uv` | int | 退款人数 | `BITMAP_COUNT(BITMAP_UNION(refund_uv))` |
| `refund_order_cnt` | int | 退款订单数 | `BITMAP_COUNT(BITMAP_UNION(refund_order_cnt))` |
| `visit_pv` | int | 访问次数（app_launch） | `SUM(visit_pv)` |
| `visit_uv` | int | 访问人数（app_launch） | `BITMAP_COUNT(BITMAP_UNION(visit_uv))` |
| `browse_pv` | int | 页面浏览次数（browse_wxapp_page） | `SUM(browse_pv)` |
| `browse_uv` | int | 页面浏览人数（browse_wxapp_page） | `BITMAP_COUNT(BITMAP_UNION(browse_uv))` |
| `register_uv` | int | 注册人数 | `BITMAP_COUNT(BITMAP_UNION(register_uv))` |

> 数据来源：`app_sales_stat_overview_di`

### previous_overview

环比期汇总数据，字段与 `overview` 完全相同。用于计算所有环比指标。如无数据可为空对象 `{}`。

### daily_summary[]

当期逐日明细，按 `stat_date` 升序，每日一行。

| 字段 | 类型 | 说明 |
|------|------|------|
| `stat_date` | string | 日期 YYYYMMDD |
| `gmv` | float | 当日 GMV |
| `pay_uv` | int | 当日支付人数 |
| `pay_cnt` | int | 当日支付订单数 |
| `order_uv` | int | 当日下单人数 |
| `order_cnt` | int | 当日下单订单数 |
| `order_amt` | float | 当日下单金额 |
| `sales_qty` | int | 当日销售件数 |
| `refund_amt` | float | 当日退款金额 |

> 数据来源：`app_sales_stat_overview_di`（逐日查询）

### previous_daily_summary[]

环比期逐日明细，字段与 `daily_summary` 完全相同。用于趋势对比图（本周 vs 上周）。

> ⚠️ 当期和环比期的天数必须一致，脚本按索引位置一一对应绘制对比图。

### refund_by_category[]

退款按品类拆分，按退款金额降序。用于退款诊断章节的品类表格。

| 字段 | 类型 | 说明 |
|------|------|------|
| `category_name` | string | 品类名称 |
| `refund_amt` | float | 退款金额 |
| `refund_cnt` | int | 退款笔数 |
| `gmv` | float | 该品类 GMV（用于计算品类退款率） |

> 数据来源：`app_commodity_stat_category_di` 或 `app_commodity_stat_spu_di`（按品类聚合）

### weekly_trend[]

近 N 周汇总趋势（建议 4 周），按时间升序。用于退款率/补贴 ROI/转化率的多周趋势图。

| 字段 | 类型 | 说明 |
|------|------|------|
| `week_label` | string | 周标签（如 "W10"、"W11"） |
| `gmv` | float | 周 GMV |
| `pay_uv` | int | 周支付人数 |
| `pay_cnt` | int | 周支付订单数 |
| `order_uv` | int | 周下单人数 |
| `refund_amt` | float | 周退款金额 |

> 数据来源：`app_sales_stat_overview_di`（按周聚合）

---

## 脚本负责计算的衍生指标

以下指标不需要在 JSON 中提供，脚本从原始字段自动计算：

| 衍生指标 | 计算公式 | 来源 |
|---------|---------|------|
| 客单价 | `gmv / pay_uv` | overview |
| 笔单价 | `gmv / pay_cnt` | overview |
| 连带率 | `sales_qty / pay_cnt` | overview |
| 购买频次 | `pay_cnt / pay_uv` | overview |
| 下单→支付转化率 | `pay_uv / order_uv` | overview |
| 金额折损率 | `1 - gmv / order_amt` | overview |
| 退款率 | `refund_amt / gmv` | overview |
| 退款渗透率 | `refund_uv / pay_uv` | overview |
| 退款人均金额 | `refund_amt / refund_uv` | overview |
| 净 GMV | `gmv - refund_amt` | overview |
| 日环比增速 | `(当日 - 环比日) / 环比日` | daily vs previous_daily |
| 品类退款率 | `refund_amt / gmv` | refund_by_category |
| 周退款率趋势 | `refund_amt / gmv` | weekly_trend |
| 周转化率趋势 | `pay_uv / order_uv` | weekly_trend |

---

## 文案字段（主控撰写）

以下字段由主控基于数据分析结果撰写，非 SQL 查询结果。

### executive_summary（推荐）

一段 HTML 文本，概括报告核心结论。渲染在 Section 1 开头。

### highlights（推荐）

亮点 + 痛点卡片。`positive.label` / `positive.text` + `negative.label` / `negative.text`，text 支持 HTML。

### insights（推荐）

关键洞察列表（string[]），3~5 条，支持 HTML 标签。渲染为蓝色洞察框。

### findings（必填）

核心分析发现，报告主体。数组，每个元素为一个分析章节：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 发现标题（脚本自动加编号 2.1、2.2...） |
| `content_html` | string | ✅ | 分析描述，支持 HTML |
| `tables` | array | 可选 | 表格列表，每个含 `headers`(string[]) + `rows`(array[]) + `summary_row`(array，可选） |
| `charts` | array | 可选 | Chart.js 图表列表，每个含 `id` / `title` / `type`(line/bar/doughnut) / `half_width`(bool) / `data`({labels, datasets}) / `options` |

charts.data.datasets[] 每项：`label`(string) + `data`(number[]) + `color`(string，可选) + `fill`(bool) + `dash`(bool) + `show_datalabels`(bool) + `datalabel_format`(yuan/percent/raw)

### recommendations（推荐）

业务优化建议卡片。数组，每项：`priority`(P0/P1/P2/P3) + `title`(string) + `items`(string[]，支持 HTML)。

### appendix_tables（可选）

附录表格。数组，每项：`title`(string) + `headers`(string[]) + `rows`(array[])。

---

## 数据来源表映射

| JSON 字段 | SQL 查询的数据表 |
|---------|---------------|
| `overview` / `previous_overview` | `app_sales_stat_overview_di` |
| `daily_summary` / `previous_daily_summary` | `app_sales_stat_overview_di`（逐日） |
| `refund_by_category` | `app_commodity_stat_category_di`（按品类聚合退款） |
| `weekly_trend` | `app_sales_stat_overview_di`（按周聚合，近 4 周） |
