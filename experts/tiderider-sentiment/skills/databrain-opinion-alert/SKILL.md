---
name: databrain-opinion-alert
version: 2.2.0
description: 游戏舆情告警 Skill。监控游戏口碑指标并推送企业微信告警。当前主推「商店评分告警 v2」（Steam / Google Play / App Store 三渠道，P0/P1/P2 三级，支持分语种/分国家全切片自动评估、四维触发条件、静默期、归因），保留向后兼容的 KOL 热帖告警与关键词声量告警。当用户需要「设置舆情告警」「监控游戏评分」「评分下滑通知」「KOL 热帖预警」「关键词监控」「定时推送舆情」时使用。
author: databrain-team
metadata: {"openclaw": {"requires": {"env": ["DATABRAIN_TOKEN"]}}}
---

# databrain-opinion-alert

## 1. 能力总览

| 告警类型 | 状态 | 触发条件 | 适用场景 |
|---------|------|---------|---------|
| **商店评分告警 v2**（重点） | ✅ 主推 | P0/P1/P2 三级 × 四维触发条件（绝对水位/相对下跌/历史基准/样本量），支持全切片评估 | 版本更新后实时监控玩家口碑、按国家/语种定位异常 |
| KOL 热帖告警 | ✅ 兼容 | 出现超高互动量帖子（可过滤负面情绪） | 捕捉病毒式传播的舆情事件 |
| 关键词声量告警 | ✅ 兼容 | 特定词汇当日讨论量超过历史均值的 N 倍 | 监控特定议题（如"崩溃"、"封号"） |

> 商店评分告警 v2 是依据 [新版告警模板](舆情告警模版.md) 重写的版本。详细技术设计见 [references/store_score_alert.md](references/store_score_alert.md)。

---

## 2. 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABRAIN_TOKEN` | 是 | — | 认证 token 原始值（**不含** `Bearer ` 前缀），脚本会自动拼接；不要写死在代码中 |
| `DATABRAIN_HOST` | 否 | 自动 fallback | API 主机地址；不设置时自动按优先级尝试 `databrain.intlgame.com` → `databrain.woa.com` → `databrain-global.intlgame.com`，首个成功的会被缓存复用。显式设置后仅使用该地址，仅允许受信任域名（`databrain.woa.com`、`databrain.intlgame.com`、`databrain-*.intlgame.com`） |
| `OPINION_ALERT_QUERY_INTERVAL` | 否 | `3.0` | Global Query API 请求间隔（秒）；脚本默认节流以降低 HTTP 566 / 200 空 body 风险 |

Token 自动从环境变量读取。若为空，引导用户前往 `https://databrain.woa.com/v2/user-center/personal-tokens-center` 获取 Databrain Token，设置 `DATABRAIN_TOKEN` 环境变量即可，**不要**加 `Bearer` 前缀。外网用户可使用 `https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center`。

脚本请求 Databrain API 时会自动添加请求头：`Authorization: Bearer <DATABRAIN_TOKEN>`。当前测试结果：`databrain.intlgame.com` 与 `databrain-global.intlgame.com` 可直接使用 Databrain Token 访问 Global Query API；`databrain.woa.com` 在未完成 WOA SSO 登录时会跳转到 `std.passport.woa.com`。

---

## 3. 商店评分告警 v2（推荐使用）

### 3.1 设计要点

- **三渠道**：`steam` / `google_play` / `app_store`
- **三等级**：`P0`（严重，立即处理）/ `P1`（警告）/ `P2`（关注）
- **四维触发**（任一命中且样本量达标 → 触发）：
  - **A 绝对水位**：Steam 看好评率，Google Play / App Store 看 0-5 星评分（另含一星占比）
  - **B 相对下跌**：6h / 24h 内显著下跌
  - **C 历史基准**：低于 30 天 P5 / P25 或 7 天中位数
  - **样本量门槛**：每个等级独立 `min_sample`，不达标 → 跳过该等级
