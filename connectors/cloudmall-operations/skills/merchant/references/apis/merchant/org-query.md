# 商户域 — 组织节点查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-store.md`；写操作见 `org-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：org.tree 组织树 · org.search 组织节点搜索

---

## ✅ 组织树 — ops.merchant.org.tree

- **语义**：全量组织树（总部→区域→门店/自提点节点），内存递归构建

### 入参（无）

### 出参（数组，树形）

- **关键字段来源**：`id`（→ 编辑/删除/建门店的 orgNodeId）、`storeId`（STORE 节点关联门店ID）、`children[].id`
- **枚举字段**：`type`（HQ/REGION/STORE/PICKUP——PICKUP 为历史预留，当前代码不产生）、`status`（ACTIVE/INACTIVE）、`storeStatus`（STORE 节点关联门店四态）、`storeType`（PHYSICAL/VIRTUAL）、`deletable`（boolean）
- **格式敏感字段**：`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.org.tree","input":{},"summary":"查看组织架构树"}
```

---

## ✅ 组织节点搜索 — ops.merchant.org.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| keyword | String | 否 | 名称/编号模糊匹配 |
| type | String | 否 | `HQ`/`REGION`/`STORE`（PICKUP 历史预留，当前不出现） |
| status | String | 否 | `ACTIVE`/`INACTIVE` |
| parentId | String | 否 | 父节点ID |
| address | String | 否 | 地址模糊匹配 |
| createdTimeStart / createdTimeEnd | String | 否 | 创建时间区间（yyyy-MM-dd HH:mm:ss） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`、`records[].parentId`
- **枚举字段**：`type`、`status`、`childCount`（子节点数）、`deletable`（boolean）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.org.search","input":{"pageNum":1,"pageSize":20,"keyword":"华南","type":"REGION"},"summary":"搜索华南相关区域节点"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 组织导出 / 模板下载 | 二进制文件流响应；产品决策仅开放 URL 型导出，此型走管理后台 |
