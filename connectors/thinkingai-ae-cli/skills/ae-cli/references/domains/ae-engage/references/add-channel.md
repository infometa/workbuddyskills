# ae-engage engage-setting channel create

> Trigger keywords: push channel · Mapped command: `ae-cli engage-setting channel create` · Capability id: `engage-setting.channel.create`

Create a new Engage **运营设置** push channel (not config-center channels; those use `engage-scene config-channel`).

**First decide channel kind:** Webhook (`channelType=1`) and Client (`channelType=3`) share the same CLI command and outer `--req` fields, but **`config` / `pushIdType` / custom-param prefixes differ**. Do not reuse a webhook payload for client (or the reverse).

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--req` | json | Yes | Channel creation request JSON object |

## `--req` Object Fields (common)

| Field | Type | Required | Description |
|------|------|------|------|
| `channelType` | number | Yes | `1` webhook · `3` client (see below) |
| `channelSubBizType` | string | Yes | must match type: `webhook` or `client` |
| `channelName` | string | Yes | channel name |
| `pushIdType` | string | Yes | prefixed property code — **rules differ by channel kind** |
| `config` | string | Yes | channel config JSON **string** — **shape differs by channel kind** |
| `enableTouchEvent` | number | Yes | reach funnel: `0` off · `1` on |
| `eventClickName` | string | Yes when funnel on | click event (e.g. `ops_click`) |
| `eventDeliveryName` | string | Yes when funnel on | delivery event (e.g. `ops_view`) |
| `touchEventSource` | string | Yes | usually `custom` for custom event names |

The outer Capability input uses `project_id` and `req`; fields inside `req` keep the native camelCase DTO shape. The Hermes Capability handler assigns the outer `--project-id` to `req.projectId`.

## Response shape

The created channel is under `data.item`; response keys recursively use snake_case (`channel_id`, `channel_status`, `channel_type`).

## Webhook vs Client (read this first)

| | **Webhook** | **Client** |
|--|-------------|------------|
| `channelType` | `1` | `3` |
| `channelSubBizType` | `webhook` | `client` |
| `config.url` | **HTTP(S) callback URL** (server endpoint that receives the push) | **Client config key / scene id** (e.g. `popup`, `abtest`, `difficulty_ratio`) — **not** an `http://` URL |
| `pushIdType` | Prefer **`user:`** user properties (e.g. `user:#account_id`) | **`user:`** or **`client:`** (e.g. `user:#account_id`, `client:#distinct_id`) |
| `config.userParamsList[].columnName` | Prefer **`user:`** only (validated against user dispatch props) | **`user:`** and/or **`client:`** (validated against user props + client-param list) |
| `config.authConfig` | Optional HTTP auth (`enable` / `secretKey` / `secretType`) | Usually omit / unused |
| `config.paramsList` | Content template — same type enum for both | Same |
| Reach funnel | Same outer fields | Same |

Prefix convention (aligned with 配置中心通道管理):

- User property → `user:<prop_name>` (e.g. `user:#account_id`, `user:city`)
- Client parameter → `client:<column_name>` (e.g. `client:#os`, `client:#distinct_id`)
- Never pass bare `#account_id` / `city` for `pushIdType` or `columnName`

## Preflight

```bash
# User properties (both kinds; required for webhook custom params)
ae-cli analysis-meta property list --project-id <id> --scope user --query <kw> --limit 50

# Client parameters (client channel pushId / custom params)
ae-cli engage-setting client-param list --project-id <id>

# Optional: copy a real config shape
ae-cli engage-setting channel list --project-id <id>
ae-cli engage-setting channel get --project-id <id> --channel-id <id>
```

If a property / client-param is not found after list/get, stop — do not invent codes.

---

## A. Webhook channel

```text
channelType=1, channelSubBizType=webhook
```

### Webhook `config` JSON (stringified into `req.config`)

