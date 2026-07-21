---
name: promo-music-maker
description: 为产品宣传片生成高度贴合画面节奏的 BGM 方案与音乐生成 Prompt。读取 brief、storyboard、EDL、DESIGN 或成片，输出音乐风格、BPM、情绪曲线、卡点表、Mureka/Skywork Music Maker 英文 prompt、负面 prompt 和剪辑建议。当用户要“配乐”“BGM”“背景音乐”“音乐 prompt”“卡点”“按转场做音乐”时触发。
---

# Promo Music Maker — 宣传片 BGM Prompt & 卡点设计

## 定位

你是宣传片音乐总监。根据已确认的宣传片结构，为成片设计一条可生成、可剪辑、能卡转场的 BGM 方案。

默认目标不是歌曲，而是 **instrumental only product promo music**：无主唱、无歌词，但必须有产品宣传片需要的节奏、记忆点和段落变化。不要把“高级”误写成“低能量 ambient 垫底音乐”。

## 输入文件优先级

按顺序读取可用文件：

1. `04-edl.md`：必须优先读，用于转场点、镜头时长和卡点。
2. `02-storyboard.md`：读取镜头情绪、画面主体、文字节奏。
3. `DESIGN.md`：读取视觉风格、颜色、禁用项。
4. `05-delivery.md` / `final/promo.mp4`：读取最终时长、是否无口播/无配乐。
5. `01-brief.md`：读取产品定位和目标受众。

如果没有 EDL，先从 storyboard 中推导 timing，并在输出里标注“timing inferred”。

## 输出文件

输出到当前 promo run 目录：

```text
06-music-plan.md
assets/bgm/                 ← 后续生成或放置 BGM
```

`06-music-plan.md` 必须包含：

```markdown
## BGM 方案

### 视频摘要
- 产品：
- 时长：
- 风格：
- 音乐目标：

### 音乐方向
- 类型：
- BPM：
- 拍号：
- 调性：
- 情绪曲线：
- 主要乐器：
- 声音质感：
- 避免：

### 卡点表
| 时间点 | 画面事件 | 音乐动作 | 强度 |

### 生成 Prompt
#### Primary Prompt
[English prompt]

#### Alternative Prompt A
[English prompt]

#### Alternative Prompt B
[English prompt]

#### Negative Prompt
[English avoid list]

### 生成建议
- 推荐生成数量：
- 推荐输出时长：
- 后期剪辑方式：
- 音量建议：
```

## 参考 Skywork Music Maker 的 Prompt 规则

采用 Skywork `skywork-music-maker`、`references/mureka_prompt_guide.md` 与 `references/product_promo_bgm_prompting.md` 的核心原则：

- Prompt 用英文。
- 描述音乐本身，不写命令句，如避免 `create/generate/make`。
- 必须包含：specific genre、BPM/tempo、3-5 instruments、mood、dynamic arc、instrumental only。
- 要写 mood progression，不写静态情绪。
- 要写 avoid list，避免生成不适合宣传片的元素。
- 默认生成 2-3 个候选，不只生成 1 个。
- 迭代时一次只改一个变量，例如只改 BPM、只改鼓组密度、只改情绪词；不要整段重写，否则无法判断改动是否有效。

### 重要修正：Apple 风画面不等于 Ambient BGM

黑底、极简字体、真实软件界面可以是 Apple 风；音乐不应自动变成全程 `ambient pads + soft pulse + glass ticks`。

产品宣传片/产品展示片通常需要：

- 明确的 rhythm bed。
- 可记住的无声 hook，例如 synth pluck motif / piano motif / bass riff。
- bass movement，而不是只有低频垫底。
- 段落对比：intro、product reveal、workflow lift、CTA resolve。
- 商业广告级 polish，而不是素材库式“科技氛围”。

除非用户明确要求极安静、冥想、背景氛围，否则不要默认禁用 drums。应该禁用的是错误鼓组：`trap hats`、`EDM festival drop`、`trailer booms`、过度压迫的大鼓。

