# MQL 语法参考（data-query skill）

> 本文件由 data-query skill 加载。本会话中第一次调用 `metric_query` 之前，必须完整读完本文件。
>
> **边界**：意图理解、口语解读、时间口径判定、指标/维度/维度值探查、路由、可行性、澄清门——全部在 **SKILL.md**（Step 1–5），本文件不重复。
> **本文件的起点**：指标名、维度名、维度值、时间口径**均已探查确认**；从这里开始，只负责把已确认的意图翻译成合法 MQL 并执行（SKILL.md Step 6–7）。

## Tools

探查工具（`metric_search` / `metric_dimensions` / `metric_dimension_resolve`）的用法与探查纪律在 **SKILL.md Step 3**——本文件从"指标、维度、维度值已探查确认"开始，只覆盖查询的构建与执行。

### metric_query — 执行 MQL 查询
| 参数 | 说明 |
|------|------|
| `query_json` | 完整的 MQL 查询 JSON 对象（格式见 §1） |

**limit / offset**：**默认不写 `limit`**——工具自动分页取全量并落 CSV。仅在用户明确要 Top-N 或明确要预览 N 条时写。不要为"防止数据太多"主动加——超硬上限（默认 100 万行）会返回截断警告，必须复述并引导用户加过滤。`offset`（默认 1）仅手动翻页时用。

**前置要求**：MQL 不是标准 SQL；本文件未覆盖的写法不要凭 SQL 经验推测。

---

## 构建原则（动手前先定）

**buildReason 说明**：`buildReason` 是构建过程的**内部决策记录**（不是 JSON 字段），回复用户时自然口语化转述。**至少要讲清**：时间判定依据（相对/字面值）、metricDefinitions key 的注册情况、占比/排名的过滤选择、多指标的维度交集。缺维度/指标、或口径有取舍时，把 buildReason 内容自然转述给用户（不足以构建查询的歧义走 SKILL.md Step 5 反问，不在这里处理）。

**先判断是否需要构建**：本轮没有取数意图（纯寒暄、纯概念解释、用户只是确认上一轮结论）→ 返回空 JSON `{}`，不构建查询。

**总原则：能简则简**
用户问题能用"指标 + 维度 + 时间"直接回答时，不要堆额外的 metricDefinitions/同环比/占比/排名：
- "昨天的同比增长率" → 只用 `__sameperiod__yoy__growth` 后缀
- "各 XX 的指标" → 直接查
- "日均某指标"（返回单值）→ metricDefinitions + period + preAggs，**不要**往 dimensions 加 `metric_time__day`（那是按天展开，不是日均）
- "上月 XX 总量" → timeConstraint 上月 + 空 dimensions，**不要**加 `metric_time__day`

---

## 1. 请求参数

> **三条最易错的"语义 → 语法"映射**（意图解读本身在 SKILL.md Step 1/2）：
> - **均值分两种**：时间维度的均值（日均 / 月均）→ period + preAggs（§1.2.2）；非时间维度的均值（每店 / 每人）→ `multi_level_agg`（§1.2.4）。用错会得到完全不同的数。
> - **"X 期末 / 期初"是单日**，不是整期 → `SPECIFY_DATE`（§1.2.1）或期末偏移（§1.1.1），**不是** `DateTrunc` 整期。
> - **"合计 / 总量" = dimensions 留空**；加了维度就变成分组展示。

请求体是标准 JSON。**字符串值内部的双引号必须转义为 `\"`。**
- `"filters": ["[dim_A]= \"value_1\""]`
- `"timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\""`

### 1.1 metrics（必填）— 指标列表

```json
"metrics": ["metric_A", "metric_B"]
```

**快速计算不能链式叠加**（自检 4）：每个指标只能挂**一个**快速计算。需要多步时用 metricDefinitions 拆步。

#### 1.1.1 同环比

> "同比"/"环比"到后缀的映射：见自检 3（"同比"单独出现 → 一律 yoy；"环比" → 按时间粒度，绝不是 yoy）。

**语法**：`{指标}__sameperiod__{偏移粒度}__{方法}`

**偏移粒度**（常用）：

| 用户说 | 偏移粒度 |
|-------|---------|
| 日环比 | `dod` |
| 周环比 | `wow` |
| 月环比 | `mom` |
| 季环比 | `qoq` |
| 同比 | `yoy` |

**期末/期初**（仅用于"与 XX 期末/期初相比"）：`moeom`（上月末）、`qoeoq`（上季末）、`yoeoy`（上年末）、`mosom`（上月初）、`yosoy`（上年初）。

所有偏移粒度支持 `{N}_` 前缀（如 `-2_yoy` = 两年前同期）。

> **提示**："同比"无粒度前缀时一律映射 yoy（见自检 3 + 本节开头的映射规则）；**只有**用户明确说"与 XX 期末/期初相比"时才用期末/期初偏移。

**⚠️ "与期末比" ≠ "同比"**：

| 用户说 | 含义 | 实现 |
|-------|------|---------|
| "同比"、"年同比" | 与**去年同期**比 | `__sameperiod__yoy__growth` |
| "与**去年末**相比" | 与去年最后一天比 | metricDefinitions + period 定位去年末（如 `SPECIFY_DATE end day of -1 year`） |
| "与**上月末**相比" | 与上月最后一天比 | `__sameperiod__moeom__growth`（要求天粒度） |

**⚠️ 未完结当期的同环比**：查"本周/月/季/年 + 同环比"必须用 period + indirections 对齐到相同跨度，否则严重失真（见自检 8 和示例 §2.4）。

**方法**：

| 用户说 | 方法 | 计算 |
|-------|------|------|
| 同期/环比值 | `value` | 对比期的原始值 |
| 增长了多少 | `growthvalue` | 当期 − 对比期 |
| 增长率 / 增速 | `growth` | (当期 − 对比期) / 对比期 |
| 下降了多少 | `decrease` | 对比期 − 当期 |
| 下降率 | `decreaserate` | (对比期 − 当期) / 对比期 |

**约束**：metric_time 必须出现在 dimensions 或 timeConstraint；偏移粒度不能细于 metric_time 粒度；期末/期初偏移仅在 `metric_time__day` 粒度可用。

**在已含时间限定的指标上叠同环比**：候选指标里名字含时间限定后缀的派生指标（如 `_ytd`、`_mtd` 等）可以叠 `__sameperiod__` 快速计算，但必须：dimensions 含 `metric_time__day`，且 timeConstraint 锚定具体日期。**推荐改用 metricDefinitions + period + indirections**，语义更清晰。

#### 1.1.2 占比

**语法**：`{指标}__proportion__{范围维度}`

**数学含义**：`占比 = 当前行值 / 范围维度分组的聚合值`

| 范围维度写法 | 分母 |
|------------|------|
| `proportion__`（⚠️ 结尾**两个下划线**，后面不接维度名） | 全部数据的聚合（全局占比） |
| `proportion__dim_A` | 每个 dim_A 组内各自聚合（组内占比） |

> **选择规则**：问"这一行是**谁**的占比"。"占总体" → 留空；"在 A 组内" → 填 A。

**⚠️ 前提——dimensions 必须包含参与占比计算的维度**：用 `proportion__`（全局占比）时，参与占比计算的实体维度（如渠道、品牌）**必须**出现在 `dimensions`，否则系统无法按该维度分组算占比。
- ❌ `"dimensions": []` + `proportion__` → 无分组维度，算不了占比
- ✅ `"dimensions": ["dim_A"]` + `proportion__` → 按维度分组，算每个维度值的全局占比

**⚠️ 两个坑（自检 2 的具体表现）**：
- **分母被缩小**：`filters` 在占比计算**之前**过滤数据；筛到单值后分母只剩它自己 → 占比恒 100%。要筛单值，用 `resultFilters` 做展示过滤（见 §1.4 和示例 §2.7）
- **范围覆盖全部维度**：`proportion__dim_A` 搭配 `dimensions: ["dim_A"]`，每行的分母就是它自己 → 100%。改用 `proportion__`（全局占比）

#### 1.1.3 排名

**语法**：`{指标}__{方法}__{顺序}__{范围维度}`

- **方法**：`rank`（并列跳号）、`rankDense`（并列不跳号）、`rowNumber`（不并列）
- **顺序**：`desc`（最大 = 1）、`asc`（最小 = 1）
- **范围维度**：省略 = 全局排名；填 dim_A = dim_A 组内排名

