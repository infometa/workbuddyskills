# 商店评分告警 v2 — 技术文档

> 与 [SKILL.md §3](../SKILL.md#3-商店评分告警-v2推荐使用) 互为补充。本文聚焦数据源、阈值语义、模块协作与 SQL 细节。

## 1. 模块结构

```
scripts/
├── thresholds.py                  # 加载/合并 thresholds.yaml（深合并 overrides）
├── alert_state.py                 # 静默期 + 升级打破，状态文件 /tmp/databrain_alert_state.json
├── store_score_query.py           # 数据查询底层（含 retry / 限流退避 / JSON 解析）
├── check_store_score_alerts.py    # 主流程：评估 + 静默期 + 输出 alert_result.json
├── attribution.py                 # 归因：投诉来源分布 + 代表性差评 Top N（仅取有 URL）
├── render_html.py                 # 自包含 HTML 详情页渲染（5 区块 + SVG 趋势图 + XSS 防护）
├── send_alert.py                  # 渲染 markdown + 自动调 render_html + 推送企业微信
thresholds.yaml                    # 阈值配置中心
references/store_score_alert.md    # 本文
```

数据流：

```
thresholds.yaml ──┐
                  ▼
            ┌───────────────────────────┐
game_id ──▶ │ check_store_score_alerts  │ ──▶ alert_result.json
channel ──▶ │  ├─ store_score_query     │
            │  ├─ alert_state（静默期） │
            └───────────────────────────┘
                                       │
              attribution ─────────────┘ ──▶ attribution.json
                                              │
                                send_alert ───┘ ──▶ 企业微信
```

---

## 2. 数据源

| 表 | 用途 | 关键字段 |
|----|------|----------|
| `tencent-databrain-prod.opinion.store_score_steam` | Steam 评分快照（小时级） | `all_reviews_score` (0~1)、`recent_reviews_score`、`all_reviews_count`、`recent_reviews_count`、`language_reviews`（JSON：`{"English": {"score": 0.8, "reviews": 12345}, ...}`）、`create_time` |
| `tencent-databrain-prod.opinion.store_score_google_play_daily` | Google Play 日级评分 + 国家分布 | `area`、`store_score` (0~5)、`comments_number`、`count_by_rating`（JSON：`{"1":..,"2":..,"3":..,"4":..,"5":..}`）、`date` |
| `tencent-databrain-prod.opinion.store_score_app_store_daily` | App Store 日级评分 + 国家分布 | 同上 |
| `tencent-databrain-prod.opinion.feeds` | 实时评论流（用于 6h/24h 下跌检测 + 归因） | `unified_edition_id`、`channel_name`（注意有空格：`'google play'` / `'app store'` / `'steam'`）、`comment_score`、`is_recommend`、`sentiment_rating`、`country`、`language`、`comment_time` |

> ⚠️ 所有表统一使用 `unified_edition_id` 作为游戏 ID 字段。废弃的 `unified_id` / `edition_id` 不再使用。

---

## 3. 等级判定

每个 `(channel, scope, slice_key)` 走同一套评估流程：

```python
for level in ("P0", "P1", "P2"):
    cfg = thresholds[level]
    if sample_in_window < cfg["min_sample"]:
        continue          # 样本量不足 → 跳过该等级
    matched = []
    if cfg.get("absolute_pp")   and cur_pp < cfg["absolute_pp"] - eps:        matched.append("A_absolute")
    if cfg.get("drop_6h_pp")    and (prev_6h_pp - cur_pp) >= cfg["drop_6h_pp"] - eps:  matched.append("B_drop_6h")
    if cfg.get("drop_24h_pp")   and (prev_24h_pp - cur_pp) >= cfg["drop_24h_pp"] - eps: matched.append("B_drop_24h")
    if cfg.get("baseline")      and cur_pp < baseline[cfg["baseline"]] - eps:  matched.append(f"C_below_{cfg['baseline']}")
    if matched:
        return level, matched
return "OK", []
```

**重要细节**：

- **P0 优先**：从 P0 开始评估，任一维度命中即停（返回最严重的等级）
- **样本量门槛在前**：不达标的等级直接跳过；这意味着 P0 不达标但 P1 达标时，可能直接落到 P1
- **浮点容差 `eps`**：Steam 用 0.05pp、GP/AS 用 0.005 score、1 星占比用 0.001。原因：日级 score 在 30 天内可能完全相等，不加容差会因尾数被判"低于"
- **A/B/C 单位与字段对应**：
  - Steam（`all_reviews` / `recent_reviews`）：好评率 × 100 (pp)
    - `absolute_pp` / `drop_6h_pp` / `drop_24h_pp`，baseline 单位也是 pp
  - GP / App Store：score 0~5
    - `absolute_score` / `drop_6h` / `drop_24h`，加 `one_star_rate` 维度（占比 0~1）

---

## 4. 切片策略

### 4.1 一次查询取全切片

不需要预设国家/语种白名单。`store_score_*` 的快照查询天然包含 `language_reviews`（Steam JSON）或 `area` 维度（GP/AS），一次取回即可：

| 渠道 | 切片粒度 | 数据来源 |
|------|---------|----------|
| Steam | 分语种 | `store_score_steam.language_reviews`（JSON 解析） |
| Google Play | 分国家 | `store_score_google_play_daily.area` |
| App Store | 分国家 | `store_score_app_store_daily.area` |

切片评估时复用同一套 `defaults` 阈值，对每个切片独立判定。

### 4.2 屏蔽噪声切片

```yaml
slicing:
  steam:        { by_language: true, exclude_languages: [] }
  google_play:  { by_country:  true, exclude_areas: ['lang_*'] }   # 屏蔽伪国家码
  app_store:    { by_country:  true, exclude_areas: [] }
```

`exclude_areas` 支持 glob 通配符（`lang_*` 匹配所有以 `lang_` 开头的伪国家码）。

### 4.3 切片样本量

- Steam：`current.count - 6h_前.count`（窗口内新增评论）
- GP / App Store：从 `feeds` 表查 6h 窗口内对应国家的评论条数

切片样本不达标时，对应等级会被自动跳过（跟全局逻辑一致）。

---

## 5. 6h / 24h 下跌的特殊处理

| 渠道 | 当前值来源 | 6h 前 / 24h 前来源 |
|------|-----------|-------------------|
| Steam | `store_score_steam` 快照（小时级） | 同表，向前 N 小时 |
| GP / App Store | `store_score_*_daily` 当日加权 | **`feeds` 表实时 6h / 24h 窗口的 `comment_score` 平均值** |

> GP/AS 的 `store_score_*_daily` 是日级累计，不能直接做 6h 对比。所以 6h/24h 下跌全部从 `feeds` 算实时窗口均分。

`feeds` 中 `channel_name` 实测值带空格：`'steam'` / `'google play'` / `'app store'`。`store_score_query.CHANNEL_TO_FEEDS_NAME` 已做映射。

---

## 6. Baseline 计算

30 天每日值序列：

- `p5` / `p25`：在排序后用线性插值
- `median_7d`：最近 7 天的中位数
- 切片暂复用全局 baseline（输出里附 `baseline_note` 提示）。后续若需要切片级 baseline，要按 area/language 展开 30 天 daily 数据，成本较高。

---

## 7. <a id="thresholds-yaml"></a>thresholds.yaml 配置

```yaml
slicing:
  steam:        { by_language: true, exclude_languages: [] }
  google_play:  { by_country:  true, exclude_areas: [] }
  app_store:    { by_country:  true, exclude_areas: [] }

silence_seconds:
  P0: 3600     # 1h
  P1: 7200     # 2h
  P2: 21600    # 6h

defaults:
  steam:
    all_reviews:
      P0: { absolute_pp: 60, drop_6h_pp: 5, baseline: p5,        min_sample: 100 }
      P1: { absolute_pp: 75, drop_6h_pp: 2, baseline: p25,       min_sample: 50  }
      P2: { absolute_pp: 80, drop_24h_pp: 1, baseline: median_7d, min_sample: 20  }
    recent_reviews:
      P0: { absolute_pp: 65, drop_6h_pp: 8, baseline: p5,        min_sample: 80  }
      P1: { absolute_pp: 80, drop_6h_pp: 3, baseline: p25,       min_sample: 40  }
      P2: { absolute_pp: 85, drop_24h_pp: 2, baseline: median_7d, min_sample: 20  }
  google_play:
    P0: { absolute_score: 3.0, one_star_rate: 0.40, drop_6h: 0.30, baseline: p5,        min_sample: 200 }
    P1: { absolute_score: 3.5, one_star_rate: 0.25, drop_6h: 0.10, baseline: p25,       min_sample: 100 }
    P2: { absolute_score: 4.0,                       drop_24h: 0.05, baseline: median_7d, min_sample: 50  }
  app_store:
    P0: { absolute_score: 3.0, one_star_rate: 0.40, drop_6h: 0.30, baseline: p5,        min_sample: 100 }
    P1: { absolute_score: 3.5, one_star_rate: 0.25, drop_6h: 0.10, baseline: p25,       min_sample: 50  }
    P2: { absolute_score: 4.0,                       drop_24h: 0.05, baseline: median_7d, min_sample: 20  }

overrides:
  # 仅写要改的字段，深合并到 defaults 上
  e7f672beaa5fddd166df98bc046ba4bd4:
    steam:
      all_reviews:
        P0: { absolute_pp: 55 }   # 该游戏整体口碑较差，把 P0 阈值放宽
```

### 字段约束

- 必须有 `defaults`、`silence_seconds`、`slicing` 三个顶层 key
- 每个等级至少含 `min_sample`
- A/B/C 维度全部可选；不写就不参与评估
- `baseline` 只能取 `p5` / `p25` / `median_7d`

---

## 8. 静默期 + 升级打破

状态文件 `/tmp/databrain_alert_state.json`，结构：

```json
{
  "<game_id>::<channel>::<scope>::<slice_key>": {
    "last_level": "P1",
    "last_triggered_at": "2026-05-07T10:00:00+00:00",
    "silence_until": "2026-05-07T12:00:00+00:00"
  }
}
```

判定逻辑（`alert_state.should_trigger`）：

```python
if now < silence_until and current_level_rank >= last_level_rank:
    return False, "in_silence"            # 静默中且未升级
return True, "first_trigger" 或 "upgraded"
```

升级判定：`P0 < P1 < P2`（rank：P0=0, P1=1, P2=2）。当前等级序号小于上次（更严重）→ 立即打破静默。

清理：等级回到 OK 时调用 `clear_state(state, key)` 删除该 key。

---

## 9. 归因（attribution.py）

### 9.1 投诉来源分布

```sql
SELECT country, language, channel_name,
       COUNT(*) AS cnt, COUNT(DISTINCT comment_uin) AS uniq_users
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND LOWER(channel_name) = '{channel}'
  AND comment_time BETWEEN ... AND ...
  AND {sentiment_rating IN (1,2)  -- GP/AS
       OR is_recommend = 0        -- Steam}
GROUP BY country, language, channel_name
```

聚合后输出 `by_country` / `by_language` / `by_channel_name` 各 Top N。

### 9.2 代表性差评

按互动量（`tweets_like + tweets_reply + tweets_retweet`）DESC 取 Top N，输出 `reviewer / comment_time / 国家 / 语种 / sources URL`。

> ⚠️ 当前实现**不输出评论文本**——`feeds_templates.md` 未文档化文本字段；后续如确认有 `comment_text` 字段可以补上。

### 9.3 代表性差评的 URL 强过滤（v2.1+）

```sql
WHERE ...
  AND EXISTS (
    SELECT 1 FROM UNNEST(sources) s
    WHERE s.url IS NOT NULL AND s.url != '' AND LOWER(s.url) != 'null'
  )
ORDER BY engagement DESC
LIMIT {top_n * 3}
```

并在 Python 端再次校验 `url.startswith(("http://", "https://"))`，规避字面 `'null'` / 空串污染。
最终保证：返回的每一条差评都可点击跳到原帖。

---

## 10. HTML 详情页（render_html.py，v2.1+）

### 10.1 设计目标

- **完全自包含**：内联 CSS、内联 SVG（自绘趋势图），不依赖任何 CDN，离线可看
- **XSS 防护**：所有用户/上游数据通过 `_esc / _attr / _url` 转义后插入 HTML
  - URL 仅允许 `http://` / `https://` scheme，`javascript:` / `data:` / `file://` 一律渲染为 "—"
  - 文本节点用 `html.escape`，属性值用 `quote=True`，URL 用 `urllib.parse.quote`
- **5 区块**：
  1. **顶部摘要**：游戏 / 渠道 / 评估时间 / 触发等级 + 关键数字
  2. **全切片表格**：默认仅显示触发的，复选可显示 OK 切片（纯 HTML+JS 实现，无 jQuery）
  3. **30 天趋势 SVG**：全球 score 折线 + 当前/30dP5/7d中位 三条水位线
  4. **归因**：Top 投诉国家/语种 + 全部代表性差评（每条带"查看原帖 ↗"跳转）
  5. **底部折叠原始 JSON**：`<details>` 元素，便于调试

### 10.2 数据契约

`render_html` 依赖 `alert_result.json` 中 `slices[*]` 字段：

| 字段 | 类型 | 是否必需 | 用途 |
|------|------|---------|------|
| `slice_key` / `label` / `level` / `matched_dims` / `current` / `baseline` / `sample_in_window` | - | ✓ | 切片表格 / 摘要 |
| `should_push` / `push_reason` | bool / str | ✓ | 触发筛选 / 显示推送状态 |
| `history_values` | list[float] | 仅全球切片必须 | 30 天 SVG 趋势图 |

`check_store_score_alerts.py` 自动塞 `history_values`（v2.1+），旧版结果文件无此字段时 SVG 区块退化为 "无足够历史数据" 提示。

### 10.3 自动 vs 手动生成

`send_alert.py` 默认在商店评分告警触发时**自动**调 `render_html`，输出到 `<html_dir>/alert_<game_id>_<channel>_<YYYYMMDD-HHMMSS>.html`。

| 场景 | 用法 |
|------|------|
| 默认：本机 file:// 链接 | 不传任何 HTML 参数即可 |
| 关闭 HTML 生成 | 加 `--no_html` |
| 自托管：内网静态目录 | `--html_dir /var/www/alerts --detail_url_base http://oa.intra/alerts/` |
| 仅生成 HTML（不推送） | `python scripts/render_html.py --result_file ... --output ...` |

### 10.4 file:// 链接的局限

企业微信 PC 客户端通常出于安全原因不会自动打开 `file://` 链接。脚本在消息底部已自动附提示文字"复制到浏览器打开"。

如需团队共享或移动端可访问，必须用 `--detail_url_base` 接入内网静态服务。

---

## 11. 推送（send_alert.py）

- 自动识别两种输入：商店评分告警 v2（看 `slices` + `channel` + `scope`） vs 旧版（看 `alert_type`）
- v2 模板：`级别 badge` + `游戏/时间/触发切片数` + `Top 10 触发明细` + `归因块`（如附）+ `📄 查看完整详情` 链接 + 推荐处置
- 等级 emoji：P0=🚨 / P1=⚠️ / P2=🟡
- 长度超 4096 字符自动分段
- Webhook URL 严格白名单（`https://qyapi.weixin.qq.com/cgi-bin/webhook/send` 前缀），防 SSRF
- `--preview_only` 仅打印不发送，便于调试

---

## 12. 已知限制 & 后续工作

| 项 | 现状 | 后续 |
|----|------|------|
| 切片 baseline | 沿用全局 baseline（输出 baseline_note） | 按 area/language 展开 30 天 daily 数据 |
| store_score_steam 限流 | API 经常 HTTP 566 / 200 empty body，已加退避重试 | 联系 Databrain 调整 quota；或缓存历史快照 |
| 评论文本归因 | 未输出文本（feeds 字段未文档化） | 确认 feeds 文本字段后追加 keyword 抽取 |
| 关联版本/事件 | 模板原本要求，因数据源不全已移除 | 待 Steam News / 事件库接入 |
| 阈值自动校准 | 全靠人工填 yaml | 后续可加 `calc_thresholds_v2.py` 用历史样本反推 |
| HTML 详情页 file:// 链接 | 企业微信 PC 端不自动打开，已附提示 | 接入内网静态目录 + `--detail_url_base` |
| HTML 趋势图切片维度 | 仅全球切片画 SVG | 后续如有强需求可对每个切片各画一张 |

---

## 13. 调试 cheatsheet

```bash
# 全部单元测试（不依赖网关，~1s 跑完）
python scripts/thresholds.py --self_test
python scripts/alert_state.py --self_test
python scripts/check_store_score_alerts.py --self_test
python scripts/render_html.py --self_test
python scripts/send_alert.py --self_test

# 端到端 dry_run（不写状态文件）
python scripts/check_store_score_alerts.py \
  --game_id ufc454d9b1af70b40588e2a6fa4da4a8b \
  --channel google_play --dry_run \
  --output /tmp/alert.json

# 仅生成 HTML（无需推送、无需归因）
python scripts/render_html.py \
  --result_file /tmp/alert.json \
  --game_name "PUBG Mobile" \
  --output /tmp/alert.html
open /tmp/alert.html

# 完整渲染预览（含 HTML 自动生成 + markdown）
python scripts/send_alert.py \
  --result_file /tmp/alert.json \
  --attribution_file /tmp/attribution.json \
  --game_name "PUBG Mobile" \
  --preview_only

# 清空所有告警状态（测试用）
rm /tmp/databrain_alert_state.json
```
