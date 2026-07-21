# Web Agent 二次开发指南

这是一个基于 CodeBuddy Agent SDK 的完整 Web Agent 应用模板。本指南将帮助你理解项目结构并进行二次开发。

## 目录

- [项目架构](#项目架构)
- [核心功能](#核心功能)
- [二次开发指南](#二次开发指南)
- [API 参考](#api-参考)
- [常见定制需求](#常见定制需求)

---

## 项目架构

### 技术栈

**后端**
- Node.js + Express (RESTful API)
- TypeScript
- @tencent-ai/agent-sdk (Agent SDK)
- better-sqlite3 (SQLite 数据库)

**前端**
- React 18 + TypeScript
- React Router (路由管理)
- TDesign React (UI 组件库)
- Vite (构建工具)

### 目录结构

```
web-agent/
├── server/                     # 后端服务
│   ├── index.ts               # Express 服务器入口
│   ├── db.ts                  # 数据库操作
│   └── index.d.ts             # 类型定义
├── src/                       # 前端源码
│   ├── components/            # React 组件
│   │   ├── ChatMessages.tsx   # 消息列表
│   │   ├── ChatInput.tsx      # 输入框
│   │   ├── ToolCallsCollapse.tsx  # 工具调用展示
│   │   ├── PermissionDialog.tsx   # 权限弹窗
│   │   ├── AgentConfigDialog.tsx  # Agent 配置
│   │   ├── Sidebar.tsx        # 侧边栏
│   │   ├── Header.tsx         # 顶部栏
│   │   └── ...
│   ├── hooks/                 # 自定义 Hooks
│   │   ├── useChat.ts         # 聊天逻辑
│   │   ├── useSessions.ts     # 会话管理
│   │   ├── useModels.ts       # 模型管理
│   │   ├── useAgents.ts       # Agent 管理
│   │   └── useTheme.ts        # 主题管理
│   ├── pages/                 # 页面
│   │   └── ChatPage.tsx       # 聊天页面
│   ├── types.ts               # TypeScript 类型定义
│   ├── config.ts              # 应用配置
│   ├── App.tsx                # 应用入口
│   └── main.tsx               # React 入口
├── data/                      # 数据存储目录
│   └── chat.db               # SQLite 数据库
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 核心功能

### 1. Agent SDK 集成

**核心文件**: `server/index.ts`

SDK 提供三个主要 API：

#### query() - 发送消息并流式接收响应

```typescript
import { query } from "@tencent-ai/agent-sdk";

const stream = query({
  prompt: "用户的问题",
  options: {
    cwd: process.cwd(),           // 工作目录
    model: "claude-sonnet-4",     // 模型选择
    maxTurns: 10,                 // 最大对话轮数
    systemPrompt: "系统提示词",    // 自定义系统提示
    permissionMode: "default",    // 权限模式
    canUseTool: async (toolName, input, options) => {
      // 工具权限控制
      return { behavior: 'allow', updatedInput: input };
    },
    resume: sessionId            // 恢复对话上下文
  }
});

// 处理流式响应
for await (const msg of stream) {
  if (msg.type === "assistant") {
    // 处理 AI 回复
  } else if (msg.type === "tool_result") {
    // 处理工具执行结果
  }
}
```

#### unstable_v2_createSession() - 创建 Agent 会话

```typescript
import { unstable_v2_createSession } from "@tencent-ai/agent-sdk";

const session = await unstable_v2_createSession({ 
  cwd: process.cwd() 
});

// 获取可用模型
const models = await session.getAvailableModels();
```

#### unstable_v2_authenticate() - 身份认证

```typescript
import { unstable_v2_authenticate } from "@tencent-ai/agent-sdk";

const result = await unstable_v2_authenticate({
  environment: 'external',
  onAuthUrl: async (authState) => {
    console.log('需要登录:', authState.authUrl);
  }
});
```

### 2. 数据库设计

**核心文件**: `server/db.ts`

使用 SQLite 存储会话和消息：

**sessions 表**
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  model TEXT NOT NULL,
  sdk_session_id TEXT,         -- Agent SDK 返回的 session_id
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

**messages 表**
```sql
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  model TEXT,
  created_at TEXT NOT NULL,
  tool_calls TEXT,             -- JSON 格式存储工具调用
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

### 3. 流式响应机制

**核心文件**: `server/index.ts` (POST /api/chat)

使用 Server-Sent Events (SSE) 实现流式响应：

```typescript
// 设置 SSE 响应头
res.setHeader("Content-Type", "text/event-stream");
res.setHeader("Cache-Control", "no-cache");
res.setHeader("Connection", "keep-alive");

// 发送不同类型的事件
res.write(`data: ${JSON.stringify({ type: "init", sessionId, ... })}\n\n`);
res.write(`data: ${JSON.stringify({ type: "text", content })}\n\n`);
res.write(`data: ${JSON.stringify({ type: "tool", name, input, ... })}\n\n`);
res.write(`data: ${JSON.stringify({ type: "tool_result", ... })}\n\n`);
res.write(`data: ${JSON.stringify({ type: "permission_request", ... })}\n\n`);
res.write(`data: ${JSON.stringify({ type: "done", ... })}\n\n`);
```

**前端处理**: `src/hooks/useChat.ts`

```typescript
const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      switch (data.type) {
        case 'text':
          // 更新消息内容
          break;
        case 'tool':
          // 显示工具调用
          break;
        case 'permission_request':
          // 弹出权限请求弹窗
          break;
      }
    }
  }
}
```

### 4. 权限控制机制

**核心文件**: `server/index.ts`, `src/hooks/useChat.ts`

支持四种权限模式（在 `src/types.ts` 中定义）：

```typescript
export type PermissionMode = 
  | 'default'              // 每次工具调用都需要确认
  | 'acceptEdits'          // 自动接受编辑类操作
  | 'plan'                 // 计划模式，只读
  | 'bypassPermissions';   // 跳过所有权限检查
```

**后端实现权限回调**:

```typescript
const canUseTool: CanUseTool = async (toolName, input, options) => {
  // bypassPermissions 模式直接放行
  if (permissionMode === 'bypassPermissions') {
    return { behavior: 'allow', updatedInput: input };
  }
  
  // 创建权限请求
  const requestId = uuidv4();
  
  // 发送权限请求到前端
  res.write(`data: ${JSON.stringify({ 
    type: "permission_request", 
    requestId,
    toolName,
    input,
    ...
  })}\n\n`);
  
  // 等待用户响应
  return new Promise((resolve) => {
    pendingPermissions.set(requestId, { resolve, ... });
  });
};
```

**前端显示权限弹窗**:

```typescript
// useChat.ts 接收权限请求
if (data.type === 'permission_request') {
  setPermissionRequest({
    requestId: data.requestId,
    toolName: data.toolName,
    input: data.input,
    ...
  });
}

// PermissionDialog.tsx 用户操作
const handleAllow = async () => {
  await fetch('/api/permission-response', {
    method: 'POST',
    body: JSON.stringify({
      requestId: permissionRequest.requestId,
      behavior: 'allow'
    })
  });
};
```

### 5. 会话恢复机制

**核心文件**: `server/index.ts`, `server/db.ts`

Agent SDK 支持使用 `resume` 参数恢复对话上下文：

```typescript
// 1. 从数据库获取 SDK 返回的 session_id
const session = db.getSession(sessionId);
const sdkSessionId = session.sdk_session_id;

// 2. 使用 resume 参数恢复对话
const stream = query({
  prompt: message,
  options: {
    ...(sdkSessionId ? { resume: sdkSessionId } : {})
  }
});

// 3. 从流中获取新的 session_id
for await (const msg of stream) {
  if (msg.type === "system" && msg.subtype === "init") {
    const newSdkSessionId = msg.session_id;
    
    // 4. 保存到数据库
    db.updateSession(sessionId, { sdk_session_id: newSdkSessionId });
  }
}
```

### 6. 自定义 Agent 管理

**核心文件**: `src/hooks/useAgents.ts`, `src/types.ts`

支持创建多个 Agent 配置：

```typescript
export interface CustomAgent {
  id: string;
  name: string;
  description?: string;
  systemPrompt: string;        // 自定义系统提示词
  icon?: string;               // 图标
  color?: string;              // 颜色
  permissionMode?: PermissionMode;  // 默认权限模式
  createdAt: Date;
  updatedAt: Date;
}

// 使用 localStorage 持久化存储
const STORAGE_KEY = 'custom_agents';
localStorage.setItem(STORAGE_KEY, JSON.stringify(agents));
```

---

## 二次开发指南

### 场景 1: 修改应用名称和样式

**修改应用名称**

编辑 `src/config.ts`:

```typescript
export const APP_CONFIG = {
  name: '我的 AI 助手',           // 修改应用名称
  nameInitial: 'A',              // 修改首字母
  description: '你的智能助理',    // 修改描述
  version: '1.0.0',
};
```

**修改主题颜色**

编辑 `src/index.css`:

```css
:root {
  --primary-color: #0052d9;     /* 主色调 */
  --success-color: #00a870;     /* 成功色 */
  --warning-color: #ed7b2f;     /* 警告色 */
  --error-color: #e34d59;       /* 错误色 */
}
```

### 场景 2: 添加自定义 Agent 预设

编辑 `src/hooks/useAgents.ts` 的默认 Agent：

```typescript
const defaultAgent: CustomAgent = {
  id: 'default',
  name: '通用助手',
  description: '我是你的 AI 助手',
  systemPrompt: '你是一个专业的 AI 助手，擅长编程、写作和问答。',
  icon: 'MessageIcon',
  color: '#0052d9',
  permissionMode: 'default',
  createdAt: new Date(),
  updatedAt: new Date(),
};

// 添加新的预设 Agent
const codeAgent: CustomAgent = {
  id: 'code-assistant',
  name: '代码助手',
  description: '专注于代码开发和调试',
  systemPrompt: '你是一个专业的代码助手，精通多种编程语言，善于代码审查、调试和优化。',
  icon: 'CodeIcon',
  color: '#00a870',
  permissionMode: 'acceptEdits',
  createdAt: new Date(),
  updatedAt: new Date(),
};

const DEFAULT_AGENTS = [defaultAgent, codeAgent];
```

### 场景 3: 添加自定义 API 端点

在 `server/index.ts` 中添加新的路由：

```typescript
// 获取会话统计信息
app.get("/api/stats", (req, res) => {
  try {
    const sessions = db.getAllSessions();
    const totalMessages = sessions.reduce((sum, session) => {
      const messages = db.getMessagesBySession(session.id);
      return sum + messages.length;
    }, 0);
    
    res.json({
      totalSessions: sessions.length,
      totalMessages,
      avgMessagesPerSession: totalMessages / sessions.length || 0
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// 导出会话记录
app.get("/api/sessions/:sessionId/export", (req, res) => {
  try {
    const { sessionId } = req.params;
    const session = db.getSession(sessionId);
    const messages = db.getMessagesBySession(sessionId);
    
    const exportData = {
      session,
      messages: messages.map(msg => ({
        ...msg,
        tool_calls: msg.tool_calls ? JSON.parse(msg.tool_calls) : null
      }))
    };
    
    res.json(exportData);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});
```

### 场景 4: 自定义工具调用展示

编辑 `src/components/ToolCallsCollapse.tsx`，修改工具调用的显示方式：

```typescript
const renderToolInput = (input: Record<string, unknown>) => {
  // 自定义显示逻辑
  if (input.command) {
    return (
      <div className="command-block">
        <code>{input.command}</code>
      </div>
    );
  }
  
  if (input.path) {
    return (
      <div className="file-path">
        📄 {input.path}
      </div>
    );
  }
  
  // 默认 JSON 显示
  return <pre>{JSON.stringify(input, null, 2)}</pre>;
};
```

### 场景 5: 添加消息导出功能

**后端**: 在 `server/index.ts` 中添加导出端点（见场景 3）

**前端**: 在 `src/components/ChatMessages.tsx` 中添加导出按钮：

```typescript
const handleExport = async () => {
  try {
    const response = await fetch(`/api/sessions/${sessionId}/export`);
    const data = await response.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `session-${sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Export failed:', error);
  }
};

// 在组件中添加按钮
<Button onClick={handleExport}>
  导出对话
</Button>
```

### 场景 6: 修改数据库结构

在 `server/db.ts` 中添加新字段或表：

```typescript
// 添加新字段到 sessions 表
db.exec(`
  ALTER TABLE sessions ADD COLUMN tags TEXT;
`);

// 创建新表
db.exec(`
  CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    preferences TEXT NOT NULL,
    created_at TEXT NOT NULL
  );
`);

// 添加操作函数
export function updateSessionTags(id: string, tags: string[]): boolean {
  const stmt = db.prepare('UPDATE sessions SET tags = ? WHERE id = ?');
  const result = stmt.run(JSON.stringify(tags), id);
  return result.changes > 0;
}
```

### 场景 7: 添加文件上传功能

**后端**: 在 `server/index.ts` 中添加上传端点：

```typescript
import multer from 'multer';
import path from 'path';

// 配置文件上传
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ storage });

// 文件上传端点
app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: '没有上传文件' });
  }
  
  res.json({
    filename: req.file.filename,
    originalName: req.file.originalname,
    path: req.file.path,
    size: req.file.size
  });
});
```

**前端**: 在 `src/components/ChatInput.tsx` 中添加文件选择：

```typescript
const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;
  
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  
  // 在消息中引用文件
  setInputValue(prev => prev + `\n[文件: ${data.originalName}]`);
};
```

### 场景 8: 添加代码高亮显示

安装依赖:

```bash
npm install react-syntax-highlighter @types/react-syntax-highlighter
```

在 `src/components/ChatMessages.tsx` 中使用：

```typescript
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const renderMessageContent = (content: string) => {
  // 检测代码块
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  
  return content.split(codeBlockRegex).map((part, index) => {
    if (index % 3 === 1) {
      // 语言标识
      const language = part || 'text';
      const code = content.split(codeBlockRegex)[index + 1];
      
      return (
        <SyntaxHighlighter
          key={index}
          language={language}
          style={oneDark}
        >
          {code}
        </SyntaxHighlighter>
      );
    }
    
    if (index % 3 === 0) {
      return <span key={index}>{part}</span>;
    }
    
    return null;
  });
};
```

### 场景 9: 添加语音输入

使用 Web Speech API：

```typescript
// src/hooks/useSpeechRecognition.ts
import { useState, useEffect } from 'react';

