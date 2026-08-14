---
name: hr-common-llm
domain: common
version: "1.1.0"
auth_level: internal
data_sensitivity: L2
description: |
  提供标准化的前端 LLM 模型代理服务调用能力。当用户需要在前端页面调用大语言模型时，根据 OpenAI 标准接口规范生成正确的前端调用代码。
  
  ⚠️ 严格限制：模型代理接口只能在前端页面（浏览器端）中调用，严禁在任何后端代码（Node.js、Python、Go、Java 等后端服务）中调用，因为后端环境缺少用户的 SSO 身份信息，调用会报错。
  
  触发场景：
  (1) 用户需要在前端页面调用大语言模型接口
  (2) 用户需要生成前端访问 LLM 的 HTTP 请求代码
  (3) 用户需要在前端实现 AI 对话、文本生成、内容分析等功能
  (4) 用户提到「调用模型」「AI接口」「LLM调用」「大模型」「智能对话」「文本生成」等关键词
  (5) 用户需要使用混元模型（HY-3-Preview）
  
  权限要求：已认证员工
---

## 接口规范

### 基本信息

| 项目       | 说明                                                                    |
| ---------- | ----------------------------------------------------------------------- |
| 请求地址   | `POST https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions` |
| 接口规范   | OpenAI Chat Completions API 标准规范                                      |
| 请求格式   | `application/json`                                                       |
| 响应格式   | `application/json` 或 `text/event-stream`（流式响应）                     |
| 跨域支持   | 已启用（CORS）                                                           |
| 身份认证   | **无需额外处理**，前端 HTTP 链路层已自动携带 SSO 身份信息                  |

### 可用模型

| 模型名称          | 类型       | 说明                                         |
| ---------------- | ---------- | -------------------------------------------- |
| `HY-3-Preview`   | 非思考模型  | 适用于推理、长文、对话、代码等场景，用户未指定模型时默认使用 |

### 请求体结构（OpenAI 标准）

```json
{
  "model": "HY-3-Preview",
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
  "model": "HY-3-Preview",
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
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1677858242,"model":"HY-3-Preview","choices":[{"index":0,"delta":{"content":"内"},"finish_reason":null}]}

data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1677858242,"model":"HY-3-Preview","choices":[{"index":0,"delta":{"content":"容"},"finish_reason":null}]}

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

1. **目标语言/框架**：JavaScript (fetch/axios)、TypeScript、React、Vue 等**前端**技术栈
2. **运行环境**：必须是**浏览器端**（前端页面）。⚠️ 如果用户要求在后端环境中调用，**必须拒绝**并说明原因
3. **模型选择**：当前可用模型为 `HY-3-Preview`（非思考模型），适用于一般对话、文本生成、内容分析等场景
4. **响应方式**：是否需要流式响应（推荐用于长文本生成场景，提升用户体验）
5. **功能需求**：对话、文本生成、内容分析、代码生成等

### Step 2: 生成代码

根据上下文生成代码时，遵循以下规则：

1. **API 地址**：使用 `https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions`
2. **请求方法**：必须使用 POST
3. **Content-Type**：必须设置为 `application/json`
4. **⚠️ 无需 Authorization**：前端 HTTP 链路层已处理身份认证，代码中**不要**添加 Authorization header
5. **跨域凭证**：fetch 使用 `credentials: 'include'`，axios 使用 `withCredentials: true`
6. **错误处理**：代码中必须包含完善的错误处理逻辑
7. **流式处理**：如需流式响应，需正确处理 SSE 数据流
8. **类型定义**：TypeScript 项目中提供完整的类型定义

### Step 3: 代码模板参考

生成代码时参考 `references/code_templates.md` 中的完整模板。

**关键模板列表：**
- JavaScript fetch（非流式）
- JavaScript fetch（流式/SSE）
- JavaScript axios
- TypeScript fetch（含类型定义）
- React Hook 封装（非流式）
- React Hook 封装（流式）
- Vue 3 Composable 封装

### Step 4: 输出代码

将生成的代码直接写入用户项目中的目标文件，或以代码块形式展示给用户。

## 注意事项

1. **⚠️ 仅限前端页面调用**：模型代理接口依赖前端 HTTP 链路层的 SSO 身份信息，后端环境无法正确认证
2. **无需 Authorization**：身份认证由前端链路层自动处理，代码中不要手动添加
3. **模型选择建议**：当前统一使用 `HY-3-Preview`（非思考模型），适用于常规对话、文本生成、内容分析等场景
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
  model: 'HY-3-Preview',
  messages: [
    { role: 'user', content: '分析这段代码的时间复杂度和空间复杂度，并提出优化建议...' }
  ],
  temperature: 0.3  // 复杂分析建议使用较低温度
};
```