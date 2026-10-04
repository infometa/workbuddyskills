# 只读 SQL 执行

> 工具 `sql.execute` · 命令 `sensors analytics sql` · 类型 查询

## 用途

对当前项目执行只读 Impala SQL（`SELECT` / `WITH ... SELECT`）并返回结构化结果。库、表、列的发现使用 `metadata.databases` / `metadata.tables` / `metadata.columns`。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--sql` | 字符串 | 是 | — | 要执行的 Impala SQL；不能为空或纯空白，长度不超过 100000 字符 | `SELECT date, count(*) AS app_start_count FROM horizon_production_3.events ... LIMIT 5` |
| `--limit` | 整数 | 否 | `1000` | 最大返回行数，取值范围 1~50000 | `5` |
| `--database` | 字符串 | 是 | — | 目标数据库名（**必填，无默认值**）；先经 `metadata.databases` 确认，当前项目默认库为其中 `created_by = sensorsdata.horizon` 的库；未指定直接报错 | `horizon_production_3` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印将要发送的请求 JSON，不发起真实 HTTP 请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty` 等）见 `sensors analytics sql --help`；本命令 `--timeout` 默认 1800s（30 分钟），可用 `--timeout` 覆盖。

## 输入 Schema

无 `--input` 复杂输入，SQL 正文通过 `--sql` 传入，行数与库通过 `--limit` / `--database` 传入。执行前门禁（不通过时不执行真实查询，先返回修正原因）：

1. SQL 非空且不是不可执行片段。
2. 只能是 `SELECT` 或 `WITH ... SELECT`；禁止一切 DDL / DML（INSERT / UPDATE / DELETE / CREATE / DROP 等）。
3. 结果投影列名不得重复：SQL 中存在重复列名或重复别名时，必须先改写成唯一列名再执行，不允许靠位置序号消歧（CLI 也会对返回列名做重复校验并报错）。
4. SQL 含 `$AppStart`、`$AppClick` 等 `$` 标识时，命令行须做 shell 转义（`\$`）；转义只发生在命令层，返回与展示的 SQL 保留原始业务 SQL。

## 构造流程

库表定位与参数构造：

1. **库名确认（--database 来源）**：`--database` 必填、无默认值，未指定直接报错。库名先经 `sensors metadata databases` 确认：当前项目默认库为其中 `created_by = sensorsdata.horizon` 的库，跨项目库对目标项目分别确认后显式传入。SQL 内不带库名前缀的表由服务端按当前项目解析。
2. **跨库写法**：访问其它库的表时在 SQL 内用 `<database>.<table>` 直接指定，可直接写 `dbA.table JOIN dbB.table`。
3. **跨库与跨项目是同一机制**：神策库名全局唯一（`horizon_{项目英文名}_{项目id}`），SQL 层没有「项目边界」，只有「先按项目把对应库名找出来」。库名发现方式：同项目多库一次 `sensors metadata databases` 可见；跨项目需对每个项目（`--project <项目英文名>`）各调一次 `sensors metadata databases` 确认库名，确认后直接写 `dbA.table JOIN dbB.table`。
4. **自带 SQL 的命令层处理**：表名带不带 `database.` 前缀都**原样执行**，不静默补库、也不强制补全为全限定名；不因字段不存在、事件值未知或枚举值未确认而改写或回退——字段 / 语法 / 权限问题由执行层错误原样返回。
5. **行数控制**：`--limit` 控制最大返回行数（默认 1000、上限 50000）；SQL 内自身的 `LIMIT` 与 `--limit` 各自生效，需要约束结果规模时两者都要检查。
6. **两步执行**：先 `--dry-run` 预览请求 JSON，确认 SQL 形态后去掉该 flag 真实执行；`current_database` 回显传入的 `--database`。

示例变体：

```bash
# 先预览请求，不发起真实请求（--database 必填）
sensors analytics sql --ai-session-id <ai_session_id> \
  --sql "SELECT count(*) FROM events WHERE date = '2026-06-21'" \
  --database <database_name> --limit 100 --dry-run

# 确认后真实执行（不带库名前缀的表由服务端按当前项目解析）
sensors analytics sql --ai-session-id <ai_session_id> \
  --sql "SELECT count(*) FROM events WHERE date = '2026-06-21'" \
  --database <database_name> --limit 100

# 跨库表：SQL 内用 <database>.<table> 指定其它库
sensors analytics sql --ai-session-id <ai_session_id> \
  --sql "SELECT * FROM <database>.<table> LIMIT 100" \
  --database <database_name> --limit 100

# $ 标识的 shell 转义（命令层转义为 \$，业务 SQL 保持 $AppStart）
sensors analytics sql --ai-session-id <ai_session_id> \
  --sql "SELECT count(*) FROM events WHERE date = '2026-06-21' AND event = '\$AppStart'" \
  --database <database_name> --limit 100
```

