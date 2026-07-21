# 四层 Design Token 体系标准

> 基于 152+ 设计系统分析 + SuperDev 119套配色方案 + 行业最佳实践蒸馏

## 一、Token 分层架构

```
┌─────────────────────────────────────────┐
│  A1 - Identity Token (身份层)            │
│  品牌 DNA：主色、品牌字体、logo规范        │
│  变更频率：极少（品牌升级时才变）           │
├─────────────────────────────────────────┤
│  A2 - Structure Token (结构层)           │
│  布局系统：间距、圆角、阴影层级             │
│  变更频率：低（产品重构时调整）             │
├─────────────────────────────────────────┤
│  B - Slot Token (插槽层)                 │
│  组件变体：按钮类型、输入框状态、卡片样式    │
│  变更频率：中（功能迭代时调整）             │
├─────────────────────────────────────────┤
│  C - Extension Token (扩展层)            │
│  行业/品牌定制：行业配色、特定组件          │
│  变更频率：高（按项目/客户定制）            │
└─────────────────────────────────────────┘
```

## 二、A1 - Identity Token

### 主色系
```css
:root {
  /* 主色 - 品牌DNA */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-200: #bfdbfe;
  --color-primary-300: #93c5fd;
  --color-primary-400: #60a5fa;
  --color-primary-500: #3b82f6;   /* 基准值 */
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-800: #1e40af;
  --color-primary-900: #1e3a8a;
}
```

### 品牌字体
```css
:root {
  --font-display: 'Inter', 'Noto Sans SC', sans-serif;
  --font-body: 'Inter', 'Noto Sans SC', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}
```

## 三、A2 - Structure Token

### 间距系统（8px网格）
```css
:root {
  --space-0: 0;
  --space-1: 4px;   /* 微间距：图标与文字 */
  --space-2: 8px;   /* 紧凑间距：同一组元素 */
  --space-3: 12px;  /* 标准间距：表单元素 */
  --space-4: 16px;  /* 舒适间距：卡片内边距 */
  --space-5: 20px;  /* 宽松间距：模块间距 */
  --space-6: 24px;  /* 区块间距 */
  --space-8: 32px;  /* 大区块间距 */
  --space-10: 40px; /* 页面级间距 */
  --space-12: 48px; /* 最大间距 */
  --space-16: 64px; /* 仅用于Hero区 */
}
```

### 圆角系统
```css
:root {
  --radius-none: 0;
  --radius-sm: 4px;    /* 小元素：Badge、Tag */
  --radius-md: 8px;    /* 标准元素：按钮、输入框 */
  --radius-lg: 12px;   /* 大元素：卡片 */
  --radius-xl: 16px;   /* 弹窗 */
  --radius-2xl: 24px;  /* 特殊场景 */
  --radius-full: 9999px; /* 头像、圆形按钮 */
}
```

### 阴影层级
```css
:root {
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
}
```

## 四、B - Slot Token

### 按钮变体
```css
:root {
  /* Primary */
  --btn-primary-bg: var(--color-primary-600);
  --btn-primary-text: #ffffff;
  --btn-primary-hover: var(--color-primary-700);
  --btn-primary-active: var(--color-primary-800);
  /* Secondary */
  --btn-secondary-bg: var(--color-primary-50);
  --btn-secondary-text: var(--color-primary-700);
  --btn-secondary-hover: var(--color-primary-100);
  /* Ghost */
  --btn-ghost-bg: transparent;
  --btn-ghost-text: var(--color-primary-600);
  --btn-ghost-hover: var(--color-primary-50);
  /* Danger */
  --btn-danger-bg: #dc2626;
  --btn-danger-text: #ffffff;
}
```

### 输入框状态
```css
:root {
  --input-bg: #ffffff;
  --input-border: #d1d5db;
  --input-focus-border: var(--color-primary-500);
  --input-focus-ring: var(--color-primary-200);
  --input-error-border: #ef4444;
  --input-error-ring: #fecaca;
  --input-disabled-bg: #f3f4f6;
  --input-disabled-text: #9ca3af;
}
```

## 五、C - Extension Token

### 行业配色扩展
```css
/* SaaS/B2B */
[data-industry="saas"] {
  --color-accent: #6366f1;  /* Indigo */
}
/* 电商 */
[data-industry="ecommerce"] {
  --color-accent: #f97316;  /* Orange */
}
/* 金融科技 */
[data-industry="fintech"] {
  --color-accent: #059669;  /* Emerald */
}
/* AI原生 */
[data-industry="ai"] {
  --color-accent: #3b82f6;  /* Blue */
}
/* 医疗 */
[data-industry="healthcare"] {
  --color-accent: #14b8a6;  /* Teal */
}
```

