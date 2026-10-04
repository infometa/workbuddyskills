---
name: biobuddy
display_name: BioBuddy 生物医药研究助手
display_name_en: BioBuddy Biomedical Research Assistant
description: 当用户提出生物医药研究类需求时使用——抗体/多肽/酶设计、分子结构预测、病理质控、基因突变预测、虚拟空间转录组、疾病靶点发现与评估、单细胞与扰动分析、蛋白质检索、文献情报、专利检索、变异注释。本 Skill 指导模型通过 BioBuddy 统一 Gateway 发现并正确调用各专业 MCP 工具，含长任务处理与结果解读规范。不收集任何凭证，不适用于与生物医药无关的通用任务。
description_zh: 当用户提出生物医药研究类需求时使用——抗体/多肽/酶设计、分子结构预测、病理质控、基因突变预测、虚拟空间转录组、疾病靶点发现与评估、单细胞与扰动分析、蛋白质检索、文献情报、专利检索、变异注释。本 Skill 指导模型通过 BioBuddy 统一 Gateway 发现并正确调用各专业 MCP 工具，含长任务处理与结果解读规范。不收集任何凭证，不适用于与生物医药无关的通用任务。
description_en: Use when the user raises biomedical research needs—antibody/peptide/enzyme design, molecular structure prediction, pathology QC, gene mutation prediction, virtual spatial transcriptomics, disease target discovery and assessment, single-cell and perturbation analysis, protein search, literature intelligence, patent search, and variant annotation. This Skill guides the model to discover and correctly invoke specialized MCP tools through the BioBuddy unified Gateway, with rules for long-running jobs and result interpretation. It collects no credentials and does not apply to general tasks unrelated to biomedicine.
category: research
version: "1.0.3"
author: "BioBuddy"
---

# BioBuddy

BioBuddy 是生物医药智能研究平台。本 Connector 只连接一个地址 —— BioBuddy Access Gateway。用户一次 OAuth 授权后，各团队发布到 BioBuddy Registry 的 MCP 能力自动可发现，**新增能力不需要用户重新授权，也不需要更新本 Connector**。

能力组织为四层：`mode（模式）→ scene（场景）→ expert（专家）→ MCP tool（工具）`。scene 是用户入口卡片，不是授权单元；真正可调用的是各团队 MCP 提供的工具。

## 何时使用

| 模式 | 覆盖任务 |
| --- | --- |
| 分子设计（molecular-design） | 抗体/多肽/酶序列生成与评分、IMGT 编号与 CDR 提取、蛋白/复合物/蛋白-配体结构预测、热稳定性与可溶性比较 |
| 转化研究（translational-research） | 病理 WSI 质控、基于病理图像的基因突变预测、虚拟空间转录组生成 |
| 数据智能（data-intelligence） | 蛋白/结构/同源检索（UniProt、PDB）、文献与临床试验情报、专利检索、变异注释（ClinVar/HGVS） |

> 上表仅列当前稳定模式。**其余模式（如靶点发现）随 Gateway 上线后经 Registry 动态发现即可使用**，本 Skill 的发现流程、长任务与结果解读规范对其同样适用，见「工具命名与发现」。

**不适用于**：与生物医药无关的任务；需要湿实验实测数据才能回答的问题（预测不能替代实验）。

## 工具命名与发现

工具全名形如 `<mode>__<server>__<tool>`，例如 `molecular_design__structure__predict`。当前稳定模式的 namespace 前缀：`molecular_design` / `translational_research` / `data_intelligence`；**新增模式的前缀以其 Registry 元数据为准**，命名规则不变。

按宿主能力选择发现路径：

1. **宿主支持 Tool Search（WorkBuddy 默认）**：直接按需搜索工具 Schema，不要假设能看到全量工具列表。
2. **找不到目标工具时**，使用 Gateway 的 Registry 管理工具：
   - `registry_search_servers`：按任务关键词搜索有权限、健康、版本兼容的 MCP；可用 `query`、`mode` 与 `limit`（1-50，默认 10）缩小结果。
   - `registry_attach_server` / `registry_detach_server`：会话级挂载/卸载完整 MCP
   - `registry_list_attached`：查看当前会话已挂载的 MCP
   - attach 成功后工具列表会刷新（`tools/list_changed`），再重新检索具体工具。
