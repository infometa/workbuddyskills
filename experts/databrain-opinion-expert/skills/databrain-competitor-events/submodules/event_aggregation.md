---
name: event_aggregation
description: 竞品事件聚合子模块。从官方帖子 Excel 文件中提取内容，对多语言官方帖子进行聚类去重，识别同一事件的不同地区发帖，输出结构化事件聚类 JSON。触发示例："聚合 XXX 近期事件"、"/event_aggregation XXX"。
---

# 事件聚合 Skill

你是竞品分析流程中的**事件聚合**子模块。你的职责是：从用户提供的帖子数据中，识别并结构化目标游戏的重要事件。

## 输入参数

从 `$ARGUMENTS` 中解析以下参数：
- **游戏名称**（game_name）：如 `Honkai: Star Rail`
- **官号主贴 CSV**（official_posts_csv）：由 opinion-query 模块输出的 official_posts 文件路径，用于事件聚类分析
- **官帖评论 CSV**（post_comments_csv）：由 opinion-query 模块输出的 post_comments 文件路径，含官帖下的玩家评论，用于提取正负面观点
- **时间戳**（timestamp）：由主流程 Step 0 从 CSV 文件名中提取的全局时间戳，格式如 `20250320_143022`


## 执行步骤

### 第一步：数据预处理

首先运行Python脚本 scripts/preprocess_and_preview.py，来预处理官号主贴 CSV中的数据，并提取出需要重点分析的字段。运行时将 `OFFICIAL_POSTS_CSV_PATH` 和 `GAME_NAME` 替换为用户输入的参数。
> `OFFICIAL_POSTS_CSV_PATH` Windows 路径注意：反斜杠须写为正斜杠，例如 `skills/opinion-query/opinion_query_20250301_120000.csv`

使用 Bash 工具执行（将参数替换为实际值，路径反斜杠改正斜杠）：

```bash
PYTHONUTF8=1 python scripts/preprocess_and_preview.py "<official_posts_csv_path>" "<game_name>"
```

捕获输出中 `===POSTS_START===` 和 `===POSTS_END===` 之间的内容作为 `input_post_str`。

### 第二步：事件聚合分析

将第一步得到的 `game_name` 和 `input_post_str` 代入以下 prompt，直接作为你的分析任务执行：

---

You are a professional analyst in the game industry. You will be given a list of official account posts of the game {game_name}. Please follow the steps below to identify the duplicated posts and form clusters:

## Detailed Guidelines:
1. Every official account post is from different regions and might be in various languages. Try your best to understand the meaning of each post from all over the world.

2. Carefully identify duplicated content post one by one.
- The same event's post could be published in different languages as there're many different regions' official accounts of the same game.
- As long as the posts are talking about the same event, they could be identified as duplicated ones.
- No need to apply too strict standards on identifying duplication. Their content don't need to be exactly the same. Similar content about the same event is sufficient to be recognized as duplication.

3. Group duplicated posts together and output grouped clusters based on the indices of the input posts.


## Final Output Instructions
- Present your thinking process and analysis steps first
- The final output part should begin with the mark "### Final Result:", then arrange the clustering results in json array.
- Each cluster result has "event_name" and "member_index_list" two fields.
- Do NOT use any forms of quotation marks inside the "event_name" field values.
- Do not add additional explanation or information after the json array.


Output Format Example:
Some thinking process and analysis steps

### Final Result:
[{
    "event_name": "",
    "member_index_list": [1,3,5]
},
{
    "event_name": "",
    "member_index_list": [2,6]
}]



------------------------------Separation Line -----------------------------------------------------------------------

The actual input list of official account posts is:
{input_post_str}

---

### 第三步：提取结构化结果

**3a. 保存 LLM 原始输出**

将第二步的完整输出文本写入临时文件，供 Python 解析：

```python
import os

# 直接使用主流程传入的全局 timestamp，不重新生成
os.makedirs("cache", exist_ok=True)
safe_name = game_name.replace(" ", "_").replace(":", "")
raw_txt_path = f"cache/_event_agg_llm_raw_{safe_name}_{timestamp}.txt"

llm_raw_output = "<第二步的完整输出文本，原样粘贴>"

with open(raw_txt_path, "w", encoding="utf-8") as f:
    f.write(llm_raw_output)

print(f"Saved raw output: {raw_txt_path}")
```

**3b. 执行结果提取与聚合**

运行Python脚本 scripts/extract_merged_clusters.py，来处理事件聚合的结果。运行时将 `OFFICIAL_POSTS_CSV_PATH`, `ALL_DATA_CSV_PATH` 和 `GAME_NAME` 替换为用户实际输入的参数。
> `CSV_PATH` Windows 路径注意：反斜杠须写为正斜杠，例如 `skills/opinion-query/opinion_query_20250301_120000.csv`

使用 Bash 工具执行（将 `<raw_txt_path>` 替换为步骤 3a 中 print 出的实际路径，`<timestamp>` 替换为主流程传入的全局时间戳）：

```bash
PYTHONUTF8=1 python scripts/extract_merged_clusters.py "<official_posts_csv_path>" "<post_comments_csv_path>" "<game_name>" "<raw_txt_path>" "<timestamp>"
```

执行完成后告知用户输出文件路径。

> 文件名规则：`safe_name = game_name.replace(" ", "_").replace(":", "")`，例如 `Honkai: Star Rail` → `Honkai_Star_Rail`，输出文件为 `cache/_cluster_summary_Honkai_Star_Rail_{timestamp}.json`。online_search 模块使用相同规则读取此文件。

> 此模块输出文件：`cache/_cluster_summary_{safe_name}_{timestamp}.json`，将作为 `/online_search` 子模块的输入。