export function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window)) {
      return;
    }
    
    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';
    
    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        }
      }
      
      if (finalTranscript) {
        setTranscript(prev => prev + finalTranscript);
      }
    };
    
    if (isListening) {
      recognition.start();
    } else {
      recognition.stop();
    }
    
    return () => recognition.stop();
  }, [isListening]);
  
  return {
    isListening,
    transcript,
    startListening: () => setIsListening(true),
    stopListening: () => setIsListening(false),
    resetTranscript: () => setTranscript('')
  };
}

// 在 ChatInput.tsx 中使用
const { isListening, transcript, startListening, stopListening, resetTranscript } = useSpeechRecognition();

useEffect(() => {
  if (transcript) {
    setInputValue(prev => prev + transcript);
    resetTranscript();
  }
}, [transcript]);
```

### 场景 10: 实现多标签页会话

**前端状态管理**: 在 `src/hooks/useSessions.ts` 中添加：

```typescript
const [openTabs, setOpenTabs] = useState<string[]>([]);

const openTab = useCallback((sessionId: string) => {
  setOpenTabs(prev => {
    if (!prev.includes(sessionId)) {
      return [...prev, sessionId];
    }
    return prev;
  });
}, []);

const closeTab = useCallback((sessionId: string) => {
  setOpenTabs(prev => prev.filter(id => id !== sessionId));
}, []);
```

**UI 实现**: 在 `src/components/Header.tsx` 中添加标签栏：

```typescript
<div className="tabs-container">
  {openTabs.map(tabId => {
    const session = sessions.find(s => s.id === tabId);
    return (
      <div 
        key={tabId}
        className={`tab ${currentSessionId === tabId ? 'active' : ''}`}
        onClick={() => navigate(`/chat/${tabId}`)}
      >
        <span>{session?.title}</span>
        <button onClick={(e) => {
          e.stopPropagation();
          closeTab(tabId);
        }}>×</button>
      </div>
    );
  })}
