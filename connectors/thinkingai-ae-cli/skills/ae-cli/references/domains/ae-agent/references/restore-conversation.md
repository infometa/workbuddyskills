# agent +restore-conversation (Restore Conversation)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Conversations / write**

## Use Cases

- Restore one archived conversation by its `conversation_id`.
- Retry safely when a previous restore result was uncertain; restoring an already active conversation is idempotent and returns `changed: false`.

## Mandatory Rules (MUST)

- Obtain the real `conversation_id` from `+find-archived-conversations`; never guess it.
- This is an ordinary `write` operation and does not require destructive confirmation.
- Restoring a conversation does not restore its previous pinned state.
- The command does not provide an archive operation.

## Command

```bash
ae-cli agent +restore-conversation --conversation-id <conversation-id>
ae-cli agent +restore-conversation --conversation-id <conversation-id> --dry-run
```

## Parameters

| Parameter           | Required | Description                                   |
| ------------------- | -------- | --------------------------------------------- |
| `--conversation-id` | Yes      | ID returned by `+find-archived-conversations` |

## Output

- `conversation_id`: the restored conversation ID.
- `changed`: `true` when this call restored the conversation, or `false` when it was already active.

## Next Steps on Failure

- `conversation_not_found`: refresh the archive search and verify ownership.
- `conversation_active`: wait for the active run to finish before retrying.
- Auth error: run `ae-cli auth login`, or verify the current Agent sandbox credentials.

## Recommended Chaining

- `+find-archived-conversations` → `+restore-conversation`

## Transition Metadata

- Transition status: transitional
- Owning module: te-claude conversation archive
- Current transport: te-claude sandbox REST API
- Gateway target: `agent.conversation.restore`
- Review after: 2026-10-23
- Exit condition: Migrate to the Gateway when the equivalent capability has stable write metadata and idempotency guarantees, or remove this command if L3 provides the same typed safety.