**坑与占比完全相同**：范围维度覆盖全部非日期维度 → 恒为 1；filters 缩小范围 → 排名失真。用 resultFilters 做展示过滤。

#### 1.1.4 时间限定

**语法**：`{指标}__period__{限定}`

| 类型 | 语法示例 |
|------|---------|
| 近 N 期 | `7d`、`3w`、`6m`、`2q`、`1y` |
| 当期至今 | `ytd`、`qtd`、`mtd`、`wtd` |
| 当期 | `cy`、`cq`、`cm`、`cw`、`cd` |

**约束**：被引用的指标不能已含时间限定；**必须有明确的时间锚点**（timeConstraint 或 dimensions 里的 metric_time）。

---

### 1.2 metricDefinitions（选填）— 临时指标定义

**何时必须用 metricDefinitions + expr**（这些措辞出现时，"能简则简"不适用）：
- "差值"、"差了多少"、"多了多少"、"少了多少" → `expr: "[m1] - [m2]"`
- "多少倍"、"倍数" → `expr: "[m1] / [m2]"`
- "不含税"、"扣除 XX 后"、"自定义公式" → 按用户公式构建 expr
- "前 N 名的 XX 总量"、"Top N 的合计/占比" → **必须两步**：先查排名圈定子集，再对子集求和

（"对比一下"、"看看差异"这类模糊表述**不**触发——见 SKILL.md Step 1 口语解读）

**临时指标命名**：必须与所有既有指标名不同，避免命名冲突。建议加业务前缀/后缀区分。

```json
"metrics": ["my_temp_metric"],
"metricDefinitions": {
    "my_temp_metric": { "refMetric": "metric_A", ... }
}
```

**可配置属性**：

| 属性 | 说明 | 约束 |
|------|------|------|
| `refMetric` | 引用既有指标 | |
| `expr` | 复合表达式 `"[m1]+[m2]"` | 可引用其它临时指标 |
| `period` | 时间限定 | 只支持相对偏移；`of` 后的锚点粒度不能细于 timeConstraint 粒度 |
| `metricGrain` | 时间粒度 | DAY/WEEK/MONTH/QUARTER/YEAR |
| `preAggs` | 时间维度上的多层聚合 | **格式是数组** `[{...}]`；必须配 period |
| `filters` | 业务限定 | 支持维度过滤和 MetricMatches |
| `indirections` | 衍生方式 | 同环比/占比/排名/多层聚合 |
| `specifyDimension` | 聚合维度控制 | `EXCLUDE` 排除外层分组影响 |

#### 1.2.1 period 语法

**只支持相对日期偏移**，基于 timeConstraint 锚定的日期做偏移。

**`of` 后的锚点粒度规则**：`of` 后的粒度**不能细于** timeConstraint 的锚点粒度。
- timeConstraint 锚定到天 → `of` 可用 `day`、`week`、`month`、`quarter`、`year`
- timeConstraint 锚定到月 → `of` 可用 `month`、`quarter`、`year`（**不能用** `day`、`week`）

**to_date**（区间：偏移日 ~ 锚点日）：
```
"to_date -6 day of 0 day"    → 基准日前 6 天 ~ 基准日（共 7 天）
"to_date -7 day of -1 day"   → 不含基准日（基准日前 8 天 ~ 前 1 天，共 7 天）
```

**grain_to_date**（某粒度的起点 ~ 锚点）：
```
"grain_to_date 0 year of 0 day"      → 今年年初 ~ 基准日（年初至今）
"grain_to_date -1 year of -1 day"    → 去年年初 ~ 昨天（含去年全年 + 今年至昨天，约两年跨度）
```

**relative_date**（单个日期/月份定位）：
```
"relative_date 0 month of 0 day"     → 基准日所在月
"relative_date -1 month of 0 day"    → 上月
```

**SPECIFY_DATE**（期初/期末定位）：
```
"SPECIFY_DATE start day of -1 year"   → 去年第一天
"SPECIFY_DATE end day of -1 month"    → 上月最后一天
```

**period 与 timeConstraint 的配合**：
- timeConstraint 锚定到天 → period 用 `of 0 day` 表示该天
- timeConstraint 锚定到月 → period 用 `of 0 month` 表示该月
- 比较两个月（如 6 月 vs 1 月）→ timeConstraint 锚定 6 月，period 用 `relative_date -5 month of 0 month` 定位 1 月

#### 1.2.2 preAggs（时间维度上的多层聚合）

**格式是数组**，必须配 period。

```json
"preAggs": [{"granularity": "DAY", "calculateType": "AVG"}]
```

- `granularity`：DAY / WEEK / MONTH / QUARTER / YEAR
- `calculateType`：AVG / MAX / MIN

典型场景："近 30 天的日均" = period 限定 30 天 + preAggs 按 DAY 求 AVG。

**⚠️ preAggs 与 dimensions 里的时间粒度**：用 preAggs 按 DAY 聚合时，**不要**在外层 dimensions 再放 `metric_time__day`。preAggs 已按天聚合再取 AVG/MAX/MIN；外层再按天展开等于没聚合。同理，preAggs 按 MONTH 聚合时 dimensions 不要放 `metric_time__month`。

**preAggs + 同比**：有 preAggs 时不能直接叠 `__sameperiod__`。必须分别定义今年/去年两个临时指标（各含 period + preAggs），再用 expr 算增长率。

#### 1.2.3 filters（业务限定）与 MetricMatches

临时指标可以附加维度过滤：

```json
"my_metric": {
    "refMetric": "metric_A",
    "filters": ["[dim_X]= \"value_1\""]
}
```

**MetricMatches** —— 按指标值筛出维度值，再用筛出的维度值计算指标：

`MetricMatches([维度名], [指标名] 运算符 值)`

**⚠️ MetricMatches 里的 `[指标名]` 只能是既有真实指标，不能是 metricDefinitions 临时指标**：`[指标名]`必须是 `metric_search` 返回过的真实 metricName（或平台预定义派生指标）；**绝不能**引用同一查询 metricDefinitions 里临时定义的 key——平台不解析临时指标。
- ❌ `"both": { "refMetric": "M", "filters": ["MetricMatches([customer_id], [temp_x] > 0)"] }`（`temp_x` 是同查询临时定义的指标，不能被引用）
- ✅ `"filters": ["MetricMatches([customer_id], [real_metric] > 0)"]`
- 如果条件需要"带筛选口径的指标"（如"买过某商品的客人"），MetricMatches **无法**通过引用带过滤的临时指标表达该口径；要么用**已预定义该口径**的派生指标（先 `metric_search` 找），要么——交叉条件无法用 MetricMatches 表达时——按 SKILL.md Step 3 转入 SQL 路径（直接 SQL）。

**MetricMatches vs resultFilters**：同指标过滤（"哪些维度的指标 A ≥ 某值"）→ resultFilters；跨指标过滤（"指标 A ≥ 某值的维度有多少个" → 用 A 筛维度值，再算 B）→ MetricMatches。

**MetricMatches 约束**：每个 MetricMatches 只支持一个指标条件。多个指标条件必须拆成多个 MetricMatches（数组内 AND）：

```json
"filters": [
    "MetricMatches([dim_X], [metric_C] > 30)",
    "MetricMatches([dim_X], [metric_D] < 0.2)"
]
```

**MetricMatches 空结果**：见 §4.2 的排查清单。

**用 MetricMatches 表达"行为定义人群"**（能否这样表达是路由决策，判定表在 SKILL.md Step 3；此处只是命中后的写法）：

- **单条件人群**（"在渠道 A 买过"）→ `MetricMatches([{人群实体维度}], [{A 口径的真实指标}] > 0)`；若渠道本身就是该指标的维度，用普通 filters 更简单。
- **排他人群**（"只在 A、不在 B"）→ 两个 MetricMatches 组合（数组内 AND）：`[{A 指标}] > 0` 与 `[{B 指标}] <= 0`——**两个口径的真实指标都必须存在**。
- ⛔ 缺任一真实指标时**不要**用临时指标凑（§1.2.3 已说明 MetricMatches 不解析临时指标）→ 按 SKILL.md Step 3 切换 SQL 路径。

#### 1.2.4 indirections（衍生方式）

```
"indirections": ["sameperiod__yoy__value"]                     → 同比
"indirections": ["proportion__dim_A"]                           → dim_A 组内占比
"indirections": ["rank__desc__dim_A"]                           → dim_A 组内排名
"indirections": ["multi_level_agg__avg,dim_A"]                  → 非时间维度的多层聚合
```