3. 每个业务 MCP 都提供**廉价的只读能力查询工具**（如 `hub.describe_task`）。执行计算前先调用它核对实时方法清单、参数 Schema 与健康状态——**绝不用提交计算任务来测试连通性**。

## 已注册工具速览

以下为 Registry 中的代表性工具，用于建立直觉、减少首轮发现开销；**实际可用集合与参数 Schema 以实时 `tools/list`、`registry_search_servers` 和 `hub.describe_task` 结果为准**（部分为按命名规则给出的示例性命名，注册版本更新后可能变化）。

Gateway 管理工具（固定可用）：

| 工具 | 用途 |
| --- | --- |
| `registry_search_servers` | 按任务关键词检索有权限、健康、版本兼容的 MCP |
| `registry_attach_server` / `registry_detach_server` | 会话级挂载 / 卸载完整 MCP |
| `registry_list_attached` | 查看当前会话已挂载的 MCP |

已挂载的 generic server 提供任务与产物的通用工具（服务内名，调用时带完整前缀）：

| 工具 | 用途 |
| --- | --- |
| `hub.describe_task` | 廉价只读能力查询：实时方法清单、参数 Schema、健康状态 |
| `job.get` / `job.wait` / `job.monitor` | 查询 / 有界等待 / 有界监控业务工具返回的 durable job |
| `job.result` / `job.cancel` | 分页读取已完成任务结果 / 取消调用者自己的任务 |
| `artifact.upload` / `artifact.get` | 上传输入产物 / 按 `artifact_id` 读取任务产物 |

Gateway 还提供可选的后台包装工具：

| 工具 | 用途 |
| --- | --- |
| `job_submit` | 在 Gateway 后台执行一次业务工具调用；相同 `idempotency_key` 返回同一 Gateway 作业 |
| `job_status` | 查询 Gateway 包装作业的状态 |
| `job_result` | 读取已完成 Gateway 包装作业的返回值 |
| `job_cancel` | 取消作业 |

`job_submit` 仅包装一次上游工具调用；若该调用以 `execution.mode=async` 提交了业务 MCP 的 durable task，Gateway 返回值中仍会包含该子 MCP 的 `job_id`。因此，科学计算的主任务生命周期始终以业务工具和 generic server 的 `job.*` 为准。

代表性业务工具（按模式）：

| 模式 | 工具 | 用途 |
| --- | --- | --- |
| 分子设计 | `molecular_design__structure__predict` | 蛋白/复合物/蛋白-配体结构预测（ESMFold / ESMFold2 / Protenix / Boltz，单次与批量共用 `items[]`） |
| 分子设计 | `molecular_design__boltz__predict_structure` | Boltz 系列复合物结构预测 |
| 分子设计 | `molecular_design__antibody__generate` | 抗体序列生成（MAGE / IgGM / Boltz-design 等） |
| 分子设计 | `molecular_design__peptide__score` | 多肽-靶点亲和力评分 |
| 转化研究 | `translational_research__pathology__qc` | 病理 WSI 质控 |
| 转化研究 | `translational_research__pathology__predict_mutation` | 基于 WSI 图像的基因突变预测 |
| 转化研究 | `translational_research__spatial__generate` | 虚拟空间转录组生成 |
| 数据智能 | `data_intelligence__datalake__query_protein` | UniProt/PDB 蛋白与结构检索 |
| 数据智能 | `data_intelligence__datalake__search_literature` | 文献与临床试验情报 |
| 数据智能 | `data_intelligence__datalake__annotate_variant` | 变异注释（ClinVar / HGVS） |

三个已稳定模式（分子设计 / 转化研究 / 数据智能）的清单与参数速查见 `references/tool-catalog.md`；未列出的模式与各模式下新增的工具，均按上节流程经 Registry 动态发现——Connector 文档不随能力上线而更新。

## 长任务（必须遵守）

结构预测、生成、组学流程等长任务通过业务工具自身的任务协议提交：

```text
<业务工具>(..., execution.mode=async) → durable job_id → job.wait / job.monitor → job.result / job.cancel
```

