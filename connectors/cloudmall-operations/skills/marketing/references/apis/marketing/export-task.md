# 营销域 — 通用导出任务查询契约

> 概念知识：`references/domains/marketing-concepts.md`；运营流程：`references/flows/marketing-support-flow.md`
> 营销域全部**异步导出能力**的统一进度查询入口：各 `*.export` 能力返回导出任务 ID 后，用本能力轮询状态并获取下载链接。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：export.task.get **通用导出任务查询**（全部 `*.export` 的状态轮询/下载链接）

---

## ✅ 查询导出任务 — `ops.marketing.export.task.get`

- **说明**：按任务 ID 查询异步导出任务的状态与下载链接。**`taskId` 只能取自某个 `*.export` 能力的返回值**（真实形态为 32 位无连字符 UUID hex，如 `3f2a9c8d1e5b47a09d6c8f21e4b7a3d5`），**禁止自行构造或猜测 taskId**。配套能力（返回 taskId 的全部导出）：

  | 导出能力 | 文件 |
  |---|---|
  | `ops.marketing.guide.export` | [guide-query.md](guide-query.md) |
  | `ops.marketing.guide.speech.export` | [guide-speech-query.md](guide-speech-query.md) |
  | `ops.marketing.guide.commission-details.export` | [guide-commission-query.md](guide-commission-query.md) |
  | `ops.marketing.guide.content-material.export-copy` | [guide-material-query.md](guide-material-query.md) |
  | `ops.marketing.cps.distributor.export` | [cps-distributor-query.md](cps-distributor-query.md) |
  | `ops.marketing.cps.settlement.export` / `export-by-activity` | [cps-settle-query.md](cps-settle-query.md) |
  | `ops.marketing.cps.goods-promotion.export` | [cps-goods-promotion-query.md](cps-goods-promotion-query.md) |
  | `ops.marketing.cps.data-stats.promotion-details.export` | [cps-promotion-query.md](cps-promotion-query.md) |
  | `ops.marketing.cps.order.export` | [cps-commission-query.md](cps-commission-query.md) |

- **纪律**：轮询有间隔（建议 ≥ 数秒一次，不密集刷）；`PENDING`/`PROCESSING` 继续等，`FAILED` 停止并向用户报告；`downloadUrl` 有时效（以响应为准，通常 30 分钟），过时需重新发起导出。**导出能力本身非幂等**（重试创建重复任务）——导出调用超时后先用本能力确认任务是否已创建，不盲目重发。**导出内容含明文 PII**（手机号等），转述打码、交付提醒保管，不把内容或链接写入持久化产物或第三方渠道。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | String | ✅ | 导出任务 ID（路径参数，**取自某个 `*.export` 能力的返回值**，32 位无连字符 UUID hex） |

### 出参（原始数据）

- **枚举字段**：`status`（`PENDING` 待处理 / `PROCESSING` 处理中 / `COMPLETED` 已完成 / `FAILED` 失败）
- **格式敏感字段**：`downloadUrl`（下载 URL，仅 `COMPLETED` 时返回；**有时效，不持久化、不当稳定链接转述**）

### 调用示例

```json
{"capability":"ops.marketing.export.task.get","input":{"taskId":"3f2a9c8d1e5b47a09d6c8f21e4b7a3d5"},"summary":"查询导出任务进度"}
```

---

---

## ⛔ 未开放

无（导出任务查询是全部异步导出能力的配套只读端点）。
