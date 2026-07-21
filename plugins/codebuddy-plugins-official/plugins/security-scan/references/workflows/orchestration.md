# 共享编排步骤

> 引用方：commands/project.md、commands/diff.md

---

## 1. 条件规则加载

### 1.1 产品形态分析（探索阶段 1.2 完成后执行）

在技术栈识别完成后，由当前 Agent 直接分析产品形态，**禁止**调用 `scripts/agent_classifier.py detect` 或 `orchestration_helper.py detect-project-type` 做判定。分析必须基于真实文件证据，而不是脚本评分、依赖名猜测或历史缓存。

返回并记录 `project_type` / `product_shape` 与 `project_type_code`：

| product_shape | project_type_code | 判定条件 | 审计策略 |
|-------------|---------|---------|---------|
| `客户端` | `client` | 有终端客户端入口或 Manifest，并能指向端侧启动/运行代码 | 客户端配置、WebView/IPC/导出组件、证书校验、接口鉴权链路审计 |
| `AI agent` | `ai_agent` | 同时有 LLM/模型调用能力与工具执行/注册/任务编排/记忆/RAG/MCP 等 Agent 行为证据 | 追加 AI Agent 安全问答集 |
| `web` | `web` | 有 HTTP/Web 入口、路由、Controller、前端页面或全栈框架入口 | 标准 Web / 接口 / 业务逻辑审计 |
| `数据库` | `database` | 仓库本身实现数据库/存储引擎/查询执行/SQL 解析/数据库代理/迁移管控等数据库产品能力 | 聚焦查询解析、权限边界、存储访问、管理接口与注入链路 |
| `未知` | `unknown` | 证据不足、证据冲突或无法判断主形态 | 走通用安全审计，不因形态加载专属问答集 |

`product_shape_evidence_chain.evidence[]` 必须包含真实 `path`、`line` 或 `lines`、`snippet`、`reason`。证据不足时不要强行归类，输出 `未知` 并说明缺失证据。

**Agent 维度条件触发传递**：编排器在启动 Deep 模式 Agent 时，将 `project_type_code`、`product_shape` 和 `product_shape_evidence_chain` 传入 Agent prompt，Agent 按策略决定执行的维度。

### 1.2 框架知识加载

按技术栈加载框架安全知识（未检测到的不加载）：

| 触发条件 | 知识文件 |
|--------|---------|
| Java + Spring | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/spring-security.yaml` |
| Java + Spring Actuator | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/actuator-exposure.yaml` |
| Java + MyBatis | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/mybatis-injection.yaml` |
| Python + Flask/Django/FastAPI | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/python-web.yaml` |
| Node.js + Express/Koa/NestJS | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/nodejs-web.yaml` |
| Go + Gin/Echo/Fiber | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/go-web.yaml` |
| 存在认证/鉴权入口 | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/authentication-bypass.yaml` |
| hasPaymentLogic = true | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/payment-logic-rules.yaml` |
| Java 技术栈 | `${CODEBUDDY_PLUGIN_ROOT}/resource/knowledge/ghost-bits-truncation.yaml` |

知识文件路径记录到 `stage1-context.json > frameworkKnowledge[]`。Agent 按需 Read 相关章节。

**推理优先原则**：知识文件是参考资料，Agent 分析能力不受限于知识文件中列出的风险类型。

---

## 2. 漏洞链检测

合并后分析 `merged-scan.json` 中的跨文件漏洞链：
- 识别多文件攻击路径
- 将同一路径的发现关联为 `vulnerabilityChain` 条目，提升严重级别

---

## 3. WebSearch 情报增强（条件执行）

跳过条件：无 `webSearchCandidate: true` 的 CVE 条目且无 `auditDimension: "C7.7"` 的条目。

**场景一：CVE 实时验证（最多 3 次 WebSearch）**

触发条件：CVE 推理产出为 `severity: "critical"` 或组件主版本落后 >=3。

```
WebSearch: "{component} {version} CVE vulnerability security advisory"
```

结果处理：
- 命中已知 CVE 且版本匹配 -> 提升 severity，补充 CVE 编号
- 发现新 CVE -> 新建 finding，`source: "websearch_validated"`
- 无结果 -> 保持原始推理结果

**场景二：0day 情报感知（最多 2 次 WebSearch）**

触发条件：red-team 在 Q1（自造轮子）发现自定义序列化/加密/过时认证方案。

```
WebSearch: "{framework/library} {version} 0day exploit vulnerability 2025 2026"
```

结果处理：
- 发现相关漏洞 -> 升级 severity，补充 `threatIntelligence` 字段
- 发现在野利用 -> 升级到 `critical`，设置 `activeExploitation: true`
- 无情报 -> 保持 `severity: "info"` + `humanReviewRequired: true`

**预算控制**：合计最多 5 次 WebSearch。优先级：critical CVE > 活跃利用信号 > 高风险组件 > high CVE > C7.7 查询。

**降级策略**：WebSearch 工具不可用或达到配额时，跳过增强，使用纯静态分析。

---

## 4. 覆盖率评估（条件执行）

跳过条件（满足任一）：
- `totalFindings >= 10`
- `fileCount <= 50`
- 扫描 Agent 均为 `status: "completed"` 且 `totalFindings >= 5`

覆盖率维度：C1 注入类 / C2 凭证 / C3 认证授权 / C4 配置 / C5 文件操作 / C6 SSRF/反序列化 / C7 业务逻辑 / C8 依赖 / C9 云安全 / C10 加密

---

## 5. 跨仓库分析（条件执行）

当 `crossRepoDependencies` 非空且含高/严重级别时触发。
通过 AskUserQuestion 获取用户确认后，浅克隆到 `.tmp-cross-repo/` 分析，完成后清理。
