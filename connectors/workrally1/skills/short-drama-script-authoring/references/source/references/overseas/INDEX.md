# 海外 海外短剧标签体系索引

> **v6.0 架构核心变化**：海外赛道文件直接对齐 海外 Story Beats 标签体系，不再用"创作者题材"命名。

---

## 一、海外 七大爆款组合路由表（v6.3 扩充）

| # | 海外 标签组合 | combo 文件 | 核心爽感 | 主力市场 |
|---|---|---|---|---|
| 1 | Werewolf + Fated Mates + Rejected Mate | `combos/werewolf-fated.md` | 命定羁绊+被弃反转+族群权斗 | 欧美 · 拉美 |
| 2 | Contract Lovers + Flash Marriage + Fake Relationship | `combos/contract-marriage.md` | 假戏真做+契约升温+身份反转 | 欧美 · 东南亚 |
| 3 | All-Too-Late + Redemption + Self-growth | `combos/chase-regret.md` | 追悔莫及+双向救赎+女性觉醒 | 欧美 · 东南亚 |
| 4 | Secret Baby + Hidden Billionaire + Reunion | `combos/secret-baby.md` | 隐藏萌宝+生父反转+认亲催泪 | 欧美 · 东南亚 · 拉美 |
| 5 | Revenge Comeback + Identity Reveal + Rebirth | `combos/revenge-comeback.md` | 归来亮身份+层层碾压打脸 | 欧美 · 东南亚 · 拉美 |
| 6 | Billionaire Obsession + Possessive Love + Forced Proximity | `combos/billionaire-obsession.md` | 霸总病态占有+唯一性专宠+护短 | 欧美 · 东南亚 · 拉美 |
| 7 | Hidden Identity + Face-Slapping | `combos/hidden-identity-face-slapping.md` | 隐身供养反讽+忘恩背叛+揭身份清算 | 欧美 · 东南亚 · 拉美 |

> **combo #7 与 #5 的边界**：#5（revenge-comeback）是"被踩弱者藏身份归来翻身"；#7（hidden-identity-face-slapping）是"至尊主动暗中供养对方→对方忘恩背叛→揭身份反噬"。分水岭 = 主角是否"暗中给予对方资源/托举其事业"：是→#7；纯粹自己被踩无恩情→#5。命中"隐藏金主/神秘赞助人/供养前任配偶/婚内背叛清算"走 #7。

> **v6.3 新增 combo（4-6）数据来源**：提炼自 53 部真实 海外/DramaBox/FlexTV 爆款剧本，深度对齐国内 combo 模板。命中"萌宝/cute baby/secret baby"走 4；"复仇/逆袭归来/heiress returns/重生"走 5；"CEO romance/霸总/possessive/obsessed"走 6。
> **多赛道映射（海外原生优先 · 兜底才弱继承国内）**：英文输入下，海外缺口**优先用海外原生 combo/规则**——萌宝/团宠有原生对应即走 #4（secret-baby）。**暂无海外原生 combo 的赛道**（如逆后宫/团宠的部分变体）走"降级取料"兜底方案链：先回海外通用层，再弱继承国内骨架但强制换该市场原生皮（见 `ARCHITECTURE.md` 一·五节）；任何情况都不切回中文、不出中式设定。

---

## 一·五、海外市场分区视图（分市场 + 通用兜底 · 各市场可薄可厚）

> 海外分支按市场组织，各市场**可薄可厚、按需生长**。现有 6 个 combo 按主力市场归类如下；缺料时走「降级取料」三级兜底（见 `ARCHITECTURE.md` 一·五节）。**当前欧美料最厚（先做成样板），日韩/东南亚/拉美先靠兜底运行、后续逐步补原生 combo。**

