# TiMEM MCP atomic tools (shared reference)

Skills orchestrate **when** to call these tools. Requires [timem-mcp](https://github.com/TiMEM-AI/timem-mcp) connected in your MCP client.

Use atomic MCP memory tools only: `search_memories`, `create_memory`, `delete_memory` (and `classify_memory_scene` when the scene is unclear).

---

## `search_memories`

Semantic search over stored memories.

| Parameter | Required | Notes |
|-----------|----------|-------|
| `query_text` | **Yes** | 3–12 task-oriented words; empty query causes API error |
| `search_tier` | Coding: recommended | `S3` by default; `S0` for explicit recall, `S6` before delete; enables empty-search `elevate_create` |
| `limit` | No | Default 10; use 5 for task-start, 10 for explicit recall |
| `domain` | No | Optional tag (defaults to `general`); serves only as a label on stored memories, does not filter or affect retrieval |

Example:

```
search_memories(
  query_text="auth JWT decision",
  search_tier="S3",
  limit=5,
)
```

### Empty search (`count=0`)

Response may include (does **not** auto-create):

| Field | Meaning |
|-------|---------|
| `memory_gap` | No hits for this query |
| `guidance` | Short next-step hint from MCP |
| `elevate_create` | Soft signal to consider create after verify (needs `search_tier`) |
| `suggested_next` | Often includes `create_memory` |

Work from codebase; apply the coding skill write rubric before `create_memory`.

---

## `create_memory`

Create memories from conversation turns (async on backend; waits by default).

| Parameter | Required | Notes |
|-----------|----------|-------|
| `messages` | **Yes** | 2–4 decision-relevant turns; `{role, content}` |
| `memory_hint` | No | Coding only: `decision` \| `constraint` \| `lesson` \| `convention` \| `preference` \| `correction`. Agent typing hint; MCP may not persist it to Engine today. |
| `domain` | No | Optional tag (defaults to `general`); stored as a tag on the memory |

Example:

```
create_memory(
  messages=[
    {"role": "user", "content": "Remember I prefer concise answers."},
    {"role": "assistant", "content": "Stored: prefer concise answers."},
  ],
)
```

---

## `delete_memory`

Soft-delete one memory by ID. Requires user intent.

1. `search_memories` to find `memory_id` (coding: tier S6).
2. Confirm with user if ambiguous.
3. `delete_memory(memory_id="...")`

---

## `ready`

Health check after install or when other tools fail with auth/network errors.

---

## `classify_memory_scene` (optional)

When unsure whether content belongs to coding / general / writing, classify recent messages:

```
classify_memory_scene(messages=[...])
```

Returns `scene`, `expert_id`, `confidence`. If confidence is low, default to `general` or ask the user. The result can be passed as the optional `domain` tag on a subsequent call.