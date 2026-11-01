# 商品域 — 仓库库存写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-inventory.md`；现态读取（库存记录/version/仓库列表/导入任务进度）先读 `inventory-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：inventory.adjust 库存调整 🔴 · inventory.init 库存初始化 · inventory.import 库存批量导入（异步受理）
>
> 流程纪律：调整库存先查现库存与 version（inventory.search）→ 用户确认数量 → 调整 → 回读核验；超时不盲目重试 ADD/SUBTRACT。导入流程：导入（异步受理拿 taskId）→ import-task 轮询到终态 → PARTIAL_FAIL 时取 failure-url 报告失败行数并引导用户下载核对。

---

## ✅ 库存调整 — ops.product.inventory.adjust

- 🔴 商业影响档位；执行前用户确认数量
- **语义**：按库存记录ID调整总库存。**乐观锁**：`version` 必须来自最近一次 `ops.product.inventory.search` 返回的 `version`；version 不匹配服务端拒绝（并发冲突）。**下限规则（服务端强制）**：SET/SUBTRACT 后的新总库存不能小于订单占用 `lockedQty`，否则被拒。调低总库存可能导致门店预留库存被自动调低（响应含 warning，如实转达用户）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 库存记录ID（来自 inventory.search 的 `records[].id`） |
| operationType | String | ✅ | `SET`（设置）/ `ADD`（增加）/ `SUBTRACT`（减少） |
| quantity | Integer | ✅ | ≥0；SET=目标值，ADD/SUBTRACT=变化量 |
| version | Integer | ✅ | 乐观锁版本号（来自最近查询结果） |

### 出参（原始返回）

`data` 为调整结果（可能含 `warning` 预留联动提示）。执行后回读 `ops.product.inventory.search` 确认；超时**禁止盲目重试 ADD/SUBTRACT**（可能重复加减）。

### 调用示例

```json
{"capability":"ops.product.inventory.adjust","input":{"id":"4000012345678901234","operationType":"ADD","quantity":10,"version":3},"summary":"为指定库存记录补货10件"}
```

---

## ✅ 库存初始化 — ops.product.inventory.init

- **语义**：为 SKU + 仓库组合创建初始库存记录（未初始化的组合无法调整）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuId | String | ✅ | SKU 业务ID |
| warehouseId | String | ✅ | 仓库ID |
| physicalQty | Integer | ✅ | 初始总库存，≥0 |

### 出参（原始返回）

`data` 为 Void（null）。

### 调用示例

```json
{"capability":"ops.product.inventory.init","input":{"skuId":"9000012345678901234","warehouseId":"7000012345678901234","physicalQty":100},"summary":"初始化SKU在指定仓库的库存"}
```

---

## ✅ 库存批量导入（异步受理） — ops.product.inventory.import

- **传输形态**：multipart 文件上传（Excel）
- **语义**：批量导入库存，**异步受理**——同步阶段仅落盘并登记任务（<1s）即返回 `taskId`，用 `import-task` 轮询进度。限制：≤5000 行、文件 ≤10MB。模板从管理后台「库存-导入」入口获取。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | String | 是 | 导入文件在**会话工作区内的相对路径**（如 `uploads/1791515932021-库存批量出入库-20261009.xlsx`）；执行器负责组装 multipart 上传，无需另行上传。用户上传的附件位于工作区 `uploads/` 目录下且文件名带时间戳前缀，路径不确定时先用 find_files 定位 |
| fileType | String | 是 | 固定值 `excel` |

### 出参

- `taskId`（导入任务 ID，→ import-task/import-failure-url 路径参数）。

### 调用示例

```json
{"capability":"ops.product.inventory.import","input":{"file":"uploads/1791515932021-库存批量出入库-20261009.xlsx","fileType":"excel"},"summary":"批量导入库存 Excel（异步，稍后轮询进度）"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 销量初始化 | 一次性数据回放运维面（归零 totalSales 重建），不开放 |
