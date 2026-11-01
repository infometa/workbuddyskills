# 商户域 — 风格配置与底部导航写操作契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-visual.md`；现值读取（风格详情/方案列表与详情）先读 `theme-tabbar-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：theme.save 保存风格配置草稿 · theme.publish 发布风格配置 🔴 · tabbar-scheme.create 创建导航方案 · tabbar-scheme.copy 复制导航方案 · tabbar-scheme.save 保存导航方案 · tabbar-scheme.publish 发布导航方案 🔴 · tabbar-scheme.offline 下线导航方案 🔴 · tabbar-scheme.set-default 设默认导航 🔴 · tabbar-scheme.delete 删除导航方案 🔴

---

## ✅ 保存风格配置草稿 — ops.merchant.theme.save

- 🟡 草稿态（不生效，publish 后才影响 C 端）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| colors | Map&lt;String,String&gt; | 是 | CSS 变量名→色值映射（非空；服务端只校验非空，**不校验变量名/色值合法性**——键集以 C 端消费的 CSS 变量为准，编辑时以 detail 回填为基础修改，不要自行发明变量名） |
| spacingMode | String | 是 | `compact` / `airy` / `premium` / `custom`（小写） |
| spacingVars | Map&lt;String,String&gt; | 是 | CSS 变量名→间距/圆角值映射（非空；键集纪律同 colors） |
| brandLogo | String | 否 | 品牌 Logo 图片 URL（COS 地址） |

### 调用示例

```json
{"capability":"ops.merchant.theme.save","input":{"colors":{"--semantic-color-brand-primary":"#1677FF"},"spacingMode":"compact","spacingVars":{"--spacing-card-gap":"8px"}},"summary":"把主品牌色改为蓝色并暂存草稿"}
```

---

## ✅ 发布风格配置 — ops.merchant.theme.publish

- 🔴 全租户 C 端视觉生效；无入参；执行后回读 detail 确认 `status=1`。

### 调用示例

```json
{"capability":"ops.merchant.theme.publish","input":{},"summary":"发布新的视觉风格"}
```

---

## ✅ 创建导航方案 — ops.merchant.tabbar-scheme.create

- 🟡 草稿态

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 是 | 1-20 字 |

### 出参（原始数据）

- **路径参数来源**：`id`（新方案 ID，后续操作路径参数）

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.create","input":{"name":"双11活动导航"},"summary":"新建一个双11活动导航方案"}
```

---

## ✅ 复制导航方案 — ops.merchant.tabbar-scheme.copy

- 🟡 草稿态（副本为草稿）

### 入参

路径 `id`（源方案 ID）。

### 出参（原始数据）

- `id`（副本 ID）+ `name`（副本名）。

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.copy","input":{"id":"7500012345678901234"},"summary":"复制当前线上导航做一版改版"}
```

---

## ✅ 保存导航方案 — ops.merchant.tabbar-scheme.save

- 🟡 草稿态；PUT /{id}/save，**全量 Tab 列表提交**（stereo ≤1）
- **⚠️ 注意**：save 会把方案状态**置回 draft**——对已发布方案保存会使其退出发布（C 端导航风险）；仅对草稿方案操作可避免

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | 是 | 路径参数，方案 ID |
| name | String | 是 | ≤20 字 |
| navStyle | String | 是 | `normal` / `stereo`（小写） |
| bgColorMode | String | 是 | `system` / `custom`（custom 时 bgColor 生效） |
| cornerRadius | String | 是 | `straight` / `round` / `large-round` |
| iconColorMode | String | 是 | `system` / `custom`（custom 时 defaultColor/selectedColor 生效） |
| tabs | array | 是 | 非空；项：`label`（≤4 字）/`iconType`（system/custom）/`iconSystemId`/`iconDefaultUrl`/`iconSelectedUrl`/`pageType`（preset/custom）/`pagePath`/`sortOrder`（≥0，必填）/`tabStyle`（normal/stereo，**stereo 全方案最多 1 个**）/`showLabel`。**发布校验硬性要求每个 Tab 的 `label`、`iconDefaultUrl`、`iconSelectedUrl`、`pagePath` 四项非空**——`iconSystemId` 只是系统图标标识，**不能替代图标 URL**：即使选系统图标（iconType=system），也必须同时给出 `iconDefaultUrl`/`iconSelectedUrl`（内联 SVG data URL 形态，如 `data:image/svg+xml;base64,...`）。拿不到现成值时，先读当前线上方案或任一完整方案的 detail，复用其 Tab 的图标 URL，不要只填 iconSystemId 留空 URL |

