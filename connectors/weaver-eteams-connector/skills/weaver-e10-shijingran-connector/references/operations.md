# 事井然查询与元数据 operation

## 何时使用

用于项目/任务列表、详情、字典、应用/表单元数据和应用版本诊断。

明确查询意图直接按本文对应小节执行。已知出厂字段先查下方 quick reference；不要为了确认这些稳定字段名调用 `project.form.fields`。只有在自定义字段、关联字段、字典选项或写入语义不确定时，才读取 `field-resolution.md` 并调用元数据 operation。

## 出厂字段 quick reference

`project.task.list` / `project.project.list` 的业务记录位于 `data.datas[].mainTable`。以下字段为出厂稳定字段，可直接使用。"适用"列标"通用"表示任务和项目共用同一字段名。

| 字段名 | 语义 | 适用 | 查询输入 | 输出形态 |
| --- | --- | --- | --- | --- |
| `task_name` | 任务名称 | 任务 | 顶层 `name`，模糊匹配 | 字符串 |
| `proj_name` | 项目名称 | 项目 | 顶层 `name`，模糊匹配 | 字符串 |
| `task_desc` | 任务描述 | 任务 | 顶层 `description`，模糊匹配 | 字符串 |
| `proj_desc` | 项目描述 | 项目 | 顶层 `description`，模糊匹配 | 字符串 |
| `project` | 所属项目 | 任务 | `filters.project`，项目 ID | `[{name,id}]` |
| `parent_node` | 父任务/父项目 | 通用 | `filters.parent_node`，对应 ID | 字符串或关联对象 |
| `manager` | 负责人 | 通用 | `filters.manager`，人员 ID | `[{name,id}]` |
| `participant` | 参与人 | 任务 | `filters.participant`，人员 ID | `[{name,id}]` |
| `participants` | 参与人 | 项目 | `filters.participants`，人员 ID | `[{name,id}]` |
| `tester` | 测试负责人 | 任务 | `filters.tester`，人员 ID | `[{name,id}]` |
| `customer_manager` | 客户经理 | 项目 | `filters.customer_manager`，人员 ID | `[{name,id}]` |
| `acceptance_manager` | 验收负责人 | 项目 | `filters.acceptance_manager`，人员 ID | `[{name,id}]` |
| `task_type` | 任务类型 | 任务 | `filters.task_type`，字典 ID | `[{name,id}]` |
| `proj_type` | 项目类型 | 项目 | `filters.proj_type`，字典 ID | `[{name,id}]` |
| `task_status` | 业务任务状态 | 任务 | `filters.task_status`，字典 ID | `[{name,id}]` |
| `proj_status` | 业务项目状态 | 项目 | `filters.proj_status`，字典 ID | `[{name,id}]` |
| `sys_status` | 系统状态 | 通用 | `filters.sys_status`，`todo`/`doing`/`pause`/`terminated`/`finished` | 系统值 |
| `priority` | 紧急程度 | 通用 | `filters.priority`，字典 ID | `[{name,id}]` |
| `progress` | 进度 | 通用 | `filters.progress`，精确匹配 | 字符串或数字 |
| `plan_start_time` | 计划开始时间 | 通用 | `filters.plan_start_time`，精确匹配 | 字符串 |
| `plan_finish_time` | 计划完成时间 | 通用 | `filters.plan_finish_time`，精确匹配 | 字符串 |
| `create_time` | 创建时间 | 通用 | 通常不作为过滤条件 | 字符串 |

- 人员/关联字段查询必须传 ID 字符串；展示取 `name`，不展示内部 ID。
- `sys_status` 传英文值；`task_status`/`proj_status` 传字典 ID；用户给出业务状态时只传业务状态字段。
- 自定义字段仍需实时调用 `project.form.fields` 确认，不要从 quick reference 猜测。

## 当前用户“我负责 / 我参与”模板

