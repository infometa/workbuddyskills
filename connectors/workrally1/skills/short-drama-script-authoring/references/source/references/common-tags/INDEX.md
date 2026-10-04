# 标签库总索引 · INDEX.md（v8.0.0 · 三库架构 · v5.7 强化中文定位）

> 64 个标签的权威全表：维度 / 文件 / level / 红线 / 质检号 / combo映射。**v8.0 三库架构**：标签按 market 分落三库——公用库 `common-tags/`（both，39个）、国内特有库 `domestic/tags/`（cn，20个含团宠）、海外特有库 `overseas/tags/`（overseas，含海外背景4个 + Story Beats）。
> 编写标准见 `_SCHEMA.md`。受众（男频/女频）为全局基调路由，写在 `routing/decision-tree.md`，不在此表计为标签。
>
> **🔴 标签定位补充（v8.0）**：本表"文件"列只给 `<维度>/<文件名>.md` 相对片段。定位真实文件时按 market 找库——`市场=国内`：先查 `common-tags/<维度>/`，未命中再查 `domestic/tags/<维度>/`；`市场=海外`：先查 `common-tags/<维度>/`，未命中再查 `overseas/tags/<维度>/`。**市场分池铁律**：国内项目禁读 overseas/tags，海外项目禁读 domestic/tags。

---

## ⚡ 标签定位机制（v5.7 新增 · 必读）

**文件名为何用英文？** 标签文件名（如 `counterattack-theme.md`）用英文，是为了跨平台/版本管理稳定、避免文件系统编码问题。**但用户永远用中文输入（如"逆袭"），LLM 也永远以中文与用户交互——英文只是文件系统的内部标识符，对用户完全不可见。**

**用户输入"逆袭"如何定位到 `counterattack-theme.md`？** 靠下面这张「中文名/别名 → 文件」权威映射表，**不靠 LLM 猜英文翻译**。流程铁律：

```
用户中文输入 → 在本表做中文匹配（含别名/同义词）→ 命中行 → 取该行"文件"列 → Read 对应英文文件
```

> **禁止**：LLM 自行把中文标签直译成英文去猜文件名（如把"逆袭"猜成 `counter-attack.md` 或 `nixi.md`）。一律以本表"文件"列为唯一真相源。表中无命中时，按 `decision-tree.md` 走最接近标签或通用规则组装，**绝不虚构文件名**。

### 中文别名 → 标签速查表（口语/简称/同义词归一）

