# team +ai-generate (AI-Generate Team Config Draft)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Team management / config generation**

## Use Cases
- Given a plain-language description of a team's goal, generate a draft `{ name, description, members[] }` that can be reviewed and passed to `+create --config`.
- Useful when the user has a goal but does not know how to write a TeamConfig manually.

## Mandatory Rules (MUST)
- `--prompt` is required (1–2000 chars). Pass the user's goal description as-is; do not pad it with generic boilerplate.
- The returned draft is a **suggestion only** — always show it to the user for review before calling `+create`. Do not auto-create without user confirmation.
- Do not fabricate `agentId` values; if the draft contains placeholder IDs, the user must replace them with real agent IDs before creating the team.

## Command
```bash
ae-cli team +ai-generate --prompt "需要一个能分析用户留存并生成周报的团队"
ae-cli team +ai-generate --prompt "A team that monitors DAU trends and sends alerts" --model <model_id>
ae-cli team +ai-generate --dry-run --prompt "test"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--prompt` | Yes | Team goal description (1–2000 chars) |
| `--model` | No | Model ID to use for generation |

## Decision Rules
- If the user says "help me create a team" or "generate a team for [goal]", call this command first rather than jumping to `+create`.
- Present the returned `name`, `description`, and `members` to the user. Ask them to confirm or adjust before proceeding.
- If the user already has a config in mind, skip this command and go directly to `+create`.

## Next Steps on Failure
- Empty or low-quality result: ask the user to refine the prompt with more specific goals, roles, or steps.
- Model error: try omitting `--model` to use the default.

## Recommended Chaining
- `+ai-generate` → user reviews and adjusts draft → `+create`
