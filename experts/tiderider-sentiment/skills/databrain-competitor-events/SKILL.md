---
name: databrain-competitor-events
description: 游戏竞品活动报告生成工具。当用户需要对某款游戏生成官媒发帖内容和官方活动报告时使用，依次执行数据获取、活动聚合、联网搜索、总结分析四个主要工作模块，最终保存并展示指定格式的竞品报告。触发示例："帮我做一份 XXX 的竞品活动分析"、"生成 XXX 游戏官帖分析报告"、"最近 XXX 有什么官方活动？"。
disable: false
metadata: {"openclaw": {"requires": {"env": ["DATABRAIN_TOKEN", "PLATFORM"]}}}
---

# Competitor Event Report (主控 Skill)

你是竞品游戏活动分析报告的总协调者。解析参数后，为每个游戏并发启动子 Agent 执行 Step 1–4（数据采集、活动聚合、联网搜索、总结分析与报告生成），所有子 Agent 完成后，串行拼接各游戏报告段落，写入文件并展示报告。注意：后续的Utility工作还包括 **[Utility 任务一] 报告的存储与展示** 以及 **[Utility 任务二] 自动化例行任务引导**。两项任务均必须执行，不可跳过。

## 前置检查

**在解析任何参数之前，先读取已安装 plugin 根目录 `.env`；若不存在，再读取当前 Skill 目录下的 `.env`。**

- 若文件**不存在**（Read 返回错误）→ 进入**首次配置流程**（见下方）
- 若文件**存在**，逐行解析（跳过空行和 `#` 注释行），提取：
  - `PLATFORM=` 后面的值 → 若为空或不存在该行 → 进入**首次配置流程**
  - `DATABRAIN_TOKEN=` 后面的值 → 若为空或不存在该行 → 进入**首次配置流程**

---

### 首次配置流程

Read `submodules/first_time_setup.md`，按照其中的指示和流程来引导用户。

---

### 平台初始化说明

`.env` 读取完成后，记录 `PLATFORM` 的值。**BRANCH 变量不在此处解析**，将在后续每个需要做分支判断的决策点现场重新解析，以确保执行时准确生效。

---

---

## ⛔ 执行纪律（全局约束，优先级最高）

以下规则适用于本 Skill 的**所有步骤**，不得以任何理由违反：

1. **禁止跳过步骤**：严禁以"时间限制"、"复杂度"、"效率"、"任务量大"为由跳过任何步骤。每个步骤都是必须执行的环节。
2. **禁止生成精简版**：严禁擅自删减报告内容、合并活动、或以"内容过长"为由截断输出。报告必须原封不动地包含所有活动的完整分析。
3. **合法的失败处理**：若某个**单条目**因客观原因（网络错误、数据缺失）失败，记录失败原因后可跳过该条目，但不得整体跳过所在步骤。
4. **禁止擅自做 tradeoff**：遇到执行困难时，不得自行判断"这样更合理"并改变执行路径。应按流程继续，或明确告知用户遇到的问题。


---

## 输入参数

从用户请求中解析以下参数：
- **game_names**：待分析的游戏名称列表（一个或多个）。原则上保留用户输入的原始游戏名称，**禁止擅自翻译**（例如不得将英文名翻译为中文，中文译名可能有误）；仅当用户输入存在明显拼写错误（typo）时，可修正为正确拼写。
- **start_time**：查询起始时间，精确到秒，如 `2025-01-01 00:00:00`
- **end_time**：查询结束时间，精确到秒，如 `2025-03-31 23:59:59`
- **my_game**（可选）：己方运营的游戏，通过竞品分析获得提升改进的受益对象。若用户未输入，则当作通用游戏处理。
- **focus_direction**（可选）：用户希望在启发建议中重点关注的方向，如"活动运营策略"、"社区互动方式"、"付费设计"等；若用户未提及则为空字符串
- **regions**（可选，非常见场景）：用户需要按国家/语言分区查询时才会提及，通常以自然语言描述（如"美国"、"日本"、"巴西"、"英语区"）。解析时须查阅 `references/country_language_code_mapping.csv`（重点参考 `language code` 和 `country code` 两列）将自然语言转换为对应的小写 code（如 `us`、`jp`、`br`、`en`）；如用户提及**某个大洲**，收集所有涉及国家的小写code并拼接为"us,ca,mx"的字符串，合并为一个报告实体，无需再拆分为单个国家一一处理。**大多数请求不涉及 regions**，此时默认单一全局视角，不在文件名和报告中附加任何区域标识。

