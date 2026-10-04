---
name: hr-common-llm
domain: common
version: "1.2.0"
auth_level: internal
data_sensitivity: L2
description: |
  提供标准化的前端 / 后端 LLM 模型代理服务调用能力。当用户需要调用大语言模型时，根据 OpenAI 标准接口规范生成正确的前端或后端调用代码。
  
  ⚠️ 严格限制：前端接口（SSO 网关地址）只能在前端页面（浏览器端）中调用，严禁在后端代码中调用，因为后端环境缺少用户的 SSO 身份信息，调用会报错；后端接口（ESB 网关地址）只能在后端服务（Java/Node.js/Python/Go 等）中调用，严禁在前端代码中直接调用。两个地址不可混用。
  
  触发场景：
  (1) 用户需要在前端页面调用大语言模型接口
  (2) 用户需要在后端服务中调用大语言模型接口
  (3) 用户需要生成前端或后端访问 LLM 的 HTTP 请求代码
  (4) 用户需要在前端或后端实现 AI 对话、文本生成、内容分析等功能
  (5) 用户提到「调用模型」「AI接口」「LLM调用」「大模型」「智能对话」「文本生成」等关键词
  (6) 用户需要使用混元模型（HY-3）
  
  权限要求：已认证员工（前端接口）/ 无需额外权限（后端接口，服务端直连 ESB 网关）
---

## 接口规范

### 基本信息

| 项目           | 前端接口（浏览器端）                                                        | 后端接口（服务端）                                                        |
| -------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 请求地址       | `POST https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions` | `POST http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions` |
| 适用环境       | 浏览器端（Web 页面）                                                         | 服务端（Java、Node.js、Python、Go 等后端服务）                              |
| 接口规范       | OpenAI Chat Completions API 标准规范                                          | 与前端接口保持一致                                                          |
| 请求格式       | `application/json`                                                           | `application/json`                                                        |
| 响应格式       | `application/json` 或 `text/event-stream`（流式响应）                         | `application/json` 或 `text/event-stream`（流式响应）                       |
| 跨域支持       | 已启用（CORS）                                                               | 不涉及（服务端直连）                                                       |
| 身份认证       | **无需额外处理**，前端 HTTP 链路层已自动携带 SSO 身份信息                      | **无需额外处理**，服务端直连 ESB 网关，无需权限校验                          |

> ⚠️ 两个地址**不可混用**：前端页面调用后端 ESB 地址会因跨域/网络策略失败；后端服务调用前端 SSO 地址会因缺少 SSO 身份信息而认证失败。请根据实际运行环境选择正确的地址。
>
> 除请求地址与适用环境不同外，前端接口与后端接口的**请求参数、请求体结构、响应结构、错误响应、可用模型均完全一致**，详见下文。

### 可用模型

| 模型名称          | 类型       | 说明                                         |
| ---------------- | ---------- | -------------------------------------------- |
| `HY-3`   | 非思考模型  | 适用于推理、长文、对话、代码等场景，用户未指定模型时默认使用 |

### 请求体结构（OpenAI 标准）

