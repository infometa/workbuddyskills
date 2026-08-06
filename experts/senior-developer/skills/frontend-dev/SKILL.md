---
name: frontend-dev
description: |
  Frontend development with premium UI design, animations, and AI-generated media assets.
  TRIGGER when: building landing pages, marketing sites, product pages with rich animations,
  generating media assets (image/video/audio/music via MiniMax API),
  implementing cinematic scroll animations, creating generative art.
  DO NOT TRIGGER when: simple UI components, basic form pages, minor CSS fixes,
  adding a button or modal, standard CRUD interfaces, simple responsive adjustments.
description_zh: "前端开发与AI媒体生成"
description_en: "Frontend dev with AI media, animations & persuasive copy"
version: 1.1.0
license: MIT
metadata:
  category: frontend
---

# Frontend Studio

构建生产级前端页面，整合 5 大能力：设计工程、动效系统、AI 资产生成、文案、生成艺术。

## Skill Structure

```
frontend-dev/
├── SKILL.md                      # 本文件（工作流骨架）
├── scripts/                      # AI 资产生成脚本
│   ├── minimax_tts.py            # 文本转语音
│   ├── minimax_music.py          # 音乐生成
│   ├── minimax_video.py          # 视频生成（异步）
│   └── minimax_image.py          # 图片生成
├── references/                   # 详细指南（按需读取）
│   ├── design-rules.md           # 设计规则与禁止模式
│   ├── motion-recipes.md         # 动效代码片段
│   ├── minimax-cli-reference.md  # CLI 参数速查
│   ├── asset-prompt-guide.md     # 资产 Prompt 工程
│   ├── minimax-tts-guide.md      # TTS 用法
│   ├── minimax-music-guide.md    # 音乐生成
│   ├── minimax-video-guide.md    # 视频生成
│   ├── minimax-image-guide.md    # 图片生成
│   ├── minimax-voice-catalog.md  # 语音ID目录
│   └── env-setup.md              # 环境配置
├── templates/                    # 模板
│   ├── viewer.html
│   └── generator_template.js
└── canvas-fonts/                 # 字体文件
```

---

## Workflow

### Phase 1: Design Architecture
1. 分析需求 — 确定页面类型和上下文
2. 规划布局分区，确定资产需求
3. 选择技术方案（详见 `references/design-rules.md`）

### Phase 2: Motion Architecture
1. 按分区选择动效工具（见下方工具矩阵）
2. 规划动效序列，遵守性能规则

### Phase 3: Asset Generation
使用 `scripts/` 生成所有图片/视频/音频资产。**绝不使用占位符 URL**。

1. 解析资产需求（类型、风格、规格、用途）
2. 编写 Prompt，展示给用户确认后再生成
3. 执行脚本，保存到项目本地
4. **所有资产保存完毕后才进入Phase 5**

### Phase 4: Copywriting
使用 AIDA/PAS/FAB 框架撰写文案。不使用 Lorem ipsum。

### Phase 5: Build UI
搭建项目，逐区构建。集成生成的资产和文案。所有媒体引用必须指向本地文件。

### Phase 6: Quality Gates
- [ ] 移动端布局正常
- [ ] `min-h-[100dvh]` 非`h-screen`
- [ ] Empty/Loading/Error 状态齐全
- [ ] 动效工具未在同一组件混用
- [ ] `useEffect` 有 cleanup
- [ ] `prefers-reduced-motion` 已处理
- [ ] 无占位符 URL（grep 检查）
- [ ] 所有媒体资产存在于本地
- [ ] 依赖已在`package.json` 中声明

---

## Motion Tool Selection Matrix

| 场景 | 工具 |
|------|------|
| UI 进出/布局动画 | **Framer Motion** |
| 滚动叙事（pin, scrub）| **GSAP + ScrollTrigger** |
| 循环图标| **Lottie**（懒加载）|
| 3D/WebGL | **Three.js / R3F**（隔离 Canvas）|
| Hover/Focus 状态 | **纯 CSS** |
| 原生滚动驱动 | **CSS** `animation-timeline: scroll()` |

**冲突规则：**
- ❌ 同一组件不混用 GSAP + Framer Motion
- ❌ R3F 必须隔离在 Canvas wrapper中
- ❌ 重型库（Lottie/GSAP/Three.js）必须懒加载

---

## Asset Generation Quick Reference

| 类型 | 脚本 | 模式 |
|------|------|------|
| 图片 | `python3 scripts/minimax_image.py` | 同步 |
| TTS | `python3 scripts/minimax_tts.py` | 同步 |
| 音乐 | `python3 scripts/minimax_music.py` | 同步 |
| 视频 | `python3 scripts/minimax_video.py` | 异步（创建→轮询→下载）|

环境变量：`MINIMAX_API_KEY`（必须）

**资产命名规范：** `{type}-{descriptor}-{timestamp}.{ext}`

**预设快捷键：**
| 快捷键 | 规格 |
|--------|------|
| `hero` | 16:9, 电影感, 文字安全区 |
| `thumb` | 1:1, 主体居中 |
| `icon` | 1:1, 扁平, 干净背景 |
| `bg-video` | 768P, 6s, 静态镜头 |
| `bgm` | 30s, 无人声, 可循环 |

---

## Performance Rules

**只动画GPU 属性：** `transform`, `opacity`, `filter`, `clip-path`

**绝不动画：** `width`, `height`, `top`, `left`, `margin`, `padding`

**移动端：**
- 尊重 `prefers-reduced-motion`
-粗指针设备禁用视差/3D
- 粒子上限：桌面800/ 平板300/ 手机100

---

## 详细参考文档

需要深入指导时查阅 `references/` 目录：
- 设计规则与禁止模式 → `references/design-rules.md`
- 动效代码片段 → `references/motion-recipes.md`
- MiniMax 各类资产生成详细指南 → 对应 `references/minimax-*-guide.md`
- 环境配置 → `references/env-setup.md`
