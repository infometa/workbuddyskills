# 直播子域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写与取值以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则语义/业务约束见 `live-concepts.md`。
> 能力契约见 `../apis/live/`，操作流程见 `../flows/live.md`。

---

## 直播间状态（五态，整数 code）

| code | 名称 | 业务含义 |
|---:|---|---|
| 0 | PENDING | 待开播 |
| 1 | LIVING | 直播中 |
| 2 | PAUSED | 暂停 |
| 3 | ENDED | 已结束 |
| 4 | EXPIRED | 已过期 |

运行时迁移（仅作状态解释，对应实时操作未开放）：

- PENDING --PUSH_START--> LIVING
- LIVING --PUSH_STOP--> PAUSED；LIVING --MANUAL_END/BAN--> ENDED
- PAUSED --PUSH_RESUME--> LIVING；PAUSED --TIMEOUT/BAN--> ENDED
- ENDED --EXPIRE--> EXPIRED

- 直播间列表筛选实现未调用状态码反查（fromCode），错误状态值不报错、只返回空结果；因此调用纪律只允许上表五个整数，不将“服务端必然拒绝错值”当作保证。
- 状态机允许 `ENDED --EXPIRE--> EXPIRED`，但全仓未发现触发 EXPIRE 的入口或定时任务。这是 Java 生命周期缺口：只能说明迁移规则预留了过期态，不能承诺已结束直播间会自动进入已过期。

## 直播间封禁状态（banStatus，整数常量）

| code | 说明 |
|------|------|
| 0 | 正常 |
| 1 | 封禁 |

## 讲解场次状态（八态，整数 code）

| code | 名称 | 业务含义 | 已开放写操作 |
|---:|---|---|---|
| 0 | SCHEDULED | 已排期 | 编辑、取消 |
| 1 | PREPARING | 准备中 | 取消；不开放实时推进 |
| 2 | LIVING | 直播中 | 不开放实时控制 |
| 3 | PAUSED | 暂停 | 不开放恢复 |
| 4 | ENDED | 已结束 | 无 |
| 5 | EXPIRED | 已过期 | 无 |
| 6 | CANCELLED | 已取消 | 终止态，不重复取消 |
| 7 | FORBIDDEN | 已禁播 | 无 |

运行时迁移：SCHEDULED 可进入 PREPARING/CANCELLED/FORBIDDEN/EXPIRED；PREPARING 可进入 LIVING/ENDED/CANCELLED/FORBIDDEN；LIVING 可进入 PAUSED/ENDED/FORBIDDEN；PAUSED 可进入 LIVING/ENDED/FORBIDDEN；ENDED 可进入 EXPIRED；其余终态不再迁出。

- 迁移带 CAS/version 并发保护（乐观锁，冲突报「场次已被并发修改，请刷新后重试」）。
- 当前仅开放 SCHEDULED 编辑，以及 SCHEDULED/PREPARING 取消；其余转换即使后端存在也不构成开放能力。

## 回放状态（四态，整数 code）

| code | 名称 | 含义 |
|---:|---|---|
| 0 | NONE | 无回放 |
| 1 | GENERATING | 生成中 |
| 2 | AVAILABLE | 可回放 |
| 3 | EXPIRED | 已过期 |

运行时中，场次结束后从 NONE 标记为 GENERATING，录制回调成功后进入 AVAILABLE；删除与过期共用 EXPIRED 收敛，没有独立“删除中”状态。

- 回放列表只做整数等值筛选，未证明会拒绝错误枚举；调用纪律仅允许上表四个整数。

## 场次数据完备度（statStatus，字符串枚举）

| 值 | 含义 |
|---|---|
| COLLECTING | 统计采集进行中（无统计行时详情恒回该值，不回缺失） |
| FINALIZING | 对账修正中 |
| FINALIZED | 已终态（再收到支付事件会重开为 FINALIZING 做对账修正，终态不是绝对终态） |

- statStatus 是统计完备度，不是场次状态；字段可能整体缺失（null 字段序列化省略）。

## 直播分类状态（status，整数常量）

| code | 说明 |
|------|------|
| 0 | 禁用 |
| 1 | 启用 |

- 启停接口 status 仅接受 0/1（其他值服务端报 400「分类状态只能为0或1」）。
