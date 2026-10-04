# Amazon 2026 Title + Item Highlights 政策

> **何时读取**：执行 title-writer 前必读（generate 与 split_legacy 均适用）。
> 埋词规则见同目录 `sif-keyword-embedding.md`，两份一起读。

生效：**2026-07-27**（除 **Media** 外全品类）

| 字段 | 上限 | 用途 |
|------|------|------|
| **Title** | 75 字符（含空格） | 移动端完整展示；只回答「产品是什么」 |
| **Item Highlights** | 125 字符（含空格） | 可搜索；承载材质、场景、功能收益、次级规格 |

## 为什么收紧：写给 AI 导购看，而不是写给搜索框看

Amazon 已把 Rufus 的商品知识与 Alexa+ 的个性化上下文整合为 **Alexa for Shopping**，
覆盖 App、网页搜索框与带屏设备。买家不再只敲关键词，而是提问：
「带狗徒步不漏水的水杯」「这两款有什么区别」。竞争从**搜索结果页坑位**变成
**AI 回答里的引用率与首推率**。

Title 变短不是削弱 SEO，而是把信息按机器可解析的方式**分流**到各模块。

## AI 导购评估 Listing 的 4 个问题（写作时逐条对齐）

| 问题 | AI 提取什么 | 本 Skill 的落点 |
|------|-----------|----------------|
| 1. 你到底是什么产品？ | 品类定义、基础参数 | **Title 前 50 字符**必须说清品类，不被修饰词干扰 |
| 2. 适合什么人与场景？ | 场景、受众、兼容设备 | **Item Highlights** |
| 3. 解决什么具体痛点？ | 防漏 / 便携 / 快充 / 易清洗 | 五点（本 Skill 只做 `handoff_keywords.bullets` 交接） |
| 4. 凭什么比同类更值得推？ | 差异化、认证、使用边界 | 五点 + A+；Highlights 可带 1 条核心差异 |

## 文案规格

- **Title**：≤75 字符（含空格）。结构 = **品牌 + 核心品类词 + 1 个关键属性 +（可选）1 个核心场景**。
  - 前 50 字符必须能独立回答「这是什么」。
  - 自然可读、可朗读（语音端会被念出来）；不堆砌、不并列多场景、不写促销语。
  - 无真实品牌时不虚构品牌。
- **Item Highlights**：≤125 字符（含空格）。写成 **1–2 句自然可读的完整句**，不是逗号分隔的词串。
  - 装：材质、推荐用途、适用场景、兼容设备/机型、核心差异、受众/尺寸。
  - 是 Title 的延伸，不重复 Title 原句、不复制五点全文。

## Title vs Item Highlights 分工

| 字段 | 应放 | 不应放 |
|------|------|--------|
| Title | 品牌、数量/规格、品类核心词、关键属性、必要场景/人群锚点 | 场景堆砌、多条卖点并列、促销语、关键词堆砌、痛点形容词长串 |
| Item Highlights | 迁出的材质、数量、规格、兼容、场景、功能收益、套装摘要 | 重复 Title 原句、复制五点全文、促销/物流词、无依据的功效承诺 |

## 官方示例（水瓶）

**优化前（92c）**

> Premium Stainless Steel Insulated Water Bottle – Keeps Drinks Cold 24 Hours, Hot 12 Hours, BPA-Free

**优化后**

- **Title（62c）**：`Premium Stainless Steel Insulated Water Bottle – BPA-Free`
- **Item Highlights（~95c）**：`Keeps drinks cold 24 hours, hot 12 hours. Ideal for gym, office, and outdoor adventures.`

## 拆分实例（旧堆词标题 → 新架构）

**旧（违规 + 语义断裂）**

> `65W USB C Charger Fast Charger for MacBook Pro iPad iPhone Samsung Type C Wall Charger Foldable Plug GaN Charger Adapter`

**新**

- Title：`VoltPro 65W GaN USB-C Charger, Foldable Plug`（44c）
- Item Highlights：`Compact travel charger for MacBook, iPad, iPhone and Samsung USB-C devices.`（74c）
- 迁走而非丢弃：兼容机型清单 → 五点 + 后台属性；功率分配边界 → 五点 5；折叠收纳场景 → A+。

**宠物水杯**

- Title：`PawGo Leakproof Dog Water Bottle for Travel`（43c）
- Item Highlights：`One-hand water release, leakproof lock, 19oz capacity for walks, hiking and car trips.`（87c）

## AI 问答承接自检（写完必做，零成本）

用 2–3 个买家会自然提出的问题，检查 Title + Item Highlights 能否被命中：

- `hiking with dog bottle that doesn't leak` → Highlights + 五点 3
- `water bottle for small dogs travel` → Title + Highlights
- `can I put it in a backpack` → 五点 3（本 Skill 标记为需五点承接）

命中不了就改写；两条问题都落在同一个字段说明信息没分流开。

## 必须淘汰的写法

| 淘汰 | 现状 |
|------|------|
| 堆满关键词就能被 AI 推荐 | 无序堆砌造成语义断裂，直接降低 AI 推荐信心 |
| 标题变短流量必跌 | 信息分流到 Highlights / 五点 / A+ / 后台属性，权重与体验更优 |
| Title 里塞满国家名、机型名 | 兼容清单进 Highlights 与后台属性，可读性和权重都更好 |
| 写成口语社交文案 | 既要自然语义，也要机器可识别的明确参数与边界 |
| 关键词在 AI 时代不重要 | 关键词从「堆砌」升级为「分流」：核心词进 Title，场景词进 Highlights，痛点词进五点 |

## 信息不得静默丢失

旧标题里的硬规格（尺寸、容量、功率、材质、兼容型号、数量）**不允许直接丢弃**。
`migration_map[].to` 必须显式落到：`title` / `highlights` / `bullets` / `backend_attributes` /
`aplus` / `dropped`，`dropped` 必须写明可丢原因（重复、促销语、无事实依据）。

## Media 类目豁免

Books / Music / Video 等 Media 类目仍按 `rule.hard.charset.title`（通常 ≤200），**不产出** Item Highlights。

## Charset 默认值（本 Skill 强制）

```yaml
TITLE_MAX: 75
HIGHLIGHTS_MAX: 125
```

即使 `rule.hard.charset.title` 仍为旧版 `[190, 200]`，非 Media 仍以 75 为硬上限。

## 卖家过渡要点

- 7/27 前可继续用旧标题，或提前改为 75c Title + Item Highlights
- 逾期未改：系统 AI 自动替换超长标题
- Item Highlights 内容**可搜索**，不影响 SEO
- 品牌卖家有 14 天审核窗口（Review Listings Changes）
