# 商户域 — 暗纹词与场景查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-search.md`（与搜索干预同属搜索运营面）；写操作见 `placeholder-action.md`。
> 覆盖 C 端搜索占位配置：暗纹场景（placeholder-scene）与场景下的暗纹词（placeholder-keyword）。出参为上游**原始业务数据**（不裁剪字段）。
> **核心模型**：暗纹词 = C 端搜索框的占位提示文案（如"秋季上新"）；按**场景**（scene，如首页搜索框）组织；一个场景下多个暗纹词按 `sortWeight` 轮换/排序展示。与热搜词不同——暗纹词是搜索框**占位提示**，热搜词是搜索**联想词**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：placeholder-keyword.page 暗纹词分页 · placeholder-scene.page 场景分页 · placeholder-scene.enabled-list 启用场景列表 · placeholder-scene.detail 场景详情（暗纹词系列完整 id 前缀为 `ops.merchant.placeholder-keyword.`，场景系列见各锚点）

---

## ✅ 暗纹词分页 — ops.merchant.placeholder-keyword.page

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | 否 | 默认 1/20 |
| sceneId | String | 否 | 场景筛选（来自场景列表出参） |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ update/delete/status 路径参数）
- **展示字段**：`content`（词内容）、`sceneId`/`sceneName`、`sortWeight`、`status`、`startTime`/`endTime`

### 调用示例

```json
{"capability":"ops.merchant.placeholder-keyword.page","input":{"pageNum":1,"pageSize":20},"summary":"看下当前配置的搜索占位词"}
```

---

## ✅ 场景分页 — ops.merchant.placeholder-scene.page

- **说明**：全量场景分页。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | 否 | 默认 1/20 |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 暗纹词 create 的 sceneId / 场景维护路径参数）
- **展示字段**：`code`（场景标识，`^[a-z][a-z0-9_]{1,31}$`）、`name`、`sort`、`remark`、`status`

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.page","input":{"pageNum":1,"pageSize":20},"summary":"分页看全部搜索占位场景"}
```

---

## ✅ 启用场景列表 — ops.merchant.placeholder-scene.enabled-list

- **说明**：仅启用场景（给暗纹词 create 选场景用）。

### 入参（无）

### 出参（数组，原始数据）

- **路径参数来源**：`[].id`（→ 暗纹词 create 的 sceneId）
- 展示字段同场景分页。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.enabled-list","input":{},"summary":"看下有哪些启用中的搜索占位场景"}
```

---

## ✅ 场景详情 — ops.merchant.placeholder-scene.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 场景 ID |

### 出参（原始数据）

完整场景配置（code/name/sort/remark/status 等），以响应为准。

### 调用示例

```json
{"capability":"ops.merchant.placeholder-scene.detail","input":{"id":"7600012345678901234"},"summary":"看这个场景的完整配置"}
```
