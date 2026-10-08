# Config channel management workflows

> Trigger keywords: config center, config channel · Commands: `ae-cli engage-scene config-channel …` · See [`scene-config-channel.md`](scene-config-channel.md) for flags, `config` JSON shape, and capability ids.

Use for AE Engage **config center channel management**: Webhook (`channel_type=0`) and client (`channel_type=1`) config channels — list, get, create, update, copy, enable/disable, operation log, and delete.

## Hard rules

1. Use `ae-cli engage-scene config-channel <action>` only.
2. Discover real `channel_id` values with `list` first; never invent IDs.
3. `channel_type`: **0 = Webhook**, **1 = client** (not the same as engage push `channelType`, where 1 = webhook).
4. `channel_status`: **1 = enabled**, **2 = disabled**.
5. Writes require explicit user intent; `delete` is high-risk — confirm, then `--yes`.
6. Before changing Webhook URL, auth, or parameter definitions on an enabled channel, disable it first.
7. In `config.customsParamList` (**user params**), every `columnName` must be prefixed with `user:` and point to a real user property, e.g. `user:#account_id`. `envParamList` entries do not use this prefix.
8. Before create/update, use the **ae-analysis** skill to verify each intended user property exists (`analysis-meta property list --scope user`, then `property get` for exact match). Never invent `columnName` values.

## Permissions

| Operation | Permission |
|---|---|
| List / get / query-log | `@opsViewConfigChannel@` |
| Create / update / copy / delete | `@opsEditConfigChannel@` |
| Enable / disable | `@opsManageConfigChannel@` |

## Workflows

### 1. List / filter by name

```bash
ae-cli engage-scene config-channel list --project-id <pid> --channel-type 0
ae-cli engage-scene config-channel list --project-id <pid> --channel-type 1
```

To filter by name, substring-match `data.items[].channel_name`.

### 2. Detail

```bash
ae-cli engage-scene config-channel get --project-id <pid> --channel-id <channel_id>
```

Parse `data.channel.config` for URL, auth, user params, and env params.

### 3. Create

Webhook requires `channel_name` and `config.url`. Optional: `testUrl`, auth, user params, env params.

**Preflight (user params):** for each intended `customsParamList[].columnName`, discover and verify the user property via ae-analysis first:

```bash
ae-cli analysis-meta property list --project-id <pid> --scope user --query <keyword> \
  --fields '["prop_name","prop_desc","select_type"]' --limit 50
ae-cli analysis-meta property get --project-id <pid> --table-type user --prop-name <prop_name>
# → use columnName "user:" + prop_name, e.g. user:#account_id
```

Then create the channel:

```bash
ae-cli engage-scene config-channel create \
  --project-id <pid> \
  --channel-name '<name>' \
  --channel-type 0 \
  --config '{"url":"https://...","testUrl":"","authConfig":{"enable":false},"customsParamList":[{"key":"uid","columnName":"user:#account_id","defaultValue":"","systemIdParam":false}],"envParamList":[]}'
```

Returns `data.channel_id`. Created channels start **enabled**.

### 4. Update

Re-verify any new or changed `customsParamList[].columnName` with `analysis-meta property list/get` (ae-analysis skill) before building `--config`.

```bash
ae-cli engage-scene config-channel get --project-id <pid> --channel-id <id>
# If channel_status=1 and changing URL / auth / param definitions:
ae-cli engage-scene config-channel update-status --project-id <pid> --channel-id <id> --channel-status 2
ae-cli engage-scene config-channel update \
  --project-id <pid> --channel-id <id> --channel-name '<name>' --config '<json>'
# Re-enable if needed
ae-cli engage-scene config-channel update-status --project-id <pid> --channel-id <id> --channel-status 1
```

Rename-only on an enabled channel: omit `--config`.

Before changing the system-integration identity (`systemIdParam`), warn the user about risk, then update.

### 5. Copy

```bash
ae-cli engage-scene config-channel get --project-id <pid> --channel-id <id>
ae-cli engage-scene config-channel create \
  --project-id <pid> --channel-name '<name>_copy' --channel-type <0|1> --config '<config from get>'
```

### 6. Enable / disable

```bash
ae-cli engage-scene config-channel update-status --project-id <pid> --channel-id <id> --channel-status 1
ae-cli engage-scene config-channel update-status --project-id <pid> --channel-id <id> --channel-status 2
```

If disable fails or the user asks about impact: the channel may still have publishing strategies; suggest checking related config items.

### 7. Operation log

```bash
ae-cli engage-scene config-channel query-log --project-id <pid> --channel-id <id>
```

### 8. Delete

Enabled channels cannot be deleted:

```bash
ae-cli engage-scene config-channel get --project-id <pid> --channel-id <id>
# If channel_status=1 → update-status 2 first (with user confirmation)
ae-cli engage-scene config-channel delete --project-id <pid> --channel-id <id> --yes
```

## Do not

- Treat engage push channels as config-center channels (`channel_type` meanings differ)
- Run `delete` without explicit user confirmation
