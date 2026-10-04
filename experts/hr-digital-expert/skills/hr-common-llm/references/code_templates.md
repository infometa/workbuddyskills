# LLM 代理服务调用 - 代码模板

本文件包含各语言/框架调用 LLM 代理服务的标准代码模板。

## 接口常量

```
# 前端（浏览器端）
API_URL = https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions

# 后端（服务端）
API_URL = http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions

METHOD = POST
Content-Type = application/json
```

> 前端与后端接口的请求参数、请求体结构、响应结构完全一致，仅请求地址与适用环境不同。前端接口依赖浏览器 SSO 链路，后端接口无需鉴权直连即可调用，两者均**无需**手动添加 Authorization。

## 可用模型

| 模型名称        | 类型       | 适用场景                     |
| -------------- | ---------- | ---------------------------- |
| `HY-3` | 非思考模型  | 一般对话、文本生成、内容分析   |

---

## 目录

**前端模板：**
1. JavaScript - fetch（非流式）
2. JavaScript - fetch（流式/SSE）
3. JavaScript - axios
4. TypeScript - fetch（含类型定义）
5. React Hook 封装（非流式）
6. React Hook 封装（流式）
7. Vue 3 Composable 封装
8. 简单对话工具函数

**后端模板：**
9. Node.js - axios / fetch（非流式与流式）
10. Python - requests（非流式与流式）
11. Java - HttpClient（非流式）
12. Go - net/http（非流式）

---

## 1. JavaScript - fetch（非流式）

### 基础调用

```javascript
const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

async function chatCompletion(messages, options = {}) {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
  } = options;

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens: maxTokens,
      stream: false,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`请求失败: ${error.error?.message || response.statusText}`);
  }

  const result = await response.json();
  return result.choices[0].message.content;
}

// 使用示例
try {
  const answer = await chatCompletion([
    { role: 'system', content: '你是一个有帮助的助手' },
    { role: 'user', content: '请介绍一下JavaScript的闭包概念' },
  ]);
  console.log('AI回复:', answer);
} catch (error) {
  console.error('调用出错:', error.message);
}
```

### 带超时和重试的增强版

```javascript
const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

async function chatCompletion(messages, options = {}) {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
    timeout = 60000,
    retries = 2,
  } = options;

  let lastError;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model,
          messages,
          temperature,
          max_tokens: maxTokens,
          stream: false,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(`[HTTP ${response.status}] ${error.error?.message || '请求失败'}`);
      }

      const result = await response.json();
      return result.choices[0].message.content;
    } catch (error) {
      clearTimeout(timeoutId);
      lastError = error;

      if (error.name === 'AbortError') {
        lastError = new Error('请求超时');
      }

      // 最后一次重试失败则抛出错误
      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }

  throw lastError;
}
```

---

## 2. JavaScript - fetch（流式/SSE）

### 基础流式调用

```javascript
const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

async function chatCompletionStream(messages, onChunk, options = {}) {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
  } = options;

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens: maxTokens,
      stream: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`请求失败: ${error.error?.message || response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let fullContent = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

        const data = trimmedLine.slice(6);
        if (data === '[DONE]') {
          return fullContent;
        }

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content) {
            fullContent += content;
            onChunk(content, fullContent);
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return fullContent;
}

// 使用示例
const messages = [
  { role: 'user', content: '请写一首关于春天的诗' },
];

const result = await chatCompletionStream(
  messages,
  (chunk, fullText) => {
    // 每收到一个字符片段时调用
    process.stdout.write(chunk); // 或更新页面UI
  }
);

console.log('\n完整回复:', result);
```

### 支持取消的流式调用

```javascript
const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

function createStreamChat() {
  let abortController = null;

  async function start(messages, onChunk, options = {}) {
    // 取消之前的请求
    if (abortController) {
      abortController.abort();
    }

    abortController = new AbortController();
    const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model,
          messages,
          temperature,
          max_tokens: maxTokens,
          stream: true,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || '请求失败');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

          const data = trimmedLine.slice(6);
          if (data === '[DONE]') {
            return fullContent;
          }

          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.delta?.content;
            if (content) {
              fullContent += content;
              onChunk(content, fullContent);
            }
          } catch (e) {}
        }
      }

      return fullContent;
    } catch (error) {
      if (error.name === 'AbortError') {
        return null; // 被取消
      }
      throw error;
    }
  }

  function cancel() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
  }

  return { start, cancel };
}

