# sheet（多维表格）

> `aitable` 是 `sheet` 的别名，`yzj-cli aitable create` 等价于 `yzj-cli sheet create`。

## URL 识别入口

用户粘贴 `https://{host}/knowledge/#/share/doc/<shareToken>?docId=<DOC_ID>` 形式的链接时，按 [doc/url-patterns.md](./doc-url-patterns.md) 提取 `DOC_ID`（doc 与 sheet 共享同一 URL 形态），再继续下方流程。提取出的 ID 直接传给 `--id`，**禁止**把整个 URL 传给 `--id`。

## 核心概念与层级

资源层级（操作前先理清，ID 自上而下逐级获取）：

```
知识库 KB ─→ 多维表格文档 DOC(fileSuffix=dbt) ─→ 数据表 sheet(sheetId,整数) ─→ 字段 field / 视图 view / 记录 record
```

- **知识库（KB_ID）**：顶层容器，`doc workspace list` 获取。
- **多维表格文档（DOC_ID）**：知识库内 `fileSuffix=dbt` 的节点；从 `doc list --workspace <KB_ID>` 中筛 `fileSuffix == "dbt"`，或 `sheet create` 新建后返回。
- **数据表（sheetId）**：多维表内部的子表，**整数** ID；来自 `sheet get` 的 `sheets[].id`。
- **字段 / 视图 / 记录**：位于数据表内，名称与 ID 均来自 schema。
- 多维表格与在线文档（otl）共用同一套知识库/节点体系：多维表本体用 `sheet`，otl 在线文档用 `doc`。

## 意图映射

| 用户说 | 命令 |
|--------|------|
| 新建多维表格 / 建一张表 | `sheet create --workspace <KB_ID> --title "..."` |
| 表结构 / 有哪些字段 / schema（推荐，精简版） | `sheet get --lite --id <DOC_ID>` |
| 表结构（含视图信息 / 字段格式详情） | `sheet get --id <DOC_ID>` |
| 看某个数据表结构 | `sheet table get --id <DOC_ID> --table-id <SHEET_ID>` |
| 加一张数据表 / 新建子表 | `sheet table create --id <DOC_ID> --name "..." --fields '[...]' --views '[...]'` |
| 改数据表名字 | `sheet table rename --id <DOC_ID> --table-id <SHEET_ID> --name "..."` |
| 删数据表 | `sheet table delete --id <DOC_ID> --table-id <SHEET_ID>` |
| 看记录 / 列出数据 / 查记录 | `sheet record list --id <DOC_ID> --table-id <SHEET_ID>` |
| 筛选记录 / 按条件查 | `sheet record list ... --filter '{...}'` |
| 搜记录 / 关键词查 | `sheet record list ... --text-value "..."` |
| 新增记录 / 写一行 | `sheet record create --id <DOC_ID> --table-id <SHEET_ID> --records '[...]'` |
| 改记录 / 更新数据 | `sheet record update --id <DOC_ID> --table-id <SHEET_ID> --records '[...]'` |
| 删记录 | `sheet record delete --id <DOC_ID> --table-id <SHEET_ID> --record-ids rec_a,rec_b` |
| 多维表格改名 / 移动 / 删除 | 复用 `doc rename` / `doc move` / `doc delete` |

### 易混淆

| 用户说 | 用 | 不用 | 理由 |
|---|---|---|---|
| 新建多维表格 | `sheet create` | `doc create` | 多维表格是 `fileSuffix=dbt` 节点；`doc create` 只建 otl 在线文档 |
| 新建文件夹 / 目录 | `doc create`（作为父文档） | `sheet create` | 知识库没有独立文件夹类型；建一个文档作为父节点，子文档挂在其下 |
| 改多维表格标题 / 移动 / 删除 | `doc rename` / `doc move` / `doc delete` | （无 `sheet rename`） | 多维表格本体复用 `doc` 命令；`sheet` 子命令只管理数据表/记录 |
| 改数据表名字 | `sheet table rename` | `doc rename` | 数据表是多维表格内部子表，用 `sheet table rename`；`doc rename` 改的是多维表格文件节点本身 |

## 核心工作流（先查后写）

```
1. 定位知识库   doc workspace list               → KB_ID
2. 定位多维表   doc list --workspace <KB_ID>      → DOC_ID（取 fileSuffix == "dbt" 的节点）
3. 读结构       sheet get --id <DOC_ID>           → sheetId、字段名/类型、视图
4. 操作数据表   sheet table create/rename/delete  （用上一步拿到的 sheetId）
```

