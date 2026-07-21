---
name: promo-creator-skills
description: 产品宣传片制作总控 skill pack。用于从产品说明、官网、应用截图或 GitHub 仓库制作 60-90 秒宣传视频，按阶段完成 brief、storyboard、素材、HyperFrames 剪辑、BGM 设计和交付。当用户要做宣传片、产品视频、项目介绍视频、launch video、开源项目 promo、BGM 卡点或真实软件界面宣传片时使用。
description_zh: "产品宣传片全流程制作，涵盖简报、分镜、素材、剪辑、配乐到交付"
description_en: "End-to-end product promo video creation: brief, storyboard, assets, editing, BGM, and delivery"
---

# Promo Creator Skills

这是产品宣传片创作的总控入口。它必须能独立指导完整项目；子 skill 是阶段深水区，不是唯一的流程来源。

默认目标：用真实产品信息、真实软件界面和可验证素材，制作一支 60-90 秒、可发布的产品宣传片 MP4。不要把它当成氛围视频、图片轮播或泛科技动效练习。

## 总控判断

当用户只说“做宣传片 / 产品视频 / launch video / promo”时，默认走完整流程：

```text
产品信息或 URL
  -> 01-brief.md
  -> 02-storyboard.md
  -> 03-asset-plan.md + assets/
  -> 04-edl.md + master-edit.html
  -> 06-music-plan.md + assets/bgm/
  -> final/promo.mp4 或 final/promo-with-bgm.mp4
  -> 05-delivery.md
```

当用户明确只要某一段能力时，只执行对应阶段。例如“只要 BGM prompt”只用音乐阶段；“我已经有素材，直接剪辑”从 EDL 和 HyperFrames 阶段开始。

## 子 Skill 路由

优先按总控流程推进；进入某个阶段时，读取对应子 skill 的 `SKILL.md` 获取详细规范。

| 用户目标 | 详细规范 |
|---|---|
| 从零做完整宣传片 | `promo-workflow/SKILL.md` |
| 只做产品分析和创意简报 | `promo-brief/SKILL.md` |
| 已有 brief，要写分镜 | `promo-storyboard/SKILL.md` |
| 已有分镜，要准备素材 | `promo-asset-producer/SKILL.md` |
| 已有素材，要剪辑渲染 | `promo-editor/SKILL.md` |
| 要配乐、BGM、卡点音乐 prompt | `promo-music-maker/SKILL.md` |

## 阶段流程

### Phase 1: Brief

详细规范见 `promo-brief/SKILL.md`。输入可以是产品说明、官网、GitHub 仓库、应用截图、用户口述或竞品链接。

产出 `01-brief.md`：
- 产品定位和目标观众
- 核心卖点和证明点
- 推荐视觉风格
- 叙事结构和时长建议
- 风险、素材缺口和需要用户确认的问题

暂停点：确认定位、风格、时长、主叙事。

### Phase 2: Storyboard

详细规范见 `promo-storyboard/SKILL.md`。不要在 brief 未确认前直接写完整剪辑。

产出 `02-storyboard.md`：
- 逐镜头时间码
- 每个镜头的画面、文案、动效、转场、素材需求
- 真实 UI / 真实产品信号应该出现在哪些镜头
- HyperFrames 实现提示

暂停点：确认镜头内容、节奏、文案密度和转场方向。

### Phase 3: Assets

详细规范见 `promo-asset-producer/SKILL.md`。优先真实产品素材，其次生成补充视觉。

产出：
- `03-asset-plan.md`
- `assets/pack-a/`：AI 生成或补充视觉
- `assets/pack-b/`：官网、截图、开源项目、文档或其他可验证素材
- `assets/pack-b/pack-b-sources.md`：来源记录

暂停点：确认素材质量和版权/来源可接受性。

### Phase 4: Edit

详细规范见 `promo-editor/SKILL.md`。用 HyperFrames/HTML/CSS/GSAP 构建可渲染视频，不只给剪辑建议。

产出：
- `04-edl.md`
- `master-edit.html`
- `final/promo.mp4`

暂停点：确认成片结构、画面密度、节奏和需要返修的镜头。

### Phase 5: Music

详细规范见 `promo-music-maker/SKILL.md`。音乐必须服务剪辑节奏，不要默认生成 ambient 科技垫底音乐。

产出 `06-music-plan.md`：
- 音乐风格、BPM、情绪曲线
- 和镜头转场对齐的 hit points
- Mureka / Skywork Music Maker 英文 prompt
- negative prompt
- 至少 2 个有明显差异的方向

用户确认或要求实际生成时，再调用脚本生成 BGM。

### Phase 6: Delivery

补齐 `05-delivery.md`：
- 最终视频路径
- 源文件路径
- 素材和 BGM 清单
- 修改方式
- 已知限制

## 工作目录

每个项目创建独立 run 目录：

```text
outputs/promo-runs/YYYY-MM-DD-<product>/
```

如果用户给了明确项目名，使用用户项目名；否则根据产品名生成短 slug。

## 暂停规则

必须暂停的节点：
- Brief 完成后
- Storyboard 完成后
- 素材计划或关键素材完成后
- BGM 方向确认前实际生成音乐
- 最终渲染后

暂停时最多问 3 个问题，并给出推荐选项。用户明确说“按你推荐来 / 继续 / ok”时，按推荐方案推进，不要反复追问。

## 执行约束

- 先做产品判断，再做画面。
- 先写分镜，再批量生成素材。
- 先确认音乐方向，再消耗音乐生成额度。
- 真实软件界面优先于抽象装饰图。
- 所有外部素材记录来源。
- 不要把多个根 HyperFrames composition 留在同一渲染目录。
- 如果图片、浏览器、音乐或渲染能力不可用，输出可执行 prompt、素材清单或命令，并明确缺口。

## BGM 默认策略

产品宣传片默认先给两个差异明显的方向：

| 方向 | 用途 |
|---|---|
| `Commercial Product Launch` | 产品发布、商业展示、CTA 更强的广告片 |
| `Clean UI Demo Groove` | 真实软件界面、SaaS、流程展示、UI demo |

候选之间必须在 genre、rhythm、bass、hook、energy curve 上形成明显差异。避免多个 prompt 都写成 `minimal / ambient / soft pulse / glass ticks`。

详细音乐规范见 `promo-music-maker/SKILL.md` 和 `references/product_promo_bgm_prompting.md`。

## 最小可执行流程

当只能读取本文件时，也按下面步骤工作：

1. 根据用户输入创建 run 目录。
2. 写 `01-brief.md`，暂停确认。
3. 写 `02-storyboard.md`，暂停确认。
4. 写 `03-asset-plan.md`，收集或生成素材，暂停确认。
5. 写 `04-edl.md` 和 `master-edit.html`，渲染 `final/promo.mp4`。
6. 写 `06-music-plan.md`，确认后生成或匹配 BGM。
7. 合成 `final/promo-with-bgm.mp4`，写 `05-delivery.md`。