</div>
```

---

## API 参考

### 后端 API 端点

#### 健康检查
```
GET /api/health
响应: { status: "ok", timestamp: string }
```

#### 登录状态
```
GET /api/check-login
响应: {
  isLoggedIn: boolean,
  method?: 'env' | 'cli' | 'none',
  envConfigured?: boolean,
  cliConfigured?: boolean,
  apiKey?: string
}
```

#### 保存环境变量配置
```
POST /api/save-env-config
请求体: {
  apiKey?: string,
  authToken?: string,
  internetEnv?: string,
  baseUrl?: string
}
响应: { success: boolean, message: string }
```

#### 获取模型列表
```
GET /api/models
响应: {
  models: Array<{ modelId: string, name: string, description?: string }>,
  defaultModel: string
}
```

#### 获取所有会话
```
GET /api/sessions
响应: {
  sessions: Array<{
    id: string,
    title: string,
    model: string,
    created_at: string,
    updated_at: string,
    messageCount: number
  }>
}
```

#### 获取单个会话
```
GET /api/sessions/:sessionId
响应: {
  session: DbSession,
  messages: Array<DbMessage>
}
```

#### 创建会话
```
POST /api/sessions
请求体: {
  model?: string,
  title?: string
}
响应: { session: DbSession }
```

#### 更新会话
```
PATCH /api/sessions/:sessionId
请求体: {
  title?: string,
  model?: string
}
响应: { success: boolean }
```

#### 删除会话
```
DELETE /api/sessions/:sessionId
响应: { success: boolean }
```

#### 发送消息 (SSE 流式响应)
```
POST /api/chat
请求体: {
  sessionId?: string,
  message: string,
  model?: string,
  systemPrompt?: string,
  cwd?: string,
  permissionMode?: PermissionMode
}
响应: Server-Sent Events
  - type: "init" - 初始化
  - type: "text" - 文本内容
  - type: "tool" - 工具调用
  - type: "tool_result" - 工具结果
  - type: "permission_request" - 权限请求
  - type: "done" - 完成
  - type: "error" - 错误
