# 懒人出游规划师（lazy-travel-planner）

专注**国内 3-7 天、2-4 人自由行**的私人行程顾问。把实时口碑与一手数据（美团 / 小红书）整合进一份**单文件 HTML 行程书**（Leaflet 地图 + 实际道路路线 + POI 卡 + Chart.js 预算图 + 风险面板 + 小红书笔记参考），每条数据标注 🟢🟡⚪ 三色置信度。

## 类型

Agent 型（单个 AI 专家）。`expertType: "agent"`，`agentName: travel-planner`。

## 来源与迁移说明

本专家由用户提供的外部 OpenClaw 格式 Agent 包（`懒人出游规划师.zip`）**资料转化**而来，能力 100% 覆盖原包：

- 原包 8 个根 MD（AGENTS / SOUL / IDENTITY / USER / MEMORY / BOOTSTRAP / HEARTBEAT / TOOLS）已**整合**进 `agents/travel-planner.md`（角色定位、三阶段流程、11 子技能路由、置信度规则、红线、表达克制、BOOTSTRAP 等价引导）。
- 原包 **11 个子技能**按原名原样保留在 `skills/` 下（SKILL.md + scripts + templates），能力无删减。
- 原包 `data/` 5 个 JSON（user_profile / price_benchmark / scoring_rules / risk_knowledge / skeleton_fallbacks）与 `references/` 4 个 MD 原样保留。
- 原包脚本依赖 `shared/check_deps.py`（原包**未随附**），已补齐为可运行桩，详见下节。

## 行业分类

`categoryId: 12-IndustryConsultant`。理由：核心产出是"跨域生活服务咨询"（目的地研究 + 运筹 + 预算 + 风险 + 可视化交付），不属于产品设计 / 技术工程 / 金融等明确分类，按规范归入行业顾问。

## 11 个子技能（skills/ 目录）

| # | 目录 | 角色 | 关键脚本 |
|---|---|---|---|
| 1 | `intake-clarify` | 需求澄清 | — |
| 2 | `preference-load` | 加载/创建用户画像 | `load_profile.py`, `update_profile.py`, `ensure_xhs.py` |
| 3 | `destination-research` | 目的地调研 | `research.py` |
| 4 | `search-orchestrator` | 多源搜索编排底座 | `orchestrate.py`, `query_expand.py`, `xhs_batch_search.py`, `dedupe_rank.py`, `deep_read.py`, `geo_fanout.py` |
| 5 | `poi-curate` | POI 筛选评分 | `score_pois.py` |
| 6 | `transport-plan` | 大交通规划 | `plan_transport.py` |
| 7 | `accommodation-pick` | 酒店筛选 | `pick_hotel.py` |
| 8 | `itinerary-optimize` | 日程编排（运筹核心） | `build_itinerary.py`, `geo_cluster.py`, `optimize_route.py`, `balance_pace.py` |
| 9 | `budget-balance` | 预算平衡 | `balance_budget.py` |
| 10 | `risk-check` | 风险检查 | `check_risks.py` |
| 11 | `report-render` | HTML 行程书生成 | `render_html.py`, `build_xhs_notes.py` |

> agent 在规划时按 `agents/travel-planner.md` 的「子技能路由」表，按需读取对应 `skills/<name>/SKILL.md` 执行；脚本用 WorkBuddy 内置 Python 运行。

## 关于 `shared/check_deps.py`（迁移补齐的依赖）

原包多个脚本（`orchestrate.py` / `geo_fanout.py` / `build_itinerary.py` / `render_html.py`）都 `from check_deps import check_or_block / check_all / get_active_sources`，但原 zip **没有**这个文件。迁移时已补齐一个可运行桩：

- `check_or_block(name)`：默认只打印 stderr 警告并**放行**，让下游"优雅降级"逻辑接管；设置环境变量 `LTP_STRICT_DEPS=1` 后，不可用的数据源会 `sys.exit(2)` 阻塞（复刻原 block 语义）。
- `check_all()` / `get_active_sources()`：返回各数据源就绪状态。
- **判定方式**（任一满足即视为 ok）：
  - `meituan_travel`：`MEITUAN_TRAVEL_OK=1` 或标记文件 `data/.meituan_ok`
  - `xhs_logged_in`：`XHS_LOGGED_IN_OK=1` 或 `data/.xhs_ok`
  - `qweather`：`QWEATHER_OK=1` 或 `data/.qweather_ok`
  - `websearch`：恒为 True（WorkBuddy 内置联网搜索是最后防线）

**默认全部 False（灰 / 静态兜底）** —— 正好触发 agent 设计好的降级：缺一手数据时用 WebSearch + `references/` 兜底，并在 HTML 里透明标 🟡⚪。要让产物拿一手数据，agent 应主动调用 WorkBuddy 已连接的对应连接器 / 可用 skill，并按上表翻转标记。

## 产物硬规则（节选自 agent MD）

- 完整出游规划（≥3 天）**必须**出 HTML 行程书，且**必须用** `skills/report-render/scripts/render_html.py` 生成，**严禁手搓 HTML**（模板含地图 / 预算图 / 数据完整性面板）。
- 价格永远标"参考价 + 查询时间"；评分 / 营业时间缺失显式标"待核实"。
- 不擅自替用户订票订房，任何不可逆操作必须等用户明确 yes。

## 使用示例（quickPrompts）

- 帮我规划一次成都 4 天 3 晚 2 人自由行，想轻松点、吃好点。
- 推荐几个适合老人和小孩的轻松路线。
- 我想五一去重庆，帮我看看人流和预算怎么安排。

## 头像

头像已自动生成在 `avatars/expert.png`。如需替换：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装 / 注册

专家已置于专家目录：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/lazy-travel-planner/
```

已通过 `register_expert.py` 写入 `marketplace.json`，在 WorkBuddy 专家中心可见。

## 打包分享

```bash
python3 scripts/package_expert.py <expert-dir>
```
