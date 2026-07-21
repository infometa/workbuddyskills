# CodeBuddy Agent SDK 开发插件

用于创建和验证 CodeBuddy Agent SDK 应用的综合开发插件。

## 概述

CodeBuddy Agent SDK Development Plugin 简化了构建 Agent SDK 应用的整个生命周期，从初始脚手架到最佳实践验证。它帮助你快速启动新项目，并确保你的应用遵循官方文档模式。

## 关于 CodeBuddy Agent SDK

CodeBuddy Agent SDK 允许你以编程方式构建具有 CodeBuddy 能力的 AI 智能体。你可以创建自主代理来执行各种任务，包括：

- **开发工具增强**: 代码审查、自动化测试、文档生成
- **自动化工作流**: CI/CD 集成、部署自动化
- **企业应用**: 客户支持、数据分析、内容创作

### SDK 信息

| 语言 | 包名 | 安装命令 |
|------|------|----------|
| TypeScript | `@tencent-ai/agent-sdk` | `npm install @tencent-ai/agent-sdk` |
| Python | `codebuddy-agent-sdk` | `pip install codebuddy-agent-sdk` |

### 环境要求

- **Node.js**: >= 18.0.0（TypeScript）
- **Python**: >= 3.10（Python）
- **CodeBuddy CLI**: 已安装

## 功能特性

### 命令: `/new-sdk-app`

交互式命令，引导你创建新的 CodeBuddy Agent SDK 应用。

**功能说明:**
- 询问关于项目的澄清问题（语言、名称、agent 类型、起始点）
- 检查并安装最新 SDK 版本
- 创建所有必要的项目文件和配置
- 设置正确的环境文件（.env.example, .gitignore）
- 提供针对你用例的工作示例
- 运行类型检查（TypeScript）或语法验证（Python）
- 自动使用相应的验证器 agent 验证设置

**使用方法:**
```bash
/new-sdk-app my-project-name
```

或简单地:
```bash
/new-sdk-app
```

该命令会交互式询问:
1. 语言选择（TypeScript 或 Python）
2. 项目名称（如未提供）
3. Agent 类型（编码、业务、自定义）
4. 起始点（最小化、基础、或特定示例）
5. 工具偏好（npm/yarn/pnpm 或 pip/uv/poetry）

**示例:**
```bash
/new-sdk-app customer-support-agent
# → 创建新的 Agent SDK 项目
# → 设置 TypeScript 或 Python 环境
# → 安装最新 SDK 版本
# → 自动验证设置
```

### Agent: `agent-sdk-verifier-py`

全面验证 Python Agent SDK 应用的正确设置和最佳实践。

**验证检查:**
- SDK 安装和版本（`codebuddy-agent-sdk`）
- Python 环境设置（requirements.txt, pyproject.toml）
- 正确的 SDK 使用和模式
- Agent 初始化和配置
- 环境和安全性（API 密钥配置）
- 错误处理和功能
- 文档完整性

**使用方法:**
该 agent 在 `/new-sdk-app` 创建 Python 项目后自动运行，或你可以通过询问触发:
```
"验证我的 Python Agent SDK 应用"
"检查我的 SDK 应用是否遵循最佳实践"
```

### Agent: `agent-sdk-verifier-ts`

全面验证 TypeScript Agent SDK 应用的正确设置和最佳实践。

**验证检查:**
- SDK 安装和版本（`@tencent-ai/agent-sdk`）
- TypeScript 配置（tsconfig.json）
- 正确的 SDK 使用和模式
- 类型安全和导入
- Agent 初始化和配置
- 环境和安全性（API 密钥配置）
- 错误处理和功能
- 文档完整性

**使用方法:**
该 agent 在 `/new-sdk-app` 创建 TypeScript 项目后自动运行，或你可以通过询问触发:
```
"验证我的 TypeScript Agent SDK 应用"
"检查我的 SDK 应用是否遵循最佳实践"
```

## 工作流示例

以下是使用此插件的典型工作流:

1. **创建新项目:**
```bash
/new-sdk-app code-reviewer-agent
```

2. **回答交互式问题:**
```
语言: TypeScript
Agent 类型: 编码 agent（代码审查）
起始点: 带常用功能的基础 agent
```

3. **自动验证:**
命令自动运行 `agent-sdk-verifier-ts` 确保一切正确设置。