| 用户可能的中文说法（含别名） | 归一到标签 | 文件 |
|---|---|---|
| 逆袭、翻盘、咸鱼翻身、草根逆袭、暴富 | 逆袭 | theme/counterattack-theme.md |
| 打脸、虐渣、打脸虐渣、扮猪吃虎打脸 | 打脸虐渣 | theme/face-slap-theme.md |
| 马甲、隐藏身份、多重身份、扮猪吃虎、神秘大佬 | 马甲 | theme/mask.md |
| 重生、重来一次、回到过去、人生重启 | 重生 | theme/rebirth-theme.md |
| 穿越、穿成、魂穿、古代穿现代 | 穿越 | theme/time-travel.md |
| 穿书、穿成书中人、进入小说 | 穿书 | theme/book-travel.md |
| 系统、金手指系统、签到、任务面板 | 系统 | theme/system.md |
| 赘婿、上门女婿、入赘 | 赘婿（设定） | setting/son-in-law.md |
| 赘婿逆袭、赘婿翻身、窝囊废逆袭 | 赘婿逆袭（主题） | theme/son-in-law-counterattack.md |
| 战神、战神归来、兵王归来、退伍归来 | 战神归来 | theme/war-god-return-theme.md |
| 强者回归、强者归来、王者归来、隐退归来 | 强者回归（设定） | setting/strong-return.md |
| 甜宠、宠妻、独宠、撒糖、现言甜宠 | 现言甜宠 | theme/sweet-pet.md |
| 虐恋、虐文、be、相爱相杀 | 虐恋 | theme/abusive-love.md |
| 追妻、追妻火葬场、追悔莫及、挽回 | 追妻 | theme/chase-wife.md |
| 破镜重圆、复合、重归于好 | 破镜重圆 | theme/reunion.md |
| 女性成长、大女主成长、独立女性 | 女性成长 | theme/female-growth.md |
| 大女主、女强、女主权谋 | 大女主（设定） | setting/female-lead.md |
| 霸总、霸道总裁、总裁、总裁文 | 霸总 | setting/ceo-male-lead.md |
| 萌宝、萌娃、带娃、宝宝助攻 | 萌宝 | setting/cute-baby.md |
| 神豪、首富、有钱人、花钱如流水 | 神豪 | setting/richest-man.md |
| 龙王、神龙、龙王令 | 龙王 | setting/dragon-king.md |
| 神医、医术高超、妙手回春 | 神医（设定） | setting/miracle-doctor.md |
| 无敌神医、医道无双 | 无敌神医（主题） | theme/invincible-doctor.md |
| 真假千金、真假大小姐、错换人生 | 真假千金 | setting/real-fake-daughter.md |
| 团宠、全家宠、团团宠 | 团宠 | setting/group-favor.md |
| 替身、替身文学、白月光替身 | 替身 | setting/stand-in.md |
| 豪门、豪门恩怨、家族恩怨、商战豪门 | 豪门恩怨 | theme/wealthy-clan-theme.md |
| 玄幻、仙侠、修仙、修真、玄幻仙侠 | 玄幻仙侠 | theme/xianxia.md |
| 异能、超能力、觉醒异能 | 异能 | theme/ability.md |
| 宫斗、宅斗、后宫争斗、古风权谋 | 古风权谋 | theme/ancient-politics.md |
| 古言、古风言情、古装爱情 | 古风言情 | theme/ancient-romance.md |
| 闪婚、先婚后爱、契约婚姻 | 闪婚 | theme/flash-marriage.md |
| 悬疑、推理、探案、刑侦 | 悬疑推理 | theme/mystery.md |
| 喜剧、搞笑、沙雕、爆笑 | 喜剧 | theme/comedy.md |
| 年代、年代文、知青、80年代 | 年代爱情 | theme/era-love.md |
| 娱乐圈、明星、艺人、内娱 | 娱乐圈 | theme/entertainment.md |
| 乡村、农村、种田、田园 | 乡村 | background/village.md |
| 职场、上班、办公室、商战 | 职场 | background/workplace.md |
| 民国、旧上海、乱世 | 民国 | background/republic.md |
| 校园、学生、青春 | 校园 | background/campus.md |
| 古代、历史、古装、宫廷 | 古装/历史古代 | background/ancient-costume.md（或 historical.md） |

> 本表为**高频别名**速查，覆盖约 80% 口语输入。表中未列的标签，以下方第三/四/五节的标签全表「标签」列中文名直接匹配；仍无命中走 `decision-tree.md` 三层推断。**所有匹配只输出中文，英文文件名仅用于内部 Read。**

---

## 一、四维体系与优先级

| 维度 | 数量 | 作用 | 优先级 |
|---|---|---|---|
| 受众（路由层，不计标签） | 2 | 叙事视角/爽点逻辑/台词风格总开关 | 最高 |
| 设定 | 20 | 核心金手指/核心爽点/核心钩子 | 2 |
| 主题 | 34 | 主线冲突/故事内核/价值落点 | 3 |
| 背景 | 6 | 世界观载体/场景/身份 | 4（最低） |

> 优先级铁律：**受众 > 设定 > 主题 > 背景**。

---

## 二、15个真实 combo 清单（映射唯一可引用范围）

