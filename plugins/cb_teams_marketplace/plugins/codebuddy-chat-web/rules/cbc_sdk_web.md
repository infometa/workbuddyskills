---
description: Use the init-cbc-sdk-web skill to create web-based chat applications. This rule MUST be applied when the user says any of these trigger phrases - Chinese "帮我创建一个 Agent Web 应用", "初始化一个聊天应用", "搭建一个 Web Agent", "创建 SDK Web 项目" or English "create an agent web app", "initialize a chat application", "build a web agent", "scaffold an SDK web project". The skill uses templates and must copy from template directory, never write code from scratch.
alwaysApply: true
enabled: true
updatedAt: 2026-02-07T00:00:00.000Z
provider: codebuddy-chat-web
---

# CodeBuddy Agent SDK Web 开发指南

这是一个快速开发指南,帮助你基于模板创建自定义 Web Agent 应用。

**关联技能**: `/init-cbc-sdk-web` - 这是一个本地技能,会从模板目录复制完整的项目结构

## ⚠️ 重要说明

**`/init-cbc-sdk-web` 是一个本地技能(Skill),不是普通的 CLI 命令!**

**这个技能有预置的完整项目模板,必须从模板目录复制,不要从零编写代码!**

### 模板位置

模板文件位于以下位置之一:
1. 已加载的 skill: `~/.codebuddy/skills/init-cbc-sdk-web/templates/`
2. Marketplace plugins: `~/.codebuddy/plugins/marketplaces/*/plugins/codebuddy-chat-web/skills/init-cbc-sdk-web/templates/`
3. 当前工作目录: `.codebuddy/skills/init-cbc-sdk-web/templates/`

### 如何使用模板

**方法 1: 使用复制脚本(推荐)**

在 skill 目录下有一个 `copy-template.sh` 脚本,使用它来复制模板:

```bash
# 找到 skill 目录(会搜索所有可能的位置)
SKILL_DIR=$(find ~/.codebuddy/skills ~/.codebuddy/plugins .codebuddy/skills -path "*/codebuddy-chat-web/skills/init-cbc-sdk-web" -o -name "init-cbc-sdk-web" -type d 2>/dev/null | head -1)

# 使用脚本复制模板
bash "$SKILL_DIR/copy-template.sh" my-agent-app
```

**方法 2: 手动复制**

如果脚本不可用,手动复制模板内容(注意:复制模板**内容**,不是模板目录本身):

```bash
# 找到模板位置(会递归搜索所有可能的目录)
TEMPLATE_DIR=$(find ~/.codebuddy/skills ~/.codebuddy/plugins .codebuddy/skills -path "*/init-cbc-sdk-web/templates" -type d 2>/dev/null | head -1)

# 创建项目目录并复制模板内容
mkdir -p my-agent-app
cp -r "$TEMPLATE_DIR/"* my-agent-app/
```

### 重要提醒

- ❌ **不要**从零开始编写代码
- ❌ **不要**尝试手动创建所有文件
- ✅ **必须**从模板目录复制完整项目
- ✅ **必须**保持模板的完整文件结构

## 推荐工作流程

### 第零步:检查 CodeBuddy Code 是否已安装

在开始之前,必须确保 CodeBuddy Code 已安装:

```bash
# 检查是否已安装
codebuddy --help

# 如果未安装,执行以下命令安装
npm install -g @tencent-ai/codebuddy-code
```

### 第一步:使用模板创建应用

