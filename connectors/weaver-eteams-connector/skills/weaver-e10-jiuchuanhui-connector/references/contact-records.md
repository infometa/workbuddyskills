# 联系记录（contact-records）

## 何时使用

用户表达联系记录/跟进记录相关意图：查询某客户/商机/线索/联系人的联系记录，或按人员+时间范围查询联系记录。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.entity.contact-records.list` | 只读 | `mainTable.moduleType`（`customer`/`clue`/`saleChance`）、`mainTable.entityId` |
| `jiuchuanhui.contact-records.by-person-time.list` | 只读 | `mainTable`: `{employeeId, startData, endData}` |

（新建联系记录/跟进走各业务模块的 `*.contact-record.create.prepare/apply`：客户/商机/线索分别见对应 reference。）

## 输入要点

- `moduleType`：要查询的对象类型（客户/商机/线索），`entityId` 为对应数据 ID。
- 按人员+时间范围查询时，`employeeId` 用人员 ID（可先用 `user.id.by-name` 解析姓名），`startData`/`endData` 用 `yyyy-MM-dd HH:mm:ss`。
- 日期类模糊表达需转换为明确范围，例如今天、本周、本月分别补齐开始和结束时间。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.entity.contact-records.list --input-json '{"mainTable":{"moduleType":"customer","entityId":"100001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-records.by-person-time.list --input-json '{"mainTable":{"employeeId":"USER_ID","startData":"2026-09-01 00:00:00","endData":"2026-09-09 23:59:59"}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.entity.contact-records.list --input-json '{"mainTable":{"moduleType":"customer","entityId":"100001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact-records.by-person-time.list --input-json '{"mainTable":{"employeeId":"USER_ID","startData":"2026-09-01 00:00:00","endData":"2026-09-09 23:59:59"}}'
```

## 输出处理

- 联系记录列表按时间倒序展示；超过 10 条先展示最相关的前 10 条并提示可继续翻页/缩小范围。

## 注意

- 记录内的关联事项名称渲染为可点击链接。

## 失败处理

- 参数缺失/不支持：说明具体问题并停止。
