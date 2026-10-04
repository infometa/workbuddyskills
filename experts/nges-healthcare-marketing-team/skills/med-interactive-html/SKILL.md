---
name: med-interactive-html
description: 医学内容高级互动HTML页面生成。将医学文本草稿（论文摘要、临床指南、教学讲义、药品推广材料、专家访谈等）转化为CSS变量+JS交互的精美互动学习页面，内置16种互动组件与6套预设主题，也可生成知识闪卡（翻转卡/填空卡/多选判断卡）。当用户提到"医学互动页面""互动学习页面""知识闪卡""医学内容二创""生成互动HTML""interactive medical page"等需求时使用本 skill。
agent_created: true
---

# med-interactive-html — 医学内容高级互动 HTML 生成

## 适用场景

将医学文本草稿（论文摘要、临床指南、教学讲义、药品推广材料、专家访谈等）转化为高质量、视觉精美的**互动 HTML 学习页面**。

适用输出：本地预览、静态托管部署、邮件附件分享、内部学习平台嵌入。

> 如需发布到文章系统或微信公众号等不支持 JS 的平台，请在生成后转为**静态适配版**：全内联 `style="..."`（不用 `<style>` 标签与 CSS 变量、色值写死）、移除 `<script>`，并将 Tab、闪卡等动态组件改为平铺展示。

## 工作流程

### Step 1: 内容解析

从用户提供的医学文本中提取：
- **标题与副标题**
- **关键标签**（疾病名、药物名、治疗策略等）
- **统计数据**（适合做数据看板的3-5 个关键数字/指标）
- **专家信息**（如有）
- **核心知识点**（分2-4 个维度/主题）
- **时间线/流程**（如有治疗演进、研究里程碑）
- **对比数据**（如有药物对比、方案对比）
- **参考文献**

### Step 2: 确认配色方案

默认使用「学术蓝」。6 种预设主题：

| 主题 | --primary | --primary-light | --primary-dark | --primary-bg | 适用场景 |
|------|-----------|-----------------|----------------|--------------|---------|
| 学术蓝 | #185FA5 | #2E7BC9 | #0D4A82 | #E8F2FC | 正式学术/CME |
| 清新绿 | #0F6E56 | #10B981 | #064E3B | #ECFDF5 | 健康科普/患教|
| 活力橙 | #D85A30 | #F97316 | #9A3412 | #FFF7ED | 自媒体/公众号 |
| 暗夜模式 | #85B7EB | #60A5FA | #3B82F6 | #1E293B | 护眼阅读 |
| 医药红 | #993556 | #BE4B6E | #6B2140 | #FDF2F8 | 药企品牌材料 |
| 科技蓝 | #378ADD | #60A5FA | #1D4ED8 | #EFF6FF | 前沿技术/AI医疗 |

### Step 3: 选择组件组合

根据内容特点，从下方组件库中选择 **5-10 个组件** 组合成页面。

### Step 4: 生成完整 HTML

- 使用 CSS 变量 + class 架构
- JS 实现交互（Tab 切换、折叠展开、翻转、悬浮提示等）
- 响应式设计（移动端适配）
- 末尾添加免责声明和参考文献

## 组件库（共 16 种）

详细 HTML/CSS/JS 模板见 `references/components.html`

### 基础布局组件

| # | 组件名 | 类名 | 说明 |
|---|--------|------|------|
| 1 | **Header** | `.header` | 主题色渐变标题区 + 标签云 |
| 2 | **Stats Grid** | `.stats-grid` | 关键数据看板（3-5 个统计卡片） |
| 3 | **Section** | `.section` | 带标题的内容区块 |
| 4 | **Footer** | `.footer` | 免责声明 + 参考文献 + 来源 |

### 专家与内容组件

| # | 组件名 | 类名 | 说明 |
|---|--------|------|------|
| 5 | **Expert Card** | `.expert-card` | 专家信息卡（头像+职称+可展开学术任职） |
| 6 | **Tabs** | `.tabs` | 多标签切换面板（2-5 个 tab） |
| 7 | **Timeline** | `.timeline` | 纵向时间轴/里程碑 |
| 8 | **Flashcard** | `.flashcard-grid` | 3D 翻转知识卡（正面问题 → 背面答案） |

### 高级互动组件

| # | 组件名 | 类名 | 说明 |
|---|--------|------|------|
| 9 | **Accordion** | `.accordion` | 手风琴折叠面板（点击标题展开/收起详情） |
| 10 | **Comparison Bar** | `.comparison-bar` | 数据对比条形图（两组数据并排比较） |
| 11 | **Tooltip Card** | `.tooltip-card` | 悬浮气泡提示卡（鼠标悬停显示术语解释） |
| 12 | **Step Navigator** | `.step-nav` | 步骤导航器（带编号的步骤流程，可点击跳转） |
| 13 | **Split Compare** | `.split-compare` | 左右分栏对比（A vs B 方案并排展示） |
| 14 | **Floating TOC** | `.floating-toc` | 浮动目录锚点导航（右侧固定，跟随滚动高亮） |
| 15 | **Counter Animation** | `.counter-anim` | 数字滚动动画（进入视口时数字从 0 递增） |
| 16 | **Callout Variants** | `.callout-*` | 多类型提示框（info/warning/success/expert-quote） |

### 辅助修饰组件

| 类型 | 说明 |
|------|------|
| **Highlight Box** | 蓝色重点摘要框（✓ 列表） |
| **Callout** | 黄色警示/提示条|
| **Expert Quote** | 专家引用块（带引号装饰） |
| **Divider** | 装饰性分隔线 |

## 组件选择建议

| 内容类型 | 推荐组件组合 |
|----------|-------------|
| 专家访谈 | Header + Stats + Expert Card + Tabs + Accordion + Flashcard + Footer |
| 临床指南解读 | Header + Stats + Step Navigator + Accordion + Comparison Bar + Floating TOC + Footer |
| 药物对比 | Header + Stats + Split Compare + Comparison Bar + Tabs + Tooltip Card + Footer |
| 研究里程碑 | Header + Stats + Timeline + Counter Animation + Tabs + Flashcard + Footer |
| 治疗流程 | Header + Step Navigator + Accordion + Callout Variants + Timeline + Footer |

## 医学内容安全规范

- 不添加原文未提供的医学信息
- 药物名称、剂量等关键数据原样保留
- 自动标注内容来源
- 生成免责声明："本页面内容仅供医学专业人士学习参考，不作为临床诊疗依据"
- 保留参考文献引用标记

## 输出规范

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{文章标题} | 互动学习</title>
    <style>
        :root { /* 主题色变量 */ }
        /* 组件样式 */
    </style>
</head>
<body>
    <div class="container">
        <!-- 组件 HTML -->
    </div>
    <script>
        // 交互逻辑
    </script>
</body>
</html>
```

## 注意事项

- 每个页面控制在 5-10 个组件，不要堆砌过多
- 根据内容自然流向安排组件顺序
- 移动端响应式 breakpoint: 640px
- 动画保持克制，以提升可读性为目的
- 暗夜模式需要将 `--bg`/`--card-bg`/`--text` 等颜色反转
