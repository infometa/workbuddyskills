---
name: mibao-index-policy
description: 执行本地增量盘点、严格内容哈希、资产台账、FTS 检索和带来源证据的结果返回。
---

# 盘点、索引与检索

使用 SourceRoot、ScanCandidate、FileInstance、Asset 和 Operation 分层保存路径事实与内容身份；完整扫描后才允许 missing 推断，内容哈希后才允许精确重复结论。

索引字段区分 A/B 技术事实、C 级模型候选和 D 级人工确认。AI 结果必须保留 evidence refs、模型/提示版本、置信度和复核状态；搜索结果返回来源、时间码/页码和命中理由。

`execution_core_v1` 通过零 MCP 的包内一次性入口开放 `inventory_build` 与 `inventory_search`。前者只在用户确认的源目录和独立项目目录间执行扫描、严格哈希、精确重复、FTS、失效检索文档清理与报告；后者只接受 `local-private` 项目，并在同一个已审计只读连接上检索，不修改索引。每个搜索结果必须带 FileInstance 证据引用并显式返回 `privacyMode=local-private`；旧隐私模式失败关闭而不自动迁移。

路径策略明确排除的单个文件名与 reparse 条目记录为 partial issue，不进入 FileInstance/Asset/FTS；不可读或无法完整枚举仍阻断。文件名查询可按点拆为多个白名单 token，其他 FTS 语法仍拒绝。`content.exactDuplicateGroupCount` 是本次严格提升计数；报告的 token 时点计数使用 `strict_as_of_exact_duplicate_group_count`，`current_exact_duplicate_group_count` 保持保守实时值 0。

WorkBuddy 宿主真正调用、报告文件回读和源目录不变仍须逐次验收；仓库测试、完整插件 MCP 或旧版上架状态不得写成当前用户素材已经处理。转换、OCR、ASR 与语义检索不在当前 operation 集合。
