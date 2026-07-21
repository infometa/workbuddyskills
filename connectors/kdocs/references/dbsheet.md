# 多维表格（dbt）工具完整参考文档

本文件包含金山文档 Skill 多维表格的操作说明。

---

## 一、数据表管理

> 数据表的 Schema 查询、增删改与批量操作

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.get_schema`](dbsheet/data_table.md) | 获取文档结构（表/字段/视图） | `file_id` |
| [`dbsheet.create_sheet`](dbsheet/data_table.md) | 创建数据表 | `file_id`, `name` |
| [`dbsheet.update_sheet`](dbsheet/data_table.md) | 修改数据表名称 | `file_id`, `sheet_id` |
| [`dbsheet.delete_sheet`](dbsheet/data_table.md) | 删除数据表 | `file_id`, `sheet_id` |
| [`dbsheet.sheet_batch_create`](dbsheet/data_table.md) | 批量创建工作表 | `file_id`, `body` |
| [`dbsheet.sheet_batch_delete`](dbsheet/data_table.md) | 批量删除工作表 | `file_id`, `body` |

## 二、视图管理

> 视图的增删改查与列表

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_view`](dbsheet/view.md) | 创建视图 | `file_id`, `sheet_id`, `name`, `type` |
| [`dbsheet.update_view`](dbsheet/view.md) | 更新视图配置 | `file_id`, `sheet_id`, `view_id` |
| [`dbsheet.delete_view`](dbsheet/view.md) | 删除视图 | `file_id`, `sheet_id`, `view_id` |
| [`dbsheet.views_list`](dbsheet/view.md) | 列出视图 | `file_id`, `sheet_id` |
| [`dbsheet.views_get`](dbsheet/view.md) | 获取单个视图 | `file_id`, `sheet_id`, `view_id` |

## 三、字段管理

> 字段的增删改

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_fields`](dbsheet/field.md) | 批量创建字段 | `file_id`, `sheet_id`, `fields` |
| [`dbsheet.update_fields`](dbsheet/field.md) | 批量更新字段 | `file_id`, `sheet_id`, `fields` |
| [`dbsheet.delete_fields`](dbsheet/field.md) | 批量删除字段 | `file_id`, `sheet_id`, `fields` |

## 四、记录操作

> 记录的增删改查

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.create_records`](dbsheet/record.md) | 批量创建记录 | `file_id`, `sheet_id`, `records` |
| [`dbsheet.update_records`](dbsheet/record.md) | 批量更新记录 | `file_id`, `sheet_id`, `records` |
| [`dbsheet.list_records`](dbsheet/record.md) | 分页遍历记录（支持筛选） | `file_id`, `sheet_id` |
| [`dbsheet.get_record`](dbsheet/record.md) | 获取单条记录 | `file_id`, `sheet_id`, `record_id` |
| [`dbsheet.delete_records`](dbsheet/record.md) | 批量删除记录 | `file_id`, `sheet_id`, `records` |
| [`dbsheet.records_list`](dbsheet/record.md) | 列举记录 | `file_id`, `sheet_id`, `fields` |
| [`dbsheet.records_search`](dbsheet/record.md) | 检索多条记录 | `file_id`, `sheet_id`, `records` |

## 五、表单视图

> 表单视图的元数据与字段管理

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.form_list_fields`](dbsheet/form.md) | 列出表单问题 | `file_id`, `sheet_id`, `view_id` |
| [`dbsheet.form_update_field`](dbsheet/form.md) | 更新表单问题 | `file_id`, `sheet_id`, `view_id`, `field_id`, `body` |
| [`dbsheet.form_get_meta`](dbsheet/form.md) | 获取表单元数据 | `file_id`, `sheet_id`, `view_id` |
| [`dbsheet.form_update_meta`](dbsheet/form.md) | 更新表单元数据 | `file_id`, `sheet_id`, `view_id`, `body` |

## 六、父子记录

> 层级关系的绑定、解绑、状态与列表

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.parent_disable`](dbsheet/parent_child.md) | 禁用父子关系（仅前端） | `file_id`, `sheet_id` |
| [`dbsheet.parent_enable`](dbsheet/parent_child.md) | 启用父子关系（仅前端） | `file_id`, `sheet_id` |
| [`dbsheet.parent_status`](dbsheet/parent_child.md) | 查询父子关系是否禁用 | `file_id`, `sheet_id` |
| [`dbsheet.parent_bind_children`](dbsheet/parent_child.md) | 绑定父子记录 | `file_id`, `sheet_id`, `parent_id`, `body` |
| [`dbsheet.parent_list_children`](dbsheet/parent_child.md) | 查询子记录列表 | `file_id`, `sheet_id`, `parent_id` |
| [`dbsheet.parent_unbind_children`](dbsheet/parent_child.md) | 解绑父子记录 | `file_id`, `sheet_id`, `parent_id`, `body` |

