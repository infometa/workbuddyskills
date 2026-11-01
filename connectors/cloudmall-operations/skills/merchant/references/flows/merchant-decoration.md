# 商户域 — 装修页面排查流程（只读）

> 对应契约：`apis/merchant/decoration-page.md`（全部只读）；概念知识：`references/domains/merchant-concepts.md`；写操作共同纪律见 `merchant-core.md`。

**场景**：确认线上装修版本、诊断发布阻塞、排查绑定残留。全部只读；装修编辑与发布依赖当前未开放的可视化装修能力。

---

## 线上版本确认

```
装修页面分页（decoration-page.search，pageType=home，status=1）
  → 列表 version 与 publishedVersion 是否一致（不一致=有未发布草稿改动）
  → 版本列表（decoration-page.versions，status=1 即当前线上版本）
  → [可选] 版本详情（decoration-page.version-detail）对比历史配置
```

## 发布阻塞诊断

```
发布校验（decoration-page.binding-check）→ valid=false 时 message 直接转述
  └─ 常见原因：home 类型非默认首页未绑定门店
     → 绑定列表（decoration-page.bindings）确认当前绑定
     → 指引用户到运营端装修编辑器补绑定后发布
```

## 绑定残留排查

```
无效绑定检测（decoration-page.invalid-bindings）
  → 有残留（已删除门店仍绑定）→ 告知用户页面与门店清单，指引进运营端清除
```

## 参数来源

| 参数 | 来源 |
|------|------|
| pageId | 装修页面分页出参 |
| versionId | 版本列表出参 `id` |
