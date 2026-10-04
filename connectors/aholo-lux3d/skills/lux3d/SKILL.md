---
name: lux3d
description: "Use the existing Lux3D MCP server to check balance, quote and create 3D or image tasks, and retrieve results."
version: "0.1.1"
author: "Aholo"
---

# Aholo Lux3D for WorkBuddy

This `SKILL.md` is the complete, self-contained WorkBuddy instruction set. Use
only the installed `lux3d-mcp` server and its discovered tool schemas. The
Connector sends the user's saved China-region API Key in the MCP
`Authorization` header. Never ask for the key in chat or put it in tool
arguments, a URL, or a generated artifact. Communicate in the user's language.

The WorkBuddy credential form labels this secret `apiKey`. It is the same
China-region Lux3D OpenAPI apiKey available from
https://labs.aholo3d.cn/api-keys, not a separate MCP credential. If the remote
MCP service reports `appKey missing`, guide the user to enter that apiKey in
the WorkBuddy Connector credential form and reconnect. Then use
`getlux3daccountbalance` to verify the connection. Do not ask the user to
paste the apiKey into chat or a tool argument.

## Available MCP tools

| Tool | Purpose |
| --- | --- |
| `getlux3daccountbalance` | Get the current account balance and the `uniqueId` needed for a quote. |
| `post_quotelux3dopenapirequests` | Quote a numbered plan of original Lux3D OpenAPI requests. |
| `post_createmultimodaltoimagetask` | Create one image from text, references, or both. |
| `post_createimagetofourviewtask` | Create four views from an image or prompt. |
| `post_createimgto3dtask` | Create a 3D model from an image. |
| `post_createtextto3dtask` | Create a 3D model from text. |
| `post_creatematerialtransfertask` | Transfer material to a model. |
| `post_createmultiformatexporttask` | Export a model to another format. |
| `gettask` | Read a known task and its returned artifacts. |
| `get_listtasks` | List the authenticated account's tasks. |

The six create tools are paid operations. Prepare their actual input using the
installed tool's `inputSchema`. Do not call a create tool just to discover its
price. Use `getlux3daccountbalance` with `source: 4` and, where the discovered
schema accepts it, `agentName: "workbuddy"`. Read the returned `uniqueId` and
balance. For `post_quotelux3dopenapirequests`, use that `uniqueId`, `source: 4`,
`agentName: "workbuddy"`, and the exact plan in `items`. Do not let the user or
the model choose a different source or Agent name.

## Convert create tool names before quoting

The quote service recognizes **OpenAPI paths**, not MCP tool names. For each
planned create tool, set `items[N].endpoint.method` to `POST` and
`items[N].endpoint.path` to the path in this table. Never put the tool name,
the MCP URL, a domain, a query string, or a `/global` prefix in `path`.

| Create tool | Quote `endpoint.path` |
| --- | --- |
| `post_createmultimodaltoimagetask` | `/lux3d/v1/generate/multimodal-to-image/task/create` |
| `post_createimagetofourviewtask` | `/lux3d/v1/generate/image-to-four-view/task/create` |
| `post_createimgto3dtask` | `/lux3d/v1/generate/img-to-3d/task/create` |
| `post_createtextto3dtask` | `/lux3d/v1/generate/text-to-3d/task/create` |
| `post_creatematerialtransfertask` | `/lux3d/v1/generate/material-transfer/task/create` |
| `post_createmultiformatexporttask` | `/lux3d/v1/multi-format-export/task/create` |

Each `items` key is a positive integer string (`"1"`, `"2"`, ...). Its
`parameters.pathParameters` and `parameters.queryParameters` are the literal
strings `"{}"` for these create endpoints. `parameters.body` is a **string
containing a serialized JSON object**, with exactly the same request fields
and values planned for the create tool. It is not an embedded object. Keep the
actual MCP tool call within its discovered input schema; do not add quote
metadata to the create tool's generation body.

For example, when planning `post_createtextto3dtask` with request body
`{"prompt":"a wooden chair","version":"G1"}`, the quote call's body is:

```json
{
  "source": 4,
  "agentName": "workbuddy",
  "uniqueId": "<uniqueId returned by getlux3daccountbalance>",
  "items": {
    "1": {
      "endpoint": {
        "method": "POST",
        "path": "/lux3d/v1/generate/text-to-3d/task/create"
      },
      "parameters": {
        "pathParameters": "{}",
        "queryParameters": "{}",
        "body": "{\"prompt\":\"a wooden chair\",\"version\":\"G1\"}"
      }
    }
  }
}
```

Pass this request in the argument shape exposed by
`post_quotelux3dopenapirequests`; its MCP `inputSchema` determines whether
the request is a direct argument object or nested under a body parameter.
Quote the complete intended plan, not a simplified or cheaper variant. Show
the returned total credits, relevant per-item costs, and expiry or pricing
scope when present. Use the quote response as an estimate; it is not a task
submission or a reservation of credits.

Once the user has authorized the displayed cost and the plan remains the same,
call the corresponding create tool with the exact quoted generation request.
If the plan or price changes, quote again. Do not infer a successful creation
from a timeout or retry an uncertain paid call automatically. Recover with
`gettask` for a known task ID or `get_listtasks` for the authenticated account.
Keep task IDs as returned and report only status and artifact URLs actually
returned by those tools. These read tools and the balance tool are not quote
items.

## Inputs, delivery, and errors

Remote MCP tools cannot read a path on the user's computer. For image or model
inputs, obtain a service-accessible HTTP(S) URL through a WorkBuddy capability
available in the current session. If no such capability exists, explain the
missing input and stop before a paid create call. Never send a local path as an
image or model URL.

Give the current user a usable artifact URL returned by `gettask`, or use an
actual WorkBuddy download tool and report its real local output. Explain that
temporary URLs may expire. Do not present a path on the MCP server as a local
file or promise offline preview, Blender assembly, or durable hosting unless
an available tool actually produced it.

For authentication errors, ask the user to reconnect the Connector with a new
key from its credential help link. Timeouts and service failures do not by
themselves mean the key is invalid. Do not expose keys, internal paths,
traces, or another account's task details.