**多层聚合的选择**：时间维度上的多层聚合 → preAggs + period；非时间维度上的多层聚合 → indirections 里的 multi_level_agg。

**period + indirections 组合（推荐）**：不带 preAggs 的 period 指标做同环比 → 用 `period` + `indirections: ["sameperiod__yoy__growth"]`。有 preAggs 时不能用该组合；必须手工拆两步 + expr。

**multi_level_agg 与外层 dimensions 冲突**：聚合维度同时在外层 dimensions 里时，结果恒等于自身。必须加 `specifyDimension: { "type": "EXCLUDE", "dimensions": "dim_X" }`。

---

### 1.3 dimensions（选填）— 分析维度

日期维度支持粒度后缀：`__year`、`__quarter`、`__month`、`__week`、`__day`。

**⚠️ 粒度后缀必须全小写**：维度名里的粒度后缀（`__day`、`__month`、`__year`、`__week`、`__quarter`）**必须小写**。这是 API 硬性要求；大写会导致查询失败或返回空结果。
- ✅ `metric_time__day`、`metric_time__month`、`metric_time__year`
- ❌ `metric_time__DAY`、`metric_time__MONTH`、`metric_time__YEAR`（大写后缀 = 错误）

同理，orders 里引用维度名也必须保持小写：
- ✅ `{"metric_time__day": "asc"}`
- ❌ `{"metric_time__DAY": "asc"}`

**⚠️ 财年（FY）维度是例外**：财年口径的维度名是 `metric_time__FY_year` / `metric_time__FY_quarter` / `metric_time__FY_month` / `metric_time__FY_week`（双下划线后接 **FY 大写、粒度小写**，与日历时间的全小写后缀区分）。何时用 FY 见 SKILL.md Step 2；timeConstraint 写法见 §1.5.1。
- ✅ `metric_time__FY_year`、`metric_time__FY_quarter`
- ❌ `metric_time_FY_year`（少一个下划线）、`metric_time__fy_year`（FY 小写）

```json
"dimensions": ["metric_time__month", "dim_A"]
```

**⚠️ 维度兼容性检查**：多指标查询时，dimensions 只能包含**所有指标都支持**的维度（交集）。用 `metric_dimensions(metrics="a,b")` 批量查询；返回的 COMMON dimensions 就是交集。

**⚠️ 目标维度不在该指标的可分析维度里** → 弃用该维度，并在 buildReason 说明缺失；**严禁用相近的无关维度顶替**（那会静默改变统计口径，见 §4.2 症状 15）。若该维度是用户问题的核心，按 SKILL.md Step 4 如实告知不覆盖。

**⚠️ dimensions 里最多一个 `metric_time` 维度**：平台**不支持** dimensions 里同时出现两个 `metric_time` 维度——不论日历粒度（`metric_time__day` / `metric_time__month` / `metric_time__year` …）还是 FY 粒度（`metric_time__FY_*`），只能挑**一个**。要"年 + 月"层级时，直接用**更细的粒度**；它的值已经区分了上层（`metric_time__month` 的值 `2025-03` 已含年份；FY 见 §1.5.1）。
- ❌ `"dimensions": ["metric_time__year", "metric_time__month"]`
- ❌ `"dimensions": ["metric_time__FY_year", "metric_time__FY_month"]`
- ❌ `"dimensions": ["metric_time__FY_quarter", "metric_time__day"]`（**FY 粒度混搭日历粒度同样算两个 metric_time 维度——本错误的最高频变体**；通常出现在字面值 FY timeConstraint 强制 FY 维度入场、同时又想按天展开时——正确写法见 §1.5.1 B 的"点名财期按日历天展开"）
- ✅ `"dimensions": ["metric_time__month"]` / `"dimensions": ["metric_time__FY_month"]`

---

### 1.4 filters 与 resultFilters

| | **filters** | **resultFilters** |
|---|---------|--------------|
| 等价于 | SQL WHERE | SQL HAVING |
| 影响 | 计算过程（分母、排名范围都受影响） | 只筛返回的行 |

**选择规则**：
1. 过滤字段是**时间相关**（metric_time、日期）→ **必须进** `timeConstraint`（⚠️ 绝不放 filters）
2. 过滤字段是**指标值或计算结果** → `resultFilters`
3. 过滤字段是**维度值**且应影响计算 → `filters`
4. 过滤字段是**维度值**但不应影响计算（占比/排名场景只展示某些行，见自检 2）→ `resultFilters`

**filters 语法**：
```
[dim_A]= "value"                    精确匹配
IN([dim_A], "v1", "v2")            包含
NotIn([dim_A], "v1")               排除
contains([dim_A], "x")             模糊
[dim_num]>= 100                    数值比较
['date_dim']>= "2023-08-01"       日期比较
```

**resultFilters 语法**：
```json
"resultFilters": ["[metric_M] > 1000"]
"resultFilters": ["[metric_M__sameperiod__mom__growth] > 0.05"]
"resultFilters": ["[dim_A]= \"value_1\""]
```

---

### 1.5 timeConstraint（选填）— 时间范围

> ⚠️ **财年租户（SKILL.md Step 2 判定）**：下方速查表的年/季/月/周行须按 §1.5.1 转成 FY 写法（`"WEEK"/"MONTH"/"QUARTER"/"YEAR"` → `"FY_*"`，dimensions 同理）；天粒度行与绝对日期保持公历。用户明确要求自然年时例外。**非财年租户**整表按原样使用。

timeConstraint 有**两种截然不同的角色**，构建时必须区分：

| 角色 | 说明 | 形式 |
|------|------|------|
| **角色 A：时间范围过滤** | 限定"查哪段数据" | 一个区间（如近 7 天、上月） |
| **角色 B：period 锚点基准** | 为 period/sameperiod 的相对偏移提供基准点 | 一个具体日期或月份 |

**📋 timeConstraint 速查表**（按用户时间表述直接查表照抄）：

| 用户说 | timeConstraint |
|-------|---------------|
| 昨天 | `"['metric_time__day']= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"DAY\")"` |
| 今天 | `"['metric_time__day']= DateTrunc(NOW(), \"DAY\")"` |
| 上周 | `"DateTrunc(['metric_time'], \"WEEK\") = DATEADD(DateTrunc(NOW(), \"WEEK\"), -1, \"WEEK\")"` |
| 本周 | `"DateTrunc(['metric_time'], \"WEEK\") = DateTrunc(NOW(), \"WEEK\")"` |
| 上月 | `"DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")"` |
| 本月 | `"DateTrunc(['metric_time'], \"MONTH\") = DateTrunc(NOW(), \"MONTH\")"` |
| 上季 | `"DateTrunc(['metric_time'], \"QUARTER\") = DATEADD(DateTrunc(NOW(), \"QUARTER\"), -1, \"QUARTER\")"` |
| 本季 | `"DateTrunc(['metric_time'], \"QUARTER\") = DateTrunc(NOW(), \"QUARTER\")"` |
| 今年 | `"DateTrunc(['metric_time'], \"YEAR\") = DateTrunc(NOW(), \"YEAR\")"` |
| 去年 | `"DateTrunc(['metric_time'], \"YEAR\") = DATEADD(DateTrunc(NOW(), \"YEAR\"), -1, \"YEAR\")"` |
| 近 7 天 | `"DateTrunc(['metric_time'], \"DAY\") >= DATEADD(DateTrunc(NOW(), \"DAY\"), -7, \"DAY\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")"` |
| 近 30 天 | `"DateTrunc(['metric_time'], \"DAY\") >= DATEADD(DateTrunc(NOW(), \"DAY\"), -30, \"DAY\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")"` |
| 近 12 个月 | `"DateTrunc(['metric_time'], \"MONTH\") >= DATEADD(DateTrunc(NOW(), \"MONTH\"), -12, \"MONTH\") AND DateTrunc(['metric_time'], \"MONTH\") < DateTrunc(NOW(), \"MONTH\")"` |
| 2025 年 4 月（具体月份） | `"DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\""` |
| 2025-06-15（具体日期） | `"['metric_time__day']= \"2025-06-15\""` |

> ⚠️ 除最后两行外，表中每行都用 NOW()（见自检 1）。只有用户指定了具体日期/月份才用字面日期。

**⛔ 时间前提**：时间缺失（强制反问）、无年份月份、模糊命名期（"冬季""大促"）的处置全部在 SKILL.md Step 2 / Step 5——**到达本节时，时间口径必须已经确认**，本节只负责把它写成 timeConstraint。

