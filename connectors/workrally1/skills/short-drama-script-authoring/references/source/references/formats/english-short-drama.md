<!-- 受控派生文本 2026.09.18.1；仅替换原包第273–411行，原包未改。 -->
# 英文短剧创作圣经（English Vertical Short Drama Bible）

> **本文件是写任何英文/海外短剧的最高优先级语感文件，必读，先于一切其它创作。**
>
> **为什么必须读这个**：模型的英文剧本肌肉记忆 = 好莱坞编剧教材（HBO/Netflix/电影长片）= 慢热、心理深度、留白、克制、政治正确、逻辑自洽。而英文短剧（海外 / DramaBox / GoodShort / ShortMax）是**完全不同的物种**——它是「视频版英文爽文」，狗血、直给、每集反转、脸谱反派被打脸。如果不先建立英文短剧的语感关键节点，模型会自动把短剧写成美剧。**这个文件就是用来对冲好莱坞惯性的参照系。**

---

## 一、一句话本质：英文短剧 = 视频版英文爽文，不是低配美剧

记住这个等式：

```
海外 英文短剧  ≈  中文国内短剧 换一张英文脸
                    ≠  缩短版 HBO / Netflix 剧
```

中文短剧和英文短剧是**同一个物种**（强情绪、强反转、每集爽点、脸谱反派、即时满足），只是：
- 人名换成 Western 名字
- 场景换成美国都市/小镇
- 文化逻辑换成西方（个人主义、约会文化、狼人/吸血鬼等本土幻想 IP）

**骨架（爽感内核）不变，只换皮。** 你已经会写中文短剧了——写英文短剧就是把那套爽感公式，用地道英文台词和西方设定重新演一遍。**不要因为换成英文就切换到"好莱坞高级模式"。**

---

## 一点五、英文单集篇幅规格（v7.0 新增 · v8.8.0 修订 · 篇幅关键节点 · DRY 引用 base.md）

> **本节是英文项目篇幅的唯一执行口径。** 篇幅真相源在 `shared/base.md` 篇幅红线，本节只引用不复制。

英文短剧篇幅一律以英文词数（words）为口径衡量。**skill 里不再存在任何中文字数（字）口径**——历史上模型把中文"700-800 字"误读成"700-800 words"，产出约合 4-5 分钟朗读的超长单集，远超 1-2 分钟时长约束（这曾是英文剧本过长的头号原因）。现已彻底删除中文字数口径，只留英文词数，从源头杜绝误读。

| 项目 | **篇幅规格（英文词数口径）** | 时长 |
|---|---|---|
| 每集（v8.8.0 修订） | **200-448 词**（目标 320 词） | 1-2 分钟 |

**节拍类型篇幅下限（防偷懒护栏）**：
- **转集 / 合集**（放弹簧 + 收口）：≥ 300 词
- **起集 / 承集**（只压不放）：≥ 200 词
- 起/承集的"短"是允许写短戏（用微表情/压抑动作/未说出口的潜台词外化填满），**不是允许写水戏**

**换算依据（对应完整 1-2 分钟时长区间）**：
- 英文朗读约 150-160 wpm；1 分钟纯台词 = 150-160 词，2 分钟 = 300-320 词
- 加动作描写/场景头（约占 30-40%），总 word count：1 分钟 ≈ 195-224 词，2 分钟 ≈ 390-448 词
- **取整 200-448 词，严格对齐 1-2 分钟时长**，1 分钟短集（200-292 词）合法不得砍掉

**自检口诀**：写完一集英文剧本，用 `wc -w` 数词数。
- 转集/合集 < 300 词、起/承集 < 200 词 = 不合格必须补写
- 任何集 > 448 词 = **超标超时**（>2 分钟），说明在写美剧不是短剧，必须删减到时长内

