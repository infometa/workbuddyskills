# 商户域 — 渠道配置与渠道追踪流程

> 对应契约：`apis/merchant/channel-config-query.md` / `channel-config-action.md`（渠道配置字典）、`apis/merchant/channel-trace-query.md` / `channel-trace-action.md`（渠道追踪单与明细）；概念知识：`references/domains/merchant-concepts.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

---

## 渠道配置（投放渠道字典，层级树）

```
channel-config.search 现状 → batch-add（支持层级嵌套；层级由嵌套深度决定，channelLevel/parentId 后端忽略）/ batch-delete
  └ 下拉级联选节点：channel-config.select（按 channelLevel/parentId 过滤；parentId 与 parentIds 必传其一，查一级传 "0"）
```

## 渠道追踪（投放追踪单与触达明细）

1. `ops.merchant.channel-trace.custom-channels` 查渠道字典（缺则 `custom-channel.add` 补建）→
2. `channel-trace.add`（pushName + channelType + 层级归因）创建追踪单 →
3. 复盘：`channel-trace.list`/`detail` 看配置 → `channel-trace-detail.list` / `member-behaviors` 看触达与行为 →
4. 停启用 `channel-trace.update-status`；批量维护走 `channel-trace.import`（multipart）/`channel-trace.export`。

- `pushPageInfo`（投放页面）与 `posterConfig`（海报配置）为**回填透传** JSON 字符串——编辑时从 detail 回填原文，不自行构造。
- 时间筛选为毫秒时间戳。
