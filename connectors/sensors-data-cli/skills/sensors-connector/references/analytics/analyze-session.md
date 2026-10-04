# Session 分析
> 工具 `analysis.session` · 命令 `sensors analytics session` · 类型 查询

## 用途

统计指定事件在平台侧 Session 定义维度上的聚合指标（会话数、会话时长、人均次数等）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径；必须包含 `event`、`date_range`、`session_name` | `-` |
| `--dry-run` | flag | 否 | 关闭 | 打印转换后的 OpenAPI Request JSON，不发起真实请求 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

`--input` 必填且无任何快捷 flag：不像 LTV 支持 `--days`，最简单的查询也须通过 `--input` 传入完整 JSON。

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | object | 是 | 结构见下 | Session 分析目标事件（允许直接传字符串，CLI 自动包装） | `"$AppStart"` |
| `date_range` | object | 是 | 见契约 | 公共日期范围，见 [analytics-query-schema.md](analytics-query-schema.md) | `2026-09-20 ~ 2026-09-26` |
| `session_name` | string | 是 | 非空 | Session 定义英文名，须来自平台已有定义；用 [list-session-definitions.md](list-session-definitions.md) 查询或 [create-session-definition.md](create-session-definition.md) 创建 | `test07281` |
| `by_fields` | string[] | 否 | 默认 `[]`，元素非空 | 分组维度 | — |
| `unit` | enum | 否 | 默认 `day` | `day` / `week` / `month` / `hour` | `day` |

`event` 对象：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `event` | string | 是 | 非空 | 事件名 | `$AppStart` |
| `aggregator` | enum | 否 | 默认 `general` | 聚合方式，`field` 配套规则见 [analytics-query-schema.md](analytics-query-schema.md) | `general` |
| `field` | string | 条件 | 三段式 | 数值类聚合必填；计数类不允许填 | — |
| `filter` | object | 否 | 过滤树 | 事件过滤 | — |

校验速记（构造后必过）：

- `session_name` 必填且不能是空字符串或纯空白，必须是 `session-list` 输出中的 `name`（结合 `cname` 消歧），不能猜。
- `event.event` 必填；`event` 传字符串等价于 `{"event": <name>}`，默认 `aggregator: "general"`。
- 计数类聚合（`general`/`unique`/`average`）不带 `field`；属性聚合（`sum`/`avg`/`max`/`min`）必带三段式 `field`。
- 过滤树 `relation` 只接受小写 `and` / `or`。

业务正确性约定（CLI 不强制校验，需自行保证）：

- Session 指标的口径取决于 `session_name` 对应的平台侧 Session 定义（事件范围、间隔、切割规则），查询前须确认该定义符合业务口径。
- `by_fields` 内事件字段路径应与 `event.event` 一致，否则分组对齐会产生解读困惑。
- 没有独立的全局过滤入口：近似计算、按天拆分、自定义分桶、汇总/明细切换、行数上限等高级项走平台默认；过滤统一写在 `event.filter`。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定 Session 定义（`session_name` 从哪来）

`session_name` 必须是平台已有 Session 定义的英文 `name`，获取路径二选一：

- 查已有定义：`sensors analytics session-list --ai-session-id <ai_session_id>`。返回中重点看 `id`（更新定义时用）、`name`（写入 `session_name` 的精确值）、`cname`（展示名，与 `name` 双字段消歧）、`events`（定义覆盖的事件）、`session_interval_seconds`（间隔秒数）、`is_event_split` / `start_event` / `stop_event`（切割配置）、`comment`（业务口径备注）。用户说了中文名或口语名时，用 `name` + `cname` 对比再结合 `comment`、`events` 判断候选；多候选时把 `id/name/cname/events/session_interval_seconds` 列出交还调用方确认，不自行二选一。
- 创建新定义：项目里没有符合口径的定义时，用 [create-session-definition.md](create-session-definition.md) 创建，创建请求里的 `name` 即后续查询使用的 `session_name`。创建 / 更新定义是写操作，执行前须经调用方确认；仅本次分析需要不同口径时优先创建新定义而非更新已有定义。

不要用中文名、口语名或猜测名直接填 `session_name`。

### 第二步：定事件与聚合（值映射）

| 业务表达 | 映射结果 |
|---|---|
| 「会话数」「访次」 | `aggregator: "general"`，不填 `field` |
| 「访问用户数」「会话内独立 UV」 | `aggregator: "unique"`，不填 `field` |
| 「人均会话次数」 | `aggregator: "average"`，不填 `field` |
| 「平均会话时长」「总停留时长」 | `aggregator: "avg"` / `"sum"` + 三段式 `field` |
| 「最大 / 最小会话深度」 | `aggregator: "max"` / `"min"` + 三段式 `field` |

### 第三步：定过滤

用户属性与事件属性条件统一写到 `event.filter`（用户字段 `user.*`，事件字段 `event.<event>.*`）。

### 第四步：定时间与粒度

相对时间先换算为绝对 `date_range`；`unit` 默认 `day`。

### 第五步：定拆分

`by_fields` 按需写入（与事件分析约定一致）；可写多个但需关注结果体量。

### 第六步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 端到端推导示例

业务输入：「最近 7 天小程序的会话次数趋势，按来源拆分。」

