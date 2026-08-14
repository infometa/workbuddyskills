# LLM 代理服务调用 - 代码模板

本文件包含各语言/框架调用 LLM 代理服务的标准代码模板。

## 接口常量

```
API_URL = https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions
METHOD = POST
Content-Type = application/json
```

## 可用模型

| 模型名称        | 类型       | 适用场景                     |
| -------------- | ---------- | ---------------------------- |
| `HY-3-Preview` | 非思考模型  | 一般对话、文本生成、内容分析   |

---

## 1. JavaScript - fetch（非流式）

### 基础调用

```javascript
const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

async function chatCompletion(messages, options = {}) {
  const {
    model = 'HY-3-Preview',
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
    model = 'HY-3-Preview',
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
    model = 'HY-3-Preview',
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
    const { model = 'HY-3-Preview', temperature = 0.7, maxTokens = 2048 } = options;

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
    model = 'HY-3-Preview',
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
    model = 'HY-3-Preview',
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
  model?: 'HY-3-Preview';
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
    model = 'HY-3-Preview',
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
  model: 'HY-3-Preview',
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
  model?: 'HY-3-Preview';
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
  const { model = 'HY-3-Preview', temperature = 0.7, maxTokens = 2048 } = options;

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
    model: 'HY-3-Preview',
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
  model: 'HY-3-Preview';
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
  const { model = 'HY-3-Preview', temperature = 0.7, maxTokens = 2048 } = options;

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
  model: 'HY-3-Preview';
  temperature?: number;
  maxTokens?: number;
}

const API_URL = 'https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions';

export function useChat(options: ChatOptions = {}) {
  const { model = 'HY-3-Preview', temperature = 0.7, maxTokens = 2048 } = options;

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
  const { model = 'HY-3-Preview', temperature = 0.7, maxTokens = 2048 } = options;

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
      model: 'HY-3-Preview',
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
