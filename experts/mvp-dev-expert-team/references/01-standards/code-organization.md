---
id: code-organization
title: 代码组织规范（分层·分包·不堆单文件，商业级必读）
domain: agentic-delivery
category: 01-standards
difficulty: advanced
tags: [code-organization, layered-architecture, single-responsibility, file-size-limit, module-boundary, 分层架构, 单一职责, 文件拆分, 目录结构, 反堆单文件]
quality_score: 95
last_updated: 2026-07-19
---
# 代码组织规范（商业级必读）

> 生成式代码最常见的结构性烂账不是"某行写错"，而是**把所有东西堆进一两个大文件**——路由、业务逻辑、数据库查询、工具函数全塞进 `app.ts` / `index.js`，单文件上千行，改一处牵全身，测不动也读不懂。这份规范把"分层、分包、不堆单文件"立成可执行纪律：从"愿景式提醒"升级成"出现即不合格 + 配套防线"。架构师定义的分层（表现层/业务层/数据层）在本规范落地为**具体的目录与文件约束**。

## 1. 分层架构原则（依赖只能向下）

```
表现层 (Routes / Controllers)   ← 只做：参数校验、调用 service、组装 HTTP 响应
        ↓ 依赖
业务层 (Services)               ← 只做：业务规则、事务编排、调用 repository
        ↓ 依赖
数据层 (Repositories / Models)  ← 只做：数据读写、ORM 查询、映射
        ↓
基础设施 (DB / Cache / 第三方)   ← 连接、客户端实例
```

**铁律**：
- 依赖**只能向下**：上层 import 下层，下层**禁止**反向 import 上层。
- Controller **禁止**直接操作数据库（必须经 service）。
- Service **禁止** import HTTP 对象（`req`/`res`），不返回 HTTP 响应，只返回业务结果/抛业务异常。
- Repository **禁止**含业务逻辑（if 余额 > 0 之类），只做数据存取。
- 跨模块（如订单调用户）通过对方的 **service 接口**，不跨层、不直连对方 repository。

## 2. 后端目录结构模板

> 以下为常见技术栈的目录**示例，非指定**。技术栈由架构师按项目选型并在 Spec 锁定；目录名按所选框架的惯例组织，但**分层依赖关系（§1）与文件组织硬规则（§4）是强制的、技术栈无关**。
### 方案 A：Express + TypeScript + Prisma

```
src/
├── routes/              # 路由定义（只挂载端点 + 接中间件，不写逻辑）
│   ├── index.ts         # 路由聚合
│   ├── auth.routes.ts   # 每个资源一个路由文件
│   └── task.routes.ts
├── controllers/         # 控制器（参数校验 → 调 service → 组装响应）
│   ├── auth.controller.ts
│   └── task.controller.ts
├── services/            # 业务逻辑（事务、规则、编排）
│   ├── auth.service.ts
│   └── task.service.ts
├── repositories/        # 数据访问（Prisma 查询封装）
│   ├── auth.repository.ts
│   └── task.repository.ts
├── middlewares/         # 认证、限流、错误捕获、日志
│   ├── auth.middleware.ts
│   ├── error.middleware.ts
│   └── rate-limit.middleware.ts
├── validators/          # Zod schema（请求体校验）
│   ├── auth.schema.ts
│   └── task.schema.ts
├── utils/               # 纯工具函数（无业务、无副作用）
├── types/               # TypeScript 类型定义
├── config/              # 配置加载（env、db 连接）
└── app.ts               # 入口：只做装配（挂中间件 + 路由 + 启动），不写业务
```

### 方案 B：FastAPI + SQLAlchemy

```
app/
├── api/                 # 路由（router 端点，调 service）
│   ├── deps.py          # 依赖注入（当前用户、db session）
│   ├── auth.py
│   └── tasks.py
├── services/            # 业务逻辑
│   ├── auth_service.py
│   └── task_service.py
├── repositories/        # 数据访问（SQLAlchemy 查询）
│   ├── auth_repo.py
│   └── task_repo.py
├── models/              # ORM 模型定义
├── schemas/             # Pydantic 请求/响应模型
├── core/                # 配置、安全、异常
├── utils/
└── main.py              # 入口：只装配（app 实例 + include_router + 启动）
```

### 方案 C：CloudBase 云函数

