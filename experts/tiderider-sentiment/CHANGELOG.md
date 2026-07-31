# Changelog

本文件记录 `tiderider-sentiment` 专家包（DataBrain × TideRider 游戏舆情专家）的版本变更。
遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

---

## [1.2.1] - 2026-07-31

### 修复 / 合规
- **埋点上报补齐 `platform` 字段**：按 DataBrain openskill 规范，在全部 skill 的埋点 `extInfo` 中补上 `platform=workbuddy`（与 `dataSource=skill` 平级），使上报满足 `source=skill + platform=workbuddy` 的要求。
  - `databrain-competitor-events`：原有 `platform` 参数默认值 `""` → `workbuddy`（函数签名 + CLI 默认值统一常量化）。
  - 其余 skill：新增常量 `_PLATFORM="workbuddy"` 并写入 `extInfo`。
- 统一采用「skill 内埋点」方案：BigQuery 直连型 skill 不经过 DataBrain 下游网关，无法服务端代埋，故所有 skill 均在本地 `report_log.py` 上报（非阻塞后台线程，令牌缺失/异常时静默兜底，绝不影响主流程）。

### 安全 / 打包
- 分发包严格排除真实 `.env`、Service Account 私钥、`__pycache__/`、`.DS_Store` 等敏感与平台特定文件，仅保留 `.env.example` 占位模板。

## [1.2.0] - 2026-07-30

### 新增
- **新增 `bug-radar` skill（Bug 库雷达）**：接入 TideRider Bug 库，支持
  - 活跃技术问题 Top 榜（含分类、严重度、可解释综合分 Score）；
  - 分类维度汇总（崩溃稳定性 / 账号付费 / 玩法 / 网络 / 性能等 9 类）；
  - 升温预警（问题日增长率突增识别）；
  - 单问题日趋势与生命周期；
  - 证据引用（按互动度挑选代表性原文 + 来源链接）；
  - 游戏覆盖探测。
- **Bug × 舆情融合 playbook**：定义了「异动归因 / 综合报告 / 主动预警 / 内容侧 vs 质量侧拆分」四类融入时机，通过游戏 UID 对齐实现 Bug 与舆情数据的干净关联；分析师 agent 路由表同步登记 Bug 触发信号与联动信号。

### 说明
- Bug 库通道对连接方式有要求（需具备直连数据仓库的凭据）；不满足时优雅降级为纯舆情回答，不影响主流程。
- 首批覆盖 Subway Surfers；数据管线扩展到其它游戏后自动可用（schema 通用、UID 已对齐）。

## [1.1.1] - 2026-07-24

### 变更
- 移除内置的「太湖」环境令牌，令牌一律由用户本地 `.env` / 运行时注入提供，避免任何凭据随包分发。

## [1.1.0] - 2026-07

### 新增
- DataBrain 快查车道多个 skill：单值指标、热帖、预警、竞品事件、内容趋势、舆情爬虫。
- 统一意图路由 agent，将「TideRider 深度分析车道」与「DataBrain 快查车道」整合到单一入口。

## [1.0.0] - 2026-06

### 新增
- 专家包首个版本：TideRider 舆情深度分析（异动归因、Steam 画像、话题/版本趋势、报告生成）。

---

> 数据源统一表述为 **DataBrain × TideRider**。对外文案不暴露任何底层库表名。
