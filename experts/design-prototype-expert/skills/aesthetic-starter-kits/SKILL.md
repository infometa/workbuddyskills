---
name: aesthetic-starter-kits
description: "10 prebuilt aesthetic templates, each a complete design system. When the user has no brand assets and needs a fast start, show these kits first — selecting one skips ConceptRoutes and generates DesignSystemManifest directly. Falls back to frontend-aesthetic-direction only if none fit."
trigger:
  - 用户没有提供品牌资料，且需要快速启动设计时
  - 优先于 frontend-aesthetic-direction 触发
  - 用户说"有没有现成的风格/模板/套件可选"时
---

# 美学启动套件（Aesthetic Starter Kits）

## 触发时机

- **优先触发**：用户没有提供品牌资料，且需要快速启动设计时，本技能优先于 `frontend-aesthetic-direction` 触发
- 用户主动询问"有没有现成的风格/模板/套件可选"
- 用户想快速看到结果，不想走完整的 ConceptRoutes 流程

## 执行内容

提供 10 个预制美学模板，每个都是完整的设计系统。用户选定后直接生成 DesignSystemManifest，跳过 ConceptRoutes 阶段。

---

## 10 个预制美学模板

### 模板 1：编辑极简风（Editorial Minimal）

**主张**：克制的深色底，纤细的蓝紫强调线，信息密度高但不拥挤。参考 Linear 和 Vercel 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#0f0f14` |
| 文字 | `#ffffff` |
| 强调 | `#5e6ad2` |
| 次要 | `#7c7c8a` |
| Display 字体 | Inter Tight 600 |
| Body 字体 | Inter 400 |
| 间距 | 8px 倍数，行高 1.65，section 间距 64px |
| 圆角 | 2px，卡片用 1px 边框代替阴影 |
| 签名元素 | 细线分隔栏 + 小字号大写标签 |

---

### 模板 2：电影感深空（Cinematic Deep Space）

**主张**：纯黑底，大面积留白，品红与青色对撞。参考 Runway 和 Active Theory 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#000000` |
| 文字 | `#ffffff` |
| 强调A | `#e219eb` |
| 强调B | `#00e5ff` |
| Display 字体 | Sora 700 |
| Body 字体 | Sora 400 |
| 间距 | 大留白，section 间距 80px，段落间距 24px |
| 圆角 | 0px，硬边 |
| 签名元素 | 渐变光晕背景 + 全屏视觉块 |

---

### 模板 3：暖纸手作（Warm Paper Handcraft）

**主张**：奶油底，手写感衬线，温润但不甜腻。参考 Aesop 和 Stripe Press 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#faf8f2` |
| 文字 | `#2d2a26` |
| 强调 | `#9d5f4d` |
| 辅助 | `#537d96` |
| Display 字体 | Playfair Display 500 |
| Body 字体 | Source Serif 400 |
| 间距 | 6px 倍数，行高 1.7，段落间距充裕 |
| 圆角 | 4px，柔和但不圆滑 |
| 签名元素 | 纸质纹理感 + 赤陶色手绘标注 |

---

### 模板 4：数据密集终端（Data-Dense Terminal）

**主张**：深色仪表盘，高信息密度，荧光色标注关键数据。参考 Bloomberg Terminal 和 ClickHouse 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#181818` |
| 文字 | `#e0e0e0` |
| 强调A | `#faff69` |
| 强调B | `#00e5a0` |
| 语义 | `#ff6b9d` |
| Display 字体 | Space Grotesk 600 |
| Body 字体 | Space Grotesk 400 |
| 数字字体 | JetBrains Mono |
| 间距 | 4px 倍数，紧凑但有序，行高 1.5 |
| 圆角 | 2px |
| 签名元素 | 等宽数字 + 微型图表 + 状态点 |

---

### 模板 5：粗野撞色（Brutalist Clash）

**主张**：大胆撞色，零圆角，粗边框，信息爆炸但有秩序。参考 The Verge 和 Balenciaga 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#ffffff` |
| 文字 | `#000000` |
| 强调 | `#ff6600` |
| 辅助 | `#00ff00` |
| Display 字体 | Unbounded 700 |
| Body 字体 | Space Grotesk 400 |
| 间距 | 硬边距，2px 实线分隔，无内边距留白 |
| 圆角 | 0px |
| 签名元素 | 粗边框卡片 + 大面积纯色块 + 高对比文字 |