> **为什么只留英文词数**：模型历史上把 skill 里的中文"字数"默认理解成"words"，而英文同数值的词数是中文信息量的约 2 倍体量。彻底删中文字数、全 skill 只按 word count 衡量，就是把这条隐性 bug 从源头钉死。
>
> **为什么下限放到 200**：按"1-2 分钟"完整区间反推，1 分钟短集（节奏快的转/合后过渡、起集压弹簧）合法存在；下限放到 200，但用节拍类型护栏卡住偷懒——不是允许写水戏，是允许"压弹簧的短戏"存在。

---

## 二、致命对照：英文短剧 vs 好莱坞剧本（模型最容易跑偏的 8 个点）

| 维度 | ❌ 好莱坞惯性（模型默认会这样写） | ✅ 英文短剧正确写法 |
|---|---|---|
| **开篇** | 空镜+人物介绍+日常铺陈，40秒后才有矛盾 | **第1个镜头就是爆点**：被甩/被打/撞见出轨/当众羞辱 |
| **节奏单位** | 一集铺垫一个主题，慢慢渗透 | **每集1-2个反转/爽点**，钩子密度极高 |
| **情绪** | 内敛、克制、留白、潜台词 | **直给、外放、说出来**——情绪写在脸上和台词里 |
| **反派** | 立体、有自洽动机、"没有纯粹的坏人" | **脸谱化、欠揍、嚣张**——观众就是要看 ta 被打脸 |
| **巧合/外力** | 避免巧合，靠人物选择驱动 | **拥抱巧合和狗血**：刚好撞见、刚好是隐藏富豪、刚好怀孕 |
| **主角** | 灰色、复杂、有缺陷的反英雄 | **清晰的受害者→逆袭者**，观众能秒代入 |
| **台词** | 简练、有潜台词、话里有话 | **功能性、信息前置、情绪直白**，一句顶一句 |
| **结局节奏** | 开放式、留余味、道德模糊 | **爽到底**：打脸打透、真相揭穿、坏人付出代价 |

> **核心心法**：每次写英文短剧台词或动作前，自问一句——
> **"这句话是写给奥斯卡评委看的，还是写给一个边滑手机边看竖屏的观众看的？"**
> 凡是显得"高级、文艺、克制、有深度"的，多半跑偏了。短剧要的是**爽、快、直、勾人**。

---

## 三、英文短剧的腔调铁律（Voice & Tone）

英文短剧有自己的"腔",和好莱坞剧本的腔完全不同。下面是可操作的语言规则：

### 1. 台词短、口语、直给
- ✅ `"You think I need you? Watch me."`（短促、有力、情绪直给）
- ✅ `"Sign the papers, Daniel. We're done."`
- ❌ `"I've spent a long time wondering whether any of this was ever real."`（太文学、太内省）

### 2. 情绪外放,说出来,不藏
英文短剧的人物**把情绪直接喊出来**,不靠潜台词。愤怒就是愤怒,鄙视就是鄙视。
- ✅ `"You humiliated me in front of everyone. Now it's my turn."`
- ❌ （沉默，她转身离开，没有再说一句话。）← 这是好莱坞的留白，短剧不要

### 3. 信息前置:第一句台词就交代身份/冲突/目标
- ✅ `"Five years of marriage, and you're leaving me for my own sister?"`（一句话交代：婚姻、背叛、对象）
- ❌ 用三场戏慢慢揭示婚姻出了问题

### 4. 动作可拍、外化,禁止心理旁白
英文短剧和中文短剧一样,**只写镜头能拍到的**。模型写英文时尤其容易飙文学性心理描写,必须掐死。
- ❌ `Something in her eyes shifted — a quiet, dangerous resolve forming beneath the surface.`（拍不出来）
- ✅ `She wipes her tears, picks up the divorce papers, and signs them without blinking.`（能拍）

### 5. 反派台词要"欠揍",主角打脸台词要"解气"
- 反派（欠揍）：`"A nobody like you? You'll come crawling back in a week."`
- 主角（打脸）：`"A week? I just bought the company that fired you. You're the one crawling."`

### 6. 善用英文短剧高频"爽句式"（见第六节台词库）

---

## 四、真实风格范例（带逐句标注「为什么这是短剧不是美剧」）

