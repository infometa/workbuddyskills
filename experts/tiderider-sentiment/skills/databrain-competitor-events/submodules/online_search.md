---
name: online_search
description: 竞品游戏联网搜索子模块。基于游戏官方帖子事件列表，通过联网搜索澄清帖子中的游戏专属背景知识（角色、活动、版本内容等），为后续深度分析模块提供上下文支撑。可单独调用测试，也可作为 competitor_report 流程的 Step 2。触发示例："搜索 XXX 相关信息"、"/online_search XXX"。
---

# 联网搜索信息 Skill (子模块)

你是竞品游戏分析流程中的**联网搜索**子模块。

分析对象是**竞品游戏的官方社媒账号帖子**，这些帖子通常与游戏宣传、版本更新、角色上线、运营活动或社区互动相关。

你的核心职责是：**通过联网搜索澄清帖子中出现的游戏专属背景知识**，让后续总结分析的步骤能够真正读懂每个事件在说什么——它涉及哪个角色、什么活动、属于哪类运营动作。

## 输入参数

- **game_name**：待分析的游戏名称
- **input_file**：事件聚合模块输出的 JSON 文件路径，默认为 `cache/_cluster_summary_{safe_name}_{timestamp}.json`
- **timestamp**：由主流程 Step 0 从 CSV 文件名中提取的全局时间戳，格式如 `20250320_143022`

若作为 `/competitor_report` 子步骤调用，直接读取上一步生成的文件。

若作为独立模块被单独调用，从 `$ARGUMENTS` 中解析以下两个参数（用户会以空格或逗号分隔传入）。如果参数格式不清晰，先向用户确认这两个参数再继续。

## 执行步骤

### 第一步：读取并解析输入数据

使用 Read 工具读取输入 JSON 文件，解析为事件列表。重点关注每个事件中的以下字段：
- `event_name`：事件名称
- `highlight_content`：代表性帖子原文
- `total_engagement`：该事件的总互动量
- `all_comment_ids`：相关帖子 ID 列表

### 第二步：为每个事件准备搜索 Query

对每个事件的 `highlight_content`，识别其中需要背景知识才能理解的内容，重点关注：
- 游戏角色名、NPC 名（这是什么角色？什么定位？）
- 活动什么时候发布，发布内容是什么
- 活动名、版本名、卡池名
- 游戏内地名、世界观名词
- 含义与日常语义不同的术语或黑话
- hashtag 中出现的游戏专属词汇

基于以上分析，为每个事件准备 1-3 条 WebSearch query，目标是搜索到这些词汇的背景知识，弄清楚帖子在说什么事情、涉及哪类游戏内容。

**Query 构造原则：**
- 包含游戏名 + 需要澄清的专有名词
- 例："Honkai Star Rail Evanescia character"、"Honkai Star Rail Trailblazer Elation path"

### 第三步：逐事件执行联网搜索

按 `total_engagement` 从高到低的顺序处理每个事件（高互动事件优先）。

对每个事件依次：
1. 执行第二步准备好的 queries，使用内置 **WebSearch 工具**（无需任何额外 API 配置）
2. 从搜索结果中提取有价值的信息，**重点关注**：
   - **活动/内容发布时间**：该事件对应的活动或内容在游戏内/官方渠道的上线日期
   - **活动/内容发布详情**：具体发布了什么（版本更新、角色上线、限时活动、联动内容等）
   - 其他背景知识：涉及角色、世界观、玩法机制等


**专有名词翻译规则（严格执行）：**

整合搜索结果时，对帖子中出现的游戏专属名词（角色名、活动名、地名等）：
- **仅当**搜索来源中有**明确的中文译名**时，才在背景说明中附上中文翻译
- 若搜索结果中未出现官方或公认的中文译名，**一律保留帖子原文中的语言形式**，不得自行推测或意译
- 禁止基于语义或发音自行翻译专有名词，错误翻译比不翻译危害更大

### 第四步：整合结果并保存输出

**4a. 整合搜索结果并保存**
将每个事件的搜索结果整合后，使用传入的全局 `timestamp`（不重新生成），确保 `cache/` 目录存在，然后将每个事件和搜索结果相关的三个字段：`search_queries`、`search_findings`、`sources` 作为 JSON 对象汇总写入，格式为 JSON 数组，顺序与输入事件列表一致：

- 注意：清理去除保存内容中任何存在的双引号，否则存入json value时会导致json格式报错。

```
safe_name = game_name.replace(" ", "_").replace(":", "")
search_result_path = f"cache/_search_results_raw_{safe_name}_{timestamp}.json"
```

```json
[
  {
    "search_queries": ["<query1>", "<query2>"],
    "search_findings": "<整合后的搜索发现，包括事件详情、背景、数据>",
    "sources": ["<url1>", "<url2>"],
    "event_release_date": "<活动/内容的官方发布日期，格式 YYYY-MM-DD；若搜索无结果或帖子非活动发布则填 'N/A'>",
    "event_release_content": "<活动/内容的具体发布详情（版本更新、角色上线、限时活动、联动等）；若帖子为社区互动或梗传播等非发布内容则填 'N/A'>"
  },
  { ... }
]
```

**`event_release_date` 和 `event_release_content` 的填写规则（严格执行）：**
- 仅在搜索结果中有**明确证据**时填入具体内容
- 以下情况一律填 `"N/A"`：
  - 搜索未找到该活动/内容的发布信息
  - 帖子本身属于社区互动、梗图传播、用户创作等非官方发布内容
  - 发布日期不确定或来源不可信
- 禁止推断或凭记忆填写，宁可 `"N/A"` 也不填错

**4b. 与原始输入json文件融合**

运行Python脚本 scripts/save_online_search.py，来融合搜索结果和输入json文件。运行时将 `input_json_path`, `search_result_path` 和 `game_name` 替换为用户实际输入的参数。
> Windows 路径注意：反斜杠须写为正斜杠，例如 `codes/Star_Rail_example.json`

使用 Bash 工具执行：

```bash
PYTHONUTF8=1 python scripts/save_online_search.py "<input_json_path>" "<search_result_path>" "<game_name>" "<timestamp>"
```

> 文件名规则：`safe_name = game_name.replace(" ", "_").replace(":", "")`，例如 `Honkai: Star Rail` → `Honkai_Star_Rail`，输出文件为 `cache/_online_search_Honkai_Star_Rail_{timestamp}.json`。

> 此模块输出文件：`cache/_online_search_{safe_name}_{timestamp}.json`，将传递给后续总结分析的步骤进行深度分析。
