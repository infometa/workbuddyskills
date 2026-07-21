---
name: make-tweakable
description: "Overlays a floating control panel on the prototype allowing real-time adjustment of color tokens, type scale, font weight, spacing multiplier, radius, and shadow parameters. Changes reflect instantly. On user confirmation, syncs back to DesignSystemManifest."
trigger:
  - 原型生成后，用户需要微调配色、间距、字号等参数时
  - 用户说"我想调一下颜色/间距/字号"时
  - make-prototype 完成后用户进入迭代阶段
---

# 调参面板（Make Tweakable）

## 触发时机

- 原型生成后（`make-prototype` 完成），用户需要微调配色、间距、字号等参数时
- 用户明确提出"想调整颜色/间距/字号/圆角/阴影"
- 迭代阶段（PatchLog 期间），用户想批量探索参数变化

## 前置条件

- **PrototypeSpec** — 已生成的高保真原型 HTML 文件
- **DesignSystemManifest** — 当前设计系统的 Token 定义

## 执行内容

在原型页面上叠加一个浮动调参面板，允许用户实时调整设计系统参数，调整结果实时反映在原型上。

### 调参面板功能

面板作为浮动控件注入原型 HTML，包含以下调节区域：

#### 1. 配色调节

| 可调参数 | 控件类型 | 说明 |
|---------|---------|------|
| 主色（Primary） | Color Picker + Hex 输入 | 调整 `--color-primary` |
| 辅色（Secondary） | Color Picker + Hex 输入 | 调整 `--color-secondary` |
| 强调色（Accent） | Color Picker + Hex 输入 | 调整 `--color-accent` |
| 背景色（Background） | Color Picker + Hex 输入 | 调整 `--color-bg` |
| 文本色（Text） | Color Picker + Hex 输入 | 调整 `--color-text` |

- 每个颜色同时显示 hex 和 oklch 值
- 调色时实时更新所有引用该 Token 的元素
- 提供"撤销"按钮回退到上一次确认的值

#### 2. 字号梯度调节

| 可调参数 | 控件类型 | 说明 |
|---------|---------|------|
| 基础字号（Body） | Slider 12-20px | 调整 `--font-size-body` |
| 梯度比例 | Select 1.125 / 1.200 / 1.250 / 1.333 / 1.500 | 选择比例后自动重算所有层级 |
| 字重（Display） | Slider 400-900 | 调整标题字重 |
| 字重（Body） | Slider 300-600 | 调整正文字重 |

- 梯度比例变化时，自动重算 H1-H4 和 Body/Caption 的字号
- 显示当前完整的字号梯度表

#### 3. 间距标尺调节

| 可调参数 | 控件类型 | 说明 |
|---------|---------|------|
| 基础单位 | Slider 4-8px | 切换 4px 或 8px 基础单位 |
| 倍数系统 | Select 线性 / 黄金比 / 自定义 | 选择倍数后重算间距标尺 |
| 全局缩放 | Slider 0.5x-2.0x | 等比缩放所有间距值 |

- 缩放时实时更新所有 `padding`、`margin`、`gap` 引用 Token 的元素
- 显示当前间距标尺的完整值表

#### 4. 圆角与阴影调节

| 可调参数 | 控件类型 | 说明 |
|---------|---------|------|
| 全局圆角 | Slider 0-24px | 统一调整所有组件圆角 |
| 按钮圆角 | Slider 0-24px | 独立调整按钮圆角 |
| 卡片圆角 | Slider 0-24px | 独立调整卡片圆角 |
| 阴影强度 | Select none / sm / md / lg | 切换全局阴影层级 |
| 阴影颜色透明度 | Slider 0-30% | 调整阴影透明度 |

### 技术实现

调参面板通过 JavaScript 注入原型 HTML，使用 CSS Custom Properties 实现实时更新：

```html
<!-- 调参面板 HTML 结构 -->
<div id="tweak-panel" style="position: fixed; top: 16px; right: 16px; z-index: 9999;">
  <div class="tweak-panel__header">
    <span>Design Tuner</span>
    <button onclick="document.getElementById('tweak-panel').classList.toggle('collapsed')">—</button>
  </div>
  <div class="tweak-panel__body">
    <!-- 配色调节区 -->
    <section class="tweak-section">
      <h4>Colors</h4>
      <label>Primary <input type="color" data-token="--color-primary" value="#{hex}"></label>
      <!-- ... -->
    </section>
    <!-- 字号调节区 -->
    <section class="tweak-section">
      <h4>Type Scale</h4>
      <label>Body Size <input type="range" min="12" max="20" data-token="--font-size-body" value="{val}"></label>
      <!-- ... -->
    </section>
    <!-- 间距调节区 -->
    <!-- 圆角阴影调节区 -->
  </div>
  <div class="tweak-panel__footer">
    <button onclick="exportTokens()">Confirm & Save</button>
    <button onclick="resetTokens()">Reset</button>
  </div>
</div>

<script>
// 实时更新逻辑
document.querySelectorAll('#tweak-panel [data-token]').forEach(input => {
  input.addEventListener('input', e => {
    const token = e.target.dataset.token;
    let value = e.target.value;
    if (e.target.type === 'color') value = '#' + value;
    if (e.target.type === 'range') value = value + 'px';
    document.documentElement.style.setProperty(token, value);
  });
});

// 梯度比例重算
function recalcTypeScale(ratio) { /* ... */ }

// 导出确认的 Token 值
function exportTokens() {
  const computed = getComputedStyle(document.documentElement);
  const tokens = {};
  // 收集所有 Token 当前值
  // 输出为 DesignSystemManifest 更新片段
}
</script>
```

### 面板样式

- 面板自身使用半透明背景 + 模糊效果（`backdrop-filter: blur(12px)`）
- 面板可折叠（点击标题栏收起/展开）
- 面板宽度固定 280px，内容超出可滚动
- 面板使用设计系统的字体和间距，但不影响原型本身的样式

### 用户确认后

1. 收集面板中所有 Token 的当前值
2. 生成 DesignSystemManifest 的更新片段（只列出变化的 Token）
3. 更新 DesignSystemManifest 文件
4. 更新 PatchLog，记录变更项
5. 移除调参面板（原型恢复为不可调状态）

### 输出格式

```markdown
# TweakLog

> 调参时间：{日期}
> 原型：{文件名}

## 变更项

| Token | 旧值 | 新值 | 说明 |
|-------|------|------|------|
| --color-primary | #{old} | #{new} | {说明} |
| --font-size-body | {old}px | {new}px | {说明} |
| --space-base | {old}px | {new}px | {说明} |

## DesignSystemManifest 更新

已同步更新以下章节：
- {章节1}
- {章节2}

## PatchLog 记录

已记录到 PatchLog。
```

## 注意事项

- 调参面板只调整 DesignSystemManifest 中已定义的 Token，不能新增 Token
- 颜色调整后应提示用户检查对比度（触发 `qa-review` 的可访问性审查对比度检测）
- 间距全局缩放可能导致布局溢出，调整时实时检查 `overflow`
- 面板移除后，原型应保留确认后的值（写入 CSS Custom Properties 的 inline 默认值）
- 如果用户取消（Reset），所有 Token 恢复为 DesignSystemManifest 的原始值
