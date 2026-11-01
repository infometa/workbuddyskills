# 商户域 — 分类导航模板写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-category-nav.md`；现值读取（分页/详情/可见性/无效绑定检测）先读 `category-nav-query.md`；分类树增量结构见 `category-nav-content-action.md`（batch-save 与 save-and-publish 完全同构）。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：category-nav.create 创建模板 · category-nav.copy 复制模板 · category-nav.name.update 更新名称 · category-nav.icon-shape.update 更新图标形状 · category-nav.store-visibility.update 门店可见性配置 🔴 · category-nav.publish 发布 🔴 · category-nav.save-and-publish 保存并发布 🔴 · category-nav.offline 下线 🔴 · category-nav.set-default 设默认 🔴 · category-nav.delete 删除 🔴 · category-nav.invalid-store-bindings.remove 清除无效绑定

---

## ✅ 创建模板 — ops.merchant.category-nav.create

- 🟡 可逆（草稿态不影响线上）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| layoutMode | String | 是 | `CLASSIC` / `THREE_LEVEL` / `BRAND`（大写；**创建后不可更改**） |
| name | String | 是 | 版本名称，≤20 字 |

### 出参（原始数据）

- **路径参数来源**：`id`（新模板 ID → 后续编辑/发布）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.create","input":{"layoutMode":"CLASSIC","name":"秋季主推导航"},"summary":"新建一个经典布局的导航模板"}
```

---

## ✅ 复制模板 — ops.merchant.category-nav.copy

- 🟡 可逆（复制产物为草稿）
- **⚠️ 注意（2026-10-15 三组对照实验实证）**：对**从未发布过**的模板（无已发布版本数据，含新建草稿）执行复制**必现服务端 500**，与门店范围（ALL/SPECIFIED）无关；**发布过**（有已发布版本数据）的模板复制正常（含已下线、指定门店范围）。复制前先查 detail 判断：若源模板从未发布，提示用户先发布再复制，或换用发布过的模板，不要反复重试

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 源模板 ID |

### 出参（原始数据）

- **路径参数来源**：`id`（副本模板 ID）；`name`（副本名称）展示字段

### 调用示例

```json
{"capability":"ops.merchant.category-nav.copy","input":{"id":"6800012345678901234"},"summary":"复制当前线上导航做一版双11改版"}
```

---

## ✅ 更新名称 — ops.merchant.category-nav.name.update

- 🟡 可逆

### 入参

id（路径）+ `name`（非空非空白）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.name.update","input":{"id":"6800012345678901234","name":"双11主推导航"},"summary":"把这个导航改名为双11主推导航"}
```

---

## ✅ 更新图标形状 — ops.merchant.category-nav.icon-shape.update

- 🟡 可逆

### 入参

id（路径）+ `iconShape`（`circle` / `square`，小写）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.icon-shape.update","input":{"id":"6800012345678901234","iconShape":"circle"},"summary":"把导航图标改成圆形"}
```

---

## ✅ 门店可见性配置 — ops.merchant.category-nav.store-visibility.update

- 🔴 商业影响（决定哪些门店的 C 端首页展示本导航）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 模板 ID |
| storeScope | String | 是 | `ALL` / `SPECIFIED`（大写） |
| storeIds | array&lt;String&gt; | 条件必填 | storeScope=SPECIFIED 时必填（门店 ID 来自门店查询） |
| forceUpdate | Boolean | 否 | 冲突二次确认时传 true，默认 false |

### 出参（原始数据）

- `success`（boolean）；success=false 时返回 `conflictTemplates[]`（`templateId`/`templateName`/`storeNames[]`/`storeIds[]`——与已发布模板的门店冲突明细）。**冲突处理**：向用户展示冲突明细并确认后，带 `forceUpdate=true` 重提（会替换冲突门店的旧关联）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.store-visibility.update","input":{"id":"6800012345678901234","storeScope":"SPECIFIED","storeIds":["5600012345678901234","5600012345678901235"],"forceUpdate":false},"summary":"把这个导航只对南山和福田两家门店可见"}
```

---

## ✅ 发布 — ops.merchant.category-nav.publish

- 🔴 商业影响（C 端首页生效）
- **说明**：纯状态开关（列表页发布按钮）。编辑页一步到位场景用「保存并发布 — ops.merchant.category-nav.save-and-publish」锚点。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 模板 ID |
| forcePublish | Boolean | 否 | 强制发布（跳过空分类警告），默认 false |
| confirmReplace | Boolean | 否 | 确认替换已有生效模板，默认 false |