```

#### 权限响应
```
POST /api/permission-response
请求体: {
  requestId: string,
  behavior: 'allow' | 'deny',
  message?: string
}
响应: { success: boolean }
```

---

## 常见定制需求

### 1. 修改默认模型

编辑 `server/index.ts`:

```typescript
const defaultModel = "claude-opus-4";  // 修改默认模型
```

### 2. 修改最大对话轮数

编辑 `server/index.ts` 的聊天处理函数:

```typescript
const stream = query({
  prompt: message,
  options: {
    maxTurns: 20,  // 从 10 改为 20
    ...
  }
});
```

### 3. 添加环境变量支持

创建 `.env` 文件:

```bash
PORT=3000
CODEBUDDY_API_KEY=your_api_key
CODEBUDDY_AUTH_TOKEN=your_auth_token
CODEBUDDY_BASE_URL=https://api.example.com
CODEBUDDY_INTERNET_ENVIRONMENT=external
```

在 `server/index.ts` 中使用:

```typescript
import dotenv from 'dotenv';
dotenv.config();

const PORT = process.env.PORT || 3000;
```

### 4. 自定义消息格式

编辑 `src/types.ts`，扩展 Message 类型:

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  contentBlocks?: ContentBlock[];
  // 自定义字段
  metadata?: {
    userId?: string;
    source?: string;
    tags?: string[];
  };
}
```