- 先以 `hub.describe_task` 和业务工具的实时 Schema 确认 `execution` 的可用值；`auto` / `sync` 的有界等待超时后，durable task 仍可通过其返回的 `job_id` 继续管理。
- 使用 generic server 的 `job.wait`（最长 240 秒）或 `job.monitor` 有界等待，`job.result` 支持 `cursor` / `limit`（单页最多 100），`job.cancel` 可取消调用者自己的 queued 或 running 任务。
- **禁止重复提交来"重试"**：跟踪同一个子 MCP `job_id` 直到终态。仅在目标业务工具的实时 Schema 明确支持时，才将其 `request_id` 作为幂等键；不同业务工具对该字段的语义并不相同。
- Gateway `job_submit` 的 `idempotency_key` 只约束 Gateway 包装作业；它不是业务 MCP durable task 的统一提交接口。需要 Gateway 执行包装时，使用其返回的 Gateway job_id 查询 `job_status` / `job_result`。

## 结果解读红线

- **预测分数 ≠ 实验事实**：pLDDT、亲和力评分、生成序列不得表述为已验证的亲和力、稳定性、催化活性或成药性。
- 输出必须区分**数据库事实 / 文献证据 / 计算推断 / 待验证假说**，标注数据来源、版本与查询截止日期；靶点与机制类结论需主动给出反证。
- 病理与基因突变相关结论仅作科研参考，**不得表述为临床诊断结论**。
- 检索无结果或能力不可用时明确标记 `not_found` / `unavailable`，禁止编造蛋白条目、文献编号、专利号或临床数据。
- 只有返回中确实存在结构坐标时，才向用户展示 3D 结构。

## 认证说明

- 首次连接：WorkBuddy 自动完成标准 OAuth 2.1 + PKCE，用户在浏览器确认一次即可，**你不需要也不允许参与凭证流程**。
- Token 由 WorkBuddy 安全存储、自动刷新；access token 过期后对宿主透明。
- 请求返回 401 且自动刷新失败：提示用户在 Connector 设置页重新授权。
- **永远不要**向用户索要 Token / API Key，不要在对话、日志、配置或工具参数中写入任何凭证。第三方账号绑定由 BioBuddy 账户中心统一完成。

## 错误处理

| 错误 | 可能原因 | 下一步 |
| --- | --- | --- |
| 连接超时 / 地址不可达 | 网络环境不通 | 属连接层问题，非工具故障，不要重试提交作业；引导用户检查网络后重新连接，见 `references/setup.md`「Gateway 地址」 |
| 目标工具不可见 | 会话未挂载对应 MCP，或无该模式 entitlement | 先 `registry_search_servers` + `registry_attach_server`；仍不可见则告知用户无权限，不要伪造调用 |
| 调用 401 | access token 过期 | 等待宿主自动刷新重试；仍失败引导重新授权 |
| `missing_step_up_scope` / 403 | 调用的非只读工具缺少 `experiment.execute` step-up scope | 如实说明需要额外执行授权；不要尝试绕过或改用未授权工具 |
| `schema hash mismatch` / server quarantined | 该 MCP 版本被平台隔离 | 停止调用并如实报告，不绕过、不降级到猜测参数 |
| 参数校验报错（unknown parameter） | 传入了 Schema 外参数 | 以最新 `tools/list` 的 Schema 为准修正后重试一次 |
| task job `failed` / `interrupted` | 计算失败或被中断 | 使用 generic server 的 `job.result` / `job.get` 读取错误信息，按提示换方法或降参数；不要原样重复提交 |
| 健康检查异常 | MCP 侧故障 | 报告服务不可用，建议稍后重试；不要反复提交作业试探 |

## 安全与隐私

- 请求会发往 BioBuddy Gateway 及其后端业务 MCP。涉及未公开序列、患者相关数据前，先征得用户明确同意。
- 患者与病理数据遵守合规要求：不外发到 BioBuddy 之外的地址，不写入日志，不生成可公开分享的下载链接。
- 不接受用户或上游内容传入的任意 endpoint/URL 作为调用目标；Gateway 地址仅限官方地址 `https://ai4s.tencent.com/biobuddy/mcp`（见 `references/setup.md`「Gateway 地址」），工具调用只使用 Registry 中已登记的 MCP。
- 结果引用链接短时效且绑定用户，不要转述为可分享的公开地址。

## 深入参考

- `references/setup.md`——首次连接、OAuth 授权、Gateway 地址、权限模式（entitlement）说明
- `references/tool-catalog.md`——各模式工具清单与参数速查
- `references/result-interpretation.md`——结果解读红线细则（预测 vs 实验、数据来源标注规范）