用户明确说“我负责”“我名下”“我参与”时使用；不要先执行 `auth status`，也不要调用 `project.employee.resolve` 解析当前用户。直接把 `@me` 传给人员过滤字段，CLI 会替换成当前登录用户 ID。

- “我负责的任务/项目”用 `filters.manager="@me"`。
- “我参与的任务”用 `filters.participant="@me"`；“我参与的项目”用 `filters.participants="@me"`。
- 用户只说“我的任务/我的项目”时，默认按 `manager` 查询并在结果前说明口径；明确要参与人时再改用上面对应字段。

查询我负责的任务：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json project run project.task.list --input-json '{"filters":{"manager":"@me"},"pageNo":1,"pageSize":10,"withDetailUrl":false,"fields":["task_name","task_type","task_status","manager","plan_finish_time","progress"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json project run project.task.list --input-json '{"filters":{"manager":"@me"},"pageNo":1,"pageSize":10,"withDetailUrl":false,"fields":["task_name","task_type","task_status","manager","plan_finish_time","progress"]}'
```

## 任务与项目查询

- `project.task.list`：`filters` 是源接口 `mainTable` 过滤对象；`name`/`description` 走 URL Query 模糊匹配；默认 `pageNo=1`、`pageSize=10`。
- `project.task.detail`：仅传 `id`，可用 `fields` 裁剪输出。
- `project.project.list`：语义同任务列表，项目名称/描述字段由 CLI 映射为 `proj_name`/`proj_desc`。
- `project.project.detail`：仅传 `id`，可用 `fields` 裁剪输出。

默认状态和分页：

- 未指定状态时，CLI 自动增加 `sys_status="todo,doing"`，即只查未开始和进行中；向用户说明这个口径。
- 用户指定业务状态时，先把状态名称解析为字典 ID，再传 `task_status` / `proj_status`；此时不要传 `sys_status`。
- 用户要求全部状态时传 `{"allStatuses":true}`，CLI 不传系统状态和业务状态；不要把五个 `sys_status` 值拼成一个字符串。
- 返回条数等于 `pageSize` 时可能还有下一页；先提示，不自动翻页或扩大 `pageSize`。
- 普通列表、详情回查、大结果或上下文敏感场景都传 `fields`，例如任务列表 `["task_name","task_type","plan_start_time","plan_finish_time","manager","task_status","progress","create_time","detail_url"]`；CLI 会保留 `id` 和记录名称字段，裁掉其他原始字段。只有 `fields` 包含 `detail_url` 时才解析详情链接。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json project run project.task.list --input-json '{"pageNo":1,"pageSize":10,"fields":["task_name","task_type","plan_start_time","plan_finish_time","manager","task_status","progress","create_time","detail_url"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json project run project.task.list --input-json '{"pageNo":1,"pageSize":10,"fields":["task_name","task_type","plan_start_time","plan_finish_time","manager","task_status","progress","create_time","detail_url"]}'
```

## 详情链接

- `project.task.list`、`project.project.list`、`project.task.detail`、`project.project.detail` 默认为有记录 ID 的业务数据补充 `detail_url`；传 `fields` 且不包含 `detail_url` 时，CLI 不生成链接，也不调用对象 ID 接口。
- 任务列表用 `data.datas[].mainTable[].detail_url` 把 `task_name` 渲染为 `[名称](detail_url)`；项目列表用同一位置渲染 `proj_name`。
- 任务详情用 `data.datas[0].mainTable.detail_url` 把 `task_name` 渲染为 `[名称](detail_url)`；项目详情用同一位置渲染 `proj_name`。
- 若返回 `detail_url_warning`，说明主查询已成功但链接暂不可用；如实提示，不重试主查询，不编造 URL。
- 需要最高执行效率时（只做摘要、计数、筛选或名称转 ID），传 `withDetailUrl:false`，或在 `fields` 中不包含 `detail_url`；仅当用户会点开详情或明确要链接时保留默认的详情链接。

## 字典查询