## 输出

`--format json` 时输出（Envelope 包裹）：

```json
{
  "columns": [
    {"name": "date", "display_name": "date", "type": "unknown"},
    {"name": "app_start_count", "display_name": "app_start_count", "type": "unknown"}
  ],
  "data": [
    ["2026-06-16 00:00:00.0", 1462]
  ],
  "request_id": "...",
  "current_database": "<传入的 --database>",
  "db_notice": "本次执行指定数据库 <库名>；SQL 内不带库名前缀的表由服务端按当前项目解析，如需跨库查询，请在 SQL 中用 <database>.<table> 形式。"
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `columns` | 列对象数组，每列 `{name, display_name, type}`（接口不返回列类型，`type` 恒为 `unknown`，`display_name` 恒同 `name`）；所有结果列的并集，按首次出现顺序排列，顺序以引擎实际返回为准，可能与 SELECT 投影顺序不同 | `[{"name":"date","display_name":"date","type":"unknown"},...]` |
| `data` | 二维结果数组，每行与 `columns` 逐位置一一对应，缺失列补 `null` | `[["2026-09-27 00:00:00.0",98],...]` |
| `request_id` | 本次请求追踪 ID（服务端返回时透传） | `5705630b96ce4be3a39be617da9ce3bc` |
| `current_database` | 本次执行指定的目标数据库（回显传入的 `--database`） | `horizon_production_3` |
| `db_notice` | 库提示文案（指定库与跨库写法说明） | `本次执行指定数据库 …` |

结构解读与输出约束：

- **列序必须以引擎返回的 `columns` 为准**：实测引擎可能按列名排序返回——SQL 写 `total_rows, distinct_user_id, distinct_distinct_id`，引擎可能返回 `distinct_user_id, distinct_distinct_id, total_rows` 顺序（看各列 `name`），`data` 每行的值随该顺序逐位置对应。展示、落表或任何二次处理时必须逐位置按 `columns[i].name` 标注 `data`；禁止按 SQL 书写顺序、别名顺序或字母序重排后再套用原始 `data`，否则会发生数据错位（典型如两个 distinct 指标的值互换）。
- 空结果输出 `columns: []`、`data: []`，只说明当前条件下无返回，不编造「没有数据」的绝对结论。
- 返回给调用方的 SQL 一律是原始业务 SQL，不要把 shell 转义后的 `\$AppStart` 写回 SQL 正文。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| SQL 为空 / 超长 | `--sql` 空白或超过 100000 字符 | 修正 SQL 后重试 |
| `--limit` 超范围 | 小于 1 或大于 50000 | 调整到 1~50000 |
| 存在重复列名 | 结果列名或别名重复（CLI 校验报 `存在重复列名：[...]`） | 改写 SQL 使投影列名唯一后重试，不允许靠位置序号消歧 |
| 列数与数据长度不一致 / 结果过大 | 服务端返回畸形，或行 × 列超过 10000000 单元 | 缩小查询范围（收紧过滤、降低 `--limit`）后重试 |
| Impala / 引擎执行错误 | SQL 语法错误、表或列不存在、无权限 | 修正 SQL；表列核对用 `metadata.tables` / `metadata.columns`；自带 SQL 直接透传执行层错误 |
| `timeout` / 连接失败 | 网络或执行超时 | 可有限重试一次；仍失败则返回失败说明，不重复提交同一条失败 SQL |
| 空结果 | 时间范围、过滤条件或事件条件过窄 | 不是错误；核对条件是否过窄后由调用方决定是否放宽 |

## 使用约束

- 只执行只读 SQL：仅 `SELECT` / `WITH ... SELECT`；不执行任何 DDL / DML（INSERT / UPDATE / DELETE / CREATE / DROP 等）。
- 真实执行前先 `--dry-run` 预览请求；门禁不通过时不执行真实查询，先返回修正原因。
- 展示、落表或二次处理时必须以返回的 `columns` 数组为准逐位置标注 `data`（列名取各列 `name`），禁止按 SQL 书写顺序或字母序重排后套用，否则会发生数据错位。
- 表名是否带 `database.` 前缀都原样执行，不静默补库；执行后关注 `current_database` / `db_notice` 确认落在预期库上。
- 不在执行阶段重新猜字段、事件或枚举值；不在展示时把 shell 转义写回 SQL 正文。