| 市场 | 现有可用 combo | 补库状态 | 本土化真相源 |
|---|---|---|---|
| **通用兜底** | `general-overseas.md`（通用兜底）+ `real-hooks.md` + Story Beats（`tags/theme/`） | ✅ 已建，任何海外题材的保底 | 反中式故事套英文皮全市场通用 |
| **欧美 western** | werewolf-fated / billionaire-obsession / secret-baby / revenge-comeback / contract-marriage / chase-regret / hidden-identity-face-slapping（7 个主力，主战场欧美） | 🟢 完整样板 | `markets/western.md` |
| **东南亚 southeast-asia** | 复用 secret-baby / contract-marriage / revenge-comeback / billionaire-obsession / hidden-identity-face-slapping（主力市场含东南亚） | 🟡 靠复用+兜底，待补原生 | `markets/southeast-asia.md` |
| **拉美 latin-america** | 复用 werewolf-fated / revenge-comeback / secret-baby / billionaire-obsession / hidden-identity-face-slapping（主力市场含拉美） | 🟡 靠复用+兜底，待补原生 | `markets/latin-america.md` |
| **日韩 japan-korea** | 暂无专属原生 combo | 🔴 走通用兜底 + 弱继承，待补日式治愈/韩式财阀复仇原生 combo | `markets/japan-korea.md` |

> **补新市场原生 combo 时**：在 `overseas/combos/` 建文件（顶部标主力市场），并在本表对应市场行更新"现有可用 combo"与"补库状态"。暂不物理拆子目录，靠本视图 + combo 顶部市场标识组织；日后某市场 combo 增多再按需拆 `overseas/<市场>/`。

---

## 二、Story Beats 标签库（单梗级本土化细化）

| 文件 | 内容 |
|---|---|
| `beats/beats-shared.md` | 非红线 Beats（国内通用型 + 海外差异化型，共 38 个）本土化变体规则 |
| `beats/beats-overseas-only.md` | 海外专属红线 Beats（国内禁用，共 10 个）完整独立标签 |
| `real-hooks.md` ⭐ | **真实爆款桥段库（v6.3）**：从 53 部真实 海外/DramaBox 爆款逆向提炼的开场抓人公式 + 付费点卡点规律 + 结尾钩子套路 + 跨剧通用桥段零件 + 人设原型速查。写海外项目时作"怎么抓人/怎么搭桥段/钩子卡哪"的查表手册。 |

> **加载建议**：海外项目进入剧本生成阶段，除主轴 combo 外，**强烈建议 Read `real-hooks.md`** 取开场/付费/结尾的实战钩子公式——这是真实市场验证的桥段零件，配合 `formats/english-short-drama.md` 第六节爽台词库使用，显著提高爽点密度。

---

## 三、三大市场 TOP 爆款组合图谱

### 欧美市场 TOP 组合
| 组合 | 叙事密码 |
|---|---|
| Fated Lovers + Werewolf + Enemies to Lovers | 命定狼人+先敌后爱，性张力+宿命感双拉满 |
| Self-growth + Office Romance + Redemption | 独立女主职场逆袭+双向救赎，欧美最吃 |
| Step-Siblings + Taboo + Hidden Feelings | 禁忌屋檐拉扯+暗恋克制（仅欧美/拉美） |
| Billionaire + Contract Lovers + Fake Relationship | 豪门契约假扮，假戏真做 |

### 东南亚市场 TOP 组合
| 组合 | 叙事密码 |
|---|---|
| Rebirth + Revenge + Love-Hate | 重生复仇+爱恨交织，狗血爽感拉满 |
| Genius Babies + Flash Marriage + Hidden Identity | 萌宝助攻+闪婚+马甲，团宠向 |
| Surrogate Bride + Pregnancy + All-Too-Late | 替孕带球跑+追悔莫及 |
| BusinessKarma + Revenge + Rebirth | 玄学因果商战复仇（佛教文化区专属） |

### 拉美市场 TOP 组合
| 组合 | 叙事密码 |
|---|---|
| Affair + Revenge + Self-growth | 婚外觉醒+复仇+女性独立 |
| Love Triangle + Love-Hate + Reunion | 三角拉扯+爱恨+久别重逢 |
| Harem + Adventure + Super Power | 后宫冒险异能（男频向） |

---

## 四、加载规则

1. **国内市场**：本模块**完全不加载**，海外专属红线标签对国内项目不可见
2. **任意海外市场**：自动加载 `beats/beats-shared.md` + `beats/beats-overseas-only.md` 中适配该市场的标签池
3. 调用优先级：**标签专属规则 > 品类适配 > 通用反模式 > 通用底座**
4. 海外 Beats 叠加在主轴标签之上做细化，不替换主轴
