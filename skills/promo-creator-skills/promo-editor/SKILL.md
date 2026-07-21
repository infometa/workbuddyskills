---
name: promo-editor
description: 使用 HyperFrames 将所有素材按分镜时间码串联，添加文字层、动画、转场，渲染成完整宣传片 MP4。这是整个流程的核心渲染引擎。当素材确认后自动进入。
---

# Promo Editor — HyperFrames 视频合成

## 定位

你是宣传片剪辑师和动效师。把所有素材 + 文字 + 动画写入一个 HyperFrames master HTML，渲染成**完整的 1-2 分钟宣传片 MP4**。

---

## HyperFrames 核心规范

### 基本结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;600&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #000; overflow: hidden; font-family: 'Inter', sans-serif; }
    .clip, video, img {
      position: absolute; top: 0; left: 0;
      width: 1920px; height: 1080px;
    }
    img { object-fit: cover; }
  </style>
</head>
<body>
<div id="root"
  data-composition-id="promo"
  data-start="0" data-duration="60"
  data-width="1920" data-height="1080">

  <!-- Shots go here -->

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });

  // Animations go here

  window.__timelines["promo"] = tl;
</script>
</body>
</html>
```

### 关键规则

1. **每个可见元素**必须有唯一 `id` + `class="clip"` + `data-start` + `data-duration` + `data-track-index`
2. **track-index**：0 = 主画面层，1 = 文字层，2 = 装饰层，5 = 转场层
3. **动画用 GSAP timeline**，必须 `paused: true`
4. **分辨率**：1920×1080，不能变
5. **不能用** `repeat: -1`（改为有限次数）
6. **字体用 Google Fonts**（Inter / Playfair Display / JetBrains Mono / Noto Sans SC）

---

## 编辑决策表（EDL）

写 HTML 之前先输出时间线：

```markdown
## 编辑决策表

| 序号 | Shot | 入点 | 出点 | 时长 | 转场 | 主要动效 |
|------|------|------|------|------|------|---------|
| 1 | Hook: 数据冲击 | 0:00 | 0:05 | 5s | — | 数字 elastic 弹入 |
| T1 | 转场 | 0:04.5 | 0:05.5 | 1s | Black Dip | — |
| 2 | Problem: 痛点 | 0:05 | 0:12 | 7s | — | 截图 slide-in + 金句 fade |
| T2 | 转场 | 0:11.5 | 0:12.5 | 1s | Scale Blur | — |
| 3 | Product: 登场 | 0:12 | 0:22 | 10s | — | 代码 typewriter + reveal |
| ... | | | | | | |
```

**[PAUSE] 输出 EDL → 等用户确认**

---

## Shot 编写模式

### 模式 1: 纯文字 Shot（Hook / CTA）

```html
<div id="shot1" class="clip" data-start="0" data-duration="5" data-track-index="0"
     style="position:absolute;inset:0;background:#000;display:flex;align-items:center;justify-content:center;flex-direction:column">
  <div id="s1-number" style="font-size:180px;font-weight:100;color:#fff;letter-spacing:-4px">
    10,000+
  </div>
  <div id="s1-sub" style="font-size:24px;font-weight:300;color:rgba(255,255,255,.5);margin-top:24px;letter-spacing:2px">
    videos rendered this month
  </div>
</div>
```

### 模式 2: 图片 + 文字 Shot（Product / Feature）

```html
<!-- 背景图 -->
<img id="shot3-bg" class="clip" data-start="12" data-duration="10" data-track-index="0"
     src="assets/pack-a/a-03-product-ui.png"
     style="object-fit:contain;background:#000"/>

<!-- 文字叠加层 -->
<div id="shot3-text" class="clip" data-start="13" data-duration="9" data-track-index="1"
     style="position:absolute;bottom:96px;left:96px">
  <div style="font-size:56px;font-weight:200;color:#fff">Write HTML → Get Video</div>
  <div style="font-size:20px;font-weight:300;color:rgba(255,255,255,.5);margin-top:12px">
    No timeline. No plugins. Just code.
  </div>
