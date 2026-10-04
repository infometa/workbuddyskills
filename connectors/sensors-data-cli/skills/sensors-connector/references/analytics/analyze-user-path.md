# 用户路径分析
> 工具 `analysis.user-path` · 命令 `sensors analytics user-path` · 类型 查询

## 用途

查询用户路径报告：从指定起始事件（正向）或结束事件（反向）出发的路径节点与流转关系。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径；输入字段名须与 `UserPathReportRequest` 一致，无 CLI 别名 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `source_type` | string | 是 | 非空 | 路径方向，推荐 `initial_event`（起始事件正向）或 `termination_event`（结束事件反向） | `initial_event` |
| `source_event` | object | 是 | 结构见下 | 起始或结束事件定义 | `{"event_name":"$AppStart"}` |
| `event_names` | string[] | 是 | 至少 1 项，元素非空 | 参与路径分析的事件列表 | `["$AppStart","$AppViewScreen","$AppEnd","$WebClick"]` |
| `by_fields` | string[] | 否 | 元素非空 | 参与分析事件的分组字段列表 | `—` |
| `col_limit` | int | 是 | > 0 | 路径列数限制 | `4` |
| `row_limit` | int | 是 | > 0 | 每列节点数限制 | `5` |
| `from_date` / `to_date` | string | 是 | `yyyy-MM-dd`，`from_date <= to_date` | 顶层平铺日期（注意：本命令无 `date_range` 嵌套对象） | `2026-09-20` / `2026-09-26` |
| `user_filter` | object | 否 | 过滤树 | 用户筛选 | `—` |
| `bucket_params` | object | 否 | key 字段名 / value 边界列表 | 数值分桶参数 | `—` |
| `sampling_factor` | int | 否 | — | 抽样因子，64 为全量 | `—` |
| `session_interval` | int | 否 | ≥ 0 | Session 切割间隔，通常按秒传（如 `1800`） | `1800` |
| `use_cache` | bool | 否 | — | 是否使用缓存 | `—` |
| `filter` | object | 否 | 过滤树 | 全局事件筛选 | `—` |
| `single_event_with_filters` | object | 否 | key 事件名 / value 过滤树 | 单事件筛选映射 | `—` |

`source_event` 每项：`event_name`（必填，事件名）、`filter`（可选过滤树）、`by_field`（可选分组字段）、`relevance_field`（可选事件关联字段）。`filter` / `user_filter` / `source_event.filter` / `single_event_with_filters` 传空对象 `{}` 视为未传；`request_id` 由 CLI 自动注入，无需手填。过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

7 个必填参数（`source_type` / `source_event` / `event_names` / `col_limit` / `row_limit` / `from_date` / `to_date`）一个都不能少；业务输入未收敛到 7 参数齐全前不构造请求。步骤化映射：

### 第一步：定方向（值映射）

| 业务表达 | `source_type` |
|---|---|
| 「看 A 之后都去了哪里」（后续路径） | `initial_event`（从起始事件向后分析） |
| 「看 B 之前都经历了什么」（前序路径） | `termination_event`（从结束事件向前回溯） |

### 第二步：定源事件

把起点或终点事件写入 `source_event.event_name`；事件名必须是已确认的精确标识。

### 第三步：定参与事件集合

整理本次路径分析允许出现的事件列表写入 `event_names[]`（至少 1 个、不能有空字符串），每个事件名都已确认存在且拼写精确。

### 第四步：定路径规模（截断参数）

| 业务表达 | 映射结果 |
|---|---|
| 「看 3 层 / 5 层路径」 | `col_limit`（层数限制，必须 > 0） |
| 「每层只保留前 5 个节点」 | `row_limit`（每列节点数限制，必须 > 0） |

两个截断参数避免默认猜值，与调用方确认后写入；截断后只能下「当前返回范围内」的结论。

### 第五步：定时间范围

相对时间先换算为绝对日期，再写顶层平铺的 `from_date` / `to_date`（本命令无 `date_range` 嵌套对象）。

### 第六步：定可选筛选（三入口分流）

| 业务表达 | 写入位置 |
|---|---|
| 「只看某类用户」 | `user_filter`（用户维度条件） |
| 「整体只看满足某事件条件的数据」 | `filter`（全局事件筛选） |
| 「某个参与事件要单独加条件」 | `single_event_with_filters`（key 为事件名，value 为过滤树） |

