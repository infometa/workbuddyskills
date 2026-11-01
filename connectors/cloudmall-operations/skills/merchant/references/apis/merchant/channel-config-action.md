# 商户域 — 渠道配置写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-channel.md`；现值读取（分页/级联下拉）先读 `channel-config-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：channel-config.batch-add 批量新增渠道 · channel-config.batch-delete 批量删除渠道 🔴

---

## ✅ 批量新增渠道 — ops.merchant.channel-config.batch-add

- 支持层级嵌套一次提交

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| list | Array | ✅ | ≥1 项 |
| list[].channelName | String | ✅ | 渠道名称 |
| list[].id | String | 否 | 已有节点ID——**给已有渠道挂子级时传父节点 id 并在 nextChannelLevelList 里放新子级** |
| list[].nextChannelLevelList | Array | 否 | 子渠道列表（递归同结构） |

**层级规则（以服务端实现为准）**：channelLevel/parentId 字段**后端忽略不消费**——层级与父子关系完全由**嵌套深度**决定（顶层项恒为一级，逐层 +1）。给已有渠道挂子级：`{id: 父渠道ID, nextChannelLevelList: [{channelName: 新子级}]}`。

### 调用示例

```json
{"capability":"ops.merchant.channel-config.batch-add","input":{"list":[{"channelName":"抖音","nextChannelLevelList":[{"channelName":"直播带货"}]}]},"summary":"新增抖音及其直播带货子渠道"}
```

---

## ✅ 批量删除渠道 — ops.merchant.channel-config.batch-delete

- 🔴 不可逆——删除渠道影响使用该渠道的追踪归因，执行前确认清单
- **⚠️ 级联行为**：顶层项恒按一级处理——一级 `isDelete=1` 会**级联删除其全部二/三级子渠道**；若要删二级节点，须将其嵌套在父节点（父 `isDelete≠1`）的 `nextChannelLevelList` 中传入，**直接放顶层会被当一级处理导致其三级子节点不被删（孤儿数据）**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| list | Array | ✅ | ≥1 项 |
| list[].id | String | ✅ | 渠道节点ID |
| list[].isDelete | Integer | ✅ | 1=删除 |
| list[].nextChannelLevelList | Array | 否 | 子渠道列表（递归同结构） |

### 调用示例

```json
{"capability":"ops.merchant.channel-config.batch-delete","input":{"list":[{"id":"6500012345678901234","isDelete":1}]},"summary":"删除废弃渠道"}
```