| 平台 | combo | 路径 |
|---|---|---|
| 国内 | counterattack | references/domestic/combos/counterattack.md |
| 国内 | face-slapping | references/domestic/combos/face-slapping.md |
| 国内 | fantasy | references/domestic/combos/fantasy.md |
| 国内 | farming | references/domestic/combos/farming.md |
| 国内 | general | references/domestic/combos/general.md |
| 国内 | palace-intrigue | references/domestic/combos/palace-intrigue.md |
| 国内 | rebirth | references/domestic/combos/rebirth.md |
| 国内 | secret-identity | references/domestic/combos/secret-identity.md |
| 国内 | sweet-romance | references/domestic/combos/sweet-romance.md |
| 国内 | war-god-return | references/domestic/combos/war-god-return.md |
| 国内 | wealthy-clan | references/domestic/combos/wealthy-clan.md |
| 国内 | women-lead | references/domestic/combos/women-lead.md |
| 海外 | chase-regret | references/overseas/combos/chase-regret.md |
| 海外 | contract-marriage | references/overseas/combos/contract-marriage.md |
| 海外 | werewolf-fated | references/overseas/combos/werewolf-fated.md |

---

## 三、设定维度（20个）

| # | 标签 | 文件 | weight | level | 红线 | 质检号 | combo映射 |
|---|---|---|---|---|---|---|---|
| 1 | 大女主 | setting/female-lead.md | high | level-1 | 强 | AP-DN | domestic/women-lead |
| 2 | 霸总 | setting/ceo-male-lead.md | high | level-1 | 强 | AP-BZ | domestic/sweet-romance |
| 3 | 萌宝 | setting/cute-baby.md | high | level-2 | 弱 | — | domestic/sweet-romance |
| 4 | 小人物 | setting/nobody.md | medium | level-2 | 弱 | — | domestic/counterattack |
| 5 | 神豪 | setting/richest-man.md | high | level-2 | 弱 | — | domestic/face-slapping |
| 6 | 强者回归 | setting/strong-return.md | high | level-2 | 弱 | — | domestic/war-god-return |
| 7 | 真假千金 | setting/real-fake-daughter.md | high | level-2 | 弱 | — | domestic/wealthy-clan |
| 8 | 强强联合 | setting/strong-strong.md | medium | level-2 | 弱 | — | domestic/women-lead |
| 9 | 欢喜冤家 | setting/happy-enemies.md | medium | level-2 | 弱 | — | domestic/sweet-romance |
| 10 | 天下无敌 | setting/invincible.md | high | level-2 | 弱 | — | domestic/fantasy |
| 11 | 青梅竹马 | setting/childhood-sweethearts.md | medium | level-2 | 弱 | — | domestic/sweet-romance |
| 12 | 王妃 | setting/princess-consort.md | medium | level-2 | 弱 | — | domestic/palace-intrigue |
| 13 | 女帝 | setting/female-emperor.md | high | level-2 | 弱 | — | domestic/women-lead |
| 14 | 龙王 | setting/dragon-king.md | high | level-2 | 弱 | — | domestic/fantasy |
| 15 | 皇后 | setting/empress.md | medium | level-2 | 弱 | — | domestic/palace-intrigue |
| 16 | 替身 | setting/stand-in.md | high | level-2 | 弱 | — | overseas/chase-regret |
| 17 | 大叔 | setting/uncle-male-lead.md | medium | level-2 | 弱 | — | domestic/sweet-romance |
| 18 | 团宠 | setting/group-favor.md | high | level-2 | 弱 | — | domestic/wealthy-clan |
| 19 | 赘婿 | setting/son-in-law.md | high | level-2 | 弱 | — | domestic/counterattack |
| 20 | 神医 | setting/miracle-doctor.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |

> 白月光、契约婚姻、重生女主、穿越女主、战神（归来）**不在设定维度**——已归入 theme（见下）或并入替身作对照变体。

---

## 四、主题维度（34个）

> 防撞名：与 combos 同名的 theme 文件加 `-theme` 后缀。