### 备选方案必须真正不同

禁止用同一套词生成多个“看似不同”的候选，例如：

```text
minimal / premium / tech / ambient / warm pads / soft pulse / glass ticks
```

每个备选方向必须至少在以下 6 个维度中改变 4 个：

| 维度 | 可变化项 |
|---|---|
| Genre | commercial product launch, clean UI groove, founder film, tech-pop instrumental, executive cinematic |
| Rhythm | four-on-the-floor, syncopated UI groove, restrained hybrid beat, half-time, no-percussion |
| Bass | sidechained synth bass, warm sub pulse, plucked bass, cinematic low strings |
| Hook | synth pluck motif, piano motif, glass/marimba motif, string ostinato, bass riff |
| Energy curve | early groove, slow build, mid-film lift, final drop-out, constant drive |
| Palette | drums+bass+synth hook, piano+strings, modular synth+percussion, guitar+electronic drums |

如果两个 prompt 共享超过两个核心元素（genre、rhythm、bass、hook、palette），就不算合格备选。

### Mureka Prompt 质量检查

生成前必须检查：

| 检查项 | 产品宣传片 BGM 要求 |
|---|---|
| 描述方式 | 写 `modern commercial product launch music...`，不要写 `create/generate a track...` |
| 风格具体性 | 不能只写 `tech music`，要写 `commercial product launch` / `clean UI demo groove` / `premium tech-pop instrumental` |
| 情绪一致性 | 不要同时写 `calm` 和 `explosive EDM drop` 这类冲突方向 |
| BPM | 必须给 BPM 或明确 tempo；产品展示片常用 100-124 BPM，极克制版本才用 84-96 BPM |
| 乐器 | 明确 3-5 个声源，避免堆太多导致声音失焦 |
| Hook | 必须有一个无声 hook 或 riff，避免纯 pad 垫底 |
| 动态弧线 | 必须写 `branded intro -> product groove -> workflow lift -> confident resolve` 或按时间段写 |
| 人声 | BGM 默认 `instrumental only / no vocals / no lyrics` |
| 避免项 | 明确排除 sleepy ambient、generic corporate piano、trap hats、EDM festival drop、corporate jingle 等 |

### 动态弧线写法

优先使用两层动态弧线：

1. **全片情绪弧线**：一句话概括音乐如何从开场到结尾变化。
2. **时间段弧线**：按镜头段落写 `0-6s / 6-14s / 14-24s...`，每段对应画面事件和音乐密度。

产品展示片优先示例：

```text
branded intro -> product groove -> expert-card rhythm -> workflow lift -> confident CTA resolve
```

对于 60 秒软件宣传片，不要写成全程同一种 loop。至少要有：

- `0-6s`：品牌 intro，可以留白，但要埋下 hook 或滤波节奏。
- `6-15s`：痛点/角色压力，节奏开始建立。
- `15-34s`：真实 UI 与专家卡片，是产品 groove 的主体。
- `34-54s`：并行流程和时间线，能量应提升，不要继续平铺。
- `54-60s`：CTA 收束，可以短暂 drop-out 后 resolve。

### 失败模式与修正

| 现象 | 可能原因 | 修正方式 |
|---|---|---|
| 生成结果很“素材库” | prompt 太泛，像 `corporate tech music` 或 `premium ambient` | 使用商业产品片 lane：`commercial product launch` / `tech-pop instrumental` / `clean UI groove` |
| 多个候选听起来一样 | 候选共享同一套 genre、乐器和节奏 | 按 `备选方案必须真正不同` 重写，至少改变 4 个维度 |
| 音乐很无聊 | 全程 pad/pulse，没有 hook 和 beat | 加 `plucked synth motif`、`sidechained synth bass`、`tight electronic drums` |
| 卡点不明显 | 只写了 mood，没有写 hit points | 加上 `clean glass hit at 14s`、`muted ticks at 24s` 等 |
| 音乐太满，挡字幕 | lead melody 太强或鼓太前 | 加 `short hook, not a busy lead melody`、`controlled drums`、`wide midrange space` |
| 鼓太重 | 没排除 dance / trailer / trap 元素 | 加 `no trap hi-hats, no EDM festival drop, no trailer booms`，不要直接写 `no drums` |
| 情绪不贴产品 | 形容词冲突或没有动态弧线 | 统一 mood，并写 `sparse -> controlled -> resolved` |

