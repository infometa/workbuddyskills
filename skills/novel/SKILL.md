---
name: novel
description: "Manage novel data — chapters, characters, plots — from the terminal fast. Use when outlining chapters, tracking characters, organizing plot timelines."
description_zh: "在终端管理小说数据(章节、角色、情节)，支持导出和搜索"
description_en: "Manage novel data (chapters, characters, plots) from terminal with export and search"
version: "2.0.0"
author: "BytesAgain"
homepage: https://bytesagain.com
allowed-tools: Bash
---

# Novel

Manage Novel data right from your terminal. Built for people who want get things done faster without complex setup.

## Why Novel?

- Works entirely offline — your data never leaves your machine
- Simple command-line interface, no GUI needed
- Export to JSON, CSV, or plain text anytime
- Automatic history and activity logging

## Getting Started

```bash
# See what you can do
novel help

# Check current status
novel status

# View your statistics
novel stats
```

## Commands

| Command | What it does |
|---------|-------------|
| `novel run` | Run |
| `novel check` | Check |
| `novel convert` | Convert |
| `novel analyze` | Analyze |
| `novel generate` | Generate |
| `novel preview` | Preview |
| `novel batch` | Batch |
| `novel compare` | Compare |
| `novel export` | Export |
| `novel config` | Config |
| `novel status` | Status |
| `novel report` | Report |
| `novel stats` | Summary statistics |
| `novel export` | <fmt>       Export (json|csv|txt) |
| `novel search` | <term>      Search entries |
| `novel recent` | Recent activity |
| `novel status` | Health check |
| `novel help` | Show this help |
| `novel version` | Show version |
| `novel $name:` | $c entries |
| `novel Total:` | $total entries |
| `novel Data` | size: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1) |
| `novel Version:` | v2.0.0 |
| `novel Data` | dir: $DATA_DIR |
| `novel Entries:` | $(cat "$DATA_DIR"/*.log 2>/dev/null | wc -l) total |
| `novel Disk:` | $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1) |
| `novel Last:` | $(tail -1 "$DATA_DIR/history.log" 2>/dev/null || echo never) |
| `novel Status:` | OK |
| `novel [Novel]` | run: $input |
| `novel Saved.` | Total run entries: $total |
| `novel [Novel]` | check: $input |
| `novel Saved.` | Total check entries: $total |
| `novel [Novel]` | convert: $input |
| `novel Saved.` | Total convert entries: $total |
| `novel [Novel]` | analyze: $input |
| `novel Saved.` | Total analyze entries: $total |
| `novel [Novel]` | generate: $input |
| `novel Saved.` | Total generate entries: $total |
| `novel [Novel]` | preview: $input |
| `novel Saved.` | Total preview entries: $total |
| `novel [Novel]` | batch: $input |
| `novel Saved.` | Total batch entries: $total |
| `novel [Novel]` | compare: $input |
| `novel Saved.` | Total compare entries: $total |
| `novel [Novel]` | export: $input |
| `novel Saved.` | Total export entries: $total |
| `novel [Novel]` | config: $input |
| `novel Saved.` | Total config entries: $total |
| `novel [Novel]` | status: $input |
| `novel Saved.` | Total status entries: $total |
| `novel [Novel]` | report: $input |
| `novel Saved.` | Total report entries: $total |

## Data Storage

All data is stored locally at `~/.local/share/novel/`. Each action is logged with timestamps. Use `export` to back up your data anytime.

## Feedback

Found a bug or have a suggestion? Let us know: https://bytesagain.com/feedback/

---
Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