4. **开始开发:**
```bash
# 设置你的 API 密钥
export CODEBUDDY_API_KEY="your-api-key"

# 运行你的 agent
npm start
```

5. **修改后验证:**
```
"验证我的 SDK 应用"
```

## 快速开始示例

### TypeScript

```typescript
import { query } from '@tencent-ai/agent-sdk';

async function main() {
  const q = query({
    prompt: '请解释什么是递归函数',
    options: { permissionMode: 'bypassPermissions' }
  });
  
  for await (const message of q) {
    if (message.type === 'assistant') {
      for (const block of message.message.content) {
        if (block.type === 'text') {
          console.log(block.text);
        }
      }
    }
  }
}

main();
```

### Python

```python
import asyncio
from codebuddy_agent_sdk import query, CodeBuddyAgentOptions, AssistantMessage, TextBlock

async def main():
    options = CodeBuddyAgentOptions(permission_mode="bypassPermissions")
    async for message in query(prompt="请解释什么是递归函数", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

asyncio.run(main())
```

## 认证配置

### 三种认证方式

1. **已有登录凭据**: 自动使用 `codebuddy` CLI 的认证信息

2. **API Key 认证**:
```bash
export CODEBUDDY_API_KEY="your-api-key"
```

3. **OAuth Client Credentials**（企业用户）: 通过 OAuth 2.0 流程获取 access token

## 核心功能

| 功能 | 说明 |
|------|------|
| 消息流式传输 | 实时接收系统消息和工具结果 |
| 多轮对话 | 跨推理调用的上下文保持 |
| 会话管理 | 通过会话 ID 继续对话 |
| 细粒度权限控制 | canUseTool 回调 |
| Hook 系统 | 工具执行前后的自定义逻辑 |
| 自定义 Agent | 定义专业化的 Agent |
| MCP 服务器集成 | 连接外部工具和服务 |

## 权限模式

| 模式 | 说明 |
|------|------|
| `default` | 所有操作需确认 |
| `acceptEdits` | 自动批准文件编辑 |
| `plan` | 只读模式 |
| `bypassPermissions` | 跳过所有权限检查 |

## 最佳实践

- **始终使用最新 SDK 版本**: `/new-sdk-app` 会检查并安装最新版本
- **部署前验证**: 在部署到生产环境前运行验证器 agent
- **保护 API 密钥安全**: 使用环境变量，不要硬编码
- **遵循 SDK 文档**: 验证器 agents 会根据官方模式进行检查
- **TypeScript 项目进行类型检查**: 定期运行 `npx tsc --noEmit`
- **权限控制**: 生产环境使用 `canUseTool` 实现细粒度权限
- **资源限制**: 使用 `maxTurns` 防止资源消耗

## 官方文档

- [SDK 概览](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk.md)
- [TypeScript SDK 参考](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-typescript.md)
- [Python SDK 参考](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-python.md)
- [SDK 会话管理](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-sessions.md)
- [SDK Hook 系统](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-hooks.md)
- [SDK 权限控制](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-permissions.md)
- [SDK MCP 集成](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-mcp.md)
- [SDK 自定义工具](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-custom-tools.md)
- [SDK 示例项目](https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-demos.md)

## 故障排除

### TypeScript 项目中的类型错误

**问题**: 创建后 TypeScript 项目有类型错误

**解决方案**:
- `/new-sdk-app` 命令会自动运行类型检查
- 如果错误持续，检查是否使用最新 SDK 版本
- 验证你的 `tsconfig.json` 符合 SDK 要求
- 确保 Node.js 版本 >= 18.0.0

### Python 导入错误

**问题**: 无法从 `codebuddy_agent_sdk` 导入

**解决方案**:
- 确保已安装依赖: `pip install codebuddy-agent-sdk`
- 如果使用虚拟环境，请激活它
- 检查 SDK 是否已安装: `pip show codebuddy-agent-sdk`
- 确保 Python 版本 >= 3.10

### 认证问题

**问题**: API 调用失败

**解决方案**:
- 检查 `CODEBUDDY_API_KEY` 环境变量是否设置
- 确保 CodeBuddy CLI 已安装并登录
- 检查网络连接

## 作者

CodeBuddy Team (codebuddy@tencent.com)

## 版本

1.0.0
