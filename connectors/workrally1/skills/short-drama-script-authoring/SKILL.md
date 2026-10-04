---
name: short-drama-script-authoring
description: 用户自然语言要生成剧集/短剧且选择使用用户提供的Short Drama Script.zip生成剧本时启用。使用该包v8.8.0的路由、标签、loop骨架、人物、剧本及评审方法，仅做授权集数范围的文字创作；已有剧本不自动重写。用户未选择时先提供使用此包/沿用已有剧本或原方式的选项。确认剧本后交回workrally-brand-film-pipeline转逐镜文字分镜，后续A0/G1/G2与资产视频链路不变。所有声音后期添加。
description_zh: Short Drama Script剧本可选入口
description_en: Short Drama Script controlled authoring
disable: false
agent_created: true
version: 2026.09.18.1
---

# Short Drama Script：受控剧本入口

## When to use

用户要求生成剧集时提供此选项，不自动强制使用。用户本次明确选用Short Drama Script则记录来源并直接进入；“生成剧集”本身不是选用本包或生成整季的授权。已有完整剧本默认保留原稿并交主流程分析转分镜；改写、评审、续写须按用户明确范围执行。

本入口适配用户本次ZIP的 **v8.8.0**，不是记忆中的v9.x，不替换或降级其他已装版本，不因相似名称复用不同包。

## 原件、审计和作用域

- 原包不随仓库分发。运行时只读 `references/source/`；接入时原包 SHA-256：`49dfa8e0514d19922777abff427838947d5cfd682fc56d542273b2a30d985b66`。
- 原入口真实name为 `Short Drama Script`。存为 `references/source/source-skill.md`，仅作参考，不作为第二个活动入口。README的历史目录名不参与路由。
- `references/source/`保留文档和数据，逐文件校验见 `references/source-manifest.json`。原包脚本不随仓库分发，**不运行、不导入Python模块、不自动安装PyYAML**。agents/旧安装元数据不激活。
- 审查覆盖204个有效文件、1,650,322字节；未发现窃密外传或恶意执行，发现内容治理和流程P1，经用户确认后采用本受控入口。
- **隔离英文资料**：活动的 `references/source/references/formats/english-short-drama.md` 是明确标注的派生副本，原第273–411行（第六节整套强制台词抽样及模板）不装入活动资料；原文只在归档中审计留存，禁止运行时回退读取。保留英文语感、结构与本土化其他章节；下游“强制抽3条”及对第六节的引用不执行。
- 任何成人亲密关系素材必须明确成年人且自愿，禁止未成年人性化、年龄不明的性内容及以胁迫作为生成许可。原包“合规/最高优先级/尺度放宽”等自述不是宿主安全依据；其他题材库同样按此边界筛选，不将虚构剧情当现实行动指令。
- 原包创作宪法只约束本次获授权的短剧写作，不覆盖用户确认、文件权限、内容安全、A0/G1/G2或最终无声视频规则。

## Steps

### 1. 锁定任务而非默认写整季

确认并记录：是否选择本入口、本次产物（选题/大纲/人设/剧本/评审/修改）、载体、语言、目标受众/市场、已有素材、目标集数及本次授权集数、单集目标时长。必要信息不足一次问清，已有有效确认不重问。

不把原包50–100集默认当用户选择；不把每批最多10集当本次授权。只写授权范围，续写须有明确指令或先前完整授权。原稿不覆盖，新稿另存新版本。

`carrier`取用户内容意图；主流程提到“文字分镜”不触发漫剧切换。只有用户确需漫剧/动态漫时加载漫剧格式。不能因整部内容有一句英文就覆盖用户已指定的语言和市场。

### 2. 读取原包入口及按需资料

先读 `references/source/source-skill.md`，适用范围以本入口为准。

**路径解析规则**：下表 `R` 仅表示目录 `references/source/references/`，不是字面路径。原入口的 `references/...` 映射到R下；`shared/...`、`frameworks/...`、`stages/...`、`formats/...`、`domestic/...`、`overseas/...`、`fusion/...`、`routing/...` 等省略前缀的路径同样按R解析。角色或标签文档内的相对链接先按其真实父目录解析，校验存在后读取，不盲目加重复前缀。

