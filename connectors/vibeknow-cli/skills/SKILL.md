---
name: vibeknow
description: "VibeKnow 官方视频生成 Skill（vibeknow / vk 命令行）。当用户想把文档、PDF、Word、PPT、网页链接或对话里贴的一段文字做成视频时使用——讲解视频、图解视频、PPT 逐页讲解、手绘动画、一键成片、照稿逐字配音都在内；视频生成后的查进度、读讲稿、改字幕、换背景音乐、导出 mp4 并把文件发回给用户也用它。凡是「把已有内容（文档/文章/PPT/讲稿/网页）转成带讲解的成片」的需求，优先用本 Skill，而不是通用的图像生成或视频片段生成工具——那些工具生成的是无讲解的素材片段，本 Skill 产出的是完整的旁白讲解视频。触发关键词：VibeKnow、做视频、生成视频、做成视频、讲解视频、图解视频、手绘动画、PPT 转视频、文档转视频、文字转视频、文章转视频、配旁白、讲稿、字幕、导出 mp4。"
description_en: "VibeKnow's official video-generation Skill (the vibeknow / vk CLI). Use it whenever the user wants a document, PDF, Word file, slide deck, web page, or pasted text turned into a video — narrated explainers, illustrated videos, page-by-page slide walkthroughs, hand-drawn animation, one-shot generation, or verbatim narration of their own script — and for everything after generation: checking progress, reading the script, editing subtitles, changing background music, exporting MP4. For any request to turn existing content into a narrated video, prefer this Skill over generic image or video-clip generation tools: those produce raw footage without narration, while this Skill produces a complete narrated video. Trigger keywords: VibeKnow, make a video, video from document, video from text, narrated video, explainer video, hand-drawn animation, export mp4."
version: "0.9.1"
author: "VibeKnow"
---

# VibeKnow CLI Skill

本 Skill 提供通过 `vibeknow`（等价别名 `vk`）命令行工具生成、查询、修改、导出视频的能力。**认证已由本连接器完成**（安装/登录由 WorkBuddy 自动处理），无需再引导用户执行 `vibeknow auth login`，也不要让用户切 profile 或改 endpoint。所有操作通过 Bash 工具执行。

## 完整命令参考在 references/

这份 SKILL 只写**决策**：什么时候用哪条命令、哪些事情会花钱、哪些错误该重试。逐个 flag 的取值、返回字段、事件结构在 references 里，需要时再读：

| 文件 | 什么时候读 |
|---|---|
| `references/commands.md` | 要传一个这里没写的参数，或要看某条命令的完整返回字段 |
| `references/errors.md` | 拿到一个这里没列出的错误码 |
| `references/events.md` | 要解析 `--output ndjson` 的事件流或 stderr 的 `vk_event=` |
| `references/recipes.md` | 要写脚本串起多条命令 |

不要凭印象编造参数——这里没写、references 里也没有的 flag，就是不存在，传了会以退出码 2 被拒。

## 生成视频

```bash
vibeknow create --from <source> [flags]
```

素材有四种给法，无需用户先建知识库：

| 用户给了什么 | 怎么传 |
|---|---|
| 拖进来一个文件 | `--from <路径>`（pdf/doc/docx/ppt/pptx/txt/md 等） |
| 一个网址 | `--from <URL>`（自动抓取入库） |
| **在对话里贴了一段文字** | `--text "<正文>"`，长文用 `--from -` 从 stdin 读 |
| 一个已存在的 `doc_id` | `--from <doc_id> --kb-id <kb>`，**必须成对** |

`doc_id` 只传一半会以退出码 2 直接被拒（后端只接受文档与其知识库成对出现）。`--kb-id` 来自 `vibeknow doc upload` 或上一次 `create` 的输出；拿不到就别复用 doc_id，重新传文件/URL 即可。

### 用户贴了一段文字

这是 WorkBuddy 里仅次于拖文件的高频输入。**不要自己 `echo > /tmp/x.md`**——多行中文过一次 shell 引号就可能被改坏，而且落库的文档名会是那个临时文件名。

