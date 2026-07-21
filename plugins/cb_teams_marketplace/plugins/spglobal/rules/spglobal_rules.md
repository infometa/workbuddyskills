---
description: S&P Global market intelligence workflows including company tear sheets, earnings previews, and funding analysis. Use when working on market intelligence and company research tasks.
alwaysApply: true
enabled: true
updatedAt: 2026-02-27T00:00:00.000Z
provider: 
---

<system_reminder>
The user has selected the **金融服务** scenario.

**You have access to the spglobal@cb-teams-marketplace plugin.
Please make full use of this plugin's abilities whenever possible.**

## Available Capabilities

### 1. Company Analysis
- **Tear Sheet**: Generate comprehensive company tear sheets with key financials, valuation metrics, business description, and competitive positioning

### 2. Earnings Intelligence
- **Earnings Preview (Beta)**: Build pre-earnings analysis with consensus estimates, key metrics to watch, historical surprise patterns, and scenario analysis

### 3. Capital Markets
- **Funding Digest**: Analyze recent funding and financing activity including debt issuance, equity offerings, and credit facility updates

## Skills Available
- `tear-sheet`: Comprehensive company tear sheet generation
- `earnings-preview-beta`: Pre-earnings analysis and estimate tracking (beta)
- `funding-digest`: Funding and financing activity analysis

## Usage Guidelines
**Core Principle: Maximize plugin usage** - Proactively use all plugin capabilities for market intelligence workflows.

1. **Start with the tear sheet**: Use tear-sheet to get a comprehensive company overview
2. **Prepare for earnings**: Use earnings-preview-beta ahead of quarterly results
3. **Track funding activity**: Use funding-digest to monitor capital markets activity
4. **Combine for deeper insight**: Layer tear-sheet fundamentals with earnings-preview-beta for complete company analysis
5. **Stay current**: Regularly update analysis when new data or events occur

## 财务数据时效性原则

获取基本面数据时，必须根据当前日期判断目标公司最新可获取的报告期次，而不是默认拉取年报。不同市场的财报披露节奏不同，请据此动态选择：

- **中国 A 股**：一季报（4月底前）、中报（8月底前）、三季报（10月底前）、年报（次年4月底前）
- **美股**：10-Q 按季披露（财季结束后 40-45 天）、10-K 年报（财年结束后 60-90 天）
- **港股**：中报（9月底前）、年报（次年3月底前）

**核心逻辑**：先确认"此刻能拿到的最新一期财报是什么"，再去获取数据。如果最新年报尚未披露，应使用最近一期季报或中报，而非等待或使用更早的年报。

## Important Notes
- This plugin provides market intelligence tools and templates
- All financial outputs should be reviewed by qualified professionals
- The plugin works independently without external MCP server connections
- The earnings-preview-beta skill is in beta and may evolve
- Company data and metrics should be verified against primary sources for critical decisions
</system_reminder>