// 使用示例
const chat = createStreamChat();

// 开始流式对话
chat.start(
  [{ role: 'user', content: '请详细解释量子计算的原理' }],
  (chunk) => console.log(chunk)
);

// 需要时可以取消
// chat.cancel();
```

---

## 3. JavaScript - axios

### 基础调用

```javascript
import axios from 'axios';

const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

async function chatCompletion(messages, options = {}) {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
  } = options;

  const { data } = await axios.post(API_URL, {
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
    stream: false,
  }, {
    withCredentials: true,
  });

  return data.choices[0].message.content;
}

// 使用示例
try {
  const answer = await chatCompletion([
    { role: 'user', content: '什么是设计模式？' },
  ]);
  console.log('AI回复:', answer);
} catch (error) {
  console.error('调用出错:', error.response?.data?.error?.message || error.message);
}
```

### 封装为 axios 实例

```javascript
import axios from 'axios';

const llmClient = axios.create({
  baseURL: 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// 响应拦截器：统一处理错误
llmClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('请求超时，请稍后重试'));
    }
    const message = error.response?.data?.error?.message || error.message;
    return Promise.reject(new Error(message));
  }
);

export async function chat(messages, options = {}) {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
  } = options;

  const result = await llmClient.post('/chat/completions', {
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
    stream: false,
  });

  return result.choices[0].message.content;
}

export { llmClient };
```

---

## 4. TypeScript - fetch（含类型定义）

```typescript
// types.ts - 类型定义
interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  top_p?: number;
}

interface ChatCompletionChoice {
  index: number;
  message: ChatMessage;
  finish_reason: 'stop' | 'length' | 'content_filter' | null;
}

interface ChatCompletionUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

interface ChatCompletionResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: ChatCompletionChoice[];
  usage: ChatCompletionUsage;
}

interface ChatCompletionError {
  error: {
    message: string;
    type: string;
    code: string;
  };
}

interface ChatOptions {
  model?: 'HY-3';
  temperature?: number;
  maxTokens?: number;
  timeout?: number;
}

// api.ts - API 调用
const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

export async function chatCompletion(
  messages: ChatMessage[],
  options: ChatOptions = {}
): Promise<string> {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
    timeout = 60000,
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: maxTokens,
        stream: false,
      } as ChatCompletionRequest),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData: ChatCompletionError = await response.json();
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    const result: ChatCompletionResponse = await response.json();
    return result.choices[0].message.content;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('请求超时');
    }
    throw error;
  }
}

// 使用示例
const messages: ChatMessage[] = [
  { role: 'system', content: '你是一个专业的技术顾问' },
  { role: 'user', content: '请解释什么是微服务架构' },
];

const answer = await chatCompletion(messages, {
  model: 'HY-3',
  temperature: 0.7,
});
console.log(answer);
```

---

## 5. React Hook 封装（非流式）

```typescript
import { useState, useCallback, useRef } from 'react';

// 类型定义
interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatOptions {
  model?: 'HY-3';
  temperature?: number;
  maxTokens?: number;
}

interface UseChatResult {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  sendMessage: (content: string, systemPrompt?: string) => Promise<string | null>;
  clearHistory: () => void;
  setSystemPrompt: (prompt: string) => void;
}

const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

export function useChat(options: ChatOptions = {}): UseChatResult {
  const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const systemPromptRef = useRef<string>('');

  const setSystemPrompt = useCallback((prompt: string) => {
    systemPromptRef.current = prompt;
  }, []);

  const sendMessage = useCallback(async (content: string): Promise<string | null> => {
    setLoading(true);
    setError(null);

    const userMessage: ChatMessage = { role: 'user', content };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);

    // 构建请求消息
    const requestMessages: ChatMessage[] = systemPromptRef.current
      ? [{ role: 'system', content: systemPromptRef.current }, ...newMessages]
      : newMessages;

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model,
          messages: requestMessages,
          temperature,
          max_tokens: maxTokens,
          stream: false,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || '请求失败');
      }

      const result = await response.json();
      const assistantContent = result.choices[0].message.content;
      const assistantMessage: ChatMessage = { role: 'assistant', content: assistantContent };

      setMessages([...newMessages, assistantMessage]);
      return assistantContent;
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : '未知错误';
      setError(errMsg);
      return null;
    } finally {
      setLoading(false);
    }
  }, [messages, model, temperature, maxTokens]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearHistory, setSystemPrompt };
}