> ⚠️ 以下范例是**风格关键节点**,展示英文短剧该有的腔调、节奏、钩子密度。不是让你照抄剧情,是让你"听见"英文短剧的声音。

### 范例 A：首集开篇黄金 3-10 秒（霸总/契约赛道）

```
EPISODE 1 — THE WRONG BRIDE

INT. ST. AGNES CHURCH - DAY

Wedding music. EMMA CARTER (25), in a borrowed wedding dress, stands at the altar.

The groom, RYAN, doesn't look at her. He's staring at the doors.

RYAN: (to the priest) Stop. This isn't right.

The doors burst open. A woman in red — Emma's stepsister, CHLOE — strides in.

CHLOE: (smirking) Sorry I'm late. Did I miss my own wedding?

EMMA: Your wedding?

RYAN: (taking off Emma's ring) It was always going to be Chloe. You were just... insurance.

He drops the ring on the floor. The whole church laughs.

EMMA picks up the ring. Her hand shakes — then steadies.

EMMA: (quiet, to herself) Insurance. Fine. Then I'll cash myself out.

Her phone BUZZES. Unknown number. She answers.

VOICE (V.O.): Miss Carter. Your grandfather left you everything. The Carter Group is yours.

CHLOE's smirk freezes. Ryan turns around slowly.
```

> 🔴 **结尾转场词铁律（v6.9 新增）**：**不要在每集结尾用 `CUT TO BLACK.` / `END OF EPISODE X.` 之类的转场词**。这些是好莱坞剧本的肌肉记忆，**不是英文短剧的格式要求**。本节范例 A/C 早期版本用过它们，已删除——保留这种转场会训练模型把"每集切黑"当成格式硬性规定，反而消解了悬念的冲击力。
>
> 正确收尾：让最后一行**角色动作/表情/台词**停在最爽的钩子上，**让观众自己滑入下一集**。比如范例 A 的 `CHLOE's smirk freezes. Ryan turns around slowly.` 已经是一个完整的强钩子，不需要再补转场词；范例 C 的 `EMMA's eyes widen.` 同样收住悬念。**强收尾靠钩子内容本身，不靠转场词。**

**逐句标注（为什么是短剧）**：
- **0-3秒**：婚礼上新郎当众悔婚 → 强冲突爆点,不是空镜介绍
- **"You were just insurance"**：反派台词欠揍、羞辱直给,不留情面
- **全教堂大笑**：公开羞辱,把屈辱感拉满（压弹簧）
- **捡起戒指、手抖→稳住**：情绪外化成可拍动作,不写心理
- **"I'll cash myself out"**：主角觉醒台词,短促有力
- **电话:你继承了整个集团**：狗血巧合 + 身份反转钩子,10秒内抛出主角的逆袭赌注
- **反派笑容凝固**：结尾钩子,下一集要看打脸
- 全程**没有一句心理旁白、没有留白、没有"高级感"**——纯爽点驱动

### 范例 B：爽点释放/打脸（复仇/逆袭赛道）

```
INT. CARTER GROUP - BOARDROOM - DAY

CHLOE storms in, expecting to take over.

CHLOE: Where's the CEO? I'm the new majority shareholder and—

The chair turns around. It's EMMA.

CHLOE: ...You?

EMMA: (calm) Me. I bought your shares this morning. Through three shell companies. You sold them to me for coffee money.

CHLOE: That's impossible! You're broke!

EMMA: (sliding a document across the table) Was. Past tense. Security?

Two guards step forward.

EMMA: Miss Carter no longer works here. Walk her out.

CHLOE: (grabbing the table) You can't do this to me! Ryan! RYAN!

EMMA: Ryan signed his resignation an hour ago. (beat) He works for me now too.

Chloe's legs give out. She drops into a chair, white as a sheet.

EMMA: (leaning in) That ring you laughed at? It's the only thing you'll be leaving with.
```