**角色 B（period 锚点）的取值**：当指标或 period 已完整定义了窗口（如带 ytd / L30D 限定的派生指标），timeConstraint 只提供锚点——**锚点必须取自已确认口径所指的那一天**，不是无条件取今天：口径是"截至今天"才锚定今天（`DateTrunc(NOW(), "DAY")`），口径是"截至上月末"就锚定上月末（`SPECIFY_DATE end day of -1 month`），口径是某个具体日期就锚定该日期。把锚点默认成今天等于把窗口改成了另一个时段。

**⚠️ 不许双重偏移**：timeConstraint 已限定某时段（如"上季"）时，metricDefinitions 里的 period 不应再做同方向的额外偏移，否则叠成"上上季"。正确做法：timeConstraint 锚定基准，period 从基准点偏移到目标。

---

### 1.5.1 财年（FY）时间规则

财年边界由指标平台配置，与自然年不对齐。FY 查询的 timeConstraint 按**相对/点名**分两种写法，外加一条**只适用于字面值形式**的硬规则。

**🔒 硬规则（仅限字面值形式）：用字面值过滤时，FY 维度必须进 `dimensions`**——当 timeConstraint 用**字面值形式** `[metric_time__FY_*]= "FY..."` 过滤时，`dimensions` 必须包含一个 FY 财年日期维度（`metric_time__FY_year` / `metric_time__FY_quarter` / `metric_time__FY_month` / `metric_time__FY_week`，维度名 = 双下划线 + FY 大写 + 粒度小写）。**空 dimensions + 字面值 FY 条件 = 平台不支持**。
- ❌ `{ "metrics": ["metric_A"], "timeConstraint": "[metric_time__FY_year]= \"FY2026\"" }`（字面值 + 空 dimensions）
- ✅ `{ "metrics": ["metric_A"], "dimensions": ["metric_time__FY_year"], "timeConstraint": "[metric_time__FY_year]= \"FY2026\"" }`
- **⚠️ DateTrunc 比较形式不受此约束；dimensions 可为空**：`DateTrunc(['metric_time'], "FY_YEAR") = ...`（A 节的相对写法、§1.5.1 C 的财年至今窗口都属于这类）。如 `{ "metrics": ["metric_A"], "dimensions": [], "timeConstraint": "DateTrunc(['metric_time'], \"FY_YEAR\") = DateTrunc(NOW(), \"FY_YEAR\") AND ['metric_time__day'] < DateTrunc(NOW(), \"DAY\")" }`——财年至今，空 dimensions 正常运行。
- **🚫 这条硬规则永远不是往 dimensions 加第二个 metric_time 维度的理由**：想要点名财期**按日历天展开**（或任何没有 FY 维度名的粒度）时，字面值形式是死路——既满足这条硬规则又保留 `metric_time__day` 会产出 `["metric_time__FY_quarter", "metric_time__day"]`，违反 §1.3（最多一个 metric_time 维度），平台直接拒绝。**放弃字面值形式**，改用 DateTrunc 偏移写法——见 B 节"点名财期按日历天展开"。

#### 0. 当前财期坐标 & 判断"是否已结束"（同期对齐的前提）

**当前财期坐标（财年 / 财季 / 财月 / 财周）直接取系统上下文的注入段**（SKILL.md Step 2 已规定）——注入段给的是平台真实标签，无需任何换算，**不要为此发查询**。财年日历由平台按租户配置（模板、周起始、年末规则各不相同），边界与自然年不对齐，所以从公历日期硬算"现在是第几财月/财周"是被禁止的。

**仅在两种情况下才回退探测**：注入段**缺少所需粒度**（如只给了年/季/月而本次需要财周），或注入段声明 `unavailable` / `lookup failed`。探测写法：

```json
{
  "metrics": ["<手头任一指标>"],
  "dimensions": ["metric_time__FY_week"],
  "timeConstraint": "['metric_time__day']= DateTrunc(NOW(), \"DAY\")"
}
// 返回维度值如 "FY2026-P05-W02" → 当前财周 = FY2026 第 5 财月第 2 周
```

注入段与探测都拿不到时 → `ask_human` 确认，**严禁猜测标签**。

**判断点名财期 X 是否已结束**（决定同期写法）：拿当前财期坐标与 X 直接比较，不需要任何日期换算。

| X 相对当前财期 | 已结束？ | 同期写法 |
|--------------|---------|-----------|
| **X == 当前期**（如当前 FY2026、用户问 FY26；当前 Q2、问 FY26 Q2） | **未结束** | §1.5.1 C 的对齐写法（grain_to_date / DateTrunc 窗口到今天） |
| **X 早于当前期**（如当前 Q2、问 FY26 Q1；或已结束的 FY25） | 已结束 | 点名字面值 + 完整 `__sameperiod__FY_yoy__` 后缀（完整比完整） |
| **X 晚于当前期** | 未来，无数据 | 告诉用户该期还没开始 |

- **相对期（本财年/季/月/周）**：定义上就是当前期 → 直接用对齐写法。
- 裸的 `P3`、"近 N 个财月"等需要当前财年标签 / 财月号的，同样取注入段坐标。
- 无论用哪种写法，对比基准都写进 **SKILL.md Step 8 的口径说明块**，不要散在正文：`统计时间范围为 {当前期标签} 至今（{起始日期} 至 {今天}）vs {上期标签} 同跨度`。

#### A. 相对财期（"本财年"、"上财季"、"近 N 个财月"…）→ 用 DateTrunc(NOW()) 推导

| 用户说 | timeConstraint |
|-------|---------------|
| 本财年 | `"DateTrunc(['metric_time'], \"FY_YEAR\") = DateTrunc(NOW(), \"FY_YEAR\")"` |
| 上财季 | `"DateTrunc(['metric_time'], \"FY_QUARTER\") = DATEADD(DateTrunc(NOW(), \"FY_QUARTER\"), -1, \"FY_QUARTER\")"` |

其余（上财年 / 本财季 / 本财月 / 上财月 / 本财周 / 上财周）按下面的规律替换粒度即可。

**规律**：把日历粒度 `"YEAR" / "QUARTER" / "MONTH" / "WEEK"` 整体换成 `"FY_YEAR" / "FY_QUARTER" / "FY_MONTH" / "FY_WEEK"`；`DateTrunc` / `DATEADD` / `NOW()` 的用法完全不变。

**本节全部是 DateTrunc 比较形式 → 豁免字面值硬规则，`dimensions` 可以为空**。只有当你**需要按财期分组展开**时才放 FY 维度（如本财年按各财季看 → `dimensions: ["metric_time__FY_quarter"]`）；要单一聚合值就留空。

#### B. 点名财期（"FY26 Q1"、"FY2025"、"FY2025 第 3 财月"…）→ 用日历格式字面值匹配

点名期是**绝对时间点**；NOW() 偏移推不出具体点名财季（财年与自然年不对齐，"FY26 Q1" ≠ "上一个财季"）→ 用日历格式字面值 `[维度名]= "字面值"` 过滤。

**📅 日历格式字面值**（月/季/周序号补零到两位；API 对前导零宽松，`FY2025-P03` 和 `FY2025-P3` 都可以）：

| 口径 | dimensions 维度名 | 字面值格式 | 示例 | 含义 |
|------|------------------|-----------|------|------|
| 财年 | `metric_time__FY_year` | `FY{yyyy}` | `FY2025` | 2025 财年 |
| 财季 | `metric_time__FY_quarter` | `FY{yyyy}-Q{qoy}` | `FY2025-Q01` | 2025 财年第 1 财季 |
| 财月 | `metric_time__FY_month` | `FY{yyyy}-P{moy}` | `FY2025-P03` | 2025 财年第 3 财月 |
| 财周 | `metric_time__FY_week` | `FY{yyyy}-P{moy}-W{wom}` | `FY2025-P02-W01` | 2025 财年第 2 财月第 1 周 |

- `{yyyy}` = 4 位财年。用户说 "FY26" 还是 "FY2026" 都指 2026 财年 → **补全为 `FY2026`**，不要写 `FY26`
- `{qoy}` 第几财季 / `{moy}` 第几财月 / `{wom}` 财月内第几周