| # | 标签 | 文件 | weight | level | 红线 | 质检号 | combo映射 |
|---|---|---|---|---|---|---|---|
| 1 | 打脸虐渣 | theme/face-slap-theme.md | high | level-2 | 弱 | — | domestic/face-slapping |
| 2 | 逆袭 | theme/counterattack-theme.md | high | level-2 | 弱 | — | domestic/counterattack |
| 3 | 马甲 | theme/mask.md | high | level-1 | 强 | AP-MJ | domestic/secret-identity |
| 4 | 女性成长 | theme/female-growth.md | high | level-1 | 强 | AP-NC | domestic/women-lead |
| 5 | 都市日常 | theme/urban-daily.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 6 | 重生 | theme/rebirth-theme.md | high | level-2 | 弱 | — | domestic/rebirth |
| 7 | 穿越 | theme/time-travel.md | high | level-2 | 弱 | — | domestic/rebirth |
| 8 | 系统 | theme/system.md | high | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 9 | 亲情 | theme/family-love.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 10 | 奇幻脑洞 | theme/fantasy-idea.md | medium | level-2 | 弱 | — | domestic/fantasy |
| 11 | 家庭伦理 | theme/family-ethics.md | medium | level-2 | 弱 | — | domestic/wealthy-clan |
| 12 | 奇幻爱情 | theme/fantasy-romance.md | high | level-2 | 弱 | — | overseas/werewolf-fated |
| 13 | 闪婚 | theme/flash-marriage.md | high | level-2 | 弱 | — | overseas/contract-marriage |
| 14 | 暗恋成真 | theme/crush-true.md | medium | level-2 | 弱 | — | domestic/sweet-romance |
| 15 | 古风言情 | theme/ancient-romance.md | high | level-2 | 弱 | — | domestic/palace-intrigue |
| 16 | 穿书 | theme/book-travel.md | high | level-2 | 弱 | — | domestic/rebirth |
| 17 | 战神归来 | theme/war-god-return-theme.md | high | level-2 | 弱 | — | domestic/war-god-return |
| 18 | 破镜重圆 | theme/reunion.md | high | level-1 | 强 | AP-PJ | overseas/chase-regret |
| 19 | 追妻 | theme/chase-wife.md | high | level-1 | 强 | AP-ZQ | overseas/chase-regret |
| 20 | 现代言情 | theme/modern-romance.md | medium | level-2 | 弱 | — | domestic/sweet-romance |
| 21 | 豪门恩怨 | theme/wealthy-clan-theme.md | high | level-2 | 弱 | — | domestic/wealthy-clan |
| 22 | 虐恋 | theme/abusive-love.md | high | level-1 | 强 | AP-NL | overseas/chase-regret |
| 23 | 异能 | theme/ability.md | medium | level-2 | 弱 | — | domestic/fantasy |
| 24 | 传承觉醒 | theme/inheritance-awakening.md | medium | level-2 | 弱 | — | domestic/fantasy |
| 25 | 玄幻仙侠 | theme/xianxia.md | high | level-2 | 弱 | — | domestic/fantasy |
| 26 | 古风权谋 | theme/ancient-politics.md | high | level-2 | 弱 | — | domestic/palace-intrigue |
| 27 | 年代爱情 | theme/era-love.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 28 | 赘婿逆袭 | theme/son-in-law-counterattack.md | high | level-2 | 弱 | — | domestic/counterattack |
| 29 | 娱乐圈 | theme/entertainment.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 30 | 悬疑推理 | theme/mystery.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 31 | 无敌神医 | theme/invincible-doctor.md | high | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 32 | 喜剧 | theme/comedy.md | medium | level-2 | 弱 | — | 无对应预置combo，走通用规则组装 |
| 33 | 现言甜宠 | theme/sweet-pet.md | high | level-2 | 弱 | — | domestic/sweet-romance |
| 34 | 剧情 | theme/drama.md | low | level-2 | 弱 | — | domestic/general |

---

## 五、背景维度（6个）