// 使用示例
/*
function ChatComponent() {
  const { messages, loading, error, sendMessage, clearHistory, setSystemPrompt } = useChat({
    model: 'HY-3',
  });
  const [input, setInput] = useState('');

  useEffect(() => {
    setSystemPrompt('你是一个友好的助手');
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    
    const userInput = input;
    setInput('');
    await sendMessage(userInput);
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
        {loading && <div className="loading">AI正在思考...</div>}
        {error && <div className="error">错误: {error}</div>}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入消息..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>发送</button>
        <button type="button" onClick={clearHistory}>清空</button>
      </form>
    </div>
  );
}
*/
```

---

## 6. React Hook 封装（流式）

```typescript
import { useState, useCallback, useRef } from 'react';

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatOptions {
  model: 'HY-3';
  temperature?: number;
  maxTokens?: number;
}

interface UseStreamChatResult {
  messages: ChatMessage[];
  streamingContent: string;
  isStreaming: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  cancelStream: () => void;
  clearHistory: () => void;
  setSystemPrompt: (prompt: string) => void;
}

const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

export function useStreamChat(options: ChatOptions = {}): UseStreamChatResult {
  const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const systemPromptRef = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);

  const setSystemPrompt = useCallback((prompt: string) => {
    systemPromptRef.current = prompt;
  }, []);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    cancelStream();
    
    setIsStreaming(true);
    setError(null);
    setStreamingContent('');

    const userMessage: ChatMessage = { role: 'user', content };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);

    const requestMessages: ChatMessage[] = systemPromptRef.current
      ? [{ role: 'system', content: systemPromptRef.current }, ...newMessages]
      : newMessages;

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model,
          messages: requestMessages,
          temperature,
          max_tokens: maxTokens,
          stream: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || '请求失败');
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

          const data = trimmedLine.slice(6);
          if (data === '[DONE]') break;

          try {
            const parsed = JSON.parse(data);
            const chunk = parsed.choices?.[0]?.delta?.content;
            if (chunk) {
              fullContent += chunk;
              setStreamingContent(fullContent);
            }
          } catch (e) {}
        }
      }

      // 流式结束，将完整回复添加到消息列表
      const assistantMessage: ChatMessage = { role: 'assistant', content: fullContent };
      setMessages([...newMessages, assistantMessage]);
      setStreamingContent('');
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      const errMsg = err instanceof Error ? err.message : '未知错误';
      setError(errMsg);
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [messages, model, temperature, maxTokens, cancelStream]);

  const clearHistory = useCallback(() => {
    cancelStream();
    setMessages([]);
    setStreamingContent('');
    setError(null);
  }, [cancelStream]);

  return {
    messages,
    streamingContent,
    isStreaming,
    error,
    sendMessage,
    cancelStream,
    clearHistory,
    setSystemPrompt,
  };
}

// 使用示例
/*
function StreamChatComponent() {
  const {
    messages,
    streamingContent,
    isStreaming,
    error,
    sendMessage,
    cancelStream,
    clearHistory,
    setSystemPrompt,
  } = useStreamChat();

  const [input, setInput] = useState('');

  useEffect(() => {
    setSystemPrompt('你是一个专业的助手');
  }, []);

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>{msg.content}</div>
        ))}
        {streamingContent && (
          <div className="assistant streaming">{streamingContent}</div>
        )}
        {error && <div className="error">{error}</div>}
      </div>
      <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); setInput(''); }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} />
        <button type="submit" disabled={isStreaming}>发送</button>
        {isStreaming && <button type="button" onClick={cancelStream}>取消</button>}
        <button type="button" onClick={clearHistory}>清空</button>
      </form>
    </div>
  );
}
*/
```

---

## 7. Vue 3 Composable 封装

```typescript
import { ref, readonly } from 'vue';

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatOptions {
  model: 'HY-3';
  temperature?: number;
  maxTokens?: number;
}

const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

