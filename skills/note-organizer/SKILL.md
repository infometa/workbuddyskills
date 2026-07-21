---
name: note-organizer
description: "Joplin — Note Manager — personal knowledge base. Personal productivity tool. Use when you need Joplin capabilities for personal organization, tracking, or management."
description_zh: "基于 Joplin 的个人笔记管理与知识库工具"
description_en: "Joplin-based personal note manager and knowledge base tool"
version: 1.0.0
---

# Note Organizer

Note Manager — personal knowledge base

## Why This Skill?

- Designed for personal daily use — simple and practical
- No external dependencies — works with standard system tools
- Data stored locally — your data stays on your machine
- Original implementation by BytesAgain

## Commands

Run `scripts/joplin.sh <command>` to use.

- `new` — [title]         Create new note
- `list` — [n]            List recent notes (default 10)
- `search` — <query>      Full-text search
- `view` — <id>           View a note
- `edit` — <id> <text>    Append to note
- `tag` — <tag>           List notes by tag
- `tags` —                Show all tags
- `notebook` — <name>     List notes in notebook
- `notebooks` —           List all notebooks
- `export` — [format]     Export all (md/json/html)
- `trash` — <id>          Move to trash
- `stats` —               Note statistics

## Quick Start

```bash
joplin.sh help
```

> **Disclaimer**: This is an independent, original implementation by BytesAgain. Not affiliated with or derived from any third-party project. No code was copied.

---
Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
