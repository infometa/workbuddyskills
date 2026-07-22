---
name: opinion-query
description: Databrain Intl 舆情查询工具。当用户说"查询 XX 游戏的舆情数据"时触发，使用固定字段查询 opinion_pc/global/query 接口，返回评论、情感、声量等数据。
---

# Opinion Query Skill

## Purpose

当用户想查询某款游戏的舆情数据时使用此 skill。执行两条 SQL 查询，分别获取**官号主贴**和**官帖下的评论数据**，各自保存为本地 CSV 文件。

## Configuration

### Token

Token 从环境变量 `DATABRAIN_TOKEN` 自动读取，**无需额外配置**。

- 若 `DATABRAIN_TOKEN` 为空，前往DataBrain 用户中心 - 个人令牌中心获取 `https://databrain.woa.com/v2/user-center/personal-tokens-center` 获取"授权访问应用-全部应用"的 token（原始值，**不加** `Bearer ` 前缀），设置到系统环境变量 `DATABRAIN_TOKEN`。

### 环境变量

| 变量名 | 是否必填 | 默认值 | 说明 |
|--------|----------|--------|------|
| `DATABRAIN_TOKEN` | 必填 | — | 认证 token 原始值（不含 Bearer 前缀） |
| `DATABRAIN_INTL_HOST` | 可选 | `https://databrain.intlgame.com` | API 主机地址 |

---

## Endpoint

`POST https://databrain.intlgame.com/api/v1/opinion_pc/global/query`

**Request Headers:**

| Header | 说明 |
|--------|------|
| `Content-Type` | `application/json` |
| `Authorization` | `Bearer <DATABRAIN_TOKEN>` |

**Request Body:**

```json
{ "sql": "..." }
```

**Response:**

接口返回 CSV 文件流，`Content-Type: text/csv; charset=utf-8`，**不是 JSON**。

---

## 执行步骤

### 第一步：输入参数格式


| 参数 | 说明 | 示例 |
|------|------|------|
| 游戏名称 | 一个或多个游戏名，用于自动查询 `unified_edition_id` | `Wuthering Waves` |
| 时间范围 | 查询的起止时间，**必须精确到秒**，含起止两端 | `2025-01-01 00:00:00` ~ `2025-03-31 23:59:59` |

若存在参数缺失，**询问用户**，不得自行假设或使用默认值。

**时间格式规则：**
- 格式：`YYYY-MM-DD HH:MM:SS`
- 用户若只提供日期（如"3月1日"），自动补全为当天完整范围：
  - `start_time` → `YYYY-MM-DD 00:00:00`
  - `end_time`   → `YYYY-MM-DD 23:59:59`
- **禁止**使用仅有日期的格式（如 `2026-03-01`），否则会漏掉当天数据。

### 第二步：查询游戏 unified_edition_id

使用 Bash 工具执行，将游戏名称作为参数传入（多个游戏用空格分隔，名称含空格须加引号）：

```bash
PYTHONUTF8=1 python scripts/game_search.py "Game Name 1" "Game Name 2"
```

> ⚠️ **Windows 路径注意：** 必须使用**正斜杠** `/`。

脚本输出 JSON，结构如下：

```json
{
  "games": [
    {
      "keyword": "Elden Ring",
      "game_id": "ebf64ca58f916f7b6033aae4f7f48dd4b",
      "game_name": "Elden Ring | 艾尔登法环",
      "entity_name": "Elden Ring",
      "entity_name_ch": "艾尔登法环",
      "release_time": "2022-02-25",
      "match_score": 100
    },
    ...
  ]
}
```

从结果中提取每个游戏的 `game_id`（即 `unified_edition_id`）和 `entity_name`（用作后续文件命名的 `game_name`）。

**将查询结果展示给用户，仅置信度极低时需要用户确认**，确保整体流程能全自动运行，尽量避免用户在中途手动介入。仅当某个游戏 `game_id` 为空或 `match_score` 极低时，提示用户核实。

### 第三步：逐游戏运行查询脚本

**在开始循环之前，先用 Bash 生成一个统一的 timestamp**，确保所有游戏的文件名使用同一时间戳：

```bash
python -c "import datetime; print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))"
```

将输出结果（如 `20260320_143022`）记为 `<timestamp>`，后续每次调用脚本时作为第五个参数传入。

**对第二步确认过的每个游戏，依次执行一次**，使用各自的 `game_id` 和 `entity_name`：

```bash
PYTHONUTF8=1 python scripts/opinion_query.py "<game_id>" "<entity_name>" "<start_time>" "<end_time>" "<timestamp>"
```

> ⚠️ **Windows 路径注意：** 必须使用**正斜杠** `/`，不得使用反斜杠 `\`。
>
> 有多个游戏时，**串行执行**，等一个完成再执行下一个。

每个游戏输出两个 CSV 文件（文件名以 `entity_name` 的 safe_name 为前缀）：
- `{safe_name}_official_posts_{timestamp}.csv`
- `{safe_name}_post_comments_{timestamp}.csv`

脚本先查官号主贴，再从主贴 comment_id 集合精准查评论（`comment_parent_id IN (...)`），进度日志输出到 stderr，最终将两个 CSV 文件路径以 JSON 输出到 stdout：

```json
{
  "official_posts":  {"path": "/path/to/Honkai_Star_Rail_official_posts_20250301_120000.csv",  "rows": 320},
  "post_comments":   {"path": "/path/to/Honkai_Star_Rail_post_comments_20250301_120000.csv",   "rows": 4821}
}
```

两个文件保存在 `cache/` 目录下。

### 第三步：处理结果

- **成功** → 解析 stdout JSON，得到 `official_posts` 和 `post_comments` 两个文件路径。
  - 告知用户两个文件已保存，路径可供后续流程调用。
  - `official_posts` CSV → event_aggregation 模块的输入（官号主贴聚类）
  - `post_comments` CSV → 仅含官帖下的评论，供 event_aggregation 提取正负面评论
- **失败** → 读取 stderr 的 Error 信息，告知用户原因。

---

## Script Usage

**Helper script:** `scripts/opinion_query.py`

**依赖：** `httpx`

```bash
PYTHONUTF8=1 python scripts/opinion_query.py "u36542a7ff008ac4ab8440c34b8f02f40" "Honkai Star Rail" "2025-01-01 00:00:00" "2025-03-31 23:59:59"
```
