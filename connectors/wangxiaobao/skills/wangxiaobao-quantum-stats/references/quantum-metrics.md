# 量子统计指标清单（quantum-metrics）

`xiaobao-cli quantum <metric> [flags]` → `POST /ai-open/quantum/<metric>`。20 个 metric **共用同一套入参**，靠 `--view` / `--mode` 区分子视图，统一返回 `Result<Object>`（结构随 metric/view 变）。默认时间 = 当天。

## 共享参数
- `--from` / `--to`：`yyyy-MM-dd HH:mm:ss`，默认当天 `00:00:00 ~ 次日`
- `--date-type`：`day|week|month|year|total`（默认 day）
- `--user-ids`：CSV 显式数据范围；不传按 管理者/个人 自动解析
- `--team-id`：团队 ID（部分 metric 的 scope）
- `--page` / `--size`：分页（默认 1 / 20）
- `--visit-type`：`first|second|third_more|special|all`（来访维度 Tab）

## 20 个指标
| metric | 说明 | view / mode | 关键参数 |
| --- | --- | --- | --- |
| `visit` | 来访统计 | view: `summary`(默认)`\|rank\|team\|time` | `--stat-dimension visit_times`(默认)`\|customer_num`；`--visit-type first\|second\|third_more\|special` |
| `visit-ongoing` | 接待中接访 | mode: `page`(默认)`\|count` | — |
| `visit-realtime` | 实时看板 | view: `trend`(默认)`\|resistance\|resistance_list\|deal` | — |
| `follow` | 跟进统计 | view: `summary\|rank\|team\|time` | `--stat-dimension follow_times`(默认)`\|customer_num`；`--visit-type` 同 visit |
| `job-performance` | 工作表现（录音/盘客率） | view: `summary\|panke_rate\|audio_rate\|rank\|user\|team\|time` | `team`=各团队录音/盘客率 |
| `work-quality` | 工作质量（接待时长/服务分） | view: `summary\|user\|team\|date` | 团队均值 **MUST** `view=team`（禁 user 手算） |
| `visit-timer` | 接访时长 | view: `summary\|team\|user\|date` | `--agg total`(默认)`\|avg`；`team/date` 须 `--interval-start/--interval-end`（分桶 0/30/60/120 → 30/60/120/1000）；`summary`=全项目 4 分桶；`user`=逐顾问平均分钟 |
| `usage-data` | 使用数据 | view: `summary\|rank\|time\|team` | `--role consultant`(默认)`\|manager`（仅影响 summary 展示）；`--usage-data-type daily_time_avg\|review_audio\|learning_times\|customer_comment\|share_audio\|audio_comment`（rank 指标） |
| `resistance-point` | 抗性点 | view: `distribution`(默认)`\|detail_texts\|detail_total` | — |
| `speech-sale` | 话术卖点 | view: `summary\|user` | — |
| `demand-data` | 挖需统计（DataStat） | view: `summary\|user` | — |
| `hot-words` | 销售热词 | view: `summary\|user\|dimensions` | — |
| `risk` | 风控 | view: `summary`(风控点列表)`\|user\|total`(触发总次数) | `--risk-dimension all`(默认)`\|effective\|review\|invalid`（仅有效= effective） |
| `special-visit` | 特殊来访标签卡（有效/无效 visitLabel 分布） | view: `summary\|user` | ⚠️ H5「特殊到访组数/排名」**不用这个**，用 `visit --visit-type special` |
| `month-report` | 月报 | mode: `query`(默认)`\|find` | — |
| `deal` | 成交统计 | view: `status`(默认)`\|team\|user\|period` | `team`=各团队 count/total/rate；`--deal-status` 默认 `1,2,3` |
| `intent` | 意向统计 | view: `level`(默认，全项目级别分布)`\|team\|user\|period` | `team/user/period` 须 `--intent-level A\|B\|C\|D\|E`；`--intent-dimension review\|ai`(默认 ai)；`--direction left\|right`（period 翻页） |
| `pin-talk` | 销讲执行率 | view: `summary\|visit_status\|team\|user\|dimension\|speech\|models` | `--visit-type first\|second\|third_more`；`--model-id/--dimension-id/--speech-id` 下钻 |
| `demand-card` | 挖需执行率卡片 | view: `summary\|visit_status\|team\|user\|dimension\|speech` | `--visit-type first\|second\|third_more\|all`；团队最高挖需率用 `--view team` |
| `rhetoric` | 说辞统计 | 无 view（默认汇总） | — |

## 跨指标坑（重复强调）
- 特殊到访组数/排名 → `visit --visit-type special`，不是 `special-visit`。
- 团队均值/占比（接待时长、服务分、挖需率、成交率、意向占比）→ 对应 metric 的 `--view team`，别手算。
- 团队最高挖需率 → `demand-card --view team`。
- 首访/复访/三访+ → `--visit-type first|second|third_more`。
- 「客户数」口径 → `--stat-dimension customer_num`（默认是 visit_times / follow_times）。
- 意向复核后 → `--intent-dimension review`（默认 ai）。