> `unified_edition_id` 无需用户提供，由 `game_search.py` 脚本根据游戏名称自动查询获得。

## 文件名约定

所有中间文件和输出文件使用统一的命名规则：

```
safe_name = game_name.replace(" ", "_").replace(":", "")
# 例：Honkai: Star Rail → Honkai_Star_Rail

# 文件前缀 file_key 由两种情况决定：
# · 未指定 regions（默认全局视角，主要场景）：file_key = safe_name
# · 指定了 regions（多区域模式，少数场景）：  file_key = {safe_name}_{region}
# region 使用从映射表查到的小写 code，不做大小写转换
# 例：Honkai_Star_Rail_us, Honkai_Star_Rail_jp
```

最终报告文件名由 `file_key` 和是否提供 `my_game` 决定：

```
# 用户未提供 my_game：
reports/_report_{file_key}_{timestamp}.md

# 用户提供了 my_game，先将其转换为 safe_name：
my_game_safe = my_game.replace(" ", "_").replace(":", "")
reports/_report_{my_game_safe}_{file_key}_{timestamp}.md
```

> **查询多个具体的国家或语言时**：game_names × regions 的笛卡尔积决定最终报告数量。  
> 例：3 个游戏 × 3 个区域 = 9 份独立报告，每份对应一个 (game, region) 对。

> **查询某个大洲时**：无需专门区分大洲内的具体国家，将整个大洲视为一个整体，合并在一起后生成一份报告即可。

各模块输入/输出文件（`{file_key}` 在全局模式时等于 `{safe_name}`，多区域模式时等于 `{safe_name}_{region}`）：

| 模块 | 输出文件 |
|---|---|
| opinion-query | `cache/{file_key}_official_posts_{timestamp}.csv` 和 `cache/{file_key}_post_comments_{timestamp}.csv` |
| event_aggregation | `cache/_cluster_summary_{file_key}_{timestamp}.json` |
| online_search | `cache/_online_search_{file_key}_{timestamp}.json` |
| 总结分析 | `cache/_report_section_{file_key}_{timestamp}.md` |
| generate_final_report | 见上方最终报告文件名规则 |

---

## 前置工作一：输入埋点

输入参数解析完成后，立即 Read `submodules/input_logging.md`，按其指令执行一次埋点上报。埋点上报后明确返回成功/失败的结果。

---

## 前置工作二：统一生成全局 timestamp

在启动任何子 Agent 之前，使用 Bash 工具生成一个统一的全局 `timestamp`，所有子 Agent 共享同一个值：

```bash
python -c "from datetime import datetime; print(datetime.now().strftime('%Y%m%d_%H%M%S'))"
```

捕获输出（如 `20250323_143022`）作为全局 `{timestamp}`，**后续所有步骤（子 Agent、报告文件名）均使用此值，不得重新生成**。

> **精度要求：** timestamp 精确到秒（`%Y%m%d_%H%M%S`），年月日相同但时分秒不同则视为不同 timestamp。
> cache/ 目录中可能存有同一天多次执行的历史文件，**必须用完整精确的 timestamp（含时分秒）** 才能唯一定位本次执行的文件，仅匹配日期前缀将导致读取历史错误文件。

---

## 执行流程总览

**主要场景（全局模式，未指定 regions）：**

