# 商户域 — 视觉配置流程（风格 / 底部导航）

> 对应契约：`apis/merchant/theme-tabbar-query.md` / `theme-tabbar-action.md`；概念知识：`references/domains/merchant-concepts.md`，状态机见 `references/domains/merchant-enums.md`；写操作共同纪律见 `merchant-core.md`。

**场景**：C 端全局视觉（风格/底部导航）配置与发布。

---

## 风格配置

1. `ops.merchant.theme.detail` 读现态（data=null=从未配置）→
2. `theme.save`（草稿 upsert）→ 复述配色/间距变更 → `theme.publish`（全租户生效）→ 回读 detail 确认 `status=1`。

- colors/spacingVars 的键集以 C 端消费的 CSS 变量为准，编辑时以 detail 回填为基础修改，不自行发明变量名。

## 底部导航（TabBar）

1. `ops.merchant.tabbar-scheme.list` 读现态 →
2. `tabbar-scheme.create`（空壳）→ `tabbar-scheme.save`（全量 Tab 列表；stereo ≤1）→ 复述 Tab 结构 → `tabbar-scheme.publish`（**顶替当前发布**，确认用户知悉）→ 回读 list。
3. 复制改版用 `copy`；下线前确认有默认兜底；设兜底用 `set-default`；仅 draft/offline 且非默认兜底可删。
