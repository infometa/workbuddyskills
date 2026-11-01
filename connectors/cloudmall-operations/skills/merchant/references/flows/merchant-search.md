# 商户域 — 搜索运营流程（热搜词 / NLU·Rerank 干预 / 暗纹词）

> 对应契约：`apis/merchant/search-intervention-query.md` / `search-intervention-action.md`（热搜词与干预）、`apis/merchant/placeholder-query.md` / `placeholder-action.md`（暗纹词与场景）；概念知识：`references/domains/merchant-concepts.md`，枚举见 `references/domains/merchant-enums.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

---

## 热搜词与搜索干预

```
热搜词：hot-keyword.search 现状 → create/update（keyword ≤20 字符，权重越小越靠前）
  └ 生效窗口 startTime/endTime（yyyy-MM-dd HH:mm:ss），null=立即生效/长期有效
NLU 干预（改写/同义词/纠错/后缀替换）：nlu.search → nlu.create / nlu.update
  └ nlu_suffix_replace 的 ruleValue 可空，其余类型必填
Rerank 干预：
  ├ rerank_manual：queryText + actionType + actionValue 必填（置顶/过滤/提升/降权指定商品）
  ├ rerank_category_boost：fieldName + matchType(exact/contains) + matchValue + boostFactor(>0) 必填
  └ rerank_diversity：无参数
变更后核验：nlu.search / rerank.search 回读 + operation-logs 查操作记录
```

## 暗纹词与场景

暗纹词是 C 端搜索框的**占位提示文案**（与热搜词的「联想词」区分），按场景组织。

```
场景维护（placeholder-scene.create）→ 场景下配置占位词（placeholder-keyword.create，sceneId 来自场景出参）→ 按需启停（update-status）
```

场景 delete 前确认级联影响（场景下已有暗纹词时的级联行为以服务端响应为准）。
