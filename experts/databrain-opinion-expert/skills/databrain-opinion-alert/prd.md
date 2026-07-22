# PRD：databrain-opinion-alert

## 一、背景与目标

游戏舆情告警 Skill，帮助 DS / 运营 同学对游戏口碑进行**持续监控**，在评分下滑、KOL 发布高互动负面帖、特定关键词声量异常时**主动推送企业微信告警**，避免人工定期盯盘。

## 二、核心功能

### 2.1 三类告警

| 类型 | 说明 | 主要字段 |
|------|------|---------|
| **评分告警** | Steam 好评率低于设定阈值，或相比近期基线大幅下滑 | `sentiment_rating IN (4,5)` / `channel='steam'` |
| **KOL 热帖告警** | 出现高互动量帖子（支持过滤负面情绪） | `engagement` / `sentiment_rating` |
| **关键词声量告警** | 用户关注的关键词当日声量超过历史均值 × 倍数阈值 | `keywords`（REPEATED STRUCT） |

### 2.2 阈值计算辅助

提供 `calc_threshold.py`，分析近 N 天历史数据，为三类告警输出**建议阈值**，解决用户不知道怎么定标准的问题。

- 评分：近 30 天日均好评率 - 2σ（或第 10 百分位）
- KOL：近 30 天 top engagement 的第 90 百分位
- 关键词：近 30 天日均声量 × 3（3 倍均值视为异常）

### 2.3 告警模板

内置默认 Markdown 模板，支持用户在对话中描述自定义格式，Agent 按自定义格式填充数据。

默认模板：
```
【舆情告警】{game_name} · {alert_type}
⚠️ 触发时间：{date}
📊 当前值：{current_value}（阈值：{threshold}）
📝 详情：{detail}
```

### 2.4 定时触发

通过 Agent `cron` 工具创建定时任务（每日定时执行），SKILL.md 中提供标准 jobMessage 模板。

## 三、技术架构

### 3.1 目录结构

```
skills/databrain-opinion-alert/
├── SKILL.md
├── prd.md
├── requirements.txt
├── .gitignore
├── scripts/
│   ├── check_alerts.py      # 主脚本：取数 → 判断阈值 → 输出 /tmp/alert_result.json
│   ├── calc_threshold.py    # 工具：历史数据分析 → 建议阈值
│   ├── send_alert.py        # 推送企业微信 Webhook
│   └── report_log.py        # 埋点上报（Agent 无感知，脚本内嵌）
└── references/
    ├── sql_templates.md     # 三类告警 SQL 模板
    └── threshold_guide.md   # 阈值设置指南
```

### 3.2 数据流

```
check_alerts.py
  ↓ 调用 Global Query API（DATABRAIN_TOKEN + DATABRAIN_HOST）
  ↓ 执行 BigQuery SQL（opinion.feeds）
  ↓ 判断是否触发告警
  ↓ 输出 /tmp/alert_result_{game_id}_{type}.json

send_alert.py
  ↓ 读取 alert JSON
  ↓ 格式化 Markdown
  ↓ POST 到 Webhook URL（企业微信，无需额外鉴权）
```

### 3.3 认证

| 接口 | 认证方式 |
|------|---------|
| BigQuery Global Query API | `DATABRAIN_TOKEN`（与 opinion-metrics 一致） |
| 企业微信 Webhook | Webhook URL 含 key，无需 header 鉴权 |

### 3.4 埋点

`check_alerts.py` 内嵌 report_log，鉴权通过后立即启动后台线程上报，Agent 完全无感知（与 opinion-metrics / opinion-summary 一致）。

## 四、check_alerts.py 接口

```bash
python scripts/check_alerts.py \
  --game_id <game_id> \
  --alert_type rating|kol|keyword \
  --start_date YYYY-MM-DD \
  --end_date YYYY-MM-DD \
  [--threshold 70]            # 评分：好评率下限 %；KOL：最低 engagement；关键词：均值倍数
  [--kol_sentiment_filter]    # 仅告警负面 KOL 帖（sentiment_rating <= 2）
  [--keywords "hack,crash"]   # 关键词告警时必填，逗号分隔
  [--message "用户原始问题"]
  [--output /tmp/alert_result.json]
```

输出 JSON 格式：
```json
{
  "triggered": true,
  "alert_type": "rating",
  "game_id": "e11000000262",
  "date_range": {"start": "2026-04-07", "end": "2026-04-13"},
  "current_value": 65.3,
  "threshold": 70,
  "detail": "好评率 65.3%，低于阈值 70%",
  "rows": [...]
}
```

## 五、calc_threshold.py 接口

```bash
python scripts/calc_threshold.py \
  --game_id <game_id> \
  --alert_type rating|kol|keyword \
  --lookback_days 30 \
  [--keywords "hack,crash"]
```

输出建议阈值及计算依据（stderr 输出分析过程，stdout 输出 JSON）。

##六、send_alert.py 接口

```bash
python scripts/send_alert.py \
  --webhook_url "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" \
  --result_file /tmp/alert_result.json \
  [--game_name "Dune Awakening"] \
  [--template_file /tmp/custom_template.txt]
```

## 七、定时任务 jobMessage 模板（SKILL.md 引用）

```
请执行舆情告警检查：
- 游戏 ID：{game_id}
- 告警类型：{alert_type}
- 时间范围：昨日（start_date=昨日, end_date=昨日）
- 阈值：{threshold}
- Webhook：{webhook_url}

执行步骤：
1. 运行 check_alerts.py 取数并判断
2. 若 triggered=true，运行 send_alert.py 推送告警
3. 无论是否触发，用 notify 工具告知用户巡检结果
```

## 八、第一期范围

- ✅ Steam 评分告警
- ✅ KOL 高互动帖告警
- ✅ 关键词声量告警
- ✅ 阈值自动计算建议
- ✅ 企业微信 Webhook 推送
- ✅ 定时任务（cron）
- ❌ 多游戏批量告警（第二期）
- ❌ 告警历史记录（第二期）
- ❌ 钉钉 / 飞书 / 邮件推送（第二期）

## 九、待确认事项

- `opinion.feeds` 中 `channel='steam'` 的数量级（影响 SQL 性能）
- 关键词字段 `keywords` 为 REPEATED STRUCT，需 UNNEST，已在 opinion-metrics 中验证可用
- KOL 的"高互动"定义：engagement 绝对值（平台间差异大），还是相对排名？→ 默认绝对值，calc_threshold.py 给出建议
