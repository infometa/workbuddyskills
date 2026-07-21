# 意图映射 · 关键词 → 模式 / 场景 / 叙事 / 皮肤

> 把"用户原话"翻译成本 skill 内部参数的唯一参考表。生成模式所有自动选择都按本文件查表。
>
> ⚠️ **绝对禁止 AskUserQuestion / 对话追问来确认场景或意图**。即使输入完全中性，也直接 best-guess 一个最接近的 scene 起 `serve.py start`，把确认/修正交给右侧面板。

---

## §1 模式分流（最先决定走哪条路）

| 用户输入特征                                  | 走哪条路                            |
| --------------------------------------------- | ----------------------------------- |
| 给出 `.html` 文件路径 / 「上传/导入腾讯文档」 | **上云模式**（直接进发布流程）      |
| 命中 §2 表里 4 类场景关键词（含语义近似）     | **生成模式**（起 `serve.py start`） |
| 命中 §2 表里"模板外场景"（custom:\*）         | **退出本 skill**，由通用 agent 处理 |
| 完全无任何线索（如「做个网页」「来个东西」）  | **退出本 skill**，由通用 agent 处理 |

---

## §2 关键词 → scene 推断（生成模式起点）

只要用户输入命中下表任一类（含语义近似），**立即**起 `serve.py start --probe-scene <id>`，**禁止追问**。

| 类别                | 典型关键词                                                                  | scene                          |
| ------------------- | --------------------------------------------------------------------------- | ------------------------------ |
| 立项 / 向上汇报     | 立项、方案、提案、申请、ROI、资源申请、向上汇报、委员会、评审、给老板做     | `proposal`                     |
| 周期同步            | 周报、双周报、月报、季报、年报、进展、同步、OKR、KR                         | `sync`                         |
| 数据洞察            | KPI、DAU、MAU、留存、归因、下跌、上涨、A/B、同比、环比、dashboard、数据分析 | `insight`                      |
| 知识传播 / 技术分享 | 技术分享、培训、课件、长文、杂志、分享会、FAQ、答疑                         | `share`                        |
| 仅「做个汇报」      | 无更具体线索时的兜底                                                        | `proposal`（默认偏向立项汇报） |
| 模板外 · 官网       | 官网、landing、产品介绍                                                     | `custom:homepage` ＊           |
| 模板外 · 邀请       | 邀请函、年会、婚礼、发布会                                                  | `custom:invitation` ＊         |
| 模板外 · 活动       | H5、活动页、运营活动、促销                                                  | `custom:campaign` ＊           |
| 模板外 · PRD        | PRD、需求文档                                                               | `custom:prd` ＊                |
| 模板外 · 画册       | 画册、作品集                                                                | `custom:brochure` ＊           |
| 模板外 · 简历       | 简历、介绍页                                                                | `custom:profile` ＊            |
| 模板外 · 会议       | 会议纪要、复盘文档                                                          | `custom:minutes` ＊            |

> ＊ 标 `custom:*` 的场景由通用 agent 处理，不进入生成模式管线。

---

## §3 「AI 帮我选」 → narrative + skin 推断

当用户在模板选择页点击「AI 帮我选」（`auto_pick_narrative: true` 或直接跳过问卷）时，按下表从用户**原始 prompt** 做关键词匹配，自动选定 `narrative` + `skin`。

| 关键词                      | scene      | narrative      | 默认 skin          |
| --------------------------- | ---------- | -------------- | ------------------ |
| 立项 / 申请 / 方案 / ROI    | `proposal` | `pyramid`      | `stillwater`       |
| 转型 / 改变 / 不得不 / 冲突 | `proposal` | `scqa`         | `prism`            |
| 战略 / 3 年 / 规划 / 愿景   | `proposal` | `blm`          | `tencent-blue`     |
| 周报 / 双周报 / 进展        | `sync`     | `prep`         | `stillwater`       |
| 复盘 / 战役 / 收尾          | `sync`     | `star`         | `letterpad`        |
| OKR / 目标 / KR / 季度      | `sync`     | `okr`          | `tencent-blue`     |
| KPI / DAU / dashboard       | `insight`  | `pyramid-data` | `pulse`            |
| 下跌 / 归因 / 为什么        | `insight`  | `attribution`  | `pulse`            |
| A/B / 同比 / 环比 / 对比    | `insight`  | `contrast`     | `pulse`            |
| 故事 / 理念 / 起源          | `share`    | `story-arc`    | `letterpad`        |
| FAQ / 问答 / 培训           | `share`    | `qa-driven`    | `hearth`           |
| 杂志 / 深度 / 长文          | `share`    | `magazine`     | `indigo-porcelain` |

---

## §4 强制规则（覆盖一切自动选择）

- **腾讯系锁定**：用户提到「腾讯内部汇报」「司内」「向 Leader 汇报」「腾讯官方」→ 皮肤强制 `tencent-blue`，且 3 张模板卡的 skin 全部为 `tencent-blue`
- **杂志深刊锁定**：narrative=`magazine` → skin 必须从 `ink-press` / `indigo-porcelain` / `forest-press` / `kraft-press` / `dune-press` 中选
- **best-guess 永远比追问优先**：哪怕只有 50% 把握也立刻起脚本，让用户在右侧面板修正

---

## §5 `serve.py` UI 兜底入口（与意图映射无关，避免概念混淆）

> 下面这两处「兜底入口」是 UI 层的概念，不是 agent 决策路径：
>
> - 模板选择页第 4 张「AI 帮我选」卡片：用户主动跳过问卷，触发 §3 的自动推断
> - scene 选择页「✚ 其他 · 让 AI 自由生成」chip：用户主动选择 `custom:freeform`，等同退出本 skill
