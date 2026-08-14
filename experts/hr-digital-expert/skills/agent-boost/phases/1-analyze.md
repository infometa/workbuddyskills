# 阶段1 · 分析（Analyze）

> **目标**：扫描项目，输出结构化能力矩阵。
> **约束**：每个文件最多读 200 行，grep 优先于全文读。详细规则见 `references/analysis-guide.md`。

---

## 1.1 解析项目路径

- `/agent-boost [path]` → 用 path
- 否则用当前工作目录

---

## 1.2 读取关键文件

按重要性优先级，**控制读取量**（每个文件最多 200 行）：

| 文件 | 用途 |
|---|---|
| `package.json` / `pyproject.toml` / `requirements.txt` | 技术栈 |
| `server.js` / `app.js` / `main.py` / `app.py` / `index.ts` | 后端入口、API 路由 |
| `public/index.html` 或 `index.html` | 前端功能（表单/图表/表格…） |
| `.deploy-state.json` | page-deliver 部署元数据（projectId / gateway URL） |
| `.mcp.json` | 已存在的 MCP 配置 |
| `README.md` 头部 | 项目自述 |

---

## 1.3 输出核心能力矩阵

```yaml
projectId: <从 .deploy-state.json 取，否则用目录名>
projectName: <推断>
projectPath: <绝对路径>
appType: static | api-readonly | crud | dashboard
backend:
  framework: express | fastapi | flask | next | nest | unknown
  port: <识别到的 PORT，否则 3000/3456/8000…>
apis:
  - method: GET
    path: /api/items
    summary: 获取数据列表
dataSources:
  - kind: mongodb | sqlite | json-file | none
    detail: { ... }
frontend:
  hasForms: true
  hasCharts: true
  hasTables: true
existingMcp:
  - name: ...
    url: ...
gateway:
  url: <可选，外部访问地址>
capabilities:       # 能力 detect 结果（见 §1.4 CAPABILITY HOOK）
  # 动态段：按 modules/registry.md 已注册能力表，对每个能力调 #detect 锚点
  # 命中的能力写入对应段（结构见各 modules/{name}.md#detect），未命中的不出现
  # 示例（实际段名/结构由各能力模块定义，本文件不硬编码）：
  #   {能力名}:
  #     recommend: true | false
  #     ...（各能力自定义字段）
```

---

## 1.4 【CAPABILITY HOOK · detect】

> 核心能力矩阵产出后，加载 `modules/registry.md`，对注册表中每个可选能力调用其 `#detect` 锚点，收集能力建议，合并到能力矩阵的 `capabilities` 段。

**执行方式**：
1. 加载 `modules/registry.md`，读取「已注册能力」表（§3.1 能力清单）
2. 对表中的每个能力，加载对应 `modules/{name}.md`，执行其 `#detect` 锚点（传入核心矩阵：appType / apis / dataSources）
3. 收集各能力的 `capabilitySuggestion`，合并到能力矩阵的 `capabilities.{name}` 段
4. detect 未命中（不需要该能力）的能力，不出现在 `capabilities` 段

> 主线不硬编码任何能力名——所有能力从注册表读取，新增能力后本步骤自动覆盖，无需改 phase 文件。
> 各能力的 detect 产出结构见对应 `modules/{name}.md#detect`。

---

## 1.5 向用户展示

简洁概览（< 12 行）：

```
🔎 项目分析结果

类型：dashboard
技术栈：Express + ECharts
API 数：5 个（/api/health /api/dashboard /api/agent/invoke …）
数据源：本地 JSON
前端：图表 ✓  表格 ✓  表单 ✗
部署：localhost:3456

是否继续推荐 Agent？(y/n)
```
