# 营销域 — CPS 商品推广查询契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-settle-flow.md`
> **核心枚举**：`commissionType` 佣金类型 0=全局佣金 / 1=定向佣金；`promotionStatus` 推广状态 0=推广中（有效）/ 1=已停止（无效）。
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「路径参数来源 / 枚举 / 格式敏感 / 脱敏」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）调用，入参 `{capability, input, summary}`。
> 本域金额一律**元**（两位小数）、佣金率/分成比例为小数比例、CPS 返佣系数为乘数、ID 十进制字符串、时间 `yyyy-MM-dd HH:mm:ss`（详见入口 SKILL.md 通用约定）。
> 能力索引（前缀 `ops.marketing.`）：cps-goods-promotion.search 推广商品分页（附佣金率范围；无副作用只读） · cps-goods-promotion.detail 推广商品详情（推广状态+SKU；无副作用只读） · cps-goods-promotion.selector 推广商品选择器（选品场景候选分页；无副作用只读） · cps.goods-promotion.export 推广商品列表异步导出（返回任务 ID）
> 写操作见 `cps-goods-promotion-action.md`。

---

## ⛔ 未开放

无（商品推广模块全部端点均已开放）。

---

## ✅ 推广商品分页 — `ops.marketing.cps-goods-promotion.search`

- **说明**：只读无副作用，瞬态错误可单次重试。以商品中心商品分页为主驱动、填充 CPS 佣金属性返回。未指定推广状态筛选时默认「推广中在前、已停止沉底、组内按创建时间倒序」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| spuName | String | 否 | 商品名称（模糊） |
| externalSpuId | String | 否 | 外部系统 SPU 编码（模糊） |
| commissionType | Integer | 否 | 佣金类型：0 全局佣金 / 1 定向佣金；不传=不过滤 |
| promotionStatus | Integer | 否 | 推广状态：0 推广中 / 1 已停止；不传=不过滤（并启用沉底排序） |
| categoryCodes | Array&lt;String&gt; | 否 | 品类编码多选（末级编码，服务端递归展开子孙类目）；优先于 categoryCode |
| categoryCode | String | 否 | 已废弃的单品类编码（兼容保留，新调用用 categoryCodes） |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].spuId`（→ 商品推广详情/批量启停、活动推广商品编排引用）
- **枚举字段**：`commissionType`（0/1，附 `commissionTypeDesc`）、`promotionStatus`（0/1，附 `promotionStatusDesc`）、`status`（商品上下架状态：ENABLED/DISABLED/HIDDEN）
- **格式敏感字段**：`price`（元）；`commissionRateRange.minCommissionRate`/`maxCommissionRate`（**四位小数比率**，0.1213=12.13%）、`commissionRateRange.minCommissionAmount`/`maxCommissionAmount`（元）；`spuId`（Long→string）；`categoryPath`（类目完整路径，如「服装 / 女装 / 连衣裙」）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-goods-promotion.search","input":{"pageNum":1,"pageSize":20,"spuName":"研学","promotionStatus":0,"categoryCodes":["T900001_C61"]},"summary":"查看该类目下推广中的商品及佣金率"}
```

---

## ✅ 推广商品详情 — `ops.marketing.cps-goods-promotion.detail`

- **说明**：只读无副作用，瞬态错误可单次重试。查询单个商品的推广属性（商品基础信息 + 推广状态 + SKU 列表；不含佣金率范围，佣金率看分页结果的 `commissionRateRange`）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | Long | ✅ | 商品 SPU ID（十进制字符串） |

### 出参（原始数据）

- **路径参数来源**：`spuId`、`skuList[].skuId`
- **枚举字段**：`commissionType`（0/1）、`promotionStatus`（0/1）、`status`（ENABLED/DISABLED/HIDDEN）、`topFlag`（0 否 / 1 是）
- **格式敏感字段**：`price` 及 `skuList[].price`（元）；`spuId`（Long→string）；`categoryPath`（类目完整路径）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-goods-promotion.detail","input":{"spuId":"2058365707555589633"},"summary":"查询该商品的推广状态与SKU信息"}
```

---

## ✅ 推广商品选择器 — `ops.marketing.cps-goods-promotion.selector`

- **说明**：只读无副作用，瞬态错误可单次重试。选品场景的候选商品分页（纯商品中心标准分页，附当前推广信息），用于活动奖励适用范围、活动推广商品编排等选品入口。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| spuName | String | 否 | 商品名称（模糊） |
| externalSpuId | String | 否 | 外部系统 SPU 编码（模糊） |
| categoryCode | String | 否 | 品类编码（单选） |
| status | String | 否 | 商品状态（ENABLED/DISABLED/HIDDEN）——**当前服务端未生效**（透传时被忽略），不要依赖 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].spuId`（→ 选品后写入活动奖励适用范围 goodsList / 活动推广 selectGoods）
- **枚举字段**：`promoted`（boolean，是否已在推广）、`promotionStatus`（0/1）、`commissionType`（0/1）、`status`（ENABLED/DISABLED/HIDDEN）
- **格式敏感字段**：`price`（元）；`spuId`（Long→string）
- **脱敏字段**：无

### 调用示例

```json
{"capability":"ops.marketing.cps-goods-promotion.selector","input":{"pageNum":1,"pageSize":20,"spuName":"研学"},"summary":"选品：分页查找名称含研学的候选商品"}
```

---

## ✅ 推广商品列表导出 — `ops.marketing.cps.goods-promotion.export`

- **说明**：按筛选条件异步导出商品推广配置。返回**导出任务 ID**，用 `ops.marketing.export.task.get` 轮询任务状态，`COMPLETED` 后从 `downloadUrl` 下载。筛选条件结构同 `ops.marketing.cps-goods-promotion.search`。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （筛选条件） | object | 否 | 结构同推广商品分页查询 |

### 出参（原始数据）

- **格式敏感字段**：返回 `String`——导出任务 ID（→ `ops.marketing.export.task.get` 的 `taskId`）

### 调用示例

```json
{"capability":"ops.marketing.cps.goods-promotion.export","input":{"pageNum":1,"pageSize":20},"summary":"导出商品推广配置清单"}
```

---
