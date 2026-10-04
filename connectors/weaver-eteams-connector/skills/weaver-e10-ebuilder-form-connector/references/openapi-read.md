# OpenAPI 只读查询（按 objId）

## 何时使用

已知表单对象 `objId`，要查单条详情、按条件分页查表单数据或查总数时使用。走 E10 表单 OpenAPI（`getDataById` / `getAllData` / `getAllDataCount`）。

若目标不是 OpenAPI 而是已发布的自定义接口（有 `interfacePk`），改走 [`custom-api.md`](custom-api.md)。两者同时出现且用户没指定时，先向用户消歧。

## 请求头契约（CLI 注入，Agent 不手写）

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## operation

| operation | risk | 必填 | 用途 |
| --- | --- | --- | --- |
| `ebuilder-form.openapi.detail` | read | `objId` + `dataId` | 按数据 ID 取单条详情 |
| `ebuilder-form.openapi.query` | read | `objId` | 表单级分页查询 |
| `ebuilder-form.openapi.count` | read | `objId` | 表单级总数查询 |

### 公共参数

| 字段 | 说明 |
| --- | --- |
| `objId` | 表单对象 ID（必填），来自 `context.resolve` |
| `mainTable` | 主表查询条件对象；字段名以 [`fields-browser.md`](fields-browser.md) 取到的写入键为准 |
| `pageNo` / `pageSize` | 分页（`query` 专用）；默认小页读取 |
| `isReturnDetail` | 是否返回明细表数据 |
| `fieldNoFindIgnore` | 字段不存在时忽略而非报错；**不要为了绕过报错而默认打开** |

## 处理链

1. `context.resolve` 拿 `objId`（必要时先 `menu.search`）。
2. 需要条件字段时先 `fields.get` 确认写入键。
3. `openapi.count` 确认量级 → `openapi.query` 小页读取 → 需要单条完整数据时 `openapi.detail`。
4. 摘要给用户：命中数、已读页数、是否还有更多。**不要原样粘贴超长 JSON。**

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.count --input-json '{"objId":"121000000000000001","mainTable":{}}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.query --input-json '{"objId":"121000000000000001","mainTable":{},"pageNo":1,"pageSize":20}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.detail --input-json '{"objId":"121000000000000001","dataId":"1234567890123456789"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.query --input-json '{"objId":"121000000000000001","mainTable":{},"pageNo":1,"pageSize":20}'
```

## 失败处理

| subtype | 含义 | 处置 |
| --- | --- | --- |
| `obj_id_required` | 缺少 `objId` | 回 `context.resolve` 补齐，不要从其它 ID 猜 |
| `field_required` | 缺少必要字段 | 补字段后重试 |
| `field_invalid` | 字段名不被接口接受 | 用 `fields.get` 的 `config.dataKey` 重新取值 |
| `http_error` | HTTP 层失败 | 保留业务消息，停止后续步骤，不重试 |
| `business_error` | 服务端业务失败 | 原样转达业务消息，不要改写或美化 |
| `response_invalid` | 响应结构异常 | 停止并原样反馈，不要换接口重试 |
| `session_expired` | 登录态失效 | 引导用户断开并重新连接本连接器以重新登录，然后从只读步骤重新开始 |

## 红线

- 长整型 `objId` / `dataId` 一律按字符串传递，避免精度丢失。
- 不要把 `fieldNoFindIgnore` 当成绕过字段校验的开关。
- 查询结果只是"当前页"，汇报总数时必须用 `count` 的返回值。