```json
{
  "model": "HY-3",
  "messages": [
    { "role": "system", "content": "你是一个有帮助的助手" },
    { "role": "user", "content": "用户的问题或指令" }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

#### 核心参数说明

| 参数         | 类型      | 必填 | 说明                                                                |
| ------------ | --------- | ---- | ------------------------------------------------------------------- |
| `model`      | string    | ✅   | 模型名称，可选值见上方「可用模型」                                     |
| `messages`   | array     | ✅   | 对话消息数组，包含 `role` 和 `content` 字段                           |
| `temperature`| number    | ❌   | 生成随机性，范围 0-2，默认 0.7。值越高回复越随机                        |
| `max_tokens` | number    | ❌   | 最大生成 token 数，建议设置合理上限避免过长响应                         |
| `stream`     | boolean   | ❌   | 是否启用流式响应，默认 false。启用后逐字返回，提升交互体验               |
| `top_p`      | number    | ❌   | 核采样参数，范围 0-1，与 temperature 二选一使用                        |

#### messages 消息角色

| 角色        | 说明                                       |
| ----------- | ------------------------------------------ |
| `system`    | 系统提示词，设定 AI 的行为和角色（可选）     |
| `user`      | 用户输入的问题或指令                         |
| `assistant` | AI 的回复（用于多轮对话时提供上下文）         |

### 响应结构

#### 非流式响应

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1677858242,
  "model": "HY-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "AI的回复内容"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### 流式响应（SSE）

流式响应返回 `text/event-stream` 格式，每个数据块格式如下：

```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1677858242,"model":"HY-3","choices":[{"index":0,"delta":{"content":"内"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1677858242,"model":"HY-3","choices":[{"index":0,"delta":{"content":"容"},"finish_reason":null}]}

data: [DONE]
```

### 错误响应

```json
{
  "error": {
    "message": "错误描述",
    "type": "error_type",
    "code": "error_code"
  }
}
```

| HTTP 状态码 | 说明                                     |
| ----------- | ---------------------------------------- |
| 200         | 成功                                     |
| 400         | 请求参数错误（消息格式不正确、缺少必填字段等）|
| 401         | 认证失败（SSO 信息无效）                   |
| 429         | 请求过于频繁，触发限流                     |
| 500         | 服务端内部错误                            |

## 代码生成工作流

### Step 1: 确定调用上下文

分析用户需求，确定以下信息：

1. **运行环境**：先确定用户是要在**前端（浏览器端）**还是**后端（服务端）**调用，这决定了使用哪个请求地址
   - 前端：JavaScript (fetch/axios)、TypeScript、React、Vue 等浏览器端技术栈 → 使用 SSO 网关地址
   - 后端：Java、Node.js、Python、Go 等服务端技术栈 → 使用 ESB 网关地址
   - ⚠️ 若上下文明显是浏览器端代码却要求调用 ESB 地址，或明显是后端服务代码却要求调用 SSO 地址，**必须提示用户环境与地址不匹配**并纠正为正确地址
2. **模型选择**：当前可用模型为 `HY-3`（非思考模型），适用于一般对话、文本生成、内容分析等场景
3. **响应方式**：是否需要流式响应（推荐用于长文本生成场景，提升用户体验）
4. **功能需求**：对话、文本生成、内容分析、代码生成等

### Step 2: 生成代码

根据上下文生成代码时，遵循以下规则：

1. **API 地址**：
   - 前端（浏览器端）：`https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions`
   - 后端（服务端）：`http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions`
   - 建议将 API 地址抽取为可配置的常量/环境变量，而非硬编码在业务逻辑中
2. **请求方法**：必须使用 POST
3. **Content-Type**：必须设置为 `application/json`
4. **身份认证**：
   - 前端：**无需 Authorization**，前端 HTTP 链路层已处理身份认证，代码中**不要**添加 Authorization header；fetch 使用 `credentials: 'include'`，axios 使用 `withCredentials: true`
   - 后端：**无需 Authorization**，服务端直连 ESB 网关调用，无需额外鉴权，也无需设置跨域凭证
5. **错误处理**：代码中必须包含完善的错误处理逻辑，判断 HTTP 状态码及业务 `error` 字段
6. **流式处理**：如需流式响应，需正确处理 SSE 数据流（前后端处理方式一致，均为解析 `data: {...}` 行，以 `data: [DONE]` 结束）
7. **类型定义**：TypeScript 项目中提供完整的类型定义

### Step 3: 代码模板参考

生成代码时参考 `references/code_templates.md` 中的完整模板。

**前端模板：**
- JavaScript fetch（非流式）
- JavaScript fetch（流式/SSE）
- JavaScript axios
- TypeScript fetch（含类型定义）
- React Hook 封装（非流式）
- React Hook 封装（流式）
- Vue 3 Composable 封装

**后端模板：**
- Node.js（axios / fetch，非流式与流式）
- Python（requests，非流式与流式）
- Java（HttpClient，非流式）
- Go（net/http，非流式）

### Step 4: 输出代码

将生成的代码直接写入用户项目中的目标文件，或以代码块形式展示给用户。

## 注意事项

1. **⚠️ 地址与环境严格对应**：前端 SSO 地址仅限浏览器端调用（依赖前端链路层的 SSO 身份信息，后端调用会认证失败）；后端 ESB 地址仅限服务端调用（前端浏览器直接调用会因跨域/网络策略失败），两者不可混用
2. **无需 Authorization**：无论前端还是后端，身份认证均由链路层自动处理，代码中都不要手动添加 Authorization header
3. **模型选择建议**：当前统一使用 `HY-3`（非思考模型），适用于常规对话、文本生成、内容分析等场景
4. **流式响应建议**：长文本生成场景推荐使用流式响应，逐字返回提升用户体验
5. **Token 限制**：建议设置合理的 `max_tokens` 避免过长响应导致超时
6. **多轮对话**：保持对话上下文时，需在 `messages` 数组中包含历史消息
7. **生成代码时**，优先参考 `references/code_templates.md` 中的模板，确保代码风格统一

## 常见使用场景

### 场景一：简单问答

```javascript
const messages = [
  { role: 'user', content: '请解释一下什么是微服务架构？' }
];
```

### 场景二：带系统提示的对话

```javascript
const messages = [
  { role: 'system', content: '你是一个专业的HR助手，专门解答员工关于公司政策的问题。' },
  { role: 'user', content: '请问年假是怎么计算的？' }
];
```

### 场景三：多轮对话

```javascript
const messages = [
  { role: 'system', content: '你是一个编程助手' },
  { role: 'user', content: '如何用JavaScript实现防抖函数？' },
  { role: 'assistant', content: '防抖函数的实现如下...' },
  { role: 'user', content: '能给一个使用示例吗？' }
];
```

### 场景四：复杂分析任务

```javascript
const payload = {
  model: 'HY-3',
  messages: [
    { role: 'user', content: '分析这段代码的时间复杂度和空间复杂度，并提出优化建议...' }
  ],
  temperature: 0.3  // 复杂分析建议使用较低温度
};
```