```
解析 game_names（regions 为空，每个游戏对应一个全局查询）
       │
       ├─ [并发] 子 Agent: game_1 → Step 1(全局) → Step 2 → Step 3 → Step 4 → 报告
       ├─ [并发] 子 Agent: game_2 → Step 1(全局) → Step 2 → Step 3 → Step 4 → 报告
       └─ [并发] 子 Agent: game_N → Step 1(全局) → Step 2 → Step 3 → Step 4 → 报告
                    │
             等待所有子 Agent 完成
                    │
       [串行] 每个游戏各自写入独立报告文件 → 展示制品
```

**少数场景（多区域模式，用户明确指定了 regions）：**

```
解析 game_names × regions，构建 (game, region) 对列表
       │
       ├─ [并发] 子 Agent: (game_1, region_1) → Step 1(区域定向) → Step 2 → Step 3 → Step 4 → 报告
       ├─ [并发] 子 Agent: (game_1, region_2) → Step 1(区域定向) → Step 2 → Step 3 → Step 4 → 报告
       └─ [并发] 子 Agent: (game_N, region_M) → Step 1(区域定向) → Step 2 → Step 3 → Step 4 → 报告
                    │
             等待所有子 Agent 完成
                    │
       [串行] 每个 (game, region) 对各自写入独立报告文件 → 展示制品
```
> **区域为某个大洲时**，收集所有涉及国家的小写code，并拼接为"us, ca, mx"的字符串例如`--country=us,ca,mx`。无需再拆分为单个国家一一处理。
> **并发粒度说明**：并发上限 3 作用于任务单元总数（全局模式 = 游戏数；多区域模式 = game × region 对数）。
> **并发调用失败时串行保底**：并发启动子agent遇到权限问题或其他报错时，改为串行执行任务保底。


---

## 并发阶段：为每个 (game, region) 对启动独立子 Agent

解析出 `game_names` 和 `regions` 后，构建完整的 **(game, region) 对列表**：

```
pairs = [(game, region) for game in game_names for region in regions]
# 若 regions 未指定，则视为 regions = [""]（单一全局视角，region 传空字符串）
```

按以下规则并发启动子 Agent：

- **并发上限为 3**：每批最多同时启动 3 个子 Agent
- 若对总数 ≤ 3：**在同一条消息中**一次性启动所有子 Agent（并发）
- 若对总数 > 3：将列表按每批 3 个拆分，**每批在同一条消息中并发启动**，等待本批全部完成后再启动下一批
- 批次之间不得跳过等待，不得串行逐个启动

每个子 Agent 的 prompt 模板如下（将占位符替换为实际值）：