### 第七步：自检并执行

对照必填清单与约束过一遍 → `--dry-run` 确认请求体 → 执行。

### 调用示例

最小可用请求（正向路径）：

```bash
sensors analytics user-path --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "source_type": "initial_event",
  "source_event": { "event_name": "$AppStart" },
  "event_names": ["$AppStart", "$AppViewScreen"],
  "col_limit": 3,
  "row_limit": 5,
  "from_date": "2026-07-01",
  "to_date": "2026-07-03"
}
__SENSORS_QUERY__
```

带筛选和分组的请求（反向路径 + 单事件筛选）：

```bash
sensors analytics user-path --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "source_type": "termination_event",
  "source_event": { "event_name": "order_pay" },
  "event_names": ["$AppViewScreen", "submit_order", "order_pay"],
  "by_fields": ["event.submit_order.order_type"],
  "col_limit": 4,
  "row_limit": 6,
  "from_date": "2026-07-01",
  "to_date": "2026-07-07",
  "user_filter": {
    "relation": "and",
    "conditions": [
      { "field": "user.platform", "function": "equal", "params": ["ios"] }
    ]
  },
  "single_event_with_filters": {
    "submit_order": {
      "relation": "and",
      "conditions": [
        { "field": "event.submit_order.order_type", "function": "equal", "params": ["express"] }
      ]
    }
  }
}
__SENSORS_QUERY__
```

## 输出

不走公共 `columns` / `rows` 结构（见 [analytics-query-schema.md](analytics-query-schema.md) 公共输出一节），保留路径专属结构：

| 字段 | 含义 | 示例值 |
|---|---|---|
| `nodes` | 路径节点分层列表；`nodes[i]` 为第 i 列节点集合 | `[{"times":5513.0,"event_name":"$AppStart","id":"0_$AppStart"}]` |
| `links` | 路径连线分层列表；`links[i]` 为第 i 列到第 i+1 列的流转 | `[{"times":4.0,"source":"0_$AppStart","target":"1_$AppViewScreen"}]` |
| `truncate_rows` | 各列节点截断数量 | `[]` |
| `truncate_col` | 路径列是否截断 | `false` |
| `truncated` | 整份结果是否截断 | `false` |
| `sampling_factor` | 结果抽样因子（如返回，64 为全量） | `0` |
| `report_update_time` / `data_update_time` / `data_sufficient_update_time` | 各类更新时间（如返回） | `2026-09-27 09:52:33.519` / `2026-09-27 09:40:36.640` / `2026-09-27 02:00:00.000` |
| `request_id` | 请求追踪 ID | `891f88dec42a4a069066f91be60746a3` |

结构性读法：`nodes[0]` 是起点（或终点反向时为首层回溯）列，逐列向后（前）读；`links[i]` 描述第 i 列节点到第 i+1 列节点的流转关系，节点与连线按层级一一对应。`links` 中可能出现 `is_wastage: true` 的连线（`target` 形如 `N_wastage`），表示从该节点流失的用户量；`N_wastage` 是虚拟节点、不在 `nodes` 中出现，解读时按流失口径处理。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `source_type: Field required` / `source_type 不能为空字符串，请传入有效的路径方向` | 路径方向缺失或空白 | 补 `initial_event` 或 `termination_event` |
| `source_event.event_name` 缺失或为空 | 源事件没填 | 补精确事件名 |
| `event_names: Field required` / `event_names 不能为空列表，至少需要一个参与分析的事件` | 参与事件数组为空 | 至少一个事件 |
| `row_limit` / `col_limit` 校验失败 | 限制值非正整数 | 改为 > 0 的整数 |
| `session_interval` 校验失败 | 传负数 | ≥ 0 |
| 日期校验失败 | 非 `yyyy-MM-dd` 或 `from_date > to_date` | 改为合法绝对日期 |
| 返回为空 | 时间范围不对、事件集过窄或过滤过严 | 先放宽过滤，再缩小事件集合逐步重查（由调用方决定） |

## 使用约束

- 多候选事件/属性时禁止自行二选一；示例中的事件名占位符必须替换为已确认的真实标识。
- `truncate_rows` 非空或 `truncate_col=true` 时只能下「当前返回范围内」的结论，不得宣称完整路径。
- `sampling_factor != 64` 时绝对量级为采样估算，原样传回调用方。
