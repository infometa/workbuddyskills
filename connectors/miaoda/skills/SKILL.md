---
name: miaoda
description: 秒哒（Miaoda）应用搭建平台交互命令，支持通过自然语言对话创建、生成、修改、发布网页/Web应用/小程序/移动App等。
version: 1.0.0
author: miaoda
---

# miaoda-cli

操作秒哒（Miaoda）平台资源的 CLI 工具。秒哒是**对话式全栈应用搭建平台**，通过自然语言描述即可生成包含前端界面、后端服务、数据库结构在内的可部署产品。

## 登录认证

```bash
miaoda login    # 设备授权登录流程；--no-browser 跳过自动打开浏览器
miaoda status    # 查看登录状态，token 过期时自动刷新
miaoda logout    # 删除本地登录凭证
```

## 快捷命令

应用管理：

- `miaoda list-apps --brief` — 列出当前用户的所有应用（精简字段，推荐）
- `miaoda app-detail --app-id <id>` — 获取应用详情，自动附带 `conversationId`
- `miaoda get-context-id --app-id <id>` — 找回丢失的 `conversationId`
- `miaoda conversation-history --app-id <id> --limit 3` — 查看最近的对话历史摘要

创建与修改：

- `miaoda chat --text '创建一个待办事项管理应用'` — 新建应用，进入 PRD 澄清阶段
- `miaoda chat --text '把按钮颜色改成蓝色' --app-id <id> --context-id <id>` — 修改已生成的应用
- `miaoda generate-app --app-id <id> --context-id <id> --watch` — 确认生成应用（仅首次创建时调用一次）
- `miaoda trajectory --app-id <id>` — 轮询对话/生成进度事件

发布部署：

- `miaoda publish --app-id <id> --wait` — 发布到生产环境并等待结果
- `miaoda publish-status --release-id <id>` — 查询指定发布任务的状态

## 输出与解析

除持续事件流命令外，成功结果输出为单个 JSON 对象到标准输出（stdout）。`trajectory`、`chat`（默认流式）与 `generate-app --watch` 则按事件逐行输出 JSON（JSON Lines）；应逐行解析，不能假定整个 stdout 是一个 JSON 对象。诊断与错误信息写入标准错误（stderr），不得用 stderr 中的文本作为成功数据解析。

### `list-apps --brief`

返回平台响应对象，应用数组位于 `data.items`（部分平台响应兼容为 `data.list`）。`--brief` 会将每个应用裁剪为以下字段：

```json
{
  "status": 0,
  "data": {
    "items": [
      {
        "appId": "app_123",
        "name": "待办事项管理",
        "type": "WEB",
        "appFocus": "DESIGNING",
        "host": "https://app_123.appmiaoda.com",
        "updatedAt": "2026-08-07T09:30:00Z"
      }
    ]
  }
}
```

- `appId`：后续命令的应用标识。
- `name`、`type`：应用名称与类型；可为空或随平台扩展。
- `appFocus`：应用生命周期状态，发布前必须使用它做预检。
- `host`：已发布时的生产地址；为空时表示尚无可分享的生产地址。
- `updatedAt`：平台返回的最后更新时间。

### `app-detail`

成功时返回 `{ "status": 0, "data": { ... } }`。CLI 会清理部分内部字段，并默认尽力从 trajectory 补充 `data.conversationId`；补充失败不影响详情查询，因此调用方应接受该字段缺失，并可改用 `get-context-id` 重试。

```json
{
  "status": 0,
  "data": {
    "appId": "app_123",
    "name": "待办事项管理",
    "appFocus": "DESIGNING",
    "conversationId": "conv_456",
    "host": "https://app_123.appmiaoda.com"
  }
}
```

- `data.appId`：应用标识，应与请求的 `--app-id` 一致。
- `data.conversationId`：修改既有应用时与 `appId` 配对传给 `chat` 或 `generate-app`。
- `data.appFocus`：发布资格依据。仅 `DESIGNING`、`RELEASED`、`RELEASE_FAILED` 可继续发布；`NOT_GENERATE`、`WAITING`、`UNDER_CREATING`、`CREATE_FAILED` 应停止发布并根据状态继续生成、等待或处理失败。
- `data.host`：生产地址，仅在已发布且地址可用时对外分享。

### `trajectory`

每个事件单独占一行 JSON。事件 ID 位于 `result.metadata.eventId`，可作为下一次查询的 `--last-event-id`；终止状态为 `result.status.state` 为 `completed`、`input-required`、`failed`，或 `result.final` 为 `true`。PRD 就绪事件中的生成按钮结构如下：

