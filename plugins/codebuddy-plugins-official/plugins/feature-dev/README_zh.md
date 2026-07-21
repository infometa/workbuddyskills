# 功能开发 Plugin

一个全面、结构化的功能开发工作流程,配备专门的 Agent 用于代码库探索、架构设计和质量审查。

## 概述

功能开发 Plugin 提供了一个系统化的 7 阶段方法来构建新功能。它不是直接跳到编码,而是引导你了解代码库、提出澄清问题、设计架构并确保质量——从而设计出更好、能与现有代码无缝集成的功能。

## 理念

构建功能不仅仅是写代码。你需要:
- 在修改之前**理解代码库**
- **提出问题**以澄清模糊的需求
- 在实施之前**深思熟虑地设计**
- 在构建之后**审查质量**

这个 Plugin 将这些实践嵌入到一个结构化的工作流程中,当你使用 `/feature-dev` 命令时会自动运行。

## 命令: `/feature-dev`

启动一个引导式的功能开发工作流程,包含 7 个不同的阶段。

**用法:**
```bash
/feature-dev Add user authentication with OAuth
```

或者简单地说:
```bash
/feature-dev
```

该命令将以交互方式引导你完成整个过程。

## 7 阶段工作流程

### 阶段 1: 发现

**目标**: 了解需要构建什么

**发生的事情:**
- 如果功能请求不清楚,进行澄清
- 询问你正在解决什么问题
- 识别约束和需求
- 总结理解并与你确认

**示例:**
```
You: /feature-dev Add caching
CodeBuddy: Let me understand what you need...
        - What should be cached? (API responses, computed values, etc.)
        - What are your performance requirements?
        - Do you have a preferred caching solution?
```

### 阶段 2: 代码库探索

**目标**: 了解相关的现有代码和模式

**发生的事情:**
- 并行启动 2-3 个 `code-explorer` Agent
- 每个 Agent 探索不同的方面(类似功能、架构、UI 模式)
- Agent 返回全面的分析以及需要阅读的关键文件
- CodeBuddy 阅读所有已识别的文件以建立深入理解
- 展示发现的全面摘要

**启动的 Agent:**
- "Find features similar to [feature] and trace implementation"
- "Map the architecture and abstractions for [area]"
- "Analyze current implementation of [related feature]"

**输出示例:**
```
Found similar features:
- User authentication (src/auth/): Uses JWT tokens, middleware pattern
- Session management (src/session/): Redis-backed, 24hr expiry
- API security (src/api/middleware/): Rate limiting, CORS

Key files to understand:
- src/auth/AuthService.ts:45 - Core authentication logic
- src/middleware/authMiddleware.ts:12 - Request authentication
- src/config/security.ts:8 - Security configuration
```

### 阶段 3: 澄清问题

**目标**: 填补空白并解决所有歧义

**发生的事情:**
- 审查代码库发现和功能请求
- 识别未充分说明的方面:
  - 边缘情况
  - 错误处理
  - 集成点
  - 向后兼容性
  - 性能需求
- 以有组织的列表呈现所有问题
- **在继续之前等待你的回答**

**示例:**
```
Before designing the architecture, I need to clarify:

1. OAuth provider: Which OAuth providers? (Google, GitHub, custom?)
2. User data: Store OAuth tokens or just user profile?
3. Existing auth: Replace current auth or add alongside?
4. Sessions: Integrate with existing session management?
5. Error handling: How to handle OAuth failures?
```

**关键**: 这个阶段确保在设计开始之前没有任何歧义。

### 阶段 4: 架构设计

**目标**: 设计多种实现方法

**发生的事情:**
- 启动 2-3 个具有不同重点的 `code-architect` Agent:
  - **最小化更改**: 最小的更改,最大的重用
  - **整洁架构**: 可维护性、优雅的抽象
  - **务实平衡**: 速度 + 质量
- 审查所有方法
- 对哪种方法最适合此任务形成意见
- 展示比较以及权衡和建议
- **询问你更喜欢哪种方法**

**输出示例:**
```
I've designed 3 approaches:

Approach 1: Minimal Changes
- Extend existing AuthService with OAuth methods
- Add new OAuth routes to existing auth router
- Minimal refactoring required
Pros: Fast, low risk
Cons: Couples OAuth to existing auth, harder to test

Approach 2: Clean Architecture
- New OAuthService with dedicated interface
- Separate OAuth router and middleware
- Refactor AuthService to use common interface
Pros: Clean separation, testable, maintainable
Cons: More files, more refactoring

Approach 3: Pragmatic Balance
- New OAuthProvider abstraction
- Integrate into existing AuthService
- Minimal refactoring, good boundaries
Pros: Balanced complexity and cleanliness
Cons: Some coupling remains

Recommendation: Approach 3 - gives you clean boundaries without
excessive refactoring, and fits your existing architecture well.

Which approach would you like to use?
```

### 阶段 5: 实施

**目标**: 构建功能

**发生的事情:**
- 在开始之前**等待明确批准**
- 阅读前面阶段中识别的所有相关文件
- 按照所选架构实施
- 严格遵循代码库约定
- 编写整洁、有文档记录的代码
- 在取得进展时更新 todos

**注意:**
- 实施仅在您批准后才开始
- 遵循阶段 2 中发现的模式
- 使用阶段 4 中设计的架构
- 持续跟踪进度

### 阶段 6: 质量审查

**目标**: 确保代码简单、DRY、优雅且功能正确

**发生的事情:**
- 并行启动 3 个具有不同重点的 `code-reviewer` Agent:
  - **简单性/DRY/优雅性**: 代码质量和可维护性
  - **Bug/正确性**: 功能正确性和逻辑错误
  - **约定/抽象**: 项目标准和模式
