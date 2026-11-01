# 商品域 — 评价处理流程

> 对应契约：`apis/product/review-query.md`（搜索/Tab计数/详情/模板/统计/关键词/设置查询/导出）、`apis/product/review-action.md`（回复/审核/关键词/模板维护/设置保存）。概念知识：`references/domains/product-concepts.md`，评价状态机与驳回原因枚举：`references/domains/product-enums.md`；写操作共同纪律见 `product-core.md`。

---

## 评价处理

**场景**：评价的查询、回复与审核。

### 操作步骤

1. **总览**：`ops.product.review.tab-count`（各状态数量）→ `review.search`（按状态/星级/商品/时间过滤）
2. **看全文**：`review.detail`（含图片与追评）——⚠️ 手机号服务端已脱敏，昵称等身份信息为原始值：身份类字段**禁止转述给终端用户**，只用于运营核对
3. **执行**：
   - 回复：`review.reply`（可先 `review.reply-templates` 参考模板，但 content 传最终文案）——**回复公开可见，文案先给用户过目**；**前置：仅审核通过态（APPROVED/AUTO_APPROVED/TIMEOUT_APPROVED）可回复**，待审/已拒评价回复会被拒；已通过的违规评价唯一补救就是回复（无下线能力）
   - 审核：`review.audit`（单条）/ `batch-audit`（批量，≤100 条一批）/ `append-audit`（追评——id 用**追评记录自身ID**，非主评价ID），APPROVE/REJECT；**驳回仅对待审核（PENDING_AUDIT）生效，终态不可变更**——批量驳回前先按 PENDING_AUDIT 过滤；rejectReason 用枚举（SPAM/INAPPROPRIATE/IRRELEVANT/OTHER，OTHER 补 rejectRemark）
4. **核验**：`review.detail`/`review.search` 回读状态

### 看板分析

统计五项（overview / trend / star-distribution / word-cloud / product-ranking）用于向用户汇报评价健康度，全部只读。

### 关键词与设置维护

1. **关键词**：候选池 `review.keyword-candidates` → 批量启用 `keyword-batch-enable` 或单条 `keyword-enable` / `keyword-disable` / `keyword-reject`（⚠️ 服务端无前置状态校验，先读现态再操作；已启用列表 `review.keywords-enabled`）
2. **评价设置**（全局配置，改前确认）：`review.setting-get` 读现态 → `review.setting-save`（审核时效/默认好评/追评窗口/评分维度）
3. **导出**：`review.export`（URL 型契约）
