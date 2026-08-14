# 项目分析指引

> Plugin 阶段一「分析」时的扫描规则。目标：用最少的 token 推断出 `appType`、API 列表、数据源类型，写入能力矩阵。

---

## 一、扫描原则

1. **优先级排序读文件**，每个文件**最多读 200 行**，必要时只读头部
2. **grep 优先于 read**：找特定模式先用 grep
3. **先确定 appType**，再针对性深挖
4. **跨语言通用**：不假设是 Node.js，也支持 Python / Go

---

## 二、文件扫描优先级

| 优先级 | 文件 | 用途 |
| --- | --- | --- |
| 1 | `package.json` / `pyproject.toml` / `go.mod` / `requirements.txt` | 技术栈 + 框架识别 |
| 2 | `.deploy-state.json` | projectId / gateway URL（page-deliver 部署元数据） |
| 3 | `server.js` / `app.js` / `main.py` / `app.py` / `index.ts` / `main.go` | 后端入口 |
| 4 | `public/index.html` 或 `index.html` | 前端功能识别 |
| 5 | `.mcp.json` | 已存在的 MCP 配置（合并到能力矩阵） |
| 6 | `README.md` 头部 50 行 | 项目自述 |
| 7 | `docs/` 任意一份 | 补充信息（按需） |

---

## 三、appType 判定规则

**按以下顺序判定**，先命中先生效：

| 条件 | appType |
| --- | --- |
| 入口代码有图表渲染（`echarts` / `chart.js`），且至少 1 个 `/api/*` GET | `dashboard` |
| 入口代码有 GET + POST/PUT/DELETE 混合的 `/api/*` 路由 | `crud` |
| 入口代码只有 GET `/api/*`，无写入 | `api-readonly` |
| 没有 server 入口文件，仅 `public/` 或根目录 `index.html` | `static` |
| 其他 | `unknown` |

> 数仓应用（含 `queryDW` / `batchQueryDW` / `SELECT ... FROM catalog_`）由 DW 能力模块独立检测（见下方「§十二 数仓 SQL 检测」），不在内置 appType 体系中。

---

## 四、API 路由提取

### Node.js / Express / Koa / Fastify

正则：

```regex
^\s*(?:app|router|fastify)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]
```

### Python / FastAPI

正则：

```regex
^\s*@\w+\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]
```

### Python / Flask

正则：

```regex
@app\.route\s*\(\s*['"]([^'"]+)['"](?:[^)]*methods\s*=\s*\[([^\]]+)\])?
```

### Go / net/http / gin

正则：