- 整合发现
- 识别最高严重性的问题
- **展示发现并询问你想做什么**:
  - 现在修复
  - 稍后修复
  - 照样继续
- 根据你的决定解决问题

**输出示例:**
```
Code Review Results:

High Priority Issues:
1. Missing error handling in OAuth callback (src/auth/oauth.ts:67)
2. Memory leak: OAuth state not cleaned up (src/auth/oauth.ts:89)

Medium Priority:
1. Could simplify token refresh logic (src/auth/oauth.ts:120)
2. Consider extracting OAuth config validation

All tests pass. Code follows project conventions.

What would you like to do?
```

### 阶段 7: 总结

**目标**: 记录已完成的工作

**发生的事情:**
- 将所有 todos 标记为完成
- 总结:
  - 构建了什么
  - 做出的关键决策
  - 修改的文件
  - 建议的后续步骤

**示例:**
```
Feature Complete: OAuth Authentication

What was built:
- OAuth provider abstraction supporting Google and GitHub
- OAuth routes and middleware integrated with existing auth
- Token refresh and session integration
- Error handling for all OAuth flows

Key decisions:
- Used pragmatic approach with OAuthProvider abstraction
- Integrated with existing session management
- Added OAuth state to prevent CSRF

Files modified:
- src/auth/OAuthProvider.ts (new)
- src/auth/AuthService.ts
- src/routes/auth.ts
- src/middleware/authMiddleware.ts

Suggested next steps:
- Add tests for OAuth flows
- Add more OAuth providers (Microsoft, Apple)
- Update documentation
```

## Agent

### `code-explorer`

**目的**: 通过跟踪执行路径深入分析现有代码库功能

**重点领域:**
- 入口点和调用链
- 数据流和转换
- 架构层和模式
- 依赖关系和集成
- 实现细节

**触发时机:**
- 在阶段 2 中自动触发
- 可以在探索代码时手动调用

**输出:**
- 带有 file:line 引用的入口点
- 逐步执行流程
- 关键组件和职责
- 架构洞察
- 需要阅读的基本文件列表

### `code-architect`

**目的**: 设计功能架构和实施蓝图

**重点领域:**
- 代码库模式分析
- 架构决策
- 组件设计
- 实施路线图
- 数据流和构建顺序

**触发时机:**
- 在阶段 4 中自动触发
- 可以在架构设计时手动调用

**输出:**
- 找到的模式和约定
- 带有基本原理的架构决策
- 完整的组件设计
- 带有特定文件的实施地图
- 带有阶段的构建顺序

### `code-reviewer`

**目的**: 审查代码的 bug、质量问题和项目约定

**重点领域:**
- 项目指南合规性(CLUAUDE.md)
- Bug 检测
- 代码质量问题
- 基于置信度的过滤(仅报告高置信度问题 ≥80)

**触发时机:**
- 在阶段 6 中自动触发
- 可以在编写代码后手动调用

**输出:**
- 关键问题(置信度 75-100)
- 重要问题(置信度 50-74)
- 带有 file:line 引用的具体修复
- 项目指南引用

## 使用模式

### 完整工作流程(推荐用于新功能):
```bash
/feature-dev Add rate limiting to API endpoints
```

让工作流程引导你完成所有 7 个阶段。

### 手动 Agent 调用:

**探索功能:**
```
"Launch code-explorer to trace how authentication works"
```

**设计架构:**
```
"Launch code-architect to design the caching layer"
```

**审查代码:**
```
"Launch code-reviewer to check my recent changes"
```

## 最佳实践

1. **对复杂功能使用完整工作流程**: 7 个阶段确保彻底的规划
2. **认真回答澄清问题**: 阶段 3 可以防止未来的困惑
3. **慎重选择架构**: 阶段 4 给你选项是有原因的
4. **不要跳过代码审查**: 阶段 6 在问题到达生产环境之前捕获它们
5. **阅读建议的文件**: 阶段 2 识别关键文件——阅读它们以了解上下文

## 何时使用此 Plugin

**适用于:**
- 涉及多个文件的新功能
- 需要架构决策的功能
- 与现有代码的复杂集成
- 需求有些不清楚的功能

**不适用于:**
- 单行 bug 修复
- 琐碎的更改
- 明确定义的简单任务
- 紧急热修复

## 要求

- 已安装 CodeBuddy Code
- Git 仓库(用于代码审查)
- 具有现有代码库的项目(工作流程假设有现有代码可供学习)

## 故障排除

### Agent 耗时太长

**问题**: 代码探索或架构 Agent 很慢

**解决方案**:
- 对于大型代码库,这是正常的
- Agent 尽可能并行运行
- 这种彻底性会在更好的理解中得到回报

### 澄清问题太多

**问题**: 阶段 3 问了太多问题

**解决方案**:
- 在初始功能请求中更具体
- 提前提供有关约束的上下文
- 如果真的没有偏好,说"whatever you think is best"

### 架构选项太多

**问题**: 阶段 4 中有太多架构选项

**解决方案**:
- 信任建议——它基于代码库分析
- 如果仍然不确定,请寻求更多解释
- 如果有疑问,选择务实的选项

## 提示

- **在功能请求中具体说明**: 更多细节 = 更少的澄清问题
- **信任流程**: 每个阶段都建立在前一个阶段的基础上
- **审查 Agent 输出**: Agent 提供有关代码库的有价值见解
- **不要跳过阶段**: 每个阶段都有其目的
- **用于学习**: 探索阶段教你了解自己的代码库

## 作者

Sid Bidasaria (sbidasaria@anthropic.com)

## 版本

1.0.0
