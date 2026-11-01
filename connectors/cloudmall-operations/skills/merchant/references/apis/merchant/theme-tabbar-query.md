# 商户域 — 风格配置与底部导航查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-visual.md`；写操作见 `theme-tabbar-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **核心模型**：
> - 风格配置租户级单例：`status` 0=草稿 / 1=已发布；detail 优先返回草稿态（无记录 data=null，前端用默认值兜底）。
> - TabBar 方案多方案：`draft`/`published`/`offline`；**同一租户同时仅 1 个 published**（新发布顶替旧发布）；默认兜底方案仅 1 个；同一方案 stereo Tab 最多 1 个。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：theme.detail 风格配置查询 · tabbar-scheme.list 导航方案列表 · tabbar-scheme.detail 导航方案详情

---

## ✅ 风格配置查询 — ops.merchant.theme.detail

- 无入参（租户级单例）

### 出参（原始数据）

- **枚举字段**：`status`（0=草稿 / 1=已发布，整数）
- **嵌套结构**（`configJson`）：`colors`（Map：CSS 变量名→色值，如 `"--semantic-color-brand-primary"`→`"#1677FF"`）、`spacingMode`（compact/airy/premium/custom，小写）、`spacingVars`（Map：CSS 变量→间距/圆角值）、`brandLogo`（品牌 Logo URL）
- data 为 null 时=从未配置，向前端默认值兜底——**null ≠ 配置为空**。

### 调用示例

```json
{"capability":"ops.merchant.theme.detail","input":{},"summary":"看下当前的店铺视觉风格配置"}
```

---

## ✅ 导航方案列表 — ops.merchant.tabbar-scheme.list

### 入参

pageNum（≥1）/ pageSize（≤100，默认 20）/ status（`draft`/`published`/`offline`，小写，可空）。

### 出参（分页，原始数据）

- **路径参数来源**：`records[].id`（→ 所有 {id} 路径参数）
- **枚举字段**：`status`（draft/published/offline）、`isDefault`
- **展示字段**：`name`、`tabCount`、`tabs[]`（label/iconUrl 缩略）、`updatedBy`
- **格式敏感字段**：`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.list","input":{"pageNum":1,"pageSize":20,"status":"published"},"summary":"看下当前在线的底部导航方案"}
```

---

## ✅ 导航方案详情 — ops.merchant.tabbar-scheme.detail

- 完整编辑回填结构

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 方案 ID |

### 出参（原始数据）

- **枚举字段**：`navStyle`（normal/stereo）、`bgColorMode`（system/custom）、`cornerRadius`（straight/round/large-round）、`iconColorMode`（system/custom）
- **关键字段来源**：`version`（integer，→ save 的并发参考）
- **嵌套结构**：`bgColor`、`defaultColor`/`selectedColor`、`tabs[]`（id/label/iconType/iconSystemId/iconDefaultUrl/iconSelectedUrl/pageType/pagePath/sortOrder/tabStyle/showLabel）。`tabs[].iconDefaultUrl`/`iconSelectedUrl` 为图标 URL（系统图标是内联 SVG data URL）——保存/发布校验必填，缺现成图标值时从线上方案的 detail 复用

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.detail","input":{"id":"7500012345678901234"},"summary":"取这个导航方案的完整配置用于编辑"}
```

---

## ⛔ 未开放（风格与导航）

| 操作 | 不开放理由 |
|------|-----------|
| 无 | 本模块全部端点已开放 |