**⚠️ "按财年、拆到财月" = 单个维度 `metric_time__FY_month`**——它的值自带 FY 前缀（`FY2025-P03`，补零后字符串升序即时间序），且 dimensions 最多一个 metric_time 维度（§1.3）；绝不额外加 `metric_time__FY_year`，orders 也只引用 `metric_time__FY_month`。

**⚠️ timeConstraint 过滤粒度可以粗于 dimensions 展开粒度**（timeConstraint 锁定 FY 范围、dimensions 按更细粒度展开；高频用法）：

| 用户意图 | dimensions | timeConstraint |
|---------|-----------|---------------|
| FY2026 全年（单值） | `["metric_time__FY_year"]` | `"[metric_time__FY_year]= \"FY2026\""` |
| FY2026 全年，**按各财季展开** | `["metric_time__FY_quarter"]` | `"[metric_time__FY_year]= \"FY2026\""` |
| FY26 Q1（仅该财季） | `["metric_time__FY_quarter"]` | `"[metric_time__FY_quarter]= \"FY2026-Q01\""` |
| FY2025 第 3 财月 | `["metric_time__FY_month"]` | `"[metric_time__FY_month]= \"FY2025-P03\""` |
| FY26 Q1~Q2（连续区间） | `["metric_time__FY_quarter"]` | `"[metric_time__FY_quarter]>= \"FY2026-Q01\" AND [metric_time__FY_quarter]<= \"FY2026-Q02\""` |
| FY25 第 1~3 财月（枚举） | `["metric_time__FY_month"]` | `"IN([metric_time__FY_month], \"FY2025-P01\", \"FY2025-P02\", \"FY2025-P03\")"` |

**占比/排名**：分组维度和范围维度都用 FY 维度名（如 `metric_A__proportion__metric_time__FY_quarter` = 每财季内占比），orders 引用同一 FY 维度名。FY 维度仍必须出现在 `dimensions`。

**⚠️ 点名财期按日历天展开（或任何没有 FY 维度名的粒度）**

陷阱在于：§1.3 最多允许一个 metric_time 维度，而字面值硬规则（§1.5.1 开头）强制 FY 维度进 dimensions。各执行一半就会产出非法的 `"dimensions": ["metric_time__FY_quarter", "metric_time__day"]`。**绝不组合这两个维度——改为放弃字面值形式**：

1. **取当前财期坐标**（§1.5.1 #0）：来自系统上下文注入段，不发查询。
2. **把点名期换算成 NOW() 偏移**：数当前期与目标期之间隔多少个完整财期——纯粹基于注入段标签做**期数算术**，不做公历边界数学。如目标 = 当前财年 Q1、当前 = Q2 → 偏移 `-1`；目标在上一财年 → 跨年界计数（每财年 4 财季 / 12 财月）。
3. **用 DateTrunc 比较形式**（豁免于字面值硬规则，dimensions 可自由放 `metric_time__day`）：

```json
{
  "metrics": ["metric_A"],
  "dimensions": ["metric_time__day"],
  "timeConstraint": "DateTrunc(['metric_time'], \"FY_QUARTER\") = DATEADD(DateTrunc(NOW(), \"FY_QUARTER\"), -1, \"FY_QUARTER\")",
  "orders": [{"metric_time__day": "asc"}]
}
```

- FY_year / FY_month / FY_week 目标同理：换粒度和偏移数；目标**就是**当前期时去掉 DATEADD（`DateTrunc(['metric_time'], "FY_QUARTER") = DateTrunc(NOW(), "FY_QUARTER")`）。
- 只有请求的展开粒度**有** FY 维度名（年/季/月/周）时，才可以按上表继续用字面值形式配那个单一 FY 维度。

#### C. 财年同期对比（FY 自定义日历偏移）

**FY 同期偏移粒度**（用法与日历偏移 dod/wow/mom/qoq/yoy 相同，见 §1.1.1）：

| 用户说 | FY 偏移粒度 |
|-------|-----------|
| 财年同比 | `FY_yoy` |
| 财季环比 | `FY_qoq` |
| 财月环比 | `FY_mom` |
| 财周环比 | `FY_wow` |

- 表达式：`{指标}__sameperiod__FY_yoy__{方法}`（方法同 §1.1.1：`growth` / `value` / `growthvalue` 等）
- 支持 `{N}_` 前缀：`{N}_FY_yoy`（如 `-2_FY_yoy` = 两个财年前同期）
- 通用格式 `{N}_{自定义日历名}_{偏移粒度}`；自定义日历名通常为 `FY`（以元数据返回的财年维度名为准）

**⚠️ 当前财期未完结时的财期同比（自检 8 的 FY 版，极易失真）**

**触发条件 = 被查财期是"还没结束的当前期"**，与用户**怎么称呼它无关**：
- **相对说法**："本财年/季/月/周 + 同环比"。
- **点名当前期（同样命中，最易漏判）**：用户直接点名当前未完结的财年（如现在 FY26 进行中，用户问 **"FY26 … 同比"**）。这本质就是"本财年未完结 + 同比"；**绝不能**当普通点名期处理成 `[metric_time__FY_year]= "FY2026"` + 完整 `__sameperiod__FY_yoy__growth`——那是拿未完结的 FY26 比**完整的** FY25，严重失真。

**正确写法 = 两期都对齐到相同的"财期期初 ~ 今天"跨度**（与自检 8 呼应）。**两种写法都可行；按是否合并成单查询选择**——关键是避开第三条错误路径"点名字面值 + 完整后缀"。

**写法 1（合并单查询：period + indirections）**——一次查询同时输出当期值和同比增速：
- `period: "grain_to_date 0 FY_year of 0 day"`（FY 粒度 ∈ {`FY_year`、`FY_quarter`、`FY_month`、`FY_week`}）——天然捕获**当前财年至今**；**不需要也不应该**写 `FY2026` 字面值。
- `indirections: ["sameperiod__FY_yoy__growth"]`。
- timeConstraint 锚定今天（日历日：`['metric_time__day']= DateTrunc(NOW(), "DAY")`，**单个日期锚点，不是区间**）。
- **⚠️ `dimensions` 绝不能包含 `metric_time__FY_year`（高频错误）**：两期的值来自**上面两个 metricDefinitions**（当期 + `sameperiod`），不是按 FY 分组得来的，所以往 `dimensions` 放 FY 维度是错的。需要时间维度就用 **`metric_time__day`**（匹配 period 的 `of 0 day` 锚点粒度）；要单一聚合值就**留空**、或只放业务维度（如渠道）。
  - ❌ `"dimensions": ["metric_time__FY_year"]`
  - ✅ `"dimensions": ["metric_time__day"]`（按日展开）或 `"dimensions": []`（聚合）或 `"dimensions": ["dim_A"]`（按业务维度）
- 完整示例见 §2.8。

**写法 2（拆两条查询：DateTrunc 窗口）**——分别查当期和上财年同期，Agent 自己算 `(当期 − 上期) / 上期`。纯 `timeConstraint`，FY 条件用 DateTrunc 比较形式，**dimensions 可为空**（不受字面值硬规则约束）：

| 本条查询取什么 | timeConstraint |
|----------|---------------|
| 当期（财年至今，期初 → 今天） | `"DateTrunc(['metric_time'], \"FY_YEAR\") = DateTrunc(NOW(), \"FY_YEAR\") AND ['metric_time__day'] <= DateTrunc(NOW(), \"DAY\")"` |
| 上财年同期（上一 FY，同口径跨度） | `"DateTrunc(['metric_time'], \"FY_YEAR\") = DATEADD(DateTrunc(NOW(), \"FY_YEAR\"), -1, \"FY_YEAR\") AND ['metric_time__day'] <= DATEADD(DateTrunc(NOW(), \"DAY\"), -1, \"FY_YEAR\")"` |

- 上财年那条的天上界 = **"今天整体回移一个财年"**（`DATEADD(今天, -1, "FY_YEAR")`），保持两个跨度严格对齐。
- 本财季/月/周同理：`FY_YEAR` 换成 `FY_QUARTER` / `FY_MONTH` / `FY_WEEK`，回移量 `-1, "FY_YEAR"` 相应替换。
- 要按维度展开（"按渠道"）→ 两条查询的 `dimensions` 都放该业务维度。完整示例见 §2.8。

**怎么判断"未完结"** → 绝不从公历日期硬算（财年边界不规则）；用 §1.5.1.0：当前财期坐标取自系统上下文注入段，与 X 直接比较。相对期定义上就是当前期。无论用哪种对齐，对比基准都按 **SKILL.md Step 8 的口径说明格式**写明（`统计时间范围为 {当前期标签} 至今（{起始日期} 至 {今天}）vs {上期标签} 同跨度`）；坐标拿不到或基准仍不确定 → `ask_human`。

