# 工具清单与参数速查

> 本目录为 Registry 已注册能力的速查参考，**详表仅覆盖当前已稳定的三个模式：分子设计、转化研究、数据智能**。平台以 Gateway 形态持续接入新模式及各模式下的新增工具——**未在本文列出的模式与工具一律通过 Registry 动态发现（见第 4 节），通用约定对所有模式同样适用，无需等待本文更新**。实际可用工具与参数 Schema 一律以实时 `tools/list`、`registry_search_servers` 和各 MCP 的 `hub.describe_task` 返回为准；下表中按命名规则给出的示例性命名可能随注册版本变化。

## 1. 命名与通用约定

- 对外工具全名：`<mode>__<server>__<tool>`，服务内工具用点号分域（如 `structure.predict`），Gateway 自动加前缀。
- 当前已稳定模式的 namespace 前缀：`molecular_design` / `translational_research` / `data_intelligence`。**新增模式的 namespace 前缀以该 MCP 在 Registry 中的元数据为准**，命名规则不变。
- 本节约定（批量、执行模式与风险标注）适用于所有模式，包括未来新增模式。
- 批量约定：单次与批量共用同一个 `items[]` 参数，不做 `predict` / `predict_batch` 两个工具；输入 `id` 会在输出中原样保留。
- 执行模式：业务工具的 `execution.mode` 支持 `auto`、`sync`、`async`。以该工具的实时 Schema 为准；任务超出有界同步等待后，继续使用返回的 durable `job_id` 管理。
- 风险标注：GPU 计算类工具为费用型（costly），调用前先确认方法、参数与健康状态。

## 2. Gateway 管理工具（固定可用）

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `registry_search_servers` | 按任务关键词检索有权限、健康、版本兼容的 MCP | `query`、可选 `mode`、`limit`（1-50，默认 10） |
| `registry_attach_server` | 会话级挂载完整 MCP（幂等） | server 标识 |
| `registry_detach_server` | 会话级卸载 MCP | server 标识 |
| `registry_list_attached` | 查看当前会话已挂载的 MCP | 无 |

## 3. 业务 MCP 任务与 Gateway 异步包装

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `hub.describe_task` | 廉价只读能力查询：实时方法清单、参数 Schema、健康状态 | 任务域 |
| `job.get` | 查询业务工具提交的 durable task 状态快照 | `job_id` |
| `job.wait` | 有界等待一个 durable task | `job_id`、`timeout_seconds`（最长 240 秒） |
| `job.monitor` | 有界监控一个或多个 durable task | `job_id` 或 `job_ids`、`timeout_seconds` |
| `job.result` | 分页读取成功 task 的结果 | `job_id`、可选 `cursor`、`limit`（1-100） |
| `job.cancel` | 取消调用者自己的 queued 或 running task | `job_id` |

长任务应直接调用业务工具，并传入其 Schema 支持的 `execution.mode=async`；返回的 durable `job_id` 由 generic server 的 `job.*` 管理。仅在实时 Schema 明确说明时，才将 `request_id` 用作幂等键。

`artifact.upload` / `artifact.get` 同样由 generic server 提供。该 server 已挂载且业务结果返回 `artifact_id` 时，才按实时 Schema 获取产物。

Gateway 还提供 `job_submit` / `job_status` / `job_result` / `job_cancel` 作为可选后台包装：`job_submit(tool, arguments, idempotency_key)` 只在 Gateway 后台转发一次工具调用。它的 `idempotency_key` 和 Gateway job_id 只适用于该包装层，不能替代业务 MCP durable task 的 `job_id` 与 `job.*` 生命周期。

## 4. 新模式与新增工具的动态发现

本文详表不枚举全部能力。遇到不属于上述三个稳定模式的任务，或在已列模式中找不到目标工具时，按以下流程发现，**不要假设工具不存在，也不要凭命名规则猜测参数**：

1. `registry_search_servers`：用任务关键词检索有权限、健康、版本兼容的 MCP（含新上线的模式与工具）。
2. `registry_attach_server`：挂载目标 MCP；成功后等待 `tools/list_changed`，再刷新工具列表。
3. 以刷新后的 `tools/list` 和该 MCP 的 `hub.describe_task` 为唯一 Schema 来源。
4. 第 1-3 节的命名、批量、执行模式、风险标注与异步作业约定，以及文末的调用前核对清单，对所有模式（含未来新增）同样适用。

## 5. 分子设计模式（`molecular_design`）

| 工具（示例性命名） | 用途 | 备注 |
| --- | --- | --- |
| `molecular_design__structure__predict` | 蛋白/复合物/蛋白-配体结构预测 | `method` 指定 ESMFold / ESMFold2 / Protenix / Boltz；`items[]` 单次批量共用；长任务异步 |
| `molecular_design__boltz__predict_structure` | Boltz 系列复合物结构预测 | 支持蛋白-配体（CCD 配体） |
| `molecular_design__antibody__generate` | 抗体序列生成 | MAGE / IgGM / Boltz-design 等方法；输入抗原序列或 PDB+链+表位 |
| `molecular_design__peptide__generate` | 多肽/环肽序列生成 | PepDIF / RFpeptide / AfCycDesign 等 |
| `molecular_design__peptide__score` | 多肽-靶点亲和力评分 | PepDAF 等；评分为计算推断 |
| `molecular_design__enzyme__generate` | 酶序列生成 | PGM，ORI prompt（EC 号、温度标签） |
| `molecular_design__sequence__compare` | 相对热稳定性 / 预测可溶性比较 | 相对比较，非绝对实验值 |
| `molecular_design__antibody__number_imgt` | IMGT 编号与 CDR 提取 | 只读、廉价 |

## 6. 转化研究模式（`translational_research`）

| 工具（示例性命名） | 用途 | 备注 |
| --- | --- | --- |
| `translational_research__pathology__qc` | 病理 WSI 质控 | 输入 WSI 文件（如 .svs）；输出质量等级与问题区域 |
| `translational_research__pathology__predict_mutation` | 基于 WSI 图像的基因突变预测 | 结果仅作科研参考，非临床诊断 |
| `translational_research__spatial__generate` | 虚拟空间转录组生成 | 计算推断数据，需明确标注 |

## 7. 数据智能模式（`data_intelligence`）

| 工具（示例性命名） | 用途 | 备注 |
| --- | --- | --- |
| `data_intelligence__datalake__query_protein` | UniProt/Swiss-Prot/PDB 蛋白与结构检索 | accession / 序列 / 结构 ID |
| `data_intelligence__datalake__search_literature` | 文献与临床试验情报 | PubMed / ClinicalTrials；标注查询截止日期 |
| `data_intelligence__datalake__search_patent` | 专利检索 | 化合物 InChIKey、专利号、序列相似性 |
| `data_intelligence__datalake__annotate_variant` | 变异注释 | ClinVar / HGVS；含人群频率与临床意义 |

## 8. 调用前核对清单

1. 目标工具在当前 `tools/list` 中可见；不可见先走 Registry 挂载流程。
2. 用 `hub.describe_task` 核对方法清单、参数 Schema 与健康状态。
3. 严格按最新 Schema 传参——未知参数会被报错而非忽略。
4. 长任务通过业务工具的 `execution.mode=async` 提交，并用 generic server 的 `job.wait` / `job.monitor` 跟踪同一个 durable `job_id` 直到终态；不要重复提交"重试"。仅在目标工具实时 Schema 明确支持时才使用 `request_id` 实现幂等。
