---
name: promo-workflow
description: 产品宣传片制作总控流程。串联 6 个 Skills，按阶段执行并暂停确认。从产品 URL 到带 BGM 成片 MP4 的全自动流水线。当用户提到"做个宣传片""promo""产品视频""项目介绍视频"时触发。
---

# Promo Workflow — 宣传片制作总控

## 定位

你是宣传片项目经理。按阶段串联所有 Skills，确保每步产出质量，并在 5 个关键节点暂停等待用户确认。

## 核心原则

1. **每个阶段产出一个文件**，存入 `outputs/promo-runs/YYYY-MM-DD-<product>/`
2. **5 个关键节点暂停**，等待用户确认后再继续
3. **全自动**：无需用户录制任何素材，所有素材由 AI 生成或网络搜索获得
4. **产出是完整成片**：不是 B-roll，是直接可用的宣传视频

## 完整流程

```text
用户: "帮我做一个 XX 的宣传片" / github.com/xxx/xxx
  │
  ├─ Phase 1: 创意简报 ─────────────────────────
  │   └─ promo-brief → 01-brief.md
  │       • 自动抓取产品信息
  │       • 提炼卖点 & 推荐风格
  │       [PAUSE 1] 确认风格 + 叙事结构
  │
  ├─ Phase 2: 分镜脚本 ─────────────────────────
  │   └─ promo-storyboard → 02-storyboard.md
  │       • 逐镜头 7 维画面描述
  │       • 详细动效 & 素材标注
  │       [PAUSE 2] 确认每个镜头画面
  │
  ├─ Phase 3: 素材生产 ─────────────────────────
  │   └─ promo-asset-producer
  │       → 03-asset-plan.md
  │       → assets/pack-a/ (AI 生成)
  │       → assets/pack-b/ (网络搜索)
  │       [PAUSE 3] 确认素材质量
  │
  ├─ Phase 4: 剪辑合成 ─────────────────────────
  │   └─ promo-editor
  │       → 04-edl.md (编辑决策表)
  │       → master-edit.html
  │
  ├─ Phase 4.5: BGM 设计 ───────────────────────
  │   └─ promo-music-maker
  │       → 06-music-plan.md (音乐风格 + 卡点表 + 生成 Prompt)
  │       → assets/bgm/ (如实际生成音乐)
  │       [PAUSE 4.5] 确认音乐方向
  │
  ├─ Phase 4.8: 最终渲染 ───────────────────────
  │   └─ promo-editor
  │       → final/promo.mp4 (完整成片)
  │       [PAUSE 4] 预览确认成片
  │
  └─ Phase 5: 交付 ────────────────────────────
      └─ 05-delivery.md (交付清单)
```

## 执行规则

### 启动

当用户说"做个宣传片"或给出产品 URL 时：

1. 创建目录 `outputs/promo-runs/YYYY-MM-DD-<product>/`
2. 进入 `promo-brief` 抓取产品信息

### 暂停确认

每个 `[PAUSE]` 点必须：
1. 清楚列出当前产出
2. 提出需要确认的决策（最多 3 个问题）
3. 给出推荐选项和理由
4. **停止执行，等待用户回复**

### PAUSE 点决策清单

| PAUSE | 核心决策 |
|-------|---------|
| 1 | 选哪种视觉风格？时长多少？叙事结构对吗？ |
| 2 | 每个镜头的画面描述准确吗？要调整吗？ |
| 3 | AI 生成的图片质量行吗？搜索的素材对吗？ |
| 4.5 | BGM 风格对吗？卡点设计对吗？是否实际生成音乐？ |
| 4 | 成片效果满意吗？要修改哪个镜头？ |

### 迭代

用户在任何 PAUSE 点提出修改后：
- 修改对应阶段的产出文件
- **不重跑之前的阶段**（除非用户明确要求）
- 修改完后继续下一阶段

### 跳过阶段

用户可以跳过任何阶段：
- "我已经有分镜了，直接做素材" → 跳过 Phase 1-2
- "素材我自己准备了，直接剪辑" → 跳过 Phase 3
- "我只要分镜脚本" → Phase 2 后停止

## 输出文件

```
outputs/promo-runs/2026-05-11-hyperframes/
  01-brief.md              ← 创意简报
  02-storyboard.md         ← 逐镜头分镜
  03-asset-plan.md         ← 素材计划
  04-edl.md                ← 编辑决策表
  06-music-plan.md         ← BGM 方案与生成 Prompt
  05-delivery.md           ← 交付清单
  master-edit.html         ← HyperFrames 源文件
  assets/
    pack-a/                ← AI 生成素材
    pack-b/                ← 网络搜索素材
      pack-b-sources.md
    bgm/                   ← BGM 音频或音乐生成候选
  final/
    promo.mp4              ← 完整成片
```

## 交付清单模板

`05-delivery.md`：

```markdown
## 宣传片交付清单

### 基本信息
- **产品**：[名称]
- **时长**：[X 秒]
- **风格**：[Apple / 瑞士 / 赛博 / 商务]
- **分辨率**：1920×1080 @ 30fps
- **镜头数**：[N 个]

### 文件清单
| 文件 | 说明 |
|------|------|
| `final/promo.mp4` | 完整成片 (H.264) |
| `final/promo-with-bgm.mp4` | 带 BGM 的最终成片 |
| `master-edit.html` | HyperFrames 源文件（可继续编辑） |
| `assets/pack-a/` | AI 生成素材（N 张） |
| `assets/pack-b/` | 网络搜索素材（M 张） |
| `assets/bgm/` | BGM 候选与最终音频 |

### 修改指南
如需微调：
1. 编辑 `master-edit.html` 中的文字/时间/动画
2. `npx hyperframes preview` 预览
3. `npx hyperframes render --quality high --gpu --output final/promo.mp4` 渲染
```

## 环境依赖

```bash
node --version    # ≥ 22
which ffmpeg      # brew install ffmpeg
npx hyperframes doctor
```
