# 菜单定位与上下文解析

## 何时使用

用户给了菜单名、页面 URL，或需要拿到 `appId` / `apiPrefix` / `objId` / `listId` / 页面地址时使用。这是几乎所有其它 operation 的前置步骤。

## 请求头契约（CLI 注入，Agent 不手写）

CLI 发往 E10 的每个请求都自动携带以下三项用户信息参数，缺一不可（业务入参里不要传这些字段，也不要手工拼装请求头）：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## operation

| operation | risk | 必填 | 说明 |
| --- | --- | --- | --- |
| `ebuilder-form.menu.search` | read | `menuKeywords` | 按业务关键词查询当前账号有权限访问的 eBuilder 表格/数据列表菜单 |
| `ebuilder-form.context.resolve` | read | 至少一种定位输入 | 从菜单关键词、页面 URL、`objId` 或现有 `context` 解析出完整上下文 |
| `ebuilder-form.views.list` | read | `objId` | 枚举某个表单对象下的 List/NList 视图 |

### 定位输入（任选其一，命中多条时报错而非猜）

| 字段 | 说明 |
| --- | --- |
| `menuKeywords` | 菜单关键词数组，最多 5 个；给菜单名时用这个 |
| `menu` / `menuId` | 菜单名或菜单 ID |
| `url` | E10 列表页面 URL；支持 `/sp/ebdfpage/list`、`viewport` 和 `/ebdapp/view` 三种形态 |
| `appId` / `objId` / `listId` | 已拿到的上下文片段，用于补全 |
| `context` | 上一次 `context.resolve` 的返回对象，原样回传可跳过重复搜索 |
| `listKind` | `List` 或 `NList`；已知时显式传入可避免二次判定 |

### 返回的 `context` 关键字段

`appId`、`apiPrefix`、`objId`、`listId`、`hostPageId`、`listKind`、`menuUrl`、`entryUrl`。

后续 operation 优先传 `context`（整个对象原样回传），避免重复搜索菜单或猜 ID。`context` 里的 `appId` 同时作为字段、选项接口的 `groupId`；没有可靠 `groupId` 时必须从当前应用上下文取得，不要猜测。`context` 里已有的字段不要再用单字段入参重复传，两者冲突会报 `context_conflict`。

## 推荐顺序

1. 有菜单名 → `menu.search` 拿候选菜单；多个候选时**列给用户选择**，不要用第一个。
2. 拿到菜单（或用户直接给了页面 URL）→ `context.resolve` 拿 `context`。
3. 需要切换同一表单的其它视图 → `views.list` 枚举，再回到 `context.resolve` 或直接带 `listId` 查询。

## 命令

按菜单关键词定位：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.menu.search --input-json '{"menuKeywords":["客户档案"]}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.context.resolve --input-json '{"menuKeywords":["客户档案"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.menu.search --input-json '{"menuKeywords":["客户档案"]}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.context.resolve --input-json '{"menuKeywords":["客户档案"]}'
```

按页面 URL 解析（把用户给的整串 URL 原样传入，不要手工截取参数）：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.context.resolve --input-json '{"url":"https://<用户域名>/sp/ebdfpage/list/0/123456"}'
```

## 失败处理

| subtype | 含义 | 处置 |
| --- | --- | --- |
| `keywords_required` | 未提供任何定位输入 | 至少补一种：`menuKeywords` / `url` / `objId` / `context` |
| `menu_not_found` | 菜单名未命中 | 换更通用关键词重试一次；仍无命中就向用户索取菜单全称或页面 URL |
| `menu_ambiguous` / `menu_not_unique` | 菜单多命中 | **列候选让用户选**，不要自动取第一条 |
| `menu_response_invalid` / `deployment_response_invalid` | 响应结构异常 | 停止并原样反馈，不要换接口重试 |
| `url_invalid` / `url_type_missing` / `url_id_missing` / `url_origin_required` | URL 无法解析 | 向用户索取完整 URL（含域名），不要手工拼 |
| `url_cross_origin` | URL 域名与当前登录环境不一致 | 确认用户给的是当前环境的地址，不要跨环境解析 |
| `url_app_conflict` / `url_menu_conflict` / `url_id_conflict` / `url_type_conflict` | URL 与其它入参冲突 | 只保留 URL，去掉冲突入参 |
| `api_prefix_invalid` / `api_prefix_conflict` | apiPrefix 非法或冲突 | 以 `context.resolve` 返回为准，不要手工指定 |
| `app_conflict` / `context_conflict` / `input_conflict` | 入参互相冲突 | 只保留一种定位来源 |
| `session_expired` | 登录态失效 | 引导用户断开并重新连接本连接器以重新登录，然后从只读步骤重新开始 |

## 红线

- 禁止从 `menuId`、`appId`、`listId`、`objId` 互相猜测，缺哪个就用 `context.resolve` 补。
- 禁止把未出现在 `ebuilder-form schema` 中的能力当作可用 operation。
