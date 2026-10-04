# 目标对齐（okr-align）

目标对齐用于把**当前目标**挂到**对齐目标**之下。该能力**仅 ebuilder 链路可用**——e10 标准版源资料没有提供对应接口，标准版租户调用会返回 `policy/link_unsupported`。

| operation | 风险 | 作用 |
| --- | --- | --- |
| `okr.align.create.prepare` | read-before-write | 补全双方负责人、生成预览与 continuation，**不写入** |
| `okr.align.create.apply` | high-risk-write | 提交添加目标对齐 |

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `current_id` | 目标 ID | 必填，当前目标 |
| `align_obj_id` | 目标 ID | 必填，被对齐的目标 |
| `cur_obj_principalid` | 人员 ID | 可选，当前目标负责人 |
| `ali_obj_principalid` | 人员 ID | 可选，对齐目标负责人 |
| `confirm` / `continuation` | - | 仅 `apply` 需要 |

## 关键业务规则

- **两个目标不能相同**：`current_id === align_obj_id` 时返回 `validation/align_invalid`。
- **自动补全双方负责人**：未显式提供 `cur_obj_principalid`/`ali_obj_principalid` 时，`prepare` 会用目标详情接口分别取两个目标的负责人；任一取不到会返回 `validation/align_principal_unresolved`，此时需要显式传入人员 ID（由 weaver-e10-hrm-connector 解析），**CLI 不会臆造负责人**。
- `preview` 会展示当前目标/当前目标负责人/对齐目标/对齐目标负责人四项，确认前务必核对双方是否选反。

## 确认链

1. `okr.align.create.prepare` 返回 `preview` 与 `continuation`。
2. 用户明确确认后调 `okr.align.create.apply`，传 `current_id`、`align_obj_id`、`confirm=true`、`continuation`。
3. continuation 绑定 `baseUrl`/`profile`/`userId`，10 分钟有效；`current_id` 或内容指纹变化返回 `validation/target_changed`，需重新 prepare。

## 调用示例

准备对齐：

```text
weaver-work-cli --profile eteams --json okr run okr.align.create.prepare --input-json '{"current_id":"<当前目标ID>","align_obj_id":"<对齐目标ID>"}'
```

用户核对双方负责人后提交：

```text
weaver-work-cli --profile eteams --json okr run okr.align.create.apply --input-json '{"current_id":"<当前目标ID>","align_obj_id":"<对齐目标ID>","confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

显式指定双方负责人（详情接口取不到时）：

```text
weaver-work-cli --profile eteams --json okr run okr.align.create.prepare --input-json '{"current_id":"<当前目标ID>","align_obj_id":"<对齐目标ID>","cur_obj_principalid":"<人员ID>","ali_obj_principalid":"<人员ID>"}'
```

## 失败处理

- `policy/link_unsupported` → 当前租户走标准版链路，没有目标对齐接口，不要换接口硬试。
- 写入请求发出后连接中断 → `partial/write_uncertain`，禁止自动重试；先调 `okr.get`（或按 `okr.kr.list` 的方式）回查目标关系是否已建立。
- 源资料只提供**添加**对齐的接口，没有解除对齐的 operation。

## 注意

- 确认前必须让用户看清「谁对齐谁」，`current_id` 是挂在下面的那两个之一，方向弄反需要重建关系。
- 禁止手工构造或跨任务复用 continuation。