---

### 1.6 其他参数

**orders** —— 排序列必须在 metrics 或 dimensions 里；按**排名列**排序时用 `asc`（名次越小越靠前）：
```json
"orders": [{"metric_time__day": "asc"}, {"metric_M": "desc"}]
```

---

---

## 2. 完整示例

> 基础查询 / 单个快速计算后缀不需要示例——按 §1.1 直接构建。下面只覆盖易错的复合模式。

### 2.1 跨期对比 — period + timeConstraint

某年 5 月 vs 2 月各 dim_A 的 metric_A 增长（⚠️ 这里用字面日期，因为用户指定了具体月份）：
```json
{
    "metrics": ["may_val", "feb_val", "growth_rate"],
    "metricDefinitions": {
        "may_val": {
            "refMetric": "metric_A",
            "period": "relative_date 0 month of 0 month"
        },
        "feb_val": {
            "refMetric": "metric_A",
            "period": "relative_date -3 month of 0 month"
        },
        "growth_rate": { "expr": "([may_val]-[feb_val])/[feb_val]" }
    },
    "dimensions": ["dim_A"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = \"2025-05-01\"",
    "orders": [{"growth_rate": "desc"}]
}
```

### 2.2 日均 — preAggs

指定日期近 11 天的日均 metric_A（⚠️ 这里用字面日期，因为锚定了具体日期）：
```json
{
    "metrics": ["daily_avg"],
    "metricDefinitions": {
        "daily_avg": {
            "refMetric": "metric_A",
            "period": "to_date -10 day of 0 day",
            "preAggs": [{"granularity": "DAY", "calculateType": "AVG"}]
        }
    },
    "timeConstraint": "['metric_time__day']= \"2024-11-11\""
}
```

### 2.3 MetricMatches — 跨指标筛维度值

上月 metric_A ≥ 某阈值的 dim_X 数量（用 metric_B 计数）：
```json
{
    "metrics": ["filtered_cnt"],
    "metricDefinitions": {
        "filtered_cnt": {
            "refMetric": "metric_B",
            "filters": ["MetricMatches([dim_X], [metric_A] >= 10000)"]
        }
    },
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")"
}
```

### 2.4 时间限定 + 同环比 — period + indirections（推荐）

年初至今的 metric_A 及其同比（无 preAggs 时的推荐写法）：
```json
{
    "metrics": ["ytd_val", "ytd_val_ly", "ytd_yoy_growth"],
    "metricDefinitions": {
        "ytd_val": {
            "refMetric": "metric_A",
            "period": "grain_to_date 0 year of 0 day"
        },
        "ytd_val_ly": {
            "refMetric": "metric_A",
            "period": "grain_to_date 0 year of 0 day",
            "indirections": ["sameperiod__yoy__value"]
        },
        "ytd_yoy_growth": {
            "refMetric": "metric_A",
            "period": "grain_to_date 0 year of 0 day",
            "indirections": ["sameperiod__yoy__growth"]
        }
    },
    "timeConstraint": "['metric_time__day']= DateTrunc(NOW(), \"DAY\")"
}
```

### 2.5 全局均值对比 — multi_level_agg + specifyDimension

指定季度各 dim_A 的 metric_A 与全局平均的对比（⚠️ 字面日期：用户指定了具体季度）：
```json
{
    "metrics": ["metric_A", "global_avg"],
    "metricDefinitions": {
        "global_avg": {
            "refMetric": "metric_A",
            "indirections": ["multi_level_agg__avg,dim_A"],
            "specifyDimension": { "type": "EXCLUDE", "dimensions": "dim_A" }
        }
    },
    "dimensions": ["dim_A"],
    "timeConstraint": "DateTrunc(['metric_time'], \"QUARTER\") = \"2025-01-01\""
}
```
注：不加 specifyDimension 时，每个 dim_A 组内只含自己，均值恒等于自身。

### 2.6 环比增速 + 排名 — 多步拆分（⚠️ 自检 4 高频违反场景）

上月各 dim_A 内按 metric_A 月环比增速排前 3 的 dim_D（先算环比、再排名，**禁止链式叠加**）：
```json
{
    "metrics": ["metric_A", "mom_growth", "mom_growth__rankDense__desc__dim_A"],
    "metricDefinitions": {
        "mom_growth": {
            "refMetric": "metric_A",
            "indirections": ["sameperiod__mom__growth"]
        }
    },
    "dimensions": ["dim_A", "dim_D"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = DATEADD(DateTrunc(NOW(), \"MONTH\"), -1, \"MONTH\")",
    "resultFilters": ["[mom_growth__rankDense__desc__dim_A] <= 3"],
    "orders": [{"dim_A": "asc"}, {"mom_growth__rankDense__desc__dim_A": "asc"}]
}
```
**关键**：`metric_A__sameperiod__mom__growth__rankDense__desc__dim_A` 是链式叠加（违反自检 4）。正确做法是先定义环比临时指标 `mom_growth`，再对它应用排名快速计算。

### 2.7 占比 + 同比 + 排名 — resultFilters 展示过滤（⚠️ 自检 2 高频违反场景）

某具体月份 dim_A 为 value_1 的 metric_A、同比、全局占比和全局排名（⚠️ 字面日期：用户指定了具体月份）：

✅ 正确：
```json
{
    "metrics": [
        "metric_A",
        "metric_A__sameperiod__yoy__growth",
        "metric_A__proportion__",
        "metric_A__rankDense__desc"
    ],
    "dimensions": ["dim_A"],
    "timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\"",
    "resultFilters": ["[dim_A]= \"value_1\""]
}
```

❌ 错误（分母被缩小 → 占比恒 100%，排名恒 1）：
```json
{
    "filters": ["[dim_A]= \"value_1\""],
    "metrics": ["metric_A", "metric_A__proportion__", "metric_A__rankDense__desc"],
    "dimensions": ["dim_A"]
}
```
**关键**：占比和排名需要全部维度值参与计算；`value_1` 的过滤必须进 `resultFilters`（不是 `filters`）。用 `filters` 会让分母/排名范围只剩 value_1 自己。


### 2.8 财年时间口径（FY）

**模式**：timeConstraint 按相对/点名选写法（见 §1.5.1）；**只有字面值形式**要求 FY 维度进 `dimensions`，DateTrunc 形式豁免（需要分组展开时才放）。

**点名期** —— 点名财年财季的 metric_A 与 metric_B（如 "FY26 Q1 的 A vs B"，FY26 补全为 FY2026）：
```json
{
    "metrics": ["metric_A", "metric_B"],
    "dimensions": ["metric_time__FY_quarter"],
    "timeConstraint": "[metric_time__FY_quarter]= \"FY2026-Q01\""
}
```

**点名全年、按各财季展开**（timeConstraint 锁 FY_year，dimensions 按 FY_quarter 拆）：
```json
{
    "metrics": ["metric_A"],
    "dimensions": ["metric_time__FY_quarter"],
    "timeConstraint": "[metric_time__FY_year]= \"FY2026\"",
    "orders": [{"metric_time__FY_quarter": "asc"}]
}
```

**相对期** —— 本财年各财季的 metric_A（DateTrunc(NOW()) 推导当前财年）：
```json
{
    "metrics": ["metric_A"],
    "dimensions": ["metric_time__FY_quarter"],
    "timeConstraint": "DateTrunc(['metric_time'], \"FY_YEAR\") = DateTrunc(NOW(), \"FY_YEAR\")",
    "orders": [{"metric_time__FY_quarter": "asc"}]
}
```

**财年至今 + 财年同比（本财年未完结——自检 8 的 FY 版）** —— 两期对齐到"财期期初 ~ 今天"再比。两种写法都可行（见 §1.5.1 C）：

**写法 1（合并单查询：period + indirections）**——一次查询输出当期值 + 同比增速：
```json
{
    "metrics": ["fy_ytd_val", "fy_ytd_yoy_growth"],
    "metricDefinitions": {
        "fy_ytd_val": {
            "refMetric": "metric_A",
            "period": "grain_to_date 0 FY_year of 0 day"
        },
        "fy_ytd_yoy_growth": {
            "refMetric": "metric_A",
            "period": "grain_to_date 0 FY_year of 0 day",
            "indirections": ["sameperiod__FY_yoy__growth"]
        }
    },
    "timeConstraint": "['metric_time__day']= DateTrunc(NOW(), \"DAY\")"
}
```
（本财季/月/周同理：`FY_year` 换 `FY_quarter` / `FY_month` / `FY_week`，偏移换 `FY_qoq` / `FY_mom` / `FY_wow`。结构与日历时间的 §2.4 完全同构。）