```bash
# 短文本
vibeknow create --text "季度复盘要点…" --async --output json

# 长文本 / 多行：走 stdin，shell 完全不碰正文
vibeknow create --from - --async --output json <<'EOF'
第一段…
第二段…
EOF
```

文字会以首行命名成一篇文档上传，后续行为与文件完全一致。用户说"照着我这段话念"就叠 `--script-lock`。

空文本、超过 512 KB、以及 `--text` 与 `--from` 同时传，都会以退出码 2 被拒。

### 没有素材时不要硬编

用户只给了一个题目、没有任何文件/链接/正文（"做个讲量子计算的视频"）时，**如实说明需要一份素材**。

这不是 CLI 的限制，是产品目前就不支持：两条引擎在跑任何东西之前都要先取文档，取不到就整轮失败。所以**不要用 `--prompt` 顶替**（它只影响讲稿角度，不提供内容），也不要自己编一段文字塞进 `--text` 冒充用户的素材——那样出来的片子内容是你编的，用户不会知道。

### 模式选择

| 用户诉求 | `--mode` | `--engine` | 备注 |
|---|---|---|---|
| 灵活创作 / 通用讲解 | （不传，缺省） | `pipeline`（缺省） | 最常用路径 |
| 图解视频（讲稿配整页插图） | `image` | `pipeline` | 可配 `--pages`（1–20）。**页数受内容长度限制，见下方** |
| PPT / PDF 逐页讲解复刻 | `replica` | `pipeline` | 不支持 `--images`；最多约 50 页 |
| 手绘动画 | `handdraw` | `pipeline` | 独立线路，耗时较长；默认不带字幕。**中段（选风格→分镜→绘制→矢量化）后端不推事件，`--for` 会报 `past …; drawing (…)`，长时间静默属正常，不是卡死** |
| 一键成片（免费版可能不可用） | （不传） | `agent` | **死路一条，用户没有明确点名就不要选。** 见下 |

**`--engine agent` 是终点，不是起点。** 实测一条要跑十几分钟，而且生成完之后：读不了讲稿（`video script` 退出码 5，这条线路不产生分镜）、改不了讲稿、失败也不能 `resume`——唯一的"修改"方式是整片重做、重新全额计费。而缺省的 pipeline 线路上，这些全都能做。

所以只有用户**明确说了"一键成片"**时才用它。用户说"快一点""随便来一个"**不是**点名——那种情况下请照常走缺省线路。

### ⚠️ 图解视频的页数会被内容长度卡住

每页大约需要 **130 个中文字**（后端按每页 20 秒口播、中文 400 字/分钟折算），而**不传 `--pages` 时后端默认 4 页**，也就是要 ~530 字。素材不够就会在 init 阶段以退出码 2 被拒：

```
当前知识内容最多支撑1页；当前指定2页，请降低页数或补充内容
```

**这不是失败，是掏钱之前的拦截——没有扣任何积分。** 消息里已经写明了上限，照它重跑即可：

```bash
vibeknow create --from article.md --mode image --pages 1 --async --output json
```

短素材（几百字以内）想做图解视频时，**主动带上一个小的 `--pages`**，不要用默认值去撞。或者如实告诉用户内容偏短、建议补充，再让他决定。**不要反复原样重发**，也不要改用别的模式蒙混过去。

**原稿锁定是独立开关，不是一种模式**：用户说"我已经写好讲稿了，照着念就行 / 别改我的文案"时，加 `--script-lock`，它可以和上表任意一行叠加（`--mode image --script-lock` = 用用户原文当讲稿 + 逐页配图）。原文会先过一道质量预检，不通过会以退出码 2 返回明确原因，此时如实转达、引导用户改稿，**不要重试**。

> 旧写法 `--mode script` 等价于 `--script-lock`，仍可用但会打告警，新调用一律用 `--script-lock`。

### 常用参数

完整表在 `references/commands.md`。最常需要的几个：

