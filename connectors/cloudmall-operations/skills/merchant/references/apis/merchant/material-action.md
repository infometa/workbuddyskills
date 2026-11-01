# 商户域 — 素材库写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-material.md`；现值读取（素材分页/分组树/签名 URL）先读 `material-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。**上传为文件型 multipart 传输形态**（见 upload 锚点）。
> 能力索引：material.upload 素材上传 · material.move-group 素材移动分组 · material.batch-move-group 批量移动分组 · material.rename 素材改名 · material.delete 删除素材 🔴 · material.batch-delete 批量删除素材 🔴 · material.group.create 创建素材分组 · material.group.update 编辑素材分组 · material.group.delete 删除素材分组 🔴

---

## ✅ 素材上传 — ops.merchant.material.upload

- **调用面**：仅通过当前运行时的文件型 capability 传递文件；不要把本地路径放进结构化 input。
- **说明**：客户端读取本地文件，以一次 multipart 请求交给 Open；Open 直接调用既有运营素材上传接口，不生成 `fileId`，不暂存文件。

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 只能一个文件；文件内容而非本地路径 |
| fileType | String | 是 | image / video / audio，必须与 MIME 类型一致 |
| groupId | String | 否 | 目标素材分组 ID，来自 `ops.merchant.material.group-tree` |

大小上限：image 5 MiB、video 200 MiB、audio 50 MiB。扩展名和文件内容仍由既有业务接口校验。

### 调用示例

```text
capability: ops.merchant.material.upload
file: ./banner.png
fields: fileType=image, groupId=1234567890123456789
```

以下结构化数据是与文件参数配套的调用元数据；文件经 `input.file` 提供工作区路径或 `material:{素材ID}` 引用（见能力索引处说明与调用示例）：

```json
{"capability":"ops.merchant.material.upload","input":{"file":"uploads/图片素材.png", "fileType":"image","groupId":"1234567890123456789"},"summary":"上传本地 banner 图片到指定素材分组；文件由客户端 multipart 提供"}
```

成功返回业务接口原始 `data`，包括 `materialId`、`fileName`、`fileUrl`、`fileType`、`auditStatus`。`fileUrl` 是有时效的签名地址；上传成功不代表审核通过，应依据 `auditStatus` 告知用户。

文件写入会产生真实素材记录。用户明确要求上传后才能执行；超时或网络错误时不要盲目重复上传，先按文件名查询素材库确认结果。

---

## ✅ 素材移动分组 — ops.merchant.material.move-group

- 🟡 可逆写（可再移回）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialId | String | 是 | 素材 ID（十进制字符串） |
| targetGroupId | String | 否 | 目标分组 ID；null/省略=移出至未分类 |

### 调用示例

```json
{"capability":"ops.merchant.material.move-group","input":{"materialId":"6500012345678901234","targetGroupId":"6600012345678901234"},"summary":"把这张 banner 图移到活动物料分组"}
```

---

## ✅ 素材改名 — ops.merchant.material.rename

- 🟡 可逆写

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialId | String | 是 | 素材 ID（十进制字符串） |
| fileName | String | 是 | 新文件名，≤100 字符，仅中英文/数字/下划线/短横线 |

### 调用示例

```json
{"capability":"ops.merchant.material.rename","input":{"materialId":"6500012345678901234","fileName":"banner-首页改版"},"summary":"把这个素材改名为 banner-首页改版"}
```

---

## ✅ 删除素材 — ops.merchant.material.delete

- 🔴 不可逆——执行前向用户确认素材对象；被业务引用的素材由服务端保护（拒绝删除）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialId | String | 是 | 素材 ID（十进制字符串） |

### 调用示例

```json
{"capability":"ops.merchant.material.delete","input":{"materialId":"6500012345678901234"},"summary":"删除这张已确认不用的素材"}
```

---

## ✅ 批量移动分组 — ops.merchant.material.batch-move-group

- 🟡 可逆写；先向用户复述清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialIds | array&lt;String&gt; | 是 | 素材 ID 列表，1..100 项 |
| targetGroupId | String | 是 | 目标分组 ID（必填，不支持批量移出至未分类） |

### 调用示例

```json
{"capability":"ops.merchant.material.batch-move-group","input":{"materialIds":["6500012345678901234","6500012345678901235"],"targetGroupId":"6600012345678901234"},"summary":"把这批素材统一移到活动物料分组"}
```

---

## ✅ 批量删除素材 — ops.merchant.material.batch-delete

- 🔴 不可逆——执行前向用户确认完整清单；被引用素材由服务端跳过并返回明细

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialIds | array&lt;String&gt; | 是 | 素材 ID 列表，1..100 项 |

### 出参（原始数据）

- **展示字段**：`deletedCount`（已删除数）、`skippedCount`（跳过数）、`skippedMaterials[]`（`materialId`/`fileName`/`reason` 跳过明细）
- ⚠️ 部分成功语义：`skippedCount > 0` 时逐条向用户报告跳过原因。

### 调用示例

```json
{"capability":"ops.merchant.material.batch-delete","input":{"materialIds":["6500012345678901234","6500012345678901235"]},"summary":"删除这批确认作废的素材"}
```

---

## ✅ 创建素材分组 — ops.merchant.material.group.create

- 🟡 可逆写

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupName | String | 是 | 分组名称，≤30 字 |
| parentId | String | 否 | 父分组 ID；省略=根分组 |

### 出参（原始数据）

- **路径参数来源**：`id`（新分组 ID → 移动分组/上传素材的 groupId）

### 调用示例

```json
{"capability":"ops.merchant.material.group.create","input":{"groupName":"双11活动物料"},"summary":"新建一个双11活动物料分组"}
```

---

## ✅ 编辑素材分组 — ops.merchant.material.group.update

- 🟡 可逆写

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupId | String | 是 | 分组 ID（十进制字符串） |
| groupName | String | 是 | 新分组名称，≤30 字 |

### 调用示例

```json
{"capability":"ops.merchant.material.group.update","input":{"groupId":"6600012345678901234","groupName":"双11活动物料-终版"},"summary":"把分组改名为双11活动物料-终版"}
```

---

## ✅ 删除素材分组 — ops.merchant.material.group.delete

- 🔴 不可逆——确认分组及其素材归属；服务端对含素材/含子分组的分组有保护规则时以响应为准。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupId | String | 是 | 分组 ID（十进制字符串） |

### 调用示例

```json
{"capability":"ops.merchant.material.group.delete","input":{"groupId":"6600012345678901234"},"summary":"删除这个空的活动物料分组"}
```

删除与批量删除均为不可逆操作：执行前回读分组树/素材列表确认对象清单，执行后按需回读核验。超时或网络错误时结果不确定——先查询对象是否仍存在再决定如何说明，不盲目重复提交。