```
你是竞品数据处理子 Agent，负责处理游戏「{game_name}」（区域：{region}）从数据采集到报告段落生成的全流程。
当前 Skill 根目录：{skill_root}
游戏名称：{game_name}
区域标识：{region}（若为空字符串，表示不区分区域，走全局查询）
start_time：{start_time}
end_time：{end_time}
my_game：{my_game}
focus_direction：{focus_direction}
DATABRAIN_TOKEN：{DATABRAIN_TOKEN}
全局 timestamp：{timestamp}

**重要：全局 timestamp 已由主控统一生成并传入（值为 {timestamp}），后续所有步骤必须直接使用此值，禁止从文件名提取或重新生成。**

**⚠️ 严格的 timestamp 精度要求（违反将导致读取历史错误文件）：**
cache/ 目录下积累了大量历史执行产生的中间文件，文件名格式相同、仅 timestamp 不同。
读取任何上一步骤的产出文件时，**必须使用主控传入的完整精确 timestamp（精确到秒，如 `20250323_143022`）**，一字不差地构造文件路径。

- ❌ **禁止** 使用 Glob、find、ls 等方式在 cache/ 下搜索匹配文件
- ❌ **禁止** 仅匹配日期前缀（如 `20250323_*`）—— 可能匹配到同一天其他历史执行的文件
- ❌ **禁止** 从目录列表中挑选"最新"或"最近"的文件
- ✅ **只允许** 用传入的 `{timestamp}` 直接硬构造完整路径，例如：
  `{skill_root}/cache/{file_key}_official_posts_{timestamp}.csv`
- 若以精确路径访问时文件不存在，**立即上报错误**，不得降级为搜索历史文件作为替代

**文件命名前缀（file_key）规则：**
```
safe_name = game_name.replace(" ", "_").replace(":", "")
file_key  = f"{safe_name}_{region}" if region else safe_name
# region 保持映射表查到的原始小写 code，不做大小写转换
```
后续所有中间文件和报告段落文件均以 `{file_key}` 为前缀，而非 `{safe_name}`。

**⛔ 禁止在执行步骤前进行无关的文件搜索或探路操作**，包括但不限于：
- 搜索 cache 目录下的历史 CSV / JSON 文件
- 用 Glob 查找同游戏名的历史输出文件
- 检查是否存在可复用的缓存

所有中间文件均由当前步骤现场生成，直接按步骤顺序执行即可。

请依次执行以下四个步骤。**每个步骤完成后立即输出一行进度日志**（格式见下），然后继续下一步：

### Step 1 — 舆情数据获取
若 region 为空字符串，Read `{skill_root}/submodules/opinion_query.md`，按其指令执行全局查询。
若 region 非空，Read `{skill_root}/submodules/region_query.md`，按其指令执行该区域的定向查询。
输出两个 CSV 文件路径，存放于 {skill_root}/cache/ 目录下：
- `{file_key}_official_posts_{timestamp}.csv`
- `{file_key}_post_comments_{timestamp}.csv`
使用查询返回的 entity_name 作为后续步骤的 game_name。
**不得**从 CSV 文件名中提取 timestamp，始终使用传入的全局 timestamp。

**Step 1 完成后立即输出：**
`[{game_name}({region})] ✅ Step 1 完成 — 舆情数据获取成功，共 {N} 条官方帖子，共 {n} 条帖子评论，timestamp={timestamp}`

### Step 2 — 活动聚合
Read `{skill_root}/submodules/event_aggregation.md`，按其指令执行。
传入：game_name（entity_name）、official_posts_csv、post_comments_csv、timestamp
- 输入文件路径必须为：
  - `{skill_root}/cache/{file_key}_official_posts_{timestamp}.csv`
  - `{skill_root}/cache/{file_key}_post_comments_{timestamp}.csv`
  - **禁止搜索目录，直接使用上述精确路径读取 Step 1 的产出**
输出：{skill_root}/cache/_cluster_summary_{file_key}_{timestamp}.json

**Step 2 完成后立即输出：**
`[{game_name}({region})] ✅ Step 2 完成 — 活动聚合成功，共识别 {M} 个活动簇`

### Step 3 — 联网搜索
Read `{skill_root}/submodules/online_search.md`，按其指令执行。
传入：game_name、cache/_cluster_summary_{file_key}_{timestamp}.json、timestamp
- 输入文件路径必须为：
  - `{skill_root}/cache/_cluster_summary_{file_key}_{timestamp}.json`
  - **禁止搜索目录，直接使用上述精确路径读取 Step 2 的产出**
输出：{skill_root}/cache/_online_search_{file_key}_{timestamp}.json

**Step 3 完成后立即输出：**
`[{game_name}({region})] ✅ Step 3 完成 — 联网搜索成功，共搜索 {m} 个问题`

### Step 4 — 总结分析与报告段落生成

传入：game_name、{skill_root}/cache/_online_search_{file_key}_{timestamp}.json、my_game、focus_direction
- 输入文件路径必须为：
  - `{skill_root}/cache/_online_search_{file_key}_{timestamp}.json`
  - **禁止搜索目录，直接使用上述精确路径读取 Step 3 的产出**
输出：报告段落 {skill_root}/cache/_report_section_{file_key}_{timestamp}.md

基于 联网搜索的结果，逐个分析结果中的每个活动，按照以下要求生成该游戏的报告段落（Markdown 格式）：
- 活动按 total_engagement 从高到低排列
- 整体使用**中文**输出
- **谨慎翻译游戏专有名词：** 仅当搜索来源中有明确的中文译名时才使用，否则保留原始语言
- focus_direction 若非空，在"可借鉴启发"中重点关注该方向；若为空，从以下角度中选择与帖子内容相符的方面针对 my_game 进行启发借鉴分析：活动运营与宣发策略、与玩家互动类活动、品牌联动、病毒梗传播方式、UGC 活动运营

**Top 正面/负面评论观点**：数据来源为输入 json 中的 positive_sentiment_comments 和 negative_sentiment_comments comment list，分别聚类并统计 Top 3 观点（依据相应的支持评论数从高到低排列）。

**正面/负面代表性评论**：按点赞量从高到低选取，过滤语义不明或重复的评论，正面和负面各语义至多展示三条，并附带中文翻译。

**空数据处理**：注意，评论数量及占比, Top 评论观点和代表性评论这三部分都可能无相关数据，此时在报告中输出"暂无相关数据"即可。

每个活动使用以下模板输出：

---

## 活动 {index}：{event_name}

**活动发布时间：** {event_release_date}

**活动发布内容：** {event_release_content}

**活动描述：** {event_description}

**代表主贴链接：** {content_url_lists[0]}

**代表主贴数据表现：** 浏览量：{tweets_view_lists[0]}， 点赞量：{tweets_like_lists[0]}， 回复量：{tweets_reply_lists[0]}， 转发量：{tweets_retweet_lists[0]}， 互动量：{engagement_lists[0]}

**评论数量及占比**：正面评论 {positive_sentiment_comment_no}条（占比xx%），负面评论 {negative_sentiment_comment_no}条（占比xx%），中性评论 {neutral_sentiment_comment_no}条（占比xx%）

**总互动量：** {total_engagement}

**Top 正面评论观点：**
- {top_positive_opinion_1}
- {top_positive_opinion_2}
- {top_positive_opinion_3}

**正面代表性评论：**
- {representative_positive_comment_1} (对应的评论中文翻译)
- {representative_positive_comment_2} (对应的评论中文翻译)
- {representative_positive_comment_3} (对应的评论中文翻译)

**Top 负面评论观点：**
- {top_negative_opinion_1}
- {top_negative_opinion_2}
- {top_negative_opinion_3}

**负面代表性评论：**
- {representative_negative_comment_1} (对应的评论中文翻译)
- {representative_negative_comment_2} (对应的评论中文翻译)
- {representative_negative_comment_3} (对应的评论中文翻译)

**宣发形式及策略：** {promotion_approach}

**可借鉴启发：** {implications}

---

将生成的完整报告段落（该游戏所有活动，**不含**总标题行）写入：
`{skill_root}/cache/_report_section_{file_key}_{timestamp}.md`

**Step 4 完成后立即输出：**
`[{game_name}({region})] ✅ Step 4 完成 — 总结分析完成，共生成 {N} 个活动报告，段落已写入 _report_section_{file_key}_{timestamp}.md`

全部完成后，返回以下 JSON（不要输出其他内容）：
{
  "game_name": "<entity_name>",
  "region": "<region>",
  "safe_name": "<safe_name>",
  "file_key": "<file_key>",
  "timestamp": "<timestamp>",
  "event_count": <该任务单元的活动总数>,
  "report_section_path": "<{skill_root}/cache/_report_section_{file_key}_{timestamp}.md 的完整路径>"
}
```

