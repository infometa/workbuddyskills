## TiMEM memory skill (Skill + MCP)

When [timem-mcp](https://github.com/TiMEM-AI/timem-mcp) is connected, follow the **timem-memory-skill** skill (prefer [timem-skill](https://github.com/TiMEM-AI/timem-skill) `dist/standalone/`; `dist/full/` also fine).

### Per-turn workflow (atomic MCP tools)

1. **Search**: `search_memories` BEFORE reply — every turn, no exceptions (coding: pass `search_tier=S3`)
2. **Reply**: use recalled context + fresh context
3. **Create**: `create_memory` AFTER reply — every turn, no exceptions
4. **"记"字规则**: If user message contains "记", MUST call `create_memory`

### Rules

- Default: call `search_memories` on every turn; more search ≠ more create
- Use `search_memories` / `create_memory` / `delete_memory` only
- Search: skip only for typo/format/trivia; Create: no skip, every turn
- AGENTS.md = team conventions; TiMEM = decisions + preferences + orientation

Canonical packages: `dist/standalone/timem-memory-skill/` (recommended) or `dist/full/timem-memory-skill/` (source: `skills/timem-memory-skill/`)