---

### 模板 6：液态玻璃（Liquid Glass）

**主张**：半透明叠层，柔和模糊，彩色光晕透过玻璃面。参考 Apple Fluid and Glows 和 Arc Browser 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#f5f5f7` |
| 文字 | `#1d1d1f` |
| 强调 | `#007aff` |
| 辅助 | `#bf5af2` |
| 玻璃层 | `rgba(255,255,255,0.6)` |
| Display 字体 | SF Pro Display 600 |
| Body 字体 | SF Pro Text 400 |
| 间距 | 8px 倍数，圆角 20px，卡片间留白 16px |
| 圆角 | 20px，卡片和按钮大圆角 |
| 签名元素 | backdrop-filter 毛玻璃 + 彩色光晕投影 + 浮动层次 |

---

### 模板 7：杂志编辑（Magazine Editorial）

**主张**：多栏排版，大标题压版，衬线与无衬线混排，印刷感。参考 Monocle 和 NYT Magazine 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#fdfdfb` |
| 文字 | `#1a1a1a` |
| 强调 | `#c8102e` |
| 辅助 | `#6b6b6b` |
| Display 字体 | Playfair Display 900 italic |
| Body 字体 | Source Sans 3 400 |
| 标注字体 | IBM Plex Mono 400 |
| 间距 | 12px 基线网格，多栏布局，栏间距 24px |
| 圆角 | 0px |
| 签名元素 | 大号斜体标题压图片 + 多栏正文 + 细规则线分隔 |

---

### 模板 8：游戏化活泼（Playful Gamified）

**主张**：圆润形状，饱和撞色，微动效，手绘涂鸦元素。参考 Headspace 和 Mailchimp Freddie 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#fff8e7` |
| 文字 | `#2d1b69` |
| 强调 | `#ff6b9d` |
| 辅助 | `#4ecdc4` |
| 点缀 | `#ffd93d` |
| Display 字体 | Fredoka 600 |
| Body 字体 | Nunito 400 |
| 间距 | 8px 倍数，元素间大间距 32px，内部紧凑 |
| 圆角 | 16px，按钮和卡片全圆角 |
| 签名元素 | 手绘涂鸦装饰 + 圆形头像 + 弹性微动效（0.3秒 ease-out） |

---

### 模板 9：日式禅意（Japanese Zen）

**主张**：大面积留白，灰阶为主，一点朱红，物哀感。参考无印良品和 Kenya Hara 的设计哲学。

| 项目 | 值 |
|------|-----|
| 背景 | `#f5f3ef` |
| 文字 | `#2a2a28` |
| 强调 | `#b34a3a` |
| 辅助 | `#8a8a85` |
| Display 字体 | Noto Serif JP 500 |
| Body 字体 | Noto Sans JP 300 |
| 间距 | 宽留白，section 间距 96px，行高 1.8 |
| 圆角 | 0px |
| 签名元素 | 大面积负空间 + 一点朱红印章 + 极细发丝线 |

---

### 模板 10：复古未来（Retrofuture Y2K）

**主张**：Y2K 美学，霓虹紫绿，像素感，CRT 扫描线，早期互联网怀旧。参考 Y2K Retrofuturism 和早期 PlayStation UI 的视觉语言。

| 项目 | 值 |
|------|-----|
| 背景 | `#0d0221` |
| 文字 | `#00ffff` |
| 强调 | `#ff00ff` |
| 辅助 | `#39ff14` |
| 暗 | `#4a0e7a` |
| Display 字体 | VT323 400 |
| Body 字体 | Space Mono 400 |
| 间距 | 4px 像素网格，紧凑居中布局 |
| 圆角 | 0px，硬边像素感 |
| 签名元素 | CRT 扫描线滤镜 + 像素化图标 + 霓虹文字发光 |

---

## 使用规则

1. **优先展示**：用户没有明确美学偏好时，展示这 10 个模板让用户选
2. **选定即跳过**：用户选定后，直接基于模板生成 DesignSystemManifest，跳过 ConceptRoutes 阶段
3. **支持微调**：用户可以基于模板微调（换配色、换字体、调间距），微调后更新 DesignSystemManifest
4. **降级机制**：如果 10 个模板都不满足，再降级到 `frontend-aesthetic-direction` 从零定制
5. **追溯标记**：每次使用模板时，在 DesignBrief 中注明"基于 XX 模板"，方便追溯