> **skill_root** 为当前 SKILL.md 所在目录的绝对路径，执行前通过 Bash `pwd` 或已知路径确认。
> 子Agent 执行任务所需的.md指令和脚本文件都存放于**skill_root**该目录下

---

## 最终汇总：拼接所有内容，生成唯一一份报告

等待所有子 Agent 返回结果后，收集每个子 Agent 的输出 JSON，汇总为列表：

```json
[
  { "game_name": "...", "region": "...", "safe_name": "...", "file_key": "...", "timestamp": "...", "event_count": N, "report_section_path": "..." },
  ...
]
```

若某个子 Agent 失败，记录失败原因，跳过该项，继续处理其余。

> **⚠️ 读取报告段落文件时的 timestamp 约束：**
> 每个子 Agent 已在返回 JSON 中提供了 `report_section_path`（包含完整的精确 timestamp）。
> 读取段落文件时**必须使用该路径**，不得自行在 cache/ 目录中搜索或猜测文件名。
> timestamp 必须与子 Agent 返回值完全一致（精确到秒），日期相同但时间不同的文件属于历史文件，**严禁读取**。

### 拼接规则

**最终只产出一份报告文件**，拼接方式视是否有 region 而定：

**① 报告总标题**（写在最前）：
```
# {start_time} 至 {end_time} 官号竞品活动情报

> 共 {total_event_count} 个活动（{game_1}：{N1} 个，{game_2}：{N2} 个，…）

---
```