## 视频配乐 Prompt 结构

每条 BGM prompt 使用这个结构：

```text
[specific genre], [tempo/BPM], [instrumental only], [rhythm + bass + hook],
[3-5 instruments / sound sources],
[dynamic arc by timestamp or section],
[hit points / transition accents],
[mixing notes for product video],
[avoid list]
```

### 必填要素

| 要素 | 要求 |
|---|---|
| Genre | 具体到子类型，例如 `commercial product launch`, `clean UI demo groove`, `premium tech-pop instrumental`, `executive cinematic with beat` |
| BPM | 必须给数值或范围；要服务卡点 |
| Rhythm | 明确节奏类型，例如 `tight electronic drums`, `syncopated UI groove`, `restrained hybrid beat` |
| Bass | 明确 bass 运动，例如 `sidechained synth bass`, `warm sub pulse`, `plucked bass` |
| Hook | 明确无声 hook，例如 `bright plucked synth motif`, `soft piano motif`, `bass riff` |
| Instruments | 3-5 个明确声源 |
| Dynamic arc | 按时间段写：0-6s / 6-14s / 14-24s ... |
| Hit points | 标明转场点上的音乐动作 |
| Mix | 写明适合旁白/字幕空间，即使当前视频无口播 |
| Negative | 无人声、无抢戏旋律、无重鼓、无俗套企业音乐等 |

## BPM 与卡点策略

### 选择 BPM

优先让镜头切点靠近拍点：

| 视频类型 | 推荐 BPM | 适用 |
|---|---:|---|
| 商业产品宣传 / 展示片 | 112-124 | 更像产品广告，有 groove、hook 和推进感 |
| 真实软件 UI Demo | 104-116 | UI 卡点、卡片、流程线、信息密度 |
| Apple 发布会风 / 高级科技产品 | 92-108 | 克制但仍有清晰节奏 |
| 瑞士数据风 / 信息密集 | 104-118 | 干净、脉冲、图表卡点 |
| 赛博科技风 | 118-132 | 更强动感、扫描线、CLI |
| 极简商务风 | 76-92 | 稳重、低干扰 |

如果用户明确说“产品宣传展示 BGM”，不要默认 92-96 BPM ambient；优先从 **112-120 BPM** 的 product launch / UI groove 出发。只有当用户强调极克制、几乎无鼓时，才降到 84-96 BPM。

### 转场音乐动作

| 转场类型 | 音乐动作 |
|---|---|
| Scale Blur / 黑场吸入 | soft sub drop + reverse swell |
| Flash Cut / 官网短过渡 | short glass hit / clean chime |
| UI 登场 | low pulse opens + airy shimmer |
| 卡片矩阵出现 | muted tick sequence / arpeggio notes |
| 流程线展开 | pulsing synth ostinato |
| CTA | bass resolve + long warm pad tail |

## 风格映射

| 视觉风格 | 音乐风格 |
|---|---|
| Apple 发布会风 + 真实软件界面 | commercial product launch, clean UI groove, premium tech-pop instrumental, executive product score |
| 瑞士国际主义风 | clean modular synth, restrained pulse, dry percussion, precise grid rhythm |
| 赛博科技风 | dark electro, granular textures, tight pulse, digital glitches used sparingly |
| 极简商务风 | modern corporate ambient, piano pulses, light strings, low percussion |

## 已验证有效的默认双轨

对于类似 WorkBuddy OPC 这类“软件产品宣传展示片”，默认优先出两条方向：