**逐句标注**：
- **椅子转过来是 Emma**：经典短剧反转镜头语言
- **"You sold them to me for coffee money"**：打脸台词,把反派的愚蠢钉死,解气
- **保安架走 + 反派腿软瘫坐**：打脸反应身体化（和中文短剧"腿软/瘫坐"完全一致）
- **"Ryan works for me now too"**：连环打脸,爽点叠加
- 反派**脸谱化地嚣张又愚蠢**——这是特征不是缺点,观众要的就是看 ta 翻车

### 范例 C：结尾强钩子（每集必备）

```
EMMA opens the inheritance file. Photos of her grandfather.

Then — a second photo falls out. Her grandfather, shaking hands with... RYAN'S FATHER.

On the back, handwriting: "The merger must go through. Whatever it takes."

EMMA: (whispering) The wedding... was never about love. It was a deal.

Her phone lights up. A text from an unknown number:

"You weren't supposed to survive the church. — M"

EMMA's eyes widen.
```

> 🔴 **不要写 `END OF EPISODE X.`**。`END OF EPISODE 1.` 是电视/电影剧本分集标记，**海外 / DramaBox 等短剧 App 自己会用 UI 显示"Episode 1/80"**，剧本里再写一遍是冗余标签。集与集的边界靠情节断点 + 钩子承载，不需要"宣告结束"的文本。

**逐句标注**：
- 不是温吞收尾,而是**抛出更大的阴谋**（婚姻是交易 + 有人要她死）
- 钩子**升级**：从"被悔婚"升级到"有人要杀她",危机层层加码
- `"You weren't supposed to survive"`：神秘短信制造下一集动力
- 短剧每集结尾都要让观众**手指停在屏幕上,忍不住点下一集**

### 范例 D：狼人/命定（海外 头部本土幻想赛道）

```
INT. PACK HALL - NIGHT

LUNA (22), in a torn dress, kneels before the pack.

ALPHA KAIDEN: (cold) Luna Hale. I, Alpha of the Crescent Pack, reject you as my mate.

The crowd gasps. Luna's bond-mark BURNS on her neck.

LUNA: (gritting through pain) You can't even look at me when you say it.

KAIDEN: (turning away) You're weak. Mateless. Worthless to this pack.

LUNA stands, swaying. Blood drips from her mark.

LUNA: Then I reject YOU, Kaiden. (her eyes flash gold) And one day, you'll kneel.

She walks out into the storm. Behind her — her eyes glow brighter. Something is awakening.

KAIDEN (V.O.): (next ep tease) What... what is she?
```

**逐句标注**：
- 狼人"拒绝命定伴侣"是 海外 头号本土爽点公式
- `"I reject YOU"` + 眼睛发金光：被弃→觉醒,经典反转
- 超自然设定用**一句话规则**承载（bond-mark 会烧/眼睛发光),不大段世界观铺陈
- 结尾 `"What is she?"`：身份钩子,留到下一集

---

## 五、英文短剧 vs 好莱坞——逐句改写对照（钉死语感）

| ❌ 好莱坞腔（模型默认会写） | ✅ 英文短剧腔（正确） |
|---|---|
| `She studies his face, searching for the man she once loved, finding only a stranger.` | `She slaps him. "Who ARE you?"` |
| `The silence between them said everything words couldn't.` | `EMMA: Say it. SAY you cheated. / DANIEL: ...I cheated.` |
| `A complicated mix of grief and relief washed over her.` | `She laughs. Then cries. Then signs the papers.` |
| `He was not a bad man, merely a weak one, trapped by circumstance.` | `RYAN: I did it for the money. I'm not sorry. / EMMA: Then neither am I.` |
| `Years of resentment simmered beneath her calm exterior.` | `EMMA: (smiling) I've waited three years for this. / She drops the evidence on the table.` |
| `Perhaps, in another life, they might have been happy.` | `EMMA: We're done. Don't text me. Don't call me. You're nothing.` |
| `The revelation hung in the air, too heavy to acknowledge.` | `CHLOE: He's... my father?! / EMMA: Surprise.` |
| `Dawn broke over the city as she made her quiet decision.` | `INT. APARTMENT - NIGHT (场次头即够，不写日出空镜)` |