| # | 标签 | 文件 | weight | level | 红线 | combo映射 |
|---|---|---|---|---|---|---|
| 1 | 乡村 | background/village.md | high | level-2 | 弱 | domestic/farming |
| 2 | 职场 | background/workplace.md | high | level-2 | 弱 | domestic/counterattack |
| 3 | 民国 | background/republic.md | high | level-2 | 弱 | 无对应预置combo，走通用规则组装 |
| 4 | 校园 | background/campus.md | high | level-2 | 弱 | 无对应预置combo，走通用规则组装 |
| 5 | 历史古代 | background/historical.md | high | level-2 | 弱 | domestic/palace-intrigue |
| 6 | 古装 | background/ancient-costume.md | high | level-2 | 弱 | domestic/palace-intrigue |

> 古装映射 `palace-intrigue`（而非 fantasy）——古装更通用，宫斗/古言比玄幻更接近主流；玄幻向由 theme/xianxia 走 fantasy。

---

## 六、质检号段总表（仅强红线7个）

| 前缀 | 标签 | 维度 | 文件 |
|---|---|---|---|
| MJ | 马甲 | theme | theme/mask.md |
| NC | 女性成长 | theme | theme/female-growth.md |
| ZQ | 追妻 | theme | theme/chase-wife.md |
| PJ | 破镜重圆 | theme | theme/reunion.md |
| NL | 虐恋 | theme | theme/abusive-love.md |
| DN | 大女主 | setting | setting/female-lead.md |
| BZ | 霸总 | setting | setting/ceo-male-lead.md |

- 反模式编号统一 `AP-<前缀><两位序号>`；桥段/素材一律不编号。
- **互斥扣分**：AP-DN 与 AP-NC 命中同一"关键胜利靠男人"问题时，只扣其一（对齐 4-review.md 第98行）。
- 弱红线标签的崩级风险由 anti-patterns.md 通用反模式（#7世界观/#8性格漂移等）兜底，不单独挂号。

---

## 七、融梗配方映射（v5.3 新增）

> 按标签查找相关融梗配方文件。完整配方路由见 `references/fusion/INDEX.md`。
> 无映射的标签可通过 `fusion/_METHODOLOGY.md` 五步法动态构造融梗反应式。

### 高频标签 → 融梗配方映射

| 标签 | 维度 | 相关融梗配方 |
|---|---|---|
| 穿越 | theme | time-travel-system, time-travel-sweet, farming-time-travel-system |
| 系统 | theme | time-travel-system, system-counterattack, farming-time-travel-system |
| 重生 | theme | rebirth-revenge, rebirth-sweet, fantasy-rebirth, palace-rebirth |
| 甜宠 | theme | sweet-abusive, rebirth-sweet, time-travel-sweet, chase-wife-sweet |
| 虐恋 | theme | sweet-abusive, chase-wife-sweet |
| 打脸虐渣 | theme | rebirth-revenge, mask-face-slap |
| 逆袭 | theme | system-counterattack, war-god-son-in-law |
| 马甲 | theme | mask-face-slap, strong-return-mask |
| 战神归来 | theme | war-god-son-in-law, strong-return-mask |
| 宫斗 | theme | palace-rebirth |
| 豪门恩怨 | theme | female-growth-wealthy, wealthy-real-fake |
| 女性成长 | theme | female-growth-wealthy |
| 追妻 | theme | chase-wife-sweet |
| 玄幻仙侠 | theme | fantasy-rebirth |
| 霸总 | setting | ceo-farming |
| 大女主 | setting | female-growth-wealthy |
| 神豪 | setting | mask-face-slap, system-counterattack |
| 强者回归 | setting | strong-return-mask, war-god-son-in-law |
| 赘婿 | setting | war-god-son-in-law |
| 真假千金 | setting | wealthy-real-fake |
| 种田 | theme | ceo-farming, farming-time-travel-system |

> 融梗配方共 16 个，详见 `references/fusion/INDEX.md` 路由表。

---

## 八、统计

- 受众 2（路由层）+ 设定 20 + 主题 34 + 背景 6 = **60 标签 + 2 路由基调**。
- 强红线（level-1，挂号）：7 个。弱红线（level-2）：53 个。
- 融梗配方（v5.3 新增）：16 个高频配方 + 方法论动态生成。