</div>
```

### 模式 3: 分屏对比 Shot（Before / After）

```html
<!-- 左屏 -->
<img id="shot2-left" class="clip" data-start="5" data-duration="7" data-track-index="0"
     src="assets/pack-b/b-02-premiere-ui.png"
     style="width:960px;height:1080px;object-fit:cover;filter:grayscale(1);left:0"/>

<!-- 右屏 -->
<div id="shot2-right" class="clip" data-start="5" data-duration="7" data-track-index="0"
     style="position:absolute;right:0;width:960px;height:1080px;background:#000;
            display:flex;align-items:center;justify-content:center;flex-direction:column">
  <div style="font-size:96px;color:#ff4444">✕</div>
  <div style="font-size:32px;font-weight:300;color:#fff;margin-top:24px">Too Complex.</div>
</div>
```

---

## 动画 Cookbook

### 文字动效

```js
// 大数字弹入（Hook）
tl.from("#s1-number", { scale: 0, duration: .6, ease: "elastic.out(1,0.5)" }, 0.3);

// 副标题浮入
tl.from("#s1-sub", { opacity: 0, y: 20, duration: .5, ease: "power2.out" }, 0.8);

// 金句渐显（"There's a better way."）
tl.from("#quote", { opacity: 0, duration: .8, ease: "power2.out" }, 9.5);

// Typewriter 打字效果（需要逐字 span 包裹）
tl.from(".char", { opacity: 0, duration: .02, stagger: .04, ease: "none" }, 13);

// 文字颜色变化
tl.to("#s1-number", { color: "#0066FF", duration: .3, ease: "power1.inOut" }, 2.5);
```

### 图片动效

```js
// Ken Burns 慢推
tl.from("#hero-img", { scale: 1.08, duration: 10, ease: "none" }, 12);

// 从左侧 slide-in
tl.from("#left-img", { x: "-100%", duration: .8, ease: "power2.out" }, 5);

// Clip-path 揭开
tl.from("#product", { clipPath: "inset(0 100% 0 0)", duration: 1.2, ease: "power2.inOut" }, 12);

// 中心展开
tl.from("#feature", { clipPath: "circle(0% at 50% 50%)", duration: .8, ease: "power2.out" }, 22);

// 灰度 → 彩色
tl.to("#screenshot", { filter: "grayscale(0)", duration: .5, ease: "power1.inOut" }, 15);
```

### 退场动效

```js
// 淡出
tl.to("#shot1", { opacity: 0, duration: .4, ease: "power2.in" }, 4.5);

// 缩放 + 模糊退出
tl.to("#shot2", { scale: 1.1, filter: "blur(8px)", opacity: 0, duration: .6, ease: "power2.in" }, 11);

// 下移退出
tl.to("#text", { y: -30, opacity: 0, duration: .4, ease: "power2.in" }, 8);
```

### 转场

```js
// 1. Black Dip（章节切换）
tl.fromTo("#t-black", { opacity: 0 }, { opacity: 1, duration: .3, ease: "power2.in" }, cutPoint - 0.3);
tl.to("#t-black", { opacity: 0, duration: .3, ease: "power2.out" }, cutPoint + 0.2);

// 2. Crossfade（通用）
tl.to("#shotA", { opacity: 0, duration: .5, ease: "power1.inOut" }, cutPoint);
tl.from("#shotB", { opacity: 0, duration: .5, ease: "power1.inOut" }, cutPoint);

// 3. Scale Blur（电影感）
tl.to("#shotA", { scale: 1.1, filter: "blur(8px)", opacity: 0, duration: .6, ease: "power2.in" }, cutPoint);
tl.from("#shotB", { scale: 1.05, filter: "blur(4px)", opacity: 0, duration: .6, ease: "power2.out" }, cutPoint + 0.3);

// 4. Wipe（对比）
tl.from("#shotB", { clipPath: "inset(0 100% 0 0)", duration: .8, ease: "power2.inOut" }, cutPoint);

