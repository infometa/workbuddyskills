# 营销域 — 协议管理查询契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/marketing-support-flow.md`
> 协议按类型管理（9 类），同类型同时只有一个“已发布”版本——发布新协议会自动结束同类型旧协议。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：agreement.search 协议分页查询 · agreement.detail 协议详情（编辑前必读） · agreement.preview 协议轻量预览
> 写操作见 `agreement-action.md`。

---

## 协议状态机（Integer code）

| code | 状态 | 可执行动作 |
|------|------|-----------|
| 0 | 未发布 | 编辑、发布、删除 |
| 1 | 已发布 | 结束（不可编辑、不可删除） |
| 2 | 已结束（终态） | 删除 |

流转：0 →发布→ 1 →结束→ 2。发布时同类型旧的"已发布"协议自动转 2。

---

## 协议类型（type，Integer 1..9）

1=系统弹窗、2=隐私政策、3=用户服务协议、4=第三方共享个人信息清单、5=个人信息收集清单、6=未成年人信息保护规则、7=预售定金协议、8=分销协议、9=分销佣金规则。

---

## ⛔ 未开放端点

| 端点 | 不开放理由 |
|------|-----------|
| 无 | 协议管理全部端点均已开放 |

---

## ✅ 协议分页查询 — `ops.marketing.agreement.search`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| title | String | 否 | 协议标题模糊搜索 |
| type | Integer | 否 | 协议类型（1..9） |
| status | Integer | 否 | 发布状态（0/1/2） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 详情/编辑/发布/结束/删除/预览）
- **枚举字段**：`type`（1..9，见类型表）、`status`（0/1/2）
- **格式敏感字段**：`publishTime`/`endTime`/`createdTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.marketing.agreement.search","input":{"pageNum":1,"pageSize":20,"type":2,"status":1},"summary":"查看已发布的隐私政策"}
```

---

## ✅ 协议详情 — `ops.marketing.agreement.detail`

- **说明**：编辑前必读

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 协议 ID（十进制字符串；本文各能力的 id 均为此义） |

### 出参（原始数据）

- **枚举字段**：`type`/`status`
- **格式敏感字段**：`publishTime`/`endTime`/`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `content` 为富文本 HTML（图片 src 为实时重签的临时 URL，约 30 分钟过期，不要持久化）。

### 调用示例

```json
{"capability":"ops.marketing.agreement.detail","input":{"id":"5300000000000000001"},"summary":"读取隐私政策全文用于修订"}
```

---

## ✅ 协议预览 — `ops.marketing.agreement.preview`

- **说明**：轻量预览（标题 + 内容 + 版本号），内容图片同样为临时签名 URL。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 协议 ID |

### 出参（原始数据）

- `title`/`content`/`version`（版本号为服务端填充的固定值）。

### 调用示例

```json
{"capability":"ops.marketing.agreement.preview","input":{"id":"5300000000000000001"},"summary":"预览协议渲染效果"}
```

---
