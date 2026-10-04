# 多维表格（dbt）工具完整参考文档

本文件包含金山文档 Skill 多维表格的操作说明。

---

## 一、数据表管理

> 数据表的 Schema 查询、增删改与批量操作

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.get_schema`](dbsheet/data_table.md) | 获取文档结构（表/字段/视图） | `url`\|`link_id`\|`file_id` |
| [`dbsheet.create_sheet`](dbsheet/data_table.md) | 创建数据表 | `url`\|`link_id`\|`file_id`, `name`, `views`, `fields` |
| [`dbsheet.update_sheet`](dbsheet/data_table.md) | 修改数据表名称 | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.delete_sheet`](dbsheet/data_table.md) | 删除数据表 | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.sheet_batch_create`](dbsheet/data_table.md) | 批量创建工作表 | `url`\|`link_id`\|`file_id`, `body` |
| [`dbsheet.sheet_batch_delete`](dbsheet/data_table.md) | 批量删除工作表 | `url`\|`link_id`\|`file_id`, `body` |
| [`dbsheet.get_schema_detail`](dbsheet/data_table.md) | 获取完整 Schema（含侧边栏智能文档和富文本字段的 content_id） | `url`\|`link_id`\|`file_id` |

## 二、视图管理

> 视图的增删改查与列表

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_view`](dbsheet/view.md) | 创建视图 | `url`\|`link_id`\|`file_id`, `sheet_id`, `name`, `type` |
| [`dbsheet.update_view`](dbsheet/view.md) | 更新视图配置 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id` |
| [`dbsheet.delete_view`](dbsheet/view.md) | 删除视图 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id` |
| [`dbsheet.views_list`](dbsheet/view.md) | 列出视图 | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.views_get`](dbsheet/view.md) | 获取单个视图 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id` |

## 三、字段管理

> 字段的增删改

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_fields`](dbsheet/field.md) | 批量创建字段 | `url`\|`link_id`\|`file_id`, `sheet_id`, `fields` |
| [`dbsheet.update_fields`](dbsheet/field.md) | 批量更新字段 | `url`\|`link_id`\|`file_id`, `sheet_id`, `fields` |
| [`dbsheet.delete_fields`](dbsheet/field.md) | 批量删除字段 | `url`\|`link_id`\|`file_id`, `sheet_id`, `fields` |

## 四、记录操作

> 记录的增删改查

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_records`](dbsheet/record.md) | 批量创建记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `records` |
| [`dbsheet.update_records`](dbsheet/record.md) | 批量更新记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `records` |
| [`dbsheet.list_records`](dbsheet/record.md) | 分页遍历记录（支持筛选） | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.get_record`](dbsheet/record.md) | 获取单条记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `record_id` |
| [`dbsheet.delete_records`](dbsheet/record.md) | 批量删除记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `records` |
| [`dbsheet.records_list`](dbsheet/record.md) | 列举记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `fields` |
| [`dbsheet.records_search`](dbsheet/record.md) | 检索多条记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `records` |

## 五、表单视图

> 表单视图的元数据与字段管理

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.form_list_fields`](dbsheet/form.md) | 列出表单问题 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id` |
| [`dbsheet.form_update_field`](dbsheet/form.md) | 更新表单问题 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `field_id`, `body` |
| [`dbsheet.form_get_meta`](dbsheet/form.md) | 获取表单元数据 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id` |
| [`dbsheet.form_update_meta`](dbsheet/form.md) | 更新表单元数据 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `body` |

## 六、父子记录

