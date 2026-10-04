# Coding Search Tier (simplified)

**Default: search on every coding turn.** Call `search_memories` BEFORE exploratory codebase grep/read — even if you could just read the code. Retrieval is cheap; missed context is expensive.

## search_tier

`search_tier` is a coding-search parameter that affects empty-result behavior (`elevate_create`). You do **not** need to classify each turn — default to `S3`.

| `search_tier` | When | Call notes |
|---------------|------|------------|
| **S3** | Default — any project-bound coding turn with a known repo (implement, edit, explain, review, refactor, debug, module/arch overview, follow-up) | required `query_text` |
| **S0** | User explicitly asks to recall ("你记得之前怎么定的吗") | `limit=10` |
| **S6** | Before `delete_memory` | search to obtain `memory_id` |

Everything else → `S3`. When unsure → `S3` and search.

If the repo is unclear, clarify first, then search with `S3`.

## Recommended call

```
search_memories(
  query_text="<concise technical question>",  # required, 3–12 words
  search_tier="S3",
  limit=5,
)
```

## Empty results

When `count=0`, read optional fields: `memory_gap`, `guidance`, `elevate_create`, `suggested_next`.

- Work from codebase; empty search ≠ auto-create.
- `elevate_create` is a soft hint, not a command — still apply your own judgment.

## No skip

No skip conditions. Every coding turn: search before working, create after replying.