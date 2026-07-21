---
name: design-system-extract
description: "从用户提供的截图/URL/代码库/品牌资料中提取设计 Token（配色、字体、间距、圆角、阴影、卡片样式），并细化所有可复用组件的完整规范（变体、状态、尺寸）。一个技能覆盖 Token 抽取与组件细化两个阶段。"
trigger:
  - 用户提供了参考截图
  - 用户提供了参考 URL
  - 用户提供了现有代码库
  - 用户提供了品牌资料（品牌指南、设计文件等）
  - DesignSystemManifest 完成后需要细化组件规范
---

# 设计系统抽取与组件细化（Design System Extract）

合并了 Token 抽取与组件细化两个阶段。从素材中提取设计 Token 整理成 DesignSystemManifest，再基于设计系统细化所有可复用组件的完整规范，产出 ComponentSpec。

## 触发时机

- 用户提供了参考素材（截图/URL/代码库/品牌资料）
- DesignSystemManifest 完成后，需要细化组件规范
- 用户要求整理组件库

## 第一部分：设计 Token 抽取

从提供的素材中系统性地提取设计 Token，整理成 DesignSystemManifest 格式。

### 1. 配色方案抽取

- **主色（Primary）**：页面中出现频率最高、面积最大的品牌色
- **辅色（Secondary）**：用于支撑主色的次要颜色
- **强调色（Accent）**：用于 CTA、高亮、关键交互的颜色
- **语义色（Semantic）**：success（绿）、warning（黄）、danger（红）、info（蓝）
- **中性色（Neutral）**：文本色、背景色、边框色、禁用色
- **标注方式**：同时用 oklch 和 hex 标注，oklch 便于程序化调色，hex 便于直接使用
- **缺失处理**：如果素材中无法区分辅色和强调色，标注为"缺失"并询问用户

### 2. 字体抽取

- **字体族**：识别标题字体和正文字体（截图识别注明置信度，代码库读取 CSS font-family）
- **字重**：提取使用的字重值（如 400、500、700）
- **字号梯度**：按比例排列（H1/H2/H3/H4/Body/Small/Caption），标注比例系统（1.250/1.333/1.5）
- **行高 / 字间距**：提取标题和正文使用的行高值
- **缺失处理**：无法确定字体时，提供 2-3 个风格匹配的候选并询问用户

### 3. 间距抽取

- **基础间距单位**：判断 4px 还是 8px（测量元素间距找最小公约数）
- **间距标尺**：xs(4px) / sm(8px) / md(16px) / lg(24px) / xl(32px) / 2xl(48px) / 3xl(64px)
- **缺失处理**：无法判断时默认 8px 并标注"推断值"

### 4. 圆角抽取

- **圆角标尺**：0px（直角）、4px（微）、8px（小）、12px（中）、16px（大）、9999px（胶囊）
- **按组件标注**：不同组件可能使用不同圆角

### 5. 阴影抽取

- **阴影层级**：sm（细微浮起）、md（中等浮起）、lg（强浮起）
- **标注方式**：`box-shadow` 完整 CSS 值

### 6. 卡片样式抽取

- **容器样式**：背景色、边框、圆角、内边距、阴影
- **内容布局**：标题区域、内容区域、操作区域的排布方式

### 输出：DesignSystemManifest

```markdown
# DesignSystemManifest

> 来源：{素材类型和描述}
> 抽取时间：{日期}
> 置信度：{高/中/低}

## 1. 配色方案
| 角色 | 色名 | OKLCH | HEX | 用途 |

## 2. 字体
| 层级 | 字体族 | 字重 | 字号 | 行高 | 用途 |

## 3. 间距标尺
| 标记 | 值 | 用途 |

## 4. 圆角
| 标记 | 值 | 适用组件 |

## 5. 阴影
| 层级 | CSS 值 | 用途 |

## 6. 卡片样式

## 7. 组件清单（初步）
| 组件 | 用途 | 备注 |

## 缺失项
- [ ] {缺失项1} — {询问内容}
```

### 缺失项处理规则

