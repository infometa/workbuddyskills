# 能力模块 · API 授权（Authorization）

> **本文件是「用户应用 API 授权」能力的唯一 owner**，覆盖其全生命周期：**detect → confirm → inject → test**。
> **可选能力**：按需启用（见 `modules/registry.md`）。§1 detect 命中（有写接口/敏感路径）+ §2 用户确认后才执行后续锚点；未启用时主线全程跳过 authz。
> 主线各阶段只做编排，授权相关细节一律委派到本文件对应锚点：
>
> | 锚点 | 被调用阶段 | 职责 |
> |------|-----------|------|
> | [`#detect`](#detect-分析阶段-1) | §1 分析 | 扫描现有鉴权 / 名单来源 / API 敏感度 |
> | [`#confirm`](#confirm-建议阶段-2) | §2 建议 | API 复用/新增确认 + 授权清单确认 |
> | [`#inject`](#inject-创建阶段-3) | §3 创建 | 生成中间件 + Role Resolver + 授权清单，注入应用 |
> | [`#test`](#test-验证阶段-5) | §5 验证 | 依据清单生成权限预期用例，喂给 `test-mcp.sh` |
>
> 模板：`assets/templates/authz/`（各框架中间件）
> 生成脚本：`scripts/gen-authz.sh` · 测试脚本：`scripts/test-mcp.sh`（L3 层）

---

## 元数据声明

> 供主线 phases 读取（见 `modules/registry.md` §2.2），不需模型解析正文。

| 字段 | 值 |
|------|-----|
| `userLabel` | 🔐 API 鉴权 |
| `contributedTools` | —（中间件形态，不向 Bridge 贡献工具；授权在应用侧中间件完成） |
| `dependsOn` | —（独立于其他能力，但需应用入口可注入中间件） |
| `testScript` | 复用 `scripts/test-mcp.sh` L3 层（通过 `AUTHZ_MANIFEST` 触发；后续可独立为 `scripts/test-authz.sh`） |

---

## 设计总纲

### 概念区分（务必分清）

| 概念 | 是什么 | 在哪实现 | 出处 |
|------|--------|----------|------|
| **身份认证（authn）** | 「你是谁」——终端用户身份 | agent-server Gateway 解 OA → 注入 `X-Staff-Name`；Bridge 透传 | `modules/mcp.md` |
| **CLI 操作者身份** | 「谁在跑 /agent-boost」——agent owner | 鉴权平台 MCP 自动注入 `x-tai-identity` | `phases/0-context.md` §0.0 |
| **API 授权（authz）** | 「你能不能访问这个接口/数据」 | **用户应用内**的授权中间件 | **本文件** |

身份链路已端到端打通（见 `modules/mcp.md#principles`），本模块只补齐**最后一环：应用侧按身份做授权判断**。

### 三条实现原则

1. **全局数据驱动中间件**：在应用入口注入**一个**全局中间件，按 `method+path` 匹配授权清单里的规则做拦截。**不逐路由改代码**——加/改权限只改清单（JSON），零编码、易维护。
2. **单一事实源**：一份授权清单 `.agent/authz/api-authz.json`，被「中间件（运行期读）」和「MCP 测试（生成预期）」共同消费，保证逻辑一致、不漂移。
3. **不破坏原有逻辑**：应用已有自己的鉴权时，**默认不重复注入**，优先复用其判断函数（`source.type=custom`）；只对缺鉴权的接口补齐。

### 授权清单 schema（`.agent/authz/api-authz.json`）

```json
{
  "schemaVersion": 1,
  "framework": "express | fastapi | flask",
  "enforcement": "middleware | reuse-existing | none",
  "roleHierarchy": ["public", "user", "admin"],
  "roles": {
    "public": { "desc": "无需登录" },
    "user":   { "desc": "任意已登录员工", "match": "any-authenticated" },
    "admin":  { "desc": "管理员", "cacheTtlSeconds": 300,
                "source": { "type": "db", "orm": "sequelize", "model": "Employee",
                            "keyColumn": "staff_name", "roleColumn": "role",
                            "adminValues": ["admin","hr_admin"], "connectionRef": "reuse-app" } }
  },
  "apis": [
    { "method": "GET",  "path": "/api/dashboard",     "requiredRole": "user",  "reuse": true,  "authStatus": "existing" },
    { "method": "GET",  "path": "/api/employees/:id", "requiredRole": "user",  "reuse": false, "authStatus": "generated" },
    { "method": "POST", "path": "/api/config",        "requiredRole": "admin", "reuse": true,  "authStatus": "to-add" },
    { "method": "GET",  "path": "/api/health",        "requiredRole": "public" }
  ],
  "test": {
    "adminStaff": "zhangsan",
    "nonadminStaff": "agent-boost-probe-nonadmin",
    "cases": [
      { "method": "POST", "path": "/api/config", "as": "nonadmin", "expect": "deny" },
      { "method": "POST", "path": "/api/config", "as": "admin",    "expect": "allow-readonly-skip" }
    ]
  }
}
```

**字段语义**：
- `requiredRole`：`public`（放行）/ `user`（需已登录）/ `admin` 或任意自定义角色（需具备该角色）。
- `reuse`：该接口是复用现有的（true）还是本次新增的（false）。
- `authStatus`：`existing`（原本已有鉴权）/ `to-add`（原有接口但缺鉴权，需补）/ `generated`（本次新生成的接口，随附鉴权）。
- `roles.*.source`：名单来源，见下方 Role Source。
- `path`：支持 `:id` / `{id}` 路径参数占位，中间件转正则匹配。

### Role Source（名单来源，可插拔）

| type | 声明 | 适用 |
|------|------|------|
| `static` | `{"type":"static","members":["zhangsan","lisi"]}` | 无 DB / 小白手输 |
| `env` | `{"type":"env","var":"ADMIN_LIST"}` | 简单环境变量 |
| `db` | `{"type":"db","orm":"...","model/table":"...","keyColumn":"...","roleColumn":"...","adminValues":[...],"connectionRef":"reuse-app"}` | **应用用 DB 存名单** |
| `custom` | `{"type":"custom","module":"./auth/roles.js","fn":"isAdmin"}` | 应用已有判断函数 |

---

## #detect 分析阶段（§1）

在 §1 扫描能力矩阵的同时，附加输出「鉴权现状」，供 §2 生成建议默认值。扫描项：

**1. 应用是否已有鉴权？**
grep 模式（按框架）：
- 通用：`X-Staff-Name` / `x-staff-name` 的读取
- Express：`req.session`、`req.user`、`passport`、自定义 `authMiddleware` / `requireAuth`
- FastAPI：`Depends(` + `get_current_user` / `oauth2` / `HTTPBearer`
- Flask：`@login_required` / `flask_login` / `session[`
→ 命中则该应用「已有鉴权」，倾向 `enforcement=reuse-existing`。

**2. 是否已有管理员/角色名单？**（决定 Role Source 默认值，优先级即 Resolver 兜底优先级）
- 现成函数（**最优**）：grep `isAdmin` / `is_admin` / `getUserRole` / `get_role` / `checkPermission` → 建议 `source.type=custom`
- DB 名单：结合 §1 已识别的数据源，找 `admins` / `roles` / `permissions` 表或集合、`users.role` / `employees.role` 字段、以及 DB 连接/ORM 的**导出点**（`module.exports`、`sequelize.models`、`db.collection(...)`、SQLAlchemy `Base`/`Session`）→ 建议 `source.type=db`
- 配置/常量：`config/admin*.json`、env `ADMIN_LIST` / `ADMINS`、代码内常量数组 → 建议 `source.type=static` / `env`
- 都没有 → 建议新建 static 名单（§2 引导填写）

**3. 每个 API 的敏感度初判**（给 `requiredRole` 建议默认值）：
| 特征 | 建议 requiredRole |
|------|------------------|
| GET 且路径/含义为只读展示 | `user` |
| POST/PUT/DELETE/PATCH（写操作） | `admin` |
| 路径含 `config`/`admin`/`setting`/`user`/`salary`/`secret` 等敏感词 | `admin` |
| `health`/`ping`/静态资源 | `public` |

**4. 为每个 API 推断「功能名」**（供 §2 交互展示，避免向用户暴露 HTTP 方法+路径）：

推断优先级（从高到低，命中即用）：
| 来源 | 例子 |
|------|------|
| 路由上方的注释 | `/** 查询员工详情 */` → "查看员工详情" |
| 处理函数名 | `getEmployeeDetail` → "查看员工详情" |
| 路径语义 | `/api/dashboard` → "查看数据看板"；`/api/config` → "修改配置" |
| HTTP方法 + 路径推断 | GET → 前缀"查看"；POST/PUT/DELETE → 前缀"修改/删除" |
| 兜底 | `GET /api/xxx` → "查询数据(xxx)" |

> 功能名一律中文，动词开头，≤8 字。推断不确定时用路径最后一段的中文直译，不做创造性命名。

**输出**（并入能力矩阵，作为 §2 输入）：
```yaml
authz:
  existingAuth: true | false
  enforcementSuggest: middleware | reuse-existing
  roleSourceSuggest:
    type: db | custom | static | env
    # 以下字段按 type 提供（db: model/roleColumn/adminValues；custom: module/fn；static: members）
    label: "员工表的角色字段"        # 人类可读描述，供 §2 展示
    sampleAdmins: ["zhangsan","lisi"] # 检测到的样例管理员（最多 3 个），供 §2 增强可信度
  apiRoleSuggest:
    - { method: GET,  path: /api/dashboard, label: "查看数据看板", requiredRole: user }
    - { method: POST, path: /api/config,    label: "修改配置",     requiredRole: admin }
```

> `label` 和 `sampleAdmins` 是 §1 推断产出，专供 §2 交互展示用，不写入授权清单的 schema。授权清单仍以 `method`/`path` 为技术标识。

---

## #confirm 建议阶段（§2）

> 在 §2 用户确认 Skill 之后插入。**面向非技术用户**：用功能名 + 检测结果展示，不暴露 HTTP 方法/路径/DB 字段名。已按 §1 分析**预填建议默认值**，用户多为点选确认。

### 步骤 A · 助手需要的能力（复用 vs 新增）

对每个已选 Skill，将其数据需求映射到 §1 的现有 API，分为「已有 / 需新增」，用功能名展示：

```
🔧 助手需要以下能力：

  ✅ 已有：
     · 查看数据看板
     · 查看员工列表

  ➕ 需新增：
     · 查看员工详情（app-guide 需要单员工明细，当前应用无此功能）

需新增的能力我会自动生成对应代码，你无需编写。是否继续？(y/n)
```

> 技术映射（method/path）保留在内部清单，不向用户展示。功能名取自 §1 `#detect` 的 `apiRoleSuggest[].label`。

- 需新增的接口 → 记入清单 `reuse:false, authStatus:generated`，由 §3 `#inject` 的**新增 API 生成**环节自动产出可运行代码。
- 用户零编码（决策原则）。若某接口的数据映射不明确，生成**基于已识别数据源的最合理实现**并在报告中标注「建议复核」，绝不留给用户写。

### 步骤 B · 权限确认

> 分两步：B1 逐功能确认谁能用，B2 确认管理员来源。均用功能名 + 检测结果展示。

**B1｜逐功能确认谁能用**（`ask_followup_question`，可批量多选调整）：

```
🔐 助手能做的事，谁能用？（已按分析预填建议，可逐条调整）

  📊 查看数据看板        → 所有员工 ✓
  👤 查看员工详情        → 所有员工 ✓
  ⚙️ 修改配置            → 仅管理员 🔒

选项：
  1) 全部采用建议
  2) 我要逐条调整
```

> 角色映射（内部技术标识 ↔ 用户展示文案）：
> | 内部 requiredRole | 展示文案 | emoji |
> |------------------|---------|-------|
> | `public` | 所有人（含未登录） | 🌐 |
> | `user` | 所有员工 | ✓ |
> | `admin` | 仅管理员 | 🔒 |
>
> 逐条调整时，每条功能提供 3 选 1：所有员工 / 仅管理员 / 所有人。技术值在后台自动映射。

**B2｜确认谁是管理员**（仅当 B1 存在 `admin` 角色时问）：

> §1 `#detect` 已检测到名单来源，§2 直接展示检测结果 + 样例管理员，让用户确认而非理解技术。

```
🔐 谁是管理员？

  ✅ 已检测到：应用里已有管理员设置
     当前管理员：张三、李四

  1) 沿用应用里已有的管理员（推荐）
  2) 我来指定管理员工号
  3) 不区分管理员，所有员工权限相同
```

| 选项 | §1 检测到的来源 | 展示文案 | 用户操作 |
|------|----------------|----------|----------|
| **1) 沿用已有** | custom 函数 / DB 字段 / 配置 | "应用里已有的管理员" + 列出 `sampleAdmins` 样例 | 点确认（已预填） |
| **2) 我来指定** | — | 弹窗输入管理员工号（逗号分隔） | 手动输入 |
| **3) 不区分** | — | 所有接口降为 `user` | 点确认 |

> 选 1 时：内部按 `roleSourceSuggest.type` 落盘（custom/db/static/env），用户无感。
> 选 2 时：落盘为 `source.type=static` + 用户输入的 `members`。
> 选 3 时：清单中不产生 `admin` 角色，所有 `admin` 接口降为 `user`。

**产出**：将确认结果写成 `.agent/authz/api-authz.json`（schema 见上），作为 §3 与 §5 的唯一输入。

---

## #inject 创建阶段（§3）

> 在 §3 创建产物时执行，紧接 MCP Bridge 生成之后。分三件事：**① 生成新增 API 代码 → ② 生成授权中间件 + Role Resolver → ③ 注入应用入口**。
> **enforcement=reuse-existing 或 none**：跳过②③的中间件注入，仅确保清单落盘（供 §5 校验）并提示用户其现有鉴权需能识别 `X-Staff-Name`。

### ① 新增 API 自动生成（决策：不让用户写代码）

对清单中 `reuse:false` 的接口，按 §1 识别的框架 + 数据源，生成**可运行**的接口实现，追加到应用后端入口（或其路由模块）：
- 数据来源：复用应用已有的数据访问层（DB 连接 / model / 数据文件读取），**不新建连接**。
- 风格对齐：模仿应用现有路由的写法（响应结构、错误处理）。
- 新增接口的 `method`/`path`/`requiredRole` 已在 §2 confirm 阶段写入授权清单，§3.4 gen-bridge 渲染时据此合入 KNOWN_ENDPOINTS（见 `phases/3-create.md` §3.4），**无需 inject 后再更新 Bridge 文件**。
- 生成的接口天然被全局中间件覆盖（无需单独加鉴权）。

### ② 生成中间件 + Role Resolver

调用 `scripts/gen-authz.sh` 渲染框架模板（仿 `gen-bridge.sh`，纯文本替换 + 语法检查）：

| 框架 | 模板 | 生成到 | 注入点 |
|------|------|--------|--------|
| Express | `assets/templates/authz/express-agent-authz.js.template` | `{app}/middleware/agent-authz.js` | `app.use(require('./middleware/agent-authz')())` |
| FastAPI | `assets/templates/authz/fastapi_agent_authz.py.template` | `{app}/agent_authz.py` | `app.add_middleware(AgentAuthzMiddleware)` |
| Flask | `assets/templates/authz/flask_agent_authz.py.template` | `{app}/agent_authz.py` | `register_agent_authz(app)` |

中间件逻辑（模板内已固化，数据驱动）：
```
读 X-Staff-Name/X-Staff-Id → 按 method+path 匹配清单规则
  ├─ 无匹配规则        → 放行（默认不干预未声明的接口）
  ├─ requiredRole=public → 放行
  ├─ requiredRole=user   → staffName 非空则放行，否则 401
  └─ 其他角色            → resolveRole() 命中则放行，否则 403 {code:"forbidden", need:<role>}
```

**Role Resolver 注入**（`${ROLE_RESOLVER}` 占位符，仿 `${PROJECT_TOOLS}` 模式）：
- `static`/`env`：使用模板内置默认 resolver（读清单 members / 环境变量），**模型无需生成代码**。
- `db`/`custom`：模型按 §1 分析结果生成 resolver 片段，通过 `ROLE_RESOLVER` env 传给 `gen-authz.sh`。生成优先级（**三级兜底**）：
  1. **复用现成函数**（`custom`）：`require`/`import` 应用已有 `isAdmin/getUserRole`，包一层返回角色。最稳、侵入最小。
  2. **复用导出的 ORM/连接**（`db`）：`require`/`import` 应用导出的连接或模型，参数化查询 `keyColumn=staffName` 取 `roleColumn`，命中 `adminValues` 即为 admin。**带 TTL 缓存**（`cacheTtlSeconds`，默认 300s）避免每请求打库。
  3. **兜底同步为 static**：若连接点识别不确定，部署时一次性把 DB 名单查出写入清单 `members`，降级为 static，并提示「名单变动需重跑同步或改用方式 1/2」。功能一定可用。

> Resolver 一律**参数化查询防注入**；DB 不可达时 fail-safe：对 `admin` 判定返回 false（拒绝）并记日志，不因授权层故障放行越权。

### ③ boost-state.json 记录

§3.8 写 boost-state 时，authz 的详情直接内嵌在 `capabilities.authz` 下（不再单独设 `authz` 顶层字段）：
```json
"capabilities": {
  "authz": {
    "enabled": true,
    "configRef": ".agent/authz/api-authz.json",
    "enforcement": "middleware",
    "framework": "express",
    "roleSource": "db",
    "generatedApis": ["GET /api/employees/:id"]
  }
}
```

---

## #test 验证阶段（§5）

> 依据授权清单生成**权限预期用例**，交给 `scripts/test-mcp.sh` 的 L3 执行（测试执行细节见 `modules/mcp.md#test`）。本节只定义**用例如何从清单推导**。
>
> **报告路径**：当前 L3 结果写入核心报告 `.agent/mcp-test-report.json` 的 `l3` 段（历史路径，与 L1/L2 合并）。后续可独立为 `scripts/test-authz.sh` 并迁移到 `.agent/authz/test-report.json`（见 `modules/registry.md` §7.2）。

**用例生成规则**（写入清单 `test.cases`，`test-mcp.sh` 读取）：
- 对每个 `requiredRole=admin`（或自定义受限角色）的接口：
  - `{as:"nonadmin", expect:"deny"}` —— 用不在名单的合成假名调用，期望 403（**任何方法都安全**：被拒不产生副作用）。
  - 若为只读（GET）：`{as:"admin", expect:"allow"}` —— 用 admin 样例调用，期望成功。
  - 若为写操作（POST/PUT/DELETE）：`{as:"admin", expect:"allow-readonly-skip"}` —— **不实际执行**，仅记录「已具备权限，跳过破坏性验证」。
- 对 `requiredRole=user` 的只读接口：`{as:"nonadmin", expect:"allow"}`（合成名视为已登录用户，验证登录用户可访问）。
- `public` 接口不生成权限用例（L2 已覆盖可调用性）。

**测试身份来源**：
- `adminStaff`：DB/名单里的一个真实管理员样例（`source=db` 时查一条；`static` 时取 members[0]；取不到则询问用户给一个样例工号）。
- `nonadminStaff`：合成假名 `agent-boost-probe-nonadmin`（确保不在任何名单/DB 中）。

**结果回流**：L3 不符预期时的定位与修复见 `modules/mcp.md#test` 的「结果判定与优化闭环」表。