| 参数 | 说明 |
|---|---|
| `--aspect horizontal\|vertical` | 画幅，缺省横屏 |
| `--voice` | 音色，`vibeknow voice list` 查询 |
| `--theme` | 视觉风格 ID，`vibeknow theme list --mode <模式>` 查询；必须与模式匹配，不传自动选 |
| `--language` | 成片语言（讲稿+配音），缺省跟随账号 |
| `--bgm` | 开启背景音乐 |
| `--avatar` | 数字人主讲，`vibeknow avatar list` 查询。**不支持 `--mode handdraw` 和 `--engine agent`** |
| `--preset <名字或路径>` | 一套预存的风格选项（YAML）。团队定好的固定风格用这个，别在每次调用里重敲十几个 flag。**preset 里不允许出现 `--export`/`--yes`/`--confirm`**——授权花钱的开关不能来自一个文件 |
| `--preview-dir <目录>` | 把封面/成片落到本地目录，逐个以 `resource_ready` 事件（含绝对 `local_path`）通报。`video status`/`video wait`/`video export` 也接受它 |
| `--async` | 提交后确认任务已起跑即返回 `task_id`/`session_id`，不等渲染完成。**不能与 `--export` 同用** |
| `--output text\|json\|ndjson` | 脚本化调用请显式传 `json` 或 `ndjson` |

**要把文件交给用户时用 `--preview-dir`，不要转发签名 URL。** 事件里刻意不含远端 URL——签名 URL 转发即泄露凭证。

### 示例

一律带 `--async`，然后用 `video wait --for` 分段等（原因见下一节）。

```bash
# 最简单：灵活创作
vibeknow create --from report.pdf --async --output json
# → {"task_id":42,"session_id":"s_yyy"}

# 图解视频，竖屏。8 页需要约 1000 字素材，短文请调低 --pages
vibeknow create --from https://example.com/article --mode image --pages 8 --aspect vertical --async --output json

# PPT 逐页讲解
vibeknow create --from slides.pptx --mode replica --async --output json

# 用户自带讲稿，照原文念（可叠加任意模式）
vibeknow create --from my-script.docx --script-lock --async --output json

# 用户在对话里贴的一段文字
vibeknow create --text "季度复盘要点…" --async --output json

# 同上但正文很长 / 多行
vibeknow create --from - --script-lock --async --output json <<'EOF'
第一段讲稿…
第二段讲稿…
EOF
```

`--async` 会等后端确认任务真正起跑（秒级）再返回，不是立刻返回。参数不合法、积分不足这类当场被拒的情况它会自己报错并非 0 退出，所以**只要拿到了 task_id，任务就是真的在跑**，可以直接进入等待。

## ⚠️ 提交 + 分段等待，不要阻塞到底

视频生成通常几十秒到数分钟，而**你的 Bash 工具默认 2 分钟就会超时**（上限 10 分钟）。裸 `video wait` 会一直等到终态，必然被掐断——任务其实还在服务端跑，而你看到的是一次"失败"。

**标准循环是这样：**

```bash
# 1) 提交，秒级返回
vibeknow create --from report.pdf --async --output json
# → {"task_id":42,"session_id":"s_yyy"}

# 2) 分段等，每段 90 秒
vibeknow video wait 42 --session-id s_yyy --for 90s --output json
```

`--for` 让每次调用都在你的超时之内回来，并**带回当前进度**：

- **退出码 6 + `reason: "wait_budget_expired"`** = 预算到了，任务好好的。stderr 的 `detail` 里有 `stage`（当前阶段）和 `waited_ms`。**把 stage 告诉用户，然后照 `next_actions` 再跑一次。**
- **退出码 0** = 真的完成了，stdout 就是结果快照。
- 其它退出码按下方总表处理。

**不要用 `video status` 代替它做轮询。** 生成阶段 status 只有一个 `preview.ready` 布尔，拿不到任何进度——每 10 秒问一次，你每次只能对用户重复同一句"还在生成"。进度在事件流里，只有 `--for` 拿得到。