## 六、色彩精规

### 四层调色板配比
| 层级 | 占比 | 说明 |
|------|------|------|
| 中性色 | 70-90% | 背景、边框、分割线、正文 |
| 强调色 | 5-10% | 主色、CTA、选中态 |
| 语义色 | 0-5% | 成功/警告/错误/信息 |
| 效果色 | <1% | 聚焦光环、悬浮阴影 |

### 每屏强调色规则
- 每屏≤2处强调色使用
- 强调色仅用于：CTA按钮、选中Tab、关键数据高亮
- 标题用深色中性色，不用强调色

## 七、排版精规

### 字重三级体系
| 级别 | 字重 | 用途 |
|------|------|------|
| Regular | 400 | 正文、说明文字 |
| Medium | 510 | 按钮文字、表格表头、小标题 |
| Semibold | 590 | 大标题、强调文字 |

### 字距规则
- ALL CAPS 文字：letter-spacing ≥ 0.06em
- 标题：负字距 letter-spacing: -0.02em ~ -0.01em
- 正文：默认 letter-spacing: 0

### 字号体系
| 用途 | 字号 | 行高 |
|------|------|------|
| Hero标题 | 36-48px | 1.1 |
| 一级标题 | 28-32px | 1.2 |
| 二级标题 | 20-24px | 1.3 |
| 三级标题 | 16-18px | 1.4 |
| 正文 | 14-16px | 1.5-1.6 |
| 辅助文字 | 12-13px | 1.5 |
| 标签/徽章 | 11-12px | 1.0 |

## 八、动效精规

### 五级时长
| 场景 | 时长 | 缓动 |
|------|------|------|
| 即时反馈 | 50-100ms | ease-out |
| 确认操作 | 150ms | ease-out |
| 内容进入 | 200-300ms | ease-out |
| 跨屏过渡 | 300-500ms | ease-in-out |
| 复杂动画 | ≤500ms | 自定义 |

### 收敛值
- 所有动效时长以 **150ms** 为基准收敛值
- 超过500ms的动画需要特殊审批

### 禁止项
- 禁止弹跳缓动 `cubic-bezier(0.68, -0.55, 0.265, 1.55)`
- 禁止超过1秒的动画
- 禁止同时超过3个元素的动画

## 九、5态覆盖标准

每个交互组件必须覆盖以下5种状态：

| 状态 | 设计要求 | 示例 |
|------|----------|------|
| Loading | 骨架屏/进度条/思考指示 | AI生成中的打字机效果 |
| Empty | 引导文案+CTA+示例 | 空列表的"创建第一个"提示 |
| Error | 错误分类+重试+降级 | "网络异常，点击重试" |
| Populated | 内容展示+交互操作 | 数据列表的完整展示 |
| Edge | 边界处理+截断+安全阀 | 超长文本折叠、成本上限提醒 |

---

## 十、DESIGN.md 9 节标准模板（项目级设计契约）

> 每个项目必须产出一份 `DESIGN.md`，作为团队的设计契约源文件。设计师在 Phase 2 产出，前端在 Phase 3 据此实现。9 节结构覆盖从视觉主题到 Agent 实现指南的完整链路。

### 9 节结构（必含，不可删减）

