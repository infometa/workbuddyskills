# List / NList 列表查询

## 何时使用

用户要看某个 eBuilder 页面里的表格数据、分页结果、真实总数，或需要先知道有哪些可搜索字段/固定条件时使用。

先按 [`context-routing.md`](context-routing.md) 拿到 `context`，再按 `context.listKind` 分流：**`List` 走 `list.*`，`NList` 走 `nlist.*`，两套接口不要互相试跑。**

## 请求头契约（CLI 注入，Agent 不手写）

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## operation

| operation | risk | 用途 |
| --- | --- | --- |
| `ebuilder-form.list.config` | read | 读传统表格 List 的基础设置、显示列、排序、搜索、统计和固定条件 |
| `ebuilder-form.list.query` | read | 按 List 运行时接口查分页数据和真实总数 |
| `ebuilder-form.nlist.config` | read | 读数据列表 NList 的页面、组件与 `comps[1].config` 运行时配置 |
| `ebuilder-form.nlist.query` | read | 按 NList eblist 运行时接口查分页数据和真实总数 |

四个 operation 都接受 `context`（推荐）或等价的定位字段（`appId` / `apiPrefix` / `objId` / `listId` / `hostPageId` / `listKind`）。

### `list.query` 查询参数

| 字段 | 说明 |
| --- | --- |
| `pageNo` / `pageSize` | 分页；默认小页读取，用户没要求全量时不要放大 |
| `allPages` | 拉全部页；预计达到或超过 100 页时 CLI 会拒绝（见失败处理） |
| `searchParamData` / `filterCondition` | 搜索与固定条件对象，结构以 `list.config` 返回为准 |
| `orderParams` | 排序参数数组 |
| `tableuid` | 每次查询生成的随机值，一般来自 `list.config`，不要手工构造 |
| `passid` / `cid` | 默认取上下文的 `objId`；只有页面运行上下文明确给出其他值时才显式传 |

### `nlist.query` 查询参数

| 字段 | 说明 |
| --- | --- |
| `pageNo` / `pageSize` / `allPages` | 同上 |
| `compId` | 目标组件 ID，来自 `nlist.config` |
| `tableuid` / `refPluginPackageId` | 运行时透传标识 |
| `customConfig` | NList 的 LZW 数字串编码配置对象，**必须用 `nlist.config` 的返回值，不要手工拼** |
| `filter` / `fieldFilter` / `pageFilter` | 过滤条件，结构以 `nlist.config` 为准 |

## 处理链

1. `context.resolve` 拿 `context` 与 `listKind`。NList 的 `listId` 以配置 `comps[1].config.ebListId` 为准、`objId` 以该配置的 `objId` 为准；菜单 `pageId` 只用于取页面信息，不要拿它和 `ebListId` 反复匹配；`comps[1]`、`config`、`ebListId` 或 `objId` 缺失时停止并报告结构问题，不要扫描其他组件回退。
2. 需要知道可搜索字段或固定条件时，先跑对应的 `config`（`list.config` / `nlist.config`）。
3. 组装查询条件跑 `query`。
4. 结果摘要给用户：条数、总数、是否还有更多。**不要原样粘贴超长 JSON。**

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.list.config --input-json '{"context":{"objId":"121000000000000001","listId":"1001","listKind":"List"}}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.list.query --input-json '{"context":{"objId":"121000000000000001","listId":"1001","listKind":"List"},"pageNo":1,"pageSize":20}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.nlist.query --input-json '{"context":{"objId":"121000000000000001","listKind":"NList"},"pageNo":1,"pageSize":20}'
```

## 失败处理

| subtype | 含义 | 处置 |
| --- | --- | --- |
| `list_context_invalid` | 上下文缺少 List 所需字段 | 重跑 `context.resolve`，不要手工补 `listId` |
| `nlist_context_invalid` | 上下文缺少 NList 所需字段 | 同上 |
| `list_kind_invalid` | `listKind` 不是 `List` / `NList` | 以 `context.resolve` 返回值为准 |
| `list_id_required` / `host_page_id_required` | 缺少列表/页面标识 | 回 `context.resolve` 补齐 |
| `nlist_config_missing` / `nlist_component_missing` | 拿不到 NList 组件配置 | 先跑 `nlist.config`；仍缺失说明该页面不是 NList，改用 `list.*` |
| `nlist_config_invalid` / `custom_config_invalid` | `customConfig` 非法 | 用 `nlist.config` 返回值原样回传，不要手工改写 |
| `page_size_too_large` | 单页条数超限 | 调小 `pageSize` 分页读取，不要一次拉全量 |
| `page_type_invalid` / `page_response_invalid` | 分页响应异常 | 停止并原样反馈，不要换页重试 |
| `too_many_pages` | 查询全部页达到或超过 100 页预算 | 请用户增加筛选条件；**不得**拆成多次单页查询规避预算 |
| `count_invalid` | 总数不可用 | 如实说明总数未知，不要拿行数冒充总数 |
| `session_expired` | 登录态失效 | 引导用户断开并重新连接本连接器以重新登录，然后从只读步骤重新开始 |

## 红线

- 单页大小受 CLI 限制，超限时按错误提示调小，不要绕过。
- `customConfig` 是 CLI 内部编码，禁止自行构造或改写。
- 明细展开会产生重复行，统计条数时以 `query` 返回的真实总数为准，不要自行去重。
