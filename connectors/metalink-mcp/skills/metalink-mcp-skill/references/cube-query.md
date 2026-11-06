# Cube 查询：参数、过滤、日期与库存

本文件随技能包提供，构造 Cube 查询前读取。工具定义决定可传参数，`describe_cube` / `describe_business_model` 决定当前可见成员。关联表存在某列不代表 Cube 已声明该列。

调用顺序、定义复用、重试和保存条件统一见[主技能](../SKILL.md)。每个新问题先获取上下文和历史案例；已核验且仍有效的定义不必重复读取，Cube 已能覆盖问题时不强制读取基础模型 schema。

内容：模式与参数 → 过滤器 → 日期与快照 → 查询示例 → 排名与错误。

## 模式与参数

未指定 mode 时，有 measures 推断为 aggregate，否则推断为 detail。aggregate 计算声明指标，dimensions 与带粒度的 time_dimension 定义分组。detail 通过 dimensions 投影已声明维度/时间维度，保留完整 JOIN 后的行和原始时间戳，不添加 GROUP BY、DISTINCT 或聚合；一行不一定是一条基础记录。

“各门店库存明细表”若要求每店库存数量、金额一行，仍是 aggregate。数值 measure 不能当作 detail field；数值 dimension 可以作为 field，但不因此产生 SUM/AVG 指标。

| MCP 参数 | 格式与约束 |
|---|---|
| `cube` | 必填字符串，当前可见 Cube 名 |
| `mode` | 可省略，按 measures 推断；显式值为 `aggregate` 或 `detail`，没有 distinct 模式 |
| `measures` | aggregate 至少一个已声明指标名，字符串数组；不能填 `SUM(x)` |
| `dimensions` | aggregate 分组、detail 投影；已声明维度/时间维度名的数组 |
| `fields` | detail 投影的兼容参数；与 dimensions 二选一，不同时传 |
| `time_dimension` | 两种模式均可用已声明的 `name` 加顶层 date_range 仅筛日期；aggregate 用 `name:granularity` 分组；兼容 `name:granularity:start,end` |
| `date_field` | 日期绑定的兼容参数；优先使用 time_dimension，不混传冲突字段 |
| `date_range` | 恰好两个非空边界字符串的数组 `["start","end"]`；语义为左闭右开 `[start,end)`，日期字段绑定见下方规则 |
| `timezone` | 默认 UTC；显式提供已确认的业务时区，使用 IANA 名或有效固定偏移，如 `Asia/Shanghai`、`+08:00`；适用边界见日期说明 |
| `filters` | 字符串数组，每项 `dimension:operator[:value]`，各项 AND |
| `order_by` | 字符串数组，每项 `member:asc` 或 `member:desc`，成员必须选中且不重复 |
| `limit` / `offset` | 非负整数；执行默认 limit=1000，最多 10000，offset 默认不偏移 |
| `sql_only` | JSON 布尔值；true 仅预览，false 执行，默认 false |
| `question` | 可省略的字符串；每次调用提供本次子问题的指标、过滤、日期与粒度，翻页和同范围纠错沿用 |

detail 必须有非空且不重复的投影成员，不传 measures 或时间粒度；aggregate 不传 fields。MCP 使用上述 snake_case 参数；不要混入内部 CubeQuery 的 `timeDimensions`、`dateRange`、`orderBy` 或结构化 filters 对象。参数只表示结构，成员名仍须通过 describe 核验。

粒度枚举：`year`、`quarter`、`month`、`week`、`day`、`hour`、`minute`。不支持 `second`、`daily`、`monthly` 或中文别名。模式、粒度、过滤操作符和排序方向使用上述小写值。

同一时间字段同时出现在 dimensions 与 time_dimension 时，使用后者的粒度。order_by 用已声明成员名（如 `已声明时间字段:asc`），不用生成的 `__month` 等别名。limit=0 返回零行，不代表无限。执行默认 limit=1000、最大 10000；预览采用用户提供的 limit，不自动套用执行默认值或最大值，比较预览与执行时显式提供计划使用的 limit。分页或固定行数 TOP N 要添加能区分并列行的稳定排序键。

## 过滤器

下表中的商品、部门和日期字段仅为示例项目成员；实际调用替换为已核验的声明名。

| 操作符 | 示例 | 含义 |
|---|---|---|
| `eq` / `neq` | `goods_code:eq:G1` / `channel:neq:outlet` | 等于 / 不等于 |
| `in` / `not_in` | `channel:in:retail,online` / `dept_code:not_in:D1,D2` | 属于 / 不属于非空集合 |
| `gt` / `gte` | `unit_price:gt:100` / `acc_date:gte:2026-09-01` | 大于 / 大于等于 |
| `lt` / `lte` | `acc_date:lt:2026-10-01` / `unit_price:lte:500` | 小于 / 小于等于 |
| `contains` / `starts_with` | `goods_name:contains:花生油` / `goods_code:starts_with:G` | SQL LIKE 包含 / 前缀匹配 |
| `is_null` / `is_not_null` | `brand_name:is_null` / `brand_name:is_not_null` | SQL NULL 判断，不带值 |