**重复调用 `--for` 不花钱、不丢东西**：任务归后端所有，不属于监视它的那个进程。**预算用完绝对不要改用 `create` 重来**——那是第二次全额扣费。

`stage` 有四种形态，都不是故障：

| 形态 | 含义 |
|---|---|
| `outline / script_writing` | 正在这个节点里 |
| `past script_writing` | 这个节点做完了，之后还没有新消息 |
| `past …; drawing (…)` | 手绘线路的中段静默，属正常且会持续几分钟 |
| `no stage reported yet` | 刚起跑的头几秒 |

**它们都不代表任务健康——静默两边都不能证明。** 它们排除的是那个会花钱的误判：以为安静的任务已经死了，于是重新 `create`。

**连续两轮 stage 一样是正常的**，慢的线路上很常见：一个步骤可能跨好几个预算窗口。不要因此缩短 `--for`、加快轮询，更不要重开。对用户如实说"还在这一步"即可。

各模式实际会报的节点（已逐一实测）：

| 模式 | 会看到 |
|---|---|
| 缺省 / `--script-lock` | `big_director` `script_writing` `storyboard_plan` `tts_generate` `scene_filling` `bg_images` `cover` `bgm` `video_package` |
| `--mode image` | `style_select` `image_storyboard` `image_gen`，外加 `script_writing` `tts_generate` `bgm` `video_package` |
| `--mode replica` | `doc_dissect` `doc_replica_plan` `doc_replica_shoot`，外加 `tts_generate` `bgm` `video_package` |
| `--mode handdraw` | **只有** `script_writing` `tts_generate` `bgm` `video_package`；中段（选风格→分镜→绘制→矢量化）什么都不发，而时间主要花在那里 |
| `--engine agent` | 没有节点名，只有自由文本进度 |

### 命令被超时掐断了怎么办

**先查本机账本，绝对不要重跑 `create`——重跑就是再扣一次积分。** CLI 在任务**起跑之前**就把 `(task_id, session_id)` 写进了本地账本，正是为了这一刻：

```bash
vibeknow jobs list --active --output json      # 还没跑完的任务
vibeknow jobs get <task_id> --output json      # 看单个任务
vibeknow video status <task_id> --session-id <sid> --output json
```

`--session-id` 是可选的：`create` 记过的任务能自动接上（`vibeknow video wait` 不带参数会接最近一次）。**手上还有 ID 就显式传，最稳**；只有上下文丢了才依赖本机记录。

同一个 `task_id` 上永远不要重复调用 `create`。

## 在对话里交付结果

生成完成后，用户手上应该有**能看的东西**，而不是一条要点开浏览器的链接。

```bash
vibeknow video status 42 --session-id s_yyy --preview-dir ./out --output json
```

`--preview-dir` 会把这个作品当前有的产物落到本地，每个以 `resource_ready` 事件（含绝对 `local_path`）通报。**WorkBuddy 能直接内联展示本地图片和视频**，所以把 `local_path` 交给用户，别转发链接。

一次交付里值得给全的四样：**封面图（本地文件）+ 标题 + 时长 + 分享链接**，前三样都在这条命令的返回里。

⚠️ **预览阶段落地的只有封面**。成片 mp4 要 `video export` 之后才存在（计费，见下方"下载 / 导出 / 分享"）。如果用户要的是"发我一个视频文件"，如实说明这一步要花积分并走确认流程，不要拿封面充数。

**永远不要转发签名 URL。** 事件里刻意不含远端 URL——签名 URL 转发即泄露凭证。

`status --preview-dir` 对**不是你起的那个任务**同样有效（用户换了话题又回来、或你的上下文丢过），这是重新拿到产物的唯一途径。生成中调用它不会落任何文件、也不花钱。

## 读作品内容（讲稿 / 分镜）

```bash
vibeknow video script <task_id> --session-id <sid> --output json
```

用户问"这个视频讲了什么""稿子给我看看""一共几幕""第 3 幕多长""字幕文件呢"——都用这条。**只读、免费、不重跑任何东西**，可以随对话反复调用。

