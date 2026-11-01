# 商户域 — 组织节点写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-store.md`；现值读取（组织树/节点搜索）先读 `org-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：org.create 新建组织节点 · org.update 编辑组织节点 · org.delete 删除组织节点 🔴 · org.batch-delete 批量删除组织节点 🔴 · org.import 导入组织节点 🔴

---

## ✅ 新建组织节点 — ops.merchant.org.create

- **约束**：HQ 不可手动创建；门店必须挂 REGION 下（服务端校验，存量例外仅限历史数据）
- **提交前两步自查（先问后写）**：
  1. **层级白名单自查**：确认目标父节点类型与新建类型组合合法（HQ→建 REGION、REGION→建 STORE），"REGION 下建 REGION"先本地判非法并说明，不提交换取服务端拒绝；
  2. **类型歧义必须追问**：用户指令中的"××分部/××大区"等命名不能作为 type 的判定依据——节点类型（区域还是门店节点）用户未明确给出时先向用户确认，禁止按现有同名节点类比推断；address 等字段同样须来自用户，缺失就不传或先问，不编造。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | String | ✅ | `REGION`/`STORE`——**PICKUP 不可创建**（暂不在组织树，传即被拒）；层级白名单：REGION 下建 STORE、STORE 下不可再建 |
| name | String | ✅ | ≤50 字 |
| parentId | String | ✅ | 父节点 ID——**实际必填**（一级节点仅允许 HQ 品牌总部，而 HQ 不可手动创建，故省略必失败）；合法：HQ→建 REGION、REGION→建 STORE |
| code | String | 否 | 组织编号，1~30 位字母数字，全局唯一 |
| address | String | 否 | ≤200 字 |
| contactPhone | String | 否 | — |

### 出参（原始返回）

`data` 为新建节点对象，含 `id`。

### 调用示例

```json
{"capability":"ops.merchant.org.create","input":{"parentId":"7310012345678901234","type":"REGION","name":"华南大区"},"summary":"创建华南大区区域节点"}
```

---

## ✅ 编辑组织节点 — ops.merchant.org.update

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 节点ID |
| name | String | 否 | ≤50 字 |
| code | String | 否 | 1~30 位字母数字 |
| address | String | 否 | ≤200 字 |
| contactPhone | String | 否 | — |
| status | String | 否 | `ACTIVE`/`INACTIVE` |
| parentId | String | 否 | 更换上级节点；不传不变更 |

### 出参（原始返回）

无返回数据。

### 调用示例

```json
{"capability":"ops.merchant.org.update","input":{"id":"7300012345678901234","name":"华南大区","contactPhone":"0755-88888888"},"summary":"更新区域节点联系方式"}
```

---

## ✅ 删除组织节点 — ops.merchant.org.delete

- 🔴 不可逆；有子节点时被拒绝（子节点保护），须先处理子节点

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 节点ID |

### 调用示例

```json
{"capability":"ops.merchant.org.delete","input":{"id":"7300012345678901234"},"summary":"删除无子节点的区域节点"}
```

---

## ✅ 批量删除组织节点 — ops.merchant.org.batch-delete

- 🔴 不可逆；子节点保护同样生效

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 1..100 个节点ID |

### 出参（原始返回）

`{deletedCount, skippedCount, ...}` 部分失败逐条报告。

### 调用示例

```json
{"capability":"ops.merchant.org.batch-delete","input":{"ids":["7300012345678901234"]},"summary":"批量删除空区域节点"}
```

---

## ✅ 导入组织节点 — ops.merchant.org.import

- 🔴 批量写（同步导入，每行独立事务）
- **传输形态**：multipart 文件型——文件经 multipart file part 传递（本地路径不入 input）。**模板获取**：管理后台「组织管理-导入-下载模板」。

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 组织 Excel（.xlsx，≤10MB） |

### 出参（原始数据）

- **展示字段**：`taskId`（可选）、`totalCount`、`successCount`、`failureCount`、`hasFailureDetail`、`failureDetailUrl`（⚠️ 后端暂未生成失败明细文件，恒为 null——失败数以 failureCount 为准）
- ⚠️ 同步导入通常不设置 `status`（null）——**不要把 status=null 当「处理中」**。

### 调用示例

```json
{"capability":"ops.merchant.org.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"导入这批组织架构 Excel；文件由客户端 multipart 提供"}
```