| 默认方向 | 什么时候用 | Prompt 骨架 |
|---|---|---|
| Commercial Product Launch | 更像现代产品发布广告片，需要产品上架感、推进感和 CTA 动能 | `118 BPM, tight electronic drums, sidechained synth bass, bright plucked synth hook, warm chord pads, clean UI impact hits` |
| Clean UI Demo Groove | 更像高级软件 UI 演示片，需要服务界面、卡片、流程线和时间线卡点 | `112 BPM, muted kick, crisp snare snaps, syncopated digital percussion, rubbery synth bass, short glass-pluck motif` |

这两个方向已在 WorkBuddy OPC run 中验证过：

- `promo-v2-commercial-launch-01.mp4`：适合作为产品发布广告片方向的优先候选。
- `promo-v2-ui-groove-02.mp4`：适合作为真实软件 UI 演示方向的优先候选。

以后不要把这类需求先写成 `minimal / ambient / soft pulse / glass ticks`。除非用户明确要求“安静氛围”，否则第一轮 BGM 应先生成上面这组双轨。

## 当前 WorkBuddy OPC 示例模板

当视频是“WorkBuddy 专家团 - OPC·一人公司场景”，不要从 ambient pad 起步。优先从产品展示片 prompt 起步：

```text
modern commercial product launch music for a 60-second AI software showcase, 118 BPM, 4/4, instrumental only, polished, confident, forward-moving. Tight electronic drums, sidechained synth bass, bright plucked synth hook, warm chord pads, clean UI impact hits. Structure: 0-6s filtered branded intro for OPC; 6-15s groove builds under solo-founder pressure; 15-24s full product-demo beat as real WorkBuddy UI appears; 24-34s hook variation and crisp accents as expert-team cards assemble; 34-44s stronger rhythmic lift for team-lead decomposition and parallel expert work; 44-54s open uplifting section for OPC workflow timeline; 54-60s short confident resolve for “one more team.” Hit accents at 6,14,15,24,34,44,54,57.1,58.4s. No vocals, no lyrics, no sleepy ambient, no generic corporate piano, no trap hats, no EDM festival drop, no trailer booms.
```

## 生成流程

1. 读取 EDL，列出所有 shot start/end 和 transition points。
2. 建立 `energy curve`：每个镜头 1-5 强度，不要全程同一强度。
3. 选择 BPM，使主要镜头切点尽量靠近小节或半小节。
4. 写 `Primary Prompt`，必须包含动态时间段和 hit points。
5. 对照 `Mureka Prompt 质量检查`，修掉泛词、冲突词和命令句。
6. 写至少三个真正不同的备选 prompt：
   - A：commercial product launch，广告片式产品展示，有 beat 和 hook。
   - B：clean UI groove，软件界面卡点和流程推进。
   - C：founder film with momentum，一人公司情绪叙事但不能变成慢 ambient。
   - 如用户明确要更稳，可加 D：executive cinematic with beat。
7. 写 `Negative Prompt`。
8. 给出生成建议：`n=3`，优先 instrumental，生成 60-75 秒，最终按 EDL 剪到 60 秒。
9. **[PAUSE] 等用户确认音乐方向与 prompt**。

## 如果要实际生成音乐

只有当用户明确要生成音频时才执行。

1. 检查 `MUREKA_API_KEY`。
2. 如果不存在，提示用户配置后停止。
3. 如果存在，使用随本 repo `scripts/mureka.py` 提供的 Skywork Music Maker / Mureka instrumental 方式：

```bash
python scripts/mureka.py instrumental \
  --prompt "<validated English prompt>" \
  -n 3 \
  --format mp3 \
  --output assets/bgm/
```

国内站 key 需要同时设置：

```bash
export MUREKA_API_URL="https://api.mureka.cn"
```

脚本来自 Skywork Music Maker，并保留其命令结构；本 repo 只允许把 API base 改为读取 `MUREKA_API_URL`，不要把 API key 写入项目文件。