```bash
# 使用技能初始化项目(会从 templates/ 目录复制完整项目)
/init-cbc-sdk-web my-agent-app

# 进入项目目录
cd my-agent-app

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**模板包含的完整文件结构**:
```
my-agent-app/
├── server/              # 后端服务
│   ├── server.ts       # Express + WebSocket 服务器
│   ├── agent.ts        # Agent SDK 封装
│   ├── chat-session.ts # 会话管理
│   ├── store.ts        # 数据存储
│   ├── config.ts       # 配置文件
│   └── types.ts        # 类型定义
├── client/              # 前端应用
│   ├── App.tsx         # 主应用组件
│   ├── components/     # UI 组件
│   └── hooks/          # React Hooks
├── package.json         # 依赖配置
├── tsconfig.json        # TypeScript 配置
├── vite.config.ts       # Vite 配置
├── tailwind.config.js   # Tailwind 配置
└── .env.example         # 环境变量模板
```

### 第二步:根据需求定制应用

在 `server/index.ts` 中修改 `systemPrompt` 来定制你的 Agent:

```typescript
const systemPrompt = `
你是一个 [你的 Agent 角色],专门帮助用户 [主要功能]。

核心能力:
1. [能力描述]
2. [能力描述]
3. [能力描述]

工作方式:
- [工作方式描述]
- [输出格式要求]
`;
```

### 第三步:测试和迭代

1. 在浏览器中访问 http://localhost:3000
2. 测试你的 Agent 功能
3. 根据效果调整 systemPrompt
4. 如需更多功能,参考下方 SDK 文档

### 第四步:遇到问题时查阅文档

**官方文档**(需要深入了解时参考):
- **TypeScript SDK 文档**: https://www.codebuddy.ai/docs/zh/cli/sdk-typescript
- **通用 SDK 文档**: https://www.codebuddy.ai/docs/zh/cli/sdk

---

## 常见定制场景

### 场景 1:修改系统提示词

最简单的定制方式,直接修改 `server/index.ts` 中的 `systemPrompt`:

```typescript
const systemPrompt = `你是一个代码审查助手,帮助开发者提高代码质量。`;
```

### 场景 2:调整 AI 模型

在 `server/index.ts` 中修改模型配置:

```typescript
const config = {
  model: "claude-sonnet-4",  // 或 "claude-opus-4"
  maxTurns: 10,
  cwd: process.cwd()
};
```

### 场景 3:限制工具访问

控制 Agent 可以使用的工具:

```typescript
const config = {
  allowedTools: ["Read", "Grep", "WebSearch"],  // 只允许这些工具
  // ...其他配置
};
```

---

## 快速参考:核心概念

### Query API(单次对话)

```typescript
import { query } from "@tencent-ai/agent-sdk";

const stream = query({
  prompt: "你的问题",
  options: { model: "claude-sonnet-4" }
});

for await (const message of stream) {
  console.log(message);
}
```

### Session API(多轮对话)

```typescript
import { unstable_v2_createSession } from "@tencent-ai/agent-sdk";

const session = await unstable_v2_createSession({
  model: "claude-sonnet-4"
});

await session.sendMessage("第一条消息");
await session.sendMessage("后续消息");
```

### 消息类型

SDK 返回三种消息类型:
- **System**: 会话初始化信息
- **Assistant**: AI 的回复内容
- **Result**: 执行完成的统计信息(耗时、成本)

---

## 配置选项速查表

| 选项 | 说明 | 示例 |
|------|------|------|
| `model` | AI 模型 | `"claude-sonnet-4"` |
| `maxTurns` | 最大对话轮数 | `10` |
| `systemPrompt` | 系统提示词 | `"你是助手"` |
| `allowedTools` | 允许的工具 | `["Read", "Write"]` |
| `cwd` | 工作目录 | `process.cwd()` |

---

## 进阶功能(需要时查阅)

当你需要以下功能时,请查阅官方文档:

### 1. 错误处理
处理 SDK 异常和连接错误

### 2. 权限控制
使用 `canUseTool` 回调精细控制工具访问

### 3. 自定义 Agent
定义专门的子 Agent 处理特定任务

### 4. MCP 服务器
集成自定义工具和功能

### 5. Hook 系统
在工具执行前后插入自定义逻辑

---

## 生产环境建议

### 安全性
- 将 SDK 隔离到独立服务/容器
- 添加用户认证和授权
- 验证和清理用户输入

### 性能
- 使用数据库替代内存存储
- 添加请求限流
- 实现日志和监控

### 配置
- 使用环境变量管理敏感信息
- 设置合适的 CORS 策略
- 配置 HTTPS

---

## 完整文档链接

需要深入了解时,请访问:

- **TypeScript SDK 文档**: https://www.codebuddy.ai/docs/zh/cli/sdk-typescript
- **通用 SDK 文档**: https://www.codebuddy.ai/docs/zh/cli/sdk

文档涵盖:
- 完整 API 参考
- 高级配置选项
- 自定义 Agent 和 MCP 服务器
- Hook 系统详解
- 权限控制机制
- 多 Agent 协作
- Python SDK 使用
- 生产部署指南
