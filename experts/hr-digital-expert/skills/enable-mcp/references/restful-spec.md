# restful.json 能力描述规范（App Capability Gateway 供给侧契约）

> 适用：page-deliver 生成的应用。目标：应用把「能被 Agent 调用的业务能力」以一份静态
> `restful.json` 自描述，平台侧 MCP 网关（deliver-api 的 `list_apps` / `list_app_tools` /
> `call_app_tool`）据此按用户权限发现并调用。

## 1. 文件位置与暴露方式

- 路径：项目根目录 `public/restful.json`（随静态目录自动暴露在 `/restful.json`）。
- 静态站（无 server）：放在 `index.html` 同级，由静态托管直接暴露。
- 大小硬限：256KB。超出视为生成端异常。

## 2. 顶层结构

```json
{
  "specVersion": "1.0",
  "appId": "recruit-funnel-20260601-192630",
  "appName": "招聘漏斗看板",
  "description": "展示招聘各阶段转化情况，支持按部门和日期筛选，可提交候选人备注",
  "tools": []
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `specVersion` | 是 | 固定 `"1.0"` |
| `appId` | 是 | 必须等于 `.deploy-state.json` 的 `projectId`，不是字面 `{project_id}` |
| `appName` | 是 | 应用名，能力视角命名，最长 16 字符 |
| `description` | 是 | 2-3 句话描述应用能做什么、适合什么场景，最长 256 字符 |
| `tools` | 是 | 工具数组，至少 1 个 |

## 3. tools[] 元素

```json
{
  "name": "query_funnel",
  "summary": "按日期区间查询招聘漏斗各阶段人数",
  "method": "GET",
  "path": "/app-mcp/api/funnel",
  "parameters": [
    { "name": "start_date", "in": "query", "type": "string", "required": true, "description": "开始日期 YYYY-MM-DD" },
    { "name": "dept", "in": "query", "type": "string", "required": false, "description": "部门编号，缺省为全部" }
  ],
  "callExample": {
    "good": "{\"start_date\":\"2026-06-01\",\"dept\":\"hr\"}"
  },
  "response": {
    "description": "各阶段人数列表",
    "example": { "stages": [ { "name": "简历筛选", "count": 120 } ] }
  }
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 应用内唯一的工具名，蛇形命名 |
| `summary` | 是 | 给 Agent 看的一句话功能摘要 |
| `method` | 是 | `GET` / `POST` / `PUT` / `DELETE` |
| `path` | 是 | 必须且只能以 `/app-mcp/` 开头，支持 `{param}` 占位符 |
| `parameters` | 否 | 入参定义 |
| `callExample` | 是 | `call_app_tool` args 的正确示例，见下文 |
| `response` | 否 | `{ description, example }` |

### callExample 规则

1. `callExample` 必须且只能包含 `good` 一个 JSON 字符串，因为 `call_app_tool.args` 本身要求传 JSON 字符串
2. `good` 字符串解析后，其键名必须与 `call_app_tool` 的 `args` 契约一致：只能出现 `parameters[].name`，不得携带 HTTP method、path、header、身份或包装字段
3. `good` 必须是能通过该工具必填校验的真实参数值；`body` 参数的值保留参数名这一层，例如 `"{\"item\":{\"name\":\"示例\"}}"`
4. 示例值不得包含敏感数据、真实员工信息或权限信息；身份由网关自动注入，不能作为参数传递

### parameters[] 元素

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 参数名 |
| `in` | 是 | `query` / `path` / `body` |
| `type` | 是 | `string` / `number` / `boolean` / `object` / `array` |
| `required` | 是 | 是否必须提供 |
| `description` | 是 | 参数含义与格式约定 |
| `fields` | object/array 必填 | 第一层字段清单 |

### fields[] 规则

1. 每个 field 包含 `name`、`type`、`required`、`description`
2. `object` 的 `fields` 描述该对象的 JSON 键；嵌套 object/array 递归展开，通常一层足够，最深三层
3. `array` 的 `fields` 描述每个元素对象的 JSON 键
4. 参数、field、服务端解析结果三者必须同名、同类型、同必填性；服务端依赖的每个输入都必须出现在对应链路上
5. description 必须说明业务含义、格式和枚举值，不能只写类型名

### 参数还原矩阵

第三方 Agent 必须仅按以下规则还原请求，生成端也必须按同一矩阵自查：

| 声明位置 | 还原规则 |
|----------|----------|
| `in: "query"` | 作为 URL query 参数发送，参数名即 query key |
| `in: "path"` | 替换路径中的同名 `{param}` 占位符 |
| `in: "body"` 且 `type: "object"` | 序列化为请求 JSON body；`fields[].name` 即第一层 JSON 键 |
| `in: "body"` 且 `type: "array"` | 序列化为请求 JSON body；`fields[].name` 是每个元素对象的 JSON 键 |
| 嵌套 object field | 放在父级字段名下，作为嵌套 JSON object |
| 嵌套 array field | 放在父级字段名下；其 `fields` 描述每个元素对象的键 |

禁止只把字段写在 description 文本里；可机器还原的结构必须进入 `parameters` / `fields`。

## 4. 硬性规则

1. `appId` 必须等于真实 projectId
2. `appName` 最长 16 字符；顶层 `description` 最长 256 字符
3. 每个工具的 `path` 必须且只能以 `/app-mcp/` 开头；不得使用 `/api/`、页面路径或其他普通应用路径
4. 每个工具的 `method` + `path` 必须在服务端真实存在
5. path 模板中的 `{xxx}` 必须有对应 `in:"path"` 参数
6. object/array 参数必须展开 `fields`
7. 每个参数和 field 必须显式声明 `type` 与 `required`，并与服务端解析规则一致
8. 每个工具必须提供 `callExample.good`
9. 服务端不得存在未声明的隐藏必填参数，也不得声明服务端不解析的参数
10. 禁止出现 `restful.json` 之外的调用入口；网关只按本文件组装请求
11. public 应用对非 owner 放行 `restful.json` 声明的 GET / POST / PUT / DELETE 工具；平台只校验应用访问权限，不限制工具方法。写操作必须由应用基于网关注入的 `X-Staff-Id` / `X-Staff-Name` 做服务端业务鉴权，不能依赖平台自动拦截

## 5. 服务端实现要求

- 网关注入明文身份头 `X-Staff-Id` / `X-Staff-Name`，应用可据此做细粒度鉴权
- 面向 Agent 暴露的接口统一挂载在 `/app-mcp/` 下；该保留前缀不用于页面、静态资源或其他普通业务 API
- 写操作（POST / PUT / DELETE）必须在服务端显式鉴权；public / grant2user 场景不能仅凭应用可见性放行
- 响应统一 JSON；非 2xx 时网关把状态码与截断响应体回传给 Agent
- 大结果建议分页；网关对 args 有 32KB 硬限

## 6. 模板

- 通用模板：`${SKILL_DIR}/assets/templates/restful.json`
- 模板覆盖查询、写入、更新、删除、嵌套 `fields` 与 `callExample` 正确示例；按实际能力裁剪，未实现的工具必须删除
