# 商户域 — 素材查找与上传流程

> 对应契约：`apis/merchant/material-query.md`（检索/分组树/签名 URL）、`apis/merchant/material-action.md`（上传/改名/移动/删除/分组维护）；概念知识：`references/domains/merchant-concepts.md`；写操作共同纪律见 `merchant-core.md`。

---

## 素材查找

```
[可选] 分组树（material.group-tree，按 fileType 过滤）→ 取分组 id
  → 素材分页（material.search，keyword/fileType/groupId/auditStatus 筛选）
  → fileUrl/thumbnailUrl 为时效签名地址——提示用户链接有时效，不当稳定链接转述
```

- 按 ID 精确复查素材内容（看图/识别图片）用 `material.batch-get-urls` 换新鲜签名 URL，不要翻分页代替。

## 素材上传

```
用户明确要求上传本地文件
  → [可选] 查分组树取得 groupId
  → 文件型执行器用 ops.merchant.material.upload 单次 multipart 上传
  → 返回 materialId 与 auditStatus；审核中不表述为已审核通过
  → 当前运行时不能传文件时，停止并说明需要文件型 capability；不把本地路径塞进结构化 input
```

## 参数来源

| 参数 | 来源 |
|------|------|
| groupId（素材） | 素材分组树出参 `id` |
| 关键词/类型 | 用户提供 |