### 5. 添加用户认证

安装依赖:

```bash
npm install express-session passport passport-local bcrypt
```

在 `server/index.ts` 中添加认证中间件:

```typescript
import session from 'express-session';
import passport from 'passport';
import { Strategy as LocalStrategy } from 'passport-local';

app.use(session({
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: false
}));

app.use(passport.initialize());
app.use(passport.session());

// 配置认证策略
passport.use(new LocalStrategy(
  async (username, password, done) => {
    // 验证用户逻辑
    const user = await db.findUser(username);
    if (!user || !await bcrypt.compare(password, user.password)) {
      return done(null, false);
    }
    return done(null, user);
  }
));

// 保护路由
const requireAuth = (req, res, next) => {
  if (req.isAuthenticated()) {
    return next();
  }
  res.status(401).json({ error: '需要登录' });
};

app.post('/api/chat', requireAuth, async (req, res) => {
  // 聊天逻辑
});
```

### 6. 添加消息搜索功能

在 `server/db.ts` 中添加:

```typescript
export function searchMessages(query: string): DbMessage[] {
  const stmt = db.prepare(`
    SELECT * FROM messages 
    WHERE content LIKE ? 
    ORDER BY created_at DESC 
    LIMIT 100
  `);
  return stmt.all(`%${query}%`) as DbMessage[];
}
```

