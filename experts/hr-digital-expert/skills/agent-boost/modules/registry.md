# 能力注册表（Capability Registry）

> §1 分析后、§2 确认前加载本文件，按其中的能力逐个调用 `#detect` 锚点。
> §3 / §5 同理按本表调用已启用能力的 `#inject` / `#test`。
> **新增能力 = 新建 `modules/{name}.md` + 本表加一行**，主线 phases 无需改动。

---

## 一、能力分层

| 层 | 何时启用 | 例子 |
|----|---------|------|
| **核心层（always-on）** | 所有应用，不可关闭 | 项目分析、MCP Bridge、agent.md、skills、chat-widget、注册部署 |
| **可选能力层（capability modules）** | §1 `#detect` 命中 + §2 用户确认 | authz |

> 核心层的主线编排见各 `phases/*.md`；本表只管「可选能力层」。
> MCP Bridge 属核心层（`modules/mcp.md`），不在此注册，因为它始终启用、不可关闭。
> 外部集成（企微/飞书等）不在本注册表——它们由 agent-server 管理面板在 agent 创建后独立绑定，与 agent-boost 创建主线解耦。

---

## 二、能力模块契约

每个可选能力模块文件（`modules/{name}.md`）按统一契约暴露**锚点**+ 声明**元数据**：

### 2.1 锚点（lifecycle hooks）

| 锚点 | 被调用阶段 | 职责 | 产出 |
|------|-----------|------|------|
| `#detect` | §1 分析 | 扫描应用，判断是否需要本能力 + 给出建议默认值 | `capabilitySuggestion.{name}` 段并入能力矩阵 |
| `#confirm` | §2 建议 | 弹窗询问用户配置，持久化能力配置文件 | `.agent/{name}/config.json`（或模块自定义路径） |
| `#inject` | §3 创建 | 生成代码产物（Bridge 工具片段 / 中间件 / 配置），注入 `${PROJECT_TOOLS}` 或独立产物 | 产物文件 + `PROJECT_TOOLS` 片段 |
| `#test` | §5 验证 | 生成测试用例 + 执行验证 | 测试报告 `.agent/{name}/test-report.json` |

> 锚点可省略（某能力不需要某阶段时省略对应锚点）。
> **能力间正交**：一个应用可同时启用多个能力，互不干扰，各自独立 detect/confirm/inject/test。

### 2.2 元数据声明（module 文件头部）

每个 module 文件在头部声明 `userLabel`（功能化名称，§2 展示用，不带内部标识），供主线 phases 读取。

> 主线展示能力时一律用 `userLabel`，不暴露 `name`。

---

## 三、已注册能力

### 能力清单

| 能力 | userLabel | 模块文件 | dependsOn | 默认推荐时机 |
|------|-----------|---------|-----------|-------------|
| authz | 🔐 API 鉴权 | [`modules/authz.md`](./authz.md) | — | 有写接口 / 敏感路径时推荐 |
| dw-qa | 📊 数仓问数 | [`modules/dw-qa.md`](./dw-qa.md) | — | 前端代码含 SQL 查询时推荐 |

### 锚点覆盖矩阵

| 能力 | #detect | #confirm | #inject | #test | contributedTools | testScript |
|------|:-------:|:-------:|:-------:|:-----:|------------------|-----------|
| authz | ✅ | ✅ | ✅ | ✅ | —（中间件，不贡献工具） | 复用 `scripts/test-mcp.sh` L3 |
| dw-qa | ✅ | ✅ | ✅ | ✅ | —（生成 Skill 文件，不贡献工具） | 模型自行验证 |

> 后续新增能力在此两表追加一行，并补全元数据声明。

---

## 四、主线 Hook 点

主线 phase 文件中以下标记为能力 hook 调用点。模型按本注册表，**只调用「已启用」能力的对应锚点**——主线不感知具体能力名：

| Hook 点 | 所在文件 | 调用锚点 | 说明 |
|---------|---------|----------|------|
| `【CAPABILITY HOOK · detect】` | `phases/1-analyze.md` | `#detect` | 遍历注册表每个能力调 detect，收集建议 |
| `【能力启用确认】` | `phases/2-suggest.md` | — | 汇总 detect 建议，按 `userLabel` 弹窗让用户选启用哪些 |
| `【CAPABILITY HOOK · confirm】` | `phases/2-suggest.md` | `#confirm` | 对每个已启用能力调 confirm，收集配置 |
| `【CAPABILITY HOOK · inject】` | `phases/3-create.md` | `#inject` | 对每个已启用能力调 inject（前置校验 `dependsOn`），贡献 `PROJECT_TOOLS` + 独立产物 |
| `【CAPABILITY HOOK · test】` | `phases/5-verify.md` | `#test` | 对每个已启用能力调 test，追加独立测试报告 |

> Hook 点的执行顺序：按注册表「已注册能力」表的行顺序。
> 未启用的能力，其所有锚点一律跳过——主线不会加载对应模块文件。
> **主线 phase 文件中不应硬编码任何能力名（authz 等）**，所有能力信息通过本注册表读取。

---

## 五、能力状态承载

能力启用状态写入 `boost-state.json` 的 `capabilities` 字段（唯一事实源）：

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

- `enabled`：是否启用该能力（决定 §2-§5 是否调用其锚点）。
- `configRef`：该能力配置文件的相对路径（供路线 B 快速模式直接读取，不重新 detect/confirm）。
- 其余字段：各能力自定义详情（如 authz 的 enforcement/framework/roleSource/generatedApis），直接内嵌在对应能力条目下。
- 重新跑 `/agent-boost`（路线 B）时，模型读此字段判断哪些能力的 hook 需要执行。

> 能力段为**动态生成**：按本次实际启用的能力写入，不预设固定字段。

---

## 六、新增能力指引

1. 新建 `modules/{name}.md`，按契约实现需要的锚点（detect/confirm/inject/test，可省略不需要的）
2. 在 module 文件头部声明 `userLabel`
3. 在本注册表「已注册能力」两个表各加一行
4. 按需在 `assets/templates/{name}/` 放模板，`scripts/` 加生成脚本 + 独立 test 脚本
5. **不改任何 phase 文件** —— 主线 hook 点已通用化
6. 能力配置统一持久化到 `.agent/{name}/` 目录，并在 `boost-state.json` 的 `capabilities.{name}` 段声明 `enabled` 与 `configRef`
7. test 报告独立落到 `.agent/{name}/test-report.json`

> 能力的 `#inject` 若需向 MCP Bridge 贡献工具，统一通过 `PROJECT_TOOLS` 环境变量追加片段（见 `modules/mcp.md#gen`）。

---

## 七、能力 test 机制

- **核心 L1+L2**：`scripts/test-mcp.sh`（所有应用必跑），报告 `.agent/mcp-test-report.json`
- **能力 L3**：各能力 `#test` 锚点 + 独立 test 脚本，报告 `.agent/{name}/test-report.json`
- **门禁汇总**：`gate = mcp.gate AND 所有能力 gate`，任一层失败即 gate=false