### 出参（原始数据）

- **状态字段**：`success`（boolean）
- **冲突字段**：`conflictTemplates[]`（confirmReplace=false 且存在门店冲突时返回；确认后带 confirmReplace=true 重提）
- **警告字段**：`emptyCategories[]`（未关联商品的分类名称列表；forcePublish=false 且存在时返回；确认后带 forcePublish=true 重提）

### 调用示例

```json
{"capability":"ops.merchant.category-nav.publish","input":{"id":"6800012345678901234","forcePublish":false,"confirmReplace":false},"summary":"发布这个导航模板"}
```

⚠️ `success=false` 不是失败报错，而是**带冲突/警告的二次确认请求**——必须把冲突明细讲给用户、取得明确确认后再带对应 flag 重提，不得静默强制发布。

---

## ✅ 保存并发布 — ops.merchant.category-nav.save-and-publish

- 🔴 商业影响（一次性保存完整变更到 published 版并发布）
- **说明**：编辑页「发布」按钮专用；把名称/图标/门店范围/分类树变更/商品变更一次性提交并发布。分类树增量结构见 `category-nav-content-action.md`（additions/updates/deletions/sortChanges 与 batch-save 完全同构）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 模板 ID |
| name / iconShape / storeScope / storeIds | — | 否 | 如有变更才传 |
| categoryAdditions | array | 否 | 新增分类（tempId/name/parentId/level/sortOrder/iconUrl/coverImage/componentsJson——componentsJson 结构见 `category-nav-content-action.md` 批量保存节，仅 BRAND 布局使用） |
| categoryUpdates | array | 否 | 更新分类（categoryId + 可选 name/sortOrder/iconUrl/coverImage/componentsJson） |
| categoryDeletions | array&lt;String&gt; | 否 | 删除分类 ID 列表 |
| categorySortChanges | array | 否 | 排序变更（categoryId + sortOrder） |
| productChanges | Object | 否 | key=分类ID或临时ID，value=`{added: spuIds[], removed: spuIds[]}` |
| forcePublish / confirmReplace | Boolean | 否 | 语义同 publish |

### 出参

同 publish（success / conflictTemplates / emptyCategories）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.save-and-publish","input":{"id":"6800012345678901234","categoryAdditions":[{"tempId":"tmp-1","name":"秋季新品","parentId":"0","level":1,"sortOrder":0}],"forcePublish":false,"confirmReplace":false},"summary":"新增秋上新分类并直接发布"}
```

---

## ✅ 下线 — ops.merchant.category-nav.offline

- 🔴 商业影响（C 端立即失去该导航）
- **服务端前置约束**：**默认兜底模板（isDefault）不可下线、不可删除**。

### 入参

路径 `id`（模板 ID）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.offline","input":{"id":"6800012345678901234"},"summary":"下线双11活动导航"}
```

---

## ✅ 设默认 — ops.merchant.category-nav.set-default

- 🔴 不可逆类商业影响（改变全租户兜底导航）

### 入参

路径 `id`（模板 ID）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.set-default","input":{"id":"6800012345678901234"},"summary":"把这个导航设为默认兜底导航"}
```

---

## ✅ 删除 — ops.merchant.category-nav.delete

- 🔴 不可逆
- **服务端前置约束**：**仅 `draft`/`offline` 状态的模板可删除**（published 需先下线）；**默认兜底模板（isDefault）不可删除**。

### 入参

路径 `id`（模板 ID）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.delete","input":{"id":"6800012345678901234"},"summary":"删除这个废弃的导航模板"}
```

---

## ✅ 清除无效绑定 — ops.merchant.category-nav.invalid-store-bindings.remove

- **说明**：清除已被删除门店的残留绑定（检测结果来自 invalid-store-bindings.check）。
- **⚠️ 注意**：若某模板的门店关联被**全部清除**，`storeScope` 会自动切换为 `ALL`（全门店可见）——需向用户说明此影响。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | array | 是 | `[{templateId, shopIds[]}]`，来自 check 结果 |

### 出参

`removedCount`（实际移除数量）。

### 调用示例

```json
{"capability":"ops.merchant.category-nav.invalid-store-bindings.remove","input":{"items":[{"templateId":"6800012345678901234","shopIds":["5600012345678901234"]}]},"summary":"清掉这个模板里已删除门店的残留绑定"}
```
