# 商户域 — 素材库查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-material.md`；写操作见 `material-action.md`。
> 覆盖素材中心的检索、签名 URL 与预置分组映射。出参为上游**原始业务数据**（不裁剪字段）。
> **核心枚举**：素材类型 `fileType` image / video / audio；审核状态 `auditStatus` auditing=审核中 / approved=已通过 / rejected=已驳回 / manual_review=人工复审。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：material.search 素材分页 · material.group-tree 素材分组树 · material.batch-get-urls 批量获取签名 URL · material.group-preset-mapping 预置分组映射

---

## ✅ 素材分页 — ops.merchant.material.search

- **说明**：分页检索素材库文件；keyword 对文件名模糊匹配。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| fileType | String | 否 | image / video / audio（严格小写） |
| groupId | String | 否 | 分组 ID（来自分组树出参 `id`；查未分组素材时省略） |
| keyword | String | 否 | 文件名关键词，≤100 字符 |
| sortField | String | 否 | 排序字段：uploadTime / fileName |
| sortOrder | String | 否 | asc / desc |
| auditStatus | String | 否 | auditing / approved / rejected / manual_review |

### 出参（分页，原始数据）

- **路径参数来源**：`records[].materialId`、`records[].groupId`
- **枚举字段**：`fileType`（image/video/audio）、`auditStatus`（auditing/approved/rejected/manual_review）
- **格式敏感字段**：`fileSize`（字节数，整数）；`createdTime`（yyyy-MM-dd HH:mm:ss）
- ⚠️ **`fileUrl`/`thumbnailUrl` 为 COS 预签名地址（分钟级时效）**——不持久化、不当稳定链接转述；需要给用户看时提示链接有时效。
- 展示型字段 `fileName/groupName` 可直接透传。

### 调用示例

```json
{"capability":"ops.merchant.material.search","input":{"pageNum":1,"pageSize":20,"fileType":"image","keyword":"banner"},"summary":"在素材库里找 banner 图片"}
```

---

## ✅ 素材分组树 — ops.merchant.material.group-tree

- **说明**：查询素材分组树（含各级分组与素材数量统计）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fileType | String | 否 | 按素材类型过滤：image / video / audio；省略=全部 |

### 出参（树形列表，原始数据）

- **路径参数来源**：`[].id`（分组 ID → 素材分页的 groupId 筛选）；`[].children[].id` 同
- **格式敏感字段**：根节点含 `totalCount`（全部素材数）与 `ungroupedCount`（未分类数），均为整数
- 展示型字段 `groupName/materialCount` 可直接透传。

### 调用示例

```json
{"capability":"ops.merchant.material.group-tree","input":{"fileType":"image"},"summary":"查看图片素材的分组结构与数量"}
```

---

## ✅ 批量获取签名 URL — ops.merchant.material.batch-get-urls

- **说明**：按素材 ID 批量换取新鲜 COS 签名 URL。**按 ID 精确复查素材内容（看图/识别图片）的唯一入口**；不要用分页接口翻列表代替。返回的新 URL 有效期 60 分钟。
- **注意**：不存在或已删除的 ID **静默不返回**（不出现在结果中也不报错）——须逐个比对请求与响应，明确告知用户哪个 ID 未取到。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialIds | array&lt;String&gt; | 是 | 素材 ID 列表（十进制字符串），1..50 项 |

### 出参（列表，原始数据）

- **路径参数来源**：`[].materialId`
- **格式敏感字段**：`[].fileUrl`（新鲜签名 URL，60 分钟时效——不持久化、不当稳定链接转述）

### 调用示例

```json
{"capability":"ops.merchant.material.batch-get-urls","input":{"materialIds":["6500012345678901234","6500012345678901235"]},"summary":"获取这两个素材的最新访问链接"}
```

---

## ✅ 预置分组映射 — ops.merchant.material.group-preset-mapping

- **说明**：按预置分组名称换取分组 ID（商品模块联动场景）；Map 值为十进制字符串分组 ID。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupNames | array&lt;String&gt; | 是 | 预置分组名称列表（query 参数，多值重复传递） |

### 出参（Map&lt;String, String&gt;，原始数据）

- **路径参数来源**：value 即分组 ID（→ 移动分组/上传素材的 `groupId`/`targetGroupId`）

### 调用示例

```json
{"capability":"ops.merchant.material.group-preset-mapping","input":{"groupNames":["商品主图","详情图"]},"summary":"查商品主图和详情图预置分组的 ID"}
```

---

## ⛔ 未开放（素材库）

| 操作 | 不开放理由 |
|------|-----------|
| 素材引用注册/注销（reference/register、unregister） | 业务系统间联动回调（商品发布等由业务服务登记），非运营手工操作 |