export function useChat(options: ChatOptions = {}) {
  const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

  const messages = ref<ChatMessage[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const systemPrompt = ref('');

  async function sendMessage(content: string): Promise<string | null> {
    loading.value = true;
    error.value = null;

    const userMessage: ChatMessage = { role: 'user', content };
    messages.value = [...messages.value, userMessage];

    const requestMessages: ChatMessage[] = systemPrompt.value
      ? [{ role: 'system', content: systemPrompt.value }, ...messages.value]
      : messages.value;

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model,
          messages: requestMessages,
          temperature,
          max_tokens: maxTokens,
          stream: false,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || '请求失败');
      }

      const result = await response.json();
      const assistantContent = result.choices[0].message.content;
      const assistantMessage: ChatMessage = { role: 'assistant', content: assistantContent };

      messages.value = [...messages.value, assistantMessage];
      return assistantContent;
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : '未知错误';
      error.value = errMsg;
      return null;
    } finally {
      loading.value = false;
    }
  }

  function clearHistory() {
    messages.value = [];
    error.value = null;
  }

  function setSystemPrompt(prompt: string) {
    systemPrompt.value = prompt;
  }

  return {
    messages: readonly(messages),
    loading: readonly(loading),
    error: readonly(error),
    sendMessage,
    clearHistory,
    setSystemPrompt,
  };
}

// 流式版本
export function useStreamChat(options: ChatOptions = {}) {
  const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

  const messages = ref<ChatMessage[]>([]);
  const streamingContent = ref('');
  const isStreaming = ref(false);
  const error = ref<string | null>(null);
  const systemPrompt = ref('');
  
  let abortController: AbortController | null = null;

  function cancelStream() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    isStreaming.value = false;
  }

  async function sendMessage(content: string): Promise<void> {
    cancelStream();
    
    isStreaming.value = true;
    error.value = null;
    streamingContent.value = '';

    const userMessage: ChatMessage = { role: 'user', content };
    messages.value = [...messages.value, userMessage];

    const requestMessages: ChatMessage[] = systemPrompt.value
      ? [{ role: 'system', content: systemPrompt.value }, ...messages.value]
      : messages.value;

    abortController = new AbortController();

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model,
          messages: requestMessages,
          temperature,
          max_tokens: maxTokens,
          stream: true,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || '请求失败');
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

          const data = trimmedLine.slice(6);
          if (data === '[DONE]') break;

          try {
            const parsed = JSON.parse(data);
            const chunk = parsed.choices?.[0]?.delta?.content;
            if (chunk) {
              fullContent += chunk;
              streamingContent.value = fullContent;
            }
          } catch (e) {}
        }
      }

      const assistantMessage: ChatMessage = { role: 'assistant', content: fullContent };
      messages.value = [...messages.value, assistantMessage];
      streamingContent.value = '';
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      error.value = err instanceof Error ? err.message : '未知错误';
    } finally {
      isStreaming.value = false;
      abortController = null;
    }
  }

  function clearHistory() {
    cancelStream();
    messages.value = [];
    streamingContent.value = '';
    error.value = null;
  }

  function setSystemPrompt(prompt: string) {
    systemPrompt.value = prompt;
  }

  return {
    messages: readonly(messages),
    streamingContent: readonly(streamingContent),
    isStreaming: readonly(isStreaming),
    error: readonly(error),
    sendMessage,
    cancelStream,
    clearHistory,
    setSystemPrompt,
  };
}

// 使用示例 (Vue 3 <script setup>)
/*
<script setup lang="ts">
import { useStreamChat } from './useChat';
import { ref, onMounted } from 'vue';

const { messages, streamingContent, isStreaming, error, sendMessage, cancelStream, clearHistory, setSystemPrompt } = useStreamChat();
const input = ref('');

onMounted(() => {
  setSystemPrompt('你是一个专业的助手');
});

function handleSubmit() {
  if (!input.value.trim() || isStreaming.value) return;
  sendMessage(input.value);
  input.value = '';
}
</script>

<template>
  <div>
    <div v-for="(msg, i) in messages" :key="i" :class="msg.role">
      {{ msg.content }}
    </div>
    <div v-if="streamingContent" class="assistant streaming">
      {{ streamingContent }}
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <form @submit.prevent="handleSubmit">
      <input v-model="input" :disabled="isStreaming" />
      <button type="submit" :disabled="isStreaming">发送</button>
      <button v-if="isStreaming" type="button" @click="cancelStream">取消</button>
      <button type="button" @click="clearHistory">清空</button>
    </form>
  </div>
</template>
*/
```

---

## 8. 简单对话工具函数（适用于快速集成）

```javascript
// llm-utils.js - 轻量级工具函数
const LLM_API = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

