---
name: wecomcli-smartpage
description: 企业微信智能文档（原名智能主页，smartpage）管理技能。提供智能文档的创建（将本地 Markdown 文件发布为智能文档）与内容导出（异步导出为 Markdown）能力。适用场景：(1) 将一个或多个本地 Markdown 文件创建为智能文档 (2) 异步导出智能文档内容为 Markdown。支持通过 docid 或文档 URL 定位文档。当用户明确提到「智能文档」「智能主页」，或链接形如 `https://doc.weixin.qq.com/smartpage/xxx` 时触发该技能。注意：普通文档（`/doc/*`）请用 `wecomcli-doc`；在线表格（`/sheet/*`）请用 `wecomcli-sheet`；智能表格（`/smartsheet/*`）请用 `wecomcli-smartsheet`。
metadata:
  requires:
    bins: ["wecom-cli"]
  cliHelp: "wecom-cli doc --help"
---

# 企业微信智能文档管理

> `wecom-cli` 是企业微信提供的命令行程序，所有操作通过执行 `wecom-cli` 命令完成。

资源型技能，负责**智能文档**（原名智能主页，`/smartpage/*`）的创建与内容导出。

## 调用方式

通过 `wecom-cli` 调用，品类为 `doc`：

```bash
wecom-cli doc <tool_name> '<json_params>'
```

## 返回格式说明

所有接口返回 JSON 对象，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `errcode` | integer | 返回码，`0` 表示成功，非 `0` 表示失败 |
| `errmsg` | string | 错误信息，成功时为 `"ok"` |

当 `errcode` 不为 `0` 时，说明接口调用失败，可重试 1 次；若仍失败，将 `errcode` 和 `errmsg` 展示给用户。

### 特殊错误码

| errcode | errmsg | 含义 | 处理方式 |
|---------|--------|------|----------|
| `851002` | `incompatible doc type` | 文档品类与所调用的接口不匹配 | 确认目标 URL 为 `/smartpage/*`；若不是，请跳转到对应品类的 skill |

## 接口详述

### 创建智能文档

创建智能文档（原名智能主页），支持传入标题和多个子页面。每个子页面可指定标题、内容类型和本地文件路径。创建成功返回 `docid` 和 `url`。

>  **特殊语法**：此命令必须使用 `+smartpage_create`（带 `+` 前缀），加号不可省略；该 `+` 仅适用于此命令，不要泛化到其他 `doc` 子命令。

**命令**

```bash
wecom-cli doc +smartpage_create '<JSON 参数>'
```

**参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `title` | string | 否 | — | 智能文档标题 |
| `pages` | array | 是 | — | 子页面列表 |
| `pages[].page_title` | string | 否 | — | 子页面标题 |
| `pages[].content_type` | int | 否 | 1 | 内容类型：1-Markdown，0-Text（纯文本） |
| `pages[].page_filepath` | string | 否 | — | 子页面内容对应的本地文件路径 |

**注意事项**

- `content_type` **必须与文件实际内容匹配**：`.md` 文件或包含 Markdown 语法的内容必须传 `1`，仅纯文本才传 `0`。绝大多数场景应传 `1`。
- `docid` 仅在创建时返回，需妥善保存。
- 每个子页面的 Markdown 文件大小不得超过 **10MB**，超过会导致创建失败；如文件过大，需先拆分为多个子页面再创建。
- 智能文档还支持背景块（`<card>`）、分栏（`<grid>`）等扩展语法，详见 [references/smartpage-create.md](references/smartpage-create.md)。

### 导出智能文档内容

获取智能文档的完整内容，导出为 Markdown。采用**异步两步操作**：先用 `smartpage_export_task` 提交导出任务拿到 `task_id`，再用 `smartpage_get_export_result` 轮询任务，直到 `task_done` 为 `true` 时返回 `content`。

**第一步：提交导出任务**

```bash
# 通过 docid
wecom-cli doc smartpage_export_task '{"docid": "DOCID", "content_type": 1}'
# 通过 url
wecom-cli doc smartpage_export_task '{"url": "https://doc.weixin.qq.com/smartpage/xxx", "content_type": 1}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `docid` | string | 与 `url` 二选一 | — | 智能文档的 docid |
| `url` | string | 与 `docid` 二选一 | — | 智能文档的访问链接 |
| `content_type` | int | 是 | — | 导出内容格式，目前仅支持 `1`（Markdown） |

**第二步：轮询导出结果**

```bash
wecom-cli doc smartpage_get_export_result '{"task_id": "TASK_ID"}'
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `task_id` | string | 是 | — | 由 `smartpage_export_task` 返回的任务 ID |

**使用规则**

- 第一步获取 `task_id` 后，携带其调用第二步；若 `task_done` 为 `false` 则继续轮询，直到 `task_done` 为 `true`，返回的 `content` 字段即为完整 Markdown 内容。

参见 [API 详情](references/smartpage-export.md)。

## 跨技能依赖

| 依赖技能 | 典型协作场景 | 数据流向 |
|---|---|---|
| `wecomcli-msg` | 用户要求把智能文档链接发给某人/某群 | 本 skill 创建后返回 `url` → `wecomcli-msg` 发送链接 |