> 层级关系的绑定、解绑、状态与列表

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.parent_disable`](dbsheet/parent_child.md) | 禁用父子关系（仅前端） | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.parent_enable`](dbsheet/parent_child.md) | 启用父子关系（仅前端） | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.parent_status`](dbsheet/parent_child.md) | 查询父子关系是否禁用 | `url`\|`link_id`\|`file_id`, `sheet_id` |
| [`dbsheet.parent_bind_children`](dbsheet/parent_child.md) | 绑定父子记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `parent_id`, `body` |
| [`dbsheet.parent_list_children`](dbsheet/parent_child.md) | 查询子记录列表 | `url`\|`link_id`\|`file_id`, `sheet_id`, `parent_id` |
| [`dbsheet.parent_unbind_children`](dbsheet/parent_child.md) | 解绑父子记录 | `url`\|`link_id`\|`file_id`, `sheet_id`, `parent_id`, `body` |

## 七、分享视图

> 视图分享的开启、关闭、权限、状态

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.share_open_view`](dbsheet/share.md) | 打开分享视图 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `body` |
| [`dbsheet.share_view_status`](dbsheet/share.md) | 查询视图是否已开启分享 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id` |
| [`dbsheet.share_get_link_info`](dbsheet/share.md) | 查询分享链接信息 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `share_id` |
| [`dbsheet.share_close_view`](dbsheet/share.md) | 关闭分享视图 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `share_id` |
| [`dbsheet.share_get_repeatable`](dbsheet/share.md) | 查询表单是否可重复提交 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `share_id` |
| [`dbsheet.share_set_repeatable`](dbsheet/share.md) | 设置表单是否可重复提交 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `share_id`, `body` |
| [`dbsheet.share_update_permission`](dbsheet/share.md) | 修改分享权限 | `url`\|`link_id`\|`file_id`, `sheet_id`, `view_id`, `share_id`, `body` |

## 八、高级权限

> 角色与主体的权限管理与异步任务

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.permission_list_roles`](dbsheet/permission.md) | 列举自定义角色 | `url`\|`link_id`\|`file_id` |
| [`dbsheet.permission_query_task`](dbsheet/permission.md) | 获取异步任务结果 | `url`\|`link_id`\|`file_id`, `task_id` |
| [`dbsheet.permission_create_roles_async`](dbsheet/permission.md) | 新增自定义角色（异步） | `url`\|`link_id`\|`file_id`, `body` |
| [`dbsheet.permission_update_roles_async`](dbsheet/permission.md) | 更新自定义角色（异步） | `url`\|`link_id`\|`file_id`, `body` |
| [`dbsheet.permission_delete_roles_async`](dbsheet/permission.md) | 删除自定义角色（异步） | `url`\|`link_id`\|`file_id`, `body` |
| [`dbsheet.permission_list_subjects`](dbsheet/permission.md) | 列举成员（内容权限） | `url`\|`link_id`\|`file_id`, `cloud_permission_id`, `permission_type` |

## 九、仪表盘

> 仪表盘的列表与复制

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.dashboard_copy`](dbsheet/dashboard.md) | 复制仪表盘 | `url`\|`link_id`\|`file_id`, `dashboard_id`, `body` |
| [`dbsheet.dashboard_list`](dbsheet/dashboard.md) | 列出仪表盘 | `url`\|`link_id`\|`file_id` |

## 十、Webhook 与开放协作

> Webhook 的创建、列表、删除

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.list_webhooks`](dbsheet/webhook.md) | 查询全部 Hook 订阅 | `url`\|`link_id`\|`file_id` |
| [`dbsheet.create_webhook`](dbsheet/webhook.md) | 创建 Hook 订阅 | `url`\|`link_id`\|`file_id`, `body` |
| [`dbsheet.delete_webhook`](dbsheet/webhook.md) | 取消 Hook 订阅 | `url`\|`link_id`\|`file_id`, `hook_id` |

## 十一、智能文档/富文本字段块操作