在 `server/index.ts` 中添加端点:

```typescript
app.get('/api/search', (req, res) => {
  const { q } = req.query;
  if (!q || typeof q !== 'string') {
    return res.status(400).json({ error: '缺少查询参数' });
  }
  
  const messages = db.searchMessages(q);
  res.json({ messages });
});
```

### 7. 添加 Markdown 渲染

安装依赖:

```bash
npm install react-markdown remark-gfm
```

在 `src/components/ChatMessages.tsx` 中使用:

```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MessageContent = ({ content }: { content: string }) => (
  <ReactMarkdown 
    remarkPlugins={[remarkGfm]}
    components={{
      code: ({ node, inline, className, children, ...props }) => {
        const match = /language-(\w+)/.exec(className || '');
        return !inline && match ? (
          <SyntaxHighlighter
            language={match[1]}
            style={oneDark}
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        ) : (
          <code className={className} {...props}>
            {children}
          </code>
        );
      }
    }}
  >
    {content}
  </ReactMarkdown>
);
```

### 8. 添加快捷键支持

在 `src/components/ChatInput.tsx` 中添加:

```typescript
const handleKeyDown = (e: React.KeyboardEvent) => {
  // Ctrl/Cmd + Enter 发送消息
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    handleSend();
  }
  
  // Esc 清空输入
  if (e.key === 'Escape') {
    setInputValue('');
  }
};

<textarea
  onKeyDown={handleKeyDown}
  ...
/>
```

### 9. 添加消息重新生成

在 `src/components/ChatMessages.tsx` 中添加:

```typescript
const handleRegenerate = async (messageId: string) => {
  // 找到该消息及其之前的用户消息
  const messageIndex = messages.findIndex(m => m.id === messageId);
  if (messageIndex < 0) return;
  
  const userMessage = messages[messageIndex - 1];
  if (!userMessage || userMessage.role !== 'user') return;
  
  // 删除该消息
  setSessions(prev => prev.map(s => {
    if (s.id === sessionId) {
      return {
        ...s,
        messages: s.messages.filter(m => m.id !== messageId)
      };
    }
    return s;
  }));
  
  // 重新发送用户消息
  await sendMessage(userMessage.content);
};
```

### 10. 添加会话分享功能

**后端**: 在 `server/index.ts` 中添加:

```typescript
app.post('/api/sessions/:sessionId/share', (req, res) => {
  const { sessionId } = req.params;
  const session = db.getSession(sessionId);
  const messages = db.getMessagesBySession(sessionId);
  
  if (!session) {
    return res.status(404).json({ error: '会话不存在' });
  }
  
  // 生成分享 token
  const shareToken = uuidv4();
  
  // 保存分享信息到数据库
  db.createShare({
    token: shareToken,
    session_id: sessionId,
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()  // 7天后过期
  });
  
  res.json({ 
    shareUrl: `${req.protocol}://${req.get('host')}/share/${shareToken}` 
  });
});

app.get('/api/share/:token', (req, res) => {
  const { token } = req.params;
  const share = db.getShare(token);
  
  if (!share || new Date(share.expires_at) < new Date()) {
    return res.status(404).json({ error: '分享链接不存在或已过期' });
  }
  
  const session = db.getSession(share.session_id);
  const messages = db.getMessagesBySession(share.session_id);
  
  res.json({ session, messages });
});
```

---

## 调试技巧

### 1. 查看 Agent SDK 日志

在 `server/index.ts` 中添加详细日志:

```typescript
for await (const msg of stream) {
  console.log("[Stream] Message:", JSON.stringify(msg, null, 2));
  // 处理消息...
}
```

### 2. 查看数据库内容

使用 SQLite 命令行工具:

```bash
sqlite3 data/chat.db

