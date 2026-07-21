---
name: github-ai-trends
description: Generate GitHub AI trending project reports as formatted text leaderboards. Fetches top-starred AI/ML/LLM repos by daily, weekly, or monthly period and renders a styled leaderboard. Use when the user asks for AI project trends, GitHub trending, AI leaderboard, or wants to see popular AI repos.
description_zh: "生成 GitHub AI 热门项目趋势排行榜报告"
description_en: "Generate GitHub AI trending project leaderboard reports"
version: 1.1.0
---

# GitHub AI Trends

Generate formatted leaderboard of trending AI projects on GitHub, output directly to chat.

## Usage

Run the script and paste its stdout as the reply:

```bash
python3 scripts/fetch_trends.py --period weekly --limit 20
```

## Parameters

- `--period`: `daily` | `weekly` | `monthly` (default: weekly)
- `--limit`: Number of repos (default: 20)
- `--token`: GitHub token for higher rate limits (or set `GITHUB_TOKEN` env)
- `--json`: Output raw JSON instead of formatted text

## How It Works

1. Searches GitHub API for AI-related repos (by keywords + topics) pushed within the period
2. Deduplicates and sorts by star count
3. Outputs a formatted markdown leaderboard ready for chat display

## Notes

- Without a GitHub token, API rate limit is 10 requests/minute. With token: 30/minute.
- No pip dependencies, uses only stdlib.
- Output is markdown formatted for direct chat display.