```json
{
  "url": "https://example.com/hook",
  "paramsList": [
    { "key": "title", "keyName": "标题", "type": "STRING", "required": 0 },
    { "key": "body", "keyName": "动态正文", "type": "TEXT", "required": 0, "tips": "$[user:city]" }
  ],
  "userParamsList": [
    {
      "key": "uid",
      "columnName": "user:#account_id",
      "defaultValue": "-",
      "columnDesc": "账号 ID"
    }
  ],
  "authConfig": { "enable": false }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `url` | Yes | Real HTTP(S) webhook endpoint |
| `paramsList` | No | Content template definitions |
| `userParamsList` | No | Custom params; `columnName` = `user:…`; `defaultValue` must be non-blank |
| `authConfig` | No | When `enable=true`, `secretKey` required |

Do **not** put `client:…` in webhook `userParamsList` unless you have confirmed the environment accepts it — create validation uses **user** dispatch props.

### Webhook example

```bash
ae-cli engage-setting channel create --project-id 1 \
  --req '{"channelType":1,"channelSubBizType":"webhook","channelName":"demo_webhook","pushIdType":"user:#account_id","config":"{\"url\":\"https://example.com/hook\",\"paramsList\":[{\"key\":\"title\",\"keyName\":\"标题\",\"type\":\"STRING\",\"required\":0}],\"userParamsList\":[{\"key\":\"city\",\"columnName\":\"user:city\",\"defaultValue\":\"-\"}],\"authConfig\":{\"enable\":false}}","enableTouchEvent":1,"eventDeliveryName":"ops_view","eventClickName":"ops_click","touchEventSource":"custom"}'
```

---

## B. Client channel

```text
channelType=3, channelSubBizType=client
```

### Client `config` JSON (stringified into `req.config`)

```json
{
  "url": "popup",
  "paramsList": [
    { "key": "messageType", "keyName": "消息类型", "type": "NUM", "required": 0 },
    {
      "key": "gifts",
      "keyName": "礼包",
      "type": "OBJ_ARRAY",
      "required": 0,
      "objArray": [
        { "key": "gift_name", "keyName": "道具名", "type": "STRING", "required": 0 },
        { "key": "count", "keyName": "数量", "type": "NUM", "required": 0 }
      ]
    }
  ],
  "userParamsList": [
    {
      "key": "os",
      "columnName": "client:#os",
      "defaultValue": "-",
      "columnDesc": "操作系统"
    },
    {
      "key": "city",
      "columnName": "user:city",
      "defaultValue": "-",
      "columnDesc": "城市"
    }
  ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `url` | Yes | **Client scene / config key** (string id like `popup`, `abtest`) — not an HTTP URL |
| `paramsList` | No | Content template (same type enum as webhook) |
| `userParamsList` | No | `columnName` may be `user:…` **or** `client:…`; `defaultValue` non-blank |
| `authConfig` | No | Usually omit |

`pushIdType` examples: `user:#account_id`, `client:#distinct_id` (discover client codes via `client-param list`).

### Client example

```bash
ae-cli engage-setting channel create --project-id 1 \
  --req '{"channelType":3,"channelSubBizType":"client","channelName":"demo_client","pushIdType":"client:#distinct_id","config":"{\"url\":\"popup\",\"paramsList\":[{\"key\":\"type\",\"keyName\":\"场景\",\"type\":\"STRING\",\"required\":0}],\"userParamsList\":[{\"key\":\"os\",\"columnName\":\"client:#os\",\"defaultValue\":\"-\"}]}","enableTouchEvent":0,"eventClickName":"","eventDeliveryName":"","touchEventSource":"custom"}'
```

---

## Content template types (`paramsList[].type`) — both kinds

| type | Meaning |
|------|---------|
| `STRING` | 文本 |
| `TEXT` | 动态文本 (`$[user:…]` / `$[client:…]` placeholders) |
| `NUM` | 数值 |
| `OBJ_ARRAY` | 对象组 (`objArray` children required) |
| `DATE` | 日期 |
| `DATE_TIME` | 时间 |
| `ARRAY` | 列表 |
| `SINGLE_SELECT` | 单选下拉 (**requires** existing config-table `tableId`) |
| `RADIO` | 单选 |

`required`: `0` optional · `1` required. `OBJ_ARRAY` children: `STRING` / `NUM` / `DATE` / `DATE_TIME` / `TEXT` / `SINGLE_SELECT` only.

## Other channel types

`channelType` also supports `2` APP_PUSH (`fcm` / `aurora` / `apns`), `4` WECHAT, `5` DOU_YIN — each has its own `config` DTO. Discover with `channel get` on an existing channel of that subtype before creating; do not invent FCM/APNs secrets.

## Additional Constraints

- `req.config` must be a **JSON string**, not a nested object in the CLI flag.
- Match `channelSubBizType` to `channelType` (`1`↔`webhook`, `3`↔`client`).
- When `enableTouchEvent=1`, set `touchEventSource` plus delivery/click event names.
- For webhook tests, prefer a known mock URL from `channel get` rather than inventing production endpoints.

## Safety Constraints

This command is a **write operation**. Verify `--req` completeness and the correct webhook vs client rules before executing.
