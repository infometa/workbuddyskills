# Memory examples

## Coding examples

### Example 1 — Explicit remember (search + create)

**User:** "请记住：这个仓库 MCP 配置用 uvx，不要 pip install -e"

**Actions:**

1. `search_memories(query_text="MCP 配置 uvx", search_tier="S3", limit=5)`
2. Answer → `create_memory(memory_hint="constraint", messages=[...])`

### Example 2 — Module overview (search first, then code, then create)

**User:** "给我说一下记忆相关的模块"

**Actions:**

1. `search_memories(query_text="记忆模块 架构", search_tier="S3", limit=5)`
2. If `count=0`: read `memory_gap` / `elevate_create`; verify from code (`app/memory_management`, `core/timem_core`)
3. Answer combining verified memories + codebase
4. `create_memory(memory_hint="convention", messages=[the Q + your verified summary])`

### Example 3 — Explicit recall (S0)

**User:** "你记得之前 auth 怎么定的吗？"

**Actions:**

1. `search_memories(query_text="auth 架构 决策", search_tier="S0", limit=10)`
2. Answer from verified memories only → `create_memory` with this exchange

### Example 4 — Typo fix (search + create)

**User:** "这个变量名拼错了，改一下" → Search anyway. Create after fix (the exchange may hold reusable convention).

### Example 5 — Task with a conclusion (search + create)

**Context:** 6 turns on auth refactor; JWT chosen and implemented; user says "好了就这样"

**Actions:** `create_memory(memory_hint="decision", messages=[4–6 relevant turns covering the JWT choice])` — no special closure step needed, this is just the normal "create after answering".

## General examples

### Example 1 — Preference recall (search + create)

**User:** "你记得我喜欢什么样的回答风格吗？"

**Actions:** `search_memories(query_text="回答风格 偏好", limit=5)` → verify → answer → `create_memory(messages=[this exchange])`.

### Example 2 — Save preference (explicit remember)

**User:** "请记住：以后解释技术问题用中文，尽量简洁。"

**Actions:** search (optional dedup) → answer → `create_memory(messages=[...])`.

### Example 3 — Trivia (search + create)

**User:** "今天星期几？" → Search anyway. Create after answering (trivial but still create).

### Example 4 — Scoped topic

**User:** "关于 TiMEM 产品，我们之前定的目标用户是谁？"

**Actions:** `search_memories(query_text="TiMEM 目标用户", limit=5)` → answer → create.

### Example 5 — Personalized task without recall wording (search + create)

**User:** "帮我写一段自我介绍。"

**Actions:** Search `自我介绍 偏好 背景`  → answer → create (the exchange may hold durable background).

### Example 6 — Pure mood (search + create)

**User:** "今天有点累，随便聊聊吧。" → Search anyway. Still create after reply (no skip policy).

## Writing examples

### Example 1 — Recall tone (search)

**User:** "帮我写产品介绍，用我们之前定的那种专业但友好的语气。"

**Actions:**

1. `search_memories(query_text="产品介绍 语气 专业 友好", limit=5)`
2. Draft using verified tone constraints.

### Example 2 — Save style rule (create)

**User:** "请记住：对外文案不用感叹号，受众是开发者。"

**Actions:**

1. Gate hits → `create_memory(messages=[user turn, assistant confirmation])`

### Example 3 — Series continuity

**User:** "继续写 blog-2026 系列的下一篇，风格和上一篇一致。"

**Actions:**

1. `search_memories(query_text="blog 风格 系列", limit=5)`
2. Write draft → `create_memory` after draft (no skip).

### Example 4 — Draft without recall wording (search + create)

**User:** "写一段产品介绍。"

**Actions:**

1. Default search → `search_memories(query_text="产品介绍 风格 受众", limit=5)`
2. Draft using verified constraints if any → `create_memory` after draft (no skip)

### Example 5 — One-off edit (still create)

**User:** "把这段改成被动语态。" (one-off edit)

**Actions:** Edit text; still `create_memory` after edit (no skip policy).