## 七、分享视图

> 视图分享的开启、关闭、权限、状态

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.share_open_view`](dbsheet/share.md) | 打开分享视图 | `file_id`, `sheet_id`, `view_id`, `body` |
| [`dbsheet.share_view_status`](dbsheet/share.md) | 查询视图是否已开启分享 | `file_id`, `sheet_id`, `view_id` |
| [`dbsheet.share_get_link_info`](dbsheet/share.md) | 查询分享链接信息 | `file_id`, `sheet_id`, `view_id`, `share_id` |
| [`dbsheet.share_close_view`](dbsheet/share.md) | 关闭分享视图 | `file_id`, `sheet_id`, `view_id`, `share_id` |
| [`dbsheet.share_get_repeatable`](dbsheet/share.md) | 查询表单是否可重复提交 | `file_id`, `sheet_id`, `view_id`, `share_id` |
| [`dbsheet.share_set_repeatable`](dbsheet/share.md) | 设置表单是否可重复提交 | `file_id`, `sheet_id`, `view_id`, `share_id`, `body` |
| [`dbsheet.share_update_permission`](dbsheet/share.md) | 修改分享权限 | `file_id`, `sheet_id`, `view_id`, `share_id`, `body` |

## 八、高级权限

> 角色与主体的权限管理与异步任务

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.permission_list_roles`](dbsheet/permission.md) | 列举自定义角色 | `file_id` |
| [`dbsheet.permission_query_task`](dbsheet/permission.md) | 获取异步任务结果 | `file_id`, `task_id`, `task_type` |
| [`dbsheet.permission_create_roles_async`](dbsheet/permission.md) | 新增自定义角色（异步） | `file_id`, `body` |
| [`dbsheet.permission_update_roles_async`](dbsheet/permission.md) | 更新自定义角色（异步） | `file_id`, `body` |
| [`dbsheet.permission_delete_roles_async`](dbsheet/permission.md) | 删除自定义角色（异步） | `file_id`, `body` |
| [`dbsheet.permission_list_subjects`](dbsheet/permission.md) | 列举成员（内容权限） | `file_id`, `cloud_permission_id`, `permission_type` |

## 九、仪表盘

> 仪表盘的列表与复制

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.dashboard_copy`](dbsheet/dashboard.md) | 复制仪表盘 | `file_id`, `dashboard_id`, `body` |
| [`dbsheet.dashboard_list`](dbsheet/dashboard.md) | 列出仪表盘 | `file_id` |

## 十、Webhook 与开放协作

> Webhook 的创建、列表、删除

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`dbsheet.list_webhooks`](dbsheet/webhook.md) | 查询全部 Hook 订阅 | `file_id` |
| [`dbsheet.create_webhook`](dbsheet/webhook.md) | 创建 Hook 订阅 | `file_id`, `body` |
| [`dbsheet.delete_webhook`](dbsheet/webhook.md) | 取消 Hook 订阅 | `file_id`, `hook_id` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 多维表格读结构/数据 | `dbsheet.get_schema` → `dbsheet.list_records` / `dbsheet.get_record` |
| 多维表格增删改 | `dbsheet.get_schema` → `dbsheet.create_records` / `dbsheet.update_records` / `dbsheet.delete_records`|

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
| 多维表格读不到结构化数据 | 误用 `read_file_content` 作主读 | 改用 `dbsheet.get_schema`、`dbsheet.list_records` 等，见 `references/dbsheet.md` |

---

## 附录

### 字段类型

| 类型 | 说明 |
|------|------|
| `SingleLineText` | 单行文本 |
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
