# 数据标签域 — 动态人群包写操作契约

> 用于促销口令码和运营增量定向。概念知识：`references/domains/data-tag.md`；运营流程：`references/flows/data-tag.md`（动态人群包与促销闭环）；人群包现值读取先读 `crowd-query.md`，规则/手工标签见 `tag-action.md`。ID 与 UID 都使用十进制字符串；写操作须遵守入口 Skill 的风险档位、影响说明和回读纪律（确认由运行时权限模式兜底）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：data-tag.manual-tag.create-with-crowd 创建手工标签与动态人群包 · data-tag.manual-tag.add-users 批量添加用户

---

## ✅ 创建手工标签与动态人群包 — ops.data-tag.manual-tag.create-with-crowd

- 原子创建一个手工标签、标签值和状态为 ONLINE 的动态人群包。保存返回的 `tagId`、`tagValueId`、`crowdId`：促销定向使用 `tagValueId`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 标签名称（≤50 字符） |
| valueName | String | ✅ | 标签值名称（≤50 字符） |
| remark | String | — | 备注（≤500） |
| categoryId | String | — | 分类 ID |

### 调用示例

```json
{"capability":"ops.data-tag.manual-tag.create-with-crowd","input":{"name":"口令码-秋季活动","valueName":"已参与","remark":"促销活动定向人群"},"summary":"创建秋季活动动态定向人群"}
```

---

## ✅ 批量添加用户 — ops.data-tag.manual-tag.add-users

- `uids` 每批最多 500；`tagValueId` 与 `crowdId` 至少一个，优先传前者。仅 DYNAMIC 或 FILE_UPLOAD 人群包可增员。重复 UID 合并，`addedCount=0` 不表示失败。结果写入的 Redis 标签命中有秒级异步延迟

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uids | String[] | ✅ | UID 列表（非空，每批最多 500） |
| tagValueId | String | 条件 | 标签值 ID（与 crowdId 至少一个，优先传） |
| crowdId | String | 条件 | 人群包 ID |
| bizRefId | String | — | 业务引用标识 |

### 出参（原始返回）

`totalCount`、`addedCount`、`failedCount`、crowdId 与 messageId。

### 调用示例

```json
{"capability":"ops.data-tag.manual-tag.add-users","input":{"tagValueId":"6110000000000000001","uids":["6200000000000000001","6200000000000000002"],"bizRefId":"promotion-autumn-2026"},"summary":"将两名已确认会员加入秋季活动定向人群"}
```
