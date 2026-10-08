# engage-setting channel test-send

> Trigger keywords: push channel · Capability id: `engage-setting.channel.test-send` · Domain: `engage`.

## Command

```bash
ae-cli engage-setting channel test-send \
  --project-id <project_id> --channel-id <channel_id> --push-id <send_id> \
  --content-list '[{"key":"title","value":"hello"}]' \
  [--user-params-list '<json_array>'] [--push-environment dev|pro] \
  [--mock-push] [--channel-template-id <id>]
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--channel-id` | Yes | Channel ID to test. |
| `--push-id` | Yes | Recipient send ID (e.g. a test device id). |
| `--content-list` | Yes | JSON array of key/value content pairs, e.g. `[{"key":"title","value":"hello"}]`. |
| `--user-params-list` | No | JSON array of custom user params for the test push. |
| `--push-environment` | No | Push environment: `dev` or `pro`. |
| `--mock-push` | No | Mock the push (build request only, do not send). |
| `--channel-template-id` | No | WeChat channel template ID. |

## Output

- `data.push_succeeded`: whether the test push succeeded.

## Decision Rules

- Use this command when the user asks to send a test message to a channel / verify channel delivery.
- Discover the real channel id with `ae-cli engage-setting channel list` first; never invent a channel id.
- `--mock-push` is useful to inspect the request body/headers without actually delivering a message.
- Risk is `write`; sending a real test push to a recipient is a write action.
