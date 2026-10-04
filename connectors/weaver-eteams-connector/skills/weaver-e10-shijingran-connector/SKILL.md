---
name: weaver-e10-shijingran-connector
description: 泛微E10事井然项目管理助手，覆盖项目和任务的创建、查询、修改、删除操作，以及项目/任务类型、紧急程度、状态等字典查询。当用户需要创建/管理项目或任务时触发使用。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
display_name: 泛微E10事井然项目管理
display_name_en: Weaver E10 Shijingran Project Management
description_zh: 泛微E10事井然项目管理助手，封装项目和任务的创建、查询、修改、删除操作，并提供项目/任务类型、紧急程度、状态等字典查询能力。适用于在对话中通过 Agent 创建、查询、修改、删除项目或任务等场景。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。
description_en: Weaver E10 Shijingran project management assistant. Covers CRUD operations for projects and tasks, and provides dictionary queries for project/task types, priorities, and statuses. Used when an Agent needs to create, query, modify, or delete projects or tasks in conversation. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint.
version: 1.0.7
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
cliHelp: "weaver-work-cli project --help"
---

# 泛微E10事井然项目管理

## 适用场景（何时使用本技能）

用户要创建、查询、修改或删除事井然项目与任务，或查项目/任务的类型、状态、紧急程度等字典时使用本技能。

用户处理的是流程审批、组织人员或发票时，转对应业务技能，不在本技能范围。

## CRITICAL：共享规则

先读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。

## 路由

命中以下意图时按表路由到对应 operation 和 reference；不要为了普通查询执行 `project schema`、`project.version.check`、`project.form.fields` 或读取非必要 reference。

| 意图 | operation | reference | 备注 |
| --- | --- | --- | --- |
| 查询任务/项目列表 | `project.task.list` / `project.project.list` | [operations.md](references/operations.md) | `@me` 直接传 `filters.manager` / `filters.participant(s)` |
| 查询任务/项目详情 | `project.task.detail` / `project.project.detail` | [operations.md](references/operations.md) | |
| 查询任务/项目类型、状态、优先级 | `project.dictionary.*` | [operations.md](references/operations.md) | |
| 应用/对象 ID、字段定义、字段选项 | `project.app.ids`、`project.object.id`、`project.form.fields`、`project.form.options` | [operations.md](references/operations.md) | 仅自定义字段或异常排查 |
| 关联表单按名称查记录 | `project.form.data.page` | [field-resolution.md](references/field-resolution.md) | |
| 按姓名解析员工/部门/分部 | `project.employee/department/subcompany.resolve` | [field-resolution.md](references/field-resolution.md) | 多个匹配必须让用户选择 |
| 版本异常诊断 | `project.version.check` | [operations.md](references/operations.md) | 仅接口异常或用户主动询问 |
| 创建/修改/删除任务或项目 | `project.task/*`、`project.project/*` 的 prepare/apply | [write-operations.md](references/write-operations.md) | 严格 prepare → apply |

## 高优先级语义

- 事井然、项目管理、项目、任务、待办任务、任务列表、项目列表、任务详情、项目详情。
- 我负责的任务、我参与的任务、我负责的项目、我参与的项目、所属项目、父任务、父项目。
- 创建/新建项目或任务、修改/编辑项目或任务、删除项目或任务。
- 任务类型、任务状态、任务紧急程度/优先级、项目类型、项目状态、项目优先级。
- 负责人、参与人、测试负责人、客户经理、验收负责人、所属部门、所属分部、关联表单字段。

## 处理链

1. 判断用户目标对象和最小必要条件，按路由读取最小必要 reference；已知出厂字段直接使用 `operations.md` 的字段 quick reference。
2. 名称条件先解析为 ID；0 个匹配要告知，多个匹配必须让用户选择，不得猜。
3. 查询默认第 1 页 10 条；返回条数等于 pageSize 时提示可能还有更多，等待用户要求再翻页。
4. 列表和详情中不要单独输出 `detail_url` 列；将 `task_name` / `proj_name` 渲染为 Markdown 链接（方括号内为记录名称，紧跟的圆括号内为 `detail_url` 的取值）。链接不可用时名称保持纯文本并如实说明，不得编造 URL。
5. 写操作先 `prepare`，向用户摘要目标、差异、风险、默认值和不可逆性；用户明确确认后才 `apply`。
6. `partial/write_uncertain`、登录失效、回查失败或网络中断时停止写流程，不自动重试。

## 执行原则

- 业务调用统一使用 `weaver-work-cli --profile eteams --json project run <operation>`，优先 `--input-json`；复杂多行 JSON 用 UTF-8 文件和 `--input <path>`。
- 列表展示只保留用户所需字段；普通列表也用 `fields` 对齐展示列，不要拉回全部原始字段；关联类字段取 `name`，不展示内部 ID。
- 同一会话已确认 CLI 可用、登录态有效且字段语义无变化时，不要重复执行版本、认证或 schema 诊断；“我负责/我参与”直接使用 `@me`；同一会话已解析的名称→ID、字典 ID、对象 ID 直接复用。
- 大结果需要检查时先用 operation 内置过滤/裁剪参数，必要时再落盘为 UTF-8 JSON 并用 Node 解析；不要依赖 `grep`、`head`、`wc` 等 shell 工具。仅做摘要、统计、筛选或名称转 ID 时，优先 `withDetailUrl:false` 和 `fields` 裁剪输出；`fields` 不含 `detail_url` 时可少一次链接解析请求。
- 不要把接口原始路径、Cookie、ETEAMSID或 Token 作为用户可执行步骤。
- 接口异常后才调用版本诊断；版本低于 `20.6.11` 时提示升级，不重试原接口。

## 写操作失败决策树

1. `apply` 缺少 `confirm: true` 或 continuation：停止，重新执行 `prepare` 并取得用户确认。
2. `target_changed`：目标已变化，重新回查并重新 `prepare`。
3. `partial/write_uncertain`：停止，不重试写入；先执行只读详情/列表回查。
4. 登录失效：按共享规则处理登录，不得使用旧 continuation 直接重试。
5. 回查失败：向用户说明结果不确定，等待用户决策。

## 不在范围

- 禁止绕过 `weaver-work-cli` 直接调用 E10 原始接口。
- 不提供附件上传；`attachment` 只接受已上传文件 ID，且处理文件前必须取得用户敏感数据确认。
- 不自动替用户选择同名人员、组织、项目、任务或字典选项。
- 不自动翻页、自动扩大 pageSize 或自动聚合全量数据。
- 不在正常路径预调用版本诊断。
