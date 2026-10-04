# The King of Short Drama

短剧创作全流程引擎（Agent Skill 包）。

## 一句话定位

把"题材识别 → 知识匹配 → 案例对照 → 内容生成 → 评审 → 修改"封装为一条主 agent 自主调度的 6 步流程。用户上传任意长度文本或创意，agent 自动判断载体（短剧/漫剧）、短剧题材、目标市场与语言，按对应题材的爆款公式分批产出大纲/人设/分集剧本，自审后修改成稿。

## 结构（1 个头部 skill + 平台标签组合模块 + 融梗体系 + 共享/市场/工具体系）

```
the-king-of-short-drama/
├── SKILL.md                          头部流程总纲（决策树，不存知识）
├── README.md / LICENSE / CHANGELOG.md
├── references/
│   ├── routing/decision-tree.md      步骤 0：平台标签+市场+语言+需求 识别 + 受众基调全局路由 + 融梗碰撞模式
│   ├── tags/                         v7.0 四维标签库（一标签一文件 · 双旋钮 · 七节结构含融梗亲和性）
│   │   ├── _SCHEMA.md                标签编写宪法（十字段frontmatter + 七节结构 + level分级 + 融梗亲和性）
│   │   ├── INDEX.md                  60标签全表 + 15 combo映射 + 强红线号段 + 融梗配方映射
│   │   ├── setting/                  20 个角色设定标签（含融梗亲和性第七节）
│   │   ├── theme/                    34 个主题情节标签（含融梗亲和性第七节）
│   │   └── background/               6 个时代背景标签
│   ├── fusion/                       v5.3 融梗体系（方法层+知识层+创新层）
│   │   ├── _METHODOLOGY.md           融梗方法论（五步法+反应式+速查表+红线总表）
│   │   ├── INDEX.md                  融梗配方总索引（16高频配方+路由表+标签映射）
│   │   └── recipes/                  融梗配方库（_TEMPLATE.md + 16个高频配方）
│   ├── platforms/                    平台标签驱动架构
│   │   ├── hongguo/                  红果平台
│   │   │   ├── INDEX.md              红果60标签全表 + 爆款组合路由
│   │   │   ├── combos/               标签组合文件（原赛道文件）
│   │   │   │   ├── face-slapping.md  打脸虐渣+马甲+神豪
│   │   │   │   ├── counterattack.md  逆袭+神豪+小人物
│   │   │   │   ├── sweet-romance.md  现言甜宠+霸总+先婚后爱
│   │   │   │   ├── women-lead.md     女性成长+大女主+女强
│   │   │   │   ├── war-god-return.md 战神归来+赘婿逆袭+打脸虐渣
│   │   │   │   ├── secret-identity.md 马甲+隐藏身份+扮猪吃虎
│   │   │   │   ├── rebirth.md        重生+穿越+穿书
│   │   │   │   ├── wealthy-clan.md   豪门恩怨+打脸虐渣+真假千金
│   │   │   │   ├── fantasy.md        玄幻仙侠+古风权谋+传承觉醒
│   │   │   │   ├── palace-intrigue.md 宫斗宅斗+古风权谋+重生
│   │   │   │   ├── farming.md        种田经营+穿越+系统
│   │   │   │   └── general.md        通用兜底
│   │   │   └── atoms/                原子标签
│   │   │       ├── setting/          设定类原子标签
│   │   │       └── theme/            主题类原子标签
│   │   ├── reelshort/                ReelShort 海外平台
│   │   │   ├── INDEX.md              48 个 Beats 三类分类 + 四大市场爆款组合
│   │   │   ├── combos/               海外标签组合文件
│   │   │   └── beats/                ReelShort Story Beats 标签库
│   │   │       ├── beats-shared.md   非红线 Beats 本土化变体
│   │   │       └── beats-overseas-only.md 海外专属红线标签（国内禁用）
│   │   └── shared/                   平台共用文件
│   │       ├── base.md               短剧通用规格（所有平台共用）
│   │       ├── anti-patterns.md      11 大 AI 创作反模式检测标准
│   │       ├── expression-library.md  情绪表达变体库
│   │       └── conflict-variants.md  冲突解法变体库
│   ├── markets/                      出海市场本土化规则
│   │   ├── southeast-asia.md
│   │   ├── western.md
│   │   ├── latin-america.md
│   │   └── japan-korea.md
│   ├── formats/                      载体/格式规范
│   │   ├── manga-drama.md            竖屏漫剧（分镜/视觉化补充）
│   │   └── hollywood-script.md       海外好莱坞格式排版（体量仍按竖屏短剧）
│   ├── frameworks/                   emotion-spring / hook-design / five-elements
│   ├── stages/                       1-outline / 2-character / 3-script / 4-review / 5-revise
│   ├── tools/                        运营与迭代工具文档（auto-review-rules 等）
│   └── case-studies/                 各题材爆款案例库
└── scripts/                          text_splitter / auto_review / validate_skill / build_registry（自动化质检）
```

## 术语

- 整体 = 一个 **Skill 包**（installable skill）
- 里面每个标签组合 = 一个 **标签组合模块（combo module）**，物理上是 markdown 文件，可单独新增/替换/维护
- Agent Skills 规范下 skill 之间无法互相 invoke，所以采用"头部 skill + 模块文件"而非多个独立 skill——这样既满足"独立可维护"，又避免多份 metadata 抢占上下文、互相误触发

## 红果标签组合

| # | 标签组合 | 市场 | 卖什么 |
|---|---|---|---|
| 1 | 打脸虐渣+马甲+神豪 | 国内 | 不公被纠正 |
| 2 | 草根逆袭+系统+重生 | 国内 | 草根改命 |
| 3 | 霸总甜宠+先婚后爱+追妻 | 通用 | 被独宠供养 |
| 4 | 大女主+独立+成长 | 通用 | 女性独立价值 |
| 5 | 战神归来+兵王+都市 | 国内 | 武力征服 |
| 6 | 马甲隐藏+多重身份+反差 | 通用 | 多重反差连爆 |
| 7 | 重生穿越+先知+改命 | 通用 | 先知掌控 |
| 8 | 豪门认亲+真假+血脉 | 下沉女频 | 血脉+真假对决 |
| 9 | 古装玄幻+修仙+等级 | 通用 | 等级跃迁 |
| 10 | 宫斗宅斗+古风权谋+重生 | 国内 | 后宫宅门博弈 |
| 11 | 种田经营+穿越+系统 | 国内 | 经营成长 |
| 兜底 | general | 通用 | 无法归类时的通用框架 |

## 多语种

只维护一份中文源文件，**不需要双语/多语版**。模型按识别的用户语言输出最终内容；海外题材按目标市场本土化。

## 扩展

新增标签组合：新建 combo 文件 → 在 `platforms/hongguo/INDEX.md` 登记。

## 安装

```bash
unzip the-king-of-short-drama.zip -d ~/.workbuddy/skills/
```

## 许可

MIT（基于 GongLingRui/screen-creative-skills 重构）
