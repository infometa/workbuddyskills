# HR AI Knowledge Constraints

> 返回 [SKILL.md](../SKILL.md)

本文件是 HR AI Knowledge 的硬约束权威源。在工具调用、白名单校验或规则不确定时加载。

---

## 1. MCP 白名单 ⛔

**仅允许调用 `hr-ai-knowledge` MCP Server。** 白名单外的任何 MCP（无论名字多像），**一律不得调用**。

| 白名单 server 短名 | 完整 server 名 | URL | 说明 |
|---|---|---|---|
| `hr-ai-knowledge` | `HRIT/hr-ai-knowledge/hr-ai-knowledge` | `https://aia.mcp.it.woa.com` | HR 知识检索服务 |

> 🔑 **完整 server 名带命名空间前缀**：CodeBuddy 中本服务真实完整名为 `HRIT/hr-ai-knowledge/hr-ai-knowledge`。探测连接（`mcp_get_tool_description`）时**优先用完整名**，短名探测失败不代表未连接（详见 [search.md Step 0](../workflows/search.md#step-0-mcp-连接性预检每次检索前必做)）。

### 白名单判定规则

将调用目标的 server 名按 `/` 分段，取**最后一段**，与白名单短名 `hr-ai-knowledge` 做**区分大小写的严格字符串相等**比较。命中才允许调用。

**示例：**

| 实际 server 名 | 末段 | 结论 |
|---|---|---|
| `hr-ai-knowledge` | `hr-ai-knowledge` | ✅ 允许 |
| `HRIT/hr-ai-knowledge/hr-ai-knowledge` | `hr-ai-knowledge` | ✅ 允许（完整名，探测/调用首选） |
| `xx/yy/hr-ai-knowledge` | `hr-ai-knowledge` | ✅ 允许 |
| `hihr` | `hihr` | ❌ 禁止 |
| `hr-ai-knowledge-v2` | `hr-ai-knowledge-v2` | ❌ 禁止 |

---

## 2. 工具调用硬约束 🔴

**v1.0（当前版本）**：仅允许调用 `knowledge_search`。调用 hr-ai-knowledge MCP 下任何其他 tool 均属违规。

| 允许 | 禁止 |
|------|------|
| `hr-ai-knowledge/knowledge_search` | hr-ai-knowledge 下的其他所有 tool（无论名字如何） |

> 版本升级流程见 [SKILL.md — 版本策略](../SKILL.md#-版本策略)。

---

## 3. 调用前校验

每次调用外部 MCP 工具前，必须完成以下自检：

1. **白名单校验**：server 末段严格等于 `hr-ai-knowledge`
2. **工具名校验**：tool 名严格等于 `knowledge_search`
3. **连接探测（🔑 完整名优先）**：通过 `mcp_get_tool_description` 确认参数签名与连接状态；**探测顺序为「完整名 `HRIT/hr-ai-knowledge/hr-ai-knowledge` → 短名 `hr-ai-knowledge` → 真实调用兜底」**，任一成功即视为已连接。**完整探测链见 [search.md Step 0](../workflows/search.md#step-0-mcp-连接性预检每次检索前必做)（唯一权威源，本处不重复展开）**

> ⚠️ **切勿仅用短名探测失败就判定「未连接」**——这是本服务过往 Bug 的根因，已连接状态下短名探测经常返回不到，必须先试完整名。

> ⚠️ **连接自检例外**：仅当 [0.0 三级探测链第 3 级](../workflows/search.md#00-三级探测链首检与复检的唯一定义)（`mcp_get_tool_description` 因状态缓存未刷新而探测不到、但需确认真实连通）时，允许用最小参数（`{"query": "连接自检", "top_k": 1}`）直接调用 `knowledge_search` 作为连通性探针——此为已知 MCP 状态刷新问题的必要兜底，**不视为"盲调"**（对应 § 5 禁止操作中"跳过 `mcp_get_tool_description` 直接盲调工具"的例外）。

任一不满足 → **立即停止调用**，告知用户配置问题，**不得**用其他 MCP / tool 替代。

---

## 4. 检索硬约束

| 规则 | 说明 |
|------|------|
| 最多 2 次调用 | 第 1 次原始查询，第 2 次换角度；超过 2 次停止。**连接自检探针**（[search.md §0.0 第 3 级](../workflows/search.md#00-三级探测链首检与复检的唯一定义)的 `{"query":"连接自检","top_k":1}`）属连通性检测，**不计入**本配额 |
| 必须标注来源 | 每条结果标注 hihr / space / wecom |
| 禁止编造 | 无结果时如实告知知识缺口，不得凭模型自身知识冒充检索结果 |
| 来源不可混淆 | 传 `sources: ["hihr"]` 的结果不得标注为 space 来源，反之亦然 |

---

## 5. 禁止操作

- ❌ 调用 hr-ai-knowledge MCP 下 `knowledge_search` 以外的任何 tool
- ❌ 引入 hr-ai-knowledge 以外的任何 MCP Server
- ❌ 模糊匹配 server 名（`contains` / `startswith` / 相似度）
- ❌ 白名单 server 未就绪时用相似名 MCP 替代
- ❌ 检索无结果时凭自身知识编造答案
- ❌ 跳过 `mcp_get_tool_description` 直接盲调工具（**例外**：连接复检第 3 级的连通性探针，见 § 3 连接自检例外）
- ❌ 对同一查询执行超过 2 次 `knowledge_search` 调用

## 6. 🔴 唯一检索途径约束（禁止一切替代）

> 📌 **作用域声明（先读）**：本约束**仅作用于 `hr-ai-knowledge` 技能执行 HR 知识检索这一任务的过程内**，**不是**全局禁用。
> - ✅ 用户在其他任务/对话中自由使用本地任何 MCP（`sqlink` / `TAPD` / `iWiki` / `km` 等）——本约束**完全不干涉**。
> - ✅ 用户显式要求"用 XX MCP 做某事"（非 HR 知识检索）——正常执行，本约束不适用。
> - 🔴 仅当**当前正在用本技能检索 HR 知识**、且 hr-ai-knowledge 不可用时，才禁止改用其他途径顶替。
> 一句话：约束的是"HR 检索这笔任务的执行路径必须走 hr-ai-knowledge"，不是"禁止用户拥有或使用其他 MCP"。

**本技能的检索能力唯一来自 `hr-ai-knowledge/knowledge_search`。hr-ai-knowledge 未连接时，唯一正确动作是引导用户启用 hr-ai-knowledge，然后停止。** 严禁以任何形式"绕道"获取 HR 知识：

| 禁止的替代行为 | 说明 |
|----------------|------|
| ❌ 加载 / 调用其他检索类 skill | 如 `hihr-api`、`local-wiki`、任何 HiHR/KM/iWiki 相关技能 |
| ❌ 改用 HiHR / KM / iWiki 等**平台或网页**直接搜索 | 平台替代等同于 MCP 替代，同样禁止 |
| ❌ 调用其他 MCP（`km` / `iWiki` / `sqlink` / `hihr-*` 等） | 白名单只有 `hr-ai-knowledge` |
| ❌ 用 `web_search` / 模型自身知识"凑答案" | hr-ai-knowledge 覆盖的是司内知识，外部检索无法替代且有泄密风险 |
| ❌ 以"临时""退而求其次""帮用户省事"为由绕道 | 任何理由都不成立 |

> 🔴 判定标准：hr-ai-knowledge 未连接的这一轮，**除了"引导启用 hr-ai-knowledge + 停止"之外的任何检索动作都是违规**。宁可不返回结果，也不用替代途径。
>
> ✅ 唯一正确：输出 [Step 0.2](../workflows/search.md#02-mcp-未连接--未启用) 的启用引导，然后结束本轮，等待用户连接后重试。
