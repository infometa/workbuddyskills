---
name: indicator-api-codegen
description: 提供标准化的指标 HTTP 查询接口调用能力。当用户需要在前端页面查询预置指标数据（如比率、占比、平均值、人均、趋势对比、流入流出率等）时，根据接口规范生成正确的前端调用代码。⚠️严格限制：指标接口只能在前端页面（浏览器端）中调用，严禁在任何后端代码（Node.js、Python、Go、Java等后端服务）中调用，因为后端环境没有用户的SSO身份信息，调用会报错。使用场景：1.用户需要在前端页面调用指标接口查询指标数据。2.用户需要生成前端访问指标 API 的 HTTP 请求代码。3.用户需要在前端编写指标数据获取逻辑。4.用户提到"查指标"、"指标接口"、"指标数据"、"占比"、"比率"、"流入流出率"等关键词
---

## 接口规范

> 遵循 `hr-datawarehouse-api-constraint` 规则。指标接口与数仓 SQL 接口同域，共用 SSO 身份认证链路。

| 项目 | 说明 |
|---|---|
| 请求地址 | `POST https://dos-dataview-mcp.woa.com/api/indicator` |
| 请求格式 | `application/json` |
| 响应格式 | `application/json` |
| 跨域支持 | 已启用（CORS） |

### 请求体

```json
{
  "apiCode": "inflow-count-proportion",
  "queryParams": {
    "commonParam": {},
    "numeratorParams": {
      "flowInBeginDate": "2025-01-21",
      "flowInEndDate": "2025-03-22",
      "org": ["OA000001"]
    },
    "denominatorParams": {
      "flowInBeginDate": "2025-01-21",
      "flowInEndDate": "2025-03-22",
      "org": ["OA000001"]
    },
    "groupByList": ["org", "careerLevelName"]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiCode` | String | 是 | 指标 API 编码，如 `inflow-count-proportion` |
| `queryParams` | Object | 否 | 查询参数对象 |

**queryParams 结构：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `commonParam` | Object | 通用查询参数 |
| `numeratorParams` | Object | 分子查询参数 |
| `denominatorParams` | Object | 分母查询参数 |
| `groupByList` | String[] | 分组维度代码数组，如 `["org", "careerLevelName"]` |

> `queryParams` 结构与 MCP 工具 `indicator_query` 的 `queryParams` 参数一致，可直接复用 `indicator-query` SKILL 的产出。

### 响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": [{ "org": "OA000001", "careerLevelName": "T8", "count": 12, "proportion": 0.35 }]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | `0` 成功，非 `0` 失败 |
| `message` | string | 状态描述 |
| `data` | array/null | 指标查询结果 |

### 错误码

| code | 说明 |
|---|---|
| `0` | 成功 |
| `400` | `apiCode` 为空 |
| `401` | 未认证：未找到 `staffId` |
| `403` | 无指标访问权限（`indicatorPowerResult` 为 `false`） |
| `500` | 指标服务异常 |

## 硬规则

**✅ DO**
- 仅在**前端浏览器**代码中调用此接口
- 必须携带跨域凭证：`fetch` 用 `credentials: 'include'`；`axios` 用 `withCredentials: true`
- 请求体必须包含 `apiCode` 字段
- 占比/率类指标：`numeratorParams` 与 `denominatorParams` 中"范围"类参数的**键名必须逐字一致**
- 遵循 `hr-data-desensitization` 规则：脱敏是服务端运行时行为，前端按业务字段名正常处理，不要硬编码绕开
- 如需确定 `apiCode` 与参数定义，先使用 `indicator-query` SKILL 完成指标匹配

**❌ DON'T**
- 禁止在 Node.js / Python / Go / Java 等后端代码中调用（无 SSO 身份，会报 401）
- 禁止手动设置 `x-tai-identity` 请求头（由网关根据 SSO Cookie 自动注入）
- 禁止在请求体中放 `staffId`（由 `AuthenticationFilter` 从身份头注入，前端无需传）

## 代码模板

各前端技术栈的标准调用模板见 `references/code_templates.md`，覆盖：fetch / axios / TypeScript / React Hook / Vue 3 Composable。生成代码时优先参考模板，确保凭证携带与错误处理不遗漏。