> 多维表格智能文档（FlexPaper sheet）与富文本字段内的文档块增删改查与格式转换

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_innerdoc_flexpaper`](dbsheet/innerdoc_block.md) | 在多维表格文件中新建一个智能文档（FlexPaper sheet） | `url`\|`link_id`\|`file_id`, `name` |
| [`dbsheet.innerdoc_block_create`](dbsheet/innerdoc_block.md) | 创建侧边栏智能文档/富文本字段内的文档块 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_query`](dbsheet/innerdoc_block.md) | 查询侧边栏智能文档/富文本字段内的单个文档块 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_list`](dbsheet/innerdoc_block.md) | 批量查询侧边栏智能文档/富文本字段内的文档块列表 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_update`](dbsheet/innerdoc_block.md) | 更新侧边栏智能文档/富文本字段内的单个文档块 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_batch_update`](dbsheet/innerdoc_block.md) | 批量更新侧边栏智能文档/富文本字段内的多个文档块 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_delete`](dbsheet/innerdoc_block.md) | 删除侧边栏智能文档/富文本字段内的单个文档块 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_batch_delete`](dbsheet/innerdoc_block.md) | 批量删除侧边栏智能文档/富文本字段内的多个文档块 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |
| [`dbsheet.innerdoc_block_convert`](dbsheet/innerdoc_block.md) | 将 HTML/Markdown 转换为侧边栏智能文档/富文本字段内的文档块结构 | `url`\|`link_id`\|`file_id`, `attachment_id`, `arg` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 新建多维表 | 自定义列 → `create_file_with_content`（`dbt` + `fields` + `records`）；接受默认列 → `create_empty_file`（`dbt`）→ `get_file_link`（参数与禁令见各工具 reference） |
| 已有 .dbt 内新增数据表 | `dbsheet.create_sheet`（`views` + `fields` 均非空） |
| 读多维表正文 | `read_file`（返回 content_format 为 dbsheet_records，含 schema、records） |
| 多维表格读结构/数据 | `dbsheet.get_schema` → `dbsheet.list_records` / `dbsheet.get_record` |
| 多维表格增删改记录 | 见「写入前字段映射」+「新增记录与全空记录复用」→ `dbsheet.update_records` / `dbsheet.create_records`；用户明确要求删除时 `dbsheet.delete_records` |
| 本地图片/文件写入附件字段 | `upload_attachment`（`file_id` 为目标 `.dbt`）→ `dbsheet.update_records`（`uploadId`=返回的 `object_id`，`source`=`upload_ks3`；勿用 `Cloud`） |
| 智能文档/表格内容转新建 dbt | `read_file` 源文档 → `create_file_with_content`（`name` 只写文件名，`file_extension=dbt`，`fields`+`records`）；选项列见下节 |

### 单选/多选建列（create_fields / create_file_with_content）

向 `.dbt` 预置 `SingleSelect`/`MultipleSelect` 选项时：

1. **扁平 `items`**：写在 `fields[].items`，**禁止** `fields[].data.items`（可 200 但 `items: null`）。
2. 创建后 **`dbsheet.get_schema`** 确认该列 `items` 非空，再 `create_records`/`update_records`。
3. 录入选项 **value** 字符串须与 `items[].value` 一致（或开启 `autoAddItem`）。

`create_file_with_content` 建 dbt 时 `fields[]` 规则相同；详见 `references/dbsheet/field.md` 中 `dbsheet.create_fields`。

### 写入前字段映射

向已有表增/改记录时：

1. **必须先** `dbsheet.get_schema` 确认 `sheet_id` 与字段名；禁止用 `read_file` 探 `sheet_id` 或字段结构。
2. 用户口述的字段名对照 schema **现有列**：**列名完全一致则直接用**。无同名列时 **禁止 Agent 自行语义映射**，须 `askUserQuestion` 让用户选择：写入哪个现有列 / 新建该列 / 跳过；`fields` 的 key 必须用用户确认后的表中真实列名。禁止新建与已有列同义的列。
3. 无等价列且确需新列 → **须 `askUserQuestion` 确认**（新建列 / 跳过该字段 / 写入其他列）后再 `dbsheet.create_fields`；禁止先 `create_records` 写入不存在的列碰运气，`Field not found` 失败后再建列**不算**已告知用户。
4. 映射完成后按「新增记录与全空记录复用」选择 `update_records` / `create_records`；**必须**用 `list_records` 或 `get_record` 回读验证，禁止仅凭 `result: ok` 宣称成功。
5. 回复用户时说明口述字段与表中真实列名的对应关系（如「任务名→文本」「状态→单选项」）；若新建了列须一并说明。

### 新增记录与全空记录复用

向已有表**新增** N 条记录时（用户未明确要求追加到表尾）：

1. `list_records` 按默认顺序盘点记录。
2. **全空记录**：`fields` 为 `{}`，或除 `AutoNumber`/`CreatedTime`/`CreatedBy`/`LastModifiedBy`/`LastModifiedTime`/`Formula`/`Lookup` 外所有字段均为空；任一业务字段有值则**跳过**。
3. 从列表头部依次取前 min(N, 全空记录数) 条 → `update_records`（每条须带 `id`）。
4. 仍有剩余 (N−K) 条 → `create_records` 追加（API 只能在表尾创建，无「插入到第几行」参数）。
5. **禁止**用 `delete_records`（含 `mode=all`）清理全空记录；**禁止**覆盖含用户数据的记录。
6. 不要求连续全空记录；全空记录不足时剩余追加到表尾，须在回复中说明。

用户明确说「在末尾/最后追加」时，可跳过步骤 2–3，直接 `create_records`。

---

## 获取记录工具使用指南

| 场景 | 优先工具 | 备用工具 | 说明 |
|------|----------|----------|------|
| 列举数据表所有 / 分页记录 | `dbsheet.records_list` | `dbsheet.list_records` | `records_list` 基于游标分页；若返回错误，改用 `list_records`（页码分页） |
| 查询数据表中某一条记录 | `dbsheet.get_record` | `dbsheet.records_search` | `get_record` 直接按记录 id GET 查询；返回错误时可改用 `records_search` |
| 批量获取指定多条记录 | `dbsheet.records_search` | — | 传入记录 id 列表一次取回多条，无需逐条查询 |

---

## 错误速查表

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `400100` Unknown enum / 参数值不被识别 | 凭直觉猜测 type 等枚举值，未查文档 | 打开 `references/dbsheet/field.md` 对应工具的参数说明，从 description 中的对照表取正确枚举值，修正后重试一次 |
| `400001` 参数缺失 / 格式错误 | 未确认必填参数或参数类型 | 打开 `references/dbsheet/field.md` 对应工具的参数表，确认参数名、类型、必填性，补齐后重试 |
| 记录不全 / 需全量或分页 | `read_file` 单次返回 records 有上限 | 概览用 `read_file`；全量/分页/条件筛选用 `dbsheet.records_list` / `list_records` / `records_search` |
| `Field not found` / 字段不存在 | `create_records` 传了 schema 中不存在的列名 | 先 `get_schema`；无同名列须 `askUserQuestion` 确认映射或缺列方案，禁止撞错后静默建列 |
| `SingleSelect`/`MultipleSelect` 响应 `items: null` | 误用 `fields[].data.items` 包装 | 改为扁平 `fields[].items`；`get_schema` 验证选项非空 |
| `conflict` / `lock` / 写入冲突 | 并发写入同一数据表的多条记录导致锁竞争 | 指数退避重试（2s → 4s → 8s，最多 3 次）；批量写入时改为串行逐条 `dbsheet.update_records` / `dbsheet.create_records` |
| 新增记录落到表尾很后面 | 表内已有全空记录，直接 `create_records` 只会追加到末尾 | 先 `list_records` 复用全空记录 `update_records`，不足再 `create_records`；见「新增记录与全空记录复用」 |

---

## 附录

### 字段类型

| 类型 | 说明 |
|------|------|
| `MultiLineText` | 多行文本 |
| `Number` | 数值 |
| `Currency` | 货币 |
| `Percentage` | 百分比 |
| `Date` | 日期 |
| `Time` | 时间 |
| `Checkbox` | 复选框 |
| `SingleSelect` | 单选项 |
| `MultipleSelect` | 多选项 |
| `Rating` | 等级 |
| `Complete` | 进度条 |
| `Phone` | 电话 |
| `Email` | 电子邮箱 |
| `Url` | 超链接 |
| `Contact` | 联系人 |
| `Attachment` | 附件 |
| `Link` | 关联 |
| `Note` | 富文本 |
| `Address` | 地址 |
| `AutoNumber` | 编号（自动填充） |
| `CreatedBy` | 创建者（自动填充） |
| `CreatedTime` | 创建时间（自动填充） |
| `LastModifiedBy` | 最后修改者（自动填充） |
| `LastModifiedTime` | 最后修改时间（自动填充） |
| `Formula` | 公式（自动计算） |
| `Lookup` | 引用（自动计算） |

### 视图类型

| 类型 | 说明 |
|------|------|
| `Grid` | 表格视图 |
| `Kanban` | 看板视图 |
| `Gallery` | 画册视图 |
| `Form` | 表单视图 |
| `Gantt` | 甘特视图 |
| `Calendar` | 日历视图 |

### 筛选规则（filter op）

| 操作符 | 适用字段类型 | 说明 |
|--------|-------------|------|
| `Equals` | 通用 | 等于 |
| `NotEqu` | 通用 | 不等于 |
| `Greater` | 数值、日期 | 大于 |
| `GreaterEqu` | 数值、日期 | 大于等于 |
| `Less` | 数值、日期 | 小于 |
| `LessEqu` | 数值、日期 | 小于等于 |
| `BeginWith` | 文本 | 开头是 |
| `EndWith` | 文本 | 结尾是 |
| `Contains` | 文本 | 包含 |
| `NotContains` | 文本 | 不包含 |
| `Intersected` | 单选、多选 | 选项包含指定值 |
| `Empty` | 通用 | 为空（`values` 可省略） |
| `NotEmpty` | 通用 | 不为空（`values` 可省略） |

### 错误响应

| 情况 | 响应示例 |
|------|---------|
| 命令不支持 | `{"msg":"core not support","result":"unSupport"}` |
| 内核错误 | `{"errno":-1880935404,"msg":"Invalid request","result":"ExecuteFailed"}` |
| HTTP 状态非 200 | 请求本身失败，检查 `file_id` 是否正确及鉴权信息 |
