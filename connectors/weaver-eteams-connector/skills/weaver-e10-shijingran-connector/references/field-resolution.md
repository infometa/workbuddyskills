# 事井然字段值解析

## 何时使用

仅在以下情况读取本文：

- 用户以名称描述人员、部门、分部、项目、任务、Ebuilder 关联或选择类字段，需要名称转 ID。
- 字段是自定义字段、字段名不在 `operations.md` quick reference 中，或字段语义不确定。
- 需要读取关联字段配置、字典选项或写入字段约束。

已知出厂字段直接使用 `operations.md` 的 quick reference，不要先拉全量表单 schema。解析结果仅在当前会话或当前任务内复用；不要写入持久缓存。

## 通用规则

- ID 一律按字符串传递，避免大整数精度丢失。
- 人员、组织、Ebuilder 关联的纯数字值长度通常大于等于 10 位；已确认是 ID 时直接使用，不要重新解析。
- 多个 ID 用英文逗号拼接且无空格，例如 `"id1,id2"`；不要传 JSON 数组。
- 名称转 ID 结果、字典 ID、`groupId`、当前表对象 ID、`refObjId` 和标题字段 `dataKey` 在同一会话内复用；同一名称不要重复解析。
- 不要用字段显示文本、`text` 或中文名称代替字段名 `name`。

## 人员与组织

- `project.employee.resolve`：输入 `name`、`match: exact|fuzzy`、`status: normal|all`；默认精确匹配在职员工。
- `project.department.resolve`：输入 `name`、`match`。
- `project.subcompany.resolve`：输入 `name`、`match`。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json project run project.employee.resolve --input-json '{"name":"张三","match":"exact"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json project run project.employee.resolve --input-json '{"name":"张三","match":"exact"}'
```

0 个匹配时告知用户；1 个匹配取 `id`；多个匹配列出名称和组织信息让用户选择。多选字段先把每个名称分别解析，再用英文逗号拼接 ID。

用户明确说“我负责”“我参与”时，不需要按姓名解析自己，也不需要执行 `auth status`：直接传 `@me`，CLI 会自动解析为当前登录人。查询过滤用于 `manager`、`participant`、`participants`，写入用于 `manager`。

## 项目与任务名称转 ID

`project` 字段引用项目 ID，`parent_node` 在任务表引用任务 ID、在项目表引用父项目 ID。

| 字段 | 所属表 | 解析目标 | 查询 operation | 名称过滤 |
| --- | --- | --- | --- | --- |
| `project` | task | 项目 ID | `project.project.list` | `name`（映射到 `proj_name`） |
| `parent_node` | task | 任务 ID | `project.task.list` | `name`（映射到 `task_name`） |
| `parent_node` | project | 项目 ID | `project.project.list` | `name`（映射到 `proj_name`） |

解析步骤：

1. 使用用户提供的名称作为顶层 `name` 模糊查询，`pageNo=1`、`pageSize=10`。
2. 从 `data.datas[].mainTable` 匹配名称；关联对象输出取 `name`，记录 ID 取 `id`。
3. 0 个匹配时告知用户；1 个匹配取 `id`；多个匹配列出名称、计划时间和负责人让用户选择。
4. 将记录 ID 作为字段值填入写入或过滤条件。

示例（解析项目名称“需求评审”）： 

```powershell
weaver-work-cli --profile eteams --json project run project.project.list --input-json '{"name":"需求评审","pageNo":1,"pageSize":10}'
```

```bash
weaver-work-cli --profile eteams --json project run project.project.list --input-json '{"name":"需求评审","pageNo":1,"pageSize":10}'
```

不要为了按名称解析项目或任务而调用 `project.form.fields`。

## Ebuilder 关联字段

1. `project.form.fields` 获取当前表字段定义，找到目标字段的 `config.refObjId` 和 `config.dataTitle`。
2. 再次调用 `project.form.fields` 时把 `sourceId` 设为 `config.refObjId`，找到 `id=config.dataTitle` 的字段并取其 `config.dataKey` 作为 `fieldKey`。
3. `project.form.data.page` 输入 `refObjId=config.refObjId`、`fieldKey`、`value=用户名称`。
4. 取响应 `datas[0].mainTable.id.fieldValue` 作为业务字段 ID；多条匹配让用户选择。

`project.form.fields` 返回较大时，先保存为 UTF-8 JSON，再用 Node 解析 envelope 的 `data.data[].fields[]`；不要依赖 `grep`、`head`、`wc`。解析示例见 `operations.md` 的“大结果落盘与 Node 解析”。

## Select 与字典字段

`task_type`、`task_status`、`priority`、`proj_type`、`proj_status` 等字典类字段优先使用 `project.dictionary.*`：

| 字段 | 字典 operation |
| --- | --- |
| `task_type` | `project.dictionary.task-type` |
| `task_status` | `project.dictionary.task-status` |
| `priority`（任务） | `project.dictionary.task-priority` |
| `proj_type` | `project.dictionary.project-type` |
| `proj_status` | `project.dictionary.project-status` |
| `priority`（项目） | `project.dictionary.project-priority` |

1. 用默认或较大 `pageSize` 查询字典。
2. 按用户输入名称匹配字典记录的名称字段，取记录 `id`。
3. 优先选择启用项；多个相近选项无法区分时让用户选择。
4. 解析出的业务状态 ID 传给 `task_status` / `proj_status`，不要再传 `sys_status`。

非字典 Select 字段（如约束类型、排程模式、验收进展）已有出厂枚举；先使用源资料/CLI reference 中的枚举映射。只有枚举无法确认时才用 `project.form.fields` 找字段元数据 `id`，再用 `project.form.options` 查询。

## 注意

- 解析结果只在当前任务内复用；同名或歧义必须重新让用户确认。
- 不要把全量 schema 或原始认证响应粘贴给用户。
- 解析失败时不要猜 ID；把候选或缺口告诉用户。
