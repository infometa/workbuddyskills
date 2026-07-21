# TeachAny Baseline Rules（精简版）

TeachAny 只有一套标准：所有课件必须完整包含以下 19 项基线。

**没有"快速模式基线"，没有"占位就行"。**

唯一豁免条件：某项依赖的外部资源在当前网络环境下**反复尝试（≥2 次，间隔 ≥30 秒）确实无法连接**，且无本地替代方案。豁免时必须在 PLAN.md 和交付说明中记录：具体报错、已尝试次数、后续补齐步骤。

## 19 项基线

1. TTS 旁白音频（`tts/` 目录，≥1 个有声 MP3，单个 ≥5KB）。
2. 至少一个教学动画/视频（课型需要时）。
3. Canvas/SVG/iframe 真实互动（非弹窗、非纯点击）。
4. 学科插图或场景图（`assets/` 目录，≥1 张真实内容图片，≥5KB）。
5. Hero 知识结构图（`assets/hero-infographic.svg` 或 `hero-infographic.png`）。
6. 音频播放器或连续讲解入口（标准 TTS narrator 或 ai-tutor.js）。
7. 标准知识图谱模块（`data-teachany-kg` 属性 + `<section id="knowledge-graph">`）。
8. 标准 AI 学伴入口卡片（正文靠前位置可见，不只依赖 FAB）。
9. section hints。
10. TTS narrator（`scripts/teachany-tts-narrator.js`）。
11. AI tutor JS（`scripts/ai-tutor.js`）。
12. knowledge graph JS/CSS（`scripts/teachany-knowledge-graph.js`）。
13. 五件套完整挂载（AI 学伴、导师卡片、TTS narrator、section hints、知识图谱）。
14. manifest.json 元信息完整（name、subject、grade、node_id、teachany_version 等必填字段）。
15. 顶部 TeachAny 品牌栏与版本标注。
16. 历史/地理使用标准地图模块与地图库（`find-map.py` 先查）。
17. 发布注册：registry / community index / knowledge graph manifest 均通过 `rebuild-index.py` 更新。
18. 问题锚点模块（学生进入即选择/输入要解决的问题）。
19. 移动端与小程序 web-view 准备（375px 可用，按钮 ≥44px，无 hover-only 核心功能）。

## 关键禁令

- 禁止用静态图伪装互动。
- 禁止手写知识图谱、AI 学伴卡片、TTS 控制器来替代标准模块。
- 禁止手改 registry 类生成文件（registry.json、community/index.json）。
- 禁止在没有证据时声称线上可访问（URL 返回 200 才算发布完成）。
- 禁止以"先做简版""用户只是看看""时间不够"为由跳过基线项。
- 禁止用 <5KB 的空白图片或静音 MP3 作为资产占位。
- **禁止在 hero/header 与第一个 section 之间放置裸 `<img>` 标签**。概念图、分层图、练习图等必须嵌入对应教学 section 内部，或用 `<figure>` 包裹并附带 `<figcaption>`。不得在页面顶部堆叠独立图片块。
- **禁止 assets/ 下存在 <5KB 的 webp/png/jpg 占位文件**。所有图片资产必须是真实内容图（hero SVG、教学示意图、Canvas 截图等）。如果图片资源暂未生成，在 HTML 中不要引用它。

## 常用验证

```bash
node "$TEACHANY_SKILL/scripts/validate-courseware.cjs" "$COURSE_DIR"
python3 "$TEACHANY_SKILL/scripts/find_nodes.py" "知识点"
python3 "$TEACHANY_SKILL/scripts/find-map.py" 唐
python3 scripts/find-hero.py <course-id>
python3 scripts/rebuild-index.py
```

## 反模式速查

| 反模式 | 正确做法 |
|---|---|
| "先做简版再补" | 直接做完整版，不存在简版 |
| "用户没说要发布，先本地看看" | 每个课件都是正式课件，都要发布 |
| 先写漂亮页面再补教学 | 先问题锚点和学习闭环 |
| 全文讲解无操作 | 每个核心概念至少一个可操作点 |
| AI 学伴只放 FAB | 正文靠前加导师卡片 |
| 图谱手写 SVG | 用 `data-teachany-kg` 标准模块 |
| 地图手写 Leaflet | 用 TeachAny 地图模块和 `find-map.py` |
| TTS 用 <5KB 静音 MP3 | 用 `tts-engine.py` 生成真实语音 |
| 图片用 <5KB 纯色占位 PNG | 生成真实 Hero SVG 或教学示意图 |
| Hero 后堆叠裸 `<img>` 标签 | 图片嵌入对应 section 内部或用 `<figure>` 包裹 |
| assets/ 放占位 webp/png 凑数 | 要么生成真实图片，要么不引用不放文件 |