返回 `script`（整篇讲稿）、`scenes[]`（逐幕的 `scene_index`/`script_text`/`duration_sec`/`layout_type`/`status`，以及该幕的 `tts_url`/`srt_url`/`bg_image_url`）、`scene_count`、`duration_sec`。字段细节见 `references/commands.md`。

**没有分镜时不会返回空结果，而是非 0 退出**，退出码告诉你等下去有没有意义：

| 退出码 | 原因 | 怎么办 |
|---|---|---|
| 6 | **还**没有分镜，通常在生成中 | 先 `video status` 看进度，之后再读 |
| 5 | 作品是 `--engine agent`（一键成片）做的，那条线路不产生分镜 | **永远读不到**，如实告诉用户，不要重试 |
| 5 | 任务失败或已删除，根本没跑到出分镜那一步 | 看 `video status`，失败的可以试 `video resume` |

区别很重要：退出码 6 的意思是"待会儿再来"，而两个 5 都是"没有可等的东西"。

**先跑这条，再跑 `video edit`**：`--scene` 用的就是它打印的幕号。

## 改视频：三档，代价不同

用户看完稿子提的要求要分三类，代价差得很远，别混为一谈。

### ① 呈现——免费、即时、不重跑

```bash
vibeknow video set <task_id> --session-id <sid> --bgm off --output json
vibeknow video set <task_id> --session-id <sid> --subtitle-preset 2 --subtitle-size 52 --output json
vibeknow video set <task_id> --session-id <sid> --title "季度复盘" --output json
```

覆盖：背景音乐开关与音量、字幕开关与样式、标题。一条命令可以同时改多项，**没传的字段不会被动到**。

**字幕优先用 `--subtitle-preset`，不要手搓单项。** 可读性是一组配合而不是几个独立设置——描边款会同时清掉底板、底板款会同时关掉描边。手拼很容易只对一半，而**只对一半也会退出 0**：wire 上没有任何东西是错的，只是视频难看。`vibeknow subtitle presets` 列出十一种现成的；`vibeknow subtitle fonts` 列出后端允许的字体（`#` 和字体全名都能传）。preset 只覆盖构成这个"look"的字段，所以 `--subtitle-preset 2 --subtitle-size 52` = "那个样式，但字大一点"。

> ⚠️ **除 `--title` 外，每一项都会作废已导出的 mp4**——改动要重新烘焙进文件。预览和分享链接照常可用，只有下载没了，要重新 `video export`（计费、走退出码 8）。响应里的 `export_invalidated` 就是这件事，为 `true` 时**必须主动告诉用户**，否则他改完音乐、过一会儿发现下载不了，完全无从联系到自己刚才那句话。

退出码 **5** 表示这个作品做不到（该引擎不支持调音量、渲染器不支持字幕样式等），不要换个值重试，如实说明。

### ② 讲稿文字——计费、要用户确认、有整幕重生成

```bash
vibeknow video script <task_id> --session-id <sid> --output json     # 先看幕号
vibeknow video edit <task_id> --session-id <sid> --scene 3 --script "新的这一幕要说的话" --output json
```

改**一幕**的旁白并重新生成那一幕。`--script-only` 只重做配音，不动版式和背景图（更便宜）；缺省会一并重做，改写长度变化明显时需要这个，否则版面不会重新排。

**这会花钱**，所以走和导出同一套确认闸门（`scene_edit_confirmation`）：无终端时以**退出码 8** 返回 `{"status":"blocked","pending_actions":[…]}`，payload 里**同时带 `from` 和 `to`**——用户批准的是一个 diff，只给他看替换后的文本等于让他同意一个看不见的改动。把两边都转达，等明确同意，再**原样执行** `resume_command`。

三件事必须知道：