```regex
(?:Handle|HandleFunc|GET|POST|PUT|DELETE|PATCH)\s*\(\s*['"`]([^'"`]+)['"`]
```

**记录格式（写入 KNOWN_ENDPOINTS）：**

```json
{
  "method": "GET",
  "path": "/api/items",
  "summary": "推断的描述（从注释/路由名/函数名推断）",
  "params": [
    {"name": "limit", "in": "query", "type": "integer"}
  ]
}
```

---

## 五、数据源识别

### Mongo

grep 模式：`MongoClient` / `mongoose\.` / `mongodb://` / `MONGO_URI`

提取：

- collection 名（`db\.collection\(['"](\w+)['"]\)`）
- 数据库名（环境变量 / 连接字符串）

### MySQL / Postgres

grep 模式：`mysql\.|mysql2|sequelize|pg|pymysql|psycopg|postgres://`

提取：

- 表名（`FROM\s+(\w+)` / `INSERT\s+INTO\s+(\w+)` / `JOIN\s+(\w+)`）

### SQLite / 本地文件

grep 模式：`sqlite|better-sqlite3|fs\.readFileSync.*\.json`

提取：

- 数据文件路径（`data/.*\.json`、`*.db`）

### Redis / KV

grep 模式：`createClient|ioredis|REDIS_URL`

→ 通常作为缓存，**不计入主数据源**

### 无数据源

如果以上都不命中，标记 `kind: none`，应用是纯展示型或纯路由代理。

---

## 六、前端功能识别

读 `public/index.html` 或根目录 `index.html`（最多 200 行）。

| 模式 | 功能 |
| --- | --- |
| `<form>` / `<t-form>` / `el-form` | hasForms |
| `echarts` / `chart\.js` / `<canvas>` 含 ECharts 类语法 | hasCharts |
| `<table>` / `<t-table>` / `el-table` | hasTables |
| `<select>` / `<input type="date">` / `<t-select>` | hasFilters |
| `<button.*@click=` / `onclick=` | hasActions |
| `fetch\(` / `axios\.` | doesAjax |

---

## 七、技术栈识别

| 文件 | 推断 |
| --- | --- |
| `package.json` 含 `express` | Node + Express |
| `package.json` 含 `next` | Next.js |
| `package.json` 含 `nest` | NestJS |
| `pyproject.toml` 含 `fastapi` | Python + FastAPI |
| `requirements.txt` 含 `flask` | Python + Flask |
| `go.mod` 含 `gin-gonic` | Go + Gin |
| 仅 HTML/CSS/JS 静态文件 | static |

---

## 八、部署信息提取

### page-deliver 部署的项目

读 `.deploy-state.json`：

```json
{
  "projectId": "project-xxx",
  "projectName": "...",
  "platform": "anydev",
  "gateway": {
    "url": "https://gateway.xxx.com/project-xxx"
  }
}
```

→ 用 `projectId` 作为 Agent 的 `projectId`，用 `gateway.url` 作为 MCP Bridge 的外部访问 URL。

### 非 page-deliver 项目

- `projectId` 用目录名 + 时间戳（`<dir>-<yyyymmdd>`）
- `gateway.url` 留空（用户使用本机访问 MCP Bridge）

---

## 九、端口推断

按以下顺序找端口：

1. 入口代码中 `process.env.PORT || <num>` / `os.getenv("PORT", <num>)`
2. `package.json` scripts 里的 `--port <num>`
3. README 中的端口信息
4. 默认值（按框架）：Express/Koa = 3000，FastAPI = 8000，Flask = 5000，Next = 3000

→ 写入能力矩阵的 `backend.port` 字段。

MCP Bridge 端口起始 `8932`（避开常见占用），运行时由 `mcp_bridge.py` 的 `_find_free_port()` 自动探测第一个空闲端口并写入 `.bridge-port`；可通过 `BRIDGE_PORT` 环境变量覆盖起始探测点。

---

## 十、能力矩阵输出（最终）

```yaml
projectId: employee-dashboard-20260608-004200
projectName: 员工数据看板
projectPath: /data/.../employee-dashboard-20260608-004200
appType: dashboard
backend:
  framework: express
  port: 3456
apis:
  - { method: GET, path: /api/health, summary: 健康检查 }
  - { method: GET, path: /api/dashboard, summary: 查询看板数据 }
dataSources:
  - { kind: json-file, detail: { path: data/dashboard.json } }
frontend:
  hasForms: false
  hasCharts: true
  hasTables: true
  hasFilters: true
existingMcp: []
gateway:
  url: null
deploy:
  platform: page-deliver
  state: in_progress
```

→ 这个对象作为阶段二「建议」的输入。

---

## 十一、扫描注意事项

1. **不要全文读 server.js**（可能很大），只读路由定义部分
2. **不要解析复杂的动态路由**（如 `app.use('/admin', adminRouter)` 嵌套），抓不到就标记 unknown
3. **不要假设有 OpenAPI**，但如果发现 `swagger.json` / `openapi.yaml` 优先用它
4. **所有 grep 都加 `--include` 限制扩展名**，避免扫到 node_modules/.git
5. **找不到信息时大方承认**，不编造

---

## 十二、数仓 SQL 检测

> 供 dw-qa 能力模块 `#detect` 锚点使用。检测到 SQL 时触发「数仓问数」能力推荐。

### 检测信号

在扫描 `public/index.html`（或根目录 `index.html`）及 `src/**/*.js` / `src/**/*.ts` / `src/**/*.vue` 时，grep 以下模式（命中任一即 `dw-qa.detected = true`）：

| # | grep 模式 | 说明 |
|---|----------|------|
| 1 | `queryDW\(\|batchQueryDW\(\|cachedQueryDW\(` | 数仓查询函数调用 |
| 2 | `` `SELECT\s+.*\s+FROM\s+ `` | 模板字符串中的 SQL |
| 3 | `const\s+T_[A-Z_]+\s*=\s*['"]catalog_` | 表常量定义 |
| 4 | `dos-dataview-mcp\|/api/query` | 数仓 API 端点 |
| 5 | `SELECT\s+.*\s+FROM\s+catalog_` | 直接含 catalog 前缀的 SQL |

### 提取信息

检测命中后，附加提取以下信息供 §2 展示：

```yaml
dw-qa:
  detected: true
  sqlCount: <grep 命中的 SQL 数量>
  files: [<含 SQL 的文件列表>]
  tables: [<从 const T_XXX 提取的表常量>]
  queryFunctions: <检测到的查询函数名>
  # 应用结构（基础层 — 必出）
  appTitle: <应用标题，从 <title> 或导航标题提取>
  templateType: <page-deliver 模板类型，如 dw-readonly / dw-crud（如可识别）>
  features:                     # 功能模块（Tab/视图级别）
    - name: <模块名>
      loadFunctions: [<该模块的加载函数名列表>]
  # 应用结构（增强层 — 尽量出，识别不到不阻塞）
  featureDetails:
    - { name: <模块名>, filters: [<筛选条件>], display: <展示方式> }
  suggestLabel: "📊 数仓问数"
```

> 详细 detect/inject 逻辑见 `modules/dw-qa.md`。
