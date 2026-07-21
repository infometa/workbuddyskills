# Market Analysis CN

Bilingual (Chinese / English) market analysis expert plugin for WorkBuddy / CodeBuddy.

## What it does

Transforms scattered market information into structured, decision-ready business insights:

- **Market Trend Analysis** — industry trends, market sizing, growth forecasts.
- **Competitor Analysis** — competitor teardowns, SWOT, differentiation positioning.
- **User Behavior Analysis** — user personas, behavior patterns, conversion funnels.
- **Deep Strategic Report** — integrated insights with strategic recommendations and action plans.

## Activation triggers

市场分析、竞品分析、用户行为分析、趋势分析、market analysis、competitor analysis、trends.

## Plugin structure

```
market-analysis-cn/
├── .codebuddy-plugin/
│   └── plugin.json
├── agents/
│   └── market-analysis-cn.md
└── README.md
```

## Metadata

| Field | Value |
|-------|-------|
| categoryId | 05-MarketingGrowth |
| expertType | agent |
| version | 1.0.0 |
| defaultInitPrompt | 分析AI Agent行业的市场趋势 |

## Usage

After installing the plugin, invoke the expert and ask for market trend, competitor, user behavior, or deep strategic analysis in either Chinese or English. Output is delivered as a structured Markdown report with data sources, analysis framework, and prioritized, actionable recommendations.

## Notes

- Output is advisory; combine with your own compliance and risk-control review before acting.
- Only feed in business / market / user data that is explicitly approved for analysis.
