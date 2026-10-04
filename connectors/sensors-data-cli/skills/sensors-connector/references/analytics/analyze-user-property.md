# 属性分析
> 工具 `analysis.user-property` · 命令 `sensors analytics user-property` · 类型 查询

## 用途

按用户/事件属性维度查询分布报表（单属性分布、属性交叉分布等）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `measures` | object[] | 是 | 至少 1 项 | 指标列表，结构见下 | `[{"aggregator":"unique","field":"user.$id"}]` |
| `filter` | object | 否 | 过滤树 | 顶层过滤 | `{"conditions":[{"field":"user.$update_time","function":"isSet","params":[]}]}` |
| `by_fields` | string[] | 否 | 默认 `[]` | 分组维度，用 `user.*` 或 `event.*` 带前缀字段 | `["user.$latest_utm_campaign"]` |
| `x_axis_field` | string | 否 | 默认 `""` | 横轴字段 | `user.$latest_utm_campaign` |
| `sampling_factor` | int | 否 | 默认 `64`（全量） | 采样倍率 | `64` |
| `limit` | int | 否 | — | 返回条数上限 | `10` |
| `bucket_params` | object | 否 | — | 分桶参数 | `—` |
| `use_cache` | bool | 否 | — | 是否使用缓存 | `true` |

`measures[]` 每项：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `event_name` | string | 否 | 事件名，允许为空（空=纯属性口径，不绑定事件） | `—` |
| `aggregator` | enum | 否 | 默认 `general`；聚合方式见 [analytics-query-schema.md](analytics-query-schema.md) 聚合器表 | `unique` |
| `field` | string | 否 | 指标字段，通常为 `user.*` 或 `event.*` 属性 | `user.$id` |
| `name` | string | 否 | 指标显示名（仅请求侧展示用；输出指标列名固定为 `value`，不取 `name`） | `用户数` |

校验速记与易错点：

- `measures[]` 必填且每项是 JSON 对象，不能是字符串；空列表报错 `measures 不能为空列表`。
- `aggregator` 合法值为 `general` / `unique` / `average` / `sum` / `avg` / `max` / `min`（`distinct_count` 为旧值兼容，统一写 `unique`，不要拼变体）。
- `by_fields` 与 `x_axis_field` 必须保持同维度口径，否则分组不生效。
- 用户属性条件统一写 `filter`；过滤树 `relation` 只接受小写 `and` / `or`。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定是否绑定事件

用户只是看属性本身（省份、城市、渠道、版本的分组统计）时，`measures[].event_name` 留空（纯属性分析口径）；需绑定事件口径时才填精确事件名。

### 第二步：定指标（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「按省份看唯一用户数」「去重人数」 | `aggregator: "unique"` + `field: "user.$id"` |
| 「看某属性的分组统计」 | `measures[]` + `by_fields[]`，计数类聚合用 `unique` |
| 属性聚合（求和 / 均值等） | 按 [analytics-query-schema.md](analytics-query-schema.md) 聚合器表的 `aggregator + field` 配套组合填写 |

### 第三步：定过滤

用户属性条件（如「只看某时间之后更新的用户」）统一写入 `filter`，字段带 `user.` 前缀。

### 第四步：定拆分和横轴

按维度统计写 `by_fields[]`；横轴展示的字段写 `x_axis_field`，与 `by_fields` 保持同一维度口径。

### 第五步：定返回量

需限制结果行数（「只看前 10 个维度值」）时写 `limit`。

### 第六步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

按省份统计唯一用户数（含过滤与缓存）：

```bash
sensors analytics user-property --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "measures": [
    { "aggregator": "unique", "field": "user.$id" }
  ],
  "filter": {
    "conditions": [
      { "field": "user.$update_time", "function": "isSet", "params": [] }
    ]
  },
  "sampling_factor": 64,
  "use_cache": true,
  "x_axis_field": "user.province",
  "by_fields": ["user.province"],
  "bucket_params": {}
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。列构成：有 `by_fields` 时拆分列即 `by_fields` 中的字段名（如 `user.e2e_vip_level`），指标列固定为 `value`（统计值 / 指标值）；无分组时 `columns` 各列 `name` 仅 `value`。输出中不出现 `by_value` 列，按 `columns` 顺序解释 `rows`。

结构性读法：拆分列值大量为空或重复时，优先检查 `by_fields` 与 `x_axis_field` 是否同维度；`event_name` 为空时按纯属性分析口径解读，不要强行绑定某个事件。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `measures 不能为空列表` | `measures` 为 `[]` | 至少 1 项指标 |
| `aggregator` 不被识别 | 传了不支持的旧值或拼错变体 | 改用 [analytics-query-schema.md](analytics-query-schema.md) 枚举值（旧 `distinct_count` 统一写 `unique`） |
| 分组不生效 | `by_fields` 与 `x_axis_field` 口径不一致 | 统一检查两者字段 |
| `event_name` 为空仍报错 | 旧版本不支持空事件口径 | 属性分析允许为空；升级 CLI |
| 结果为空 | 过滤过严或属性无数据 | 先去掉过滤验证；是否重查由调用方决定 |
| `truncated=true` | 结果被截断 | 原样传回，不下绝对结论 |

## 使用约束

- 多候选属性时禁止自行二选一；示例中的属性占位符必须替换为已确认的真实标识。
- `event_name` 为空是合法输入，表示纯属性分析口径，不强行绑定事件。
- `truncated=true` 原样传回，不下绝对结论；空结果不得自动放宽条件重试。