> **判据**：左列每句都"很美、很高级、很HBO"——也正因如此,它们在短剧里全是废戏。短剧的美 = 爽、快、勾人。

---

## 六、台词素材隔离

原包第六节的整套强制抽样规则和模板已隔离，不参与创作加载。使用原创且与人物动机相符的台词，不套用敏感关系模板；年龄不明角色不得进入成人亲密关系创作。原文不随仓库分发，不作运行时回退。

## 七、英文短剧腔调自检闸门（生成后逐项扫,任一不过即重写）

写完每集英文剧本,在心里跑一遍：

- [ ] **首镜即爆点**：第1个镜头就是强冲突/羞辱/背叛,不是空镜或人物介绍？
- [ ] **零心理旁白**：全集没有 `she felt / he realized / something shifted / a sense of` 这类拍不出的内心描写？
- [ ] **情绪外放**：人物的愤怒/鄙视/决心是**说出来/做出来**的,不是靠沉默留白暗示？
- [ ] **台词短而狠**：对白以短句为主,信息前置,没有大段内省独白？
- [ ] **反派够欠揍**：反派嚣张、脸谱、让观众想看 ta 翻车,而不是"复杂到让人同情"？
- [ ] **每集有反转/爽点**：本集至少有1个反转或爽点释放,不是纯铺垫渗透？
- [ ] **拥抱狗血巧合**：该用的身份反转、隐藏富豪、突然怀孕、撞见出轨等狗血梗没有被"逻辑洁癖"删掉？
- [ ] **结尾强钩子**：集末抛出更大悬念/危机升级,让观众忍不住点下一集？
- [ ] **没有好莱坞味**：通读一遍,这像 海外 爆款,还是像 HBO 迷你剧的某一集？像后者就重写。
- [ ] 🔴 **零中文/骨架标注泄漏（一票否决）**：全集正文（含集标题、场景头）**没有任何一个中文字**，也没有任何内部结构标签——`起/承/转/合`、`压/放`、`(转 · 放)`、`Beat:`、`Plot Unit N`、`情节单元`、`关键节点`、`Key Node` 全部不得出现。英文成品里出现任意一处 = 立即删除并重写。详见 `shared/base.md`「交付正文禁泄漏内部骨架标注」。

> **终极自检（一票否决）**：把这集给一个只看竖屏爽剧、手指随时准备划走的观众看——ta 会不会在第 5 秒划走？会,就重写开篇。看完会不会立刻想点下一集?不会,就重写结尾。

### 好莱坞腔量化阈值表（v6.8 · v8.5 删 H1 · 唯一真相源 · 机械命中即扣分/重写）

> **定位**：上面 9 项是**定性**自检（"通读像 海外 还是 HBO"），靠手感。下面这张表是**量化卡尺**——把定性升级成可机械命中的硬阈值，逐句扫台词，命中即判。**本表是全 skill 唯一定义源**：`stages/3-script.md` 步骤 14.5（生成时扫）与 `stages/4-review.md`（自审时扣分）均**引用本表、不复制本表**，调阈值只改这一处，杜绝多版本漂移。
>
> 🔴 **v8.5 删除 H1（单句台词 > 25 词 = 重写）**：H1 是"台词短而狠"的刚性执行器，把所有长句一律砍短，导致强情绪场景被压成电报体、台词来不及在一场里"停留"写满（详见 `stages/3-script.md` 铁律15「情绪停留」）。**删除 H1 = 允许长句存在**——当一个角色在强情绪 beat 里需要把话说透、把情绪递进说完时，一句 30-40 词的台词是合理的，不该被机械砍断。短剧的"快"靠跨集悬念，不靠把每句台词都切短。保留 H2-H6：它们防的是**真·拍不出来**的文学腔/心理旁白/留白（"可拍摄性"维度），与"句子长短"是两个不同维度，不随 H1 删除而放松。

