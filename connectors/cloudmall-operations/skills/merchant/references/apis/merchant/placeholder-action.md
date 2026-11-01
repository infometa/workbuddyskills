# 商户域 — 暗纹词与场景写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-search.md`；现值读取（暗纹词分页/场景查询）先读 `placeholder-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：placeholder-keyword.create 新增暗纹词 · placeholder-keyword.update 编辑暗纹词 · placeholder-keyword.delete 删除暗纹词 · placeholder-keyword.update-status 启停暗纹词 · placeholder-scene.create 新增场景 · placeholder-scene.update 编辑场景 · placeholder-scene.delete 删除场景 🔴 · placeholder-scene.update-status 启停场景

---

## ✅ 新增暗纹词 — ops.merchant.placeholder-keyword.create

- 🟡 可逆写（C 端搜索框文案，影响面小）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sceneId | String | 是 | 场景 ID（十进制字符串） |
| content | String | 是 | 词内容，≤20 字 |
| sortWeight | Integer | 是 | 排序权重 |
| status | Integer | 否 | 状态 |
| startTime / endTime | String | 否 | 生效时间窗（`yyyy-MM-dd HH:mm:ss` 字符串，**非毫秒时间戳**；不传=立即生效/长期有效） |

### 调用示例

```json
{"capability":"ops.merchant.placeholder-keyword.create","input":{"sceneId":"7600012345678901234","content":"秋季上新","sortWeight":10},"summary":"给首页搜索场景加一条秋季上新占位词"}
```

---

## ✅ 编辑暗纹词 — ops.merchant.placeholder-keyword.update

- 🟡 可逆写

### 入参

id（路径）+ **sceneId（必填**——与当前场景相同=原地编辑、不同=转移场景**）** + content/sortWeight 等可改字段。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-keyword.update","input":{"id":"7800012345678901234","sceneId":"7600012345678901234","content":"双11大促","sortWeight":5},"summary":"把这条占位词改成双11大促"}
```

---

## ✅ 删除暗纹词 — ops.merchant.placeholder-keyword.delete

- 🟡 可逆（可重建）

### 入参

路径 `id`。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-keyword.delete","input":{"id":"7800012345678901234"},"summary":"删除这条过期的占位词"}
```

---

## ✅ 启停暗纹词 — ops.merchant.placeholder-keyword.update-status

- 🟡 可逆

### 入参

路径 `id` + `status` 整数。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-keyword.update-status","input":{"id":"7800012345678901234","status":1},"summary":"启用这条占位词"}
```

---

## ✅ 新增场景 — ops.merchant.placeholder-scene.create

- 🟡 可逆写

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | String | 是 | 场景标识，2-32 位，`^[a-z][a-z0-9_]{1,31}$`（小写开头） |
| name | String | 是 | 场景名称，≤32 字 |
| sort | Integer | 是 | 排序权重 |
| status | Integer | 是 | 状态：0=停用 / 1=启用 |

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.create","input":{"code":"search_home","name":"首页搜索","sort":1,"status":1},"summary":"新建首页搜索占位场景"}
```

---

## ✅ 编辑场景 — ops.merchant.placeholder-scene.update

- 🟡 可逆写
- **注意**：update 的必填字段与 create 不同，以本表为准。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 场景 ID（路径） |
| name | String | 是 | ≤32 字 |
| sort | Integer | 是 | 排序权重 |
| remark | String | 否 | ≤200 字 |
| status | Integer | 是 | 整数 |

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.update","input":{"id":"7600012345678901234","name":"首页搜索框","sort":2,"status":1},"summary":"把场景改名为首页搜索框"}
```

---

## ✅ 删除场景 — ops.merchant.placeholder-scene.delete

- 🔴 场景下已有暗纹词时的**级联行为以服务端响应为准**——执行前确认级联影响

### 入参

路径 `id`。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.delete","input":{"id":"7600012345678901234"},"summary":"删除这个废弃场景"}
```

---

## ✅ 启停场景 — ops.merchant.placeholder-scene.update-status

- 🟡 可逆

### 入参

路径 `id` + `status` 整数。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.update-status","input":{"id":"7600012345678901234","status":0},"summary":"停用这个占位场景"}
```
