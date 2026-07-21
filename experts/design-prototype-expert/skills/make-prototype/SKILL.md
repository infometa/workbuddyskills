---
name: make-prototype
description: "Generates high-fidelity HTML prototypes strictly following the DesignSystemManifest. Uses defined colors, fonts, spacing, and components. Includes all interaction states, responsive layout, semantic HTML, prefers-reduced-motion support, and real content. Auto-triggers AI-slop detection after generation."
trigger:
  - 用户选定了设计方向，需要生成高保真原型时
  - DesignSystemManifest 已完成，且用户已选定美学方向（ConceptRoutes 或 AestheticStarterKit 选定结果）
---

# 原型生成（Make Prototype）

## 触发时机

- 用户选定了设计方向（ConceptRoutes 中某个方向，或选定了 AestheticStarterKit 中的某个模板），需要生成高保真原型时
- DesignSystemManifest 已完成

## 前置条件

在执行此技能之前，以下文档必须已存在且被引用：
1. **DesignBrief** — 确定产品定位、目标用户、页面唯一目标
2. **DesignSystemManifest** — 确定配色、字体、间距、组件规范、交互状态
3. **方向已选定** — ConceptRoutes（路径 B）或 AestheticStarterKit 选定结果（路径 A），二者满足其一即可

## 执行内容

严格按 DesignSystemManifest 的规范生成 HTML 原型。

### 原型必须满足

**1. 设计系统一致性**
- 使用设计系统中定义的配色变量（CSS custom properties）
- 使用设计系统中定义的字体配对
- 使用设计系统中定义的间距规则（基础间距单位的倍数）
- 不临时发明新的颜色、字体或间距值
- 所有组件遵循设计系统中的组件规范

**2. 交互状态完整性**
- 所有可交互元素必须包含完整状态：hover、active、focus、disabled
- 状态变化必须通过 CSS 实现，不依赖 JavaScript（除非是复杂交互）
- focus 状态必须有明显的视觉反馈（focus-visible）

**3. 响应式适配**
- 桌面端（≥1024px）：完整布局
- 移动端（<768px）：单列布局，导航折叠，触控友好的点击区域（≥44px）
- 使用 CSS Grid / Flexbox 实现响应式，不使用固定像素宽度

**4. 语义化 HTML**
- 使用正确的 HTML5 语义标签（header、nav、main、section、article、footer）
- 使用 ARIA 属性增强可访问性
- 表单元素必须有 label
- 图片必须有 alt 文本

**5. 动效与无障碍**
- 尊重 `prefers-reduced-motion: reduce` 媒体查询
- 动效用于增强而非干扰，不自动播放大段动画
- 色彩对比度满足 WCAG AA 标准（正文 ≥4.5:1，大文本 ≥3:1）

**6. 内容真实性**
- 使用真实内容，不用 lorem ipsum
- 使用与产品定位和目标用户匹配的真实文案
- 图片使用有意义的占位（如 picsum.photos 带语义化 seed），不用无意义 stock placeholder

### 输出格式

生成一个完整的 HTML 文件（内联 CSS），文件命名格式：`prototype-{方向名}.html`

文件结构：
```html
<!DOCTYPE html>
<html lang="{语言}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{页面标题}</title>
  <style>
    /* === Design System Tokens === */
    :root {
      --color-primary: #{hex};
      --color-secondary: #{hex};
      --color-accent: #{hex};
      --color-neutral: #{hex};
      --color-bg: #{hex};
      --font-display: '{字体名}', fallback;
      --font-body: '{字体名}', fallback;
      --space-base: {数值}px;
    }

    /* === Reset === */
    /* ... */

    /* === Components === */
    /* ... */

    /* === Responsive === */
    @media (max-width: 768px) { /* ... */ }

    /* === Reduced Motion === */
    @media (prefers-reduced-motion: reduce) { /* ... */ }
  </style>
</head>
<body>
  <!-- 语义化结构 -->
</body>
</html>
```

### 生成后自动执行

原型生成后**自动触发 AI 味检测**，检查以下内容：
1. 是否命中强禁止清单中的任何默认审美
2. 是否使用了设计系统之外的临时值
3. 是否有 lorem ipsum 或无意义占位文本
4. 是否有未覆盖交互状态的元素
5. 色彩对比度是否达标

检测结果写入 QAReport。

## 注意事项

- 没有设计系统就不要生成高保真页面——这是铁律。
- 用户提出修改时只做局部 Patch，不整页重写。
- 用与用户相同的语言编写页面内容。
- 字体从 Google Fonts 或 CDN 引入，确保可加载。
