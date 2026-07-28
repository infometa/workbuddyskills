---
name: databrain-opinion-metrics
version: 2.1.0
description: 查询游戏舆情核心指标。支持声量、情绪分布、Brand Health、互动量、分渠道/分语种分布、Steam 评论评分、社区指标等。当用户询问游戏的"舆情"、"口碑"、"声量"、"情绪"、"评分"、"社媒表现"、"正负面评价"、"玩家讨论"、"Brand Health"时触发。
author: databrain-team
metadata: {"openclaw": {"requires": {"env": ["DATABRAIN_TOKEN"]}}}
---

# databrain-opinion-metrics

## 快速开始

收到请求时，按以下流程执行：

1. **解析意图** → 确认游戏名称、时间范围、指标类型
2. **确认 game_id** → 若未知，调用 `python scripts/game_search.py "游戏名"` 获取 `unified_edition_id`
3. **查询指标** → 从 `references/` 找到对应 SQL 模板 → 替换 `<game_id>`、`<start_date>`、`<end_date>` → 调用 `python scripts/query_metrics.py --message "用户原始问题" --sql "..." ...` 执行
4. **解读输出** → 解析 JSON `rows` 字段，结合指标口径说明呈现结果

---

# Configuration

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABRAIN_TOKEN` | 是 | — | 认证 token 原始值（**不含** `Bearer ` 前缀），脚本会自动拼接；不要写死在代码中 |
| `DATABRAIN_HOST` | 否 | 自动 fallback | API 主机地址；不设置时自动按优先级尝试 `databrain.intlgame.com` → `databrain.woa.com` → `databrain-global.intlgame.com`，首个成功的会被缓存复用。显式设置后仅使用该地址，仅允许受信任域名（`databrain.woa.com`、`databrain.intlgame.com`、`databrain-*.intlgame.com`） |
| `DATABRAIN_DISPLAY_HOST` | 是 | — | 系统链接展示域名，由平台注入；Agent 构造系统链接时使用（`{DATABRAIN_DISPLAY_HOST}/v2/agent/chat?sessionId=...`），脚本不直接读取 |

Token 自动从环境变量读取。若为空，引导用户前往 `https://databrain.woa.com/v2/user-center/personal-tokens-center` 获取 Databrain Token，设置 `DATABRAIN_TOKEN` 环境变量即可，不要加 `Bearer` 前缀。外网用户可使用 `https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center`。

---

# 数据源

所有可查指标均通过 `POST /api/v1/opinion_pc/global/query`（BigQuery Global Query API）执行，返回 CSV。

| 数据表 | 用途 | 可查性 |
|--------|------|--------|
| `tencent-databrain-prod.opinion.feeds` | 声量、情绪、互动、评论 | ✅ 可查 |
| `store_score_*` 系列 | GP/AS/Steam 商店评分 | ❌ API 无权限，需 BQ 直连 |
| `t_opinion_news` | 新闻稿指标 | ❌ BQ 路径待确认 |

---

# 查询流程

## Step 1：确认 game_id

```bash
python scripts/game_search.py "游戏名"
```

输出示例：
```json
{
  "games": [{"game_id": "e76337e746e1f95fdbf7e23c26010e448", "entity_name": "Dune: Awakening"}]
}
```

- `e...` = PC 游戏，`u...` = 移动游戏

## Step 2：执行查询

从 references 找到 SQL 模板，替换占位符后传入：

```bash
python scripts/query_metrics.py \
  --message "用户原始问题" \
  --sql "SELECT ..." \
  --game_id e76337e746e1f95fdbf7e23c26010e448 \
  --start_date 2026-03-24 \
  --end_date   2026-03-30
```

或从文件读取 SQL：

```bash
python scripts/query_metrics.py \
  --sql_file /tmp/query.sql \
  --game_id e76337e746e1f95fdbf7e23c26010e448 \
  --date 2026-03-30
```

## Step 3：解读输出

```json
{
  "game_id": "e76337e746e1f95fdbf7e23c26010e448",
  "start_date": "2026-03-24",
  "end_date":   "2026-03-30",
  "rows": [{"date": "2026-03-24", "volume": "1127"}, ...],
  "row_count": 7
}
```

如需 CSV 格式，追加 `--format csv`。

---

# 新增指标（无需改代码）

在对应数据表的 reference 文件末尾追加 SQL 模板即可，无需修改脚本：

- `opinion.feeds` 相关 → 追加到 `references/feeds_templates.md`
- 新增数据表 → 新建 `references/<table_name>_templates.md`

---

# 安全说明

`query_metrics.py` 在执行前做如下校验：

1. `--game_id` 格式：`^[ue][0-9a-f]+$`
2. 日期格式：`^\d{4}-\d{2}-\d{2}$`
3. SQL 不得含 DDL/DML 关键词（`DROP`、`DELETE`、`INSERT`、`UPDATE`、`CREATE`、`ALTER` 等）
4. `DATABRAIN_HOST` 只允许受信任域名
5. Token 仅通过环境变量注入，不接受命令行传入

---

# 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `DATABRAIN_TOKEN not set` | 未注入 token | 通过服务端环境变量注入 |
| `DATABRAIN_HOST 不是受信任域名` | host 不在白名单 | 使用 `databrain.*.woa.com` 或 `databrain*.intlgame.com` |
| `Invalid game_id` | ID 格式不符 | 用 `game_search.py` 重新查询 |
| `SQL contains forbidden keyword` | SQL 含 DDL/DML | 检查模板 SQL，只允许 SELECT |
| `row_count: 0` | 该游戏在该时间范围内无数据 | 确认游戏平台和日期范围 |
| `ModuleNotFoundError: httpx` | 未安装依赖 | `pip install httpx` |

---

# 补充资源

- 声量/情绪/互动基础 SQL → [references/feeds_templates.md](references/feeds_templates.md)（Step 2 构造查询时读取；包含表 Schema、关键字段说明）
- Mentions & Sentiment 全量指标口径 → [references/mentions_sentiment.md](references/mentions_sentiment.md)（需要 DoD、Brand Health、情感分等复杂指标时读取）
- 社区指标（曝光/发帖/创作者/观看/互动）→ [references/community.md](references/community.md)（查询 Community 模块指标时读取；注意官号/玩家内容字段待确认）
- Game Store 评论评分 → [references/game_store.md](references/game_store.md)（查询 Steam 评论时读取；其他平台评分暂不可查）
- PR & News 指标 → [references/pr_news.md](references/pr_news.md)（❌ BQ 表名待确认，当前不可执行）
- Social 过滤逻辑（官号/关键词/账号分类）→ [references/social_filter_logic.md](references/social_filter_logic.md)（需要按账号类型过滤时读取）
- Hashtag 趋势查询 → [references/hashtag_trending.md](references/hashtag_trending.md)（⚠️ BQ 表路径待确认）
- Meme 热梗查询 → [references/meme.md](references/meme.md)（⚠️ 使用 tencent-databrain 非 prod 项目，待确认）
- 商店评分 SQL 口径 → [references/store_score_templates.md](references/store_score_templates.md)（❌ API 无权限，需 BQ 直连）
- 查询脚本 → [scripts/query_metrics.py](scripts/query_metrics.py)（Step 3 执行 SQL 时调用）
- 游戏 ID 查询脚本 → [scripts/game_search.py](scripts/game_search.py)（game_id 未知时调用）
