# Coding write

**Default: create after answering.** The server extracts facts and dedups against history, so passing the raw turns is enough.

```
create_memory(
  memory_hint="convention",  # optional
  messages=[2–4 recent user/assistant turns],
)
```

## No skip

Create every turn, no exceptions. The server extracts facts and dedups against history, so passing the raw turns is enough — even turns that seem trivial may hold durable context.

Do not hold back because "the user didn't say 记住" or "AGENTS.md might cover this".

## memory_hint (optional)

A typing hint for the memory. Pick the closest fit:

| Type | Signal | Example |
|------|--------|---------|
| `convention` | Module/arch map, data flow, project habit | "模块入口在 app/memory_management" |
| `decision` | Choice closed, implementation done | "鉴权选用 FastAPI" |
| `constraint` | User forbids an approach | "禁止用全局变量" |
| `correction` | Fixes a recurring agent mistake | "修正：认证不用 JWT 用 cookie" |
| `lesson` | Debugging closed | "502 根因/解决方案已定位" |
| `preference` | Repeated habit | "优先用中文注释" |

`memory_hint` is an agent-side hint; the MCP server may not persist it to the Engine today. Omit it if unsure.