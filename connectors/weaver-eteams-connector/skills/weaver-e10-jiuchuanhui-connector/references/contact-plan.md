# 联系计划（contact-plan）

## 何时使用

用户表达联系计划相关意图：创建联系计划、完成联系计划。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.contact-plan.create.prepare/apply` | 高风险写 | `form`: `{mainTable, ...}`；`type` 必填且与关联字段一一对应（见下） |
| `jiuchuanhui.contact-plan.complete.prepare/apply` | 高风险写 | `planId` |

## 输入要点

- **`type` 联动规则（必填，传数字 1/2/3）**：`type=1`（客户）→ 必填 `customer`（客户 ID）；`type=2`（商机）→ 必填 `sale_chance`（商机 ID）；`type=3`（线索）→ 必填 `clue`（线索 ID）。三选一、一 一对应，不可混搭。字段 key 是 `customer`/`sale_chance`/`clue`，不是 `customer_id`/`sale_id`/`clue_id`。
- `status` 必填，默认"进行中"（ID=1）。
- `remind_time`（联系时间）必填，格式 `yyyy-MM-dd HH:mm`；字段 key 是 `remind_time`（非 `plan_time`）。
- `manager`（负责人）必填，默认当前操作人。
- `visit_type`（联系类型）与 `type`（关联对象类型）**无关**——`type` 分模块，`visit_type` 分方式（上门/电话等），可独立选择。

## 命令

Windows PowerShell：

```powershell
# 为客户创建联系计划 (type=1 → customer)
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.create.prepare --input-json '{"form":{"mainTable":{"type":"1","customer":"100001","remind_time":"2026-09-10 14:00"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.complete.prepare --input-json '{"mainTable":{"planId":"600001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.complete.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# 为客户创建联系计划 (type=1 → customer)
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.create.prepare --input-json '{"form":{"mainTable":{"type":"1","customer":"100001","remind_time":"2026-09-10 14:00"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.complete.prepare --input-json '{"mainTable":{"planId":"600001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-plan.complete.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 输出处理

- 创建成功返回 `datajson.dataIds`；完成计划成功以 `resultCode===200` 为标志。

## 注意

- `type` 与关联字段必须联动：客户、商机、线索分别传对应事项 ID。
- 写操作执行前必须展示摘要并取得用户确认。

## 失败处理

- 关联事项不唯一：先搜索候选并让用户选择。
- `partial/write_uncertain`：停止重试，补一次只读回查。