- 没有 `=`、`equals`、`like`、`between`、`or`、`not_contains`、`ends_with`。过滤成员只能是声明的维度/时间维度，不要求选中；不能用 measure 名表达 HAVING。
- 集合直接用逗号分隔：`goods_code:in:G1,G2`，不加方括号、圆括号、SQL 引号。标量也不加 SQL 引号：`goods_name:eq:花生油`。JSON 的双引号仍保留。
- 不在字段/操作符两侧加空格。IN 项会去除两端空格和空项；标量值原样保留。当前格式没有单项逗号转义，不能表达含逗号的单个 IN 值，不用 SQL 引号伪装转义。
- `eq:null` 比较字符串 `null`；`neq` / `not_in` 不包含 NULL。排除 outlet 但保留 NULL 需要 `(channel <> 'outlet' OR channel IS NULL)`，两个 AND filters 无法表达。核验后可改用当前授权范围内的公共语义 SQL；API 模式仍须处于所选 Cube 的 SQL 范围，不能因参数表达不足扩大来源。如采用分组后处理，必须证明分组完整、互不重叠且指标可加，不能套用于均值、比率或快照。
- 数字过滤值通过此接口仍是字符串，比较依赖字段类型和数据库转换。子串匹配用普通值，例如 `status:contains:complete`，不要自行添加 `%`。`like` 不会自动替换成 `contains`，传入的值也不会被删除 `%`。contains/starts_with 不转义用户值中的 `%`、`_`；大小写取决于数据库。
- 业务枚举（商品状态、部门类型等）从字段说明、业务规则或授权查询核验，不从参数枚举表猜测。查到代码不等于确认了它的业务含义。

## 日期范围与分组

推荐顶层 `date_range=["start","end"]`：JSON 的两个元素不表示闭区间，实际范围为 `[start,end)`，开始包含、结束不包含。9 月是 `2026-09-01` 到 `2026-10-01`；9、10 两月到 `2026-11-01`；10 月 11 日单日到 `2026-10-12`。边界用完整日期或完整时间戳，如 `2026-10-01T00:00:00+08:00`；不传裸 `2026-09` 或 `2026`。保留用户明确的部分月份范围。

先确定需要“每部门一行”还是“每部门每天/月一行”，再选参数。以下 `已声明时间字段`、`已声明部门字段` 为占位符，必须替换为当前公开定义中的实际成员名：

| 查询类型 | 日期表达 |
|---|---|
| aggregate，仅过滤日期、不按日期分组 | `time_dimension="已声明时间字段"`，`date_range=["2026-09-01","2026-10-01"]` |
| aggregate，按月/日分组 | `time_dimension="已声明时间字段:month"`，`date_range=["2026-09-01","2026-10-01"]` |
| detail，筛选日期并保留原始明细 | `dimensions=["已声明部门字段","已声明时间字段"]`，`time_dimension="已声明时间字段"`，配合顶层 date_range；不传粒度 |
| 扩展指标的计算窗口/快照 | 按已声明指标的时间字段和窗口绑定 date_range，检查实际计算与过滤范围 |
| 字符串月键 | 按已声明字段的真实类型与枚举过滤，不自动转换成 DATE；例如示例项目字符串成员 `month_dt:eq:202610` |

显式 `time_dimension="已声明时间字段"` 只选择日期过滤字段，不自动把它加入 SELECT/GROUP BY；该用法需要 date_range。不要写 `已声明时间字段:2026-09-01,2026-10-01`：冒号后的位置是粒度，不是日期。

未显式指定过滤时间字段时，date_range 可以绑定 dimensions 中唯一选中的已声明时间维度。aggregate 若两者都没有，只有指标定义能提供相应时间字段/窗口时才能使用；普通 expression Cube 或 detail 不应依赖没有绑定字段的范围。优先显式绑定，避免歧义。

已声明日期成员也可用 `gte` / `lt` filters 筛选；扩展指标的比较、回溯或快照窗口不能一律替换为普通过滤。顶层 date_range 与 time_dimension 内嵌范围同时提供时必须一致。

顶层 date_range 的规范化路径优先采用 RFC3339 时间戳中的显式偏移，例如 `+08:00` 或 `Z`；timezone 用于解释没有偏移的日期/时间，不覆盖显式偏移。省略 timezone 默认 UTC，仍应显式提供已确认的业务时区，不用含糊的 CST。

旧的 `name:granularity:start,end` 内嵌范围仍兼容，但旧编译路径的时区处理可能不同；不能把顶层范围的偏移优先规则承诺给所有内嵌范围、filters 或分组行为。对当前路径的转换有具体疑问时预览实际 WHERE、指标窗口与分组。自然月/周不是财务月/周；财务周期先读取业务日期映射。