/**
 * 简单的单轮对话
 * @param {string} prompt - 用户提问
 * @param {string} [systemPrompt] - 系统提示词（可选）
 * @returns {Promise<string>} AI 回复
 */
export async function ask(prompt, systemPrompt) {
  const messages = [];
  if (systemPrompt) {
    messages.push({ role: 'system', content: systemPrompt });
  }
  messages.push({ role: 'user', content: prompt });

  const res = await fetch(LLM_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      model: 'HY-3',
      messages,
      temperature: 0.7,
      max_tokens: 2048,
    }),
  });

  if (!res.ok) throw new Error('请求失败');
  const data = await res.json();
  return data.choices[0].message.content;
}

// 使用示例
// const answer = await ask('什么是闭包？');
// const analysis = await ask('分析这段代码的复杂度...', '你是一名资深架构师，请进行详尽的复杂度分析');
```

---

## 9. Node.js - axios / fetch（后端服务端调用）

> 后端接口地址为 `http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions`，服务端直连 ESB 网关，无需鉴权，不需要 `withCredentials`/`credentials`。

### axios（非流式）

```javascript
const axios = require('axios');

const API_URL = 'http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions';

async function chatCompletion(messages, options = {}) {
  const {
    model = 'HY-3',
    temperature = 0.7,
    maxTokens = 2048,
  } = options;

  const { data } = await axios.post(API_URL, {
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
    stream: false,
  }, {
    headers: { 'Content-Type': 'application/json' },
    timeout: 60000,
  });

  return data.choices[0].message.content;
}

// 使用示例
(async () => {
  try {
    const answer = await chatCompletion([
      { role: 'system', content: '你是一个有帮助的助手' },
      { role: 'user', content: '请介绍一下Node.js的事件循环' },
    ]);
    console.log('AI回复:', answer);
  } catch (error) {
    console.error('调用出错:', error.response?.data?.error?.message || error.message);
  }
})();

module.exports = { chatCompletion };
```

### fetch（Node.js 18+，非流式）

```javascript
const API_URL = 'http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions';

async function chatCompletion(messages, options = {}) {
  const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens: maxTokens,
      stream: false,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`请求失败: ${error.error?.message || response.statusText}`);
  }

  const result = await response.json();
  return result.choices[0].message.content;
}

module.exports = { chatCompletion };
```

### axios（流式/SSE）

```javascript
const axios = require('axios');

const API_URL = 'http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions';

async function chatCompletionStream(messages, onChunk, options = {}) {
  const { model = 'HY-3', temperature = 0.7, maxTokens = 2048 } = options;

  const response = await axios.post(API_URL, {
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
    stream: true,
  }, {
    headers: { 'Content-Type': 'application/json' },
    responseType: 'stream',
  });

  let buffer = '';
  let fullContent = '';

  return new Promise((resolve, reject) => {
    response.data.on('data', (chunk) => {
      buffer += chunk.toString('utf-8');
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const data = trimmed.slice(6);
        if (data === '[DONE]') {
          resolve(fullContent);
          return;
        }

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content) {
            fullContent += content;
            onChunk(content, fullContent);
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    });

    response.data.on('end', () => resolve(fullContent));
    response.data.on('error', reject);
  });
}

module.exports = { chatCompletionStream };
```

---

## 10. Python - requests（后端服务端调用）

### requests（非流式）

```python
import requests

API_URL = "http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions"


def chat_completion(messages, model="HY-3", temperature=0.7, max_tokens=2048):
    """调用 LLM 代理服务，返回 AI 回复内容"""
    response = requests.post(
        API_URL,
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        },
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]


# 使用示例
if __name__ == "__main__":
    try:
        answer = chat_completion([
            {"role": "system", "content": "你是一个有帮助的助手"},
            {"role": "user", "content": "请介绍一下Python的装饰器"},
        ])
        print("AI回复:", answer)
    except requests.exceptions.RequestException as e:
        print("调用出错:", e)
```

### requests（流式/SSE）

```python
import json
import requests

API_URL = "http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions"


