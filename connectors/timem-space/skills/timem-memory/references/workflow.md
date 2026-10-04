# Memory workflow

## General

### What belongs

- Personal preferences, role/background
- **Durable office/topic facts** — decisions, owners, deadlines, meeting conclusions, product/project facts that will matter again across sessions
- Life/work context that is not coding- or writing-specific

**Not:** a daily work log, process-only narration, or transient in-progress state.

Static rules → **AGENTS.md** / **CLAUDE.md**.

### Search

**Default: search on every turn.** Call `search_memories` BEFORE answering — even if the user did not say remember/记得. Retrieval is cheap; missed context is expensive.

1. `search_memories(query_text=<3–12 words>, limit=5)`
2. Verify hits against the current conversation; abstain if stale or contradictory.

**Do not under-call** — "I can answer directly" or "this is work not about the person" is not a skip reason.

### Create

**Default: create after answering.** The server extracts facts and dedups against history, so passing the raw turns is enough.

- `create_memory(messages=[2–4 recent turns])`

**No skip.** Create every turn — the server extracts facts and dedups against history, so even seemingly trivial turns may hold durable context. Passing the raw turns is enough.

**Scope:** the server resolves scope from your API key.

## Writing

### Search workflow

**Default: search** when prior style/audience may help. When unsure → search.

1. **Trigger** — need prior style, tone, audience, or series conventions? OR drafting where those may apply without explicit recall wording? → **search**
2. **Query** — 3–12 words: style, audience, tone keywords (required).
3. **Call**:
   ```
   search_memories(
     query_text="<style or audience keywords>",
     limit=5,
   )
   ```
4. **Apply** — use verified constraints in the draft; abstain if hits are stale.

**Do not under-call** — "I can draft without tools" is not a skip reason when style/audience may matter.

### Create workflow

**No skip.** Create every turn — the server extracts facts and dedups against history.

1. **Call**:
   ```
   create_memory(
     messages=[2–4 recent turns],
   )
   ```

### Task end

Create every turn; the server dedups, so prefer passing raw turns over manually gating.

## Coding

Coding uses `search_tier` and `memory_hint` parameters unique to that domain. See the dedicated references:

- [search-tier.md](search-tier.md) — search_tier classification (S3 default, S0 recall, S6 delete)
- [write-rubric.md](write-rubric.md) — create_memory gating and memory_hint types

### Per-turn workflow (coding)

1. **Search**: `search_memories(query_text=<3–12 words>, search_tier="S3", limit=5)` BEFORE exploratory codebase grep/read
2. **Reply**: Generate reply using recalled context + fresh code/work context
3. **Create**: `create_memory(memory_hint="<optional>", messages=[2–4 recent turns])` AFTER reply