**强制规则：**
- 针对数据表/字段/记录的任何操作前，**必须先 `sheet get` 拿到真实 `sheetId` 和字段名**，禁止猜测或编造 ID。
- `sheetId` 是整数，`--table` 传整数；字段名须与 schema 的 `fields[].name` 完全一致。
- 危险操作（`sheet table delete`、`sheet record delete`、`doc delete`）不可恢复，执行前先展示「目标名称 + ID」并获得用户确认，确认后命令须带 `--yes`（未带会被 CLI 拒绝）。

## ID 上下文传递

| 来源命令 | 提取字段 | 用于 |
|---------|---------|------|
| `doc workspace list` | `id` | `sheet create --workspace`、`doc list --workspace` |
| `doc list --workspace <KB_ID>` | `fileSuffix == "dbt"` 项的 `id` | `sheet get --id`、`sheet table ... --id` |
| `doc list --workspace <KB_ID>` | 任意节点的 `id` | `sheet create --parent`、`doc move --target-parent-id`（任何文档都可作为父节点） |
| `doc create` | `id` | 同上（新建父文档后的 PARENT_DOC_ID） |
| `sheet create` | `id` | 同上（新建后的 DOC_ID） |
| `sheet get` | `sheets[].id`（整数） | `sheet table get/rename/delete --table-id` |
| `sheet get` | `sheets[].fields[].name` | 构造 `--fields` / 记录数据的字段 key |

## 命令速查

```bash
# 在知识库根级创建多维表格
yzj-cli sheet create --workspace <KB_ID> --title "项目跟踪表"

# 在指定父文档下创建多维表格（PARENT_DOC_ID 来自 doc list 或 doc create 的返回）
yzj-cli sheet create --workspace <KB_ID> --title "项目跟踪表" --parent <PARENT_DOC_ID>

# aitable 别名等价写法
yzj-cli aitable create --workspace <KB_ID> --title "项目跟踪表"

# 获取多维表结构（schema）——推荐优先使用精简版
yzj-cli sheet get --lite --id <DOC_ID>   # 精简版（推荐，体积约为完整版 1/10）
yzj-cli sheet get --id <DOC_ID>          # 完整版（含视图信息 / 字段格式详情，一般少用）

# 数据表（子表）管理
yzj-cli sheet table get    --id <DOC_ID> --table-id <SHEET_ID>
yzj-cli sheet table create --id <DOC_ID> --name "项目跟踪" --fields '[]' --views '[]'
yzj-cli sheet table rename --id <DOC_ID> --table-id <SHEET_ID> --name "2024数据"
yzj-cli sheet table delete --id <DOC_ID> --table-id <SHEET_ID> --yes   # ⚠️ 连同记录一起删除，不可恢复

# 记录（行数据）管理
yzj-cli sheet record list   --id <DOC_ID> --table-id <SHEET_ID>
yzj-cli sheet record list   --id <DOC_ID> --table-id <SHEET_ID> --filter "{\"mode\":\"AND\",\"criteria\":[{\"field\":\"状态\",\"operator\":\"Equals\",\"values\":[\"进行中\"]}]}"
yzj-cli sheet record create --id <DOC_ID> --table-id <SHEET_ID> --records "[{\"fieldsValue\":{\"任务名\":\"新任务\",\"状态\":\"进行中\"}}]"
yzj-cli sheet record update --id <DOC_ID> --table-id <SHEET_ID> --records "[{\"id\":\"rec_abc\",\"fieldsValue\":{\"状态\":\"已完成\"}}]"
yzj-cli sheet record delete --id <DOC_ID> --table-id <SHEET_ID> --record-ids rec_abc,rec_def --yes   # ⚠️ 不可恢复
```

## sheet create 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--workspace <KB_ID>` | 是 | 知识库 ID，先用 `doc workspace list` 获取 |
| `--title` | 是 | 多维表格标题 |
| `--parent` | 否 | 父节点 ID，省略则创建在知识库根级 |

## sheet get 参数

获取多维表结构（schema），返回数据表（sheets）、字段（fields）、视图（views）。操作多维表数据前先调用它拿到 `sheetId` 和字段结构。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 多维表格 ID，可从 `doc list` 结果中取（`fileSuffix=dbt` 的节点） |
| `--lite` | 否 | 使用精简版 schema（**推荐**，体积约为完整版 1/10，满足绝大多数场景） |

> 精简版（`--lite`）仅含工作表 id/name 及字段 id/name/type（单选/多选字段附带选项字符串数组）。完整版（不加 `--lite`）额外含视图、字段格式详情等，仅在需要这些信息时使用。

### sheet get 返回结构（schema）

```json
{
  "sheets": [
    {
      "id": 1,
      "name": "数据表名称",
      "fields": [
        { "id": "field_1", "name": "字段名", "type": "MultiLineText" }
      ],
      "views": [
        { "id": "view_1", "name": "视图名", "type": "Grid" }
      ]
    }
  ]
}
```

