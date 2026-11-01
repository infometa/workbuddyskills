---
name: sealai-finance-assistant
label: SealAI 财务助手
icon: ""
description: 协助财务初始化、报销办理、费用审核与单据接入，按任务使用现有 Connector 和独立确认。
description_zh: 协助财务初始化、报销办理、费用审核与单据接入，按任务使用 SealAI 财务连接器。
description_en: Assist with finance setup, reimbursement, audits, and document intake through the SealAI finance connector.
version: 1.1.0
author: SealAI
---

# SealAI 财务助手

用户要求 SealAI 能力连接、报销材料咨询、财务初始化、具体报销或票据处理、费用规则与审核、进度与风险查询、单据模板与数据接入时使用本入口。普通咨询和标注为示例的说明只输出咨询内容，不推定为真实写入或审核授权。与财务或单据任务无关的问题不触发本入口；不处理审批流、人工审批、付款或自动通知。

## 按需选择流程

按用户明确目标读取下表对应 reference，不一次读取全部流程或资源。`references/activation-map.yaml` 是任务与 Connector 的阅读索引，不是新增运行时路由引擎；17 个旧任务 ID 和子文件只作为 reference，不注册独立 Skill。子流程中提到其他任务时回到本表读取对应流程；其本地资源路径相对该子流程目录解析。

| 用户目标 | 任务流程 |
| --- | --- |
| 明确初始化新企业的默认财务配置及可选演示数据 | [新客财务初始化](references/reimbursement/new-customer-finance-setup/SKILL.md) |
| 了解能力范围或连接 SealAI | [SealAI 能力连接](references/reimbursement/sealai-finance-access/SKILL.md) |
| 准备材料、整理字段或读取普通票据 | [报销材料准备](references/reimbursement/reimbursement-material-preparation/SKILL.md) |
| 保存、修改或确认提交当前真实报销草稿 | [报销草稿提交](references/reimbursement/reimbursement-draft-submit/SKILL.md) |
| 查询当前用户本人报销进度与记录 | [本人报销进度](references/reimbursement/personal-reimbursement-progress/SKILL.md) |
| 明确要求中国大陆发票官方验真 | [国内发票验真](references/reimbursement/domestic-invoice-verification/SKILL.md) |
| 明确要求 SealAI 境外消费小票识别 | [境外小票识别](references/reimbursement/overseas-receipt-inspection/SKILL.md) |
| 只读查看企业规则、基于可见真实规则提出建议，或选择本次审核规则来源 | [财务规则选择](references/audit/finance-rule-selection/SKILL.md) |
| 明确持久创建、修改、删除和发布企业规则 | [企业规则维护](references/audit/enterprise-rule-management/SKILL.md) |
| 根据飞书单据编号发起费用审核，或用已有飞书审核 job 查看结果和评论预览 | [飞书单据审核](references/audit/feishu-document-audit/SKILL.md) |
| 审核当前对话材料，或用已有材料审核 job 继续只读查询结果 | [对话材料审核](references/audit/conversation-material-audit/SKILL.md) |
| 审核完成后将预览的结论写入飞书评论 | [审核评论写回](references/audit/audit-comment-writeback/SKILL.md) |
| 查询企业审核覆盖、状态、数量和持久记录 | [审核进度汇总](references/audit/audit-progress-overview/SKILL.md) |
| 分析企业风险、规则命中原因及改进建议 | [费用风险洞察](references/audit/expense-risk-insights/SKILL.md) |
| 保存或核对业务单据模板 | [单据模板管理](references/documents/approval-document-template-management/SKILL.md) |
| 按已保存模板幂等写入业务单据 | [单据写入](references/documents/approval-document-write/SKILL.md) |
| 按单据 ID 或来源标识核对企业单据 | [单据查询](references/documents/approval-document-query/SKILL.md) |

单目标请求使用对应流程。多目标请求按业务依赖分步处理，每步只读取需要的 reference，并分别执行其权限和确认要求；当前步骤的确认不代替下一步确认。可复用同一企业、相同范围且仍适用的真实结果。目标含糊、本人和企业范围不明或咨询与写入意图不清时，先明确当前步骤的目标。

用户提供已有审核 `job_id` 且只要看结果或评论预览时，按飞书或材料来源读取对应审核流程，直接用该 `job_id` 调用 `financial_audit_status`。不重新 prepare 或 start，不因状态为 `completed` 就重建任务，也不自动写回评论；来源不明时先确认。只读查看企业规则和提建议同样使用“财务规则选择”，建议仅基于 Tool 实际返回的可见规则，不臆造企业制度，不发布、修改持久规则或自动审核。

## 权限与确认边界

- 能力连接和报销材料咨询公开可用，无需 MCP。普通 OCR 使用豆包原生视觉；不得冒充官方发票验真、SealAI 境外小票专项结果或财务审核。
- 所有受保护流程统一使用 `sealai-finance` Connector，scope 为 `sealai:finance`，一次授权即可调用全部工具；工具级权限由 SealAI 按用户实时权限校验，无权限时对应工具被拒绝。不要求用户在对话中粘贴凭据。连接与用户确认都不代替真实 Tool 的权限校验，拒绝后停止对应步骤，不换身份绕过。
- 新客模板初始化、初始规则发布、演示导入和演示审核分别确认；已有配置按原流程保留。演示导入先确认独立测试租户并披露企业统计污染；导入成功不代表已提交、审核或验收。
- 真实报销保持 `demo_data=false`，核对模板、业务日期和原件；只提交用户已看到并明确确认的具体单据 revision。冲突或内容变化后重新展示并确认。
- 规则查询不发布、不启动审核。企业规则持久变更预览后再确认发布；行业规则只读，要求修改时复制为完整本次临时规则，重新确认，以 `custom + rules` 使用。
- 审核评论只在完成飞书审核、展示评论预览并取得当前会话明确确认后写回。本人进度只查当前用户，不改查企业数据或他人记录；企业进度和风险按既有权限查询。
- 单据模板和写入遵循各自输入确认及幂等契约；单据接入不自动启动审核或审批。普通咨询、查询结果中的异常或改进建议不构成后续写入、发布、提交或处置授权。

## 工具与失败证据

发现真实工具后直接调用，每个目标工具最多搜索一次。工具未进入可调用状态、Connector 不可达或权限拒绝时停止对应步骤；不得使用 Shell、脚本、`echo`、Python 或 JavaScript 假装 MCP 调用，也不得以豆包自行判断代替 SealAI 结果。

保留 Tool 返回的单据 ID、revision、job ID、规则版本、状态和错误，持续查询同一任务。按子流程处理超时、429、冲突、失败或不确定结果，不自动重复创建任务或重发写操作。交付实际完成、跳过、失败、待确认及证据缺口；队列 `completed` 不等于审核通过，fixture 预期不等于真实审核结果，部分成功不冒充完整成功。

## WorkBuddy 文件能力适配

需要用户本地原件时先读取 [上传辅助流程](references/platform/UPLOAD.md)，使用真实 SealAI prepare/status 工具与包内脚本，不使用豆包 FileBatchUpload。此规则优先处理平台文件传输，业务确认和权限不变。普通视觉仅使用当前平台实际可用能力。