```markdown
# {产品名} DESIGN.md

> 生成日期：{日期} | 设计师：颜好看 | 基于：PRD v{版本} + 架构文档 v{版本}
> 三轴刻度：Variance={1-10} / Motion={1-10} / Density={1-10}

## 1. Visual Theme & Atmosphere（视觉主题与氛围）
- 视觉主题关键词（3-5 个，如"冷静、精准、数据驱动"）
- 氛围描述（1-2 句话，如"深色为主，数据高亮，类似 Bloomberg Terminal 的专业感"）
- 对标品牌（2-3 个，如 Linear / Vercel / Stripe）

## 2. Color Palette & Roles（色彩与角色）
- A1-identity：--bg / --surface / --fg / --muted / --accent / --border
- A2-semantic：--success / --warn / --danger / --info
- B-slot 别名：--fg-2 / --surface-warm / --meta / --accent-hover
- C-extension：项目专属扩展色（如有）
- 每屏强调色使用 ≤ 2 处的说明
- 配色来源：`references/design-systems/color-palettes.md` 第 N 套

## 3. Typography（排版）
- 标题字体 + 正文字体（Google Fonts @import 语句）
- 字号阶梯：xs/sm/base/lg/xl/2xl/3xl/4xl/5xl/6xl（含 px + rem）
- 字重：3 级（400 正文 / 510 次标题 / 590 主标题）
- 行高：正文 1.5 / 标题 1.2-1.3
- 字距：ALL CAPS ≥ 0.06em / 标题负字距 -0.02em
- 配对来源：`references/design-systems/typography-pairings.md` 第 N 套

## 4. Components（组件规范）
- 按钮（primary/secondary/ghost/destructive × default/hover/active/disabled）
- 输入框（default/focus/error/disabled）
- 卡片（default/hover/selected）
- 导航（顶部/侧边/底部）
- 模态框 / Toast / Badge / Avatar
- 图标：统一 SVG 图标库（Spec 锁定一套，尺寸 16/20/24px）

## 5. Layout & Spacing（布局与间距）
- 间距基准：4px 网格（4/8/12/16/24/32/48/64/96）
- 圆角阶梯：sm(4) / md(8) / lg(12) / xl(16) / 2xl(24) / full
- 容器最大宽度：max-w-7xl(1280px) / max-w-4xl(896px) / max-w-2xl(672px)
- 响应式断点：sm(640) / md(768) / lg(1024) / xl(1280) / 2xl(1536)
- 网格系统：12 列 / gap 24px

## 6. Depth & Elevation（深度与阴影）
- 阴影阶梯：sm / md / lg / xl / 2xl（含 box-shadow 值）
- 层级 z-index：base(0) / dropdown(1000) / sticky(1100) / modal(1200) / toast(1300)
- 毛玻璃/模糊：仅用于有功能目的的半透明（不作装饰）

## 7. Do's & Don'ts（设计守则）
- ✅ 应该做的 5-8 条
- ❌ 不应该做的 5-8 条（含行业反模式）
- 行业反模式来源：`references/design-systems/industry-design-systems.md` 对应行业

## 8. Responsive & Accessibility（响应式与无障碍）
- 响应式策略：mobile-first / 断点行为说明
- 无障碍：对比度 4.5:1 / 键盘导航 / focus 可见 / prefers-reduced-motion
- 触摸目标：最小 44×44px
- 5 态覆盖：Loading / Empty / Error / Populated / Edge

## 9. Agent Implementation Guide（实现指南）
- Tailwind config（完整 JSON，含 colors/fontFamily/spacing/borderRadius/shadow）
- CSS 变量定义（:root 代码块）
- 框架特定实现提示（按架构师锁定栈）
- 已知坑提醒（从项目 .workbuddy/memory/pitfalls.jsonl 拉取）
```

---

## 十一、Master + Overrides 持久化模式

> 设计系统不是一次性产出，而是项目演进过程中的持久化源。Master 是全局源，页面级 Override 只写差异。

### 目录结构

```
项目/
├── DESIGN.md                        # 9 节完整文档（人类可读，团队对齐用）
├── design-system/
│   ├── MASTER.md                    # 全局设计源（所有页面共享，机器可读优先）
│   ├── design-tokens.json           # Token 定义（primitive→semantic→component）
│   ├── design-tokens.css            # CSS 变量（前端 import）
│   └── pages/
│       ├── home.md                  # 首页覆盖（仅写与 Master 不同的字段）
│       ├── dashboard.md              # 仪表板覆盖
│       └── settings.md              # 设置页覆盖
```

### 检索规则（设计某页面时执行）

1. Read `design-system/MASTER.md` 获取全局设计源
2. 检查 `design-system/pages/<page>.md` 是否存在
   - 存在 → 该文件的字段覆盖 Master 对应字段，其余用 Master
   - 不存在 → 完全用 Master
3. 输出该页面的最终设计参数（Master + Override 合并结果）

### 写入规则（反上下文坍缩）

- **MASTER.md 已存在时，禁止整篇重写**——只追加/修正具体条目
- 一条「页面 X 的 CTA 按钮用 accent 而非 primary，因为转化测试显示 accent 高 23%」远胜于「要注意按钮颜色」
- 页面级 Override 只写差异字段，不复制 Master 内容
- 变更须在 MASTER.md 末尾的变更记录表追加一行（日期 + 变更 + 原因 + 影响范围）

### Token 三层结构（与四层 Token 架构的映射）

```
Primitive（原始值）    ← A1-identity + A1-structure
       ↓
Semantic（语义别名）   ← A2-semantic
       ↓
Component（组件专用）  ← B-slot + C-extension
```

**CSS 变量示例**：
```css
/* Primitive (A1) */
--color-blue-600: #2563EB;

/* Semantic (A2) */
--color-primary: var(--color-blue-600);
--color-success: #059669;

/* Component (B/C) */
--button-bg: var(--color-primary);
--button-bg-hover: var(--color-primary-dark);
```
