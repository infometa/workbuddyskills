---
name: wangxiaobao-quantum-stats
version: 0.1.0
description: "旺小宝量子看板 / 预聚合 KPI 统计：来访/跟进/成交/意向/工作表现/接访时长/使用数据/抗性点/话术卖点/挖需/销售热词/风控/特殊来访/月报/销讲执行率/挖需执行率/说辞 等 20 类指标，按 项目/团队/顾问/时间 多视图下钻。只读、无副作用。高频命令: xiaobao-cli quantum <metric> [--view <v>] [--from <d>] [--to <d>] [--team-id <id>] [--visit-type first|second|third_more|special]。何时用：用户问 今天/本周来访多少组、来访排名、各团队来访/成交/意向对比、销冠成交、意向A级分布、录音覆盖率/盘客率、平均接待时长、销讲执行率、挖需率、风控触发次数、销售热词、月报 等 看板/KPI/排名/占比/团队对比 类问题。注：指标多、每个支持的 view 不同，跑前先读 references/quantum-metrics.md；跨指标坑：特殊到访组数用 `quantum visit --visit-type special`（不是 special-visit）、团队均值 MUST `--view team` 禁手算。要问一句话开放式业务问题走 wangxiaobao-quick-qa。"
metadata:
  requires:
    bins: ["xiaobao-cli"]
  cliHelp: "xiaobao-cli quantum --help"
---

# 旺小宝量子统计（量子看板 / 预聚合 KPI）

> **CRITICAL** —— 跑命令前 MUST 先用 Read tool 读取 [`../wangxiaobao-shared/SKILL.md`](../wangxiaobao-shared/SKILL.md)（安装 / 登录 / 选项目 / 错误码 / 输出协议）。
> **强烈建议** 再读 [`references/quantum-metrics.md`](references/quantum-metrics.md) —— 20 个指标各支持哪些 view/mode、需要哪些参数都在那里；跑前对照选对 `metric + view`，避免选错卡片或漏必填参数。

`xiaobao-cli quantum <metric> [--view ...]` 一个命令覆盖全部量子指标（对应 H5 量子看板各卡片）。它们**共用一套入参**，靠 `--view` / `--mode` 区分子视图。

## 执行前必读
- 有效 token + **激活项目**（见 shared；缺失返回 `NO_ACTIVE_PROJECT`）
- **数据权限**：不传 `--user-ids` 时后端按当前用户的 管理者/个人 范围自动解析
- **时间**默认当天 `00:00:00 ~ 次日 00:00:00`；跨天/周/月用 `--from/--to` + `--date-type`
- 只读、**不要**写文件

## 快速索引：用户意图 → metric + view
| 用户问法 | 命令 |
| --- | --- |
| 今天/本周来访多少组、来访趋势 | `quantum visit`（`--view summary` / `time`） |
| 来访排名 / 各顾问来访 | `quantum visit --view rank`（或 `team`） |
| 首访/复访/三访+/特殊到访 组数 | `quantum visit --visit-type first\|second\|third_more\|special` |
| 各团队 来访/成交/意向 对比 | `quantum <visit\|deal\|intent> --view team` |
| 成交统计 / 销冠 | `quantum deal`（`--view status/user/team/period`） |
| 意向级别分布 / A 级客户 | `quantum intent --view level`（或 `user` + `--intent-level A`） |
| 录音覆盖率 / 盘客率 | `quantum job-performance`（`--view audio_rate/panke_rate/team`） |
| 平均接待时长 / 服务分 | `quantum work-quality --view team`（团队均值禁手算） |
| 接访时长分桶下钻 | `quantum visit-timer`（team/date 须 `--interval-start/--interval-end`） |
| 销讲执行率 | `quantum pin-talk`（`--view summary/team/user/...`） |
| 挖需执行率 / 团队最高挖需率 | `quantum demand-card`（团队最高用 `--view team`） |
| 风控触发 | `quantum risk`（`--risk-dimension all/effective`） |
| 销售热词 | `quantum hot-words` |
| 月报 | `quantum month-report --mode query` |

（完整 20 指标 + 各 view/参数见 [`references/quantum-metrics.md`](references/quantum-metrics.md)）

## 核心约束（跨指标坑，务必遵守）
1. **特殊到访组数/排名** 用 `quantum visit --visit-type special`，**不是** `quantum special-visit`（后者是「有效/无效标签卡」，语义不同）。
2. **团队均值类**（某团队平均接待时长 / 服务分 / 挖需率 / 成交率…）**MUST 用 `--view team`**，禁止取 `user` 视图自己手算平均。
3. **团队最高挖需率** → `quantum demand-card --view team`。
4. **首访/复访/三访+** → `--visit-type first|second|third_more`（不传 ≠ 已选某 Tab，可能混合或未过滤）。
5. **客户数维度** → `--stat-dimension customer_num`（来访默认 `visit_times`、跟进默认 `follow_times`；别一看到「客户数」就误用）。
6. **意向复核后数据** → `--intent-dimension review`（默认 `ai`）。
7. **visit-timer 的 team/date 下钻** → 必填 `--interval-start/--interval-end`（分桶：0/30/60/120 → 30/60/120/1000 分钟）。

## 响应
统一 `Result<Object>`，`data` 结构**随 metric/view 变化**（列表 / 嵌套 / 汇总都可能）。CLI 再包一层 → 读 `resp.data.data`。**按实际返回展示，不要假设固定结构、不要硬解析**。默认 `--format toon` 省 token；要严格 JSON 加 `--format json`。

## 使用场景示例
```bash
# 今天各顾问来访排名（首访）
xiaobao-cli quantum visit --view rank --visit-type first
# 各团队成交对比
xiaobao-cli quantum deal --view team
# 意向 A 级客户按顾问
xiaobao-cli quantum intent --view user --intent-level A --intent-dimension review
# 本周录音覆盖率（各团队）
xiaobao-cli quantum job-performance --view team --from "2026-06-09 00:00:00" --to "2026-06-16 00:00:00" --date-type week
# 接访时长 30~60 分钟档 各团队
xiaobao-cli quantum visit-timer --view team --interval-start 30 --interval-end 60
```

## 常见错误与排查
- **`NO_ACTIVE_PROJECT`** → 跑 `wangxiaobao-switch-project`
- **401 / token 过期** → `auth login --no-wait --force` 重登
- **400 / 缺参数**（如 visit-timer team 缺 interval、intent team 缺 intent-level）→ 对照 references 补齐必填
- **未知 metric（404）** → 端点名拼错，照 references 的 metric 列表
- **空数据** → 时间窗内无数据，或当前账号无该范围权限（不是 bug）
- **该用开放式问数** → 一句话业务问题（「客户主要疑虑是啥」）走 `wangxiaobao-quick-qa`，量子是结构化看板 KPI