**② 按游戏分组，按 game_names 原始顺序依次追加**：

- **无 region（全局模式）**：每个游戏插入游戏名标题，紧接其报告段落：
  ```
  # {game_name}
  {_report_section_{file_key}_{timestamp}.md 全部内容}
  ```

- **有 region（多区域模式）**：先按游戏分组，同一游戏内再按 regions 顺序排列各区域段落：
  ```
  # {game_name}

  ## {region_1}
  {_report_section_{file_key_region1}_{timestamp}.md 全部内容}

  ## {region_2}
  {_report_section_{file_key_region2}_{timestamp}.md 全部内容}
  ```

**③** 所有游戏段落拼接完毕后，整体即为最终报告，按 **[Utility 任务一]** 规则写入文件并展示。

**灵活性说明：** 若用户在请求中提出了特定的格式要求或希望新增输出维度（如展示搜索来源、增加互动数据对比等），在生成报告时直接按用户要求调整，无需修改模板文件。新增的输出维度必须有真实准确的数据作为基础，禁止捏造。


## [Utility 任务一]储存并展示报告

报告存储分为**两个阶段**，必须按顺序执行：

> **🔁 现场解析 BRANCH（执行本任务前必读）**
> 回顾 `.env` 中读取到的 `PLATFORM` 值，按下表重新推导 BRANCH，并在心中明确声明：**当前 BRANCH = {A/B/C}**，后续仅执行对应分支，跳过其余。
>
> | PLATFORM 值 | BRANCH |
> |---|---|
> | `WorkBuddy` | `A` |
> | `Openclaw` | `B` |
> | 其他 / 空 | `C` |

---

### 阶段一：在当前工作目录下储存报告 （根据解析BRANCH，不同BRANCH采用不同的储存和展示方式）

最终只有**一份报告文件**，文件名规则（写入 default workspace 根目录）：
- 若用户**未提供** `my_game`：`_report_{timestamp}.md`
- 若用户**提供了** `my_game`：`_report_{my_game_safe}_{timestamp}.md`

> 任何 Branch 均须遵守：必须原封不动保存报告全部内容，**禁止擅自删减**。如遇写入错误，检查占位符后重试，不得以"内容过长"为由跳过任何活动。

**[Branch A - WorkBuddy]** 使用标准分批写入协议，逐活动写入，最终**移除**占位符：
- 目标：将最终报告保存到 产物 - 制品 ，并要求调用结果展示
- **第一步：** 用 `write` 工具写入报告头部 + 第一个活动，末尾追加 `<!-- NEXT_BATCH -->`
- **第二步：** 用 `replace_in_file` 将 `<!-- NEXT_BATCH -->` 替换为下一个活动内容 + 新的 `<!-- NEXT_BATCH -->`，逐活动重复
- **第三步：** 最后一个活动直接替换 `<!-- NEXT_BATCH -->`，不再追加占位符
- **第四步：** 写入完成后使用 `open_result_view` 工具打开**存放于 WorkBuddy default workspace 根目录**的报告文件展示制品报告。（注意不是存放于{skill_root}/reports/ 目录的报告文件）


