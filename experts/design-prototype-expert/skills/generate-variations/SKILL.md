---
name: generate-variations
description: "Explores variations on an existing prototype. After a prototype exists, generates hi-fi variants along 2-3 design dimensions (warmth vs cold vs playful, loose vs dense density, light vs heavy visual weight). All variants share the same design system, differing only on selected axes. User picks or mixes."
trigger:
  - 用户需要在多个维度上探索不同方案时
  - make-prototype 完成后用户想看更多变体
  - 用户说"能不能换个感觉/氛围/密度"时
---

# 高保真变体（Generate Variations）

## 触发时机

- 用户在已确定的设计系统基础上，想沿不同维度探索方案时
- `make-prototype` 完成后，用户想看更多风格变体
- 用户提出"能不能换个感觉/氛围/密度"

## 前置条件

- **DesignSystemManifest** — 已建立的设计系统
- **PrototypeSpec** — 已有的高保真原型作为基线
- **WireframeSpec** — 布局已确定

## 执行内容

在已确定的设计系统基础上，沿 2-3 个维度产出高保真变体。每个变体必须遵循同一设计系统，只在选定维度上变化。

### 可选维度

| 维度 | 极值 A | 极值 B | 极值 C | 变化内容 |
|------|--------|--------|--------|---------|
| 整体氛围 | 温暖 | 冷峻 | 活泼 | 色温偏移、圆角大小、动效幅度 |
| 信息密度 | 宽松 | 紧凑 | — | 间距增减、内容裁剪/增加、留白比例 |
| 视觉权重 | 轻量 | 沉重 | — | 字重、阴影深度、边框粗细、色块面积 |
| 色彩饱和度 | 低饱和 | 高饱和 | — | 色彩 C 值（oklch chroma）调整 |
| 节奏速度 | 缓慢 | 急促 | — | 动效时长、信息逐步揭示 vs 一次性展示 |

### 变体生成规则

**1. 维度选择**
- 根据用户描述选择 2-3 个最有价值的维度
- 如果用户未指定维度，默认选择"整体氛围"和"信息密度"两个维度
- 每个维度选择极值对比（如温暖 vs 冷峻），中间值不生成

**2. 设计系统约束**
- 所有变体共享同一套 DesignSystemManifest 中的 Token 定义
- 变化只通过 Token 值的微调实现，不改变 Token 结构
- 变化范围：
  - 色温：oklch hue 偏移 ±20°
  - 色彩饱和度：oklch chroma ±0.05
  - 间距：倍数 ±0.25x
  - 字重：±100
  - 圆角：±4px
  - 阴影：上下一个层级

**3. 变体数量**
- 2 个维度 × 2 个极值 = 最多 4 个变体（通常生成 2-3 个）
- 每个变体生成完整的 HTML 文件

**4. 变体命名**
- 格式：`prototype-{方向名}-{维度}-{极值}.html`
- 示例：`prototype-warm-dense.html`、`prototype-cold-loose.html`

### 变体标注

每个变体必须附带说明：

```markdown
## 变体：{变体名}

### 变化维度与方向
- {维度1}：{极值} — {具体变化说明}
- {维度2}：{极值} — {具体变化说明}

### Token 变化

| Token | 基线值 | 变体值 | 变化说明 |
|-------|--------|--------|---------|
| --color-primary | oklch({L} {C} {H}) | oklch({L'} {C'} {H'}) | {色温偏移} |
| --space-base | {val}px | {val}'px | {间距调整} |
| --font-weight-display | {val} | {val}' | {字重调整} |

### 视觉效果描述
{一段话描述这个变体给人的整体感受}

### 适合场景
{这个变体适合什么类型的产品/用户/场景}
```

### 输出格式

```markdown
# VariationSpec

> 基线原型：{文件名}
> 设计系统版本：{DesignSystemManifest 版本}
> 变体维度：{维度1}、{维度2}

---

## 变体 1：{名称}

### 变化维度与方向
{如上格式}

### Token 变化
{如上表格}

### 视觉效果描述
{描述}

### 文件
`prototype-{name}.html`

---

## 变体 2：{名称}
{同上结构}

---

## 变体 3：{名称}
{同上结构}

---

## 变体对比

| 维度 | 变体 1 | 变体 2 | 变体 3 | 基线 |
|------|--------|--------|--------|------|
| {维度1} | {极值} | {极值} | — | {基线值} |
| {维度2} | — | {极值} | {极值} | {基线值} |
| 整体感受 | {关键词} | {关键词} | {关键词} | {关键词} |

## 用户选择

- [ ] 变体 1
- [ ] 变体 2
- [ ] 变体 3
- [ ] 混合：{说明从哪个变体取哪些特征}
```

### 混合模式

用户可以选择"混合"，从不同变体中各取部分特征：

```markdown
## 混合方案

- 整体氛围：取变体 1（温暖）的色温
- 信息密度：取变体 2（紧凑）的间距
- 视觉权重：保持基线

### 混合后 Token

| Token | 最终值 | 来源 |
|-------|--------|------|
| --color-primary | {值} | 变体1 |
| --space-base | {值} | 变体2 |
| --font-weight-display | {值} | 基线 |
```

## 注意事项

- 变体不是重新设计，是同一设计系统内的参数探索
- 所有变体必须通过 `qa-review`（仅 AI 味检测部分），确保变化没有引入 AI slop
- 变体生成后，用户选定或混合的结果更新为新的 PrototypeSpec 基线
- 如果用户选择的维度涉及色彩变化，混合后需重新检查对比度
- 变体数量控制在 2-3 个，避免选择过载