关键提取：
- `sheets[].id` → 数据表 ID（后续记录操作的 `sheetId`，注意是整数）
- `sheets[].name` → 数据表名称
- `sheets[].fields[]` → 字段定义（`name` 用于构造记录的 `fieldsValue` key，`type` 决定值格式）
- `sheets[].views[]` → 视图列表

### 字段类型（fields[].type）

| 分类 | type 取值 |
|------|-----------|
| 文本 | `MultiLineText` |
| 数值 | `Number`、`Currency`、`Percent` |
| 时间 | `Date`、`Time` |
| 选择 | `SingleSelect`、`MultipleSelect`、`Rating` |
| 布尔 | `Checkbox`、`Complete` |
| 身份 | `ID`、`Phone`、`Email` |
| 链接 | `Url` |
| 复杂 | `Contact`、`Attachment`、`Address`、`Note` |
| 关联 | `Link`、`Lookup` |
| 公式 | `Formula` |
| 自动（只读，写记录时不传值） | `AutoNumber`、`CreatedTime`、`CreatedBy`、`LastModifiedBy`、`LastModifiedTime` |

### 视图类型（views[].type）

`Grid`（表格）、`Kanban`（看板）、`Gallery`（画廊）、`Form`（表单）、`Gantt`（甘特图）、`Query`（查询）

### 字段值格式（构造记录数据时参考）

写记录时 `fieldsValue` 的 key 为字段名（与 schema 的 `fields[].name` 一致），值格式按字段类型：

| 字段类型 | 值类型 | 示例 |
|----------|--------|------|
| MultiLineText / ID / Phone / Email | string | `"文本内容"` |
| Number / Currency / Percent / Complete / Rating | number | `125` |
| Date | string | `"2025/11/15"` |
| Time | string | `"11:12:15"` |
| Checkbox | bool | `true` |
| SingleSelect | string | `"选项1"`（须为预定义选项） |
| MultipleSelect | string[] | `["选项1", "选项2"]` |
| Url | object | `{"address": "...", "displayText": "..."}` |
| Contact / Attachment | object[] | `[{"id": "uid", "nickname": "张三"}]` |
| Address | object | `{"districts": ["省","市","区"], "detail": "..."}` |
| Note | object | `{"fileId": "...", "summary": "..."}` |
| Link | string[] | `["记录ID1", "记录ID2"]` |
| 自动字段 | 不传 | CreatedTime/CreatedBy/AutoNumber/Formula/Lookup 等 |

## sheet table 数据表管理

数据表（子表）是多维表格内部的数据表。`sheetId`（整数）从 `sheet get` 返回的 `sheets[].id` 获取。

| 子命令 | 必填参数 | 说明 |
|--------|---------|------|
| `sheet table get` | `--id <DOC_ID>` `--table-id <SHEET_ID>` | 从 schema 中提取单个数据表结构 |
| `sheet table create` | `--id <DOC_ID>` `--name <NAME>` `--fields <JSON>` `--views <JSON>` | 创建数据表；`--fields`/`--views` 必填（JSON 数组，各至少一个元素） |
| `sheet table rename` | `--id <DOC_ID>` `--table-id <SHEET_ID>` `--name <NAME>` | 重命名数据表 |
| `sheet table delete` | `--id <DOC_ID>` `--table-id <SHEET_ID>` `--yes` | 删除数据表（⚠️ 连同记录，不可恢复，须用户确认后加 `--yes`） |

- `--id` 是多维表格文档 ID（`fileSuffix=dbt`）；`--table-id` 是数据表 ID（整数，来自 `sheet get` 的 `sheets[].id`）。
- `sheet table get` 无独立接口，内部调用 schema 后按 `sheetId` 过滤；先用 `sheet get` 拿到正确的 `sheetId`。
- `--fields` / `--views` 为 JSON 数组，字段 `type` 取值见上文「字段类型」，视图 `type` 见「视图类型」。

`sheet table create` 带字段/视图示例（Windows 下需用双引号并转义内部引号）：

```bash
yzj-cli sheet table create --id <DOC_ID> --name "项目跟踪" \
  --fields '[{"name":"任务名","type":"MultiLineText"},{"name":"状态","type":"SingleSelect","data":{"items":[{"value":"待处理"},{"value":"进行中"},{"value":"已完成"}]}}]' \
  --views '[{"name":"默认视图","type":"Grid"}]'
```

## sheet record 记录管理

记录（行）操作前先 `sheet get` 拿到 `sheetId`（整数）和字段名。`--table-id` 传 `sheetId`。