- **不报具体积分数。** 花多少取决于模型写多长、配音跑多久，后端事前不给数——填一个编出来的数字会毁掉这道闸门唯一的依据。提示里说明的是"会产生哪几类计费工作"。
- **已渲染的 mp4 不会被撤下。** 后端保留原文件，所以 `video download` 会继续返回**改之前**那一版的视频，直到重新导出。响应里以 `export_stale` 露出，`next_actions` 会给重新导出的命令。这一条要主动讲。
- **没有撤销。** 后端只保留用于自救的回滚快照，不对外提供"退回上一版"。

四种情况在本地就被拒（不发请求、不计费，**`--yes` 也不能绕过**）：幕号超出范围（错误里会写范围）、新旧文本完全相同、空文本、漏传 `--scene` 或 `--script`。

退出码 **4**（`work_edit_busy`）是同一作品上有另一个编辑在跑，等几秒重发即可；退出码 **5** 是 `insufficient_credits` 一类，不要重试。

### ③ 画面与版式——目前没有命令

换图、换版式、换封面、加水印/logo、换背景音乐文件——**当前没有任何命令能做到**。用户提这类需求时**不要编命令**，如实说明现在只能调整输入后重新 `create`（会重新计费），或者到网页端处理。

## 停止 / 继续

```bash
vibeknow video pause  <task_id> --session-id <sid> --output json
vibeknow video resume <task_id> --session-id <sid> --output json
```

**起错了就赶紧 `pause`。** 用户说"不对，我要的不是这个文档""换成竖屏"时，正在跑的那一条不会自己停——不停就是让用户为一个没人要的视频付费。已完成的部分会保留，`resume` 从那里接着跑。

**任务失败时优先 `resume`，而不是重新 `create`。** 对失败任务 `resume` 是"从最后一个检查点重试"，后端复用原账单；重新 `create` 是整片重做，等于第二次全额扣费。返回的 `mode` 字段告诉你发生了哪一种（`paused_resume` / `failed_checkpoint_retry`）。

**三种拒绝是永久的**（退出码 5），不要重试，如实告诉用户：任务用的是 `--engine agent`（这条线路没有检查点）、任务被内容风控拦下、任务状态既不是"已暂停"也不是"已失败"。退出码 **4**（`session busy`）是唯一值得重试的。

## 下载 / 导出 / 分享

```bash
vibeknow video download <task_id> --session-id <sid> --dest ./video.mp4     # 下载已渲染的 mp4
vibeknow video export   <task_id> --session-id <sid> --output json          # 触发/等待整片导出
vibeknow video export-status <export_task_id> --session-id <sid> --output json
vibeknow video url <work_id> --output json                                  # 取可播放链接
vibeknow video list --output json                                           # 列出历史作品
```

**预览与导出是两个阶段**：`create`/`video wait` 成功后拿到的是可播放预览（分享链接即可用），尚未生成 mp4；需要下载 mp4 文件时才调用 `video export`。**只需要分享链接时不要顺带触发导出**，会多花积分和几分钟等待。

**导出要花积分，无终端时 CLI 不会替用户做决定**：`video export`（以及 `create --export`）在非交互环境下以**退出码 8** 返回一个 `{"status":"blocked","pending_actions":[…]}` 信封，内含费用说明和一条 `resume_command`。此时：①把 `message` 和 `payload`（费用）如实转达；②等用户明确同意；③同意后**原样执行** `resume_command`（含 `--confirm act_…`）；拒绝则什么都不跑。

**不要自己编 `--confirm` 值，也不要擅自加 `--yes`**——只有用户事先明确授权过这笔花费才可用 `--yes`。`--confirm` 被拒（退出码 2）说明条件已变化：去掉 `--confirm` 重跑拿到新条款，再问一次用户。

## 查询音色 / 主题 / 数字人

```bash
vibeknow voice list --output json                    # 公模按语言分组 + 克隆音色
vibeknow theme list --mode image --output json       # 某模式的风格目录，ID 传给 create --theme
vibeknow avatar list --output json                   # 数字人：public（公模，含配套 voice_id）+ mine
vibeknow subtitle presets --output json              # 十一种现成字幕样式
vibeknow subtitle fonts --output json                # 后端允许的字体
```