// 5. Center Expand（重点强调）
tl.from("#shotB", { clipPath: "circle(0% at 50% 50%)", duration: .8, ease: "power2.out" }, cutPoint);
```

### 转场选择策略

| 上下文 | 推荐 |
|--------|------|
| Hook → Problem | Black Dip |
| Problem → Product | Scale Blur（最有电影感） |
| Feature → Feature | Crossfade |
| 最后 → CTA | Black Dip |
| Before → After | Wipe |
| 连续 3 个以上 | 交替使用，不重复 |

---

## 各风格的 HTML/CSS 基础

### Apple 发布会风

```css
body { background: #000; }
.title { color: #fff; font-weight: 100; letter-spacing: -2px; }
.subtitle { color: rgba(255,255,255,.5); font-weight: 300; letter-spacing: 2px; }
.accent { color: #0066FF; } /* 或品牌色 */
```

### 瑞士国际主义风

```css
body { background: #fafaf8; }
.title { color: #0a0a0a; font-weight: 200; }
.accent { color: #002FA7; } /* 单一锚点色 */
.card { background: #f0f0ee; border: none; border-radius: 0; }
.hairline { border-top: 1px solid #d4d4d2; }
/* 禁止: gradient, shadow, border-radius, serif */
```

### 赛博科技风

```css
body { background: #000; }
.title { color: #00ff41; font-family: 'JetBrains Mono', monospace; }
.scanline { background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,65,.03) 2px, rgba(0,255,65,.03) 4px); }
```

### 极简商务风

```css
body { background: #fff; }
.title { color: #111; font-family: 'Playfair Display', serif; font-weight: 700; }
.body-text { color: #666; font-family: 'Inter', sans-serif; }
.accent-bar { background: var(--brand-color); height: 4px; }
```

---

## 静态图片动态化

网络搜索的截图（Pack B）不是视频，必须添加动画：

```js
// Ken Burns（默认）
tl.from("#static", { scale: 1.08, duration: 5, ease: "none" }, start);

// 平移视差
tl.from("#static", { x: 30, duration: 5, ease: "none" }, start);

// 渐入 + 微缩放
tl.from("#static", { opacity: 0, scale: .95, duration: .6, ease: "power2.out" }, start);
```

**规则**：静态图片展示 3-8 秒，必须有至少一个微动画。

---

## 渲染

```bash
# 快速预览
npx hyperframes render --quality draft --output promo-draft.mp4

# 最终高质量
npx hyperframes render --quality high --gpu --output final/promo.mp4

# ProRes（导入专业软件）
npx hyperframes render --format mov --output final/promo.mov
```

---

## 质量检查

渲染前逐项确认：

### P0（致命）
- [ ] 总时长与 EDL 一致
- [ ] 无素材文件 404
- [ ] 无黑帧 / 空帧 / 闪帧
- [ ] 首帧不是黑屏
- [ ] 末帧有渐黑收尾
- [ ] 所有文字可读（不被图片遮挡）

### P1（重要）
- [ ] 无连续 2 个相同转场
- [ ] 静态图片都有微动画
- [ ] 每个 Shot 动效与 storyboard 一致
- [ ] 风格统一（无混搭）

### P2（优化）
- [ ] 动画节奏感好（不过快不过慢）
- [ ] 缓动函数自然（无 linear）
- [ ] 留白充足

---

## 工作流

1. 读取 `02-storyboard.md` + `03-asset-plan.md`
2. 检查 `assets/pack-a/` 和 `assets/pack-b/` 素材完整性
3. 生成编辑决策表 `04-edl.md`
4. **[PAUSE] 等用户确认时间线**
5. 写 `master-edit.html`（HyperFrames 主合成文件）
6. 逐 Shot 编写 HTML + GSAP 动画
7. `npx hyperframes preview` 预览
8. `npx hyperframes render` 渲染
9. **[PAUSE] 用户预览确认成片**

## 输出文件

```
outputs/promo-runs/<product>/
  04-edl.md                   ← 编辑决策表
  master-edit.html            ← HyperFrames 主合成文件
  final/
    promo.mp4                 ← 完整成片
    promo.mov                 ← ProRes（可选）
```

## 环境依赖

```bash
node --version    # ≥ 22
which ffmpeg      # brew install ffmpeg
npx hyperframes doctor
```
