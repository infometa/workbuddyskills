---
name: databrain-opinion-summary
version: 1.4.0
description: 通过 Databrain 生成指定游戏、时段的舆情 AI 总结报告，快速掌握玩家讨论的核心观点与口碑趋势。在用户需要「舆情总结」「口碑摘要」「玩家讨论总结」「AI 解读评论」「一段时间内的舆情报告」时使用；需先解析游戏名得到 game_id 与平台类型。
author: databrain-team
metadata: {"openclaw": {"requires": {"env": ["DATABRAIN_TOKEN"]}}}
---

# databrain-opinion-summary

## 快速开始

1. **解析意图** → 确认游戏名称、时间范围、报告语言（中/英）、可选渠道/语种过滤、摘要类型（默认 `basic`，约 1–5 分钟；用户明确要量化数据时用 `advanced`，可能长达 30 分钟，**启动前须向用户说明**）
2. **确认 game_id 与平台** → 若未知，在本 skill 下执行 [scripts/game_search.py](scripts/game_search.py) 查询 `game_id`（即 `unified_edition_id`）
   - `game_id` 以 **`u` 开头** → `--entity_type mobile`
   - **`e` 开头** → 一般为 `--entity_type pc`；若为主机版且与 PC 版区分配置，再选 `console`
3. **创建并拉取报告** → 执行 `scripts/get_opinion_summary.py`（`POST .../create_summary` → 轮询 `.../get_summary` 至 `task_status == success`）；**建议传入 `--message` 用户原问题** 以便 operationLog 打点。`create_summary` **必须**带 `date_type`（脚本默认 `day`，适用于「单日 / 昨日」）；跨多天时按需改用 `--date_type week|month|custom`
4. **呈现结果** → **将脚本 stdout 原文直接输出给用户，不要二次总结或改写**；报告正文由后端 AI 生成，已含话题分类、评论量、互动量及跳转链接，改写会丢失关键数据；需要结构化字段时加 `--json`

---

## 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|--------|
| `DATABRAIN_TOKEN` | 是 | 认证 token；脚本中自动加 `Bearer `，不要带前缀写在命令行 |
| `DATABRAIN_HOST` | 否 | 显式 API 根 URL；不设则按 `databrain.intlgame.com` → `databrain.woa.com` → `databrain-global.intlgame.com` 尝试，与 `databrain-opinion-metrics` 一致 |
| `DATABRAIN_DISPLAY_HOST` | 视平台而定 | 若需拼系统链接，由平台注入 |

Token 获取可参考舆情指标 skill：内网 `https://databrain.woa.com/v2/user-center/personal-tokens-center`，外网 `https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center`。

---

## Step 1：游戏 ID（本 skill 内 `game_search`）

在本 skill 根目录：

```bash
cd skills/databrain-opinion-summary

python scripts/game_search.py "游戏中文或英文名"
```

从 stdout 的 JSON 中取命中的 `game_id` 与 `entity_name` / `game_name`；**默认每个关键词只返回 Top1**，存在歧义时向用户确认。若存在 `error` 字段或 `game_id` 为 `null`，勿传入摘要脚本。

输出示例：

```json
{
  "games": [
    {
      "keyword": "某游戏",
      "game_id": "e76337e746e1f95fdbf7e23c26010e448",
      "entity_name": "Example Game"
    }
  ]
}
```

（实现与 `databrain-opinion-metrics/scripts/game_search.py` 一致，便于本 skill 自包含。）

---

## 摘要模式选择

> **选择原则**：默认走 `basic`，用户明确要求量化数据时才走 `advanced`，并提前告知等待时间。

| 模式 | 何时使用 | 内容 | 预计等待 |
|------|---------|------|---------|
| `basic`（**默认**） | 用户未特别说明时 | 正面 / 负面 / 中性话题摘要 + 可执行建议 | **约 1–5 分钟** |
| `advanced` | 用户**明确要求量化分析**时 | 在 basic 基础上，每条话题额外附带**评论量、互动量、点赞数**（如 `(357 Comments) [Engagement: 22714]`） | **可能长达 30 分钟**，视数据量而定 |

启动 `advanced` 前，**务必向用户说明可能需要较长时间等待**，避免误解任务卡住。

---

## Step 2：生成舆情摘要报告

```bash
cd skills/databrain-opinion-summary

python scripts/get_opinion_summary.py \
  --game_id e76337e746e1f95fdbf7e23c26010e448 \
  --entity_type pc \
  --start_date 2026-04-08 \
  --end_date 2026-04-08 \
  --date_type day \
  --message "用户原始问题" \
  --output_lang zh
```

常用可选参数：