公模数字人条目自带 `voice_id`（该形象演示用的音色）——选了数字人就把它传给 `--voice`，避免人像与声音性别错配。

**数字人作品的导出门槛**：`video export` 在任一幕数字人还在生成或已失败时会被后端拒绝。失败幕是终态，不重试就永远导不出——此时执行 `vibeknow video avatar-retry <task_id> --session-id <sid>`（只重跑失败幕，不重复扣费），等它完成再 `video export`。`retry_count` 为 0 说明没有失败幕，导出仍被拒就是还有幕在生成中，等待即可、不要反复 retry。

## 退出码处理

| 退出码 | 含义 | Agent 该怎么做 |
|---|---|---|
| 0 | 成功 | 从输出提取结果（`video_url`/`task_id` 等） |
| 1 | 通用错误 | 读 stderr 具体信息 |
| 2 | 参数非法 | 修正后重试，**不要原样重发**。涵盖：未知子命令、拼错/不存在的 flag、缺必填 flag、多余位置参数、枚举值非法。stderr 会列出合法取值；flag 拼错时还会提示最接近的那个 |
| 3 | 认证错误（凭据缺失/过期/被顶号）——**所有命令**都会这样退出 | 正常情况不该出现（连接器已代管认证）；如出现，提示用户在 WorkBuddy 里重新连接本 Connector |
| 4 | 可重试：限流、服务端错误、并发达上限、`work_edit_busy`、`session busy` | 等待后用相同参数重发同一条命令 |
| 5 | 任务失败或**状态不允许**，不可重试 | 如实告知失败原因。也涵盖"额度用尽"一类：积分不足、项目数达上限、试听配额用完——请求本身没错，重发只会再失败一次，要做的是把"用完的是什么"讲清楚 |
| 6 | **未到终态**，三种情况，先看 stderr `detail.reason` | 一律**不要**重新 `create`。`wait_budget_expired` = `--for` 预算到了、任务正常，报出 `stage` 后照 `next_actions` 再等一轮；无 reason 的流中断按 `resend_safe` 判断；任务被暂停用 `video resume` |
| 7 | **部分成功**：预览已生成，但 mp4 导出失败 | 把预览分享链接如实交付；只重试 `video export`，不要重新 `create` |
| 8 | **卡在只有用户能做的决定上**（付费导出确认、改稿确认） | 停下来。把 stdout 里 `pending_actions` 的说明转达用户，等答复后原样执行 `resume_command` |
| 130 | 用户中断 | — |

完整错误码表见 `references/errors.md`。

## 输出格式说明

- 未传 `--output` 时默认纯文本人类可读格式，**不要依赖它做解析**。CLI **不会**因为管道/非 TTY 就自动切 JSON，必须显式传。
- 脚本化调用一律显式传 `--output json`（单次快照）或 `--output ndjson`（`create`/`wait` 的流式进度，每行一个 JSON 事件，终态事件为 `task.succeeded`/`task.failed`）。
- 传了不认识的格式（如 `--output jsonl`）会以退出码 2 报错，不会静默退回纯文本。
- **每一个子命令都支持 `--output json`**，包括 `doc upload`、`credits balance`、`voice list`、`jobs *`、`doctor`、`version`、`auth whoami`。
- stdout 只放结果数据，进度/提示/告警一律在 stderr，所以 `... --output json | jq` 是安全的。
- **`--output json` 时 stderr 会同时输出 `vk_event={...}` 结构化进度行**（与 ndjson 事件同构）。`VIBEKNOW_EVENTS=1`/`0` 可强制开/关。**不要 `2>&1` 合并两个流**——stdout 是结果、stderr 是过程，合并会破坏可解析性。
- 带 `--preview-dir` 时，stderr 事件流里会出现 `resource_ready`（含绝对 `local_path`，文件已完整落盘）——把这个本地文件交给用户。`resource_preview_warning` 表示某个产物没拿到，**不代表任务失败**。

事件结构详见 `references/events.md`。