1. 定 Session 定义：`session-list` 已确认 `mp_visit_session` 是目标定义的精确 `name`。
2. 定事件：`$MPShow` 已确认精确事件名。
3. 定聚合：「会话次数」→ `aggregator: "general"`，不填 `field`。
4. 定过滤：无显式过滤。
5. 定时间：最近 7 天换算为绝对日期；`unit: "day"`。
6. 定拆分：按来源 → `by_fields: ["event.$MPShow.$referrer"]`。
7. `--dry-run` → 执行。

### 调用示例

最小可执行（会话次数趋势，`event` 字符串简写）：

```bash
sensors analytics session --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "event": "$MPShow",
  "session_name": "mp_visit_session",
  "date_range": { "from_date": "2026-06-19", "to_date": "2026-06-25" },
  "unit": "day"
}
__SENSORS_QUERY__
```

`event` 直接传字符串是 CLI 兼容写法，等价于 `{"event": {"event": "$MPShow"}}`，默认 `aggregator: "general"`。

完整示例（属性聚合 + 过滤 + 拆分）：

```bash
sensors analytics session --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "event": {
    "event": "$MPShow",
    "aggregator": "avg",
    "field": "event.$MPShow.$duration",
    "filter": {
      "relation": "and",
      "conditions": [
        { "field": "user.$platform", "function": "equal", "params": ["iOS"] }
      ]
    }
  },
  "session_name": "mp_visit_session",
  "date_range": { "from_date": "2026-06-19", "to_date": "2026-06-25", "timezone": "" },
  "unit": "day",
  "by_fields": ["event.$MPShow.$referrer"]
}
__SENSORS_QUERY__
```

## 输出

公共结构 `{truncated, columns, rows, request_id}`，见 [analytics-query-schema.md](analytics-query-schema.md)。`columns` 构成：

- `date` 列：每时间点一行，值为时间点（按 `unit` 粒度展开为行）。
- 维度列：请求 `by_fields` 中的字段（如有）；事件维度会被服务端归一化为 `event.$Anything.<prop>`（事件名替换为通配 `$Anything`，如请求 `event.$AppStart.$lib` 返回列名 `event.$Anything.$lib`），解读时按属性名对齐；用户维度（`user.*`）列名保持原样。
- 指标列：列名 = 请求中 measure 的 `name`；CLI 构造请求时 `name` 取事件名，因此指标列名即查询事件名（如 `$MPShow`），语义由 `aggregator` 决定。

输出示例（`unit: "day"`、单个维度拆分，数值为占位）：

```json
{
  "truncated": false,
  "columns": [
    {"name": "date", "display_name": "date", "type": "date"},
    {"name": "<by_fields 维度列>", "display_name": "<by_fields 维度列>", "type": "string"},
    {"name": "$MPShow", "display_name": "$MPShow", "type": "number"}
  ],
  "rows": [
    ["2026-06-19 00:00:00", "<维度值>", "<数值>"],
    ["2026-06-20 00:00:00", "<维度值>", "<数值>"]
  ],
  "request_id": "<request_id>"
}
```

读法与事件分析一致：维度列来自 `by_fields`，指标列语义由 `aggregator` 决定，每行对应一个时间点；区别只在指标语义来自平台 Session 口径（同一事件用事件分析与 Session 分析数据不一致属正常差异，解读时点出「基于 Session 口径」）。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| 命令拒绝执行（缺 `--input`） | Session 命令 `--input` 必填 | 通过 heredoc 或 JSON 文件传入；无快捷 flag |
| `session_name 不能为空` | 缺 Session 定义名或传空白 | 先经 `session-list` 查得精确 `name` 再填入 |
| Session 定义名不存在：表层常表现为 GRPC 服务未知异常，需看 `origin_cause` 中 `SESSION_NOT_EXISTS(session=...)` 才是真实原因 | `session_name` 用了中文名/口语名/猜测名 | 用 [list-session-definitions.md](list-session-definitions.md) 查 `name` + `cname` 消歧，或经 [create-session-definition.md](create-session-definition.md) 创建 |
| 事件校验失败 `event 不能为空字符串` | 事件名空白 | 传入精确事件名 |
| `by_fields[i] 不能为空字符串` | 分组维度元素空白 | 移除或填合法字段名 |
| `计数类聚合不允许提供 field` | 计数类聚合带了 `field` | 删除 `field` |
| `属性聚合必须提供 field` | 数值聚合缺 `field` | 补三段式 `event.<event>.<prop>` |
| 过滤条件被拒 | `op`/`values` 或非法 `function` | 按 [analytics-query-schema.md](analytics-query-schema.md) 重写 |
| 同事件与事件分析数据不一致 | Session 走平台 Session 定义口径 | 正常差异；解读时点出「基于 Session 口径」 |
| 结果截断 / 采样 | 时间跨度大、分组多 | 按 [analytics-query-schema.md](analytics-query-schema.md) 完整性标记口径解释 |
| 空结果 | 条件过严、命名错、Session 定义未配置 | 先确认平台侧是否有对应 Session 定义；不自动放宽重试 |

## 使用约束

- 多候选 Session 定义时禁止自行二选一，把候选 `id/name/cname` 交还调用方确认。
- 示例中的 `session_name` 与事件名占位符必须替换为已确认的真实标识。
- 空结果不代表业务上不存在，不得自动放宽条件重试。