| # | 命中信号 | 判定 | 处理 |
|---|---|---|---|
| ~~H1~~ | ~~单句台词 > 25 词~~ | ~~v8.5 已删除~~：长句在强情绪"停留"场景里是允许的，不机械砍短（见铁律15） | — |
| H2 | 出现委婉词 `Perhaps / Maybe / It seems / One might say / I suppose` | 委婉腔，短剧要直给 | 改成直陈/命令句 |
| H3 | 隐喻/比喻/抽象抒情（如 `Her silence was a cathedral` `a quiet resolve forming beneath the surface`） | 文学腔，拍不出 | 改成可拍的动作/表情 |
| H4 | 心理旁白动词 `she felt / he realized / something shifted / a sense of` | 内心描写，拍不出 | 外化成动作或说出来 |
| H5 | 情绪靠潜台词/沉默留白传递，而非直说出来 | 好莱坞克制腔 | 让人物把情绪喊/做出来 |
| H6 | 连续 ≥ 2 句无动作、无对话推进的纯氛围段 | 废戏 | 删除或换成冲突推进 |

> **量化判据**：每集逐句扫 H2-H6 这 5 项，命中即标记。生成阶段（3-script 14.5）命中即当场重写；自审阶段（4-review）按命中密度计入"硬指标与表达"维度扣分。**5 项与本节上方 9 项定性闸门配合使用：定性管"整体味道"，量化管"逐句卡死"，两层都要过。**

---

## 八、美式角色原型库（Casting Bible · 对冲"中式故事套英文皮陷阱"）

> **为什么要这一节**：模型写英文短剧时有两个翻车惯性——① 直接用中文名（陆念念、苏暖暖）；② 自作聪明做"中式故事套英文皮"：把主角设成华裔，用「Susan Su / Ethan Lu」中文名配英文别名，搭唐人街、中餐馆、玉佩、华裔参议员世家。**这两种都是假本土化，明令禁止。** 英文短剧的主角就是**土生土长的西方人**，按下面的原型库选角，人名、外形、说话方式、行为逻辑全部西式。

### 🔴 命名硬规则（先看这条）
- ✅ **正确**：名 + 姓都用地道西方姓名。男主参考 `Ethan / Liam / Lucas / Damon / Caleb / Adrian / Sebastian / Carter` + `Hart / Sterling / Blackwood / Caldwell / Sinclair / Vance`；女主参考 `Emma / Olivia / Ava / Lily / Sophia / Grace / Scarlett / Maya` + `Bennett / Carter / Reed / Monroe / Hayes`。
- ❌ **禁止**：① 拼音名（Lu Niannian）；② 中文名配英文别名（**苏念(Susan Su) / 陆景深(Ethan Lu)** 这种括号双名写法一律禁止）；③ 中英混搭（Li Wei / David Wang）；④ 把主角设成"华裔世家"以合理化中式元素。
- **判据**：剧本里不该出现任何"中文括号注释的人名"。Emma 就是 Emma，不需要"（苏暖暖）"。

### 原型对照表（每个赛道给一个美式标准像）