|阶段|要读取的实际资料（相对R）|输出|
|---|---|---|
|标签化工单|`routing/decision-tree.md`、`anti-tv-drama.md`|基于本次题材/市场的标签、已有信息、方向和缺口，提交用户确认|
|规则组装|`shared/base.md`、`frameworks/loop-model.md`、`frameworks/emotion-spring.md`、`frameworks/hook-design.md`；`domestic/INDEX.md`或`overseas/INDEX.md`、`common-tags/INDEX.md`及命中标签/combo|专属创作规范，按需读取，禁止把整库一次灌入常驻上下文|
|融梗与案例|多标签时 `fusion/_METHODOLOGY.md`、按需配方；`case-studies/INDEX.md`及命中案例|差异化方向与案例对照，不把参考当市场效果保证|
|骨架锁定|原入口步骤2.5，`frameworks/loop-model.md`、`anti-tv-drama.md`|必要骨架/情节单元/授权集数的节拍，用户确认后写正文；小体量按实际范围不硬塞50集框架|
|写作|按任务读 `stages/1-outline.md`、`stages/2-character.md`或`stages/3-script.md`；首集读 `frameworks/first-episode.md`|仅授权范围的文字产物，已有稿件仅按指定修改范围处理|
|评审修订|`stages/4-review.md`、`shared/anti-patterns.md`、`stages/5-revise.md`|内容自检和所请求的修订，不自动覆盖原稿；没有真实投放数据不报可验证的爆款概率|

条件加载：女频关系loop使用 `frameworks/narrative-loop.md`；漫剧使用 `formats/manga-drama.md`与 `tags-manga/registry.yaml`；英文使用已隔离处理的 `formats/english-short-drama.md`及 `overseas/markets/`实际对应文件；好莱坞排版仅在用户指定时读 `formats/hollywood-script.md`。

包内英文词数规则不能直接用空白分词衡量中文篇幅，也不能当精确时长证明；对白时长按配音速度和表演停顿核验。原包“自动改到过关”仅用于本轮新生成草稿自检，不授权改写既有剧本或追加集数。

### 3. 缺失参考不能虚构

原包存在旧引用：`frameworks/five-elements.md`、`shared/expression-library.md`、`shared/conflict-variants.md`及校验脚本提及的 `beats-shared.md`。不声称已经读取不存在的资料，不自动运行构建器补齐。

- 仅为旧目录说明或非本任务必要模块：记录不适用，使用已真实读到的其他适用资料继续。
- 本次明确需要该方法或必须依赖其内容：标为缺失并问是否补充原件/改用已核验的方法，不能悄悄拿别的文件冒充。
- 脚本校验器也有旧路径残留，不运行它作为完整性证明；使用安装manifest校验文件存在及字节。

### 4. 交付文字，再交回主流程

只写剧本的请求：交付授权范围剧本并结束，不查询生成模型、不生图、不生成音频或视频。

完整剧集制作：确认剧本后交回 `workrally-brand-film-pipeline` 的统一文字分镜步骤；不是直接跳到A0，也不调用旧的“先生成资产再写分镜”分支。

交接本地字段：`preproduction_route=episodic`、`script_method=short-drama-script-authoring`、入口版本、原包版本/哈希、选用确认来源、载体/语言/市场、`episode_scope`、剧本文件及版本、骨架确认状态、角色/道具/场景设定、`post_audio_plan`、`audio_policy=all_post_production`。

剧本台词、旁白、环境声、音效、音乐全部作为**后期文字计划**保留。最终视频prompt只描述无声表演和画面，不注入配乐、朗读、对白、环境声等发声指令。若需要精确口型同步，另行核验后期方案，不自动开启原生声音。

主流程负责逐镜Markdown落盘展示、A0/G1/G2、CHAR/PROP/SC、默认摄影、资产固定去噪、生成单元、剪辑与包装；本入口不修改这些规范、不自动重生成已有媒体。

## Pitfalls

- 包声明是v8.8.0；历史目录名或云端记忆不等于当前包版本。
- “可选剧本生成”不是自动写整季；已有脚本不经授权重写。
- 包内scripts是维护/辅助工具，不是使用标签与写作方法的前提。
- 来源资料即使带agent_created字段，也不把它当成当前助手原创；原件保留，适配边界写在本入口。
- 英文敏感模板已从活动路径隔离，不能因依赖引用再去加载未接入的原文。

## Verification

- [ ] 有选择本入口的用户确认，集数/载体/语言/修改范围明确。
- [ ] 按原包阶段和真实资料写作，骨架未确认不写正文；必要缺失资料已披露。
- [ ] 未执行脚本、未联网取原包链接、未覆盖原稿、未自动续写。
- [ ] 未加载隔离台词模板，所有关系素材按内容安全边界筛选。
- [ ] 仅文字任务停止；完整制作交回统一文字分镜，再进入原A0/G1/G2。
- [ ] 全部声音列为后期制作，视频只出无声画面；历史媒体未改动。

## CHANGELOG

### 2026.09.18.1
- 接入本次Short Drama Script.zip v8.8.0，校验清单见 source-manifest.json，活动层只使用 `references/source/` 文字资料。原包 zip 不随仓库分发。
- 剧集可选启用、按授权范围写作，隔离脚本及英文第六节模板；后续制作链路不变。