- **全切片评估**：Steam 评估「全球聚合 + 官方语言切片」，默认语言优先级为 `EN / JA / KO / ZH-CN / DE / FR / RU / ES / PT-BR`，并支持 `custom_languages` 自定义语种维度；Google Play 评估「全球聚合 + 分国家切片」；App Store 按国家独立评估，**不做全球均分**（避免单一市场崩盘被稀释）
- **静默期 + 升级打破**：每个 `(game_id, channel, scope, slice_key)` 独立维护静默期；P2→P1→P0 升级会立即打破当前静默
- **归因**：触发时附加 6h 窗口的高频投诉来源（Steam 用 Top 语种；Google Play / App Store 用 Top 国家/地区）+ 代表性差评（每条都带可点击原帖 URL，无 URL 的样本被 SQL 过滤掉）。Steam 代表性差评链接优先取 `content_url`，再 fallback 到 `sources.url`
- **HTML 详情页**（v2.1+）：触发时自动生成自包含 HTML，含 5 区块（摘要 / 全切片表格 / 30 天 SVG 趋势图 / 归因与差评链接 / 折叠原始 JSON），企业微信消息中带 `📄 查看完整详情` 链接
- **告警文案**：商店评分告警 v2 必须由 `scripts/alert_message_renderer.py` 生成，并严格遵循 `舆情告警模版.md §1.3` 的 6 段格式；不要在 agent prompt 或其他脚本里另写自由拼接逻辑

### 3.2 输入参数

| 变量 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `GAME_NAME` | 是 | 游戏名（用于查 game_id） | `PUBG Mobile` |
| `CHANNEL` | 是 | 渠道 | `steam` / `google_play` / `app_store` |
| `SCOPE` | Steam 必填 | 评分口径 | `all_reviews` / `recent_reviews` |
| `PUSH_TARGET` | 否 | 默认由 bot 投递到当前会话/当前群；配置完成时必须同步告知用户可通过“消息推送”或“告警机器人”推送到群 | 当前会话 |
| `WEBHOOK_URLS` | 否 | 仅当用户明确选择企业微信机器人直推时使用；多个用 `;` 分隔 | `https://qyapi.weixin.qq.com/...` |
| `INTERVAL` | 否 | 巡检频率 | `15min` / `1h` / `6h` / `24h`（默认 `1h`） |
| `THRESHOLDS_FILE` | 否 | 阈值配置 YAML 路径 | 默认 `thresholds.yaml` |

> 阈值在 `thresholds.yaml` 里集中维护，按 `game_id` 深合并覆盖。无需逐次询问用户。
> 口径说明：Steam 阈值单位是好评率百分比（如 `absolute_pp: 75` = 好评率 < 75%）；Google Play / App Store 阈值单位是评分 0-5（如 `absolute_score: 3.5` = 评分 < 3.5），不要描述成“好评率”。

### 3.3 流程

1. **确认参数** → 收集 `GAME_NAME`、`CHANNEL`、（Steam 时）`SCOPE`、巡检频率；默认不要求 webhook
2. **获取 game_id** → 若未知，执行 `python scripts/game_search.py "<游戏名>"` 获取 `unified_edition_id`
3. **（可选）调阈值** → 编辑 `thresholds.yaml` 的 `overrides.<game_id>` 节点；省略则用 `defaults`
4. **执行评估** → `check_store_score_alerts.py` 输出 `/tmp/alert_result.json`
5. **（可选）做归因** → `attribution.py` 输出 `/tmp/attribution.json`（仅触发时执行）
6. **推送** → 默认由 bot 定时任务投递告警结果；若用户提供 `WEBHOOK_URLS`，可额外调用 `send_alert.py --webhook_url` 直推企业微信群

### 3.4 命令样例