**[Branch B - Openclaw]** 使用标准分批写入协议，逐活动写入，最终**移除**占位符（文件存档用途，不通过 IM 推送完整报告）：
- **第一步：** 用 `write` 工具写入报告头部 + 第一个活动，末尾追加 `<!-- NEXT_BATCH -->`
- **第二步：** 用 `replace_in_file` 将 `<!-- NEXT_BATCH -->` 替换为下一个活动内容 + 新的 `<!-- NEXT_BATCH -->`，逐活动重复
- **第三步：** 最后一个活动直接替换 `<!-- NEXT_BATCH -->`，不再追加占位符
- **第四步：** 报告生成完成后，直接在当前对话回复中输出摘要规则如下：
  - **在当前对话中直接回复：** 不要使用 message tool 主动发送消息。
  - **内容范围：** 仅输出每个游戏各活动的摘要内容，按以下格式发送：（活动名，互动量），**无需附带其他信息、不发送完整报告原文**
  - **分条规则：** 每个游戏的摘要作为**一条独立消息**发送；若有多个游戏，则拆分成多条消息，按游戏顺序发送。
- **第五步：** 报告生成完成后，把生成的报告文件以文件传输的方式发送给用户。

**[Branch C - Others]** 使用标准分批写入协议，逐活动写入，最终**移除**占位符：
- **第一步：** 用 `write` 工具写入报告头部 + 第一个活动，末尾追加 `<!-- NEXT_BATCH -->`
- **第二步：** 用 `replace_in_file` 将 `<!-- NEXT_BATCH -->` 替换为下一个活动内容 + 新的 `<!-- NEXT_BATCH -->`，逐活动重复
- **第三步：** 最后一个活动直接替换 `<!-- NEXT_BATCH -->`，不再追加占位符
- **第四步：** 写入完成后，原封不动地打印输出报告的完整内容


---

### 阶段二：copy 到 reports 目录存档

阶段一完成后，使用 Bash 的 `cp` 命令将 default workspace 的报告文件**直接复制**到 skill 的 reports 目录，**禁止重新生成内容**：

```bash
cp "{default_workspace_file_path}" "{skill_root}/reports/_report_{filename}.md"
```

同时告知用户文件已保存：

| 文件 | 说明 |
|---|---|
| artifact 路径 | 制品展示文件 |
| `{skill_root}/reports/` | 本地存档副本 |



## [Utility 任务二] 自动化例行任务 （后续必要任务、不可跳过）

> **🔁 现场解析 BRANCH（执行本任务前必读）**
> 回顾 `.env` 中读取到的 `PLATFORM` 值，按下表重新推导 BRANCH，并在心中明确声明：**当前 BRANCH = {A/B/C}**，后续仅执行对应分支，跳过其余。
>
> | PLATFORM 值 | BRANCH |
> |---|---|
> | `WorkBuddy` | `A` |
> | `Openclaw` | `B` |
> | 其他 / 空 | `C` |

**[Branch A - WorkBuddy]** 
WorkBuddy平台自带优秀的自动化任务工具，因此更推荐使用平台上提供的自动化功能。将以下引导信息输出给用户：
如果对本次生成报告满意，希望自动化例行报告，可前往WorkBuddy的"自动化"功能模块，进行定时任务的创建和管理。

**[Branch B - Openclaw]**
Read `{skill_root}/submodules/daily_push.md`，按其指令判断是否需要引导用户开启自动推送。

**[Branch C - Others]**
Read `{skill_root}/submodules/daily_push.md`，按其指令判断是否需要引导用户开启自动推送。




> 禁止在报告展示后添加任何形式的回顾或总结文字。

> 如果某个子模块执行失败，记录失败原因，检查对应中间文件是否存在，必要时从失败步骤重新执行，无需从头开始。

