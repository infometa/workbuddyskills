# 商户域 — 门店隔离与网店模式写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-store.md`（门店隔离与网店模式节）；现状读取（隔离分页/已隔离全集/模式查询）先读 `store-isolation-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：store-isolation.batch-add 批量新增门店隔离 🔴 · store-isolation.update-status 隔离启停 · store-isolation.delete 删除隔离记录 🔴 · store-mode.update 网店模式设置 🔴

---

## ✅ 批量新增门店隔离 — ops.merchant.store-isolation.batch-add

- 🔴 商业影响（隔离后门店间数据互不可见，影响运营视图）
- **说明**：批量登记进入隔离的门店（每条隔离记录对应一个门店）；先经 store-ids 排除已隔离项，防重复配置。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeIds | array&lt;String&gt; | 是 | 门店 ID 列表（先经 store-ids 排除已隔离项） |

### 出参（原始数据）

- 新增条数（integer）

### 调用示例

```json
{"capability":"ops.merchant.store-isolation.batch-add","input":{"storeIds":["5600012345678901235","5600012345678901236"]},"summary":"把这两家门店加入数据隔离"}
```

---

## ✅ 门店隔离启停 — ops.merchant.store-isolation.update-status

- 🟡 可逆写（解除后可重新隔离）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 隔离记录 ID（路径，来自 search 出参） |
| isolated | Boolean | ✅ | true=隔离生效 / false=解除隔离 |

### 调用示例

```json
{"capability":"ops.merchant.store-isolation.update-status","input":{"id":"7100012345678901234","isolated":false},"summary":"解除这条门店的隔离状态"}
```

---

## ✅ 删除门店隔离记录 — ops.merchant.store-isolation.delete

- 🔴 不可逆（删除后如需隔离须重新配置）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 隔离记录 ID（路径，来自 search 出参） |

### 调用示例

```json
{"capability":"ops.merchant.store-isolation.delete","input":{"id":"7100012345678901234"},"summary":"删除这条门店隔离记录"}
```

---

## ✅ 网店模式设置 — ops.merchant.store-mode.update

- 🔴 全租户（切换单网点/多网点模式影响 C 端门店选择与运营视图）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| mode | String | 是 | `single` / `multi`（小写） |
| version | Long | 是 | 乐观锁版本号（来自 store-mode.get 出参 `version`） |

### 调用示例

```json
{"capability":"ops.merchant.store-mode.update","input":{"mode":"multi","version":2},"summary":"把店铺切换为多网点模式"}
```
