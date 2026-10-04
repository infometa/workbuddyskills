# AE Tracking Capability API (internal reference)

> **Terminology**: authentication = CLI token | capability = gateway-registered operation | tracking plan = program | upload = save xlsx | delete = clear program | query/fetch = read program

> This file is the implementation basis for `src/core/tracking-client.ts`, maintained for internal contributors.
> **Skill body should not reference this document** — skill users interact via CLI commands and do not need to know underlying endpoints.
> xlsx format contract is in `xlsx-schema.md`, not here.

The AE CLI must call common-service through capability gateway URLs under `/api/cli/`.
The legacy common-service endpoints are wrapped server-side by these capabilities and must not be
called directly from `ae-cli`.

## Authentication

All capability requests use the CLI token chain:

- Header: `cli-token: <token>`
- Do not send `authorization: bearer ...`.
- Do not send `access_token` form fields.

## 响应统一包装

```json
{ "return_code": 0, "return_message": "success", "showStackMessage": false, "data": ... }
```
- `return_code === 0` 为成功；非 0 抛错，取 `return_message`
- Empty project query may return no `data`.

## Capabilities

### 1. `track.program.query`

获取项目唯一的埋点方案。

- Method: `POST`
- URL: `/api/cli/analysis/v1/capabilities/track.program.query/execute`
- Input:

```json
{ "project_id": 1603 }
```

- Response `data` 结构（事件池 / 事件属性池 / 公共属性 / 用户属性）：

```jsonc
{
  "projectId": 1603,
  "events": [
    { "eventName": "...", "displayName": "...", "eventDesc": "...", "eventTag": "...",
      "props": ["prop_name", "parent.child"], "propInfosOnEvent": [{"name":"...","hasReported":false}] }
  ],
  "eventProps": [ { "name": "...", "displayName": "...", "type": "string", "desc": "..." } ],
  "commonEventProps": [ /* 同 eventProps */ ],
  "userProps": [
    { "name": "...", "displayName": "...", "type": "datetime",
      "propTag": "时间类", "updateType": "user_setOnce" }
  ]
}
```

空项目：`data` 不存在，直接 `{ return_code: 0, return_message: "success" }`。

### 2. `track.program.delete`

一次清空整个项目的方案（事件 / 事件属性 / 公共属性 / 用户属性）。

- Method: `POST`
- URL: `/api/cli/analysis/v1/capabilities/track.program.delete/execute`
- Input:

```json
{ "project_id": 1603 }
```

### 3. `track.program.excel_save`

批量上传 xlsx。

Upload is a two-step capability-gateway flow:

1. Upload the xlsx as an input file.

   - Method: `POST`
   - URL: `/api/cli/analysis/v1/input-files`
   - Content-Type: `multipart/form-data`
   - Form fields:
     - `project_id`
     - `purpose`: `track.program.xlsx`
     - `file`: xlsx binary
   - Response includes `input_file_id`.

2. Execute the save capability.

   - Method: `POST`
   - URL: `/api/cli/analysis/v1/capabilities/track.program.excel_save/execute`
   - Input:

```json
{ "project_id": 1603, "input_file_id": "...", "lang": "zh" }
```

- Agents MUST pass `lang` with the generated xlsx language (`zh` / `en` / `ja` / `ko`) so the backend resolves localized sheet names and headers consistently.
- Response: `{ return_code: 0, return_message: "success" }` on success.

**合并语义**：对事件走 **merge-by-name**（同名不覆盖、新名新增）。若要完全替换，
必须先调 `delete` 端点清空再上传。

## 类型枚举（AE 后端接受值）

### PropType（事件属性 / 公共属性 / 用户属性 `type` 字段）
| canonical | 说明 |
|---|---|
| `string` | 文本 |
| `number` | 数值 |
| `bool` | 布尔 |
| `datetime` | 日期时间 |
| `object` | 对象（单对象，含子属性） |
| `array_row` | 对象数组（允许 `父名.子名` 嵌套子属性） |
| `array_string` | 字符串数组 |

### UpdateType（用户属性 `updateType` 字段）
| canonical | 语义 |
|---|---|
| `user_set` | 覆盖赋值 |
| `user_setOnce` | 仅首次赋值 |
| `user_add` | 数值累加 |

## v2（暂未实现）

- UI「逐个添加」通向单事件 CRUD 接口，v1 走 `track.program.excel_save` 统一入口
- 列项目、校验错误响应等见 plan 文档的"未抓端点"清单