| 子命令 | 必填参数 | 说明 |
|--------|---------|------|
| `sheet record list` | `--id` `--table-id` | 查询记录；支持 `--filter`/`--fields`/`--view-id`/`--page-token`/`--limit`（每页返回记录数，映射后端 pageSize；`data.pageToken` 非空时继续翻页）/`--text-value` |
| `sheet record create` | `--id` `--table-id` `--records` | 创建记录，`--records` 为 JSON 数组 |
| `sheet record update` | `--id` `--table-id` `--records` | 更新记录，`--records` 为 JSON 数组（每项含 `id`） |
| `sheet record delete` | `--id` `--table-id` `--record-ids` `--yes` | 删除记录，`--record-ids` 为逗号分隔的记录 ID（⚠️ 不可恢复，须用户确认后加 `--yes`） |

**`--records` / `--record-ids` 格式**（注意各子命令不同）：
- create：`--records '[{"fieldsValue": {"字段名": "值", ...}}]'`（不传 id，系统分配；自动字段不传）
- update：`--records '[{"id": "记录ID", "fieldsValue": {"字段名": "新值"}}]'`（只传要改的字段）
- delete：`--record-ids rec_abc,rec_def`（逗号分隔的记录 ID，非 JSON）

`fieldsValue` 的 key 必须与 schema 的 `fields[].name` 一致，值格式见上文「字段值格式」。

**`--filter` 结构**（list）：

```json
{"mode": "AND", "criteria": [{"field": "字段名", "operator": "操作符", "values": ["值"]}]}
```

`mode`：`AND` / `OR`（默认 AND）。常用 `operator`：`Equals`、`NotEqu`、`Greater`、`GreaterEqu`、`Less`、`LessEqu`、`GreaterEquAndLessEqu`（2 值）、`BeginWith`、`EndWith`、`Contains`、`NotContains`、`Intersected`、`Empty`（不传 values）、`NotEmpty`（不传 values）。同一字段不可定义多个条件。

**分页**：`list` 的 `data.pageToken` 非空说明还有更多数据，用它作为 `--page-token` 继续查询；`data.list[].id` 用于后续 `update`/`delete`。

> Windows（cmd/PowerShell）不支持单引号包裹 JSON，需用双引号并将内部引号转义为 `\"`（见上方命令速查示例）。

## 浏览与管理多维表格（复用 `doc` 命令）

多维表格是 `fileSuffix=dbt` 的文档节点，**列表/重命名/移动/删除都用 `doc` 命令**（`sheet` 域不重复定义）。参数细节见 [doc.md](./doc.md)。

```bash
# 列出知识库下的节点，多维表格 = 返回项中 fileSuffix == "dbt"
yzj-cli doc list --workspace <KB_ID>

# 新建父文档（用于归类多维表格）
yzj-cli doc create --workspace <KB_ID> --title "2024季度数据"
# 之后用返回的 id 作为 --parent 创建子级，或用 doc move 把已有表挪进去

# 重命名多维表格
yzj-cli doc rename --id <DOC_ID> --title "新表名"

# 移动到其它父文档下
yzj-cli doc move --id <DOC_ID> --target-parent-id <PARENT_DOC_ID>

# 删除多维表格（⚠️ 不可恢复，须用户确认后加 --yes）
yzj-cli doc delete --id <DOC_ID> --yes
```

要点：
- `doc list` 返回的是知识库**根级**一层节点（otl 文档、dbt 多维表），需自行按 `fileSuffix == "dbt"` 过滤出多维表格；要看某个父文档下的子节点用 `doc list --workspace <KB_ID> --parent-id <PARENT_DOC_ID>`。
- `doc create` 可建一个文档作为父节点用于归类；返回的节点 `id` 可作为 `sheet create --parent` 或 `doc move --target-parent-id` 的入参。
- `<DOC_ID>` 即多维表格的节点 ID，从 `doc list` 结果的 `id` 取，同一个 ID 也用于 `sheet get`。
- `doc delete` 不可恢复，属危险操作，须先展示「目标名称 + ID」并获得用户确认。

## 文档链接返回

执行以下命令后，**必须**拼接多维表格链接并返回给用户：

- `sheet create` — 创建多维表格后
- `sheet table create` — 创建数据表后
- `sheet record create` — 新增记录后
- `sheet record update` — 更新记录后

```
https://www.yunzhijia.com/knowledge/lingee/#/store/doc/<DOC_ID>
```

- `<DOC_ID>` 取命令返回的多维表格节点 ID
- 示例：节点 ID `6a684c293814fd27380acc8e` → `https://www.yunzhijia.com/knowledge/lingee/#/store/doc/6a684c293814fd27380acc8e`

## 说明

- `sheet create` 创建的是多维表格文件节点（`fileSuffix=dbt`）；在线文档请用 `doc create`。
- 节点级浏览与管理（列表/重命名/移动/删除）复用 `doc` 命令，详见上文「浏览与管理多维表格」。
- 字段类型与值格式的完整规格（各类型的 `data` 配置、筛选操作符等）以服务端 `WPS在线文档API对接文档` 为准。