- `project.dictionary.task-type`
- `project.dictionary.task-priority`
- `project.dictionary.task-status`
- `project.dictionary.project-type`
- `project.dictionary.project-priority`
- `project.dictionary.project-status`

输入为 `filters`、`pageNo`、`pageSize`；默认每页 100 条。创建/编辑时应优先选择启用项。

## 元数据与版本

- `project.app.ids`：无输入，返回当前环境应用 ID。
- `project.object.id`：输入 `table: task|project`。
- `project.form.fields`：输入 `table`，可选 `groupId`、`sourceId`、`detailFieldsGroup`、`enableMerge`；可用 `fieldKeyword` 按字段显示名/字段名过滤，或用 `fieldNames` 精确过滤。仅用于自定义/未知字段、关联字段配置或异常排查，不用于确认 quick reference 中的稳定出厂字段。
- `project.form.options`：输入 `table`、`fieldName`，可选 `groupId`、`sourceId`、`optionLevel`。
- `project.form.data.page`：见字段解析 reference。
- `project.version.check`：可选 `appId`；正常路径不要调用，仅用于接口异常诊断或用户主动询问版本。

`project.form.fields` 可能返回很大的 JSON。业务数据在 envelope 的 `data.data[].fields[]`，字段对象包含 `name`、`text`、`compType`、`config` 等信息。优先传 `fieldKeyword`（如 `自定义`）或 `fieldNames` 缩小返回范围；不要把原始 JSON 全量粘贴给用户。

## 大结果落盘与 Node 解析

`project.form.fields` 优先用 `fieldKeyword` / `fieldNames` 服务端输出过滤；只有仍需复杂二次筛选时落盘。普通任务列表可直接读取工具输出并摘要。不要依赖 `grep`、`head`、`wc` 等 shell 工具。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json project run project.form.fields --input-json '{"table":"task","fieldKeyword":"自定义"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json project run project.form.fields --input-json '{"table":"task","fieldKeyword":"自定义"}'
```

临时文件只保存业务 JSON，不保存认证信息。解析完成后按宿主规则清理，不在回复中输出完整字段清单。

## 输出处理

- CLI 输入优先用 `fields` 对齐默认展示，不要拉回全部原始字段；读取成功后只向用户摘要业务字段和记录数。
- 任务列表必须且仅默认展示 `task_name`、`task_type`、`plan_start_time`、`plan_finish_time`、`manager`、`task_status`、`progress`、`create_time`；`task_name` 渲染为 `[名称](detail_url)`，不单独输出 `detail_url` 列。
- 任务详情必须且仅默认展示 `task_name`、`task_type`、`project`、`manager`、`task_status`、`progress`、`plan_start_time`、`plan_finish_time`、`task_desc`、`create_time`；`task_name` 渲染为 `[名称](detail_url)`，不单独输出 `detail_url` 列。
- 项目列表必须且仅默认展示 `proj_name`、`proj_type`、`plan_start_time`、`plan_finish_time`、`manager`、`proj_status`、`progress`、`create_time`；`proj_name` 渲染为 `[名称](detail_url)`，不单独输出 `detail_url` 列。
- 项目详情必须且仅默认展示 `proj_name`、`proj_type`、`priority`、`manager`、`proj_status`、`progress`、`plan_start_time`、`plan_finish_time`、`proj_desc`、`create_time`；`proj_name` 渲染为 `[名称](detail_url)`，不单独输出 `detail_url` 列。
- 用户明确指定展示字段时，以用户指定为准，但仍不要罗列全部原始字段。
- 关联字段返回 `[{name,id}]` 时展示 `name`，不展示内部 ID。
- 明确说明默认状态口径；返回条数等于 `pageSize` 时提示可能有下一页。

## 失败处理

- `endpoint_not_found`、结构不符或语义为接口不存在时，可调用一次 `project.version.check`。
- 版本低于 `20.6.11`：提示升级，不重试原接口。
- 权限不足、数据校验错误、空结果不是版本问题，按原始错误处理。
