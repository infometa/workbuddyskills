# 事井然写操作确认链

## 何时使用

创建、修改、删除项目或任务时使用。所有写操作必须执行 `prepare -> apply`，不能直接提交。

## 字段与默认值

### 任务创建

- 必填业务字段只有 `task_name`；`records` 至少 1 条、最多 100 条。
- `manager` 未指定或传 `"@me"` 时，CLI 在 prepare 自动填当前登录人 ID，无需先查 userId；要指定他人时，先按 `field-resolution.md` 解析为 ID，并在 prepare 摘要中说明负责人。
- `plan_start_time` / `plan_finish_time` 未指定时留空，业务接口不会注入默认值；在 prepare 摘要中如实说明「不设置计划时间」。
- `project`、`parent_node`、人员、字典和自定义字段需要 ID 时，先按 `field-resolution.md` 解析。

### 项目创建

- 必填业务字段是 `proj_name`；`manager` 未指定或传 `"@me"` 时自动填当前登录人 ID（同任务创建）。
- `plan_start_time` / `plan_finish_time` 未指定时留空，不要声称有默认值。
- `progress` 为 0-100 的数字；不要把百分比符号写入值。

### 通用格式

- 日期时间：`yyyy-MM-dd HH:mm`，例如 `2026-09-14 18:00`。
- 仅验收日期等纯日期字段使用 `yyyy-MM-dd`。
- 多选字段用英文逗号拼接 ID 字符串且无空格，例如 `"id1,id2"`；不要传 JSON 数组。
- 所有 ID 都按字符串传递。
- `sys_status` 是系统维护字段，只能用于查询过滤，不能写入。
- 附件字段只接受已上传文件 ID；本 Skill 不提供附件上传，处理文件前必须取得用户敏感数据确认。

## 创建

`prepare` 输入 `records`，每条记录是源接口 `mainTable` 字段对象。`prepare` 不触网写入，只生成请求预览和 continuation。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json project run project.task.create.prepare --input-json '{"records":[{"task_name":"需求评审"}]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json project run project.task.create.prepare --input-json '{"records":[{"task_name":"需求评审"}]}'
```

向用户摘要记录数、用户提供的字段、准备使用的目标对象、解析后的 ID、接口默认值和不可逆性。用户明确确认后才执行 apply：

```json
{"continuation":"PREPARE_CONTINUATION","confirm":true}
```

## 修改

- `project.task.update.prepare` / `project.project.update.prepare` 输入 `id` 和 `fields`。
- 只传用户明确要求修改的字段；未提及字段保持原值。
- `prepare` 会先回查当前数据并绑定指纹；向用户展示变更前/后差异。
- 若用户用名称指定关联字段，先解析为 ID，再进入 prepare。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json project run project.task.update.prepare --input-json '{"id":"<taskId>","fields":{"progress":50}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json project run project.task.update.prepare --input-json '{"id":"<taskId>","fields":{"progress":50}}'
```

## 删除

- `project.task.delete.prepare` / `project.project.delete.prepare` 仅输入 `id`。
- 删除不可逆；prepare 摘要必须明确说明目标名称、类型和“不可恢复”。
- 用户确认后才能 apply。

## apply 约束

- 必须 `confirm: true`。
- `continuation` 必须原样传入，不得改写、截断或重新生成。
- 修改/删除 apply 前会再次回查；`target_changed` 时必须重新 prepare。
- continuation 与当前登录会话绑定，登录变化后不得复用。

## 失败处理

- `confirmation.required` 或缺少 `confirm`：停止，重新向用户确认。
- `target_changed`：重新回查并重新 prepare。
- `partial/write_uncertain`：禁止重试写入，先只读回查详情或列表。
- 网络中断、登录失效、回查失败：停止写流程并如实告知用户。