| 中式原型（模型默认会写） | ✅ 美式原型（应该写成这样） | 外形/身份 | 说话方式 | 行为逻辑 |
|---|---|---|---|---|
| **霸总（陆景深/总裁）** | **American Billionaire CEO**（Ethan Sterling 型） | 30 出头，西装定制，曼哈顿顶层办公室 / 私人飞机，白手起家或家族企业继承人 | 命令式短句、冷硬、不解释（`"Make it happen." / "You're mine now."`） | 雷厉风行、占有欲强、对外冷酷对女主专属温柔；用**钱和权**碾压而非"家族脸面" |
| **灰姑娘打工妹（苏暖暖）** | **American working-class heroine**（Emma Carter 型） | 20 多岁，咖啡店/医院/律所打工，租公寓、挤地铁、欠学贷 | 嘴硬有骨气、敢顶嘴（`"I don't need your money."`） | 靠自己也接受贵人助攻；逆袭靠**能力+机遇**，不靠"认回豪门亲生" |
| **萌宝（陆念念，被豪门争夺）** | **American secret baby / single-dad kid**（Lily 型） | 4-6 岁，金发碧眼或多元族裔，叫 `Daddy/Mommy`，爱吃 pancake、去 playground | 童言童语、英文、直接（`"Are you my real daddy?"`） | secret baby 反转、单亲爸带娃、亲子鉴定——**美式家庭剧逻辑，不是中式抢孙** |
| **恶毒女配（绿茶白莲）** | **American mean-girl / scheming socialite**（Chloe Vance 型） | 名媛/继姐妹/前任，名牌加身、社交名流 | 表面甜、背后狠、爱炫富（`"People like you don't belong here."`） | 抢男人、造谣、social-media 毁誉——靠**社交圈和钱**整人，不是中式宅斗下毒 |
| **逆后宫男主团（多个备胎）** | **American reverse-harem leads**（CEO + 狼人 Alpha + 摇滚明星 + 青梅竹马 best friend） | 各有鲜明西式身份：亿万富翁、乐队主唱、特种兵、霸总弟弟 | 各有腔调，但都对女主直球追求（`"Choose me, Maya."`） | 多个西式男主同时竞逐一个女主，吃醋、争风——**美式 reverse harem，不是后宫嫔妃** |
| **团宠真假千金** | **American found-family darling**（everyone adores her） | 被富豪家族/狼群/兄弟团捧在手心的女主 | 软萌或飒，被全员护着 | 哥哥们/家族/学校全员宠她，护短打脸欺负她的人——**美式 found-family，不是中式宗族认亲** |
| **命定狼人 Alpha** | **American Werewolf Alpha**（Damon Blackwood 型） | 狼群首领，肌肉、纹身、危险气场，住森林大宅/小镇 | 低沉霸道、命定宣言（`"You're my mate, whether you like it or not."`） | bond-mark、拒绝/认领命定伴侣、狼群权力斗争——**海外 头部本土幻想 IP** |

### 场景与道具替换表（换皮要换彻底）

| ❌ 中式外壳（中式故事套英文皮陷阱） | ✅ 美式场景道具 |
|---|---|
| 唐人街、中餐馆、华裔餐馆继承战 | 曼哈顿/洛杉矶 downtown、diner、家族酒庄/连锁餐饮集团 |
| 玉佩、传家信物、祖传翡翠 | 家族戒指（heirloom ring）、怀表、信托基金文件 |
| 华裔参议员/世家、家族祠堂 | old-money 家族（the Sterlings）、乡村庄园、私人会所 |
| 中式豪门大宅、四合院 | mansion / penthouse / estate in the Hamptons |
| 春节家宴、中秋团聚、跪拜长辈 | Thanksgiving dinner、圣诞家庭聚会、charity gala 慈善晚宴 |
| 婆媳斗法、嫡庶之争、家族逼婚 | mother-in-law 看不起儿媳、继姐妹争产、prenup 婚前协议博弈 |

> **终极自检（中式故事套英文皮一票否决）**：通读剧本，如果主角是"华裔 + 中文名配英文别名 + 唐人街/玉佩/华裔世家"——**这不是本土化，是中式内核换了张英文标签，必须重写成纯西方故事。** 正确的英文短剧里，主角 Emma Carter 就是在曼哈顿土生土长的美国人，她的故事里**不需要任何中国元素来解释她是谁**。

---

## 九、与其它文件的关系

- 本文件管**语感与腔调**（英文短剧该是什么声音）——最高优先级,先读。
- `formats/hollywood-script.md` 管**排版格式**（Slugline/Action/Dialogue 怎么排）——只管皮,不管魂。
- `markets/western.md` 管**本土化**（人名/场景/文化换皮）——注意：本土化是换皮不是换骨,短剧的狗血爽感内核 跨语言不变。
- `overseas/` 管**爆款赛道与 Story Beats**（狼人/契约/追妻等具体梗）。
- 节奏/钩子/情绪弹簧/反模式 → 全部沿用短剧通用体系（`frameworks/` + `stages/`）,英文项目同样适用,不因语言改变。

> **一句话收尾**：写英文短剧时,你不是一个好莱坞编剧,你是一个把中文爆款短剧"翻译"成西方故事的爽文高手。换的是脸,不是魂。
