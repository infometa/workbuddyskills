# 新建与编辑目标（okr-write）

新建目标与编辑目标都拆成 `prepare -> apply` 两个 operation，四个 operation 都属于高风险写入，必须经用户明确确认。

| operation | 风险 | 作用 |
| --- | --- | --- |
| `okr.create.prepare` | read-before-write | 归一化输入、补默认值、生成预览与 continuation，**不写入** |
| `okr.create.apply` | high-risk-write | 提交新建目标 |
| `okr.update.prepare` | read-before-write | 先查询当前目标详情并合并修改，生成预览与 continuation，**不写入** |
| `okr.update.apply` | high-risk-write | 提交编辑目标 |

## 入参字段

`prepare` 与对应 `apply` 使用同一组业务字段；`apply` 额外要求 `confirm=true` 与 `continuation`，编辑类 `apply` 还要求显式传 `id`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 目标名称（新建必填） |
| `period_type` | `"1"`..`"4"` | 周期类型（新建必填） |
| `period_range` | string | 周期范围（新建必填，格式随类型变化） |
| `period_quarter` | `"1"`..`"4"` | `period_type=2` 必填 |
| `principalid` | 人员 ID | 责任人，默认当前登录用户 |
| `partners` | 人员 ID 或数组 | 参与人，英文逗号拼接或数组 |
| `scope_id` | `"1"` / `"2"` | 1-个人目标（默认） 2-部门目标 |
| `scope_data_id` | 部门 ID | 标准版链路 `scope_id=2` 必填 |
| `principal_dept` | 部门 ID | ebuilder 链路 `scope_id=2` 必填 |
| `parent_id` | 目标 ID | 上级目标 |
| `category_id` | string | 目标分类 id |
| `remark` | string | 目标描述 |
| `progress` | number | 进度 0-100（ebuilder 新建默认 0） |
| `status` | `"0"` / `"1"` | **标准版**：0-保存草稿（新建默认） 1-正式提交 |
| `m_status` | `"1"`..`"5"` | **ebuilder**：1-进行中（新建默认） 2-已完成 3-已撤销 4-审批中 5-未开始 |
| `wb_state` | `"1"`..`"3"` | **ebuilder** 紧急状态：1-正常 2-紧急 3-非常紧急 |
| `keyresult_list` | array | 随目标一起创建的关键成果（**仅标准版**），元素 `{name, principalid?, weight?, target_value?}` |
| `confirm` | `true` | 仅 `apply`，必须为 `true` |
| `continuation` | string | 仅 `apply`，取自 `prepare` 返回 |

非本链路的字段会被忽略并记入 `meta.notes`（如标准版链路的 `m_status`/`wb_state`/`principal_dept`，ebuilder 链路的 `keyresult_list`）。

## 关键业务规则

- **标准版新建默认草稿**：未传 `status` 时新建默认 `status=0`，不会直接提交为正式目标。
- **标准版编辑必须显式传 `status`**：`update.prepare` 不传 `status` 会返回 `validation/status_required`，避免把正式目标静默回退为草稿。
- **编辑为全量合并**：`update.prepare` 先通过详情接口取回当前目标，再合并用户修改；只读字段（如 `creator`、`img_url`）不回写。
- **ebuilder 新建默认值**：`m_status=1`、`progress=0`。
- **部门目标**：标准版要 `scope_data_id`，ebuilder 要 `principal_dept`，缺失时 prepare 阶段直接阻断。
- **人员 ID**：必须传人员 ID，传姓名会返回 `validation/person_id_invalid` 并指向 weaver-e10-hrm-connector。

## 确认链

1. 调 `okr.create.prepare` / `okr.update.prepare`，向用户展示 `preview`（含目标名称、级别、周期、责任人、参与人、状态等）与 `expiresInSeconds`。
2. 用户明确同意后调 `okr.create.apply` / `okr.update.apply`，传 `confirm=true` 与 prepare 返回的 `continuation`。
3. continuation 绑定 `baseUrl`/`profile`/`userId`，10 分钟有效；登录上下文变化会返回 `validation/context_mismatch`，写入内容指纹变化会返回 `validation/target_changed`，两种情况都必须重新 prepare。

`apply` 成功后返回 `status=COMPLETE`、`goalId`、`path` 与 `detailUrl`（可点击的绝对地址）。

## 失败处理

- 写入请求发出后连接中断 → `partial/write_uncertain`，**禁止自动重试**，先调 `okr.get` 复核目标是否已落库。
- `validation/context_mismatch`、`validation/target_changed` → 重新执行 prepare，不要复用旧 continuation。
- `validation/scope_data_id_required`、`validation/principal_dept_required`、`validation/period_quarter_invalid` → 补齐参数后重新 prepare。

## 调用示例

新建个人月度目标：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json okr run okr.create.prepare --input-json '{"name":"2026年9月目标","period_type":"3","period_range":"2026-09"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"name":"2026年9月目标","period_type":"3","period_range":"2026-09"}' | weaver-work-cli --profile eteams --json okr run okr.create.prepare --input -
```

用户在对话中确认后提交：

```text
weaver-work-cli --profile eteams --json okr run okr.create.apply --input-json '{"confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

编辑已有目标（标准版必须带 `status`）：

```text
weaver-work-cli --profile eteams --json okr run okr.update.prepare --input-json '{"id":"<目标ID>","name":"2026年9月目标（修订）","status":"0"}'
```

## 注意

- 禁止手工构造或跨任务复用 continuation；`confirm=true` 只在用户明确确认后传入。
- `preview` 是给用户看的确认摘要，不是真实请求体；不要用 `preview` 去推测接口字段名。
