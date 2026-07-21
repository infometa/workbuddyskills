---
name: make-a-deck
description: "Generates an HTML slide deck following the design system. One core message per slide, max 6 lines, clear visual hierarchy, keyboard navigation, 0.2-0.3s transitions with prefers-reduced-motion support."
trigger:
  - 用户需要生成演示文稿时
  - 用户说"做个PPT/幻灯片/演示"时
  - 用户需要向他人展示设计方案时
---

# 幻灯片（Make a Deck）

## 触发时机

- 用户需要生成演示文稿
- 用户要求"做个 PPT / 幻灯片 / 演示 / deck"
- 用户需要向团队或客户展示设计方案

## 前置条件

- **DesignSystemManifest** — 幻灯片必须使用设计系统的配色和字体
- **DesignBrief** 或用户提供的内容大纲 — 确定幻灯片的内容结构

## 执行内容

按设计系统生成 HTML 幻灯片，每张幻灯片遵循严格的视觉和信息规范。

### 幻灯片规范

**1. 单页内容限制**
- 每张幻灯片一个核心信息点
- 不超过 6 行文字（不含标题）
- 标题 ≤ 12 个字（中文）/ ≤ 8 个单词（英文）
- 正文每行 ≤ 20 个字（中文）/ ≤ 12 个单词（英文）

**2. 视觉层级**
- 标题：设计系统中最大的字号层级（Display 或 H1）
- 正文：设计系统的 Body 字号
- 辅助信息：设计系统的 Caption 字号
- 每页必须有明确的视觉焦点（最大的元素 = 最重要的信息）

**3. 配色与字体**
- 背景使用设计系统的背景色或主色
- 文字使用设计系统的文本色
- 强调色仅用于关键数据或 CTA
- 字体使用设计系统的 display + body 字体配对

**4. 布局类型**

支持以下幻灯片布局类型，根据内容选择：

| 布局类型 | 适用场景 | 结构 |
|---------|---------|------|
| Title | 封面页 | 居中大标题 + 副标题 + 日期/作者 |
| Statement | 核心观点 | 一句话居中，大字号，留白为主 |
| Bullet | 要点列举 | 标题 + 3-5 个要点（每点一行） |
| Split | 对比/图文 | 左右分栏：文字 vs 图片/数据 |
| Data | 数据展示 | 标题 + 大数字 + 说明 |
| Quote | 引用 | 大引号 + 引用文字 + 来源 |
| Section | 分隔页 | 居中章节标题，背景色区分 |
| Closing | 结尾页 | 核心总结 + 联系方式/CTA |

**5. 键盘导航**
- `→` / `Space` / `PageDown`：下一页
- `←` / `PageUp`：上一页
- `Home`：跳到第一页
- `End`：跳到最后一页
- `F`：全屏
- `Esc`：退出全屏
- 页码指示器：底部 `当前页 / 总页数`

**6. 过渡动画**
- 翻页过渡时长：0.2s - 0.3s
- 过渡类型：fade（淡入淡出）或 slide（水平滑动）
- 必须尊重 `prefers-reduced-motion: reduce`

```css
@media (prefers-reduced-motion: reduce) {
  .slide {
    transition: none;
  }
}
```

**7. 响应式**
- 16:9 宽高比（默认 1280×720）
- 自适应缩放：根据视口大小等比缩放
- 投影模式：高对比度，大字号

### 技术实现

```html
<!DOCTYPE html>
<html lang="{语言}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{演示标题}</title>
  <style>
    /* === Design System Tokens === */
    :root { /* ... DesignSystemManifest tokens ... */ }

    /* === Slide Container === */
    .deck {
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      position: relative;
    }

    .slide {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      opacity: 0;
      transform: translateX(100%);
      transition: opacity 0.3s ease, transform 0.3s ease;
      padding: var(--space-3xl);
    }

    .slide.active {
      opacity: 1;
      transform: translateX(0);
    }

    .slide.prev {
      transform: translateX(-100%);
    }

    /* === Layout Types === */
    .slide--title { /* ... */ }
    .slide--statement { /* ... */ }
    .slide--bullet { /* ... */ }
    .slide--split { /* ... */ }
    .slide--data { /* ... */ }
    .slide--quote { /* ... */ }
    .slide--section { /* ... */ }
    .slide--closing { /* ... */ }

    /* === Navigation === */
    .nav {
      position: fixed;
      bottom: 24px;
      right: 24px;
      font-family: var(--font-body);
      font-size: var(--font-size-caption);
      color: var(--color-text-secondary);
    }

    @media (prefers-reduced-motion: reduce) {
      .slide { transition: none; }
    }
  </style>
</head>
<body>
  <div class="deck">
    <section class="slide slide--title active" data-layout="title">
      <h1>{标题}</h1>
      <p>{副标题}</p>
      <span>{日期/作者}</span>
    </section>

    <section class="slide slide--statement" data-layout="statement">
      <p class="statement-text">{核心观点}</p>
    </section>

    <!-- ... more slides ... -->

    <section class="slide slide--closing" data-layout="closing">
      <h2>{总结}</h2>
      <p>{联系方式/CTA}</p>
    </section>
  </div>

  <div class="nav"><span id="current">1</span> / <span id="total">{N}</span></div>

  <script>
    const slides = document.querySelectorAll('.slide');
    let current = 0;

    function goTo(index) {
      if (index < 0 || index >= slides.length) return;
      slides[current].classList.remove('active');
      slides[current].classList.add(index > current ? 'prev' : '');
      current = index;
      slides[current].classList.remove('prev');
      slides[current].classList.add('active');
      document.getElementById('current').textContent = current + 1;
    }

    document.addEventListener('keydown', (e) => {
      switch(e.key) {
        case 'ArrowRight':
        case ' ':
        case 'PageDown':
          e.preventDefault(); goTo(current + 1); break;
        case 'ArrowLeft':
        case 'PageUp':
          e.preventDefault(); goTo(current - 1); break;
        case 'Home':
          e.preventDefault(); goTo(0); break;
        case 'End':
          e.preventDefault(); goTo(slides.length - 1); break;
        case 'f':
        case 'F':
          if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
          } else {
            document.exitFullscreen();
          }
          break;
        case 'Escape':
          if (document.fullscreenElement) document.exitFullscreen();
          break;
      }
    });
  </script>
</body>
</html>
```

### 输出格式

生成一个完整的 HTML 文件：`deck-{主题}.html`

附赠幻灯片大纲文档：

```markdown
# DeckOutline

> 主题：{主题}
> 页数：{N}
> 设计系统版本：{DesignSystemManifest 版本}

| 页码 | 布局类型 | 核心信息点 | 备注 |
|------|---------|-----------|------|
| 1 | Title | {标题} | 封面 |
| 2 | Statement | {核心观点} | — |
| 3 | Bullet | {要点列表} | — |
| ... | ... | ... | ... |
| N | Closing | {总结} | 结尾 |
```

## 注意事项

- 幻灯片内容必须使用真实内容，不用 lorem ipsum
- 每页文字不超过 6 行是铁律——超了就拆页或精简
- 幻灯片不是文档，不要在一张幻灯片上放完整段落
- 生成后自动触发 `qa-review`（仅 AI 味检测部分），确保幻灯片设计没有 AI slop
- 如果用户未提供大纲，先根据 DesignBrief 生成大纲让用户确认，再生成幻灯片
- 幻灯片的 `transition` 时长必须在 0.2s-0.3s 之间