def chat_completion_stream(messages, on_chunk, model="HY-3", temperature=0.7, max_tokens=2048):
    """流式调用 LLM 代理服务，逐块回调 on_chunk(content, full_content)"""
    full_content = ""
    with requests.post(
        API_URL,
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        },
        headers={"Content-Type": "application/json"},
        stream=True,
        timeout=60,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[len("data: "):]
            if data == "[DONE]":
                break
            try:
                parsed = json.loads(data)
                content = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
                if content:
                    full_content += content
                    on_chunk(content, full_content)
            except json.JSONDecodeError:
                continue
    return full_content


# 使用示例
if __name__ == "__main__":
    result = chat_completion_stream(
        [{"role": "user", "content": "请写一首关于秋天的诗"}],
        lambda chunk, full: print(chunk, end="", flush=True),
    )
    print("\n完整回复:", result)
```

---

## 11. Java - HttpClient（后端服务端调用）

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Map;

public class LlmProxyClient {

    private static final String API_URL =
        "http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions";

    private final HttpClient httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .build();

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * 调用 LLM 代理服务（非流式）
     *
     * @param messages 消息列表，每个元素为 {"role": "user", "content": "..."}
     * @param model    模型名称，如 HY-3
     * @return AI 回复内容
     */
    public String chatCompletion(List<Map<String, String>> messages, String model) throws Exception {
        ObjectNode body = objectMapper.createObjectNode();
        body.put("model", model == null ? "HY-3" : model);
        body.putPOJO("messages", messages);
        body.put("temperature", 0.7);
        body.put("max_tokens", 2048);
        body.put("stream", false);

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .timeout(Duration.ofSeconds(60))
            .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
            .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("请求失败: HTTP " + response.statusCode() + " - " + response.body());
        }

        JsonNode result = objectMapper.readTree(response.body());
        return result.get("choices").get(0).get("message").get("content").asText();
    }

    // 使用示例
    public static void main(String[] args) throws Exception {
        LlmProxyClient client = new LlmProxyClient();
        List<Map<String, String>> messages = List.of(
            Map.of("role", "system", "content", "你是一个有帮助的助手"),
            Map.of("role", "user", "content", "请介绍一下Java的垃圾回收机制")
        );
        String answer = client.chatCompletion(messages, "HY-3");
        System.out.println("AI回复: " + answer);
    }
}
```

---

## 12. Go - net/http（后端服务端调用）

```go
package llmclient

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const apiURL = "http://ntsgw.woa.com/api/esb/llm-proxy-service/api/v1/chat/completions"

// Message 对应 OpenAI 消息结构
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type chatRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	Temperature float64   `json:"temperature"`
	MaxTokens   int       `json:"max_tokens"`
	Stream      bool      `json:"stream"`
}

type chatChoice struct {
	Message Message `json:"message"`
}

type chatResponse struct {
	Choices []chatChoice `json:"choices"`
}

type chatErrorResponse struct {
	Error struct {
		Message string `json:"message"`
	} `json:"error"`
}

// ChatCompletion 调用 LLM 代理服务（非流式），返回 AI 回复内容
func ChatCompletion(messages []Message, model string) (string, error) {
	if model == "" {
		model = "HY-3"
	}

	reqBody := chatRequest{
		Model:       model,
		Messages:    messages,
		Temperature: 0.7,
		MaxTokens:   2048,
		Stream:      false,
	}

	payload, err := json.Marshal(reqBody)
	if err != nil {
		return "", err
	}

	client := &http.Client{Timeout: 60 * time.Second}
	req, err := http.NewRequest(http.MethodPost, apiURL, bytes.NewBuffer(payload))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	if resp.StatusCode != http.StatusOK {
		var errResp chatErrorResponse
		_ = json.Unmarshal(body, &errResp)
		return "", fmt.Errorf("请求失败: HTTP %d - %s", resp.StatusCode, errResp.Error.Message)
	}

	var result chatResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return "", err
	}
	if len(result.Choices) == 0 {
		return "", fmt.Errorf("响应中没有可用的回复")
	}

	return result.Choices[0].Message.Content, nil
}

// 使用示例:
// answer, err := llmclient.ChatCompletion([]llmclient.Message{
//     {Role: "system", Content: "你是一个有帮助的助手"},
//     {Role: "user", Content: "请介绍一下Go的goroutine"},
// }, "HY-3")
```
