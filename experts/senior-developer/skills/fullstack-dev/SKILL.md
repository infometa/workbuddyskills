---
name: fullstack-dev
description: |
  Full-stack backend architecture and frontend-backend integration guide.
  TRIGGER when: building a full-stack app, creating REST API with frontend, scaffolding backend service,
  building todo app, building CRUD app, building real-time app, building chat app,
  Express + React, Next.js API, Node.js backend, Python backend, Go backend,
  designing service layers, implementing error handling, managing config/auth,
  setting up API clients, implementing auth flows, handling file uploads,
  adding real-time features (SSE/WebSocket), hardening for production.
  DO NOT TRIGGER when: pure frontend UI work, pure CSS/styling, database schema only,
  simple scripts, bug fixes, single-file changes, adding a small feature to existing code.
description_zh: "全栈应用架构与开发指南"
description_en: "Full-stack architecture guide (REST API, Express, React, Next.js)"
license: MIT
metadata:
  category: full-stack
  version: "1.1.0"
---

# Full-Stack Development Practices

## MANDATORY WORKFLOW

**触发此 skill 后，必须按以下步骤执行：**

### Step 0: Gather Requirements

确认以下信息（如用户已指定则跳过）：

1. **Stack**: 后端+前端语言/框架
2. **Service type**: API-only / 全栈单体 / 微服务
3. **Database**: SQL / NoSQL
4. **Integration**: REST / GraphQL / tRPC / gRPC
5. **Real-time**: SSE / WebSocket / Polling /不需要
6. **Auth**: JWT / Session / OAuth / 不需要

### Step 1: Architectural Decisions

基于需求做出并声明决策（每个决策一句话）：

| 决策项 | 参考 |
|--------|------|
|项目结构 | Feature-first（推荐）vs Layer-first |
| API 客户端 | Typed fetch / React Query / tRPC / OpenAPI |
| 认证策略 | JWT + refresh / session / 第三方 |
| 实时方案 | Polling / SSE / WebSocket |
| 错误处理 | Typed error hierarchy + global handler |

### Step 2: Scaffold with Checklist

**后端服务 Checklist：**
- [ ] Feature-first 项目结构
- [ ] 配置集中管理，环境变量启动时验证（fail fast）
- [ ] 类型化错误层级（非通用 Error）
- [ ] 全局错误处理中间件
- [ ] 结构化 JSON 日志 + request ID
- [ ] 数据库 Migration +连接池
- [ ] 输入验证（Zod / Pydantic / Go validator）
- [ ] 认证中间件
- [ ] 健康检查端点（`/health`, `/ready`）
- [ ] 优雅关闭（SIGTERM）
- [ ] CORS 配置（显式 origin）
- [ ] 安全头（helmet等）
- [ ] `.env.example`（不含真实密钥）

**前后端集成 Checklist：**
- [ ] 类型化 API Client
- [ ] Base URL 从环境变量读取
- [ ] Auth token 自动附加
- [ ] API 错误映射为用户友好消息
- [ ] Loading 状态处理
- [ ] 跨边界类型安全
- [ ] CORS 显式配置
- [ ] Refresh token 流程

### Step 3: Implement

按照 references 中的模式编写代码。每完成一个模块立即验证。

### Step 4: Verify

```bash
# 构建检查
cd server && npm run build
cd client && npm run build

# 冒烟测试
curl http://localhost:3000/health

# 集成检查：前端能连通后端
```

### Step 5: Handoff

```
📦 交付：
- 实现的功能和端点列表
- 启动命令
- 已知限制 / 下一步建议
- 关键文件列表
```

---

## 7条铁律

1. 按**Feature** 组织代码，不按技术层
2. Controller 不含业务逻辑
3. Service 不导入 HTTP 请求/响应类型
4. 所有配置来自环境变量，启动时验证
5. 所有错误类型化、结构化返回
6. 所有输入在边界处验证
7. 结构化 JSON 日志 + request ID

---

## 详细参考文档（按需查阅）

需要具体代码模式和深入指导时，查阅以下参考文档：

| 主题 | 参考文件 |
|------|---------|
| 项目结构、三层架构、DI 模式 | [references/architecture-patterns.md](references/architecture-patterns.md) |
| API 设计（URL、状态码、分页） | [references/api-design.md](references/api-design.md) |
| 认证流程（JWT、刷新、RBAC） | [references/auth-flow.md](references/auth-flow.md) |
| 数据库 Schema、索引、迁移 | [references/db-schema.md](references/db-schema.md) |
| Django 最佳实践 | [references/django-best-practices.md](references/django-best-practices.md) |
| 环境管理与CORS | [references/environment-management.md](references/environment-management.md) |
| 发布检查清单 | [references/release-checklist.md](references/release-checklist.md) |
| 技术选型决策 | [references/technology-selection.md](references/technology-selection.md) |
| 测试策略 | [references/testing-strategy.md](references/testing-strategy.md) |

---

## 反模式速查

|❌ 不要| ✅ 应该 |
|---------|---------|
| 业务逻辑写在路由/Controller | 移到 Service 层 |
| `process.env` 散落各处 | 集中配置模块 |
| `console.log` | 结构化 JSON Logger |
| 通用 `Error('oops')` | 类型化错误类|
| Controller 直接查DB | Repository 模式 |
| 无输入验证 | 边界验证（Zod/Pydantic） |
| 静默吞错 | 日志 + 重抛或返回错误 |
| 无健康检查 | `/health` + `/ready` |
| 硬编码配置密钥 | 环境变量 |
| 无优雅关闭 | 处理 SIGTERM |
| 前端硬编码 API URL | 环境变量 |
| JWT 存localStorage | Memory + httpOnly cookie |
| 展示原始 API错误 | 映射为用户友好消息 |
| 大文件走 API Server | Presigned URL 直传 |