```json
{
  "result": {
    "metadata": { "eventId": 42 },
    "status": { "state": "input-required" },
    "artifact": {
      "parts": [
        {
          "data": {
            "type": "prdAgentAction",
            "is_generated": false,
            "appInfo": { "requirementType": "WEB" },
            "actions": [{ "event": { "name": "generateApp" } }]
          }
        }
      ]
    }
  }
}
```

仅当任意 `result.artifact.parts[].data.actions[]` 中存在 `event.name = "generateApp"`，且 `is_generated` 不为 `true` 时，才调用一次 `generate-app`。普通任务可能不会产生该事件。

### `publish-status`

成功时返回 `{ "status": 0, "data": { "status": "..." } }`，其中 `data.status` 的终态为 `SUCCESS` 或 `FAILED`，进行中为 `PROCESSING`；字段缺失或未知值应按 `UNKNOWN` 处理并继续谨慎轮询或人工确认。

```json
{
  "status": 0,
  "data": {
    "releaseId": "release_789",
    "status": "SUCCESS"
  }
}
```

`publish --wait` 会先输出 `{ "releaseId": "...", "status": "PROCESSING" }`，随后持续输出状态行；遇到 `SUCCESS` 成功结束，遇到 `FAILED` 以错误退出。

## 错误处理与降级

数据命令成功时退出码为 `0`；认证失败、参数校验失败、HTTP/API 错误、请求超时和发布失败均为退出码 `1`。错误信息以 `Error: ...` 或认证提示写入 stderr。`miaoda status` 仅用于交互式检查，未登录或待授权过期时会提示但仍可能以退出码 `0` 结束，自动化流程应在执行数据命令时再以退出码判断认证是否可用。

- **`--app-id` 不存在或无访问权限**：命令以 `1` 退出，stderr 通常包含 `HTTP 404`、`HTTP 403` 或平台 API 错误。不要继续执行 `trajectory`、`chat` 或 `publish`；先执行 `list-apps --brief` 确认可访问的 `appId`。
- **发布前置条件不满足**：先读取 `app-detail` 的 `data.appFocus`。若不在 `DESIGNING`、`RELEASED`、`RELEASE_FAILED`，不要调用 `publish`；对 `NOT_GENERATE`/`WAITING`/`UNDER_CREATING` 等状态，继续等待 trajectory 或按生成流程处理；`CREATE_FAILED` 时先定位生成失败原因。平台拒绝发布时同样以 `1` 退出。
- **token 已过期或刷新失败**：数据命令以 `1` 退出，stderr 会包含 `Token 已过期，刷新失败`、`Token 已过期且无 refresh_token` 或 `未找到有效的登录凭证`，并提示执行 `miaoda login`。重新授权后，从失败步骤重新查询状态；不要假定未完成的发布或生成已经成功。
- **请求超时或网络/API 异常**：以 `1` 退出，可能显示 `Error: request timed out`、`HTTP <status>` 或 `API error (status=<n>)`。保留已知的 `appId`、`conversationId`、`releaseId` 或最后 `eventId`，再用 `app-detail`、`publish-status` 或 `trajectory --last-event-id <n>` 查询，避免重复触发生成或发布。
- **`--app-id` 未配对 `--context-id`**：修改类 `chat`/`generate-app` 命令以 `1` 退出，并明确提示平台会创建新应用。使用 `miaoda get-context-id --app-id <id>` 恢复会话 ID 后重试。

注意事项：

- **`--app-id` 与 `--context-id` 必须成对使用**：仅传 `--app-id` 不传 `--context-id` 不会修改已有应用，平台会静默创建新应用；CLI 会在此情况下报错以防误建。
- **generate-app 仅调用一次**：只在 trajectory 中出现 `event.name = "generateApp"` 按钮（PRD 就绪信号）时调用，且只在首次创建时调用一次。后续修改统一用 `chat`。
- **发布前置条件**：需先检查 `app-detail` 返回的 `data.appFocus`，仅当其为 `DESIGNING`、`RELEASED`、`RELEASE_FAILED` 时才能发布。
- **通用任务无需生成/发布**：报告、PPT、分析文档等任务在 `chat` 阶段直接完成（`needGenerateApp: false`），不涉及 `generate-app` 与 `publish`。
- **URL 使用规范**：编辑器地址 `https://www.miaoda.cn/projects/<app_id>` 仅供本人预览编辑，禁止对外分享；对外分享必须使用发布后的生产地址 `https://<app_id>.appmiaoda.com`。
- **单引号传参**：传递多行文本参数时，使用单引号可防止命令注入攻击，并减少不必要的转义。

## 更多 API

1. `miaoda --help` 查看所有命令
2. `miaoda <command> --help` 查看命令参数详情