**写法 2（拆两条查询：DateTrunc 窗口）**——确切的 timeConstraint 对照见 §1.5.1 C 的表；Agent 自己算 `(当期 − 上期) / 上期`。"按渠道"就把业务维度加进两条查询。

**点名当前期（FY26 进行中时问 "FY26 … 同比"）** —— 同样用对齐写法：`grain_to_date 0 FY_year` 天然捕获当前 FY，所以**绝不**写 `FY2026` 字面值 + 完整 `__sameperiod__FY_yoy__` 后缀；需要分组就把业务维度（如渠道）放进 `dimensions`，并按 SKILL.md Step 8 的口径说明格式写明对比基准。

---

---

## 3. 输出前自检

生成 JSON 后**逐条**核对。以下每一条违反都会导致平台报错或口径失真，**没有轻重之分**；任一不合规 → 回对应小节修正后再提交，不许侥幸。

**1. 相对时间必须用 NOW()；严禁硬编码日期（timeConstraint 与 period 锚点同样适用）**
"上月"、"今年"、"近 N 天"、"去年"、"昨天"等相对时间 → 用 `NOW()` 推导；不要直接写 `"2026-03-05"`。
- ✅ `DATEADD(DateTrunc(NOW(), "MONTH"), -1, "MONTH")` — 上月月初
- ✅ `DateTrunc(NOW(), "DAY")` — 今天（常用于 period 锚点）
- ✅ `DATEADD(DateTrunc(NOW(), "DAY"), -1, "DAY")` — 昨天
- ❌ 任何硬编码的当前/近期日期，如 `"2026-03-05"`、`DATE('2025-06-01')`
- **例外**：用户明确说了"2025 年 4 月"这类具体时间点 → 用字面值 `"2025-04-01"`；**点名的财期**（"FY26 Q1"、"FY2025"）同样用日历格式字面值（`[metric_time__FY_quarter]= "FY2026-Q01"`），**而不是** NOW() 偏移。相对财期（本/上财年）仍用 DateTrunc(NOW())。FY 查询还有一条硬规则（**只有**字面值形式要求 FY 维度进 dimensions；DateTrunc 比较形式 dimensions 可为空），见 §1.5.1
- **不许 `DATE()` 包裹**：API 不支持 `DATE('...')`；直接写 `"..."` 字符串

**2. 占比/排名 + filters = 分母/范围被缩小 → 结果恒为 100% / 恒为 1**
"某值在整体中的占比/排名"：`dimensions` 必须包含该维度让所有值参与计算；目标行用 **resultFilters** 做展示过滤，绝不用 filters。
- ❌ `"filters": ["[dim_A]= \"value_1\""]` → 占比恒 100%，排名恒 1
- ✅ `"resultFilters": ["[dim_A]= \"value_1\""]`（细节 §1.1.2/§1.4，示例 §2.7）

**3. 同环比后缀映射（"同比/环比"的措辞解读在 SKILL.md Step 2；此处只管后缀选择）**
- 无限定词 / "同比" → `yoy`
- "月同比" → `mom`（与上月同期比）
- "周同比" → `wow`（与上周同期比）
- "季同比" → `qoq`（与上季同期比）
- ⚠️ "同比"单独出现、无粒度前缀时，**一律**映射为 yoy，绝不映射为 mom/qoq/wow

**4. 一个指标只能挂一个快速计算；禁止链式叠加**
需要多步时（如先算环比再排名）→ 用 metricDefinitions 拆步；完整示例见 §2.6。
- ❌ `metric_A__sameperiod__mom__growth__rankDense__desc__dim_A`（链式：同环比后缀 + 排名后缀）
- ✅ 先用 metricDefinitions 定义临时指标 `mom_growth`（indirections），再对它应用 `__rankDense__desc__dim_A`

**5. MetricMatches 只能用在 metricDefinitions 的 filters 里；顶层 filters 禁止**
MetricMatches 是"按指标值筛维度值"的高级特性；**必须**包裹在临时指标定义（metricDefinitions）的 filters 里。
- ✅ `"metricDefinitions": { "temp": { "refMetric": "metric_C", "filters": ["MetricMatches([dim_C], [metric_A] >= 10000)"] } }`
- ❌ `"filters": ["MetricMatches([dim_C], [metric_A] >= 10000)"]`（顶层 filters 不支持 MetricMatches）

**6. 必须遵守预定义派生指标的粒度限制**
metric_search 返回的部分派生指标会在"可分析维度"里注明 metric_time 支持的粒度（如"仅支持天粒度"）。
使用前必须校验：timeConstraint 粒度 ∈ 该指标注明的粒度列表。不兼容时**不要**硬用；改用原子指标 + 快速计算后缀（粒度自适应）。
- ❌ 月粒度 timeConstraint + 某派生指标（若该指标注明"仅支持天粒度"）
- ✅ 月粒度 timeConstraint + 原子指标 + 快速计算后缀，如 `metric_A__sameperiod__yoy__growth`
- ⚠️ **替代仅限语义等价**：只有"原子指标 + 后缀"与该派生指标的业务口径一致（同一基础度量、同一限定）时才可替换；派生指标带特殊口径（如不含税、特定人群）而替代表达不出 → 不是替换问题，按 SKILL.md Step 4/5 处理（如实说明或反问），严禁静默换口径

**7. "时间变化趋势"中占比/排名的范围维度必须是对应的 metric_time 粒度**
查询涉及"XX 在 YY 内排名/占比的**时间变化趋势**"时，范围维度必须是对应的 `metric_time__{grain}`（每个时间段内独立计算排名/占比），**不能**是实体维度、也不能留空。
- ✅ `metric_A__proportion__metric_time__month`（每月内各维度值的占比）
- ✅ `metric_A__rank__desc__metric_time__week`（每周内各维度值的排名）
- ❌ `metric_A__proportion__`（全局占比，无时间分组 → 跨期混算）
- ❌ `metric_A__proportion__dim_A`（每个维度值组内占比 → 恒 100%）
- **规律**：月度趋势用 `metric_time__month`，周度趋势用 `metric_time__week`，季度趋势用 `metric_time__quarter`，以此类推

**8. 未完结当期的同环比必须对齐跨度（原则见 SKILL.md Step 2；此处是 MQL 写法）**
"本周/月/季/年（或当前财期，不论怎么称呼——本财年 / FY26 / 本财季 / P6）+ 同环比"配整期 timeConstraint，是拿**未完结当期比完整上期** → 严重失真。两期都对齐到"期初 ~ 今天"：metricDefinitions `period: "grain_to_date 0 <grain> of 0 day"` + `indirections: ["sameperiod__yoy__growth"]`，timeConstraint 锚定今天。FY 粒度：`<grain>` 换成 `FY_year`/`FY_quarter`/`FY_month`，偏移换成 `FY_yoy` 等——细节 §1.5.1 C，示例 §2.4（日历）/ §2.8（FY）。
- **例外**：已完结的过去期（"上月"、已结束的 FY25）→ 简单 `__sameperiod__` 后缀即可。
- **形态自检（最易漏）**：`__sameperiod__FY_*__` 后缀 + **当前**财期的 FY **字面值** timeConstraint = 正在犯这个错 → 改 §1.5.1 C 对齐写法；拿不准该财期是否已结束 → 按 §1.5.1.0 用注入段坐标比较。只有**已结束**的过去财期才可以"字面值 + 完整后缀"。

**9. metricDefinitions 里的每个 key 都必须同时出现在 metrics 数组（包括辅助指标）**
定义了就必须注册。自检：数一遍 metricDefinitions 的 key → 确认每个都在 metrics 里。
**⚠️ 特别注意"辅助指标"**：即使某个临时指标只在 `expr` 里充当中间计算变量（如被 `"ratio": { "expr": "[val]/[total]" }` 引用的 `"total": { "refMetric": "metric_A", "specifyDimension": ... }`），该辅助指标**也必须**出现在 metrics 数组。API 不会自动推断依赖——metricDefinitions 里的每个 key，无论最终输出还是中间计算，都必须显式注册进 metrics。
- ❌ `"metrics": ["ratio"]` + `"metricDefinitions": { "total": {...}, "ratio": { "expr": "[val]/[total]" } }`（`total` 未注册）
- ✅ `"metrics": ["total", "ratio"]` + `"metricDefinitions": { "total": {...}, "ratio": { "expr": "[val]/[total]" } }`