.tables                           # 查看所有表
SELECT * FROM sessions;           # 查看所有会话
SELECT * FROM messages LIMIT 10;  # 查看最近 10 条消息
```

### 3. 前端调试

在浏览器控制台中查看状态:

```typescript
// 在 useChat.ts 中添加
useEffect(() => {
  console.log('[useChat] State:', {
    isLoading,
    currentSessionId,
    messagesCount: currentSession?.messages.length
  });
}, [isLoading, currentSessionId, currentSession]);
```

### 4. 网络请求调试

在 Chrome DevTools 的 Network 标签中:
- 筛选 `Fetch/XHR`
- 查看 `EventStream` 类型的请求（SSE）
- 查看请求和响应的详细内容

---

## 常见问题

### Q: 如何修改端口号？

A: 在 `server/index.ts` 中修改:

```typescript
const PORT = process.env.PORT || 3001;  // 改为 3001
```

同时更新 `package.json` 中的开发命令:

```json
{
  "scripts": {
    "dev:server": "PORT=3001 tsx watch server/index.ts"
  }
}
```

### Q: 如何禁用权限检查？

A: 在创建会话时设置 `permissionMode` 为 `bypassPermissions`:

```typescript
const newSession: Session = {
  ...
  permissionMode: 'bypassPermissions'
};
```

或者在 Agent 配置中设置默认权限模式。

### Q: 如何清空所有数据？

A: 执行以下操作:

```typescript
// 使用数据库函数
db.clearAllData();

// 或直接删除数据库文件
rm data/chat.db
```

### Q: 消息没有显示怎么办？

A: 检查以下几点:

1. 后端是否正常接收到消息
2. SSE 流是否正常发送（查看 Network 标签）
3. 前端是否正确解析 SSE 事件
4. 状态是否正确更新

添加日志进行调试:

```typescript
console.log('[SSE] Received data:', data);
console.log('[State] Messages:', currentSession?.messages);
```

### Q: 如何添加新的工具？

A: CodeBuddy Agent SDK 的工具是由 SDK 内部管理的，无需在应用层添加。如果需要自定义工具行为，可以通过 `canUseTool` 回调进行控制。

---

## 生产部署

### 1. 构建生产版本

```bash
# 构建前端
npm run build

# 生成的文件在 dist/ 目录
```

### 2. 使用 PM2 部署

```bash
# 安装 PM2
npm install -g pm2

# 启动应用
pm2 start server/index.ts --name web-agent --interpreter tsx

# 查看状态
pm2 status

# 查看日志
pm2 logs web-agent
```

### 3. 使用 Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

构建和运行:

```bash
docker build -t web-agent .
docker run -p 3000:3000 -v $(pwd)/data:/app/data web-agent
```

### 4. 环境变量配置

在生产环境中使用环境变量:

```bash
# .env.production
PORT=3000
NODE_ENV=production
CODEBUDDY_API_KEY=your_api_key
CODEBUDDY_AUTH_TOKEN=your_auth_token
```

---

## 性能优化

### 1. 数据库优化

```typescript
// 添加索引
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
  CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at);
`);

// 定期清理旧数据
export function cleanOldSessions(daysOld: number = 30): void {
  const cutoffDate = new Date(Date.now() - daysOld * 24 * 60 * 60 * 1000);
  db.prepare('DELETE FROM sessions WHERE updated_at < ?')
    .run(cutoffDate.toISOString());
}
```

### 2. 前端优化

```typescript
// 使用 React.memo 避免不必要的重渲染
export const ChatMessage = React.memo(({ message }: { message: Message }) => {
  // 组件内容
});

// 使用虚拟滚动处理大量消息
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={100}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <ChatMessage message={messages[index]} />
    </div>
  )}
</FixedSizeList>
```

### 3. 缓存优化

```typescript
// 缓存模型列表
let cachedModels: Model[] = [];
let cacheTime: number = 0;
const CACHE_DURATION = 5 * 60 * 1000;  // 5 分钟

app.get('/api/models', async (req, res) => {
  const now = Date.now();
  if (cachedModels.length > 0 && now - cacheTime < CACHE_DURATION) {
    return res.json({ models: cachedModels });
  }
  
  // 获取新数据
  const models = await fetchModels();
  cachedModels = models;
  cacheTime = now;
  
  res.json({ models });
});
```

---

## 扩展阅读

- [CodeBuddy Agent SDK 文档](https://codebuddy.tencent.com)
- [Express.js 官方文档](https://expressjs.com/)
- [React Router 文档](https://reactrouter.com/)
- [TDesign React 组件库](https://tdesign.tencent.com/react/)
- [better-sqlite3 文档](https://github.com/WiseLibs/better-sqlite3)
- [Server-Sent Events (SSE) 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个模板。

## License

MIT
