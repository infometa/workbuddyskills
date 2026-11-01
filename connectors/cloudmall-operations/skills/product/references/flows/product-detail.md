# 商品域 — 商详装修与 FAQ 维护流程

> 对应契约：`apis/product/detail-layout-query.md`（配置查询/操作日志）、`apis/product/detail-layout-action.md`（编辑锁/配置保存）、`apis/product/faq-query.md`（FAQ 分页）、`apis/product/faq-action.md`（FAQ 增改/启停/排序/删除）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 商详装修（锁协议流程）

**场景**：调整商详页模块顺序/启停（带编辑锁协议）。

1. **拿锁**：`ops.product.detail-layout.lock-acquire`——被他人持有时返回 `locked=true, lockedBy=<持锁人>`，向用户报告后停止（不等待、不强行操作）
2. **读现态**：`ops.product.detail-layout.config-get`（9 模块排序与启停 + 锁状态）→ 与用户确认调整
3. **保存**：`ops.product.detail-layout.config-save`（全量替换）
4. **释放**：`ops.product.detail-layout.lock-release`（保存完成或放弃后释放，TTL 10 分钟不续租也会自动过期）
- 排查历史：`ops.product.detail-layout.logs`（最近 20 条，含前后快照）

## FAQ 维护

**场景**：维护商详常见问题。

1. **查列表**：`ops.product.faq.page`（按生效状态/关键词筛选）→ 取 `records[].id`
2. **建/改**：`faq.create`（sort 不传追加末尾）/ `faq.update`（sort 不传保留原值）
3. **启停**：`faq.toggle`（返回新状态）；**排序**：`faq.reorder`（数组顺序=最终顺序）
4. **删除**：🔴 `faq.delete` 确认问题内容后执行