```bash
cd skills/databrain-opinion-alert

# Step 1: 找 game_id
python scripts/game_search.py "PUBG Mobile"

# Step 2: 评估（Google Play 示例）
python scripts/check_store_score_alerts.py \
  --game_id ufc454d9b1af70b40588e2a6fa4da4a8b \
  --channel google_play \
  --output /tmp/alert_result.json \
  --message "PUBGM Google Play 评分巡检"

# Steam 示例（需要 --scope）
python scripts/check_store_score_alerts.py \
  --game_id e7f672beaa5fddd166df98bc046ba4bd4 \
  --channel steam --scope all_reviews \
  --output /tmp/alert_result.json

# Step 3: 归因（仅触发时执行）
python scripts/attribution.py \
  --game_id ufc454d9b1af70b40588e2a6fa4da4a8b \
  --channel google_play --hours 6 \
  --output /tmp/attribution.json

# Step 4: 生成推送内容（preview 模式不发送；默认生成 HTML 并用当前用户 token 挂载到 AI Gallery）
python scripts/send_alert.py \
  --result_file /tmp/alert_result.json \
  --attribution_file /tmp/attribution.json \
  --game_name "PUBG Mobile"
# 自动产物：Markdown 告警内容 + 本地 HTML + 当前用户账号下的 AI Gallery 详情链接，消息中以 [查看详情](...) 展示

# 可选：用户明确选择企业微信机器人直推时再传 webhook
python scripts/send_alert.py \
  --webhook_url "$WEBHOOK_URL" \
  --result_file /tmp/alert_result.json \
  --attribution_file /tmp/attribution.json \
  --game_name "PUBG Mobile"

# 仅生成 HTML（不推送，调试用）
python scripts/render_html.py \
  --result_file /tmp/alert_result.json \
  --attribution_file /tmp/attribution.json \
  --game_name "PUBG Mobile" \
  --output /tmp/alert_detail.html
open /tmp/alert_detail.html
```

#### HTML 详情页相关参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--no_html` | - | 关闭 HTML 详情页生成 |
| `--no_gallery` | - | 不使用当前用户 token 挂载 AI Gallery，仅保留本地 HTML / 自托管链接 |
| `--html_dir` | `/tmp` | HTML 输出目录 |
| `--detail_url_base` | 空（默认 AI Gallery） | 自托管时填 base URL（如 `http://oa.intra/alerts/`），显式覆盖默认 Gallery 链接 |

默认会调用 `scripts/publish_gallery_html.py`，使用当前用户的 `DATABRAIN_TOKEN` 将详情页挂载到 AI Gallery，并保持 `visibility=self`。发布出的作品归属当前用户账号；若当前用户没有 Gallery 创建/访问权限或发布失败，脚本会降级保留本地 HTML 链接并继续生成告警文案，避免详情页发布问题阻断告警。

### 3.5 阈值配置（thresholds.yaml）