### 出参

`version`（integer，每次保存递增）。

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.save","input":{"id":"7500012345678901234","name":"双11活动导航","navStyle":"normal","bgColorMode":"system","cornerRadius":"round","iconColorMode":"system","tabs":[{"label":"首页","iconType":"system","iconSystemId":"home","iconDefaultUrl":"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSIjNjY2NjY2IiBkPSJNMTIgM2w5IDhoLTN2OWgtNXYtNmgtMnY2SDZ2LTlIM3oiLz48L3N2Zz4=","iconSelectedUrl":"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSIjMTY3N0ZGIiBkPSJNMTIgM2w5IDhoLTN2OWgtNXYtNmgtMnY2SDZ2LTlIM3oiLz48L3N2Zz4=","pageType":"preset","pagePath":"/pages/index/index","sortOrder":0},{"label":"分类","iconType":"system","iconSystemId":"category","iconDefaultUrl":"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSIjNjY2NjY2IiBkPSJNNCA0aDd2N0g0ek0xMyA0aDd2N2gtN3pNNCAxM2g3djdINHpNMTMgMTNoN3Y3aC03eiIvPjwvc3ZnPg==","iconSelectedUrl":"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSIjMTY3N0ZGIiBkPSJNNCA0aDd2N0g0ek0xMyA0aDd2N2gtN3pNNCAxM2g3djdINHpNMTMgMTNoN3Y3aC03eiIvPjwvc3ZnPg==","pageType":"preset","pagePath":"/pages/category/index","sortOrder":1}]},"summary":"保存双11导航方案的两个 Tab 配置"}
```

> 示例要点：每个 Tab 都带 `iconSystemId` + `iconDefaultUrl` + `iconSelectedUrl` 三者齐全——系统图标也要有图标 URL。没有现成图标时，先读当前线上方案的 detail，复用其对应 Tab 的图标 URL。

---

## ✅ 发布导航方案 — ops.merchant.tabbar-scheme.publish

- 🔴 C 端生效，**顶替当前发布**（同一租户同时仅 1 个 published）——确认用户知悉顶替语义
- **发布前服务端校验**（不满足直接拒绝）：Tab 数量 2-5；每个 Tab 的 `label`、`iconDefaultUrl`、`iconSelectedUrl`、`pagePath` 非空；`pagePath` 以 `/` 开头且仅含字母/数字/`-`/`_`/`/`
- **被拒「Tab 信息不完整」时的处置**：回读该方案 detail 找出缺字段的 Tab → 补全（系统图标从线上方案 detail 复用图标 URL）→ save 全量重提 → 再 publish；不要只补 `iconSystemId`（它不是图标 URL，不能过校验）

### 入参

路径 `id`（方案 ID）。

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.publish","input":{"id":"7500012345678901234"},"summary":"发布双11活动导航"}
```

---

## ✅ 下线导航方案 — ops.merchant.tabbar-scheme.offline

- 🔴 C 端失去该导航，下线前确认有默认兜底

### 入参

路径 `id`（方案 ID）。

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.offline","input":{"id":"7500012345678901234"},"summary":"下线双11活动导航"}
```

---

## ✅ 设默认导航 — ops.merchant.tabbar-scheme.set-default

- 🔴 改全租户兜底导航

### 入参

路径 `id`（方案 ID）。

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.set-default","input":{"id":"7500012345678901234"},"summary":"把这个方案设为默认兜底导航"}
```

---

## ✅ 删除导航方案 — ops.merchant.tabbar-scheme.delete

- 🔴 不可逆；**仅 draft/offline 且非默认兜底可删**（published 需先下线）

### 入参

路径 `id`（方案 ID）。

### 调用示例

```json
{"capability":"ops.merchant.tabbar-scheme.delete","input":{"id":"7500012345678901234"},"summary":"删除这个废弃的草稿导航方案"}
```