| 参数 | 说明 |
|------|------|
| `--message` | 用户原始问题，用于 `operationLog` 埋点（**建议总是传入**） |
| `--date_type` | `create_summary` 必填粒度，默认 `day`（昨日/单日）；多日范围可试 `week` / `month` / `custom` |
| `--language zh en` | 只分析指定语种评论 |
| `--channel twitter reddit steam` | 只分析指定社媒渠道 |
| `--top_n 10` | 各维度 Top N，默认 10 |
| `--output_lang en` | 报告输出语言；默认 `zh`，**欧美/全球游戏建议传 `en`** |
| `--task_type advanced` | 高级量化总结（含评论量、互动量等量化数据）；用户明确要求时传入；可配合 `--prompt` 自定义 |
| `--json` | stdout 输出完整 `get_summary` 的 `data` JSON，便于解析 |

`id_type`（`unified_id` / `edition_id` / `unified_edition_id`）由脚本根据 `entity_type` 与 `game_id` 长度自动选择。

---

## 安全说明

`get_opinion_summary.py` 在执行摘要请求前校验：

1. `--game_id` 格式：`^[ue][0-9a-f]+$`
2. `--start_date` / `--end_date`：`YYYY-MM-DD`，且 `end_date >= start_date`
3. `DATABRAIN_HOST` 仅允许受信任域名（与 metrics / game_search 一致）
4. Token 仅通过环境变量注入，不接受命令行传入

---

## API 说明（脚本已实现）

| 步骤 | 方法 | 路径 |
|------|------|------|
| 创建任务 | POST | `/api/v1/opinion_pc/summary/advanced/create_summary` |
| 查询结果 | POST | `/api/v1/opinion_pc/summary/advanced/get_summary` |

请求体须包含 **`date_type`**（蛇形命名，如 `day`），**不要**使用 `DateType` 等错误字段名；缺省会导致 **HTTP 400**（校验提示 EditionUnifiedId / DateType 等，实为 JSON 字段未按约定绑定）。

创建成功返回 `task_id`；轮询直至 `task_status` 为 `success`，响应中含 `report_zh` / `report_en`。

---

## 依赖与本地开发

```bash
pip install -r requirements.txt
```

可在本 skill 根目录放置 `.env` 供本地调试（与 metrics skill 相同约定；服务端仍以环境变量为准）。

---

## 常见问题

| 现象 | 处理 |
|------|------|
| `DATABRAIN_TOKEN not set` | 注入 token |
| `Invalid game_id` | 使用 `game_search.py` 重新查询，确保为 `u`/`e` 开头的 hex |
| `Invalid --start_date` / `--end_date` | 使用 `YYYY-MM-DD` |
| `game_search` 返回 `game_id: null` | 换关键词或确认游戏是否收录 |
| `create_summary` 全域名 **HTTP 400**、提示 DateType / edition 相关 | 确认 payload 含 **`date_type`**（默认脚本已传）；字段名须为 snake_case，勿用驼峰 `DateType` |
| 多域名均 create 失败（非 400） | 检查网络、token 权限、游戏是否在舆情侧可查 |
| 长时间 `task_status` 非 success | `basic` 正常 1–5 分钟，`advanced` 可达 30 分钟；脚本最长等待约 7200s；属正常现象，请等待 |
| `task_status` 为 `failed` / `error` | 队列或生成失败；可稍后重试（advanced 失败可降级为默认 basic 重试） |
| 正文为空 | 尝试 `--json` 查看原始字段；或切换 `--output_lang` |

---

## 打包与分发（清单）

独立分发本 skill 时建议包含：

- `SKILL.md`、`requirements.txt`、`.gitignore`（可选）
- `scripts/get_opinion_summary.py`、`scripts/game_search.py`、`scripts/report_log.py`

运行要求：**Python 3.9+**（脚本使用内置类型注解语法）。安装依赖：`pip install -r requirements.txt`。**勿**将含 `DATABRAIN_TOKEN` 的 `.env` 打入制品。

工作目录：必须在 skill 根目录执行 `python scripts/...`，以便 `get_opinion_summary` 与同目录下的 `report_log` 可互相 import。

「相关资源」中指向仓库内其他 skill 的链接在**仅拷贝本目录**时可能失效，属可选参考，不影响本包内脚本运行。

---

## 相关资源

- 摘要脚本 → [scripts/get_opinion_summary.py](scripts/get_opinion_summary.py)
- 游戏 ID 查询 → [scripts/game_search.py](scripts/game_search.py)
- 打点（内嵌，Agent 无感知） → [scripts/report_log.py](scripts/report_log.py)
- 同类设计参考 → [../databrain-opinion-metrics/SKILL.md](../databrain-opinion-metrics/SKILL.md)
- 原始实现参考（同 API）→ [../opinion-query-slow/scripts/get_opinion_report.py](../opinion-query-slow/scripts/get_opinion_report.py)