```
cloud-functions/
├── login/
│   ├── index.js         # 入口：路由分发（薄）
│   ├── service.js       # 业务逻辑
│   ├── repo.js          # 数据库操作
│   └── package.json
└── get-tasks/
    ├── index.js
    ├── service.js
    ├── repo.js
    └── package.json
```

## 3. 前端目录结构

前端多框架目录模板见 `agents/mvp-dev-expert-team-frontend.md`「项目目录结构」章节（Vue / Next.js / Taro / Nuxt 均含 `pages/components/services/utils/types/stores` 分层）。同样遵循：组件按功能拆分、API 调用统一封装在 `services/`、页面只做组装不堆逻辑。

## 4. 文件组织硬规则（出现即不合格）

| # | 规则 | 不合格表现 |
|---|------|-----------|
| 1 | **单一职责**：一个文件一个主职责、一个主导出 | 一个文件同时放路由+逻辑+SQL+工具 |
| 2 | **单文件 ≤ 300 行**（不含空行注释）。超限必须拆分（按子功能拆文件，不是拆函数凑数） | `app.ts` / `index.js` 单文件 800 行 |
| 3 | **按资源/功能分包**：一个资源 = 一个 controller + 一个 service + 一个 repository | 所有 controller 堆进一个 `controllers.ts` |
| 4 | **入口文件只装配**：`app.ts`/`main.py` 只做挂中间件、挂路由、启动，**不写任何业务逻辑** | 入口里写 `router.post(...)` + 业务实现 |
| 5 | **业务逻辑不进路由处理器**：router/controller 只编排，逻辑下沉到 service | `router.post('/tasks', async (req,res)=>{ /* 50行业务 */ })` |
| 6 | **工具函数纯净**：`utils/` 只放无业务、无副作用的纯函数，不放业务逻辑 | 把"创建订单"放进 utils |
| 7 | **类型/Schema 单独成文件**：请求校验、类型定义独立，不混进逻辑文件 | Zod schema 和业务逻辑写一个文件 |

> 300 行是硬上限不是目标。一个 controller 文件超过 200 行就该警惕——大概率是把 service 的活干进来了。

## 5. 模块边界与依赖方向

```
✅ 允许：controller → service → repository
❌ 禁止：repository → service（反向）
❌ 禁止：controller → repository（跨层）
❌ 禁止：service A → repository B（跨模块直连数据层，应调 service B）
❌ 禁止：service import res/req（业务层耦合 HTTP）
```

跨模块协作走 service 接口：订单服务需要用户信息 → 调 `userService.getById()`，不直接查用户表。

## 6. 反模式（出现即不合格）

1. **巨型入口文件**：把所有路由 + 中间件 + 业务 + 启动全塞 `app.ts`。
2. **路由处理器里写业务**：`router.post` 回调里几十行业务逻辑 + SQL。
3. **单文件超 300 行**：尤其 controller / service / 入口。
4. **跨层调用**：controller 直接 `prisma.task.findMany()`。
5. **业务逻辑进 utils**：`utils/createOrder.ts` 里写订单创建流程。
6. **按类型而非功能堆放**：所有 controller 一个文件、所有 service 一个文件。
7. **service 返回 HTTP 响应**：`res.json(...)` 出现在 service 层。
8. **配置硬编码散落**：连接串/密钥写进业务文件而非 `config/`。

## 7. 代码组织自检清单（每次交付前必填）

- [ ] 入口文件只装配，无业务逻辑，行数 < 100
- [ ] 每个文件单一职责，单文件 ≤ 300 行（超限已拆分）
- [ ] controller 不直接操作数据库，逻辑下沉 service
- [ ] service 不 import HTTP 对象，不返回 HTTP 响应
- [ ] repository 不含业务逻辑
- [ ] 按资源分包，每资源 controller+service+repository 三件套
- [ ] 请求校验/类型独立成文件
- [ ] utils 只放纯函数
- [ ] 依赖只向下不反向、不跨层、不跨模块直连数据层
- [ ] 无巨型文件（grep 统计 `wc -l` 最大文件 ≤ 300 行）

## 8. 门禁命令

```bash
# 找出超过 300 行的源文件（不合格即退回）
find src -name '*.ts' -o -name '*.js' -o -name '*.py' | xargs wc -l | sort -rn | awk '$1>300 && $2!="total" {print "OVER LIMIT:", $0}'
# 入口文件行数检查
wc -l src/app.ts app/main.py 2>/dev/null
```

发现任何文件超 300 行或入口含业务逻辑 → **退回开发重做**，不算通过 Phase 3。
