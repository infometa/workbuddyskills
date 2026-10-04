---
name: memory-timem
description: >-
  TiMEM long-term memory skill covering coding, general, and writing domains.
  AUTO on EVERY turn when TiMEM MCP is connected: call search_memories BEFORE
  generating reply, then create_memory AFTER generating reply. No exceptions,
  no skip. If user message contains "记", MUST call create_memory. Ambiguous:
  classify_memory_scene.
version: "1.0.4"
display_name: 跨Agent记忆 - 太忆TiMEM
display_name_en: Cross‑Agent Memory - TiMEM Memory Skill
description_zh: '跨 Agent 记忆管理平台—太忆空间，让你的记忆随你走。需配套太忆 MCP 连接器，请访问：https://space.timem.cloud/。你的所有 AI 助手， 终于共用同一个大脑 说一次"记住"，换多少个 Agent 都记得你'
description_en: 'Cross‑Agent Memory Management Platform — Taiyi Space, take your memories wherever you go. Requires the TiMEM MCP. Visit: https://space.timem.cloud/.
All your AI assistants finally share one single brain. Say "remember" once, and any number of Agents will remember you.'
---

# TiMEM Memory Skill

Use TiMEM memory with MCP (`search_memories` / `create_memory` / `delete_memory`).

Search before reply and create after reply — every turn, no exceptions.

## Trigger

When TiMEM MCP is connected — **every turn, no exceptions**.

## Instructions

1. **Search**: Call `search_memories` BEFORE generating reply (pass `query_text`; coding also passes `search_tier=S3`)
2. **Reply**: Generate reply using recalled context + fresh context
3. **Create**: Call `create_memory` AFTER generating reply, passing 2-4 recent turns — **every turn, no skip**
4. **"记"字强制**: If user message contains "记", MUST call `create_memory` even if you think there's nothing new to store

## Example

### Coding

Input: User asks "timem-mcp 的 rule learning 循环是怎么实现的？"

1. `search_memories(query_text="rule learning 循环实现", search_tier="S3")` → returns 2 hits about rule loop architecture
2. Answer the question using recalled + fresh code context
3. `create_memory(messages=[...recent turns...])`

### General

Input: User says "我们团队 Q3 的 OKR 是什么？"

1. `search_memories(query_text="团队 Q3 OKR 目标")` → returns 1 hit with Q3 OKR details
2. Answer using the recalled information
3. `create_memory(messages=[...recent turns...])`

### Writing

Input: User says "按之前的语气写一段产品介绍"

1. `search_memories(query_text="产品介绍 语气 风格")` → returns 1 hit with established tone guidelines
2. Write the product introduction matching the established style
3. `create_memory(messages=[...recent turns...])`

## Parameters

| Field | Rule |
|-------|------|
| `query_text` | required, 3–12 task-oriented words |
| `messages` | required for create, 2–4 recent `{role, content}` turns |
| `search_tier` | coding only: `S3` default; `S0` recall; `S6` before delete |
| `memory_hint` | coding only, optional: `decision` / `constraint` / `lesson` / `convention` / `preference` / `correction` |

`domain` is optional (defaults to `general`); it is used only as a memory tag and does not affect retrieval or storage.

Never paste full files or long logs into `messages`. Never use random UUIDs per turn.

**Memory vs rule:** facts / preferences / orientation → `create_memory`; reusable "in situation X, do Y" → `learn_rule` (rule-learning skill).

**Memory vs knowledge base:** memory stores cognition *about the user* distilled from conversations (preferences, decisions, lessons); the knowledge base stores *reference material the user provides* (papers, docs, specs, plans) via `write_knowledge` / `search_knowledge` (timem-knowledge skill). Rule of thumb: does the info stand on its own outside this conversation as external material? → knowledge base. Did it grow out of interactions as cognition about the user? → memory. When unsure which holds the answer, query both.

## Skip

No skip. Every turn: search before reply, create after reply.

## Forget

User asks to forget → `search_memories` (coding: `search_tier="S6"`) to get `memory_id` → confirm if ambiguous → `delete_memory(memory_id="...")`.

## References

- [mcp-tools.md](references/mcp-tools.md)
- [workflow.md](references/workflow.md)
- [examples.md](references/examples.md)
- [search-tier.md](references/search-tier.md)
- [write-rubric.md](references/write-rubric.md)

## AGENTS.md snippet

For business repos: [assets/agents-snippet.md](assets/agents-snippet.md)

## Changelog

- 1.0.4 (2026-09-08): Add memory-vs-knowledge-base boundary note and pointer to timem-knowledge skill.
- 1.0.3 (2026-09-04): Remove three-domain teaching and all `session_id` notes; domain is an optional tag only. Name → 跨Agent记忆-太忆 TiMEM.
- 1.0.2 (2026-09-01): Adjust metadata frontmatter layout.
- 0.3.1 (2026-08-26): Remove all `session_id` requirements — server schema has no such field.
- 1.0.1 (2026-08-30): Add metadata block (author/version/display_name/descriptions); unify versioning; clean legacy merge references.
- 0.2.0 (2026-08-19): Introduce three-domain selection (coding / general / writing) within the single memory skill.
- 0.1.0 (2026-08-18): Initial version of the memory skill.