---

## 输出格式

### 展示阶段

向用户展示 10 个模板的摘要，每个模板包含：模板编号、名称、一句话主张、配色预览、适用场景。

```markdown
# Aesthetic Starter Kits

以下 10 个预制美学模板，每个都是完整的设计系统。选定后直接进入设计系统生成，跳过方向探索阶段。

| # | 模板名 | 主张 | 适用场景 |
|---|--------|------|---------|
| 1 | 编辑极简风 | 克制深色底，蓝紫强调线 | SaaS 后台、开发者工具 |
| 2 | 电影感深空 | 纯黑底，品红青色对撞 | 创意工作室、影视作品 |
| 3 | 暖纸手作 | 奶油底，手写衬线 | 品牌官网、内容出版 |
| 4 | 数据密集终端 | 深色仪表盘，荧光标注 | 金融数据、监控面板 |
| 5 | 粗野撞色 | 大胆撞色，零圆角 | 媒体出版、潮流品牌 |
| 6 | 液态玻璃 | 半透明叠层，毛玻璃 | 科技产品、Apple 生态 |
| 7 | 杂志编辑 | 多栏排版，大标题压版 | 新闻媒体、长文阅读 |
| 8 | 游戏化活泼 | 圆润撞色，手绘涂鸦 | 教育产品、儿童应用 |
| 9 | 日式禅意 | 大留白，灰阶朱红 | 生活方式、高端品牌 |
| 10 | 复古未来 | Y2K 霓虹，CRT 扫描线 | 游戏产品、复古品牌 |

请选择一个模板（输入编号），或说"都不满意"进入自定义方向探索。
```

### 选定后

用户选定模板后，直接生成基于该模板的 DesignSystemManifest：

```markdown
# DesignSystemManifest

> 来源：美学启动套件 - 模板{N}：{模板名}
> 微调：{如有微调，列出变更项}

## 1. 配色方案
{从模板提取的完整配色，补充 oklch 标注}

## 2. 字体
{从模板提取的字体配对}

## 3. 间距标尺
{从模板提取的间距系统}

## 4. 圆角
{从模板提取的圆角规范}

## 5. 阴影
{根据模板风格推导阴影层级}

## 6. 卡片样式
{根据模板风格推导卡片规范}

## 7. 组件清单
{初步组件清单，交给 design-system-extract 第二部分细化}
```

同时在 DesignBrief 中追加：

```markdown
## 美学模板来源
- 使用模板：模板{N} - {模板名}
- 微调项：{如有}
```

### 微调处理

用户选定模板后可以要求微调，常见微调维度：

| 微调维度 | 示例 | 处理方式 |
|---------|------|---------|
| 换配色 | "把强调色换成绿色" | 修改对应 Token 值，保持色相和谐 |
| 换字体 | "标题换成衬线" | 替换 display 字体，保持 body 字体 |
| 调间距 | "间距再大一点" | 调整基础间距单位或倍数 |
| 调圆角 | "圆角再圆一点" | 调整圆角值，保持风格一致 |
| 调明暗 | "有没有浅色版" | 反转明暗关系，保持色相和对比度 |

微调后更新 DesignSystemManifest，并在 PatchLog 中记录变更。

---

## 注意事项

- 本技能优先于 `frontend-aesthetic-direction` 触发——只有用户明确说"都不满意"或"我要自定义"时才降级
- 模板中的字体需要从 Google Fonts 或 CDN 引入，确保可加载
- 模板 6（液态玻璃）的 `backdrop-filter` 在部分浏览器需要 `-webkit-` 前缀
- 模板 10（复古未来）的 CRT 扫描线效果用 CSS `repeating-linear-gradient` 实现，不影响性能
- 模板选定后仍需继续用 `design-system-extract` 细化组件规范
- 模板选定后仍需走完整的 QA 流程（触发 `qa-review` 一次完成五道检查）
- **重要**：模板 3（暖纸手作）的奶油底 + 赤陶橙组合与强禁止清单第 10 条相关，但本模板是有意识的风格选择（参考 Aesop 和 Stripe Press），在使用时必须在 DesignBrief 中注明"基于暖纸手作模板，赤陶橙为有意识选择而非模型惯性"