完整配置和默认值见 [references/store_score_alert.md](references/store_score_alert.md#thresholds-yaml)。摘要：

```yaml
slicing:
  steam:
    by_language: true
    language_priority: [EN, JA, KO, ZH-CN, DE, FR, RU, ES, PT-BR]
    custom_languages: []             # 可写标准代码或 language_reviews 原始 key
    include_unlisted_languages: true  # priority/custom 之外的语种排在最后继续评估
    exclude_languages: []             # 可写标准代码或 language_reviews 原始 key
  google_play:  { by_country:  true, exclude_areas: [] }   # 可加 'lang_*' 屏蔽伪国家码
  app_store:    { by_country:  true, exclude_areas: [] }

silence_seconds: { P0: 3600, P1: 7200, P2: 21600 }

defaults:
  steam:
    all_reviews:
      P0: { absolute_pp: 60, drop_6h_pp: 5, baseline: p5,        min_sample: 100 }
      P1: { absolute_pp: 75, drop_6h_pp: 2, baseline: p25,       min_sample: 50  }
      P2: { absolute_pp: 80, drop_24h_pp: 1, baseline: median_7d, min_sample: 20  }
  google_play: ...
  app_store:   ...

overrides:
  e7f672beaa5fddd166df98bc046ba4bd4:   # 仅写要改的字段，深合并
    steam:
      all_reviews:
        P0: { absolute_pp: 55 }
```

默认阈值口径：
- Steam：P0/P1/P2 使用 `absolute_pp`，代表好评率低于对应百分比阈值。
- Google Play / App Store：P0/P1/P2 使用 `absolute_score`，默认分别为评分低于 `3.0 / 3.5 / 4.0`；同时 P0/P1 可用 `one_star_rate` 监控一星占比。

### 3.6 默认定时推送机制

告警默认走 bot 定时巡检和投递，不把企业微信 webhook 作为必填项。用户说“帮我配置告警”时，优先完成 game_id、渠道、阈值和巡检频率配置，并必须同步告知用户：

> 已配置为 bot 定时巡检。触发告警时会在当前会话/当前群里推送告警卡片；如需推送到指定群，可在平台侧配置“消息推送”或“告警机器人”，也可以补充企业微信机器人 webhook 做直推。

`INTERVAL=1h` 时建议 cron 每 1 小时巡检一次：

```
jobName: store-score-alert-{game_id}-{channel}
cronExpression: 0 * * * *      # 每小时整点
jobMessage: |
  cd skills/databrain-opinion-alert
  python scripts/check_store_score_alerts.py \
    --game_id {game_id} --channel {channel} {--scope all_reviews 仅 steam} \
    --output /tmp/alert_{game_id}_{channel}.json \
    --message "每{interval}巡检 {game_name}"

  # 仅触发时做归因 + 生成告警内容，bot 负责把本次输出投递到当前会话/群
  if jq -e .triggered /tmp/alert_{game_id}_{channel}.json >/dev/null; then
    python scripts/attribution.py \
      --game_id {game_id} --channel {channel} --hours 6 \
      --output /tmp/attr_{game_id}_{channel}.json
    python scripts/send_alert.py \
      --result_file /tmp/alert_{game_id}_{channel}.json \
      --attribution_file /tmp/attr_{game_id}_{channel}.json \
      --game_name "{game_name}"
  fi

delivery.mode: "announce"
delivery.channel: "<当前渠道>"
delivery.to: "<当前用户ID或群ID>"
```

> 群推送说明：默认使用当前 bot 的定时投递能力。每次完成告警配置时，都要同步告知用户可在 WorkBuddy / 平台侧配置“消息推送”或“告警机器人”绑定目标群；只有用户明确提供企业微信机器人 webhook 时，才在 `send_alert.py` 中增加 `--webhook_url`。

> ⚠️ 电脑休眠期间定时任务暂停，唤醒后恢复（系统限制）。

---

## 4. 其它告警（KOL 热帖 / 关键词告警）

> 评分告警的旧实现（`check_alerts.py --alert_type rating`）已被 v2 取代；KOL 保持兼容，关键词告警已升级为 v2 模板。

### 4.1 KOL 热帖告警

```bash
python scripts/check_alerts.py \
  --game_id <game_id> \
  --alert_type kol \
  --start_date 2026-04-13 --end_date 2026-04-13 \
  --threshold 10000 \
  --kol_sentiment_filter \
  --output /tmp/alert_result.json
```

`--threshold` 为最低 engagement；`--kol_sentiment_filter` 仅告警 `sentiment_rating ≤ 2`。

### 4.2 关键词告警 v2

```bash
python scripts/check_alerts.py \
  --game_id <game_id> \
  --alert_type keyword \
  --start_date 2026-04-13 --end_date 2026-04-13 \
  --threshold 3.0 \
  --keywords "crash,hack,ban" \
  --window_hours 24 \
  --sensitivity medium \
  --viral_threshold 500 \
  --user_id <user_id> \
  --output /tmp/alert_result.json
```

关键词匹配口径为 `keywords` NLP 字段 **或** 正文模糊匹配（`content_to_zh/content`），可覆盖 `AZ3` 这类版本热词尚未进入 NLP keywords 的场景。

触发维度：
- `mention_spike`：当前窗口提及量 ≥ 历史基准 × `--threshold`，且 ≥ 最小绝对量。
- `negative_ratio`：负面占比达到 `--sensitivity` 阈值，并高于历史负面基准 5pp。
- `viral_post`：24h 内单帖互动量 ≥ `--viral_threshold`。

危机词配置在 [keyword_crisis_terms.yaml](keyword_crisis_terms.yaml)。命中危机词时会自动识别类别和默认等级：
- P1：外挂作弊、封号争议、付费争议。
- P0：数据安全、停服跑路、法律舆论。

关键词告警静默规则：静默时长 = `--window_hours`；状态 key 为 `user_id + game_id + keyword_group + trigger_dimension`。同一关键词组的不同触发维度互不影响；相似关键词组不做跨组聚合去重。

### 4.3 不确定阈值？

```bash
python scripts/calc_threshold.py \
  --game_id <game_id> \
  --alert_type kol --lookback_days 30
```

详见 [references/threshold_guide.md](references/threshold_guide.md)。

---

## 5. 推送（共用）

```bash
python scripts/send_alert.py \
  --webhook_url "https://qyapi.weixin.qq.com/...;..." \
  --result_file /tmp/alert_result.json \
  --attribution_file /tmp/attribution.json \   # 可选，仅商店评分告警
  --game_name "<游戏名>"
```

`send_alert.py` 自动识别输入是「商店评分告警 v2」还是「旧版 KOL/keyword」。商店评分告警 v2 的企业微信 Markdown 由 `scripts/alert_message_renderer.py` 统一生成，并在推送前执行 6 段格式校验；不要在 agent prompt 或其他脚本里另写自由拼接逻辑。

> 调试时加 `--preview_only` 打印 markdown 不发送。

---

## 6. 安全说明

- `--game_id` 校验：`^[ue][0-9a-f]+$`
- `thresholds.yaml` 中 `overrides` 仅允许字段级深合并，不允许新增 channel
- `--keywords` 不允许 SQL 特殊字符（`'`, `"`, `;`, `--`）
- Token 仅通过环境变量 `DATABRAIN_TOKEN` 注入；脚本请求时自动追加 `Authorization: Bearer <token>`
- `DATABRAIN_HOST` 仅允许受信任域名：`databrain.woa.com`、`databrain.intlgame.com`、`databrain-*.intlgame.com`
- Global Query SQL 在发送前会压成单行，避免网关对多行 SQL 返回 `HTTP 200` 但 body 为空

---

## 7. 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `DATABRAIN_TOKEN 未设置` | 未注入 token | 通过系统环境变量注入 token 原始值 |
| `DATABRAIN_HOST ... 不在受信任域名列表` | host 不在白名单 | 使用 `databrain.woa.com`、`databrain.intlgame.com` 或 `databrain-*.intlgame.com` |
| `Invalid game_id` | ID 格式不符 | 用 `scripts/game_search.py` 重新查询 |
| `HTTP 566` / `HTTP 200 but empty body` | 网关限流或网关解析异常 | 保持默认请求间隔；确认 SQL 已由脚本压成单行 |
| `triggered=false` | 当前没有切片命中阈值或仍在静默期 | 查看 `/tmp/alert_result.json` 中 `slices[*].push_reason` |

---

## 8. 已知问题

- **store_score_steam 表查询频繁限流（HTTP 566 / HTTP 200 空 body）**：脚本已带退避重试 + 强制日期范围裁剪以避开全表扫描。若仍持续失败，需联系 Databrain 调整 quota。
- **国家/语种切片的 baseline 暂沿用全局 baseline**：原因是 store_score_*_daily 的 by_area 历史展开成本较高，先用全局基准近似；切片输出里有 `baseline_note` 提示。

---

## 9. 相关资源

- 商店评分告警评估 → [scripts/check_store_score_alerts.py](scripts/check_store_score_alerts.py)
- 归因（仅取有 URL 的差评）→ [scripts/attribution.py](scripts/attribution.py)
- HTML 详情页渲染（自包含） → [scripts/render_html.py](scripts/render_html.py)
- 推送 → [scripts/send_alert.py](scripts/send_alert.py)
- 告警文案 deterministic renderer → [scripts/alert_message_renderer.py](scripts/alert_message_renderer.py)
- 阈值加载 → [scripts/thresholds.py](scripts/thresholds.py)
- 状态/静默期 → [scripts/alert_state.py](scripts/alert_state.py)
- 数据查询底层 → [scripts/store_score_query.py](scripts/store_score_query.py)
- 阈值配置 → [thresholds.yaml](thresholds.yaml)
- v2 详细技术文档 → [references/store_score_alert.md](references/store_score_alert.md)
- 旧版告警检查 → [scripts/check_alerts.py](scripts/check_alerts.py)
- 阈值建议 → [scripts/calc_threshold.py](scripts/calc_threshold.py)
- 游戏 ID 查询 → [scripts/game_search.py](scripts/game_search.py)
- SQL 模板（旧） → [references/sql_templates.md](references/sql_templates.md)
- 阈值设置指南（旧） → [references/threshold_guide.md](references/threshold_guide.md)
- 原始 PRD → [prd.md](prd.md)
