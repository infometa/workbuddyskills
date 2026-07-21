---
name: github-trending-cn
description: "GitHub Trending Monitor. Fetch GitHub trending repos by daily/weekly/monthly period using real GitHub Search API. Runs scripts/github_trending.py (no pip deps, stdlib only). Use when user asks for 今日热门, 本周热门, 本月热门, GitHub trending, 开源动态, or popular repos. Supports language filter (python/javascript/go/rust etc.) and GITHUB_TOKEN for higher rate limits. 触发词：GitHub、trending、开源、热门项目."
description_zh: "获取 GitHub 今日/本周/本月热门项目，支持语言过滤"
description_en: "Fetch GitHub trending repos (daily/weekly/monthly) with language filter"
version: 2.0.0
allowed-tools: Bash,Read
---

# GitHub Trending CN

获取 GitHub 真实热门项目数据，支持今日 / 本周 / 本月，可按编程语言过滤。

## 快速开始

```bash
# 今日热门（默认）
python3 scripts/github_trending.py

# 本周热门，Top 25
python3 scripts/github_trending.py --period weekly --limit 25

# 本月热门，只看 Python 项目
python3 scripts/github_trending.py --period monthly --language python

# 输出 JSON（方便进一步处理）
python3 scripts/github_trending.py --period daily --json
```

## 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--period` | `-p` | `daily` | 时间范围：`daily` / `weekly` / `monthly` |
| `--limit` | `-n` | `20` | 返回项目数量 |
| `--language` | `-l` | 全部 | 编程语言过滤，如 `python`、`go`、`rust` |
| `--token` | `-t` | 环境变量 | GitHub PAT，也可设置 `GITHUB_TOKEN` |
| `--json` | — | 否 | 输出原始 JSON |

## 提高 API 限额

不带 token 时，GitHub API 限制为 10 次/分钟；带 token 可提升到 30 次/分钟。

```bash
export GITHUB_TOKEN=your_personal_access_token
python3 scripts/github_trending.py --period weekly
```

## 实现说明

- **无任何 pip 依赖**，仅使用 Python 标准库
- 调用 `https://api.github.com/search/repositories` 真实 API
- 按 `pushed:>=DATE stars:>=10` 过滤 + `sort=stars` 排序
- 多语言补充策略：先全量抓取，再按主流语言补充，确保结果多样性

## 常见问题

**Q: 提示 HTTP 403 / rate limit exceeded？**  
A: 设置 `GITHUB_TOKEN` 环境变量，或稍等片刻再试。

**Q: 结果和 github.com/trending 不完全一致？**  
A: GitHub 官方 Trending 页面使用内部算法，此脚本通过 Search API 按近期 stars 增量近似实现，结果高度吻合但不完全相同。

**Q: 支持哪些编程语言？**  
A: 所有 GitHub 支持的语言标识符，如 `python`、`javascript`、`typescript`、`go`、`rust`、`java`、`cpp`、`swift`、`kotlin` 等。