是否预览按 [主技能](../SKILL.md) 第 5 步判断。仅要求预览时返回 SQL 并说明未执行后结束，不继续执行或保存；任务包含执行且疑问解决后才执行。接口或服务版本不支持某种参数形式时，依据实际工具定义选择可表达相同业务范围的形式，不能只凭编译成功认定日期已生效。

## 库存与跨模型查询

- 库存期末数是时点值。确认截止日和数据完整性；T+1 更新约定不证明昨日数据已经齐全。
- `nonAdditiveDimension` / `non_additive_dimension` 表示半累加快照。`windowChoice` / `window_choice` 的 `MIN`、`MAX`（大写）选择最早/最晚快照维度，再按指标表达式聚合，不是对库存金额直接取最大值。分区由 `windowGroupings` / `window_groupings` 决定。
- 不默认所有库存指标均配置了快照，也不把各门店/商品各自最新日期的混合结果称为统一截止日库存。跨日指标不得直接相加。
- 商品检索先确认编码、规格和多候选，再把返回编码传入库存查询；只有库存成功返回部门编码后才做门店名称映射。映射保留未匹配键及一对多关系，不能无依据去重或扩大金额。

## MCP 参数示例

以下是示例项目的 `query_cube` 参数对象，Cube 和字段名不是通用默认值，仅在当前可见定义包含这些成员时使用。先完成主技能的上下文、规则和历史案例步骤。仅展示 SQL 时将 `sql_only` 改为 true，并在返回预览后结束；任务包含执行且需要检查生成 SQL 时，预览并解决疑问后再以相同业务参数执行。

### 商品候选记录

```json
{
  "cube": "goods_catalog",
  "dimensions": ["goods_code", "goods_name", "goods_spec"],
  "filters": ["goods_name:contains:花生油", "goods_spec:eq:4L"],
  "order_by": ["goods_code:asc", "goods_name:asc", "goods_spec:asc"],
  "limit": 100,
  "sql_only": false,
  "question": "查找名称含花生油且规格为4L的商品候选记录"
}
```

detail 不保证编码唯一。分页前确认排序键足以区分行；这些示例字段若仍有重复，需核验可用的稳定键。

### 普通销售 Cube：9 月各部门总额，每部门一行

```json
{
  "cube": "sales_metrics",
  "measures": ["revenue"],
  "dimensions": ["dept_code"],
  "time_dimension": "acc_date",
  "date_range": ["2026-09-01", "2026-10-01"],
  "timezone": "Asia/Shanghai",
  "filters": ["channel:in:retail,online"],
  "order_by": ["dept_code:asc"],
  "limit": 1000,
  "sql_only": false,
  "question": "2026年9月零售和线上渠道各部门销售总额是多少？"
}
```

该参数组合仅筛日期并按部门分组，不按日期分组。求整体标量总额时去掉 dimensions 和部门排序，仍保留日期/渠道过滤。

### 按月销售额排名

```json
{
  "cube": "sales_metrics",
  "measures": ["revenue"],
  "dimensions": ["dept_code"],
  "time_dimension": "acc_date:month",
  "date_range": ["2026-09-01", "2026-11-01"],
  "timezone": "Asia/Shanghai",
  "order_by": ["revenue:desc", "dept_code:asc", "acc_date:asc"],
  "limit": 20,
  "sql_only": false,
  "question": "2026年9至10月销售额最高的20个部门与月份组合是什么？"
}
```

这是全部“部门×月份”组合中前 20 行。每个月分别 TOP 3 应按月独立过滤、每次 limit=3，或使用已核验语义 SQL 的分区排名；不能把全局 LIMIT 当作每月 LIMIT。并列是否全部保留由业务需求决定，固定行数时加稳定排序键。

## 错误与分页

完整性、positional 返回、partial 和纠错预算沿用 [主技能](../SKILL.md)。Cube 分页保持过滤与排序不变，添加足以区分并列行的排序键，offset 按实收行数推进；并发数据更新仍可能改变分页结果。排序不能区分行时，不宣称已取得稳定全量。

Unknown measure/dimension/detail field 时重新 describe 并核对模式；unknown variant 对照本文件枚举；日期错误保持业务范围修正格式。`sql_only` 成功但执行失败时，按 [SQL 诊断说明](wren-sql.md) 区分连接、语法和权限问题，不能删除日期或改换 Cube 来取得非空结果。

过滤操作符不支持时，CLI flags 返回参数错误；受保护 MCP 在身份验证通过后返回 `status=invalid_query`、`code=unsupported_filter_operator`、`field=filters`、`can_correct_arguments=true`，SDK/HTTP 标记 `isError=true`。响应包含完整合法操作符及 `status:contains:complete` 示例。按原始匹配意图修正参数，不机械替换 `like` 或删除通配符；其他权限/查询错误沿用原有处理。CLI `--from` JSON 继续由原生编译器校验枚举。