- 信息不全时用 checklist 标注缺失项，每个附一句具体询问内容
- 一次性集中询问，不反复追问
- 可从上下文合理推断的值标注"推断值"并继续，不阻塞流程

---

## 第二部分：组件细化

基于 DesignSystemManifest，列出所有识别到的可复用组件，每个组件标注完整规范。

### 每个组件的标注结构

**1. 组件名称**：语义化命名（PascalCase，如 `PrimaryButton`、`ProductCard`）

**2. 用途**：一句话说明 + 使用场景

**3. 变体（Variants）**
- 尺寸：sm / md / lg
- 风格：primary / secondary / ghost / outline
- 布局：horizontal / vertical
- 状态：editable / read-only

**4. 状态（States）**
- **default**：默认状态 — 背景/文字色/边框/阴影
- **hover**：悬停 — 变化项（颜色变化、阴影提升、微动效）
- **active**：按下/选中 — 变化项
- **focus**：键盘聚焦 — focus ring 样式（必须有可见焦点指示器）
- **disabled**：禁用 — 透明度、色彩变化
- **error**：错误状态（表单组件）— 错误色应用方式和提示位置

**5. 间距和尺寸规范**
- 外尺寸：宽高（固定值或 min/max 约束）
- 内边距：上/右/下/左，引用间距标尺
- 元素间距：组件内部 gap
- 最小触控区域：移动端 ≥ 44px

### 输出：ComponentSpec

```markdown
# ComponentSpec

> 来源：{DesignSystemManifest / 截图 / 原型代码}
> 组件总数：{N}
> 生成时间：{日期}

## 组件 1：{ComponentName}

### 用途
{一句话说明}

### 变体
| 变体名 | 差异说明 | 使用场景 |

### 状态
| 状态 | 背景 | 文字色 | 边框 | 阴影 | 其他 |

### 尺寸规范
- 宽度：{值或约束}
- 内边距：{上} {右} {下} {左}（引用间距标尺）
- 最小触控区域：{值}px

### Token 引用
- 主色 → `{color-token}`
- 字体 → `{font-token}`
- 圆角 → `{radius-token}`
- 阴影 → `{shadow-token}`

## 组件清单汇总
| # | 组件名 | 类别 | 变体数 | 状态数 |

## 缺失项
- [ ] {缺失项} — {说明}
```

### 组件类别参考

| 类别 | 常见组件 |
|------|---------|
| 按钮 | PrimaryButton、SecondaryButton、GhostButton、IconButton |
| 表单 | Input、Textarea、Select、Checkbox、Radio、Switch、Slider |
| 反馈 | Toast、Alert、Modal、Tooltip、Badge |
| 导航 | Tabs、Breadcrumbs、Pagination、NavBar、SideBar |
| 展示 | Card、Table、List、Avatar、Tag、Chip |
| 布局 | Container、Grid、Stack、Divider |
| 媒体 | Image、VideoPlayer、Carousel、Gallery |

### 提取规则

1. **从截图提取**：识别视觉上重复出现的 UI 模式，推断组件边界和状态
2. **从代码提取**：读取组件目录结构，解析 props 和 CSS 类名推断变体和状态
3. **从 DesignSystemManifest 提取**：根据设计系统中的组件规范章节细化
4. **不要遗漏状态**：即使素材中没展示所有状态，也必须推断并标注完整状态，标注"推断"来源
5. **所有色值引用 Token**：不直接写 hex 值，引用 DesignSystemManifest 中定义的 Token 名

## 注意事项

- 从截图提取时色彩识别可能有偏差，标注置信度
- 从代码库提取时优先读取 CSS 变量定义和 Tailwind config
- 从 URL 提取时分析 CSS 计算样式而非内联样式
- 抽取结果必须与素材一致，不要"美化"或"修正"原始设计
- 如果素材本身存在设计系统不一致的问题，如实标注
- 如果发现素材中存在未在 DesignSystemManifest 中定义的新 Token，回溯更新 DesignSystemManifest
- 组件规范中的所有数值必须引用设计系统的 Token，不临时发明
