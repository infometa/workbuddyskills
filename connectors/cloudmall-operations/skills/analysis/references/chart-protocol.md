# 图表可视化协议

> 本文件定义 `<chart_data>` 标签的图表选择规则与 JSON 字段规范。
>
> **当前 Agent 适配说明**：本技能的对话结果使用 Markdown 表格和文字描述。本文件中的 `<chart_data>` 标签格式**仅供参考数据结构**（图表类型、字段含义），实际输出时改用 Markdown 表格 + 文字描述呈现数据。趋势数据用表格列出每日数值，占比数据用表格列出各项占比。

---

## 图表选择路由

**数据点不足降级规则**（优先于下方路由表执行）：

当时间维度 label 数 ≤ 2 时，禁止输出 `line` / `bar` / `dual_axis` 趋势类图表，改为：
- 2 个时间点 → 用 `kpi` 展示今日 vs 昨日（或本周已有日期 vs 上周同日）对比
- 1 个时间点 → 纯文字说明数值，不出图

**环比拆图规则**（优先于下方路由表执行）：

当查询同时含"当期 vs 环比期"对比（如本周/上周）+ 不同指标量级差 ≥10 倍时，每个指标单独出一张 `line`（多 datasets），不混入同一张图。

根据 SQL 返回的数据特征，从上到下匹配，命中即停：

| 数据场景 | chart_type | 判定条件 |
|---------|-----------|---------|
| 核心指标概览 | `kpi` | 3~6 个独立 KPI 指标 + 环比变化 |
| 排行 / TOP N | `bar` | label 最长项 ≤ 8 个字符（品类名、渠道名） |
| 排行 / TOP N（长名称） | `horizontal_bar` | label 最长项 > 8 个字符（商品名、推广人名） |
| 单量级时间趋势 | `line` | 逐日/逐周趋势，各指标数值量级接近（max/min < 10） |
| 双量级时间趋势 | `dual_axis` | 两指标量级相差 10 倍以上（如 PV + 转化率） |
| 单时间点占比 | `doughnut` | 一个时间窗口内的类别占比（≤ 6 个类别） |
| 跨天占比变化 | `stacked_bar` | 多天的类别构成变化 |
| 转化漏斗 | `funnel` | 有明确前后环节递减关系（曝光→点击→加购→成交） |
| 当期 vs 环比期对比 | `bar`（多 datasets） | 两组数据同维度对比 |
| 效率矩阵 / 二维对比 | `scatter` | 两个独立指标的交叉分析 |
| 多字段明细 | `table` | 结果字段 > 5 列且无法归约为单一图表 |

**选择优先级**：
1. 单指标直答不出图（如"退款率多少"），直接文字回答
2. 能用图表就不用表格，`table` 仅在字段多且无法归约时使用
3. 消歧顺序：时间轴 → line/dual_axis/stacked_bar → 递减关系 → funnel → 占比 → doughnut → 排行 → bar/horizontal_bar → 兜底 table

**输出规则**：
1. 图表标签替代 Markdown 表格，不重复输出同内容的表格
2. 每个 `<chart_data>` 前必须有 1~2 句文字概括
3. 图表标签就近嵌入相关分析文字之后，不集中堆到末尾
4. 数值必须来自 SQL 查询结果，禁止编造
5. 输出 `<chart_data>` 前确认：所有 `[]` `{}` 引号成对闭合、无尾逗号、数值不加引号
6. 必须是合法可解析的 JSON
7. 非 table 类型不输出 columns 和 rows 字段
8. 每条 dataset 的 values 长度必须等于 labels 长度；对比类图表（如本周/上周）labels 用相对位置（周一~周日），不用两周日期并集

---

## JSON 字段规范

所有图表类型均包含 `chart_type`（必填）、`title`（必填）。`table` 类型额外必填 `columns`（列头）和 `rows`（行数据），其余类型不输出这两个字段。

| chart_type | 核心字段 | 特殊字段说明 |
|-----------|---------|------------|
| `kpi` | `kpis[]`：每项含 `label`、`value`、`change`、`change_good` | 无 labels/datasets，kpis 替代 |
| `line` / `bar` / `horizontal_bar` / `doughnut` / `funnel` | `labels[]`（X 轴或类别）、`datasets[]`：每项含 `label`、`values[]` | 标准结构；每条 dataset.values 长度 = labels 长度 |
| `stacked_bar` | 同上 | 多个 dataset 堆叠展示总量+构成，与 `bar` 多 datasets（并排对比）区分 |
| `dual_axis` | 同上 | `datasets[].axis` 必填，值为 `"left"` 或 `"right"` |
| `scatter` | `x_label`、`y_label` | `datasets[].points[]`：每点含 `x`、`y`、`label`，`size`（可选，控制气泡大小） |
| `table` | `columns[]`、`rows[]` | 无 labels/datasets；无图表视图，仅渲染为表格 |

---

## 最简示例

**kpi**（特殊结构，无 labels/datasets）：
```
<chart_data>
{"chart_type":"kpi","title":"核心指标概览","kpis":[{"label":"GMV","value":"45.2万","change":"+8.3%","change_good":true},{"label":"退款率","value":"3.2%","change":"-0.5个百分点","change_good":true}]}
</chart_data>
```

**dual_axis**（需指定 axis）：
```
<chart_data>
{"chart_type":"dual_axis","title":"近7天 PV/UV 趋势","labels":["04-01","04-02","04-03"],"datasets":[{"label":"PV","values":[9200,7800,10100],"axis":"left"},{"label":"UV","values":[1350,1100,1480],"axis":"right"}]}
</chart_data>
```

**scatter**（特殊 points 结构）：
```
<chart_data>
{"chart_type":"scatter","title":"渠道效率矩阵","x_label":"UV","y_label":"转化率(%)","datasets":[{"label":"渠道","points":[{"x":780,"y":5.2,"label":"自然流量","size":125},{"x":270,"y":8.1,"label":"分销渠道","size":93}]}]}
</chart_data>
```
