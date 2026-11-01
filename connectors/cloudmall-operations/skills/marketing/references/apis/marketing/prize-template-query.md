# 营销域 — 奖品模板查询契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/interactive-activity-flow.md`
> 奖品模板是互动活动奖品池的素材库（积分/优惠券/实物三类）；被“在用”活动引用的模板不可删除。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：prize-template.search 奖品模板分页查询 · prize-template.detail 奖品模板详情
> 写操作见 `prize-template-action.md`。

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| 无 | 奖品模板全部端点均已开放 |

---

## ✅ 奖品模板分页查询 — `ops.marketing.prize-template.search`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | 默认 1 |
| pageSize | Integer | 否 | 1..100，默认 10 |
| name | String | 否 | 奖品名称模糊 |
| type | String | 否 | 奖品类型精确匹配：points / coupon / physical（与 types 二选一） |
| types | String[] | 否 | 奖品类型 IN 匹配（优先于 type） |
| status | Integer | 否 | 1=有效，0=停用 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 详情/编辑/删除/启停）、`records[].bizTemplateId`（type=coupon 时为关联的优惠券模板 ID，可回查促销域券模板详情）
- **枚举字段**：`type`（points/coupon/physical）、`sendDescType`/`useDescType`（text/image）、`status`（1/0）
- **格式敏感字段**：`image`（COS 预签名 URL，约 60 分钟过期，过期需重查，**不要持久化**）；`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `autoSend`（1=自动发放 0=手动）、`quantity`（奖品数量）。

### 调用示例

```json
{"capability":"ops.marketing.prize-template.search","input":{"pageNum":1,"pageSize":10,"type":"coupon","status":1},"summary":"查找可用的优惠券类奖品模板"}
```

---

## ✅ 奖品模板详情 — `ops.marketing.prize-template.detail`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 奖品模板 ID（十进制字符串；本文各能力的 id 均为此义） |

### 出参（原始数据）

- 结构同列表项（含 `config` 奖品配置 JSON 字符串**原文回显**——编辑时原值回传；`expireSeconds` 可换算为小时展示、`{"expireSeconds": 7200}` 即 2 小时、`sendDesc`/`useDesc` 发放与使用说明）；`image` 为预签名 URL（约 60 分钟过期）。

### 调用示例

```json
{"capability":"ops.marketing.prize-template.detail","input":{"id":"5200000000000000001"},"summary":"查看奖品模板详情"}
```

---
