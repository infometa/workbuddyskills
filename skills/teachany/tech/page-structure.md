# TeachAny Page Structure（精简版）

## 标准页面顺序

1. `<head>` meta（现行标准）：`teachany-node`（node_id）、`teachany-id`（course-id）、`teachany-subject`、`teachany-grade`、`teachany-version`。旧版 `course-*` 命名已废弃，新课件不要使用。
2. 顶部品牌栏：TeachAny + Gallery 链接 + course version + skill version。
3. Hero 区：标题、对象、学习目标。
4. Hero 知识结构图：独立 `<figure>`，不是背景图。
5. 问题锚点：2–3 个预设场景 + 自定义问题。
6. 前测/诊断。
7. 2–5 个主体学习 section：每段包含解释、互动、反馈。
8. 总结迁移题。
9. AI 学伴入口卡片。
10. 知识图谱 section。
11. 标准脚本：AI tutor、TTS narrator、section hints、knowledge graph。

## Section 模板

```html
<section class="ta-section" id="module-1" data-tsh="想一想：这里的关键变化是什么？">
  <h2>模块标题</h2>
  <p data-tts>一段清晰解释。</p>
  <div class="interactive-card">真实互动组件</div>
  <div class="check-card">即时练习与反馈</div>
</section>
```

## 必要交互要求

- 操作前有任务；操作后有反馈。
- 图像、公式、文字至少两种表征联动。
- 学生能撤回、重试或看到状态变化。
- 不依赖 hover 才能完成核心任务。

## 移动端要求

- viewport 使用 `viewport-fit=cover`。
- 主要按钮和拖拽目标 ≥44px。
- 网格在窄屏变单列。
- 音频条、AI FAB、底部导航互不遮挡。

## 标准模块挂载

使用模板默认配置。不要复制粘贴旧课件里的内联模块实现。