**10. JSON 本身合法** —— 字符串值内部的双引号必须转义成 `\"`（如 `"timeConstraint": "DateTrunc(['metric_time'], \"MONTH\") = \"2025-04-01\""`）。MQL 表达式几乎都含嵌套引号，这是最高频的低级错误。

**11. 维度名大小写正确** —— 日历粒度后缀**全小写**（`metric_time__day`，不是 `__DAY`）；FY 维度是**双下划线 + FY 大写 + 粒度小写**（`metric_time__FY_year`）。`orders` 里引用维度名时同样保持一致（§1.3）。

**12. `dimensions` 里至多一个 `metric_time` 维度** —— 日历粒度与 FY 粒度混放**同样算两个**（`["metric_time__FY_quarter", "metric_time__day"]` 会被平台拒绝，是本错误最高频的变体）。要"年+月"层级只保留更细的那个，它的值已含上层（§1.3）。

**13. 用 FY 字面值就必须配 FY 维度** —— timeConstraint 写成 `[metric_time__FY_*]= "FY..."` 时，`dimensions` 必须含一个 FY 维度；`DateTrunc(['metric_time'], "FY_*")` 比较形式豁免、dimensions 可为空。想按日历天展开点名财期 → 放弃字面值形式改 DateTrunc 偏移（§1.5.1）。

**14. period 的 `of` 锚点粒度不能比 timeConstraint 更细** —— timeConstraint 锚到月，`of` 只能用 month/quarter/year，**不能**用 day/week（§1.2.1）。

**15. preAggs 聚合粒度不能与 `dimensions` 的时间粒度相同** —— preAggs 按 DAY 求 AVG 时，外层 dimensions 不要再放 `metric_time__day`，否则等于没聚合、日均恒等于原值（§1.2.2 / §4.2 症状 4）。

**16. timeConstraint 与 period 不做同方向重复偏移** —— timeConstraint 已限定"上季"时，period 再 `-1` 会叠成"上上季"。正确分工：timeConstraint 锚基准，period 从基准点偏移到目标（§1.5 / §4.2 症状 3）。

**17. 多指标时 `dimensions` 只能取交集** —— 用 `metric_dimensions(metrics="a,b")` 返回的 **COMMON dimensions**；任一指标不支持的维度都不能进（§1.3 / §4.2 症状 16）。

**18. 过滤值逐字等于工具返回值** —— 大小写/空格/标点完全一致；样例列表可能被截断，样例里没有的值先 `metric_dimension_resolve` 反查，不要凭印象拼（§4.2 症状 7）。

**19. 多步查询的每一步都已完成** —— 如"某维度 Top 3 的指标总量" = 先查排名圈定子集 → 再对子集聚合 → 综合作答。**只做第一步就回答等于答错**。

---

## 4. 出错与异常结果处理

### 4.1 有明确报错

**读错误信息驱动**：API 报错通常直接指出问题（如 `Metric 'X' not found`、`timeConstraint must be a string`）→ 按错误信息修。严禁不读报错就凭猜改 JSON。

### 4.2 无报错、但结果异常（静默错数）

查询跑通了但结果可疑时按下表排查。

> ⛔ **可为与不可为的界线**：本表的触发条件必须是**你能机械核对的事实**——结果的形态（行数/列数）、返回的时间标签、与工具返回值的字面比对、查询 JSON 自身的结构。
> **数值本身"合不合理"不在你的判断范围内**：业务真实下滑与口径失真在数字上无法区分。所以顺序是——先按下表核对**结构性原因**；结构全部正确而数值仍被质疑 → **如实说明当前口径并请用户确认，绝不自行"修正"数据**。

| # | 你能核对到的事实 | 原因 | 修复 |
|---|---|---|---|
| 1 | 每行占比都是 100%，或每行排名都是 1 | filters 把分母/排名范围缩到只剩目标行；或范围维度覆盖了全部非日期维度 | 目标行改用 resultFilters 展示过滤；全局占比用 `proportion__`（自检 2 / §1.1.2） |
| 2 | 查询含"当期 + 同期对比"，且当期是**尚未结束**的期间（对照注入段的当前财期坐标） | 未完结当期与完整上期跨度不等长 | 两期对齐到"期初 ~ 今天"（自检 8 / §1.5.1 C）。⚠️ **增速为负本身不是判据**——只有"当期未结束"这个结构事实才是 |
| 3 | 返回的时间标签与你意图的时段差一期 | timeConstraint 与 period 同方向重复偏移 | timeConstraint 锚基准，period 做唯一偏移（自检 16） |
| 4 | "日均"列的值等于总量列 | preAggs 聚合粒度与 dimensions 的时间粒度相同 | dimensions 去掉该时间粒度（自检 15 / §1.2.2） |
| 5 | 要"日均"却返回按天的多行明细 | 用 `metric_time__day` 维度当日均实现 | 改 metricDefinitions + period + preAggs（§1.2.2） |
| 6 | 所选指标的名称/描述含"累计 / 至今 / YTD / MTD"，却被用于按期趋势 | 累计口径指标天然单调不回落 | 换非累计的原始指标 + 时间粒度维度 |
| 7 | 返回 0 行 | ① 过滤值与工具返回值不是逐字一致；② 时间范围早于数据覆盖起点 | 先逐字核对过滤值（自检 18），再用粗粒度查询探测覆盖起点（SKILL.md「字典盲区」）；**两者都正确 → "无数据"就是正确答案**，如实回答，不要改条件重查（SKILL.md Step 4） |
| 8 | 用户要的是单个总量，结果却是多行 | 加了不该加的 dimensions | dimensions 留空；只有"每天/每日/按天"才放 `metric_time__day` |
| 9 | "近 N 期"返回的最后一期就是当前未结束的期间 | 只写了下界，缺上界 | 补上界：`... AND DateTrunc(['metric_time'], "X") < DateTrunc(NOW(), "X")` |
| 10 | 排序用的指标不是用户点名的那个 | 自选了排序指标 | 改用用户确认过的指标；用户没点名 → 按 SKILL.md Step 5 反问，**不要自选** |
| 11 | 返回的期间边界落在自然年/季的分界上 | 财期写成了日历粒度（`metric_time__year` / `"YEAR"`） | 换 `metric_time__FY_*` + FY 写法（§1.5.1） |
| 12 | 返回的财期标签与用户点名的财期不一致 | 用 NOW() 偏移去推导点名财期 | 点名期用日历格式字面值（§1.5.1 B）；相对期才用 DateTrunc(NOW()) |
| 13 | FY 同期查询的结果多出一列 FY 分组 | 把 `metric_time__FY_year` 放进了 dimensions | 那里不放 FY 维度——两期来自两个 metricDefinitions（§1.5.1 C） |
| 14 | 所选指标的 displayName/描述与用户原话的口径对不上（实体/范围/时间限定不同） | 候选指标语义不匹配 | 重新核对描述；替代只在语义等价时可行（自检 6）。**对不齐就不要硬选** → 按 SKILL.md Step 5 反问 |
| 15 | 结果里出现用户没提过的分组列 | 用户要的维度不存在，被相近维度顶替 | 绝不顶替：弃用并在 buildReason 说明；核心维度缺失按 SKILL.md Step 4 如实告知 |
| 16 | 多指标查询里某个指标整列为空 | dimensions 含了该指标不支持的维度 | 只取 `metric_dimensions` 返回的 COMMON dimensions（自检 17） |
| 17 | 临时指标名与 `metric_search` 返回过的某个指标同名 | 命名冲突，平台可能取到既有指标 | 加业务前缀/后缀区分（§1.2） |
| 18 | 加 MetricMatches 前后，结果行数与数值完全相同 | MetricMatches 引用了 metricDefinitions 临时指标（平台不解析） | 只能引用真实指标；否则用预定义派生指标，或切 SQL 路径（§1.2.3） |


### 4.3 重试纪律

见 SKILL.md Step 7——自动重试一次、只许语义等价修改、严禁静默丢弃/收窄过滤条件。仍失败就向用户解释原因与已尝试的思路，可行的调整通过 ask_human 提议。
